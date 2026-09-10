import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from utils import clicar_menu_exato, extrair_numero_capitulo
from modulos.capitulos import extrair_indices 

def rodar(navegador, wb, profundidade="modelos", status_global=None,
          nome_pacote="Simplus", icone_pacote="simplus"):
    """Executa a varredura base para um pacote com estrutura Simplus."""
    try:
        aba = wb.create_sheet(nome_pacote[:31])
        
        if profundidade == "modelos":
            aba.append(['Pacote', 'Manual', 'Submanual', 'Montadora', 'Modelo'])
        elif profundidade == "indices":
            aba.append(['Pacote', 'Manual', 'Submanual', 'Montadora', 'Modelo', 'Índice'])
        elif profundidade == "capitulos":
            aba.append(['Pacote', 'Manual', 'Submanual', 'Montadora', 'Modelo', 'Qtd Índices', 'Capítulo'])

        print(f"Garantindo pacote '{nome_pacote}'...")
        botao_pacote = WebDriverWait(navegador, 10).until(
            EC.element_to_be_clickable((By.XPATH, f"//img[@alt='{icone_pacote}']"))
        )
        navegador.execute_script("arguments[0].click();", botao_pacote)
        time.sleep(3) 

        estrutura_manuais = {
            "ABS/ASR/ESP": [], "CLIMA TRUCK": [], "CLIMACAR": [], "CÂMBIO": [],
            "CÂMBIO TRUCK": [], "CÓDIGO DE FALHAS": [], "ELECTRA": [], "ELECTRA TRUCK": [],
            "INJEÇÃO ELETRÔNICA": [], "LOCAR": [], "LOCAR TRUCK": [], "LUBRITEC": [],
            "REVISA CAR": [], "SCOPE TRUCK": [], "TORKS": [], "TORKS TRUCK": [],
            "INJEÇÃO DIESEL": ["INJEÇÃO ELETRÔNICA DIESEL", "MANUAL ARLA"],
            "MIX": ["AIRBAG", "ALARMES", "IMOBILIZADOR", "RESETS"],
            "MOTORES": ["LINHA LEVE", "LINHA PESADA"],
            "OSCI": ["MT PRO", "PICO SCOPE"],
            "SINCRO": ["CORREIAS", "CORRENTES", "POLY-V"]
        }

        manuais_disponiveis = list(estrutura_manuais.keys())
        manuais_alvo = manuais_disponiveis 
        
        if status_global is not None:
            print(f"\n{'='*50}")
            print(" INTERVENÇÃO SOLICITADA: SELECIONE O MANUAL")
            print(f"{'='*50}")
            print("[0] - TODOS OS MANUAIS")
            for idx, nome_man in enumerate(manuais_disponiveis, 1):
                print(f"[{idx}] - {nome_man}")
                
            print("\n>>> O robô foi pausado. Aguardando a sua digitação no painel...")
            status_global["aguardando_input"] = True
            
            while status_global["resposta_input"] is None:
                time.sleep(1)
                
            resposta_usuario = status_global["resposta_input"]
            status_global["aguardando_input"] = False
            status_global["resposta_input"] = None
            
            try:
                opcao = int(resposta_usuario)
                if opcao == 0:
                    print("\n=> Opção [0]: Retomando... Varrendo TODOS os manuais.")
                elif 1 <= opcao <= len(manuais_disponiveis):
                    manual_escolhido = manuais_disponiveis[opcao - 1]
                    manuais_alvo = [manual_escolhido]
                    print(f"\n=> Opção [{opcao}]: Retomando... Varrendo apenas '{manual_escolhido}'.")
                else:
                    print("\n=> Opção inválida. Por segurança, varrendo TODOS.")
            except:
                print("\n=> Entrada inválida. Por segurança, varrendo TODOS.")

        estrutura_filtrada = {k: v for k, v in estrutura_manuais.items() if k in manuais_alvo}

        for nome_manual, lista_submanuais in estrutura_filtrada.items():
            print(f"\n==========================================")
            print(f"ABRINDO MANUAL PRINCIPAL: {nome_manual}")
            print(f"==========================================")
            print(f"[MANUAL] {nome_manual}")

            sucesso_manual = clicar_menu_exato(navegador, nome_manual)
            if not sucesso_manual:
                print(f"  [AVISO] Manual '{nome_manual}' não encontrado nesta versão. Pulando...")
                continue 

            time.sleep(1.5) 
            lista_para_raspar = lista_submanuais if len(lista_submanuais) > 0 else ["-"]

            for nome_submanual in lista_para_raspar:
                manual_texto_log = nome_manual if nome_submanual == "-" else f"{nome_manual} ({nome_submanual})"

                if nome_submanual != "-":
                    print(f"\n  >>> Acessando Submanual: {nome_submanual}")
                    print(f"[MANUAL] {nome_manual} -> {nome_submanual}") 
                    sucesso_sub = clicar_menu_exato(navegador, nome_submanual)
                    if not sucesso_sub:
                        print(f"  [AVISO] Submanual '{nome_submanual}' não encontrado. Pulando...")
                        continue
                    time.sleep(2) 
                else:
                    print(f"\n  >>> Manual direto (sem submanuais). Iniciando varredura...")
                
                print("  Aguardando a lista de montadoras...")
                xpath_caixa_montadoras = "//div[contains(@class, 'sc-dWRHGJ')]"
                
                try:
                    WebDriverWait(navegador, 5).until(
                        EC.presence_of_element_located((By.XPATH, f"{xpath_caixa_montadoras}//div[contains(@class, 'menu-item')]"))
                    )
                except:
                    print(f"  [AVISO] Nenhuma montadora encontrada. Pulando...")
                    continue 
                
                caixa_montadoras = navegador.find_element(By.XPATH, xpath_caixa_montadoras)
                lista_inicial = caixa_montadoras.find_elements(By.XPATH, ".//div[contains(@class, 'menu-item')]")
                nomes_disponiveis = [m.text.strip() for m in lista_inicial if m.text.strip()]
                montadoras_alvo = nomes_disponiveis 
                
                if profundidade in ["indices", "capitulos"] and status_global is not None:
                    print(f"\n{'='*50}")
                    print(f" INTERVENÇÃO SOLICITADA: MONTADORA DE '{manual_texto_log}'")
                    print(f"{'='*50}")
                    print("[0] - TODAS AS MONTADORAS")
                    for idx, nome_mont in enumerate(nomes_disponiveis, 1):
                        print(f"[{idx}] - {nome_mont}")
                        
                    print("\n>>> O robô foi pausado. Aguardando a sua digitação no painel...")
                    status_global["aguardando_input"] = True
                    
                    while status_global["resposta_input"] is None:
                        time.sleep(1)
                        
                    resposta_usuario = status_global["resposta_input"]
                    status_global["aguardando_input"] = False
                    status_global["resposta_input"] = None
                    
                    try:
                        opcao = int(resposta_usuario)
                        if opcao == 0:
                            print("\n=> Opção [0]: Retomando... Varrendo TODAS as montadoras.")
                        elif 1 <= opcao <= len(nomes_disponiveis):
                            montadora_escolhida = nomes_disponiveis[opcao - 1]
                            montadoras_alvo = [montadora_escolhida]
                            print(f"\n=> Opção [{opcao}]: Retomando... Varrendo apenas '{montadora_escolhida}'.")
                        else:
                            print("\n=> Opção inválida. Por segurança, varrendo TODAS.")
                    except:
                        print("\n=> Entrada inválida. Por segurança, varrendo TODAS.")
                
                qtd_montadoras = len(lista_inicial)
                for i in range(qtd_montadoras):
                    caixa_atualizada = navegador.find_element(By.XPATH, xpath_caixa_montadoras)
                    montadoras_atualizadas = caixa_atualizada.find_elements(By.XPATH, ".//div[contains(@class, 'menu-item')]")
                    montadora_atual = montadoras_atualizadas[i]
                    nome_montadora = montadora_atual.text.strip()
                    
                    if not nome_montadora: continue
                    if nome_montadora not in montadoras_alvo: continue
                    
                    print(f"[MONTADORA] {nome_montadora}")
                    print(f"Iniciando varredura na montadora: {nome_montadora}")
                        
                    modelos_da_montadora = []
                    xpath_modelos_exato = "//div[contains(@class, 'automodel-menu-item')]//span[contains(@class, 'label')]"
                    
                    for tentativa_clique in range(2):
                        navegador.execute_script("arguments[0].scrollIntoView({block: 'center'});", montadora_atual)
                        time.sleep(0.5)
                        navegador.execute_script("arguments[0].click();", montadora_atual)
                        time.sleep(0.8) 
                        
                        tentativas_espera = 0
                        while tentativas_espera < 20:
                            modelos_da_montadora = navegador.find_elements(By.XPATH, xpath_modelos_exato)
                            if len(modelos_da_montadora) > 0: break 
                            time.sleep(1)
                            tentativas_espera += 1
                            
                        if len(modelos_da_montadora) > 0: break 
                        else:
                            if tentativa_clique == 0:
                                print(f"      [ALERTA] A montadora '{nome_montadora}' retornou 0. Reaplicando regra de 20s...")
                    
                    qtd_modelos = len(modelos_da_montadora)
                    print(f"      -> {nome_montadora}: {qtd_modelos} modelos salvos.")
                    print(f"[TOTAL_MODELOS] {qtd_modelos}") 

                    for m in range(qtd_modelos):
                        sucesso_reconexao = False
                        for tentativa_rec in range(15):
                            modelos_atualizados = navegador.find_elements(By.XPATH, xpath_modelos_exato)
                            
                            if m < len(modelos_atualizados):
                                sucesso_reconexao = True
                                break
                                
                            time.sleep(1)
                            try:
                                setinhas = navegador.find_elements(By.XPATH, "//img[@alt='arrow-navigator']")
                                if len(setinhas) > 0:
                                    navegador.execute_script("arguments[0].click();", setinhas[0])
                                    time.sleep(1.5)
                            except: pass

                            try:
                                cx_verificacao = navegador.find_element(By.XPATH, xpath_caixa_montadoras)
                                montadoras_verificacao = cx_verificacao.find_elements(By.XPATH, ".//div[contains(@class, 'menu-item')]")
                                if i < len(montadoras_verificacao):
                                    navegador.execute_script("arguments[0].scrollIntoView({block: 'center'});", montadoras_verificacao[i])
                                    navegador.execute_script("arguments[0].click();", montadoras_verificacao[i])
                                    time.sleep(1.5)
                            except: pass

                        if not sucesso_reconexao:
                            print(f"      [ALERTA CRÍTICO] DOM permanentemente perdido no modelo {m+1}. Abortando {nome_montadora}.")
                            break
                        
                        modelo_span = modelos_atualizados[m]
                        nome_modelo = modelo_span.text.strip()
                        if not nome_modelo: continue

                        if profundidade == "modelos":
                            aba.append(['Simplus', nome_manual, nome_submanual, nome_montadora, nome_modelo])
                            print(f"[{manual_texto_log}] -> [{nome_montadora}] -> Mapeado: {nome_modelo}")
                            print("[REGISTROS] 1")

                        elif profundidade == "indices":
                            try:
                                container_modelo = modelo_span.find_element(By.XPATH, "./ancestor::div[contains(@class, 'automodel-menu-item')]")
                                navegador.execute_script("arguments[0].scrollIntoView({block: 'center'});", container_modelo)
                                time.sleep(0.4)
                                navegador.execute_script("arguments[0].click();", container_modelo)
                            except:
                                navegador.execute_script("arguments[0].scrollIntoView({block: 'center'});", modelo_span)
                                navegador.execute_script("arguments[0].click();", modelo_span)

                            time.sleep(2.5) 
                            if len(navegador.find_elements(By.XPATH, "//h1[contains(text(), 'Índices')]")) > 0:
                                lista_indices = extrair_indices(navegador)
                                if lista_indices:
                                    for indice in lista_indices:
                                        aba.append(['Simplus', nome_manual, nome_submanual, nome_montadora, nome_modelo, indice])
                                        print(f"[{manual_texto_log}] -> [{nome_montadora}] -> [{nome_modelo}] -> {indice}")
                                        print("[REGISTROS] 1") 
                                else:
                                    aba.append(['Simplus', nome_manual, nome_submanual, nome_montadora, nome_modelo, "SEM ÍNDICES"])
                                    print(f"[{manual_texto_log}] -> [{nome_montadora}] -> [{nome_modelo}] -> SEM ÍNDICES")
                                    print("[REGISTROS] 1")
                            else:
                                print(f"  [Aviso] Painel de índices não abriu para {nome_modelo}")
                                aba.append(['Simplus', nome_manual, nome_submanual, nome_montadora, nome_modelo, "ERRO NO CLIQUE"])
                                print("[REGISTROS] 1")

                        elif profundidade == "capitulos":
                            try:
                                container_modelo = modelo_span.find_element(By.XPATH, "./ancestor::div[contains(@class, 'automodel-menu-item')]")
                                navegador.execute_script("arguments[0].scrollIntoView({block: 'center'});", container_modelo)
                                time.sleep(0.4)
                                navegador.execute_script("arguments[0].click();", container_modelo)
                            except:
                                navegador.execute_script("arguments[0].scrollIntoView({block: 'center'});", modelo_span)
                                navegador.execute_script("arguments[0].click();", modelo_span)

                            time.sleep(2.5) 
                            if len(navegador.find_elements(By.XPATH, "//h1[contains(text(), 'Índices')]")) > 0:
                                lista_indices = extrair_indices(navegador)
                                if lista_indices:
                                    qtd_indices = len(lista_indices)
                                    print(f"  >>> {qtd_indices} índices encontrados. Injetando clique no primeiro...")
                                    try:
                                        xpath_primeiro_indice = "(//div[contains(@class, 'index-menu-item')])[1]"
                                        elemento_primeiro_indice = WebDriverWait(navegador, 5).until(
                                            EC.element_to_be_clickable((By.XPATH, xpath_primeiro_indice))
                                        )
                                        navegador.execute_script("arguments[0].scrollIntoView({block: 'center'});", elemento_primeiro_indice)
                                        navegador.execute_script("arguments[0].click();", elemento_primeiro_indice)
                                        print("  [AGUARDANDO] Baixando renderização do capítulo do servidor Delphi...")
                                        
                                        xpath_imagem_capitulo = "//img[@alt='manual']" 
                                        img_capitulo = WebDriverWait(navegador, 40).until(
                                            EC.visibility_of_element_located((By.XPATH, xpath_imagem_capitulo))
                                        )
                                        print("  [SUCESSO] Capítulo renderizado! Iniciando varredura OCR no cabeçalho...")
                                        
                                        numero_cap = extrair_numero_capitulo(navegador, img_capitulo)
                                        print(f"  [OCR] -> Leitura concluída! Capítulo identificado: {numero_cap}")
                                        
                                        aba.append(['Simplus', nome_manual, nome_submanual, nome_montadora, nome_modelo, qtd_indices, numero_cap])
                                        print(f"[{manual_texto_log}] -> [{nome_montadora}] -> [{nome_modelo}] -> {qtd_indices} ÍNDICES -> CAP: {numero_cap}")
                                        print("[REGISTROS] 1")
                                        
                                        print("  >>> Fechando capítulo e reabrindo menu lateral...")
                                        try:
                                            xpath_setinha = "//img[@alt='arrow-navigator']"
                                            btn_setinha = WebDriverWait(navegador, 5).until(
                                                EC.element_to_be_clickable((By.XPATH, xpath_setinha))
                                            )
                                            navegador.execute_script("arguments[0].click();", btn_setinha)
                                            time.sleep(2)
                                            print("  [SUCESSO] Menu lateral restaurado.")
                                        except Exception as e_seta:
                                            print(f"  [AVISO] Não foi possível clicar na setinha: {e_seta}")
                                        
                                    except Exception as erro_cap:
                                        print(f"  [AVISO] Falha durante a interação com o capítulo/menu/OCR: {erro_cap}")
                                        try:
                                            setinhas_emergencia = navegador.find_elements(By.XPATH, "//img[@alt='arrow-navigator']")
                                            if len(setinhas_emergencia) > 0:
                                                navegador.execute_script("arguments[0].click();", setinhas_emergencia[0])
                                                time.sleep(2)
                                        except: pass

                                else:
                                    aba.append(['Simplus', nome_manual, nome_submanual, nome_montadora, nome_modelo, 0, "-", "NÃO"])
                                    print(f"[{manual_texto_log}] -> [{nome_montadora}] -> [{nome_modelo}] -> 0 ÍNDICES")
                                    print("[REGISTROS] 1")
                            else:
                                print(f"  [Aviso] Painel de índices não abriu para {nome_modelo}")
                                aba.append(['Simplus', nome_manual, nome_submanual, nome_montadora, nome_modelo, "ERRO NO CLIQUE", "-", "NÃO"])
                                print("[REGISTROS] 1")

            if len(lista_submanuais) > 0:
                print(f"  Fechando a sanfona do manual '{nome_manual}'...")
                clicar_menu_exato(navegador, nome_manual)
                time.sleep(1)

        print("\nRASPAGEM DO PACOTE SIMPLUS CONCLUÍDA!")

    except Exception as e:
        print(f"Ocorreu um erro na extração do Simplus: {e}")
