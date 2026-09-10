from flask import Flask, render_template, request, jsonify
import openpyxl
import threading
import time
import sys
import os
import navegador_base
from modulos import beta_desenvolvimento, simplus

app = Flask(__name__)

# ==============================================================================
# DICIONÁRIO GLOBAL DE TELEMETRIA
# ==============================================================================
status = {
    "processando": False,
    "tempo_inicio": None,
    "manual_atual": "-",
    "montadora_atual": "-",
    "modelos_coletados": 0,
    "montadora_atual_coletados": 0,
    "montadora_atual_total": 0,
    "logs": [],
    "aguardando_input": False,
    "resposta_input": None
}

# ==============================================================================
# CLASSE INTERCEPTADORA AVANÇADA (SEM DUPLICAÇÕES)
# ==============================================================================
class RedirecionadorLogs:
    def __init__(self, terminal_original):
        self.terminal_original = terminal_original

    def write(self, mensagem):
        self.terminal_original.write(mensagem)
        
        texto_limpo = mensagem.strip()
        if not texto_limpo:
            return

        # Comandos internos (não aparecem no terminal)
        if texto_limpo.startswith("[MANUAL]"):
            status["manual_atual"] = texto_limpo.replace("[MANUAL]", "").strip()
            
        elif texto_limpo.startswith("[MONTADORA]"):
            status["montadora_atual"] = texto_limpo.replace("[MONTADORA]", "").strip()
            status["montadora_atual_coletados"] = 0 
            status["montadora_atual_total"] = 0     
            
        elif texto_limpo.startswith("[TOTAL_MODELOS]"):
            try:
                status["montadora_atual_total"] = int(texto_limpo.replace("[TOTAL_MODELOS]", "").strip())
            except:
                pass
            
        elif texto_limpo.startswith("[REGISTROS]"):
            try:
                qtd = int(texto_limpo.replace("[REGISTROS]", "").strip())
                status["modelos_coletados"] += qtd
                status["montadora_atual_coletados"] += qtd
            except:
                pass
            
        # Logs visíveis (com limite de 300 linhas)
        else:
            status["logs"].append(texto_limpo)
            if len(status["logs"]) > 300:
                status["logs"].pop(0)

    def flush(self):
        self.terminal_original.flush()

sys.stdout = RedirecionadorLogs(sys.stdout)

# ==============================================================================
# ROTAS DO FLASK
# ==============================================================================
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/obter_status', methods=['GET'])
def obter_status():
    return jsonify(status)

@app.route('/enviar_resposta', methods=['POST'])
def enviar_resposta():
    data = request.json
    status["resposta_input"] = str(data.get("resposta", "0")).strip()
    return jsonify({"status": "ok"})

@app.route('/iniciar_coleta', methods=['POST'])
def iniciar_coleta():
    if status["processando"]:
        return jsonify({"erro": "O robô já se encontra ativo!"}), 400
    
    data = request.form
    
    status["manual_atual"] = "Inicializando..."
    status["montadora_atual"] = "Autenticando..."
    status["modelos_coletados"] = 0
    status["montadora_atual_coletados"] = 0
    status["montadora_atual_total"] = 0
    status["logs"] = []
    status["tempo_inicio"] = time.time()
    status["aguardando_input"] = False
    status["resposta_input"] = None

    threading.Thread(target=processar_robos, args=(data,)).start()
    return jsonify({"mensagem": "Comando aceito!"})

def processar_robos(data):
    status["processando"] = True
    navegador = None 
    nome_arquivo = data.get('arquivo', 'dados_coletados')
    
    try:
        wb = openpyxl.Workbook()
        wb.remove(wb.active)
        
        headless = 'headless' in data
        email = data['email']
        senha = data['senha']
        profundidade = data.get('profundidade', 'modelos')
        
        navegador = navegador_base.iniciar_sessao(email, senha, headless)
        
        if 'simplus' in data: 
            simplus.rodar(navegador, wb, profundidade, status)

        if 'beta' in data:
            # O Beta define o escopo da coleta no próprio console interativo.
            beta_desenvolvimento.rodar(navegador, wb, "capitulos", status)

        os.makedirs("01 - Relatorios", exist_ok=True)
        caminho_final = os.path.join("01 - Relatorios", f"{nome_arquivo}.xlsx")
        wb.save(caminho_final)
        print(f"Sucesso! Planilha salva em: {caminho_final}")
        
    except Exception as e:
        print(f"CRITICAL ERROR: {str(e)}")
        try:
            os.makedirs("01 - Relatorios", exist_ok=True)
            wb.save(os.path.join("01 - Relatorios", f"{nome_arquivo}_RECUPERADO.xlsx"))
        except: pass
            
    finally:
        if navegador:
            navegador_base.finalizar_sessao(navegador)
        status["processando"] = False
        status["tempo_inicio"] = None

if __name__ == '__main__':
    app.run(port=5002, threaded=True)
