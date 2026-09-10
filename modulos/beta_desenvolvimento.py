import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from utils import clicar_menu_exato, extrair_numero_capitulo
from modulos.capitulos import extrair_indices 

NOME_PACOTE = "Simplus"
ICONE_PACOTE = "simplus"
MANUAL_COM_VARREDURA_COMPLETA_DE_INDICES = "CÓDIGO DE FALHAS"
MAX_TENTATIVAS_INDICES = 6

def criar_aba_manual(wb, nome_manual, profundidade):
    """Cria uma aba de relatório segura para o manual em processamento."""
    caracteres_invalidos = '\\/*?:[]'
    nome_aba = "Simplus - " + ''.join(
        '-' if caractere in caracteres_invalidos else caractere
        for caractere in nome_manual
    )
    aba = wb.create_sheet(nome_aba[:31])

    if profundidade == "modelos":
        aba.append(['Pacote', 'Manual', 'Submanual', 'Montadora', 'Modelo'])
    elif profundidade == "indices":
        aba.append(['Pacote', 'Manual', 'Submanual', 'Montadora', 'Modelo', 'Índice'])
    elif profundidade == "capitulos":
        aba.append(['Pacote', 'Manual', 'Submanual', 'Montadora', 'Modelo', 'Qtd Índices', 'Índice', 'Capítulo'])
    return aba

