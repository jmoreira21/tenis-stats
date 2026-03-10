// === CARREGAR ANOS NOS DOIS SELECTS (Torneio e Campanha) ===
window.addEventListener('DOMContentLoaded', () => {
    fetch('http://127.0.0.1:5000/api/anos')
        .then(res => res.json())
        .then(anos => {
            const selectTorneio = document.getElementById('select-ano');
            const selectCampanha = document.getElementById('select-ano-campanha');
            selectTorneio.innerHTML = ''; selectCampanha.innerHTML = '';
            
            anos.forEach(ano => {
                selectTorneio.innerHTML += `<option value="${ano}">${ano}</option>`;
                selectCampanha.innerHTML += `<option value="${ano}">${ano}</option>`;
            });
        });
});

// === NAVEGAÇÃO ENTRE AS 3 ABAS ===
const abas = {
    'jogador': { btn: document.getElementById('aba-jogador'), secao: document.getElementById('secao-jogador') },
    'torneio': { btn: document.getElementById('aba-torneio'), secao: document.getElementById('secao-torneio') },
    'campanha': { btn: document.getElementById('aba-campanha'), secao: document.getElementById('secao-campanha') }
};

function trocarAba(abaAtiva) {
    for (const chave in abas) {
        if (chave === abaAtiva) {
            abas[chave].btn.classList.add('ativa');
            abas[chave].secao.classList.remove('oculta');
        } else {
            abas[chave].btn.classList.remove('ativa');
            abas[chave].secao.classList.add('oculta');
        }
    }
}

abas.jogador.btn.addEventListener('click', () => trocarAba('jogador'));
abas.torneio.btn.addEventListener('click', () => trocarAba('torneio'));
abas.campanha.btn.addEventListener('click', () => trocarAba('campanha'));

// === FUNÇÃO REUTILIZÁVEL PARA O AUTOCOMPLETE ===
// Como temos vários campos de texto agora, essa função evita repetir código
function configurarAutocomplete(inputId, listaId, rota) {
    const input = document.getElementById(inputId);
    const lista = document.getElementById(listaId);

    input.addEventListener('input', () => {
        const texto = input.value;
        if (texto.trim() === '') { lista.style.display = 'none'; return; }

        fetch(`http://127.0.0.1:5000/api/${rota}/${texto}`)
            .then(res => res.json())
            .then(itens => {
                lista.innerHTML = '';
                if (itens.length === 0) { lista.style.display = 'none'; return; }
                
                itens.forEach(item => {
                    const div = document.createElement('div');
                    div.className = 'item-sugestao';
                    div.textContent = item;
                    div.addEventListener('click', () => {
                        input.value = item;
                        lista.style.display = 'none';
                    });
                    lista.appendChild(div);
                });
                lista.style.display = 'block';
            });
    });

    // Esconde ao clicar fora
    document.addEventListener('click', (e) => { if (e.target !== input) lista.style.display = 'none'; });
}

// Ativando os autocompletes
configurarAutocomplete('input-jogador', 'lista-sugestoes', 'sugestoes');
configurarAutocomplete('input-torneio', 'lista-sugestoes-torneio', 'sugestoes_torneio');
configurarAutocomplete('input-campanha-jogador', 'lista-sugestoes-campanha-jogador', 'sugestoes');
configurarAutocomplete('input-campanha-torneio', 'lista-sugestoes-campanha-torneio', 'sugestoes_torneio');

// === BUSCA 1: JOGADOR (Igual a antes) ===
document.getElementById('btn-buscar-jogador').addEventListener('click', () => {
    const nome = document.getElementById('input-jogador').value;
    if (nome.trim() === '') return;

    fetch(`http://127.0.0.1:5000/api/jogador/${nome}`)
        .then(res => { if (!res.ok) throw new Error(); return res.json(); })
        .then(dados => {
            document.getElementById('nome-jogador').textContent = dados.nome;
            document.getElementById('pais-jogador').textContent = dados.pais;
            document.getElementById('mao-jogador').textContent = dados.mao_dominante;
            document.getElementById('vitorias-jogador').textContent = dados.vitorias;
            document.getElementById('derrotas-jogador').textContent = dados.derrotas;
            document.getElementById('area-resultado-jogador').style.display = 'block';
        })
        .catch(() => alert('Jogador não encontrado!'));
});

// === BUSCA 2: TORNEIO (Igual a antes) ===
document.getElementById('btn-buscar-torneio').addEventListener('click', () => {
    const torneio = document.getElementById('input-torneio').value;
    const ano = document.getElementById('select-ano').value;
    if (torneio.trim() === '') return;

    fetch(`http://127.0.0.1:5000/api/torneio/${torneio}/${ano}`)
        .then(res => { if (!res.ok) throw new Error(); return res.json(); })
        .then(dados => {
            document.getElementById('nome-oficial-torneio').textContent = `${dados.torneio_oficial} (${dados.ano})`;
            document.getElementById('campeao-torneio').textContent = dados.campeao;
            document.getElementById('vice-torneio').textContent = dados.vice;
            document.getElementById('placar-torneio').textContent = dados.placar;
            document.getElementById('area-resultado-torneio').style.display = 'block';
        })
        .catch(() => alert('Torneio não encontrado nesse ano!'));
});

// === BUSCA 3: CAMPANHA (A NOVA MÁGICA) ===
document.getElementById('btn-buscar-campanha').addEventListener('click', () => {
    const jogador = document.getElementById('input-campanha-jogador').value;
    const torneio = document.getElementById('input-campanha-torneio').value;
    const ano = document.getElementById('select-ano-campanha').value;

    if (jogador.trim() === '' || torneio.trim() === '') return;

    fetch(`http://127.0.0.1:5000/api/campanha/${jogador}/${torneio}/${ano}`)
        .then(res => { if (!res.ok) throw new Error("Não encontrado"); return res.json(); })
        .then(dados => {
            document.getElementById('titulo-campanha').textContent = `${dados.jogador} em ${dados.torneio} (${dados.ano})`;
            
            // Mostra ou esconde o banner de campeão
            const banner = document.getElementById('banner-campeao');
            banner.style.display = dados.campeao ? 'block' : 'none';

            // Monta a lista de partidas injetando HTML
            const listaDiv = document.getElementById('lista-partidas');
            listaDiv.innerHTML = ''; // Limpa a busca anterior

            dados.partidas.forEach(partida => {
                // Define se a borda vai ser verde ou vermelha
                const classeResultado = partida.resultado === 'V' ? 'vitoria' : 'derrota';
                
                listaDiv.innerHTML += `
                    <div class="partida ${classeResultado}">
                        <div class="info-partida">
                            <span class="rodada">${partida.rodada}</span>
                            <span class="oponente">${partida.resultado === 'V' ? 'Venceu' : 'Perdeu para'} ${partida.oponente}</span>
                        </div>
                        <div class="placar-partida">${partida.placar}</div>
                    </div>
                `;
            });

            document.getElementById('area-resultado-campanha').style.display = 'block';
        })
        .catch(erro => alert('Não encontramos registros desse jogador nesse torneio no ano selecionado.'));
});