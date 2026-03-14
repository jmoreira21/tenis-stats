from flask import Blueprint, jsonify
from database import conectar_banco, buscar_jogador_por_nome, TRADUCAO_RODADA

torneio_bp = Blueprint('torneio', __name__)


def erro(mensagem, codigo=404):
    return jsonify({"erro": mensagem}), codigo


@torneio_bp.route('/api/torneio/<nome_torneio>', methods=['GET'])
def buscar_historico_torneio(nome_torneio):
    conn = conectar_banco()
    try:
        finais = conn.execute('''
            SELECT
                SUBSTR(CAST(tourney_date AS TEXT), 1, 4) AS ano,
                tourney_name,
                winner_name,
                loser_name,
                score
            FROM partidas
            WHERE tourney_name LIKE ? AND round = 'F'
            ORDER BY tourney_date DESC
        ''', (f'%{nome_torneio}%',)).fetchall()

        if not finais:
            return erro("Torneio não encontrado.")

        return jsonify({
            "torneio_oficial": finais[0]['tourney_name'],
            "edicoes": [
                {
                    "ano": f['ano'],
                    "campeao": f['winner_name'],
                    "vice": f['loser_name'],
                    "placar": f['score']
                }
                for f in finais
            ]
        })
    except Exception as e:
        return erro(f"Erro interno: {str(e)}", 500)
    finally:
        conn.close()


@torneio_bp.route('/api/campanha/<jogador>/<torneio>/<ano>', methods=['GET'])
def buscar_campanha(jogador, torneio, ano):
    conn = conectar_banco()
    try:
        jog = buscar_jogador_por_nome(conn, jogador)
        if not jog:
            return erro("Jogador não encontrado")

        id_jogador = jog['player_id']

        partidas_query = conn.execute('''
            SELECT round, winner_id, winner_name, loser_name, score, tourney_name
            FROM partidas
            WHERE tourney_name LIKE ? AND SUBSTR(CAST(tourney_date AS TEXT), 1, 4) = ? AND (winner_id = ? OR loser_id = ?)
            ORDER BY match_num
        ''', (f'%{torneio}%', ano, id_jogador, id_jogador)).fetchall()

        if not partidas_query:
            return erro("Campanha não encontrada.")

        partidas = []
        campeao = False
        for p in partidas_query:
            ganhou = p['winner_id'] == id_jogador
            partidas.append({
                "rodada": TRADUCAO_RODADA.get(p['round'], p['round']),
                "oponente": p['loser_name'] if ganhou else p['winner_name'],
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
    except Exception as e:
        return erro(f"Erro interno: {str(e)}", 500)
    finally:
        conn.close()