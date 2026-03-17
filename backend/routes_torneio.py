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

        # Primeiro busca o tourney_id exato da edição — evita misturar partidas
        # de edições diferentes do mesmo torneio (ex: Buenos Aires 2019 vs 2020)
        edicao = conn.execute('''
            SELECT DISTINCT tourney_id, tourney_name
            FROM partidas
            WHERE tourney_name LIKE ? AND SUBSTR(CAST(tourney_date AS TEXT), 1, 4) = ?
            LIMIT 1
        ''', (f'%{torneio}%', ano)).fetchone()

        if not edicao:
            return erro("Torneio não encontrado neste ano.")

        # Qualifying
        qualifying_query = conn.execute(
            "SELECT round, winner_id, winner_name, loser_name, score, winner_entry, loser_entry, tourney_name "
            "FROM partidas "
            "WHERE tourney_id = ? AND (winner_id = ? OR loser_id = ?) AND round IN ('Q1','Q2','Q3') "
            "ORDER BY CASE round WHEN 'Q1' THEN 1 WHEN 'Q2' THEN 2 WHEN 'Q3' THEN 3 END ASC",
            (edicao['tourney_id'], id_jogador, id_jogador)
        ).fetchall()

        # Main draw
        partidas_query = conn.execute(
            "SELECT round, winner_id, winner_name, loser_name, score, winner_entry, loser_entry, tourney_name "
            "FROM partidas "
            "WHERE tourney_id = ? AND (winner_id = ? OR loser_id = ?) AND round NOT IN ('Q1','Q2','Q3') "
            "ORDER BY CASE round "
            "WHEN 'R128' THEN 1 WHEN 'R64' THEN 2 WHEN 'R32' THEN 3 WHEN 'R16' THEN 4 "
            "WHEN 'QF' THEN 5 WHEN 'SF' THEN 6 WHEN 'F' THEN 7 WHEN 'RR' THEN 8 ELSE 9 END ASC",
            (edicao['tourney_id'], id_jogador, id_jogador)
        ).fetchall()

        if not qualifying_query and not partidas_query:
            return erro("Campanha não encontrada.")

        # Entradas especiais que valem badge — entrada normal (Q, vazio, null) nao mostra
        ENTRADAS_ESPECIAIS = {
            'LL': 'Lucky Loser', 'WC': 'Wildcard',
            'PR': 'Protected Ranking', 'SE': 'Special Exempt'
        }

        entrada_especial = None
        for p in partidas_query:
            entry = p['winner_entry'] if p['winner_id'] == id_jogador else p['loser_entry']
            if entry in ENTRADAS_ESPECIAIS:
                entrada_especial = ENTRADAS_ESPECIAIS[entry]
                break

        def montar_partidas(rows):
            resultado = []
            for p in rows:
                ganhou = p['winner_id'] == id_jogador
                resultado.append({
                    "rodada": TRADUCAO_RODADA.get(p['round'], p['round']),
                    "oponente": p['loser_name'] if ganhou else p['winner_name'],
                    "placar": p['score'],
                    "resultado": "V" if ganhou else "D"
                })
            return resultado

        campeao = any(p['winner_id'] == id_jogador and p['round'] == 'F' for p in partidas_query)
        nome_torneio = (partidas_query or qualifying_query)[0]['tourney_name']

        return jsonify({
            "jogador": jog['nome_completo'],
            "torneio": nome_torneio,
            "ano": ano,
            "campeao": campeao,
            "entrada_especial": entrada_especial,
            "qualifying": montar_partidas(qualifying_query),
            "partidas": montar_partidas(partidas_query)
        })
    except Exception as e:
        return erro(f"Erro interno: {str(e)}", 500)
    finally:
        conn.close()