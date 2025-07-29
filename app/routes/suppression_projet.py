from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from app.db.database import get_session
from app.models.project_model import Projects
from app.models.inputs import input
from app.models.output import output

router = APIRouter()

@router.delete("/resultats/suppression/{id_projet}")
def supprimer_projet(id_projet: str, session: Session = Depends(get_session)):
    try:
        # Vérifier que le projet existe
        projet = session.exec(select(Projects).where(Projects.id_projet == id_projet)).first()
        if not projet:
            raise HTTPException(status_code=404, detail="Projet introuvable")

        # Supprimer les entrées liées dans inputs
        session.exec(select(input).where(input.id_projet == id_projet)).all()
        for row in session.exec(select(input).where(input.id_projet == id_projet)):
            session.delete(row)

        # Supprimer les entrées liées dans outputs
        for row in session.exec(select(output).where(output.id_projet == id_projet)):
            session.delete(row)

        # Supprimer le projet
        session.delete(projet)
        session.commit()

        return {"message": f"Projet {id_projet} supprimé avec succès ✅"}

    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Erreur serveur : {str(e)}")
