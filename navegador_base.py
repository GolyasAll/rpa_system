import time
import random

from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys


def iniciar_sessao(email, senha, modo_invisivel=False):

    opcoes = Options()

    if modo_invisivel:
        opcoes.add_argument('--headless=new')
        print("Modo Invisível (Headless) ATIVADO.")
    else:
        print("Modo Visual ATIVADO. Abrindo janela do Chrome...")
    
    opcoes.add_argument('--window-size=1920,1080')
    opcoes.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    opcoes.add_argument('--log-level=3') 

    navegador = webdriver.Chrome(options=opcoes)

    try:
        print("Acessando o Simplo Online em segundo plano...")
        navegador.get("https://www.simploonline2.com/")

        campo_email = WebDriverWait(navegador, 10).until(
            EC.presence_of_element_located((By.XPATH, "//input[@name='email']"))
        )
        # Usa o e-mail que o usuário digitou na Matriz
        campo_email.send_keys(email)
        
        campo_senha = navegador.find_element(By.XPATH, "//input[@type='password']")
        # Usa a senha que o usuário digitou na Matriz
        campo_senha.send_keys(senha)
        
        time.sleep(1)
        campo_senha.send_keys(Keys.ENTER)

        numero_aleatorio = random.randint(1000, 9999)
        nome_aleatorio = f"Visitante_{numero_aleatorio}"
        print(f"Registrando dispositivo: {nome_aleatorio}")

        campo_popup = WebDriverWait(navegador, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//input[@name='deviceName']"))
        )
        campo_popup.send_keys(nome_aleatorio)

        botao_confirmar = navegador.find_element(By.XPATH, "//button[contains(text(), 'Confirmar')]")
        botao_confirmar.click()

        print("Aguardando o carregamento do painel...")
        WebDriverWait(navegador, 15).until(
            EC.url_changes("https://www.simploonline2.com/")
        )
        
        # =========================================================
        # NOVA BLINDAGEM DO PAINEL PRINCIPAL
        # =========================================================
        print("Aguardando os ícones dos pacotes aparecerem na tela...")
        WebDriverWait(navegador, 15).until(
            EC.presence_of_element_located((By.XPATH, "//img[@alt='simplus']"))
        )
        time.sleep(2) 
        # =========================================================

        print("Login feito com sucesso! Sessão global iniciada.")
        return navegador

    except Exception as e:
        print(f"Erro crítico durante o login global: {e}")
        navegador.quit()
        raise e

def finalizar_sessao(navegador):
    """Realiza o logout seguro e encerra o processo do Chrome"""
    if not navegador:
        return
        
    try:
        print("\nIniciando processo de logout seguro...")
        xpath_setinha_perfil = "//*[local-name()='svg' and @viewBox='0 0 512 512' and ./*[local-name()='path' and contains(@d, 'M256 294.1')]]"
        botao_setinha = WebDriverWait(navegador, 10).until(
            EC.element_to_be_clickable((By.XPATH, xpath_setinha_perfil))
        )
        botao_setinha.click()
        time.sleep(1) 
        
        botao_sair = WebDriverWait(navegador, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//span[text()='Sair']"))
        )
        botao_sair.click()
        print("Logout efetuado com sucesso!")
        time.sleep(2)
    except Exception as e:
        print(f"Aviso: Não foi possível deslogar formalmente.")
    finally:
        print("Encerrando a sessão do navegador...")
        navegador.quit()
        print("--- SISTEMA FINALIZADO ---")