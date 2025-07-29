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
        # Vérifier que le projet existe
        projet = session.exec(select(Projects).where(Projects.id_projet == id_projet)).first()
        if not projet:
            raise HTTPException(status_code=404, detail="Projet non trouvé")

        # Supprimer les anciennes entrées input/output liées à ce projet
        anciens_inputs = session.exec(select(input).where(input.id_projet == id_projet)).all()
        for i in anciens_inputs:
            session.delete(i)

        # Supprimer les anciennes entrées output liées au projet
        anciens_outputs = session.exec(select(output).where(output.id_projet == id_projet)).all()
        for o in anciens_outputs:
            session.delete(o)

        session.commit()


        # Insérer les nouvelles données dans `input`
        input_dict = data.model_dump()
        input_dict["id_projet"] = id_projet
        nouvelle_entree = input(**input_dict)
        session.add(nouvelle_entree)
        session.commit()

        # Relancer les calculs
        calcul = ProjetCalcul(id_projet=id_projet)
        nouveaux_resultats = calcul.run()

        return {
            "message": "Mise à jour réussie ✅",
            "id_projet": id_projet,
            "nouveaux_calculs": nouveaux_resultats
        }

    except Exception as e:
        session.rollback()
        tb = traceback.format_exc()  # 🔍 récupère toute la stacktrace
        raise HTTPException(
            status_code=500,
            detail=f"Erreur serveur : {str(e)}\nTraceback:\n{tb}"
        )