from fastapi import APIRouter, BackgroundTasks, HTTPException
from fastapi.responses import FileResponse, Response

from models.pratica import AnalisiPratica, PraticaSintesi, RichiestaEstrazione, RichiestaRelazione
from services.estrazione_service import estrazione_service
from services.pratiche_service import pratiche_service

router = APIRouter(prefix="/api/pratiche", tags=["pratiche"])


@router.get("", response_model=list[PraticaSintesi])
def lista_pratiche():
    return pratiche_service.lista()


@router.get("/estrattori")
def estrattori():
    return estrazione_service.estrattori()


@router.get("/{pratica_id}", response_model=AnalisiPratica)
def analisi_pratica(pratica_id: str):
    analisi = pratiche_service.analisi(pratica_id)
    if not analisi:
        raise HTTPException(status_code=404, detail="Pratica non trovata")
    return analisi


@router.get("/{pratica_id}/documenti/{file}")
def documento(pratica_id: str, file: str):
    path = pratiche_service.documento(pratica_id, file)
    if not path:
        raise HTTPException(status_code=404, detail="Documento non trovato")
    return FileResponse(path, media_type="application/pdf", headers={"Content-Disposition": f'inline; filename="{file}"'})


@router.post("/{pratica_id}/relazione")
def relazione(pratica_id: str, req: RichiestaRelazione):
    analisi = pratiche_service.analisi(pratica_id)
    if not analisi:
        raise HTTPException(status_code=404, detail="Pratica non trovata")
    data = pratiche_service.relazione_docx(analisi, req)
    return Response(
        content=data,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f'attachment; filename="relazione_{pratica_id}.docx"'},
    )


@router.get("/{pratica_id}/estrazione")
def stato_estrazione(pratica_id: str):
    stato = estrazione_service.stato(pratica_id)
    if not stato:
        raise HTTPException(status_code=404, detail="Nessuna estrazione per questa pratica")
    return stato


@router.post("/{pratica_id}/estrazione", status_code=202)
def avvia_estrazione(pratica_id: str, req: RichiestaEstrazione, background: BackgroundTasks):
    pratica = pratiche_service.da_estrarre(pratica_id)
    if not pratica:
        raise HTTPException(status_code=404, detail="Pratica non trovata")
    info = {e["nome"]: e for e in estrazione_service.estrattori()}
    if not info[req.estrattore]["disponibile"]:
        raise HTTPException(status_code=400, detail=info[req.estrattore]["nota"])
    cartella, files, attesi = pratica
    stato = estrazione_service.prenota(pratica_id, req.estrattore, len(files))
    if not stato:
        raise HTTPException(status_code=409, detail="Estrazione già in corso")
    background.add_task(estrazione_service.esegui, pratica_id, req.estrattore, cartella, files, attesi)
    return stato
