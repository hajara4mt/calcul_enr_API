from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from app.db.database import get_session
from app.models.output import output  

router = APIRouter()

@router.get("/resultats/{id_projet}")
def get_output_by_id(id_projet: str, session: Session = Depends(get_session)):
    statement = select(output).where(output.id_projet == id_projet)
    result = session.exec(statement).first()

    if not result:
        raise HTTPException(status_code=404, detail="Résultat non trouvé pour ce projet")

    return result.model_dump(exclude={"Id"}) 
