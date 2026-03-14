from flask import Blueprint, jsonify
from database import conectar_banco, buscar_jogador_por_nome, TRADUCAO_SUPERFICIE, TRADUCAO_RODADA

h2h_bp = Blueprint('h2h', __name__)


def erro(mensagem, codigo=404):
    return jsonify({"erro": mensagem}), codigo


def _stats_jogador(conn, id_jog):
    """Calcula estatísticas de carreira de um jogador para o card comparativo do H2H."""
    v = conn.execute("SELECT COUNT(*) FROM partidas WHERE winner_id = ?", (id_jog,)).fetchone()[0]
    d = conn.execute("SELECT COUNT(*) FROM partidas WHERE loser_id = ?",  (id_jog,)).fetchone()[0]
    total = v + d
    aproveitamento = round((v / total) * 100, 1) if total > 0 else 0

    titulos_q = conn.execute(
        "SELECT tourney_level, COUNT(*) as qtd FROM partidas WHERE winner_id = ? AND round = 'F' GROUP BY tourney_level",
        (id_jog,)
    ).fetchall()
    titulos = {"G": 0, "F": 0, "M": 0, "A": 0, "C": 0}
    for linha in titulos_q:
        if linha['tourney_level'] in titulos:
            titulos[linha['tourney_level']] = linha['qtd']

    sup_q = conn.execute(
        "SELECT surface FROM partidas WHERE winner_id = ? AND surface IS NOT NULL GROUP BY surface ORDER BY COUNT(*) DESC LIMIT 1",
        (id_jog,)
    ).fetchone()
    piso = TRADUCAO_SUPERFICIE.get(sup_q['surface'], sup_q['surface']) if sup_q else "Sem dados"

    return {
        "vitorias": v,
        "derrotas": d,
        "aproveitamento": aproveitamento,
        "grand_slams": titulos["G"],
        "atp_finals": titulos["F"],
        "masters": titulos["M"],
        "atp_500_250": titulos["A"],
        "challengers": titulos["C"],
        "piso_favorito": piso
    }


@h2h_bp.route('/api/head_to_head/<jogador1>/<jogador2>', methods=['GET'])
def head_to_head(jogador1, jogador2):
    conn = conectar_banco()
    try:
        jog1 = buscar_jogador_por_nome(conn, jogador1)
        jog2 = buscar_jogador_por_nome(conn, jogador2)

        if not jog1 or not jog2:
            nao_encontrado = jogador1 if not jog1 else jogador2
            return erro(f"Jogador não encontrado: {nao_encontrado}")

        id_jog1 = jog1['player_id']
        id_jog2 = jog2['player_id']

        confrontos_db = conn.execute('''
            SELECT winner_id, winner_name, loser_name, score, tourney_name,
                   SUBSTR(CAST(tourney_date AS TEXT), 1, 4) AS ano, round
            FROM partidas
            WHERE (winner_id = ? AND loser_id = ?) OR (winner_id = ? AND loser_id = ?)
            ORDER BY ano DESC, tourney_date DESC
        ''', (id_jog1, id_jog2, id_jog2, id_jog1)).fetchall()

        if not confrontos_db:
            return erro("Nenhum confronto encontrado entre os jogadores.")

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
                "rodada": TRADUCAO_RODADA.get(p['round'], p['round']),
                "vencedor": p['winner_name'],
                "placar": p['score']
            })

        return jsonify({
            "jogador1": jog1['nome_completo'],
            "jogador2": jog2['nome_completo'],
            "vitorias_jogador1": vitorias_j1,
            "vitorias_jogador2": vitorias_j2,
            "stats_jogador1": _stats_jogador(conn, id_jog1),
            "stats_jogador2": _stats_jogador(conn, id_jog2),
            "partidas": lista_partidas
        })
    except Exception as e:
        return erro(f"Erro interno: {str(e)}", 500)
    finally:
        conn.close()