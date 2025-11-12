from flask import Flask
app = Flask(__name__)

@app.route('/')
def home():
    return "✅ Site da Loja Próxima está rodando no Render!"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
import os
import webbrowser
from urllib.parse import urlencode
from dotenv import load_dotenv
import googlemaps

# ------------- Config -------------
load_dotenv()  # lê .env
API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")
if not API_KEY:
    raise RuntimeError("Coloque sua chave no arquivo .env como GOOGLE_MAPS_API_KEY=...")

gmaps = googlemaps.Client(key=API_KEY)

def geocode_cep(cep: str):
    """Converte um CEP brasileiro em coordenadas (lat, lng) usando Geocoding API."""
    results = gmaps.geocode(cep + ", Brasil") # type: ignore
    if not results:
        raise ValueError("CEP não encontrado.")
    loc = results[0]["geometry"]["location"]
    return (loc["lat"], loc["lng"]), results[0]["formatted_address"]

def buscar_lojas(lat: float, lng: float, termo: str, max_results: int = 10):
    """Busca lojas próximas ao ponto (lat,lng) usando Places Nearby."""
    places = gmaps.places_nearby( # type: ignore
        location=(lat, lng),
        rank_by="distance",
        keyword=termo,
        open_now=False
    )
    return places.get("results", [])[:max_results]

def medir_distancias(origem_latlng, destinos_place_ids):
    """Usa Distance Matrix API para pegar distância e tempo até vários destinos de uma vez."""
    if not destinos_place_ids:
        return []
    destinos = [f"place_id:{pid}" for pid in destinos_place_ids]
    matrix = gmaps.distance_matrix( # type: ignore
        origins=[origem_latlng],
        destinations=destinos,
        mode="driving",
        language="pt-BR"
    )
    rows = matrix.get("rows", [])
    if not rows:
        return []
    elements = rows[0].get("elements", [])
    out = []
    for el in elements:
        if el.get("status") == "OK":
            out.append({
                "distance_text": el["distance"]["text"],
                "duration_text": el["duration"]["text"],
                "distance_value": el["distance"]["value"],
            })
        else:
            out.append({
                "distance_text": "N/D",
                "duration_text": "N/D",
                "distance_value": 10**12
            })
    return out

def coords_do_place(place_id: str):
    """Pega lat/lng via Place Details (faz parte da Places API)."""
    det = gmaps.place(place_id=place_id, language="pt-BR") # type: ignore
    res = det.get("result", {})
    loc = res.get("geometry", {}).get("location", {})
    if not loc:
        raise ValueError("Não foi possível obter as coordenadas do destino.")
    return loc["lat"], loc["lng"], res.get("formatted_address") or res.get("name") or "Destino"

def abrir_rota_no_maps(origem_lat, origem_lng, destino_lat, destino_lng):
    """Abre no navegador a rota do Google Maps usando coordenadas do destino."""
    params = {
        "api": 1,
        "origin": f"{origem_lat},{origem_lng}",
        "destination": f"{destino_lat},{destino_lng}",
        "travelmode": "driving"
    }
    url = "https://www.google.com/maps/dir/?" + urlencode(params)
    webbrowser.open(url)

def main():
    print("=== Buscar loja mais próxima (Google Maps) ===")
    cep = input("Qual o seu CEP? ").strip()
    tipo = input("Qual o tipo de loja que você está procurando? ").strip()

    (lat, lng), end_formatado = geocode_cep(cep)
    print(f"\nSua localização: {end_formatado} ({lat:.6f}, {lng:.6f})")

    lojas = buscar_lojas(lat, lng, tipo)
    if not lojas:
        print("Nenhuma loja encontrada.")
        return

    place_ids = [l["place_id"] for l in lojas]
    dist_infos = medir_distancias((lat, lng), place_ids)

    print("\nLojas próximas:")
    melhores = []
    for i, (loja, info) in enumerate(zip(lojas, dist_infos), start=1):
        nome = loja.get("name", "Sem nome")
        end = loja.get("vicinity") or "Endereço não disponível"
        print(f"{i:02d}. {nome}")
        print(f"    Endereço: {end}")
        print(f"    Distância/Tempo: {info['distance_text']} / {info['duration_text']}")
        melhores.append({
            "place_id": loja["place_id"],
            "nome": nome,
            "endereco": end,
            "dist_m": info["distance_value"]
        })

    melhores.sort(key=lambda x: x["dist_m"])
    melhor = melhores[0]
    dest_lat, dest_lng, dest_label = coords_do_place(melhor["place_id"])
    print(f"\n🏬 Loja mais próxima: {melhor['nome']} - {melhor['endereco']}")
    print(f"Destino: {dest_label} ({dest_lat:.6f}, {dest_lng:.6f})")
    abrir_rota_no_maps(lat, lng, dest_lat, dest_lng)
    print("\nAbrindo no navegador...")

if __name__ == "__main__":
    main()

