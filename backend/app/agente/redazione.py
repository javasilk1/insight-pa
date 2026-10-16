"""
Redazione del testo di ogni difformità, con le norme trovate dalla ricerca.

Il modello di linguaggio scrive descrizione e valutazione e sceglie quali
passaggi normativi citare, ma non decide tipo, entità, gravità o esito: quelli
arrivano dal confronto. Le citazioni sono controllate: un articolo che non era
tra i passaggi trovati viene scartato.
"""
import os

from pydantic import BaseModel, Field

from .catalogo import CATALOGO
from .confronto import Riscontro
from .norme import Passaggio, carica_corpus

CITAZIONI = {p.id: p.citazione for p in carica_corpus()}

ISTRUZIONI = """Sei l'assistente di un geometra italiano che verifica lo stato legittimo di un immobile.
Ti do una difformità già individuata confrontando titolo edilizio, catasto e rilievo, e alcuni passaggi normativi.
Scrivi:
- descrizione: cosa è diverso tra i documenti, in 1-2 frasi, usando solo i fatti forniti;
- valutazione: cosa comporta e quali strade ci sono (tolleranza, edilizia libera, sanatoria, variazione catastale), in 1-3 frasi;
- articoli_citati: gli id dei passaggi normativi su cui si basa la valutazione, solo tra quelli forniti.
Non cambiare numeri, tipo o gravità. Non dire che l'abuso è sanabile o insanabile in modo definitivo: è una bozza che il tecnico firmerà."""


class TestoDifformita(BaseModel):
    descrizione: str
    valutazione: str
    articoli_citati: list[str] = Field(default_factory=list, description="id dei passaggi normativi citati")


def domanda(r: Riscontro) -> str:
    """La query per la ricerca nelle norme: tipo, testo di base e fatti, senza i numeri."""
    cat = CATALOGO[r.tipo]
    base = cat.descrizione.format_map({"dest_vecchia": "", "dest_nuova": "", **r.segnaposti})
    return f"{r.tipo.replace('_', ' ')}. {base} {cat.valutazione} {r.valutazione_extra}"


def riferimento(articoli: list[str]) -> str:
    return "; ".join(CITAZIONI[a] for a in articoli if a in CITAZIONI)


class RedattoreTesto:
    """Testo di base del catalogo e articoli previsti per il tipo: nessun modello, risultato ripetibile."""
    nome = "testo"
    modello = None

    def redigi(self, r: Riscontro, passaggi: list[Passaggio]) -> tuple[TestoDifformita, list[str]]:
        cat = CATALOGO[r.tipo]
        valutazione = f"{cat.valutazione} {r.valutazione_extra}".strip()
        testo = TestoDifformita(
            descrizione=cat.descrizione.format_map({"dest_vecchia": "", "dest_nuova": "", **r.segnaposti}),
            valutazione=valutazione, articoli_citati=r.articoli,
        )
        return testo, []


class RedattoreModello:
    """Testo scritto da un modello di linguaggio (LangChain) con output strutturato."""
    nome = "modello"

    def __init__(self, llm, modello: str | None = None):
        self.modello = modello
        self._llm = llm.with_structured_output(TestoDifformita)

    def redigi(self, r: Riscontro, passaggi: list[Passaggio]) -> tuple[TestoDifformita, list[str]]:
        norme = "\n\n".join(f"[{p.id}] {p.citazione} - {p.titolo}\n{p.testo}" for p in passaggi)
        messaggio = (
            f"Tipo: {r.tipo.replace('_', ' ')} (ambito {r.ambito}, gravità {r.gravita})\n"
            f"Entità: {r.entita or 'non quantificata'}\n"
            "Fatti dai documenti:\n" + "\n".join(f"- {f}" for f in r.fatti)
            + f"\n\nPassaggi normativi:\n{norme}"
        )
        testo: TestoDifformita = self._llm.invoke([("system", ISTRUZIONI), ("human", messaggio)])
        trovati = {p.id for p in passaggi}
        validi = [a for a in testo.articoli_citati if a in trovati]
        note = [f"citazione scartata: {a} non era tra i passaggi trovati" for a in testo.articoli_citati if a not in trovati]
        if not validi:
            validi = [a for a in r.articoli if a in trovati] or r.articoli
            note.append("nessuna citazione valida dal modello: uso gli articoli previsti per il tipo")
        testo.articoli_citati = validi
        return testo, note


def crea_redattore(nome: str):
    """testo | claude | ollama"""
    if nome == "testo":
        return RedattoreTesto()
    if nome == "claude":
        from langchain_anthropic import ChatAnthropic

        modello = os.getenv("CLAUDE_MODEL", "claude-opus-5")
        return RedattoreModello(ChatAnthropic(model=modello, max_tokens=2000), modello)
    if nome == "ollama":
        from langchain_ollama import ChatOllama

        modello = os.getenv("OLLAMA_MODEL", "qwen2.5:7b")
        url = os.getenv("OLLAMA_URL", "http://localhost:11434")
        return RedattoreModello(ChatOllama(model=modello, base_url=url, temperature=0), modello)
    raise ValueError(f"redattore sconosciuto: {nome}")
