import sqlite3
import os

diretorio_atual = os.path.dirname(os.path.abspath(__file__))
caminho_db = os.path.join(diretorio_atual, '..', 'dados', 'tennis.db')

conexao = sqlite3.connect(caminho_db)
cursor = conexao.cursor()

print("🧹 Iniciando a faxina global (Algoritmo de Unificação)...")

# 1. Regras universais (aplica no banco todo de uma vez)
print("Removendo prefixos e espaços duplos...")
cursor.execute("UPDATE partidas SET tourney_name = SUBSTR(tourney_name, 5) WHERE tourney_name LIKE 'ATP %'")
cursor.execute("UPDATE partidas SET tourney_name = TRIM(tourney_name)")
cursor.execute("UPDATE partidas SET tourney_name = REPLACE(tourney_name, '  ', ' ')")
conexao.commit()

# 2. Lógica de votação para unificar maiúsculas/minúsculas
print("Analisando grafias corretas...")
cursor.execute("SELECT tourney_name, COUNT(*) as qtd FROM partidas GROUP BY tourney_name")
todos_torneios = cursor.fetchall()

# Dicionário para guardar o nome que aparece mais vezes (a "grafia oficial")
oficiais = {}
for nome, qtd in todos_torneios:
    if not nome: continue
    nome_lower = nome.lower()
    
    # Se ainda não existe no dicionário, ou se tem mais "votos" que o anterior, assume o posto
    if nome_lower not in oficiais or qtd > oficiais[nome_lower][1]:
        oficiais[nome_lower] = (nome, qtd)

# 3. Executa a padronização
print("Corrigindo erros de digitação...")
atualizacoes = 0
for nome, _ in todos_torneios:
    if not nome: continue
    nome_lower = nome.lower()
    grafia_oficial = oficiais[nome_lower][0]

    # Se a grafia atual é diferente da oficial, o SQL corrige
    if nome != grafia_oficial:
        cursor.execute("UPDATE partidas SET tourney_name = ? WHERE tourney_name = ?", (grafia_oficial, nome))
        atualizacoes += 1

conexao.commit()
conexao.close()

print(f"✨ Limpeza global concluída! {atualizacoes} variações de nomes foram esmagadas e unificadas em todo o banco de dados.")