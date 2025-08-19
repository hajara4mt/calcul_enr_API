from pydantic import BaseModel , Field
from typing import Dict, Any
from datetime import datetime


class GetcalculByIdResponse(BaseModel):
    message: str  = Field( description="Message de statut renvoyé par l'API, par exemple en cas de réussite : 'Projet enregistré avec succès'")
    id_projet: str = Field(description = "Identifiant unique associé au projet crée.")
    id_utilisateur_primaire : str = Field(description = "Identifiant unique associé à l'utilisateur qui a crée le projet ")
    date_creation_projet : datetime =  Field(description ="Date de la création du projet")
    #date_modelisation_derniere: datetime = Field(description ="Date de la dernière modélisation effectuée sur le projet.")
    calculs: Dict[str, Any] = Field(description = "Résultats calculés pour le projet créé , incluant les bilans de consommation et les scénarios ENR.")


