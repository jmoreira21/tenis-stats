import sqlite3
import os

# Caminho do banco de dados
# Suporta tanto a estrutura local (backend/../dados/) quanto o Railway (variável de ambiente)
diretorio_atual = os.path.dirname(os.path.abspath(__file__))
caminho_db = os.environ.get(
    'DATABASE_PATH',
    os.path.join(diretorio_atual, '..', 'dados', 'tennis.db')
)

# Dicionários de tradução compartilhados por todos os módulos
TRADUCAO_SUPERFICIE = {'Clay': 'Saibro', 'Grass': 'Grama', 'Hard': 'Dura', 'Carpet': 'Carpete'}
TRADUCAO_RODADA = {
    'F': 'Final', 'SF': 'Semifinal', 'QF': 'Quartas',
    'R16': 'Oitavas', 'R32': '3ª Rodada', 'R64': '2ª Rodada',
    'R128': '1ª Rodada', 'RR': 'Grupos',
    'Q1': 'Qualif. R1', 'Q2': 'Qualif. R2', 'Q3': 'Qualif. R3'
}


def conectar_banco():
    conn = sqlite3.connect(caminho_db)
    conn.row_factory = sqlite3.Row
    return conn


def buscar_jogador_por_nome(conn, nome):
    """
    Busca um jogador pelo nome. Tenta correspondência exata primeiro,
    depois busca parcial. ORDER BY player_id DESC evita pegar homônimos
    antigos (ex: Alcaraz de 1976).
    """
    jogador = conn.execute(
        "SELECT * FROM jogadores WHERE nome_completo LIKE ? ORDER BY player_id DESC LIMIT 1",
        (nome,)
    ).fetchone()
    if not jogador:
        jogador = conn.execute(
            "SELECT * FROM jogadores WHERE nome_completo LIKE ? ORDER BY player_id DESC LIMIT 1",
            (f'%{nome}%',)
        ).fetchone()
    return jogador