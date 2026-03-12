const API_URL = 'http://127.0.0.1:5000/api';

// ==========================================
// 1. CONTROLE DAS ABAS E NAVEGAÇÃO
// ==========================================
const botoes = document.querySelectorAll('.aba');
const secoes = document.querySelectorAll('.secao');

botoes.forEach(botao => {
    botao.addEventListener('click', () => {
        botoes.forEach(b => b.classList.remove('ativa'));
        secoes.forEach(s => { s.classList.add('oculta'); s.style.display = 'none'; });
        
        botao.classList.add('ativa');
        const idSecao = botao.id.replace('aba-', 'secao-');
        document.getElementById(idSecao).classList.remove('oculta');
        document.getElementById(idSecao).style.display = 'block';
    });
});

// ==========================================
// 2. AUTOCOMPLETE UNIVERSAL
// ==========================================
function ativarSugestoes(idInput, idLista, endpoint) {
    const input = document.getElementById(idInput);
    const lista = document.getElementById(idLista);
    if(!input || !lista) return;

    input.addEventListener('input', () => {
        const txt = input.value.trim();
        if(txt.length < 2) { lista.innerHTML = ''; return; }
        
        fetch(`${API_URL}/${endpoint}/${txt}`)
            .then(r => r.json())
            .then(dados => {
                lista.innerHTML = '';
                dados.forEach(item => {
                    const div = document.createElement('div');
                    div.textContent = item;
                    div.style.padding = '10px';
                    div.style.cursor = 'pointer';
                    div.style.borderBottom = '1px solid #eee';
                    div.style.backgroundColor = 'white';
                    div.addEventListener('click', () => { input.value = item; lista.innerHTML = ''; });
                    div.addEventListener('mouseover', () => div.style.backgroundColor = '#f1f1f1');
                    div.addEventListener('mouseout', () => div.style.backgroundColor = 'white');
                    lista.appendChild(div);
                });
            });
    });
    document.addEventListener('click', e => { if(e.target !== input) lista.innerHTML = ''; });
}

ativarSugestoes('input-jogador', 'lista-sugestoes', 'sugestoes');
ativarSugestoes('input-torneio', 'lista-sugestoes-torneio', 'sugestoes_torneio');
ativarSugestoes('input-campanha-jogador', 'lista-sugestoes-campanha-jogador', 'sugestoes');
ativarSugestoes('input-campanha-torneio', 'lista-sugestoes-campanha-torneio', 'sugestoes_torneio');
ativarSugestoes('input-h2h-j1', 'sugestoes-h2h-j1', 'sugestoes');
ativarSugestoes('input-h2h-j2', 'sugestoes-h2h-j2', 'sugestoes');

// ==========================================
// 3. PREENCHER ANOS NOS SELECTS
// ==========================================
fetch(`${API_URL}/anos`).then(r => r.json()).then(anos => {
    const s1 = document.getElementById('select-ano');
    const s2 = document.getElementById('select-ano-campanha');
    const opcoes = '<option value="">Ano...</option>' + anos.map(a => `<option value="${a}">${a}</option>`).join('');
    if(s1) s1.innerHTML = opcoes;
    if(s2) s2.innerHTML = opcoes;
});

// ==========================================
// 4. FUNCIONALIDADES DE BUSCA (AS 4 ABAS)
// ==========================================

// ABA 1: Buscar Jogador
document.getElementById('btn-buscar-jogador').addEventListener('click', () => {
    const nome = document.getElementById('input-jogador').value.trim();
    if (!nome) return alert('Digite o nome do jogador!');

    fetch(`${API_URL}/jogador/${nome}`)
        .then(res => { if (!res.ok) throw new Error("Jogador não encontrado"); return res.json(); })
        .then(dados => {
            document.getElementById('nome-jogador').textContent = dados.nome;
            document.getElementById('pais-jogador').textContent = dados.pais;
            document.getElementById('mao-jogador').textContent = dados.mao_dominante;
            document.getElementById('vitorias-jogador').textContent = dados.vitorias;
            document.getElementById('derrotas-jogador').textContent = dados.derrotas;
            document.getElementById('aproveitamento-jogador').textContent = dados.aproveitamento;
            document.getElementById('piso-jogador').textContent = dados.piso_favorito;

            document.getElementById('t-g').textContent = dados.titulos.G || 0;
            document.getElementById('t-f').textContent = dados.titulos.F || 0;
            document.getElementById('t-m').textContent = dados.titulos.M || 0;
            document.getElementById('t-a').textContent = dados.titulos.A || 0;
            document.getElementById('t-c').textContent = dados.titulos.C || 0;

            document.getElementById('area-resultado-jogador').style.display = 'block';
        })
        .catch(err => {
            alert(err.message);
            document.getElementById('area-resultado-jogador').style.display = 'none';
        });
});

