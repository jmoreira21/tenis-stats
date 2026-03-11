from flask import Flask, jsonify
from flask_cors import CORS
import sqlite3
import os

app = Flask(__name__)
CORS(app)


diretorio_atual = os.path.dirname(os.path.abspath(__file__))
caminho_db = os.path.join(diretorio_atual, '..', 'dados', 'tennis.db')

def conectar_banco():
    conn = sqlite3.connect(caminho_db)
    conn.row_factory = sqlite3.Row 
    return conn


@app.route('/api/anos', methods=['GET'])
def obter_anos():
    conn = conectar_banco()
    # Pega os anos únicos extraindo os 4 primeiros dígitos da data do torneio
    anos = conn.execute("SELECT DISTINCT SUBSTR(CAST(tourney_date AS TEXT), 1, 4) AS ano FROM partidas ORDER BY ano DESC").fetchall()
    conn.close()
    return jsonify([linha['ano'] for linha in anos if linha['ano']])

@app.route('/api/sugestoes/<texto>', methods=['GET'])
def sugerir_jogadores(texto):
    conn = conectar_banco()
    sugestoes = conn.execute("SELECT nome_completo FROM jogadores WHERE nome_completo LIKE ? LIMIT 10", (f'%{texto}%',)).fetchall()
    conn.close()
    return jsonify([linha['nome_completo'] for linha in sugestoes])

@app.route('/api/sugestoes_torneio/<texto>', methods=['GET'])
def sugerir_torneios(texto):
    conn = conectar_banco()
    sugestoes = conn.execute("SELECT DISTINCT tourney_name FROM partidas WHERE tourney_name LIKE ? LIMIT 10", (f'%{texto}%',)).fetchall()
    conn.close()
    return jsonify([linha['tourney_name'] for linha in sugestoes])

@app.route('/api/jogador/<nome_pesquisado>', methods=['GET'])
def buscar_jogador(nome_pesquisado):
    conn = conectar_banco()
    
    jogador = conn.execute("SELECT * FROM jogadores WHERE nome_completo LIKE ? LIMIT 1", (nome_pesquisado,)).fetchone()
    if not jogador:
        jogador = conn.execute("SELECT * FROM jogadores WHERE nome_completo LIKE ? LIMIT 1", (f'%{nome_pesquisado}%',)).fetchone()
        
    if not jogador:
        conn.close()
        return jsonify({"erro": "Jogador não encontrado"}), 404

    id_jogador = jogador['player_id']
    
    vitorias = conn.execute("SELECT COUNT(*) FROM partidas WHERE winner_id = ?", (id_jogador,)).fetchone()[0]
    derrotas = conn.execute("SELECT COUNT(*) FROM partidas WHERE loser_id = ?", (id_jogador,)).fetchone()[0]
    
    total_jogos = vitorias + derrotas
    aproveitamento = round((vitorias / total_jogos) * 100, 1) if total_jogos > 0 else 0
    
    sup_query = conn.execute("SELECT surface, COUNT(*) as qtd FROM partidas WHERE winner_id = ? AND surface IS NOT NULL GROUP BY surface ORDER BY qtd DESC LIMIT 1", (id_jogador,)).fetchone()
    
    superficie_favorita = "Sem dados"
    if sup_query:
        sup_ing = sup_query['surface']
        traducao = {'Clay': 'Saibro', 'Grass': 'Grama', 'Hard': 'Quadra Dura', 'Carpet': 'Carpete'}
        superficie_favorita = traducao.get(sup_ing, sup_ing)
        
    titulos_query = conn.execute("SELECT tourney_level, COUNT(*) as qtd FROM partidas WHERE winner_id = ? AND round = 'F' GROUP BY tourney_level", (id_jogador,)).fetchall()
    titulos = {"G": 0, "F": 0, "M": 0, "A": 0}
    for linha in titulos_query:
        nivel = linha['tourney_level']
        if nivel in titulos:
            titulos[nivel] = linha['qtd']
            
    conn.close()

    mao = "Destro" if jogador['hand'] == "R" else "Canhoto" if jogador['hand'] == "L" else "Outro"

    return jsonify({
        "nome": jogador['nome_completo'],
        "pais": jogador['ioc'],
        "mao_dominante": mao,
        "vitorias": vitorias,
        "derrotas": derrotas,
        "aproveitamento": aproveitamento,
        "piso_favorito": superficie_favorita,
        "titulos": titulos
    })

@app.route('/api/torneio/<nome_torneio>/<ano>', methods=['GET'])
def buscar_campeao(nome_torneio, ano):
    conn = conectar_banco()
    final = conn.execute('''
        SELECT tourney_name, winner_name, loser_name, score 
        FROM partidas 
        WHERE tourney_name LIKE ? AND SUBSTR(CAST(tourney_date AS TEXT), 1, 4) = ? AND round = 'F' 
        LIMIT 1
    ''', (f'%{nome_torneio}%', ano)).fetchone()
    
    conn.close()
    
    if not final:
        return jsonify({"erro": "Final não encontrada."}), 404
        
    return jsonify({
        "torneio_oficial": final['tourney_name'],
        "ano": ano,
        "campeao": final['winner_name'],
        "vice": final['loser_name'],
        "placar": final['score']
    })

@app.route('/api/campanha/<jogador>/<torneio>/<ano>', methods=['GET'])
def buscar_campanha(jogador, torneio, ano):
    conn = conectar_banco()
    
    jog = conn.execute("SELECT player_id, nome_completo FROM jogadores WHERE nome_completo LIKE ? LIMIT 1", (f'%{jogador}%',)).fetchone()
    if not jog:
        conn.close()
        return jsonify({"erro": "Jogador não encontrado"}), 404
        
    id_jogador = jog['player_id']
    
    partidas_query = conn.execute('''
        SELECT round, winner_id, winner_name, loser_name, score, tourney_name 
        FROM partidas 
        WHERE tourney_name LIKE ? AND SUBSTR(CAST(tourney_date AS TEXT), 1, 4) = ? AND (winner_id = ? OR loser_id = ?) 
        ORDER BY match_num
    ''', (f'%{torneio}%', ano, id_jogador, id_jogador)).fetchall()
    
    conn.close()
    
    if not partidas_query:
        return jsonify({"erro": "Campanha não encontrada."}), 404
        
    partidas = []
    campeao = False
    rodada_map = {'F': 'Final', 'SF': 'Semifinal', 'QF': 'Quartas', 'R16': 'Oitavas', 'R32': '3ª Rodada', 'R64': '2ª Rodada', 'R128': '1ª Rodada', 'RR': 'Grupos'}

    for p in partidas_query:
        ganhou = p['winner_id'] == id_jogador
        oponente = p['loser_name'] if ganhou else p['winner_name']
        
        partidas.append({
            "rodada": rodada_map.get(p['round'], p['round']),
            "oponente": oponente,
            "placar": p['score'],
            "resultado": "V" if ganhou else "D"
        })
        if ganhou and p['round'] == 'F':
            campeao = True

    return jsonify({
        "jogador": jog['nome_completo'],
        "torneio": partidas_query[0]['tourney_name'],
        "ano": ano,
        "campeao": campeao,
        "partidas": partidas
    })

if __name__ == '__main__':
    app.run(debug=True)