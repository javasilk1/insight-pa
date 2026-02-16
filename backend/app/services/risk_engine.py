class RiskEngine:
    """Motore di calcolo rischio per abusivismo edilizio."""

    def __init__(self):
        self.rules = {
            "superficie_eccedente": {
                "weight": 40,
                "description": "Superficie catastale eccede quella autorizzata",
            },
            "vincolo_costiero": {
                "weight": 30,
                "description": "Edificio entro 300m dalla costa (vincolo costiero)",
            },
            "permesso_mancante": {
                "weight": 20,
                "description": "Nessun permesso di costruire trovato",
            },
            "piscina_abusiva": {
                "weight": 15,
                "description": "Piscina realizzata senza permesso",
            },
            "variazione_satellite": {
                "weight": 10,
                "description": "Change detection satellitare >20%",
            },
            "documento_contrasto": {
                "weight": 25,
                "description": "Documenti presentati in contraddizione tra loro",
            },
        }

    def calculate(self, building_data: dict) -> dict:
        """
        Calcola il risk score sulla base dei dati dell'edificio.

        Parametri attesi in building_data:
            - superficie_catastale (float)
            - superficie_autorizzata (float)
            - distanza_mare (float, metri)
            - has_permesso (bool)
            - has_piscina (bool)
            - has_permesso_piscina (bool)
            - satellite_change_pct (float, 0-100)
            - documenti_contrastanti (bool)
        """
        score = 0.0
        triggered = []

        # 1. Superficie eccedente: +40% se catastale > autorizzata
        sup_cat = building_data.get("superficie_catastale", 0)
        sup_aut = building_data.get("superficie_autorizzata", 0)
        if sup_cat > 0 and sup_aut > 0 and sup_cat > sup_aut:
            score += self.rules["superficie_eccedente"]["weight"]
            triggered.append({
                "rule": "superficie_eccedente",
                "weight": self.rules["superficie_eccedente"]["weight"],
                "detail": f"Catastale {sup_cat}m² > Autorizzata {sup_aut}m² (+{sup_cat - sup_aut}m²)",
            })

        # 2. Vincolo costiero: +30% se distanza < 300m
        distanza = building_data.get("distanza_mare")
        if distanza is not None and distanza < 300:
            score += self.rules["vincolo_costiero"]["weight"]
            triggered.append({
                "rule": "vincolo_costiero",
                "weight": self.rules["vincolo_costiero"]["weight"],
                "detail": f"Distanza dal mare: {distanza}m (< 300m)",
            })

        # 3. Permesso mancante: +20% se nessun permesso
        has_permesso = building_data.get("has_permesso", True)
        if not has_permesso:
            score += self.rules["permesso_mancante"]["weight"]
            triggered.append({
                "rule": "permesso_mancante",
                "weight": self.rules["permesso_mancante"]["weight"],
                "detail": "Nessun permesso di costruire trovato",
            })

        # 4. Piscina abusiva: +15% se piscina senza permesso
        has_piscina = building_data.get("has_piscina", False)
        has_permesso_piscina = building_data.get("has_permesso_piscina", True)
        if has_piscina and not has_permesso_piscina:
            score += self.rules["piscina_abusiva"]["weight"]
            triggered.append({
                "rule": "piscina_abusiva",
                "weight": self.rules["piscina_abusiva"]["weight"],
                "detail": "Piscina presente senza permesso",
            })

        # 5. Variazione satellite: +10% se change detection > 20%
        sat_change = building_data.get("satellite_change_pct", 0)
        if sat_change > 20:
            score += self.rules["variazione_satellite"]["weight"]
            triggered.append({
                "rule": "variazione_satellite",
                "weight": self.rules["variazione_satellite"]["weight"],
                "detail": f"Change detection: {sat_change}% (> 20%)",
            })

        # 6. Documenti in contrasto: +25% se contraddittori
        docs_contrasto = building_data.get("documenti_contrastanti", False)
        if docs_contrasto:
            score += self.rules["documento_contrasto"]["weight"]
            triggered.append({
                "rule": "documento_contrasto",
                "weight": self.rules["documento_contrasto"]["weight"],
                "detail": "Documenti presentati sono contraddittori",
            })

        # Cap a 100
        score = min(score, 100.0)

        return {
            "risk_score": score,
            "color": self.get_color(score),
            "level": self.get_level(score),
            "triggered_rules": triggered,
            "total_rules": len(self.rules),
            "rules_triggered": len(triggered),
        }

    @staticmethod
    def get_color(score: float) -> str:
        if score < 30:
            return "green"
        elif score < 70:
            return "yellow"
        return "red"

    @staticmethod
    def get_level(score: float) -> str:
        if score < 30:
            return "VERDE"
        elif score < 70:
            return "GIALLO"
        return "ROSSO"


# Singleton
risk_engine = RiskEngine()
