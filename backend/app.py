from flask import Flask, jsonify
from flask_cors import CORS
import pandas as pd
import os

app = Flask(__name__)
CORS(app)

# 1. CARREGAR DADOS NA MEMÓRIA AO LIGAR O SERVIDOR (Muito mais rápido!)
diretorio_atual = os.path.dirname(os.path.abspath(__file__))
caminho_players = os.path.join(diretorio_atual, '..', 'dados', 'atp_players.csv')
caminho_matches = os.path.join(diretorio_atual, '..', 'dados', 'atp_matches_2023.csv') 

df_players = pd.read_csv(caminho_players)
df_players['nome_completo'] = df_players['name_first'] + ' ' + df_players['name_last']

# 2. ROTA NOVA: Retorna até 10 sugestões de nomes enquanto o usuário digita
@app.route('/api/sugestoes/<texto>', methods=['GET'])
def sugerir_jogadores(texto):
    # Filtra nomes que começam com ou contêm o texto digitado
    sugestoes = df_players[df_players['nome_completo'].str.contains(texto, case=False, na=False)]
    
    # Pega só os 10 primeiros resultados e transforma em uma lista normal do Python
    lista_nomes = sugestoes['nome_completo'].head(10).tolist()
    return jsonify(lista_nomes)

# 3. ROTA ANTIGA: A busca completa do jogador (agora usando o df_players da memória)
@app.route('/api/jogador/<nome_pesquisado>', methods=['GET'])
def buscar_jogador(nome_pesquisado):
    try:
        jogador_encontrado = df_players[df_players['nome_completo'].str.lower() == nome_pesquisado.lower()]
        
        if jogador_encontrado.empty:
            jogador_encontrado = df_players[df_players['nome_completo'].str.contains(nome_pesquisado, case=False, na=False)]
        
        if jogador_encontrado.empty:
            return jsonify({"erro": "Jogador não encontrado"}), 404
            
        dados = jogador_encontrado.iloc[0]
        id_jogador = dados['player_id']
        
        vitorias = 0
        derrotas = 0
        
        if os.path.exists(caminho_matches):
            df_matches = pd.read_csv(caminho_matches)
            vitorias = len(df_matches[df_matches['winner_id'] == id_jogador])
            derrotas = len(df_matches[df_matches['loser_id'] == id_jogador])

        mao = "Destro" if dados['hand'] == "R" else "Canhoto" if dados['hand'] == "L" else "Outro"

        resposta = {
            "nome": dados['nome_completo'],
            "pais": dados['ioc'],
            "mao_dominante": mao,
            "vitorias": int(vitorias),
            "derrotas": int(derrotas)
        }
        
        return jsonify(resposta)

    except Exception as e:
        return jsonify({"erro": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)