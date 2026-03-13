const API_URL = 'http://127.0.0.1:5000/api';

// ==========================================
// 1. FUNÇÕES UTILITÁRIAS
// ==========================================

/**
 * Wrapper de fetch que já trata erros HTTP e de rede de forma padronizada.
 * Retorna o JSON diretamente, ou lança um erro com a mensagem da API.
 */
async function apiFetch(url) {
    const res = await fetch(url);
    const dados = await res.json();
    if (!res.ok) {
        throw new Error(dados.erro || 'Erro desconhecido na requisição.');
    }
    return dados;
}

/**
 * Exibe uma mensagem de erro inline no elemento indicado,
 * em vez de usar alert() que bloqueia a interface.
 */
function mostrarErro(idElemento, mensagem) {
    const el = document.getElementById(idElemento);
    if (!el) return;
    el.innerHTML = `<p class="msg-erro">⚠️ ${mensagem}</p>`;
    el.style.display = 'block';
}

/** Esconde a área de resultado e limpa qualquer erro anterior. */
function limparResultado(idElemento) {
    const el = document.getElementById(idElemento);
    if (!el) return;
    el.style.display = 'none';
    el.innerHTML = '';
}

/** Altera o texto e desabilita/habilita um botão durante o carregamento. */
function setBotaoCarregando(idBotao, carregando) {
    const btn = document.getElementById(idBotao);
    if (!btn) return;
    btn.disabled = carregando;
    btn.textContent = carregando ? 'Buscando...' : btn.dataset.textoOriginal;
}

// Salva o texto original de cada botão de busca para restaurar depois
document.querySelectorAll('button[id^="btn-"]').forEach(btn => {
    btn.dataset.textoOriginal = btn.textContent;
});


// ==========================================
// 2. CONTROLE DAS ABAS E NAVEGAÇÃO
// ==========================================
const botoes = document.querySelectorAll('.aba');
const secoes = document.querySelectorAll('.secao');

botoes.forEach(botao => {
    botao.addEventListener('click', () => {
        botoes.forEach(b => b.classList.remove('ativa'));
        secoes.forEach(s => s.classList.add('oculta'));

        botao.classList.add('ativa');
        const idSecao = botao.id.replace('aba-', 'secao-');
        document.getElementById(idSecao).classList.remove('oculta');
    });
});


// ==========================================
// 3. AUTOCOMPLETE UNIVERSAL
// ==========================================
function ativarSugestoes(idInput, idLista, endpoint) {
    const input = document.getElementById(idInput);
    const lista = document.getElementById(idLista);
    if (!input || !lista) return;

    let debounceTimer = null;

    input.addEventListener('input', () => {
        clearTimeout(debounceTimer);
        const txt = input.value.trim();
        if (txt.length < 2) { lista.innerHTML = ''; return; }

        // Debounce: só busca 300ms após o usuário parar de digitar
        debounceTimer = setTimeout(async () => {
            try {
                const dados = await apiFetch(`${API_URL}/${endpoint}/${encodeURIComponent(txt)}`);
                lista.innerHTML = '';
                dados.forEach(item => {
                    const div = document.createElement('div');
                    div.className = 'sugestao-item';
                    div.textContent = item;
                    div.addEventListener('click', () => { input.value = item; lista.innerHTML = ''; });
                    lista.appendChild(div);
                });
            } catch {
                lista.innerHTML = ''; // falha silenciosa no autocomplete é aceitável
            }
        }, 300);
    });

    document.addEventListener('click', e => { if (e.target !== input) lista.innerHTML = ''; });
}

ativarSugestoes('input-jogador',           'lista-sugestoes',                   'sugestoes');
ativarSugestoes('input-torneio',           'lista-sugestoes-torneio',           'sugestoes_torneio');
ativarSugestoes('input-campanha-jogador',  'lista-sugestoes-campanha-jogador',  'sugestoes');
ativarSugestoes('input-campanha-torneio',  'lista-sugestoes-campanha-torneio',  'sugestoes_torneio');
ativarSugestoes('input-h2h-j1',            'sugestoes-h2h-j1',                  'sugestoes');
ativarSugestoes('input-h2h-j2',            'sugestoes-h2h-j2',                  'sugestoes');


// ==========================================
// 4. PREENCHER ANOS NOS SELECTS
// ==========================================
(async () => {
    try {
        const anos = await apiFetch(`${API_URL}/anos`);
        const opcoes = '<option value="">Ano...</option>' + anos.map(a => `<option value="${a}">${a}</option>`).join('');
        ['select-ano', 'select-ano-campanha'].forEach(id => {
            const el = document.getElementById(id);
            if (el) el.innerHTML = opcoes;
        });
    } catch {
        // Se a API não estiver no ar, mostra aviso nos selects
        ['select-ano', 'select-ano-campanha'].forEach(id => {
            const el = document.getElementById(id);
            if (el) el.innerHTML = '<option value="">API indisponível</option>';
        });
    }
})();


