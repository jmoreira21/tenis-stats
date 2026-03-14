from flask import Blueprint, jsonify
from database import conectar_banco, TRADUCAO_SUPERFICIE, TRADUCAO_RODADA

auxilio_bp = Blueprint('auxilio', __name__)


def erro(mensagem, codigo=404):
    return jsonify({"erro": mensagem}), codigo


@auxilio_bp.route('/api/anos', methods=['GET'])
def obter_anos():
    conn = conectar_banco()
    try:
        anos = conn.execute(
            "SELECT DISTINCT SUBSTR(CAST(tourney_date AS TEXT), 1, 4) AS ano FROM partidas ORDER BY ano DESC"
        ).fetchall()
        return jsonify([linha['ano'] for linha in anos if linha['ano']])
    except Exception as e:
        return erro(f"Erro ao buscar anos: {str(e)}", 500)
    finally:
        conn.close()


@auxilio_bp.route('/api/sugestoes/<texto>', methods=['GET'])
def sugerir_jogadores(texto):
    conn = conectar_banco()
    try:
        sugestoes = conn.execute(
            "SELECT nome_completo FROM jogadores WHERE nome_completo LIKE ? ORDER BY player_id DESC LIMIT 10",
            (f'%{texto}%',)
        ).fetchall()
        return jsonify([linha['nome_completo'] for linha in sugestoes])
    except Exception as e:
        return erro(f"Erro ao buscar sugestões: {str(e)}", 500)
    finally:
        conn.close()


@auxilio_bp.route('/api/sugestoes_torneio/<texto>', methods=['GET'])
def sugerir_torneios(texto):
    conn = conectar_banco()
    try:
        sugestoes = conn.execute(
            "SELECT DISTINCT tourney_name FROM partidas WHERE tourney_name LIKE ? LIMIT 10",
            (f'%{texto}%',)
        ).fetchall()
        return jsonify([linha['tourney_name'] for linha in sugestoes])
    except Exception as e:
        return erro(f"Erro ao buscar sugestões de torneio: {str(e)}", 500)
    finally:
        conn.close()