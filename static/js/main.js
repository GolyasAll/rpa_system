function alternarTema() {
    const html = document.documentElement;
    html.classList.toggle('dark');
    if (html.classList.contains('dark')) {
        localStorage.setItem('temaSimplo', 'dark');
    } else {
        localStorage.setItem('temaSimplo', 'light');
    }
}

if (localStorage.getItem('temaSimplo') === 'dark' || (!('temaSimplo' in localStorage) && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
    document.documentElement.classList.add('dark');
} else {
    document.documentElement.classList.remove('dark');
}

let intervaloMonitoramento = null;
let autoScroll = true;

document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById('form-coleta');
    const btnIniciar = document.getElementById('btn-start'); 
    const terminalOutput = document.getElementById('terminal-output');
    const terminalContainer = document.getElementById('terminal-container');
    const containerInterativo = document.getElementById('container-interativo');
    const inputInterativo = document.getElementById('input-interativo');
    const btnEnviarInput = document.getElementById('btn-enviar-input');
    const checkboxBeta = document.getElementById('pkg-beta');
    const grupoProfundidade = document.getElementById('grupo-profundidade');
    const tituloProfundidade = document.getElementById('titulo-profundidade');
    const opcoesProfundidade = document.querySelectorAll('input[name="profundidade"]');

    function atualizarProfundidadeParaBeta() {
        const betaSelecionado = checkboxBeta?.checked ?? false;

        opcoesProfundidade.forEach((opcao) => {
            opcao.disabled = betaSelecionado;
        });
        grupoProfundidade?.classList.toggle('opacity-40', betaSelecionado);
        grupoProfundidade?.classList.toggle('pointer-events-none', betaSelecionado);
        tituloProfundidade?.classList.toggle('opacity-40', betaSelecionado);
        grupoProfundidade?.setAttribute('aria-disabled', String(betaSelecionado));
    }

    checkboxBeta?.addEventListener('change', atualizarProfundidadeParaBeta);
    atualizarProfundidadeParaBeta();

    if (terminalContainer) {
        terminalContainer.addEventListener('scroll', () => {
            const isAtBottom = terminalContainer.scrollHeight - terminalContainer.scrollTop <= terminalContainer.clientHeight + 10;
            autoScroll = isAtBottom;
        });
    }

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const formData = new FormData(form);
        
        btnIniciar.disabled = true;
        btnIniciar.innerHTML = "PROCESSANDO...";
        
        try {
            const response = await fetch('/iniciar_coleta', {
                method: 'POST',
                body: formData
            });
            
            if (response.ok) {
                ligarMonitoramento();
            } else {
                const result = await response.json();
                alert("Erro: " + result.erro);
                resetarBotao();
            }
        } catch (error) {
            alert("Falha de conexão com o servidor.");
            resetarBotao();
        }
    });

    function ligarMonitoramento() {
        if (intervaloMonitoramento) clearInterval(intervaloMonitoramento);
        
        intervaloMonitoramento = setInterval(async () => {
            try {
                const response = await fetch('/obter_status');
                const dados = await response.json();
                
                const statusTexto = document.getElementById('status-texto');
                const statusIndicador = document.getElementById('status-indicador');
                if (dados.processando) {
                    statusTexto.innerText = "Em Execução";
                    statusTexto.className = "font-bold text-sm text-emerald-500";
                    statusIndicador.className = "w-3 h-3 rounded-full bg-emerald-500 animate-pulse";
                } else {
                    statusTexto.innerText = "Sistema Ocioso";
                    statusTexto.className = "font-bold text-sm text-slate-500 dark:text-slate-400";
                    statusIndicador.className = "w-3 h-3 rounded-full bg-rose-500";
                }

                if (dados.processando && dados.tempo_inicio) {
                    const agora = Math.floor(Date.now() / 1000);
                    const diff = agora - Math.floor(dados.tempo_inicio);
                    const horas = String(Math.floor(diff / 3600)).padStart(2, '0');
                    const minutos = String(Math.floor((diff % 3600) / 60)).padStart(2, '0');
                    const segundos = String(diff % 60).padStart(2, '0');
                    document.getElementById('telemetria-tempo').innerText = `${horas}:${minutos}:${segundos}`;
                }

                document.getElementById('telemetria-manual').innerText = dados.manual_atual || "-";
                document.getElementById('telemetria-montadora').innerText = dados.montadora_atual || "-";
                document.getElementById('telemetria-modelos').innerText = dados.modelos_coletados || "0";
                
                const containerProgresso = document.getElementById('container-progresso');
                if (dados.montadora_atual_total > 0) {
                    containerProgresso.classList.remove('opacity-0');
                    document.getElementById('telemetria-progresso-atual').innerText = dados.montadora_atual_coletados;
                    document.getElementById('telemetria-progresso-total').innerText = dados.montadora_atual_total;
                } else {
                    containerProgresso.classList.add('opacity-0');
                }

                if (dados.logs && dados.logs.length > 0 && terminalOutput) {
                    terminalOutput.innerHTML = dados.logs.map(log => {
                        if (log.includes("[SUCESSO]")) return `<div class="text-emerald-400">${log}</div>`;
                        if (log.includes("[AVISO]") || log.includes("[ALERTA]")) return `<div class="text-yellow-400">${log}</div>`;
                        if (log.includes("[ERRO]") || log.includes("CRITICAL")) return `<div class="text-red-400 font-bold">${log}</div>`;
                        if (log.startsWith("=>") || log.startsWith(">>>")) return `<div class="text-blue-400">${log}</div>`;
                        if (log.includes("[MANUAL]") || log.includes("[MONTADORA]")) return `<div class="text-purple-400 font-semibold mt-2">${log}</div>`;
                        return `<div>${log}</div>`;
                    }).join('');
                    
                    if (autoScroll && terminalContainer) {
                        terminalContainer.scrollTop = terminalContainer.scrollHeight;
                    }
                }

                if (dados.aguardando_input) {
                    containerInterativo.classList.remove('hidden');
                    inputInterativo.focus();
                } else {
                    containerInterativo.classList.add('hidden');
                }

                if (!dados.processando && dados.tempo_inicio !== null && dados.manual_atual !== "Inicializando...") {
                    clearInterval(intervaloMonitoramento);
                    resetarBotao();
                }
                
            } catch (error) {
                console.error("Erro ao puxar telemetria do servidor:", error);
            }
        }, 1000); 
    }

    function resetarBotao() {
        btnIniciar.disabled = false;
        btnIniciar.innerHTML = `INICIAR COLETA`;
    }

    if (btnEnviarInput && inputInterativo) {
        btnEnviarInput.addEventListener('click', enviarResposta);
        inputInterativo.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') enviarResposta();
        });
    }

    async function enviarResposta() {
        const valor = inputInterativo.value;
        if (!valor) return;
        
        btnEnviarInput.disabled = true;
        inputInterativo.disabled = true;
        
        try {
            await fetch('/enviar_resposta', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ resposta: valor })
            });
            inputInterativo.value = '';
        } finally {
            btnEnviarInput.disabled = false;
            inputInterativo.disabled = false;
            containerInterativo.classList.add('hidden');
        }
    }
});