// ==========================================
// 5. FUNCIONALIDADES DE BUSCA (AS 4 ABAS)
// ==========================================

// ABA 1: Buscar Jogador
document.getElementById('btn-buscar-jogador').addEventListener('click', async () => {
    const nome = document.getElementById('input-jogador').value.trim();
    if (!nome) return mostrarErro('area-resultado-jogador', 'Digite o nome do jogador!');

    setBotaoCarregando('btn-buscar-jogador', true);
    limparResultado('area-resultado-jogador');

    try {
        const dados = await apiFetch(`${API_URL}/jogador/${encodeURIComponent(nome)}`);
        renderizarJogador(dados);
    } catch (err) {
        mostrarErro('area-resultado-jogador', err.message);
    } finally {
        setBotaoCarregando('btn-buscar-jogador', false);
    }
});

function renderizarJogador(dados) {
    const area = document.getElementById('area-resultado-jogador');
    const mao = dados.mao_dominante;

    area.innerHTML = `
        <h2>${dados.nome}</h2>
        <p class="info-basica">
            <strong>País:</strong> ${dados.pais}
            <span class="separador">|</span>
            <strong>Mão:</strong> ${mao}
        </p>
        <hr>
        <div class="stats-grid">
            <div>
                <p class="stat-label">Desempenho (Carreira)</p>
                <p class="stat-value">
                    <span class="cor-vitoria">${dados.vitorias}</span>V
                    - <span class="cor-derrota">${dados.derrotas}</span>D
                </p>
            </div>
            <div>
                <p class="stat-label">Aproveitamento</p>
                <p class="stat-value">${dados.aproveitamento}%</p>
            </div>
            <div>
                <p class="stat-label">Piso Favorito</p>
                <p class="stat-value">${dados.piso_favorito}</p>
            </div>
        </div>
        <div class="estante-trofeus">
            <h3>🏆 Títulos Conquistados</h3>
            <div class="trofeus-grid">
                <div class="trofeu-item"><strong>Grand Slam:</strong> ${dados.titulos.G || 0}</div>
                <div class="trofeu-item"><strong>ATP Finals:</strong> ${dados.titulos.F || 0}</div>
                <div class="trofeu-item"><strong>Masters 1000:</strong> ${dados.titulos.M || 0}</div>
                <div class="trofeu-item"><strong>ATP 500/250:</strong> ${dados.titulos.A || 0}</div>
                <div class="trofeu-item"><strong>Challengers:</strong> ${dados.titulos.C || 0}</div>
            </div>
        </div>
    `;
    area.style.display = 'block';
}


// ABA 2: Buscar Torneio
document.getElementById('btn-buscar-torneio').addEventListener('click', async () => {
    const torneio = document.getElementById('input-torneio').value.trim();
    const ano     = document.getElementById('select-ano').value;
    if (!torneio || !ano) return mostrarErro('area-resultado-torneio', 'Preencha o torneio e o ano!');

    setBotaoCarregando('btn-buscar-torneio', true);
    limparResultado('area-resultado-torneio');

    try {
        const dados = await apiFetch(`${API_URL}/torneio/${encodeURIComponent(torneio)}/${ano}`);
        const area = document.getElementById('area-resultado-torneio');
        area.innerHTML = `
            <h2>${dados.torneio_oficial} (${dados.ano})</h2>
            <h3 class="titulo-campeao">🏆 Campeão: ${dados.campeao}</h3>
            <p><strong>🥈 Vice:</strong> ${dados.vice}</p>
            <p><strong>🎾 Placar:</strong> ${dados.placar}</p>
        `;
        area.style.display = 'block';
    } catch (err) {
        mostrarErro('area-resultado-torneio', err.message);
    } finally {
        setBotaoCarregando('btn-buscar-torneio', false);
    }
});


// ABA 3: Campanha
document.getElementById('btn-buscar-campanha').addEventListener('click', async () => {
    const jogador = document.getElementById('input-campanha-jogador').value.trim();
    const torneio = document.getElementById('input-campanha-torneio').value.trim();
    const ano     = document.getElementById('select-ano-campanha').value;
    if (!jogador || !torneio || !ano) return mostrarErro('area-resultado-campanha', 'Preencha todos os campos!');

    setBotaoCarregando('btn-buscar-campanha', true);
    limparResultado('area-resultado-campanha');

    try {
        const dados = await apiFetch(`${API_URL}/campanha/${encodeURIComponent(jogador)}/${encodeURIComponent(torneio)}/${ano}`);

        const bannerCampeao = dados.campeao
            ? `<div class="banner-campeao" style="display:block;">🏆 CAMPEÃO DO TORNEIO! 🏆</div>`
            : '';

        const partidasHtml = dados.partidas.map(p => {
            const classeResultado = p.resultado === 'V' ? 'cor-vitoria' : 'cor-derrota';
            const textoResultado  = p.resultado === 'V' ? 'Vitória sobre' : 'Derrota para';
            return `
                <div class="partida-campanha-item">
                    <strong>${p.rodada}</strong>:
                    <span class="${classeResultado} negrito">${textoResultado}</span> ${p.oponente}
                    <br><em>Placar: ${p.placar}</em>
                </div>`;
        }).join('');

        const area = document.getElementById('area-resultado-campanha');
        area.innerHTML = `
            <h2>${dados.jogador} em ${dados.torneio} (${dados.ano})</h2>
            ${bannerCampeao}
            ${partidasHtml}
        `;
        area.style.display = 'block';
    } catch (err) {
        mostrarErro('area-resultado-campanha', err.message);
    } finally {
        setBotaoCarregando('btn-buscar-campanha', false);
    }
});


