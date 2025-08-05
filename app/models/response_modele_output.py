from pydantic import BaseModel , Field
from typing import Dict, Any
from datetime import datetime


class GetOutputByIdResponse(BaseModel):
    message: str = Field( description="Message de statut renvoyé par l'API, par exemple en cas de réussite : 'Résultat complet récupéré avec succès'.")
    id_projet: str = Field(description = "Identifiant unique du projet concerné par la réponse.")
    date_modelisation_derniere: datetime = Field(description ="Date de la dernière modélisation effectuée sur le projet.")
    date_creation_projet: datetime = Field(description ="Date de la création du projet.")
    projets: Dict[str, Any] = Field(description = "Données d'entrée (inputs) du projet, telles qu'elles ont été envoyées à l'API.")
    resultats: Dict[str, Any] = Field(description = "Résultats calculés pour le projet 'id_projet', incluant les bilans de consommation et les scénarios ENR.")
