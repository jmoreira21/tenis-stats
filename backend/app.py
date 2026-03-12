from flask import Flask, jsonify
from flask_cors import CORS
import sqlite3
import os

app = Flask(__name__)
CORS(app)

# Caminho do nosso banco de dados
diretorio_atual = os.path.dirname(os.path.abspath(__file__))
caminho_db = os.path.join(diretorio_atual, '..', 'dados', 'tennis.db')

def conectar_banco():
    conn = sqlite3.connect(caminho_db)
    conn.row_factory = sqlite3.Row 
    return conn

# ==========================================
# ROTAS DE AUXÍLIO (AUTOCOMPLETE E ANOS)
# ==========================================
@app.route('/api/anos', methods=['GET'])
def obter_anos():
    conn = conectar_banco()
    anos = conn.execute("SELECT DISTINCT SUBSTR(CAST(tourney_date AS TEXT), 1, 4) AS ano FROM partidas ORDER BY ano DESC").fetchall()
    conn.close()
    return jsonify([linha['ano'] for linha in anos if linha['ano']])

@app.route('/api/sugestoes/<texto>', methods=['GET'])
def sugerir_jogadores(texto):
    conn = conectar_banco()
    # Usando ORDER BY player_id DESC para sugerir sempre os jogadores mais recentes primeiro
    sugestoes = conn.execute("SELECT nome_completo FROM jogadores WHERE nome_completo LIKE ? ORDER BY player_id DESC LIMIT 10", (f'%{texto}%',)).fetchall()
    conn.close()
    return jsonify([linha['nome_completo'] for linha in sugestoes])

@app.route('/api/sugestoes_torneio/<texto>', methods=['GET'])
def sugerir_torneios(texto):
    conn = conectar_banco()
    sugestoes = conn.execute("SELECT DISTINCT tourney_name FROM partidas WHERE tourney_name LIKE ? LIMIT 10", (f'%{texto}%',)).fetchall()
    conn.close()
    return jsonify([linha['tourney_name'] for linha in sugestoes])


# ==========================================
# ROTAS PRINCIPAIS (AS 4 ABAS DO SITE)
# ==========================================

# 1. ABA DE JOGADOR
@app.route('/api/jogador/<nome_pesquisado>', methods=['GET'])
def buscar_jogador(nome_pesquisado):
    conn = conectar_banco()
    
    # ORDER BY player_id DESC garante que não vamos pegar jogadores homônimos antigos (ex: Alcaraz de 1976)
    jogador = conn.execute("SELECT * FROM jogadores WHERE nome_completo LIKE ? ORDER BY player_id DESC LIMIT 1", (nome_pesquisado,)).fetchone()
    if not jogador:
        jogador = conn.execute("SELECT * FROM jogadores WHERE nome_completo LIKE ? ORDER BY player_id DESC LIMIT 1", (f'%{nome_pesquisado}%',)).fetchone()
        
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
        traducao = {'Clay': 'Saibro', 'Grass': 'Grama', 'Hard': 'Dura', 'Carpet': 'Carpete'}
        superficie_favorita = traducao.get(sup_ing, sup_ing)
        
    titulos_query = conn.execute("SELECT tourney_level, COUNT(*) as qtd FROM partidas WHERE winner_id = ? AND round = 'F' GROUP BY tourney_level", (id_jogador,)).fetchall()
    
    # O 'C' de Challengers está aqui
    titulos = {"G": 0, "F": 0, "M": 0, "A": 0, "C": 0} 
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

# 2. ABA DE TORNEIO
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

# 3. ABA DE CAMPANHA
@app.route('/api/campanha/<jogador>/<torneio>/<ano>', methods=['GET'])
def buscar_campanha(jogador, torneio, ano):
    conn = conectar_banco()
    
    # ORDER BY player_id DESC protegido
    jog = conn.execute("SELECT player_id, nome_completo FROM jogadores WHERE nome_completo LIKE ? ORDER BY player_id DESC LIMIT 1", (f'%{jogador}%',)).fetchone()
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

# 4. ABA HEAD-TO-HEAD
@app.route('/api/head_to_head/<jogador1>/<jogador2>', methods=['GET'])
def head_to_head(jogador1, jogador2):
    conn = conectar_banco()

    jog1 = conn.execute("SELECT player_id, nome_completo FROM jogadores WHERE nome_completo LIKE ? ORDER BY player_id DESC LIMIT 1", (f'%{jogador1}%',)).fetchone()
    jog2 = conn.execute("SELECT player_id, nome_completo FROM jogadores WHERE nome_completo LIKE ? ORDER BY player_id DESC LIMIT 1", (f'%{jogador2}%',)).fetchone()

    if not jog1 or not jog2:
        conn.close()
        return jsonify({"erro": "Um ou ambos os jogadores não foram encontrados."}), 404

    id_jog1 = jog1['player_id']
    id_jog2 = jog2['player_id']

    
    confrontos_db = conn.execute('''
        SELECT winner_id, winner_name, loser_name, score, tourney_name, SUBSTR(CAST(tourney_date AS TEXT), 1, 4) AS ano, round
        FROM partidas
        WHERE (winner_id = ? AND loser_id = ?) OR (winner_id = ? AND loser_id = ?)
        ORDER BY ano DESC, tourney_date DESC
    ''', (id_jog1, id_jog2, id_jog2, id_jog1)).fetchall()

    conn.close()

    if not confrontos_db:
        return jsonify({"erro": "Nenhum confronto encontrado entre os jogadores."}), 404

    vitorias_j1 = 0
    vitorias_j2 = 0
    lista_partidas = []

    for p in confrontos_db:
        if p['winner_id'] == id_jog1:
            vitorias_j1 += 1
        else:
            vitorias_j2 += 1
            
        lista_partidas.append({
            "ano": p['ano'],
            "torneio": p['tourney_name'],
            "rodada": p['round'],
            "vencedor": p['winner_name'],
            "placar": p['score']
        })

    return jsonify({
        "jogador1": jog1['nome_completo'],
        "jogador2": jog2['nome_completo'],
        "vitorias_jogador1": vitorias_j1,
        "vitorias_jogador2": vitorias_j2,
        "partidas": lista_partidas
    })

if __name__ == '__main__':
    app.run(debug=True)