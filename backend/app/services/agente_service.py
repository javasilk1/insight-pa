"""
Esegue l'agente di verifica su una pratica e tiene l'ultimo risultato in memoria.

Se per la pratica c'è già un'estrazione completata con lo stesso estrattore,
l'agente la riusa invece di rileggere i PDF. Come le estrazioni, i risultati
restano in memoria fino al riavvio: diventeranno righe su Postgres.
"""
import threading

from agente.grafo import crea_grafo
from agente.norme import ricerca_predefinita
from agente.redazione import crea_redattore
from estrazione.estrattori import ESTRATTORI
from models.pratica import AnalisiPratica
from services.estrazione_service import estrazione_service
from services.pratiche_service import pratiche_service


class AgenteService:
    def __init__(self):
        self._risultati: dict[str, AnalisiPratica] = {}
        self._ricerca = None
        self._lock = threading.Lock()

    @property
    def ricerca(self):
        if self._ricerca is None:
            self._ricerca = ricerca_predefinita()
        return self._ricerca

    def ultimo(self, pratica_id: str) -> AnalisiPratica | None:
        return self._risultati.get(pratica_id)

    def esegui(self, pratica_id: str, estrattore: str, redattore: str) -> AnalisiPratica | None:
        base = pratiche_service.analisi(pratica_id)
        da_estrarre = pratiche_service.da_estrarre(pratica_id)
        if not base or not da_estrarre:
            return None
        cartella, files, _ = da_estrarre
        stato_iniziale = {"cartella": str(cartella), "files": files}
        estrazione = estrazione_service.stato(pratica_id)
        if estrazione and estrazione["stato"] == "completata" and estrazione["estrattore"] == estrattore:
            stato_iniziale["documenti"] = {d["file"]: {"tipo": d["tipo"], "dati": d["dati"], "note": d["note"]}
                                           for d in estrazione["documenti"]}
        grafo = crea_grafo(ESTRATTORI[estrattore](), self.ricerca, crea_redattore(redattore))
        out = grafo.invoke(stato_iniziale)
        analisi = AnalisiPratica(
            id=base.id, origine="agente", esito=out["esito"], sintesi=out["sintesi"], immobile=base.immobile,
            documenti=base.documenti,
            dati_estratti={f: d["dati"] for f, d in out["documenti"].items()},
            difformita=out["difformita"], verifiche=out.get("verifiche", []),
            agente={"estrattore": estrattore, "redattore": redattore, "ricerca": self.ricerca.nome,
                    "passi": out["passi"], "note": out.get("note", [])},
        )
        with self._lock:
            self._risultati[pratica_id] = analisi
        return analisi


agente_service = AgenteService()
