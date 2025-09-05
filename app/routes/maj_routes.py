from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from app.db.database import get_session
from app.models.inputs import input
from app.models.project_model import Projects
from app.models.output import output
from app.models.output_enr_r import output_enr_r
from calcul_enr_api import ProjetCalcul
from app.models.response_modele_maj import Getcalculaftermaj
import traceback

router = APIRouter()

@router.put("/resultats/maj/{id_projet}" , response_model=Getcalculaftermaj)
def mise_a_jour_projet(id_projet: str, data: input, session: Session = Depends(get_session)):
    try:
        with session.begin():
            # 1. Vérifier que le projet existe
            projet = session.exec(select(Projects).where(Projects.id_projet == id_projet)).first()
            if not projet:
                raise HTTPException(status_code=404, detail="Projet non trouvé")

            # ✅ Vérifier qu'il y a bien un id_utilisateur_primaire associé
            if not projet.id_utilisateur:
                raise HTTPException(
                    status_code=400,
                    detail=f"Aucun id_utilisateur associé au projet {id_projet}"
                )

            # 2. Récupérer et mettre à jour l'ancien input (sauf date_creation, id_utilisateur_primaire)
            ancien_input = session.exec(select(input).where(input.id_projet == id_projet)).first()
            if not ancien_input:
                raise HTTPException(status_code=404, detail="Input introuvable pour mise à jour")

            nouveaux_inputs = data.model_dump(exclude={"id", "date_creation", "id_utilisateur_primaire"})
            for key, value in nouveaux_inputs.items():
                setattr(ancien_input, key, value)

            # 3. Supprimer les anciens outputs liés au projet
            anciens_outputs = session.exec(select(output).where(output.id_projet == id_projet)).all()
            for o in anciens_outputs:
                session.delete(o)

            anciens_outputs_enr = session.exec(select(output_enr_r).where(output_enr_r.id_projet == id_projet)).all()
            for o in anciens_outputs_enr:
                session.delete(o)

            session.flush()  # ⚠️ on garde en mémoire mais pas encore commit

            # 4. Relancer les calculs avec les données mises à jour (en mémoire)
            calcul = ProjetCalcul(id_projet=id_projet, donnees_saisie=nouveaux_inputs)
            resultats = calcul.run()

            # 5. Insérer les nouveaux résultats dans output et output_enr_r
            new_output = output(**resultats["db_output"])
            new_output_enr = output_enr_r(**resultats["db_output_enr"])
            session.add_all([new_output, new_output_enr])

            # (commit est géré automatiquement par `with session.begin()`)

            # 6. Reformater la réponse
            date_modelisation = resultats["api_response"]["date_modelisation"]

            return {
                "message": "Mise à jour réussie du projet",
                "id_projet": id_projet,
                "date_creation": ancien_input.date_creation,
                "date_modelisation_derniere": date_modelisation,
                "calculs": resultats["api_response"]
            }

    except HTTPException:
        raise  # on relance directement les erreurs prévues
    except Exception as e:
        tb = traceback.format_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Erreur serveur : {str(e)}\nTraceback:\n{tb}"
        )
