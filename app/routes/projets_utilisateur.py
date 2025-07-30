from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from app.db.database import get_session
from app.models.project_model import Projects
from app.models.output import output
from app.models.inputs import input
from typing import List
from datetime import datetime

router = APIRouter()

@router.get("/projets/utilisateur/{id_utilisateur}")
def get_projets_by_utilisateur(id_utilisateur: str, session: Session = Depends(get_session)):
    projets = session.exec(
        select(Projects).where(Projects.id_utilisateur == id_utilisateur)
    ).all()

    if not projets:
        raise HTTPException(status_code=404, detail="Aucun projet trouvé pour cet utilisateur")

    projets_data = []
    for projet in projets:
        # Sélectionne uniquement la colonne utile pour éviter le parsing JSON
        dernier_output = session.exec(
            select(output.data_modelisation_derniere)
            .where(output.id_projet == projet.id_projet)
            .order_by(output.data_modelisation_derniere.desc())
        ).first()

        dernier_input = session.exec(
            select(input.nom_projet)
            .where(input.id_projet == projet.id_projet)
            .order_by(input.date_creation.desc())
        ).first()

        projets_data.append({
            "id_projet": projet.id_projet,
            "nom_projet": dernier_input if dernier_input else None,
            "date_modelisation_derniere": dernier_output if dernier_output else None

        })

    return {
        "id_utilisateur": id_utilisateur,
        "projets": projets_data
    }
