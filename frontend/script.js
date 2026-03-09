// === PARTE 1: Pegando os elementos da tela ===
const inputJogador = document.getElementById('input-jogador');
const btnBuscar = document.getElementById('btn-buscar');
const areaResultado = document.getElementById('area-resultado');
const textoNome = document.getElementById('nome-jogador');
const textoPais = document.getElementById('pais-jogador');
const textoMao = document.getElementById('mao-jogador');
const textoVitorias = document.getElementById('vitorias-jogador');
const textoDerrotas = document.getElementById('derrotas-jogador');
const listaSugestoes = document.getElementById('lista-sugestoes');


btnBuscar.addEventListener('click', () => {
    const nomePesquisado = inputJogador.value;

    if (nomePesquisado.trim() === '') return;

    fetch(`http://127.0.0.1:5000/api/jogador/${nomePesquisado}`)
        .then(resposta => {
            if (!resposta.ok) throw new Error("Jogador não encontrado");
            return resposta.json();
        })
        .then(dados => {
            textoNome.textContent = dados.nome;
            textoPais.textContent = dados.pais;
            textoMao.textContent = dados.mao_dominante;
            textoVitorias.textContent = dados.vitorias;
            textoDerrotas.textContent = dados.derrotas;
            
            areaResultado.style.display = 'block';
        })
        .catch(erro => {
            textoNome.textContent = "❌ Jogador não encontrado";
            textoPais.textContent = "--";
            textoMao.textContent = "--";
            textoVitorias.textContent = "--";
            textoDerrotas.textContent = "--";
            areaResultado.style.display = 'block';
        });
});

inputJogador.addEventListener('input', () => {
    const texto = inputJogador.value;

    if (texto.trim() === '') {
        listaSugestoes.style.display = 'none';
        return;
    }

    fetch(`http://127.0.0.1:5000/api/sugestoes/${texto}`)
        .then(resposta => resposta.json())
        .then(nomes => {
            // Limpa a lista anterior
            listaSugestoes.innerHTML = '';

            // Se o Python não achar nenhum nome, esconde a lista
            if (nomes.length === 0) {
                listaSugestoes.style.display = 'none';
                return;
            }

            // Cria um item na lista para cada nome encontrado
            nomes.forEach(nome => {
                const divItem = document.createElement('div');
                divItem.classList.add('item-sugestao');
                divItem.textContent = nome;

                // Se clicar no nome sugerido, preenche o input e faz a busca principal
                divItem.addEventListener('click', () => {
                    inputJogador.value = nome;
                    listaSugestoes.style.display = 'none'; // Esconde a lista
                    btnBuscar.click(); // Clica no botão de pesquisar automaticamente!
                });

                listaSugestoes.appendChild(divItem);
            });

            // Mostra a lista na tela
            listaSugestoes.style.display = 'block';
        });
});

// Esconde a lista se o usuário clicar fora dela
document.addEventListener('click', (evento) => {
    if (evento.target !== inputJogador) {
        listaSugestoes.style.display = 'none';
    }
});