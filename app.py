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

ZODIAC_SIGNS = ["Ko\u00e7", "Bo\u011fa", "\u0130kizler", "Yenge\u00e7", "Aslan", "Ba\u015fak", "Terazi", "Akrep", "Yay", "O\u011flak", "Kova", "Bal\u0131k"]
PLANETS = ["Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto"]


def get_coordinates_and_timezone(location):
    url = f"https://api.opencagedata.com/geocode/v1/json?q={location}&key={OPENCAGE_API_KEY}"
    response = requests.get(url)
    response.raise_for_status()
    data = response.json()
    if not data['results']:
        raise ValueError("Konum bulunamad\u0131.")
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
        return jsonify({"error": "Do\u011fum tarihi ve konum zorunludur."}), 400

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


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
