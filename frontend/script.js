// Pegando os elementos da tela
const inputJogador = document.getElementById('input-jogador');
const btnBuscar = document.getElementById('btn-buscar');
const areaResultado = document.getElementById('area-resultado');
const textoNome = document.getElementById('nome-jogador');
const textoPais = document.getElementById('pais-jogador');
const textoMao = document.getElementById('mao-jogador');

btnBuscar.addEventListener('click', () => {
    const nomePesquisado = inputJogador.value;

    if (nomePesquisado.trim() === '') return;

    // Fazendo o pedido para a sua API em Python
    fetch(`http://127.0.0.1:5000/api/jogador/${nomePesquisado}`)
        .then(resposta => {
            if (!resposta.ok) {
                throw new Error("Jogador não encontrado");
            }
            return resposta.json(); 
        })
        .then(dados => {
            textoNome.textContent = dados.nome;
            textoPais.textContent = dados.pais;
            textoMao.textContent = dados.mao_dominante;
            
            areaResultado.style.display = 'block';
        })
        .catch(erro => {
           
            textoNome.textContent = "❌ Jogador não encontrado";
            textoPais.textContent = "--";
            textoMao.textContent = "--";
            areaResultado.style.display = 'block';
        });
});