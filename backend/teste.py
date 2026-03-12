import sqlite3
import os

diretorio_atual = os.path.dirname(os.path.abspath(__file__))
caminho_db = os.path.join(diretorio_atual, '..', 'dados', 'tennis.db')

conexao = sqlite3.connect(caminho_db)
cursor = conexao.cursor()

print("🔍 Verificando os últimos anos salvos no banco de dados...")
try:
    # Pega os 15 anos mais recentes e conta quantas partidas tem em cada um
    anos = cursor.execute('''
        SELECT SUBSTR(CAST(tourney_date AS TEXT), 1, 4) AS ano, COUNT(*) 
        FROM partidas 
        GROUP BY ano 
        ORDER BY ano DESC 
        LIMIT 15
    ''').fetchall()
    
    for ano in anos:
        print(f"Ano: {ano[0]} -> Partidas registradas: {ano[1]}")
except Exception as e:
    print(f"Erro ao ler o banco: {e}")

conexao.close()