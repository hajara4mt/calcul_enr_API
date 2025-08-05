from pydantic import BaseModel, Field
from typing import Dict, Any
from datetime import datetime

class Getcalculaftermaj(BaseModel):
    message: str = Field(description="Message de confirmation")
    id_projet: str = Field(description="l'Identifiant unique propre au projet coté plateforme")
 #   id_utilisateur: str = Field(description="l'Identifiant de l'utilisateur primaire coté plateforme")
    date_creation: datetime = Field(description="Date de création du projet")
    date_modelisation_derniere: datetime = Field(description="Date de la dernière mise à jour effectuée")
    calculs: Dict[str, Any] = Field(description="Résultats complets des calculs après mise à jour ")
