import sqlite3
import pandas as pd
import os
import time

diretorio_atual = os.path.dirname(os.path.abspath(__file__))
pasta_dados = os.path.join(diretorio_atual, '..', 'dados')
caminho_db = os.path.join(pasta_dados, 'tennis.db')

print("Iniciando")
inicio = time.time()

# 1. Cria a conexão com o banco (se não existir, ele cria o arquivo tennis.db)
conexao = sqlite3.connect(caminho_db)
cursor = conexao.cursor()

# 2. Carrega a tabela de Jogadores
print("Carregando tabela de jogadores", end=" ")
caminho_players = os.path.join(pasta_dados, 'atp_players.csv')
if os.path.exists(caminho_players):
    df_players = pd.read_csv(caminho_players)
    # Criamos a coluna de nome completo já no banco para facilitar a busca depois
    df_players['nome_completo'] = df_players['name_first'] + ' ' + df_players['name_last']
    df_players.to_sql('jogadores', conexao, if_exists='replace', index=False)
    print("OK!")
else:
    print("ERRO: atp_players.csv não encontrado.")

# 3. Carrega todas as Partidas
print("Carregando histórico de partidas")
# Descobre quais anos você tem baixados
anos = [arquivo.replace('atp_matches_', '').replace('.csv', '') 
        for arquivo in os.listdir(pasta_dados) 
        if arquivo.startswith('atp_matches_') and arquivo.endswith('.csv')]
anos.sort()

# Limpa a tabela de partidas se ela já existir para não duplicar dados
cursor.execute("DROP TABLE IF EXISTS partidas")

for ano in anos:
    caminho_match = os.path.join(pasta_dados, f'atp_matches_{ano}.csv')
    # low_memory=False evita avisos do Pandas sobre tipos de dados misturados
    df_matches = pd.read_csv(caminho_match, low_memory=False)
    
    # Injeta no banco empilhando (append)
    df_matches.to_sql('partidas', conexao, if_exists='append', index=False)
    print(f"  -> {ano} injetado.")

# 4. CRIANDO OS ÍNDICES (O segredo da velocidade extrema)
print("Criando índices", end=" ")
cursor.execute("CREATE INDEX IF NOT EXISTS idx_winner ON partidas(winner_id)")
cursor.execute("CREATE INDEX IF NOT EXISTS idx_loser ON partidas(loser_id)")
cursor.execute("CREATE INDEX IF NOT EXISTS idx_tourney ON partidas(tourney_name)")
cursor.execute("CREATE INDEX IF NOT EXISTS idx_nome_jogador ON jogadores(nome_completo)")
print("OK!")

conexao.close()
fim = time.time()

print("-" * 50)
print(f"Concluido em {round(fim - inicio, 1)} segundos!")