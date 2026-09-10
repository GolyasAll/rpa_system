import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
import re
import os
import requests
from io import BytesIO
from PIL import Image, ImageOps, ImageEnhance
import pytesseract

# Caminho do Tesseract
pytesseract.pytesseract.tesseract_cmd = r'C:\Users\clauber\AppData\Local\Programs\Tesseract-OCR\tesseract.exe'

def clicar_menu_exato(navegador, nome_menu):
    try:
        xpath = f"//*[normalize-space(text())='{nome_menu}']"
        elemento = WebDriverWait(navegador, 5).until(
            EC.presence_of_element_located((By.XPATH, xpath))
        )
        navegador.execute_script("arguments[0].scrollIntoView({block: 'center'});", elemento)
        time.sleep(0.4)
        navegador.execute_script("arguments[0].click();", elemento)
        return True
    except Exception:
        return False


def extrair_numero_capitulo(navegador, elemento_imagem):
    caminho_temp = "temp_ocr.png"
    try:
        # O capítulo acabou de ficar visível. Aguarda a renderização estabilizar
        # antes de enviar HOME e iniciar o OCR do cabeçalho.
        time.sleep(3)
        navegador.execute_script(
            "window.scrollTo(0, 0);"
            "document.documentElement.scrollTop = 0;"
            "document.body.scrollTop = 0;"
            "const img = arguments[0];"
            "let node = img;"
            "while (node) {"
            "  if (node.scrollHeight > node.clientHeight || node.scrollWidth > node.clientWidth) {"
            "    node.scrollTop = 0;"
            "    node.scrollLeft = 0;"
            "  }"
            "  node = node.parentElement;"
            "}"
            "img.scrollIntoView({block: 'start', inline: 'start'});",
            elemento_imagem
        )
        try:
            navegador.execute_script(
                "arguments[0].setAttribute('tabindex', '-1'); arguments[0].focus();",
                elemento_imagem
            )
            ActionChains(navegador).send_keys(Keys.HOME).perform()
        except Exception:
            # O JavaScript acima já cobre navegadores ou páginas sem foco ativo.
            pass
        time.sleep(0.5)

        url_imagem = None
        for tentativa in range(5):
            try:
                url_imagem = elemento_imagem.get_attribute("src")
                if url_imagem: break
            except:
                time.sleep(1)
                try:
                    elemento_imagem = navegador.find_element(By.XPATH, "//img[@alt='manual']")
                except: pass
                
        if not url_imagem:
            return "SEM_LINK"

        resposta = requests.get(url_imagem, timeout=15)
        imagem_completa = Image.open(BytesIO(resposta.content))
        
        # ======================================================================
        # RECORTE: Pega a largura toda (para achar o 596 e o 444 na direita)
        # ======================================================================
        largura, altura = imagem_completa.size
        area_corte = (0, 0, largura, min(120, altura))
        img_topo = imagem_completa.crop(area_corte)
        img_cinza = img_topo.convert('L')
        
        img_rgb = img_topo.convert('RGB')

        # ======================================================================
        # MOTOR OCR "INFALÍVEL" EM CASCATA
        # ======================================================================
        img_zoom = img_cinza.resize((img_cinza.width * 3, img_cinza.height * 3), Image.Resampling.LANCZOS)
        
        def ler_ocr(img_alvo):
            img_alvo.save(caminho_temp)
            # Whitelist com a letra 'í' minúscula inclusa para facilitar a leitura da palavra "Capítulo"
            texto = pytesseract.image_to_string(caminho_temp, config='--psm 6 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz:-.í')
            
            # MÁGICA: Procura OBRIGATORIAMENTE a palavra "Capítulo" seguida do número.
            # Isso ignora completamente qualquer código de barras ou serial isolado na imagem!
            # Aceita pequenas deformações de "Capítulo" produzidas pelo OCR,
            # mas exige o prefixo "Cap" e o número imediatamente depois.
            match = re.search(r'(?i)cap(?:[a-zÀ-ÿ]{0,6})?\s*([0-9oOiIlLsSbB]+)', texto)
            if match:
                bruto = match.group(1).upper()
                limpo = bruto.replace('O', '0').replace('I', '1').replace('L', '1').replace('S', '5').replace('B', '8')
                if re.match(r'^\d+$', limpo): 
                    return limpo
            return None

        # LENTES DO OCR (Filtros de imagem):
        # 1. Contraste Forte (Para ler capítulos com letra preta normal, como o 1403)
        img_contraste = ImageEnhance.Contrast(img_zoom).enhance(3.0)
        
        # 2. Inversão de Cores (Transforma a letra branca do 596 e 444 em letra preta legível!)
        img_invertida = ImageOps.invert(img_zoom)
        img_invertida = ImageEnhance.Contrast(img_invertida).enhance(3.0)
        
        # 3. Binarizações adaptativas para texto preto, branco ou cinza claro.
        pixels = list(img_cinza.getdata())
        media_pixel = sum(pixels) / len(pixels)
        desvio_pixel = max(8, (sum((pixel - media_pixel) ** 2 for pixel in pixels) / len(pixels)) ** 0.5)
        imagens_binarias = []
        for limiar in (
            media_pixel - desvio_pixel * 0.55,
            media_pixel,
            media_pixel + desvio_pixel * 0.55,
        ):
            limiar = max(35, min(220, limiar))
            binaria = img_zoom.point(lambda p, t=limiar: 255 if p > t else 0)
            imagens_binarias.extend([binaria, ImageOps.invert(binaria)])

        # 4. A própria imagem com zoom apenas (Fallback)
        # Setup para cabeçalhos azul-escuros com texto claro (ex.: "Cap 144").
        # A faixa azul é isolada e as letras claras viram texto preto em fundo branco.
        pixels_rgb = img_rgb.load()
        pontos_azuis = [
            (x, y)
            for y in range(img_rgb.height)
            for x in range(img_rgb.width)
            if (
                pixels_rgb[x, y][2] > 70
                and pixels_rgb[x, y][2] > pixels_rgb[x, y][0] * 1.35
                and pixels_rgb[x, y][2] > pixels_rgb[x, y][1] * 1.20
            )
        ]
        img_cabecalho_azul = None
        img_cabecalho_azul_texto_escuro = None
        if pontos_azuis:
            xs, ys = zip(*pontos_azuis)
            margem = 3
            area_azul = (
                max(0, min(xs) - margem),
                max(0, min(ys) - margem),
                min(img_rgb.width, max(xs) + margem + 1),
                min(img_rgb.height, max(ys) + margem + 1),
            )
            faixa_azul = img_rgb.crop(area_azul)
            img_cabecalho_azul = Image.new('L', faixa_azul.size, 255)
            img_cabecalho_azul.putdata([
                0 if min(pixel) > 165 else 255
                for pixel in faixa_azul.getdata()
            ])
            img_cabecalho_azul = img_cabecalho_azul.resize(
                (img_cabecalho_azul.width * 4, img_cabecalho_azul.height * 4),
                Image.Resampling.LANCZOS
            )

            # Tipo 22: fundo azul-vivo e texto escuro. O filtro anterior é
            # adequado para letras claras; este usa o brilho máximo do pixel
            # para preservar somente caracteres escuros em fundo branco.
            img_cabecalho_azul_texto_escuro = Image.new('L', faixa_azul.size, 255)
            img_cabecalho_azul_texto_escuro.putdata([
                0 if max(pixel) < 120 else 255
                for pixel in faixa_azul.getdata()
            ])
            img_cabecalho_azul_texto_escuro = img_cabecalho_azul_texto_escuro.resize(
                (
                    img_cabecalho_azul_texto_escuro.width * 4,
                    img_cabecalho_azul_texto_escuro.height * 4,
                ),
                Image.Resampling.LANCZOS
            )

        variacoes = [img for img in [
            img_cabecalho_azul,
            img_cabecalho_azul_texto_escuro,
            img_contraste,
            img_invertida,
            *imagens_binarias,
            img_zoom,
        ] if img is not None]

        # Tenta ler com cada lente, uma de cada vez. Achou, ele para e retorna.
        for img_filtro in variacoes:
            resultado = ler_ocr(img_filtro)
            if resultado:
                if os.path.exists(caminho_temp): os.remove(caminho_temp)
                return resultado

        if os.path.exists(caminho_temp): os.remove(caminho_temp)
        return "NÃO_LIDO"
        
    except Exception as e:
        print(f"      [ERRO OCR] Detalhe técnico: {e}")
        if os.path.exists(caminho_temp): os.remove(caminho_temp)
        return "ERRO_OCR"
