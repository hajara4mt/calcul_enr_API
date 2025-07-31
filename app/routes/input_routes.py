from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from uuid import uuid4
from app.db.database import get_session
from app.models.inputs import input
from app.models.project_model import Projects
from calcul_enr  import ProjetCalcul
import traceback  
from datetime import datetime
import random
from sqlmodel import select


router = APIRouter()

def generer_id_utilisateur_primaire():
    date_str = datetime.now().strftime("%Y%m%d")
    suffix = random.randint(1000, 9999)
    return f"USER-{date_str}-{suffix}"

def generer_id_projet():
    date_str = datetime.now().strftime("%Y%m%d")
    suffix = random.randint(1000, 9999)
    return f"PROJET-{date_str}-{suffix}"

@router.post("/calcul")
def create_projet_et_inputs(data: input, session: Session = Depends(get_session)):
    try:
        # 1. Génération automatique de l'ID projet
        projet_existant = session.exec( select(Projects).where(Projects.id_utilisateur == data.id_utilisateur)
        ).first()

        if projet_existant and projet_existant.id_utilisateur_primaire:
          id_user_primary = projet_existant.id_utilisateur_primaire
        else:
           id_user_primary = generer_id_utilisateur_primaire()

        id_projets = generer_id_projet()



        # 2. Création du projet (table projects)
        projet = Projects(id_projet=id_projets, id_utilisateur=data.id_utilisateur , id_utilisateur_primaire=id_user_primary)
        session.add(projet)

       # 3. Création de l'objet inputs avec ID projet injecté
        input_dict = data.model_dump()
        input_dict["id_projet"] = id_projets
        input_dict["id_utilisateur"] = id_user_primary  


       
        input_record = input(**input_dict)

        print("✅ ID projet injecté dans input_record :", input_record.id_projet)

        # 4. Insertion des inputs (table inputs)
        session.add(input_record)
        session.commit()
        session.refresh(input_record)

        #        # 5. on lance les calculs 

        calcul = ProjetCalcul(id_projet=id_projets)
        resultats = calcul.run()  # 🧠 Lance les calculs et enregistre dans output
        date_modelisation = resultats.pop("date_modelisation", None)

        # 6. ✅ Retourner les résultats dans la réponse API
        return {
            "message": "Projet enregistré avec succès",
            "id_projet": id_projets,
            "id_utilisateur": id_user_primary , 
            "date_creation_projet": input_record.date_creation , 
            "date_modelisation_premiere": date_modelisation,
            "calculs": resultats
        }

    except Exception as e:
        session.rollback()
        tb = traceback.format_exc()  # 🔍 récupère toute la stacktrace
        raise HTTPException(
            status_code=500,
            detail=f"Erreur serveur : {str(e)}\nTraceback:\n{tb}"
        )