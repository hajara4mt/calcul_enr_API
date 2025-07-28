from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from uuid import uuid4
from app.db.database import get_session
from app.models.inputs import input
from app.models.project_model import Projects
from calcul_enr  import ProjetCalcul
import traceback  

router = APIRouter()

@router.post("/calcul")
def create_projet_et_inputs(data: input, session: Session = Depends(get_session)):
    try:
        # 1. Génération automatique de l'ID projet
        id_projets = str(uuid4())

        # 2. Création du projet (table projects)
        projet = Projects(id_projet=id_projets, id_utilisateur=data.id_utilisateur)
        session.add(projet)

       # 3. Création de l'objet inputs avec ID projet injecté
        input_dict = data.model_dump()
        input_dict["id_projet"] = id_projets
        input_record = input(**input_dict)

        print("✅ ID projet injecté dans input_record :", input_record.id_projet)

        # 4. Insertion des inputs (table inputs)
        session.add(input_record)
        session.commit()

        #        # 5. on lance les calculs 

        calcul = ProjetCalcul(id_projet=id_projets)
        resultats = calcul.run()  # 🧠 Lance les calculs et enregistre dans output

        # 6. ✅ Retourner les résultats dans la réponse API
        return {
            "message": "Projet enregistré avec succès",
            "id_projet": id_projets,
            "calculs": resultats
        }

    except Exception as e:
        session.rollback()
        tb = traceback.format_exc()  # 🔍 récupère toute la stacktrace
        raise HTTPException(
            status_code=500,
            detail=f"Erreur serveur : {str(e)}\nTraceback:\n{tb}"
        )