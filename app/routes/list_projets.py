
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from app.db.database import get_session
from app.models.project_model import Projects
router = APIRouter()
@router.get("/projets/utilisateur")
def get_tous_utilisateurs_avec_projets(session: Session = Depends(get_session)):
    # Récupérer tous les projets
    projets = session.exec(select(Projects)).all()
    if not projets:
        raise HTTPException(status_code=404, detail="Aucun projet trouvé")
    # Dictionnaire pour regrouper par utilisateur
    utilisateurs_dict = {}
    for projet in projets:
        if projet.id_utilisateur not in utilisateurs_dict:
            utilisateurs_dict[projet.id_utilisateur] = []
        utilisateurs_dict[projet.id_utilisateur].append(projet.model_dump())
    # Transformer le dict en liste
    resultat = [
        {"id_utilisateur": user_id, "projets": projets}
        for user_id, projets in utilisateurs_dict.items()
    ]
    return resultat
