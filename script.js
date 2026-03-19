const API_URL = 'https://tenis-stats-production.up.railway.app/api';

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
        ['select-ano-campanha'].forEach(id => {
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

// Guarda referência do gráfico atual para destruir antes de recriar
let graficoPiso = null;

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
            <p class="trofeus-dica">ℹ️ Passe o mouse sobre um título para ver os detalhes</p>
            <div class="trofeus-grid" id="trofeus-grid"></div>
        </div>
        <div class="grafico-superficie">
            <h3>📊 Desempenho por Superfície</h3>
            <div class="grafico-wrapper">
                <canvas id="canvas-superficie"></canvas>
            </div>
        </div>
        <div class="secao-temporada">
            <div class="temporada-header">
                <h3>🗓️ Ver Temporada</h3>
                <div class="temporada-controles">
                    <select id="select-ano-temporada"><option value="">Selecione o ano...</option></select>
                    <button id="btn-buscar-temporada">Ver</button>
                </div>
            </div>
            <div id="area-resultado-temporada"></div>
        </div>
    `;
    area.style.display = 'block';

    // Busca os títulos detalhados e monta o grid com tooltips
    const NIVEL_CHAVE  = { G: 'Grand Slam', F: 'ATP Finals', M: 'Masters 1000', A: 'ATP 500/250', C: 'Challengers' };
    const grid = document.getElementById('trofeus-grid');
    if (grid) {
        // Renderiza imediatamente com os totais (sem tooltip ainda)
        ['G','F','M','A','C'].forEach(chave => {
            const qtd = dados.titulos[chave] || 0;
            const div = document.createElement('div');
            div.className = 'trofeu-item' + (qtd > 0 ? ' trofeu-clicavel' : '');
            div.dataset.chave = chave;
            div.innerHTML = qtd > 0
                ? `<strong>${NIVEL_CHAVE[chave]}:</strong> <span class="trofeu-qtd">${qtd} <span class="trofeu-hint">▴</span></span>`
                : `<strong>${NIVEL_CHAVE[chave]}:</strong> <span class="trofeu-zero">0</span>`;
            grid.appendChild(div);
        });

        // Busca os detalhes e adiciona tooltips nos itens com títulos
        apiFetch(`${API_URL}/titulos/${encodeURIComponent(dados.nome)}`)
            .then(titulos => {
                // Tooltip compartilhado — um único elemento no body, reposicionado no hover
                let tooltip = document.getElementById('trofeu-tooltip-global');
                if (!tooltip) {
                    tooltip = document.createElement('div');
                    tooltip.id = 'trofeu-tooltip-global';
                    tooltip.className = 'trofeu-tooltip';
                    document.body.appendChild(tooltip);
                }

                grid.querySelectorAll('.trofeu-clicavel').forEach(div => {
                    const chave = div.dataset.chave;
                    const lista = titulos[chave];
                    if (!lista || lista.length === 0) return;

                    const linhas = lista.map(t => `🏆 ${t.torneio} — ${t.ano}`).join('<br>');

                    div.addEventListener('mouseenter', () => {
                        tooltip.innerHTML = linhas;
                        tooltip.classList.add('visivel');

                        // Posiciona acima do item, centralizado, dentro da viewport
                        const rect = div.getBoundingClientRect();
                        const tooltipH = Math.min(260, lista.length * 29 + 20);
                        const top = Math.max(8, rect.top - tooltipH - 8);
                        const left = rect.left + rect.width / 2;

                        tooltip.style.top       = `${top}px`;
                        tooltip.style.left      = `${left}px`;
                        tooltip.style.transform = 'translateX(-50%)';

                        requestAnimationFrame(() => {
                            const tRect = tooltip.getBoundingClientRect();
                            if (tRect.right > window.innerWidth - 8)
                                tooltip.style.left = `${window.innerWidth - tRect.width / 2 - 8}px`;
                            if (tRect.left < 8)
                                tooltip.style.left = `${tRect.width / 2 + 8}px`;
                        });
                    });

                    // Só esconde quando o mouse sair do item E não estiver sobre o tooltip
                    div.addEventListener('mouseleave', () => {
                        setTimeout(() => {
                            if (!tooltip.matches(':hover')) {
                                tooltip.classList.remove('visivel');
                            }
                        }, 80);
                    });

                    tooltip.addEventListener('mouseleave', () => {
                        tooltip.classList.remove('visivel');
                    });
                });
            })
            .catch(() => {}); // falha silenciosa — os totais já estão visíveis
    }

    // Destrói gráfico anterior se existir (evita duplicação ao buscar outro jogador)
    if (graficoPiso) { graficoPiso.destroy(); graficoPiso = null; }

    const sup = dados.desempenho_por_superficie;
    const labels = Object.keys(sup);

    if (labels.length === 0) return;

    const COR_VITORIA  = '#28a745';
    const COR_DERROTA  = '#dc3545';
    const COR_V_ALPHA  = 'rgba(40, 167, 69, 0.15)';
    const COR_D_ALPHA  = 'rgba(220, 53, 69, 0.15)';

    // Popular o select de anos da temporada diretamente do select de campanha
    // (ambos têm os mesmos anos carregados da API)
    const selectTemporada = document.getElementById('select-ano-temporada');
    const selectCampanha  = document.getElementById('select-ano-campanha');
    if (selectCampanha && selectTemporada) {
        selectTemporada.innerHTML = selectCampanha.innerHTML;
    }

    // Handler do botão Ver Temporada — usa closure para capturar o nome do jogador atual
    const nomeJogadorAtual = dados.nome;
    document.getElementById('btn-buscar-temporada').addEventListener('click', async () => {
        const ano = document.getElementById('select-ano-temporada').value;
        if (!ano) return;

        const areaTemp = document.getElementById('area-resultado-temporada');
        areaTemp.innerHTML = '<p class="temporada-carregando">Buscando temporada...</p>';

        try {
            const temp = await apiFetch(`${API_URL}/temporada/${encodeURIComponent(nomeJogadorAtual)}/${ano}`);
            renderizarTemporada(temp, areaTemp);
        } catch (err) {
            areaTemp.innerHTML = `<p class="msg-erro">⚠️ ${err.message}</p>`;
        }
    });

    graficoPiso = new Chart(document.getElementById('canvas-superficie'), {
        type: 'bar',
        data: {
            labels,
            datasets: [
                {
                    label: 'Vitórias',
                    data: labels.map(l => sup[l].vitorias),
                    backgroundColor: COR_V_ALPHA,
                    borderColor: COR_VITORIA,
                    borderWidth: 2,
                    borderRadius: 6,
                },
                {
                    label: 'Derrotas',
                    data: labels.map(l => sup[l].derrotas),
                    backgroundColor: COR_D_ALPHA,
                    borderColor: COR_DERROTA,
                    borderWidth: 2,
                    borderRadius: 6,
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: { position: 'top' },
                tooltip: {
                    callbacks: {
                        afterLabel(ctx) {
                            const piso = labels[ctx.dataIndex];
                            const v = sup[piso].vitorias;
                            const d = sup[piso].derrotas;
                            const apr = Math.round((v / (v + d)) * 100);
                            return `Aproveitamento: ${apr}%`;
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: { precision: 0 },
                    grid: { color: 'rgba(0,0,0,0.05)' }
                },
                x: {
                    grid: { display: false }
                }
            }
        }
    });
}


// ABA 2: Buscar Torneio — histórico completo
document.getElementById('btn-buscar-torneio').addEventListener('click', async () => {
    const torneio = document.getElementById('input-torneio').value.trim();
    if (!torneio) return mostrarErro('area-resultado-torneio', 'Digite o nome do torneio!');

    setBotaoCarregando('btn-buscar-torneio', true);
    limparResultado('area-resultado-torneio');

    try {
        const dados = await apiFetch(`${API_URL}/torneio/${encodeURIComponent(torneio)}`);
        const area = document.getElementById('area-resultado-torneio');

        const edicoesHtml = dados.edicoes.map(e => `
            <div class="edicao-item">
                <span class="edicao-ano">${e.ano}</span>
                <div class="edicao-jogadores">
                    <span class="edicao-campeao">🏆 ${e.campeao}</span>
                    <span class="edicao-vice">🥈 ${e.vice}</span>
                </div>
                <span class="edicao-placar">${e.placar}</span>
            </div>`
        ).join('');

        area.innerHTML = `
            <h2 class="torneio-historico-titulo">${dados.torneio_oficial}</h2>
            <p class="torneio-historico-sub">${dados.edicoes.length} edições encontradas</p>
            <div class="edicoes-lista">${edicoesHtml}</div>
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

        function linhasPartidas(lista) {
            return lista.map(p => {
                const cls = p.resultado === 'V' ? 'cor-vitoria' : 'cor-derrota';
                const txt = p.resultado === 'V' ? 'Vitória sobre' : 'Derrota para';
                return `
                    <div class="partida-campanha-item">
                        <strong>${p.rodada}</strong>:
                        <span class="${cls} negrito">${txt}</span> ${p.oponente}
                        <br><em>Placar: ${p.placar}</em>
                    </div>`;
            }).join('');
        }

        let html = '';

        // Qualifying — só mostra se existir
        if (dados.qualifying && dados.qualifying.length > 0) {
            html += `<p class="secao-label">── Qualificatória ──</p>`;
            html += linhasPartidas(dados.qualifying);
        }

        // Main draw — com badge de entrada especial se houver
        if (dados.partidas && dados.partidas.length > 0) {
            const badge = dados.entrada_especial
                ? `<span class="badge-entrada">${dados.entrada_especial}</span>`
                : '';
            html += `<p class="secao-label">── Torneio Principal ${badge} ──</p>`;
            html += linhasPartidas(dados.partidas);
        }

        const area = document.getElementById('area-resultado-campanha');
        area.innerHTML = `
            <h2>${dados.jogador} em ${dados.torneio} (${dados.ano})</h2>
            ${bannerCampeao}
            ${html}
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


// ==========================================
// 6. RENDERIZAR TEMPORADA
// ==========================================
function renderizarTemporada(temp, container) {
    const resumoHtml = `
        <div class="temporada-resumo">
            <div class="temporada-resumo-item">
                <span class="stat-label">Torneios</span>
                <span class="stat-value">${temp.total_torneios}</span>
            </div>
            <div class="temporada-resumo-item">
                <span class="stat-label">Vitórias</span>
                <span class="stat-value cor-vitoria">${temp.total_vitorias}</span>
            </div>
            <div class="temporada-resumo-item">
                <span class="stat-label">Derrotas</span>
                <span class="stat-value cor-derrota">${temp.total_derrotas}</span>
            </div>
            <div class="temporada-resumo-item">
                <span class="stat-label">Títulos</span>
                <span class="stat-value">${temp.titulos > 0 ? '🏆 ' + temp.titulos : temp.titulos}</span>
            </div>
        </div>`;

    const torneiosHtml = temp.torneios.map((t, i) => {
        const classeCampeao = t.campeao ? 'torneio-item campeao' : 'torneio-item';
        const badge = t.campeao
            ? '<span class="badge-campeao">🏆 Campeão</span>'
            : t.so_qualifying
                ? '<span class="badge-qualifying">Q</span>'
                : '';
        const placar = t.so_qualifying ? '' : `<span class="torneio-placar">${t.vitorias}V-${t.derrotas}D</span>`;
        return `
            <div class="${classeCampeao} torneio-clicavel" data-index="${i}" data-torneio="${encodeURIComponent(t.torneio)}">
                <div class="torneio-info">
                    <strong>${t.torneio}</strong>
                    <span class="torneio-meta">${t.nivel} · ${t.superficie}</span>
                </div>
                <div class="torneio-resultado">
                    ${badge}
                    ${placar}
                    <span class="torneio-rodada">${t.resultado}</span>
                    <span class="torneio-seta">▼</span>
                </div>
            </div>
            <div class="torneio-detalhe" id="detalhe-${i}"></div>`;
    }).join('');

    container.innerHTML = resumoHtml + torneiosHtml;

    // Adiciona evento de clique em cada torneio
    container.querySelectorAll('.torneio-clicavel').forEach(el => {
        el.addEventListener('click', async () => {
            const idx     = el.dataset.index;
            const nomeTorneio = decodeURIComponent(el.dataset.torneio);
            const detalhe = document.getElementById(`detalhe-${idx}`);
            const seta    = el.querySelector('.torneio-seta');

            // Acordeão: fecha se já está aberto
            if (detalhe.classList.contains('aberto')) {
                detalhe.classList.remove('aberto');
                detalhe.innerHTML = '';
                seta.textContent = '▼';
                el.classList.remove('ativo');
                return;
            }

            // Fecha qualquer outro aberto
            container.querySelectorAll('.torneio-detalhe.aberto').forEach(d => {
                d.classList.remove('aberto');
                d.innerHTML = '';
            });
            container.querySelectorAll('.torneio-clicavel.ativo').forEach(e => {
                e.classList.remove('ativo');
                e.querySelector('.torneio-seta').textContent = '▼';
            });

            el.classList.add('ativo');
            seta.textContent = '▲';
            detalhe.classList.add('aberto');
            detalhe.innerHTML = '<p class="temporada-carregando">Buscando partidas...</p>';

            try {
                const campanha = await apiFetch(
                    `${API_URL}/campanha/${encodeURIComponent(temp.jogador)}/${encodeURIComponent(nomeTorneio)}/${temp.ano}`
                );

                function linhasPartidas(partidas) {
                    return partidas.map(p => {
                        const cls = p.resultado === 'V' ? 'cor-vitoria' : 'cor-derrota';
                        const txt = p.resultado === 'V' ? 'Vitória sobre' : 'Derrota para';
                        return `
                            <div class="detalhe-partida">
                                <span class="detalhe-rodada">${p.rodada}</span>
                                <span class="detalhe-resultado ${cls}">${txt}</span>
                                <span class="detalhe-oponente">${p.oponente}</span>
                                <span class="detalhe-placar">${p.placar}</span>
                            </div>`;
                    }).join('');
                }

                let html = '';

                // Seção qualifying
                if (campanha.qualifying && campanha.qualifying.length > 0) {
                    html += `<div class="detalhe-secao-label">Qualificatória</div>`;
                    html += linhasPartidas(campanha.qualifying);
                }

                // Seção main draw
                if (campanha.partidas && campanha.partidas.length > 0) {
                    const badge = campanha.entrada_especial
                        ? `<span class="badge-entrada">${campanha.entrada_especial}</span>`
                        : '';
                    html += `<div class="detalhe-secao-label">Torneio Principal ${badge}</div>`;
                    html += linhasPartidas(campanha.partidas);
                }

                detalhe.innerHTML = html || '<p class="temporada-carregando">Sem partidas encontradas.</p>';
            } catch (err) {
                detalhe.innerHTML = `<p class="msg-erro">⚠️ ${err.message}</p>`;
            }
        });
    });
}