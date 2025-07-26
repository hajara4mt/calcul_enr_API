from sqlmodel import SQLModel, Field
from datetime import datetime

class Projects(SQLModel, table=True):
    __tablename__ = "projects"
    id_projet: str = Field(primary_key=True)
    id_utilisateur: str
   