from flask import Flask, request, jsonify
from flask_cors import CORS
import swisseph as swe
from datetime import datetime
import pytz
import requests
import os

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": ["*"]}})

# Swiss Ephemeris
EPHE_PATH = os.environ.get('EPHE_PATH', './ephe')
swe.set_ephe_path(EPHE_PATH)

# OpenCage API Key
OPENCAGE_API_KEY = os.getenv("OPENCAGE_API_KEY", "YOUR_KEY_HERE")

ZODIAC_SIGNS = ["Koç", "Boğa", "İkizler", "Yengeç", "Aslan", "Başak", "Terazi", "Akrep", "Yay", "Oğlak", "Kova", "Balık"]
PLANETS = ["Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto"]

def get_coordinates_and_timezone(location):
    url = f"https://api.opencagedata.com/geocode/v1/json?q={location}&key={OPENCAGE_API_KEY}"
    response = requests.get(url)
    response.raise_for_status()
    data = response.json()
    if not data['results']:
        raise ValueError("Konum bulunamadı.")
    coords = data['results'][0]['geometry']
    tz = data['results'][0]['annotations']['timezone']['name']
    return coords, tz

def degree_to_sign_and_position(degree):
    sign_index = int(degree // 30)
    sign = ZODIAC_SIGNS[sign_index]
    degree_in_sign = round(degree % 30, 2)
    return sign, degree_in_sign

@app.route('/natal-chart', methods=['POST'])
def natal_chart():
    data = request.json
    birth_date = data.get('birth_date')
    location = data.get('location')

    if not birth_date or not location:
        return jsonify({"error": "Doğum tarihi ve konum zorunludur."}), 400

    coords, timezone = get_coordinates_and_timezone(location)
    tz = pytz.timezone(timezone)
    dt = tz.localize(datetime.strptime(birth_date, "%Y-%m-%d %H:%M"))
    dt_utc = dt.astimezone(pytz.utc)

    jd = swe.julday(dt_utc.year, dt_utc.month, dt_utc.day, dt_utc.hour + dt_utc.minute / 60)

    lat, lon = coords['lat'], coords['lng']
    houses, _ = swe.houses(jd, lat, lon, b'P')

    results = {}
    for planet in PLANETS:
        planet_id = getattr(swe, planet.upper())
        pos, _ = swe.calc_ut(jd, planet_id)
        sign, deg = degree_to_sign_and_position(pos[0])
        results[planet] = {"sign": sign, "degree": deg}

    return jsonify({"planets": results, "timezone": timezone})

@app.route('/transit', methods=['GET', 'POST'])
def transit_chart():
    data = request.json
    birth_date = data.get('birth_date')
    location = data.get('location')
    target_date = data.get('target_date')

    if not birth_date or not location or not target_date:
        return jsonify({"error": "Doğum tarihi, konum ve hedef tarih zorunludur."}), 400

    coords, timezone = get_coordinates_and_timezone(location)
    tz = pytz.timezone(timezone)

    natal_dt = tz.localize(datetime.strptime(birth_date, "%Y-%m-%d %H:%M"))
    natal_dt_utc = natal_dt.astimezone(pytz.utc)
    natal_jd = swe.julday(natal_dt_utc.year, natal_dt_utc.month, natal_dt_utc.day, natal_dt_utc.hour + natal_dt_utc.minute / 60)

    target_dt = tz.localize(datetime.strptime(target_date, "%Y-%m-%d %H:%M"))
    target_dt_utc = target_dt.astimezone(pytz.utc)
    transit_jd = swe.julday(target_dt_utc.year, target_dt_utc.month, target_dt_utc.day, target_dt_utc.hour + target_dt_utc.minute / 60)

    natal_positions = {}
    for planet in PLANETS:
        pid = getattr(swe, planet.upper())
        pos, _ = swe.calc_ut(natal_jd, pid)
        natal_positions[planet] = pos[0]

    transit_positions = {}
    for planet in PLANETS:
        pid = getattr(swe, planet.upper())
        pos, _ = swe.calc_ut(transit_jd, pid)
        sign, deg = degree_to_sign_and_position(pos[0])
        transit_positions[planet] = {"sign": sign, "degree": deg}

    def get_aspect(a, b):
        diff = abs((a - b) % 360)
        if diff > 180:
            diff = 360 - diff
        if abs(diff - 0) <= 5:
            return 'conjunction'
        elif abs(diff - 90) <= 5:
            return 'square'
        elif abs(diff - 120) <= 5:
            return 'trine'
        elif abs(diff - 180) <= 5:
            return 'opposition'
        return None

    aspects = []
    for t_planet, t_info in transit_positions.items():
        t_deg = t_info["degree"] + ZODIAC_SIGNS.index(t_info["sign"]) * 30
        for n_planet, n_deg in natal_positions.items():
            aspect = get_aspect(t_deg, n_deg)
            if aspect:
                aspects.append({
                    "transit_planet": t_planet,
                    "natal_planet": n_planet,
                    "aspect": aspect
                })

    return jsonify({
        "transits": transit_positions,
        "aspects": aspects,
        "timezone": timezone
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
