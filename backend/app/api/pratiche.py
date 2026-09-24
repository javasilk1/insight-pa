from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, Response

from models.pratica import AnalisiPratica, PraticaSintesi, RichiestaRelazione
from services.pratiche_service import pratiche_service

router = APIRouter(prefix="/api/pratiche", tags=["pratiche"])


@router.get("", response_model=list[PraticaSintesi])
def lista_pratiche():
    return pratiche_service.lista()


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
