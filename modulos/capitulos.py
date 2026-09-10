from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

def extrair_indices(navegador):
    """
    Extrai os índices do painel lateral.
    Contém proteção para não clicar nos menus da coluna esquerda acidentalmente.
    """
    indices = []
    try:
        # 1. ESCOPO LIMITADO: 
        # Acha o cabeçalho "Índices", sobe na árvore DOM (parent/ancestor) e desce caçando sanfonas.
        # Isso garante que ele só vai abrir as pastinhas do lado direito da tela.
        # Primeiro localiza o menor container que contém tanto o título
        # "Índices" quanto os dropdowns React. Isso isola a coluna de índices
        # sem depender de uma quantidade fixa de elementos ancestrais.
        #
        # Dentro desse container, seleciona somente os dropdowns React fechados
        # que possuem a seta `arrow-navigator` informada no HTML do sistema.
        # Mantém o escopo no painel de Índices. Assim, setas de submanuais
        # nunca participam da abertura nem da leitura dos índices.
        xpath_painel_indices = (
            "(//h1[contains(normalize-space(.), 'Índices')]"
            "/ancestor::div[.//div[contains(concat(' ', normalize-space(@class), ' '), "
            "' index-menu-item ')]][1])"
        )
        xpath_botoes = (
            f"{xpath_painel_indices}//div[@role='button' and "
            "@aria-expanded='false' and "
            "./img[@alt='arrow-navigator' and "
            "contains(concat(' ', normalize-space(@class), ' '), ' arrow-navigator ')]]"
        )

        # O React recria o DOM ao abrir cada item; por isso a lista de botões é
        # recarregada após cada clique, até não haver mais menus recolhidos.
        for _ in range(100):
            botoes_fechados = navegador.find_elements(By.XPATH, xpath_botoes)
            if not botoes_fechados:
                break

            try:
                btn = botoes_fechados[0]
                seta = btn.find_element(
                    By.XPATH,
                    "./img[@alt='arrow-navigator' and "
                    "contains(concat(' ', normalize-space(@class), ' '), ' arrow-navigator ')]"
                )
                navegador.execute_script("arguments[0].scrollIntoView({block: 'center'});", seta)
                navegador.execute_script("arguments[0].click();", seta)
                WebDriverWait(navegador, 2).until(
                    lambda _: btn.get_attribute("aria-expanded") == "true"
                )
                time.sleep(0.2)
            except:
                # Se o botão foi recriado durante o clique, tenta novamente com
                # a referência atualizada na próxima passagem do laço.
                time.sleep(0.2)
                continue

        # 2. CAPTURA: Com todas as gavetas direitas abertas, puxa os textos
        xpath_indice = (
            f"{xpath_painel_indices}//div["
            "contains(concat(' ', normalize-space(@class), ' '), ' index-menu-item ')]"
            "//span[contains(concat(' ', normalize-space(@class), ' '), ' label ')]"
        )
        
        elementos = WebDriverWait(navegador, 5).until(
            EC.presence_of_all_elements_located((By.XPATH, xpath_indice))
        )
        
        for el in elementos:
            texto = el.text.strip()
            # Impede duplicações no array e limpa vazios
            if texto and texto not in indices:
                indices.append(texto)
                # Opcional: print para acompanhar o robô "lendo"
                # print(f"  [DEBUG] Índice coletado: {texto}")
        
        return indices

    except Exception as e:
        # Se falhar (por ex: um modelo que realmente não tenha índices cadastrados)
        return []