// ABA 4: Head-to-Head
document.getElementById('btn-buscar-h2h').addEventListener('click', async () => {
    const j1 = document.getElementById('input-h2h-j1').value.trim();
    const j2 = document.getElementById('input-h2h-j2').value.trim();
    if (!j1 || !j2) return mostrarErro('area-resultado-h2h', 'Digite o nome dos dois jogadores!');

    setBotaoCarregando('btn-buscar-h2h', true);
    limparResultado('area-resultado-h2h');

    try {
        const d = await apiFetch(`${API_URL}/head_to_head/${encodeURIComponent(j1)}/${encodeURIComponent(j2)}`);

        // Linha comparativa de stats
        function linhaComparativa(label, v1, v2, maior_e_melhor = true) {
            const n1 = parseFloat(v1);
            const n2 = parseFloat(v2);
            const j1Vence = maior_e_melhor ? n1 > n2 : n1 < n2;
            const j2Vence = maior_e_melhor ? n2 > n1 : n2 < n1;
            return `
                <div class="stats-comparativas-linha">
                    <span class="stat-comp-valor ${j1Vence ? 'stat-destaque' : ''}">${v1}</span>
                    <span class="stat-comp-label">${label}</span>
                    <span class="stat-comp-valor ${j2Vence ? 'stat-destaque' : ''}">${v2}</span>
                </div>`;
        }

        const s1 = d.stats_jogador1;
        const s2 = d.stats_jogador2;

        const statsHtml = `
            <div class="stats-comparativas">
                <div class="stats-comp-header">
                    <span>${d.jogador1.split(' ').pop()}</span>
                    <span>Estatísticas de Carreira</span>
                    <span>${d.jogador2.split(' ').pop()}</span>
                </div>
                ${linhaComparativa('Vitórias', s1.vitorias, s2.vitorias)}
                ${linhaComparativa('Aproveitamento', s1.aproveitamento + '%', s2.aproveitamento + '%')}
                ${linhaComparativa('Grand Slams 🏆', s1.grand_slams, s2.grand_slams)}
                ${linhaComparativa('ATP Finals', s1.atp_finals, s2.atp_finals)}
                ${linhaComparativa('Masters 1000', s1.masters, s2.masters)}
                ${linhaComparativa('ATP 500/250', s1.atp_500_250, s2.atp_500_250)}
                ${linhaComparativa('Challengers', s1.challengers, s2.challengers)}
                <div class="stats-comparativas-linha">
                    <span class="stat-comp-valor">${s1.piso_favorito}</span>
                    <span class="stat-comp-label">Piso Favorito</span>
                    <span class="stat-comp-valor">${s2.piso_favorito}</span>
                </div>
            </div>`;

        const partidasHtml = d.partidas.map(p => `
            <div class="partida-h2h-item">
                <div>
                    <span class="partida-h2h-meta">${p.ano} - ${p.torneio} (${p.rodada})</span><br>
                    <strong>Vencedor: ${p.vencedor}</strong>
                </div>
                <div>${p.placar}</div>
            </div>`
        ).join('');

        const area = document.getElementById('area-resultado-h2h');
        area.innerHTML = `
            <div class="placar-h2h">
                <div class="lado-h2h">
                    <h2 class="nome-h2h">${d.jogador1}</h2>
                    <div class="pontuacao-h2h">${d.vitorias_jogador1}</div>
                </div>
                <div class="versus-h2h">VS</div>
                <div class="lado-h2h">
                    <h2 class="nome-h2h">${d.jogador2}</h2>
                    <div class="pontuacao-h2h">${d.vitorias_jogador2}</div>
                </div>
            </div>
            ${statsHtml}
            <h3 class="titulo-historico">🎾 Histórico de Confrontos</h3>
            <div id="lista-partidas-h2h">${partidasHtml}</div>
        `;
        area.style.display = 'block';
    } catch (err) {
        mostrarErro('area-resultado-h2h', err.message);
    } finally {
        setBotaoCarregando('btn-buscar-h2h', false);
    }
});
