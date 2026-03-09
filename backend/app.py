from flask import Flask, jsonify
from flask_cors import CORS
import csv
import os

# Inicializa o aplicativo Flask
app = Flask(__name__)
CORS(app)

# Criamos uma "rota" na web. O <nome_pesquisado> é o que o usuário vai digitar
@app.route('/api/jogador/<nome_pesquisado>', methods=['GET'])
def buscar_jogador(nome_pesquisado):
    diretorio_atual = os.path.dirname(os.path.abspath(__file__))
    caminho_arquivo = os.path.join(diretorio_atual, '..', 'dados', 'atp_players.csv')
    try:
        with open(caminho_arquivo, mode='r', encoding='utf-8') as arquivo:
            leitor_csv = csv.reader(arquivo)
            next(leitor_csv) # Pula a primeira linha
            
            for linha in leitor_csv:
                nome_completo = f"{linha[1]} {linha[2]}".lower()
                
                if nome_pesquisado.lower() in nome_completo:
                    # Em vez de um texto simples, agora criamos um Dicionário Python
                    # O Flask vai converter isso automaticamente para JSON!
                    dados_jogador = {
                        "nome": f"{linha[1]} {linha[2]}",
                        "pais": linha[5],
                        "mao_dominante": "Destro" if linha[3] == "R" else "Canhoto" if linha[3] == "L" else "Outro"
                    }
                    return jsonify(dados_jogador)
            
            # Se o loop acabar e não achar ninguém, retorna um erro 404 (Não Encontrado)
            return jsonify({"erro": "Jogador não encontrado"}), 404
            
    except FileNotFoundError:
        return jsonify({"erro": "Arquivo não encontrado no servidor"}), 500

if __name__ == '__main__':
    # O debug=True é mágico: ele reinicia o servidor sozinho toda vez que tu salvar o arquivo!
    app.run(debug=True)