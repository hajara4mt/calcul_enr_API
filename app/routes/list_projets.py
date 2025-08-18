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

@router.get("/projets/utilisateur")
def get_tous_utilisateurs_primaires_avec_projets(session: Session = Depends(get_session)):
    # --- Sous-requête 1 : dernière date de modélisation par projet (MAX)
    out_last_sq = (
        select(
            Output.id_projet,
            func.max(Output.data_modelisation_derniere).label("date_modelisation_derniere"),
        )
        .group_by(Output.id_projet)
        .subquery()
    )

    # --- Sous-requête 2 : dernière ligne d'input par projet (ROW_NUMBER = 1)
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
            input_ranked.c.date_creation,
        )
        .where(input_ranked.c.rn == 1)
        .subquery()
    )

    # --- Requête principale : Projects LEFT JOIN out_last_sq & input_last_sq
    q = (
        select(
            Projects.id_utilisateur_primaire,
            Projects.id_projet,
            input_last_sq.c.nom_projet,
            input_last_sq.c.date_creation.label("date_creation_projet"),
            out_last_sq.c.date_modelisation_derniere,
        )
        .select_from(Projects)
        .join(out_last_sq, Projects.id_projet == out_last_sq.c.id_projet, isouter=True)
        .join(input_last_sq, Projects.id_projet == input_last_sq.c.id_projet, isouter=True)
        .order_by(Projects.id_utilisateur_primaire, Projects.id_projet)
    )

    rows = session.exec(q).all()
    if not rows:
        raise HTTPException(status_code=404, detail="Aucun projet trouvé")

    # --- Regroupement par id_utilisateur_primaire
    groupes = {}
    for user_primary, id_projet, nom_projet, date_creation, date_model in rows:
        groupes.setdefault(user_primary, []).append({
            "id_projet": id_projet,
            "nom_projet": nom_projet,
            "date_modelisation_derniere": _iso(date_model),
            "date_creation_projet": _iso(date_creation),
        })

    # --- Sortie
    resultat = [
        {"id_utilisateur_primaire": k, "projets": v}
        for k, v in groupes.items()
    ]
    return resultat
