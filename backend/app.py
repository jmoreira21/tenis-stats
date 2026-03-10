from flask import Flask, jsonify
from flask_cors import CORS
import pandas as pd
import os

app = Flask(__name__)
CORS(app)

# --- INICIALIZAÇÃO E CARREGAMENTO NA MEMÓRIA ---
diretorio_atual = os.path.dirname(os.path.abspath(__file__))
pasta_dados = os.path.join(diretorio_atual, '..', 'dados')

caminho_players = os.path.join(pasta_dados, 'atp_players.csv')
df_players = pd.read_csv(caminho_players)
df_players['nome_completo'] = df_players['name_first'] + ' ' + df_players['name_last']

# Descobrindo os anos disponíveis e torneios únicos automaticamente
anos_disponiveis = []
torneios_unicos = set()

for arquivo in os.listdir(pasta_dados):
    if arquivo.startswith('atp_matches_') and arquivo.endswith('.csv'):
        # Extrai o ano do nome do arquivo (ex: de "atp_matches_2023.csv" tira "2023")
        ano = arquivo.replace('atp_matches_', '').replace('.csv', '')
        anos_disponiveis.append(ano)
        
        # Lê o arquivo do ano para pegar os nomes dos torneios
        df_temp = pd.read_csv(os.path.join(pasta_dados, arquivo))
        torneios_unicos.update(df_temp['tourney_name'].dropna().unique())

# Organiza os anos do mais recente pro mais antigo
anos_disponiveis.sort(reverse=True)
lista_torneios_unicos = list(torneios_unicos)

# --- ROTAS DE AUXÍLIO (AUTOCOMPLETE E ANOS) ---
@app.route('/api/anos', methods=['GET'])
def obter_anos():
    return jsonify(anos_disponiveis)

@app.route('/api/sugestoes/<texto>', methods=['GET'])
def sugerir_jogadores(texto):
    sugestoes = df_players[df_players['nome_completo'].str.contains(texto, case=False, na=False)]
    return jsonify(sugestoes['nome_completo'].head(10).tolist())

@app.route('/api/sugestoes_torneio/<texto>', methods=['GET'])
def sugerir_torneios(texto):
    # Filtra a lista de torneios únicos
    sugestoes = [t for t in lista_torneios_unicos if texto.lower() in t.lower()]
    return jsonify(sugestoes[:10])

# --- ROTAS PRINCIPAIS (BUSCA) ---
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
        
        vitorias, derrotas, aproveitamento = 0, 0, 0
        superficie_favorita = "Sem dados"
        titulos = {"G": 0, "F": 0, "M": 0, "A": 0, "C": 0}
        
        if anos_disponiveis:
            ano_recente = anos_disponiveis[0]
            caminho_matches = os.path.join(pasta_dados, f'atp_matches_{ano_recente}.csv')
            
            if os.path.exists(caminho_matches):
                df_matches = pd.read_csv(caminho_matches)
                
                # Separa as vitórias e derrotas
                df_vitorias = df_matches[df_matches['winner_id'] == id_jogador]
                df_derrotas = df_matches[df_matches['loser_id'] == id_jogador]
                
                vitorias = len(df_vitorias)
                derrotas = len(df_derrotas)
                
                # Calcula o Aproveitamento
                total_jogos = vitorias + derrotas
                if total_jogos > 0:
                    aproveitamento = round((vitorias / total_jogos) * 100, 1)
                
                # Descobre a Superfície Favorita (onde mais ganhou jogos)
                if not df_vitorias.empty:
                    sup_ing = df_vitorias['surface'].value_counts().idxmax()
                    traducao = {'Clay': 'Saibro', 'Grass': 'Grama', 'Hard': 'Dura', 'Carpet': 'Carpete'}
                    superficie_favorita = traducao.get(sup_ing, sup_ing)
                
                # Estante de Troféus (Filtra vitórias onde a rodada era 'F' de Final)
                finais_ganhas = df_vitorias[df_vitorias['round'] == 'F']
                if not finais_ganhas.empty:
                    # Conta quantos títulos ele tem por nível de torneio
                    contagem_titulos = finais_ganhas['tourney_level'].value_counts()
                    for nivel in titulos.keys():
                        titulos[nivel] = int(contagem_titulos.get(nivel, 0))

        mao = "Destro" if dados['hand'] == "R" else "Canhoto" if dados['hand'] == "L" else "Outro"

        return jsonify({
            "nome": dados['nome_completo'],
            "pais": dados['ioc'],
            "mao_dominante": mao,
            "vitorias": vitorias,
            "derrotas": derrotas,
            "aproveitamento": aproveitamento,
            "piso_favorito": superficie_favorita,
            "titulos": titulos
        })
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

