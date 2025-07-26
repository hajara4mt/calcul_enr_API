from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from app.db.database import get_session
from app.models.project_model import Projects 

router = APIRouter()

@router.get("/projets/utilisateur/{id_utilisateur}")
def get_projets_by_utilisateur(id_utilisateur: str, session: Session = Depends(get_session)):
    statement = select(Projects).where(Projects.id_utilisateur == id_utilisateur)
    projets = session.exec(statement).all()

    if not projets:
        raise HTTPException(status_code=404, detail="Aucun projet trouvé pour cet utilisateur")

    return [projet.model_dump() for projet in projets]