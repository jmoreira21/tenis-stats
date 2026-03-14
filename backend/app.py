from flask import Flask
from flask_cors import CORS

from routes_auxilio import auxilio_bp
from routes_jogador import jogador_bp
from routes_torneio import torneio_bp
from routes_h2h import h2h_bp

app = Flask(__name__)
CORS(app)

app.register_blueprint(auxilio_bp)
app.register_blueprint(jogador_bp)
app.register_blueprint(torneio_bp)
app.register_blueprint(h2h_bp)

if __name__ == '__main__':
    app.run(debug=True)