@app.route('/api/torneio/<nome_torneio>/<ano>', methods=['GET'])
def buscar_campeao(nome_torneio, ano):
    caminho_arquivo_ano = os.path.join(pasta_dados, f'atp_matches_{ano}.csv')
    
    if not os.path.exists(caminho_arquivo_ano):
        return jsonify({"erro": f"Banco de dados de {ano} não encontrado."}), 404
        
    try:
        df_matches = pd.read_csv(caminho_arquivo_ano)
        torneios_encontrados = df_matches[df_matches['tourney_name'].str.contains(nome_torneio, case=False, na=False)]
        
        if torneios_encontrados.empty:
            return jsonify({"erro": "Torneio não encontrado nesse ano."}), 404
            
        final = torneios_encontrados[torneios_encontrados['round'] == 'F']
        if final.empty:
            return jsonify({"erro": "Final não encontrada."}), 404
            
        dados_final = final.iloc[0]
        return jsonify({
            "torneio_oficial": dados_final['tourney_name'],
            "ano": ano,
            "campeao": dados_final['winner_name'],
            "vice": dados_final['loser_name'],
            "placar": dados_final['score']
        })
    except Exception as e:
        return jsonify({"erro": str(e)}), 500
    
  
@app.route('/api/campanha/<jogador>/<torneio>/<ano>', methods=['GET'])
def buscar_campanha(jogador, torneio, ano):
    caminho_arquivo_ano = os.path.join(pasta_dados, f'atp_matches_{ano}.csv')
    
    if not os.path.exists(caminho_arquivo_ano):
        return jsonify({"erro": f"Banco de dados de {ano} não encontrado."}), 404

    try:
        jogador_encontrado = df_players[df_players['nome_completo'].str.lower() == jogador.lower()]
        if jogador_encontrado.empty:
            jogador_encontrado = df_players[df_players['nome_completo'].str.contains(jogador, case=False, na=False)]
        
        if jogador_encontrado.empty: return jsonify({"erro": "Jogador não encontrado"}), 404
        
        id_jogador = jogador_encontrado.iloc[0]['player_id']
        nome_oficial_jogador = jogador_encontrado.iloc[0]['nome_completo']

        #Carrega as partidas do ano e acha o torneio
        df_matches = pd.read_csv(caminho_arquivo_ano)
        df_torneio = df_matches[df_matches['tourney_name'].str.contains(torneio, case=False, na=False)]
        
        if df_torneio.empty: return jsonify({"erro": "Torneio não encontrado nesse ano."}), 404
        nome_oficial_torneio = df_torneio.iloc[0]['tourney_name']

        #Pega todas as partidas onde o jogador foi o vencedor OU o perdedor
        df_campanha = df_torneio[(df_torneio['winner_id'] == id_jogador) | (df_torneio['loser_id'] == id_jogador)]
        
        if df_campanha.empty: return jsonify({"erro": f"{nome_oficial_jogador} não participou deste torneio."}), 404

        df_campanha = df_campanha.sort_values('match_num')

        partidas = []
        campeao = False

        rodada_map = {'F': 'Final', 'SF': 'Semifinal', 'QF': 'Quartas', 'R16': 'Oitavas', 'R32': '3ª Rodada', 'R64': '2ª Rodada', 'R128': '1ª Rodada', 'RR': 'Grupos'}

        # Varre cada partida que ele jogou
        for _, partida in df_campanha.iterrows():
            ganhou = partida['winner_id'] == id_jogador
            oponente = partida['loser_name'] if ganhou else partida['winner_name']
            rodada_bonita = rodada_map.get(partida['round'], partida['round'])

            partidas.append({
                "rodada": rodada_bonita,
                "oponente": oponente,
                "placar": partida['score'],
                "resultado": "V" if ganhou else "D"
            })

            if ganhou and partida['round'] == 'F':
                campeao = True

        return jsonify({
            "jogador": nome_oficial_jogador,
            "torneio": nome_oficial_torneio,
            "ano": ano,
            "campeao": campeao,
            "partidas": partidas
        })

    except Exception as e:
        return jsonify({"erro": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)