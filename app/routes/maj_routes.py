from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from app.db.database import get_session
from app.models.inputs import input
from app.models.project_model import Projects
from app.models.output import output
from calcul_enr import ProjetCalcul
import traceback

router = APIRouter()

@router.put("/resultats/maj/{id_projet}")
def mise_a_jour_projet(id_projet: str, data: input, session: Session = Depends(get_session)):
    try:
        # 1. Vérifier que le projet existe
        projet = session.exec(select(Projects).where(Projects.id_projet == id_projet)).first()
        if not projet:
            raise HTTPException(status_code=404, detail="Projet non trouvé")

        # 2. Récupérer et mettre à jour l'ancien input (sauf date_creation)
        ancien_input = session.exec(select(input).where(input.id_projet == id_projet)).first()
        if not ancien_input:
            raise HTTPException(status_code=404, detail="Input introuvable pour mise à jour")

        nouveaux_inputs = data.model_dump(exclude={"id", "date_creation"})
        for key, value in nouveaux_inputs.items():
            if key != "date_creation":
                setattr(ancien_input, key, value)

        # 3. Supprimer les anciens outputs liés au projet
        anciens_outputs = session.exec(select(output).where(output.id_projet == id_projet)).all()
        for o in anciens_outputs:
            session.delete(o)

        session.commit()

        # 4. Relancer les calculs
        calcul = ProjetCalcul(id_projet=id_projet)
        nouveaux_resultats = calcul.run()

        # 5. Extraire la date et reformater le retour
        date_modelisation = nouveaux_resultats.pop("date_modelisation", None)

        return {
            "message": "Mise à jour réussie du projet",
            "id_projet": id_projet,
            "date_modelisation_derniere": date_modelisation,
            "calculs": nouveaux_resultats
        }

    except Exception as e:
        session.rollback()
        tb = traceback.format_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Erreur serveur : {str(e)}\nTraceback:\n{tb}"
        )