// ABA 2: Buscar Torneio
document.getElementById('btn-buscar-torneio').addEventListener('click', () => {
    const torneio = document.getElementById('input-torneio').value.trim();
    const ano = document.getElementById('select-ano').value;
    if (!torneio || !ano) return alert('Preencha o torneio e o ano!');

    fetch(`${API_URL}/torneio/${torneio}/${ano}`)
        .then(res => { if (!res.ok) throw new Error("Torneio não encontrado neste ano"); return res.json(); })
        .then(dados => {
            document.getElementById('nome-oficial-torneio').textContent = `${dados.torneio_oficial} (${dados.ano})`;
            document.getElementById('campeao-torneio').textContent = dados.campeao;
            document.getElementById('vice-torneio').textContent = dados.vice;
            document.getElementById('placar-torneio').textContent = dados.placar;
            document.getElementById('area-resultado-torneio').style.display = 'block';
        })
        .catch(err => {
            alert(err.message);
            document.getElementById('area-resultado-torneio').style.display = 'none';
        });
});

// ABA 3: Campanha (AGORA COM AS CORES GARANTIDAS)
document.getElementById('btn-buscar-campanha').addEventListener('click', () => {
    const jogador = document.getElementById('input-campanha-jogador').value.trim();
    const torneio = document.getElementById('input-campanha-torneio').value.trim();
    const ano = document.getElementById('select-ano-campanha').value;
    if (!jogador || !torneio || !ano) return alert('Preencha todos os campos!');

    fetch(`${API_URL}/campanha/${jogador}/${torneio}/${ano}`)
        .then(res => { if (!res.ok) throw new Error("Campanha não encontrada"); return res.json(); })
        .then(dados => {
            document.getElementById('titulo-campanha').textContent = `${dados.jogador} em ${dados.torneio} (${dados.ano})`;
            
            const banner = document.getElementById('banner-campeao');
            banner.style.display = dados.campeao ? 'block' : 'none';

            const lista = document.getElementById('lista-partidas');
            lista.innerHTML = '';
            
            dados.partidas.forEach(p => {
                const item = document.createElement('div');
                item.style.padding = '10px';
                item.style.borderBottom = '1px solid #ccc';
                
                // LÓGICA DE CORES
                const cor = p.resultado === 'V' ? '#28a745' : '#dc3545';
                const textoResultado = p.resultado === 'V' ? 'Vitória sobre' : 'Derrota para';

                item.innerHTML = `
                    <strong>${p.rodada}</strong>: <span style="color: ${cor}; font-weight: bold;">${textoResultado}</span> ${p.oponente} <br>
                    <em>Placar: ${p.placar}</em>
                `;
                lista.appendChild(item);
            });

            document.getElementById('area-resultado-campanha').style.display = 'block';
        })
        .catch(err => {
            alert(err.message);
            document.getElementById('area-resultado-campanha').style.display = 'none';
        });
});

// ABA 4: Head-to-Head (H2H)
document.getElementById('btn-buscar-h2h').addEventListener('click', () => {
    const j1 = document.getElementById('input-h2h-j1').value.trim();
    const j2 = document.getElementById('input-h2h-j2').value.trim();
    if(!j1 || !j2) return alert("Digite o nome dos dois jogadores!");

    fetch(`${API_URL}/head_to_head/${j1}/${j2}`)
        .then(r => { if(!r.ok) throw new Error("Confronto não encontrado"); return r.json(); })
        .then(d => {
            document.getElementById('nome-h2h-j1').textContent = d.jogador1;
            document.getElementById('nome-h2h-j2').textContent = d.jogador2;
            document.getElementById('vitorias-h2h-j1').textContent = d.vitorias_jogador1;
            document.getElementById('vitorias-h2h-j2').textContent = d.vitorias_jogador2;
            
            const divLista = document.getElementById('lista-partidas-h2h');
            divLista.innerHTML = '';
            d.partidas.forEach(p => {
                divLista.innerHTML += `
                <div class="partida-h2h-item">
                    <div>
                        <span style="font-size: 12px; color: #7f8c8d;">${p.ano} - ${p.torneio} (${p.rodada})</span><br>
                        <strong>Vencedor: ${p.vencedor}</strong>
                    </div>
                    <div>
                        ${p.placar}
                    </div>
                </div>`;
            });
            document.getElementById('area-resultado-h2h').style.display = 'block';
        }).catch(err => {
            alert(err.message);
            document.getElementById('area-resultado-h2h').style.display = 'none';
        });
});