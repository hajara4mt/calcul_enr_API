from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from app.db.database import get_session
from app.models.inputs import input
from app.models.project_model import Projects
from app.models.output import output
from app.models.output_enr_r import output_enr_r
from calcul_enr_api import ProjetCalcul
from datetime import datetime
import random, traceback
from app.models.response_modele_calcul import GetcalculByIdResponse

router = APIRouter()

def generer_id_utilisateur_primaire():
    date_str = datetime.now().strftime("%Y%m%d")
    suffix = random.randint(1000, 9999)
    return f"USER-{date_str}-{suffix}"

def generer_id_projet():
    date_str = datetime.now().strftime("%Y%m%d")
    suffix = random.randint(1000, 9999)
    return f"PROJET-{date_str}-{suffix}"

@router.post("/calcul", response_model=GetcalculByIdResponse)
def create_projet_et_inputs(data: input, session: Session = Depends(get_session)):
    try:
        # 1. Vérifier utilisateur existant
        id_utilisateur_recu = data.id_utilisateur_primaire
        projet_existant = session.exec(
            select(Projects).where(
                (Projects.id_utilisateur_primaire == id_utilisateur_recu) |
                (Projects.id_utilisateur == id_utilisateur_recu)
            )
        ).first()

        if projet_existant:
            id_user_primary = projet_existant.id_utilisateur_primaire
            id_user = projet_existant.id_utilisateur
        else:
            id_user_primary = generer_id_utilisateur_primaire()
            id_user = id_utilisateur_recu

        # 2. Générer ID projet
        id_projets = generer_id_projet()

        # 3. Créer projet et flush direct
        projet = Projects(
            id_projet=id_projets,
            id_utilisateur=id_user,
            id_utilisateur_primaire=id_user_primary,
        )
        session.add(projet)
        session.flush()  # 🔑 le projet existe déjà côté DB

        # 4. Créer input rattaché au projet
        input_dict = data.model_dump()
        input_dict["id_projet"] = id_projets
        input_dict["id_utilisateur"] = id_user_primary
        input_record = input(**input_dict)
        session.add(input_record)
        session.flush()

        # 5. Calculs
        calcul = ProjetCalcul(id_projet=id_projets, donnees_saisie=input_dict)
        resultats = calcul.run()

        # 6. Sauvegarder les outputs
        output_record = output(**resultats["db_output"])
        output_enr_record = output_enr_r(**resultats["db_output_enr"])
        session.add_all([output_record, output_enr_record])

        # 7. Commit global
        session.commit()
        session.refresh(input_record)

        # 8. Réponse API
        return {
            "message": "Projet enregistré avec succès",
            "id_projet": id_projets,
            "id_utilisateur_primaire": id_user_primary,
            "date_creation_projet": input_record.date_creation,
            "date_modelisation_premiere": resultats["db_output"]["data_modelisation_derniere"],
            "calculs": resultats["api_response"],
        }

    except Exception as e:
        session.rollback()
        tb = traceback.format_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Erreur serveur : {str(e)}\nTraceback:\n{tb}",
        )
