import os
import requests
import time

# Configurando o caminho para a tua pasta 'dados'
diretorio_atual = os.path.dirname(os.path.abspath(__file__))
pasta_dados = os.path.join(diretorio_atual, '..', 'dados')

# Se a pasta 'dados' não existir por algum motivo, ele cria
os.makedirs(pasta_dados, exist_ok=True)

ano_inicial = 1968
ano_final = 2024

print("🤖 Iniciando o robô de extração de dados da ATP...")
print("-" * 50)

for ano in range(ano_inicial, ano_final + 1):
    nome_arquivo = f"atp_matches_{ano}.csv"
    caminho_arquivo = os.path.join(pasta_dados, nome_arquivo)
    
    # Otimização: Se o arquivo já estiver na pasta (como o de 2023), ele pula!
    if os.path.exists(caminho_arquivo):
        print(f"✅ {ano}: Arquivo já existe. Pulando...")
        continue
        
    # URL direta para o arquivo bruto (raw) no GitHub do Jeff Sackmann
    url = f"https://raw.githubusercontent.com/JeffSackmann/tennis_atp/master/{nome_arquivo}"
    
    print(f"⬇️ Baixando temporada {ano}...", end=" ")
    
    try:
        resposta = requests.get(url)
        
        # O código 200 significa "Sucesso" na web
        if resposta.status_code == 200:
            with open(caminho_arquivo, 'wb') as arquivo:
                arquivo.write(resposta.content)
            print("OK!")
        else:
            print(f"Falha (Erro HTTP {resposta.status_code})")
            
    except Exception as e:
        print(f"Erro de conexão: {e}")
        
    # BOA PRÁTICA: Uma pausa de 1 segundo entre os downloads.
    # Isso evita que o GitHub bloqueie o teu IP por achar que é um ataque DDoS.
    time.sleep(1)

print("-" * 50)
print("🎉 Atualização concluída! A tua base de dados agora é histórica.")