def rodar(navegador, wb, profundidade="capitulos", status_global=None):
    """Executa a varredura específica do pacote Beta (desenvolvimento)."""
    nome_pacote = NOME_PACOTE
    icone_pacote = ICONE_PACOTE
    try:
        print(f"Garantindo pacote '{nome_pacote}'...")
        botao_pacote = WebDriverWait(navegador, 10).until(
            EC.element_to_be_clickable((By.XPATH, f"//img[@alt='{icone_pacote}']"))
        )
        navegador.execute_script("arguments[0].click();", botao_pacote)
        time.sleep(3) 

        estrutura_manuais = {
            "INJEÇÃO ELETRÔNICA": [],
            "ABS/ASR/ESP": [],
            "CÂMBIO": [],
            "CLIMACAR": [],
            "CÓDIGO DE FALHAS": [],
            "ELECTRA": [],
            "LOCAR": [],
            "LUBRITEC": [],
            "MIX": ["AIRBAG", "ALARMES", "IMOBILIZADOR", "RESETS"],
            "MOTORES": ["LINHA LEVE"],
            "OSCI": ["MT PRO", "PICO SCOPE"],
            "REVISA CAR": [],
            "SINCRO": ["CORREIAS", "CORRENTES", "POLY-V"],
            "TORKS": [],
        }
        manuais_disponiveis = list(estrutura_manuais.keys())
        manuais_alvo = manuais_disponiveis
        if status_global is not None:
            print(f"\n{'='*50}")
            print(" BETA (DESENVOLVIMENTO): SELECIONE O MODO")
            print(f"{'='*50}")
            print("[0] - Sem Injeção")
            print("[1] - Com Injeção")
            print("[2] - Manual específico")
            print("\n>>> O robô foi pausado. Aguardando a sua digitação no painel...")
            status_global["aguardando_input"] = True
            while status_global["resposta_input"] is None:
                time.sleep(1)

            resposta_usuario = status_global["resposta_input"]
            status_global["aguardando_input"] = False
            status_global["resposta_input"] = None
            if resposta_usuario == "0":
                manuais_alvo = [manual for manual in manuais_disponiveis if manual != "INJEÇÃO ELETRÔNICA"]
                print("\n=> Opção [0]: varrendo todos os manuais, sem INJEÇÃO ELETRÔNICA.")
            elif resposta_usuario == "1":
                print("\n=> Opção [1]: varrendo todos os manuais, com INJEÇÃO ELETRÔNICA.")
            elif resposta_usuario == "2":
                print("\nSELECIONE O MANUAL ESPECÍFICO:")
                for indice, manual in enumerate(manuais_disponiveis, 1):
                    print(f"[{indice}] - {manual}")
                print("\n>>> Aguardando a seleção do manual no painel...")
                status_global["aguardando_input"] = True
                while status_global["resposta_input"] is None:
                    time.sleep(1)

                resposta_manual = status_global["resposta_input"]
                status_global["aguardando_input"] = False
                status_global["resposta_input"] = None
                try:
                    indice_manual = int(resposta_manual)
                    if not 1 <= indice_manual <= len(manuais_disponiveis):
                        raise ValueError
                    manuais_alvo = [manuais_disponiveis[indice_manual - 1]]
                    print(f"\n=> Manual selecionado: {manuais_alvo[0]}.")
                except (ValueError, IndexError):
                    manuais_alvo = []
                    print("\n=> Manual inválido. Nenhuma varredura será executada.")
            else:
                manuais_alvo = []
                print("\n=> Opção inválida. Nenhuma varredura será executada.")
        
        estrutura_filtrada = {k: v for k, v in estrutura_manuais.items() if k in manuais_alvo}

        abas_beta = []
        montadoras_selecionadas = None
        for nome_manual, lista_submanuais in estrutura_filtrada.items():
            aba = criar_aba_manual(wb, nome_manual, profundidade)
            abas_beta.append(aba)
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
                montadoras_alvo = montadoras_selecionadas or nomes_disponiveis

                if (montadoras_selecionadas is not None
                        and not any(nome in nomes_disponiveis for nome in montadoras_selecionadas)):
                    print(f"  [AVISO] A montadora selecionada não está disponível em '{manual_texto_log}'. Pulando...")
                    continue
                
                if (profundidade in ["indices", "capitulos"]
                        and status_global is not None
                        and montadoras_selecionadas is None):
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
                
                if profundidade in ["indices", "capitulos"] and status_global is not None:
                    montadoras_selecionadas = montadoras_alvo

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
                                    verificar_todos_indices = (
                                        nome_manual == MANUAL_COM_VARREDURA_COMPLETA_DE_INDICES
                                    )
                                    indices_para_verificar = (
                                        lista_indices[:MAX_TENTATIVAS_INDICES]
                                        if verificar_todos_indices else lista_indices[:1]
                                    )
                                    if verificar_todos_indices:
                                        print(
                                            f"  >>> {qtd_indices} índices encontrados. Verificando no máximo "
                                            f"{MAX_TENTATIVAS_INDICES} índices, até obter uma resposta do OCR..."
                                        )
                                    else:
                                        print(
                                            f"  >>> {qtd_indices} índices encontrados. "
                                            "Verificando somente o primeiro índice deste manual."
                                        )
                                    xpath_indices = "//div[contains(@class, 'index-menu-item')]"

                                    for indice_alvo in indices_para_verificar:
                                        try:
                                            # O DOM é reconstruído quando o capítulo é fechado; por isso,
                                            # relocaliza o item pelo texto antes de cada tentativa.
                                            elemento_indice = None
                                            for candidato in navegador.find_elements(By.XPATH, xpath_indices):
                                                try:
                                                    texto_indice = candidato.find_element(
                                                        By.XPATH,
                                                        ".//span[contains(@class, 'label')]"
                                                    ).text.strip()
                                                    if texto_indice == indice_alvo:
                                                        elemento_indice = candidato
                                                        break
                                                except:
                                                    continue

                                            if elemento_indice is None:
                                                raise RuntimeError(f"Índice não encontrado no menu: {indice_alvo}")

                                            navegador.execute_script(
                                                "arguments[0].scrollIntoView({block: 'center'});",
                                                elemento_indice
                                            )
                                            navegador.execute_script("arguments[0].click();", elemento_indice)
                                            print(f"  [AGUARDANDO] Carregando capítulo do índice: {indice_alvo}")

                                            xpath_imagem_capitulo = "//img[@alt='manual']"
                                            img_capitulo = WebDriverWait(navegador, 40).until(
                                                EC.visibility_of_element_located((By.XPATH, xpath_imagem_capitulo))
                                            )
                                            numero_cap = extrair_numero_capitulo(navegador, img_capitulo)

                                            aba.append([
                                                'Simplus', nome_manual, nome_submanual, nome_montadora,
                                                nome_modelo, qtd_indices, indice_alvo, numero_cap
                                            ])
                                            print(
                                                f"[{manual_texto_log}] -> [{nome_montadora}] -> [{nome_modelo}] "
                                                f"-> [{indice_alvo}] -> CAP: {numero_cap}"
                                            )
                                            print("[REGISTROS] 1")

                                            # Uma resposta do OCR, inclusive NÃO_LIDO, conclui a consulta do modelo.
                                            break

                                        except Exception as erro_cap:
                                            # Timeout ou capítulo quebrado: registra a falha e segue para o
                                            # próximo índice do mesmo modelo.
                                            aba.append([
                                                'Simplus', nome_manual, nome_submanual, nome_montadora,
                                                nome_modelo, qtd_indices, indice_alvo, 'NÃO_LIDO'
                                            ])
                                            print(
                                                f"  [AVISO] Índice '{indice_alvo}' não carregou em até 40s "
                                                f"ou falhou: {erro_cap}. Tentando o próximo..."
                                            )
                                            print("[REGISTROS] 1")

                                        finally:
                                            # Depois de cada índice (inclusive em timeout), restaura o painel
                                            # para que o próximo item possa ser localizado.
                                            try:
                                                xpath_setinha = "//img[@alt='arrow-navigator']"
                                                btn_setinha = WebDriverWait(navegador, 5).until(
                                                    EC.element_to_be_clickable((By.XPATH, xpath_setinha))
                                                )
                                                navegador.execute_script("arguments[0].click();", btn_setinha)
                                                time.sleep(2)
                                            except:
                                                pass

                                else:
                                    aba.append(['Simplus', nome_manual, nome_submanual, nome_montadora, nome_modelo, 0, "-", "-"])
                                    print(f"[{manual_texto_log}] -> [{nome_montadora}] -> [{nome_modelo}] -> 0 ÍNDICES")
                                    print("[REGISTROS] 1")
                            else:
                                print(f"  [Aviso] Painel de índices não abriu para {nome_modelo}")
                                aba.append(['Simplus', nome_manual, nome_submanual, nome_montadora, nome_modelo, "ERRO NO CLIQUE", "-", "-"])
                                print("[REGISTROS] 1")

            if len(lista_submanuais) > 0:
                print(f"  Fechando a sanfona do manual '{nome_manual}'...")
                clicar_menu_exato(navegador, nome_manual)
                time.sleep(1)

        for aba_beta in abas_beta:
            for linha in aba_beta.iter_rows(min_row=2, max_col=1):
                linha[0].value = nome_pacote

        print(f"\nRASPAGEM DO PACOTE {nome_pacote.upper()} CONCLUÍDA!")

    except Exception as e:
        print(f"Ocorreu um erro na extração do {nome_pacote}: {e}")
