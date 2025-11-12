from flask import Flask, render_template, request
import os
import googlemaps
from dotenv import load_dotenv

app = Flask(__name__)
load_dotenv()
API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")
gmaps = googlemaps.Client(key=API_KEY)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/buscar', methods=['POST'])
def buscar():
    cep = request.form['cep']
    tipo = request.form['tipo']

    results = gmaps.geocode(cep + ", Brasil")
    if not results:
        return "CEP não encontrado."

    loc = results[0]["geometry"]["location"]
    lojas = gmaps.places_nearby(location=(loc["lat"], loc["lng"]), rank_by="distance", keyword=tipo)
    if not lojas["results"]:
        return "Nenhuma loja encontrada perto desse CEP."

    loja = lojas["results"][0]
    nome = loja["name"]
    endereco = loja.get("vicinity", "Endereço não disponível")

    return f"<h1>🏬 Loja mais próxima: {nome}</h1><p>{endereco}</p>"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
