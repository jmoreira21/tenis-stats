from flask import Blueprint, jsonify
from database import conectar_banco, buscar_jogador_por_nome, TRADUCAO_SUPERFICIE, TRADUCAO_RODADA

jogador_bp = Blueprint('jogador', __name__)


def erro(mensagem, codigo=404):
    return jsonify({"erro": mensagem}), codigo


@jogador_bp.route('/api/jogador/<nome_pesquisado>', methods=['GET'])
def buscar_jogador(nome_pesquisado):
    conn = conectar_banco()
    try:
        jogador = buscar_jogador_por_nome(conn, nome_pesquisado)
        if not jogador:
            return erro("Jogador não encontrado")

        id_jogador = jogador['player_id']

        vitorias = conn.execute(
            "SELECT COUNT(*) FROM partidas WHERE winner_id = ?", (id_jogador,)
        ).fetchone()[0]

        derrotas = conn.execute(
            "SELECT COUNT(*) FROM partidas WHERE loser_id = ?", (id_jogador,)
        ).fetchone()[0]

        total_jogos = vitorias + derrotas
        aproveitamento = round((vitorias / total_jogos) * 100, 1) if total_jogos > 0 else 0

        sup_query = conn.execute(
            "SELECT surface FROM partidas WHERE winner_id = ? AND surface IS NOT NULL GROUP BY surface ORDER BY COUNT(*) DESC LIMIT 1",
            (id_jogador,)
        ).fetchone()
        superficie_favorita = TRADUCAO_SUPERFICIE.get(sup_query['surface'], sup_query['surface']) if sup_query else "Sem dados"

        titulos_query = conn.execute(
            "SELECT tourney_level, COUNT(*) as qtd FROM partidas WHERE winner_id = ? AND round = 'F' GROUP BY tourney_level",
            (id_jogador,)
        ).fetchall()
        titulos = {"G": 0, "F": 0, "M": 0, "A": 0, "C": 0}
        for linha in titulos_query:
            if linha['tourney_level'] in titulos:
                titulos[linha['tourney_level']] = linha['qtd']

        mao = {"R": "Destro", "L": "Canhoto"}.get(jogador['hand'], "Outro")

        # Desempenho por superfície para o gráfico
        superficies = ['Clay', 'Hard', 'Grass', 'Carpet']
        desempenho_sup = {}
        for sup in superficies:
            v = conn.execute(
                "SELECT COUNT(*) FROM partidas WHERE winner_id = ? AND surface = ?", (id_jogador, sup)
            ).fetchone()[0]
            d = conn.execute(
                "SELECT COUNT(*) FROM partidas WHERE loser_id = ? AND surface = ?", (id_jogador, sup)
            ).fetchone()[0]
            if v + d > 0:
                label = TRADUCAO_SUPERFICIE.get(sup, sup)
                desempenho_sup[label] = {"vitorias": v, "derrotas": d}

        return jsonify({
            "nome": jogador['nome_completo'],
            "pais": jogador['ioc'],
            "mao_dominante": mao,
            "vitorias": vitorias,
            "derrotas": derrotas,
            "aproveitamento": aproveitamento,
            "piso_favorito": superficie_favorita,
            "titulos": titulos,
            "desempenho_por_superficie": desempenho_sup
        })
    except Exception as e:
        return erro(f"Erro interno: {str(e)}", 500)
    finally:
        conn.close()


@jogador_bp.route('/api/titulos/<nome_jogador>', methods=['GET'])
def buscar_titulos(nome_jogador):
    conn = conectar_banco()
    try:
        jogador = buscar_jogador_por_nome(conn, nome_jogador)
        if not jogador:
            return erro("Jogador não encontrado")

        id_jogador = jogador['player_id']

        finais = conn.execute('''
            SELECT tourney_name, tourney_level,
                   SUBSTR(CAST(tourney_date AS TEXT), 1, 4) AS ano
            FROM partidas
            WHERE winner_id = ? AND round = 'F'
            ORDER BY tourney_date ASC
        ''', (id_jogador,)).fetchall()

        NIVEL_LABEL = {'G': 'Grand Slam', 'F': 'ATP Finals', 'M': 'Masters 1000', 'A': 'ATP 500/250', 'C': 'Challenger'}
        titulos_por_nivel = {'G': [], 'F': [], 'M': [], 'A': [], 'C': []}

        for f in finais:
            nivel = f['tourney_level']
            if nivel in titulos_por_nivel:
                titulos_por_nivel[nivel].append({
                    "torneio": f['tourney_name'],
                    "ano": f['ano']
                })

        return jsonify({
            nivel: titulos_por_nivel[nivel]
            for nivel in titulos_por_nivel
            if titulos_por_nivel[nivel]  # omite níveis sem títulos
        })
    except Exception as e:
        return erro(f"Erro interno: {str(e)}", 500)
    finally:
        conn.close()


