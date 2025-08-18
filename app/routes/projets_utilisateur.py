from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from sqlalchemy import func
from app.db.database import get_session
from app.models.project_model import Projects
from app.models.output import output as Output
from app.models.inputs import input as Input

router = APIRouter()

def _iso(dt):
    return dt.isoformat() if dt is not None else None

@router.get("/projets/utilisateur/{id_utilisateur_primaire}")
def get_projets_by_utilisateur(id_utilisateur_primaire: str, session: Session = Depends(get_session)):
    # --- Sous-requête 1 : dernière date de modélisation par projet
    out_last_sq = (
        select(
            Output.id_projet,
            func.max(Output.data_modelisation_derniere).label("date_modelisation_derniere"),
        )
        .group_by(Output.id_projet)
        .subquery()
    )

    # --- Sous-requête 2 : dernière ligne d'input (nom + date_creation) par projet
    rn = func.row_number().over(
        partition_by=Input.id_projet,
        order_by=Input.date_creation.desc()
    ).label("rn")

    input_ranked = (
        select(
            Input.id_projet,
            Input.nom_projet,
            Input.date_creation,
            rn,
        )
        .subquery()
    )

    input_last_sq = (
        select(
            input_ranked.c.id_projet,
            input_ranked.c.nom_projet,
            input_ranked.c.date_creation.label("date_creation_projet"),
        )
        .where(input_ranked.c.rn == 1)
        .subquery()
    )

    # --- Requête principale (1 seule) : filtrée par utilisateur primaire
    q = (
        select(
            Projects.id_projet,
            input_last_sq.c.nom_projet,
            input_last_sq.c.date_creation_projet,
            out_last_sq.c.date_modelisation_derniere,
        )
        .select_from(Projects)
        .join(out_last_sq, Projects.id_projet == out_last_sq.c.id_projet, isouter=True)
        .join(input_last_sq, Projects.id_projet == input_last_sq.c.id_projet, isouter=True)
        .where(Projects.id_utilisateur_primaire == id_utilisateur_primaire)
        .order_by(Projects.id_projet)
    )

    rows = session.exec(q).all()
    if not rows:
        raise HTTPException(status_code=404, detail="Aucun projet trouvé pour cet utilisateur")

    projets_data = []
    for id_projet, nom_projet, date_creation, date_model in rows:
        projets_data.append({
            "id_projet": id_projet,
            "nom_projet": nom_projet,
            "date_modelisation_derniere": _iso(date_model),
            "date_creation_projet": _iso(date_creation),
        })

    return {
        "id_utilisateur_primaire": id_utilisateur_primaire,
        "projets": projets_data
    }
