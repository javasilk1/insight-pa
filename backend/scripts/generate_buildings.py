import json
import os
import random
import uuid
from datetime import datetime

DEFAULT_OUTPUT_SQL = "/init-db/02_insert_buildings.sql"
DEFAULT_FRAZIONI_FILE = "/mock_data/frazioni.json"

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUTPUT_SQL = DEFAULT_OUTPUT_SQL if os.path.exists("/init-db") else os.path.join(BASE_DIR, "init-db", "02_insert_buildings.sql")
FRAZIONI_FILE = DEFAULT_FRAZIONI_FILE if os.path.exists(DEFAULT_FRAZIONI_FILE) else os.path.join(BASE_DIR, "mock_data", "frazioni.json")

ADDRESS_PREFIXES = ["Via", "Piazza", "Viale", "Corso", "Largo", "Vicolo"]
ADDRESS_NAMES = [
    "Cagliari", "Roma", "Garibaldi", "Mazzini", "Marconi", "Poetto",
    "Flumini", "Sant'Elena", "Fiume", "Sardegna", "Torre", "Is Pardinas",
    "Dei Pini", "Dei Ginepri", "Dei Lecci", "Europa", "Trieste", "Liguria"
]

RISK_DISTRIBUTION = [
    ("verde", 0.60),
    ("giallo", 0.30),
    ("rosso", 0.10),
]

STATUS_MAP = {
    "verde": "compliant",
    "giallo": "under_review",
    "rosso": "violation",
}

RISK_SCORE_RANGE = {
    "verde": (5, 25),
    "giallo": (35, 65),
    "rosso": (75, 95),
}

FRAZIONI_COORDS = {
    "centro": [39.2414, 9.1837],
    "flumini": [39.2200, 9.1600],
    "poetto": [39.1980, 9.1680],
    "geremeas": [39.2350, 9.1900],
    "mare_pintau": [39.2500, 9.1700],
}

COASTAL_FRAZIONI = {"poetto", "mare_pintau"}


def pick_risk_level():
    rnd = random.random()
    cumulative = 0.0
    for level, weight in RISK_DISTRIBUTION:
        cumulative += weight
        if rnd <= cumulative:
            return level
    return "verde"


def random_address():
    prefix = random.choice(ADDRESS_PREFIXES)
    name = random.choice(ADDRESS_NAMES)
    number = random.randint(1, 220)
    return f"{prefix} {name} {number}"


def jitter_coord(lat, lon, delta=0.005):
    return (
        round(lat + random.uniform(-delta, delta), 6),
        round(lon + random.uniform(-delta, delta), 6),
    )


def generate_cadastral_data(risk_level, frazione):
    base_sup = random.randint(80, 180)
    autorizzata = base_sup - random.randint(0, 20)
    catastale = base_sup + random.randint(0, 40)

    if risk_level == "verde":
        catastale = autorizzata
    elif risk_level == "giallo":
        catastale = autorizzata + random.randint(5, 20)
    else:
        catastale = autorizzata + random.randint(20, 60)

    if frazione in COASTAL_FRAZIONI:
        distanza_mare = random.randint(80, 260)
    else:
        distanza_mare = random.randint(320, 900)

    has_permesso = risk_level != "rosso"
    has_piscina = random.random() < (0.15 if risk_level == "verde" else 0.35)
    has_permesso_piscina = not (has_piscina and risk_level == "rosso")
    satellite_change_pct = random.randint(0, 15) if risk_level == "verde" else random.randint(10, 35)
    documenti_contrastanti = True if risk_level == "rosso" and random.random() < 0.5 else False

    return {
        "superficie_catastale": catastale,
        "superficie_autorizzata": autorizzata,
        "distanza_mare": distanza_mare,
        "has_permesso": has_permesso,
        "has_piscina": has_piscina,
        "has_permesso_piscina": has_permesso_piscina,
        "satellite_change_pct": satellite_change_pct,
        "documenti_contrastanti": documenti_contrastanti,
    }


def load_frazioni_config():
    if not os.path.exists(FRAZIONI_FILE):
        return None
    with open(FRAZIONI_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def main():
    random.seed(42)

    config = load_frazioni_config()
    if config:
        frazioni = config.get("frazioni", [])
        target_counts = {f["name"]: int(f.get("buildings", 10)) for f in frazioni}
    else:
        target_counts = {k: 10 for k in FRAZIONI_COORDS.keys()}

    total_buildings = sum(target_counts.values())
    if total_buildings < 50:
        scale = (50 // total_buildings) + 1
        target_counts = {k: v * scale for k, v in target_counts.items()}
        total_buildings = sum(target_counts.values())
    buildings = []

    for frazione, count in target_counts.items():
        base = FRAZIONI_COORDS.get(frazione)
        if not base:
            continue
        base_lat, base_lon = base
        for _ in range(count):
            lat, lon = jitter_coord(base_lat, base_lon)
            risk_level = pick_risk_level()
            risk_score = random.randint(*RISK_SCORE_RANGE[risk_level])
            address = random_address()
            cadastral_data = generate_cadastral_data(risk_level, frazione)

            buildings.append({
                "id": str(uuid.uuid4()),
                "address": address,
                "lat": lat,
                "lon": lon,
                "cadastral_data": cadastral_data,
                "area_name": frazione,
                "risk_score": float(risk_score),
                "status": STATUS_MAP[risk_level],
            })

    os.makedirs(os.path.dirname(OUTPUT_SQL), exist_ok=True)
    with open(OUTPUT_SQL, "w", encoding="utf-8") as sql_file:
        sql_file.write("-- Generated by generate_buildings.py\n")
        sql_file.write(f"-- {datetime.utcnow().isoformat()}Z\n\n")
        sql_file.write("INSERT INTO buildings (id, address, coordinates, cadastral_data, area_name, risk_score, status) VALUES\n")

        values = []
        for b in buildings:
            cadastral_json = json.dumps(b["cadastral_data"], ensure_ascii=False)
            # Escape single quotes in JSON for SQL
            cadastral_json_escaped = cadastral_json.replace("\\", "\\\\").replace("'", "''")
            address_escaped = b['address'].replace("'", "''")
            values.append(
                f"('{b['id']}', '{address_escaped}', "
                f"ST_GeogFromText('SRID=4326;POINT({b['lon']} {b['lat']})'), "
                f"'{cadastral_json_escaped}'::jsonb, '{b['area_name']}', {b['risk_score']}, '{b['status']}')"
            )

        sql_file.write(",\n".join(values))
        sql_file.write(";\n")

    # Stats
    stats = {"verde": 0, "giallo": 0, "rosso": 0}
    for b in buildings:
        for k, v in STATUS_MAP.items():
            if b["status"] == v:
                stats[k] += 1

    print("Generazione completata:")
    print(f"- Totale edifici: {len(buildings)}")
    print(f"- Verde: {stats['verde']} | Giallo: {stats['giallo']} | Rosso: {stats['rosso']}")
    print(f"- Output SQL: {OUTPUT_SQL}")


if __name__ == "__main__":
    main()
