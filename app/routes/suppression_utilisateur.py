from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from app.db.database import get_session
from app.models.project_model import Projects
from app.models.inputs import input
from app.models.output import output

router = APIRouter()

@router.delete("/utilisateur/suppression/{id_utilisateur}")
def supprimer_utilisateur_et_projets(id_utilisateur: str, session: Session = Depends(get_session)):
    try:
        # Récupérer tous les projets associés à l'utilisateur
        projets = session.exec(select(Projects).where(Projects.id_utilisateur == id_utilisateur)).all()

        if not projets:
            raise HTTPException(status_code=404, detail="Aucun projet trouvé pour cet utilisateur.")

        # Supprimer toutes les données associées à chaque projet
        for projet in projets:
            id_projet = projet.id_projet

            # Supprimer input
            inputs = session.exec(select(input).where(input.id_projet == id_projet)).all()
            for i in inputs:
                session.delete(i)

            # Supprimer output
            outputs = session.exec(select(output).where(output.id_projet == id_projet)).all()
            for o in outputs:
                session.delete(o)

            # Supprimer projet
            session.delete(projet)

        session.commit()

        return {"message": f"Tous les projets et données de l'utilisateur {id_utilisateur} ont été supprimés "}

    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Erreur serveur : {str(e)}")