@jogador_bp.route('/api/temporada/<jogador>/<ano>', methods=['GET'])
def buscar_temporada(jogador, ano):
    conn = conectar_banco()
    try:
        jog = buscar_jogador_por_nome(conn, jogador)
        if not jog:
            return erro("Jogador não encontrado")

        id_jogador = jog['player_id']

        # Usamos MAX(winner_id=?) para detectar se venceu a final (campeão),
        # e a rodada_eliminado para saber onde parou — evita o bug do MAX() alfabético.
        # Incluímos qualifying mas separamos: só_qualifying indica que o jogador
        # não chegou ao main draw.
        torneios_query = conn.execute('''
            SELECT
                tourney_name,
                tourney_level,
                surface,
                MIN(tourney_date) as tourney_date,
                MAX(CASE WHEN winner_id = ? AND round = 'F' THEN 1 ELSE 0 END) AS foi_campeao,
                MAX(CASE WHEN loser_id  = ? AND round NOT IN ('Q1','Q2','Q3') THEN round ELSE NULL END) AS rodada_eliminado,
                COUNT(CASE WHEN winner_id = ? AND round NOT IN ('Q1','Q2','Q3') THEN 1 END) AS vitorias,
                COUNT(CASE WHEN loser_id  = ? AND round NOT IN ('Q1','Q2','Q3') THEN 1 END) AS derrotas,
                MAX(CASE WHEN round NOT IN ('Q1','Q2','Q3') THEN 1 ELSE 0 END) AS teve_maindraw,
                MAX(CASE WHEN round IN ('Q1','Q2','Q3') THEN 1 ELSE 0 END) AS teve_qualifying
            FROM partidas
            WHERE SUBSTR(CAST(tourney_date AS TEXT), 1, 4) = ?
              AND (winner_id = ? OR loser_id = ?)
              AND tourney_name NOT LIKE '%Laver Cup%'
            GROUP BY tourney_name, tourney_level, surface
            ORDER BY tourney_date ASC
        ''', (id_jogador, id_jogador, id_jogador, id_jogador, ano, id_jogador, id_jogador)).fetchall()

        if not torneios_query:
            return erro(f"Nenhum torneio encontrado para {jog['nome_completo']} em {ano}.")

        NIVEL_LABEL = {
            'G': 'Grand Slam', 'F': 'ATP Finals',
            'M': 'Masters 1000', 'A': 'ATP 500/250', 'C': 'Challenger'
        }

        torneios = []
        total_vitorias = 0
        total_derrotas = 0
        titulos = 0

        for t in torneios_query:
            campeao   = bool(t['foi_campeao'])
            so_qualifying = bool(t['teve_qualifying']) and not bool(t['teve_maindraw'])

            if campeao:
                melhor = 'F'
            elif so_qualifying:
                melhor = 'QUAL'   # só jogou qualifying
            elif t['rodada_eliminado']:
                melhor = t['rodada_eliminado']
            else:
                melhor = '?'

            superficie = TRADUCAO_SUPERFICIE.get(t['surface'], t['surface']) if t['surface'] else 'Desconhecido'
            total_vitorias += t['vitorias']
            total_derrotas += t['derrotas']
            if campeao:
                titulos += 1

            torneios.append({
                "torneio": t['tourney_name'],
                "nivel": NIVEL_LABEL.get(t['tourney_level'], t['tourney_level']),
                "superficie": superficie,
                "resultado": "Qualifying" if so_qualifying else TRADUCAO_RODADA.get(melhor, melhor),
                "campeao": campeao,
                "vitorias": t['vitorias'],
                "derrotas": t['derrotas'],
                "so_qualifying": so_qualifying
            })

        return jsonify({
            "jogador": jog['nome_completo'],
            "ano": ano,
            "total_torneios": len(torneios),
            "total_vitorias": total_vitorias,
            "total_derrotas": total_derrotas,
            "titulos": titulos,
            "torneios": torneios
        })
    except Exception as e:
        return erro(f"Erro interno: {str(e)}", 500)
    finally:
        conn.close()