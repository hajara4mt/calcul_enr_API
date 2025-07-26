from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime
from pydantic import model_validator

class input(SQLModel, table=True):
    __tablename__ = "input"
      
    id: Optional[int] = Field(default=None, primary_key=True)
    id_projet: str 
    id_utilisateur : str
   # id_projet: str 

    typologie_projet: str
    nom_projet: str
    adresse: str
    code_ville: str
    departement: str
    situation: str
    structure: str
    typologie: str
    strategie: str
    annee_construction: float
    zone_administrative: str
    zone_gmi: str
    proximite_rcu: bool
    zone_rcu_prioritaire: bool
    rcu_proximite: str
    taux_enr_rcu: float
    type_surface: str
    surface: float
    hauteur_plafond: float
    surface_parcelle: float
    surface_emprise_sol: float
    surface_parking: float
    surface_toiture: float
    type_toiture: str
    encombrement_toiture: str
    masque: str
    surface_terrasse_disponible: float
    type_production_ch_f: str
    regime_temperature_emetteurs: str
    type_production_ecs: str
    usage_thermique: str
    perimetre_consommation: str
    systeme_chauffage: str
    energie_ecs: str
    ventilation: str

    # Champs dépendants
    saisie_conso: Optional[bool] = None
    conso_elec_initial: Optional[float] = None
    e_t_principal: Optional[str] = None
    reseau_principal: Optional[str] = None
    taux_enr_principal: Optional[float] = None
    conso_principal: Optional[float] = None
    e_t_appoint: Optional[str] = None
    reseau_appoint: Optional[str] = None
    taux_enr_appoint: Optional[float] = None
    conso_appoint: Optional[float] = None
    prod_solaire_existante: Optional[bool] = None
    donnees_dispo_pv: Optional[str] = None
    pv_saisie: Optional[float] = None
    surface_pv: Optional[float] = None
    donnees_dispo_thermique: Optional[str] = None
    thermique_saisie: Optional[float] = None
    surface_thermique: Optional[float] = None
    date_creation: datetime = Field(default_factory=datetime.utcnow)

    @model_validator(mode="after")
    def check_dependencies(self):
        # Champs obligatoires si saisie_conso est True
        if self.saisie_conso:
            champs = [
                "conso_elec_initial", "e_t_principal",
                "conso_principal", "e_t_appoint", 
                "conso_appoint", "prod_solaire_existante", "donnees_dispo_pv", "donnees_dispo_thermique", 
            ]
            for champ in champs:
                if getattr(self, champ) is None:
                    raise ValueError(f"{champ} est requis si saisie_conso = True")
        
# Principal thermique
        if self.e_t_principal in ["rcu", "rfu"]:
            if self.reseau_principal is None:
                raise ValueError("reseau_principal est requis si e_t_principal = 'rcu' ou 'rfu'")
            
            if self.taux_enr_principal is None:
                raise ValueError("taux_enr_principal est requis si e_t_principal = 'rcu' ou 'rfu'")
# Appoint thermique
        if self.e_t_appoint in ["rcu", "rfu"]:
            if self.reseau_appoint is None:
                raise ValueError("reseau_appoint est requis si e_t_appoint = 'rcu' ou 'rfu'")
            if self.taux_enr_appoint is None:
                raise ValueError("taux_enr_appoint est requis si e_t_appoint = 'rcu' ou 'rfu'")
            
        # Données PV
        if self.donnees_dispo_pv == "prod_a" and self.pv_saisie is None:
            raise ValueError("pv_saisie est requis si donness_dispo_pv = 'prod_a'")
        if self.donnees_dispo_pv == "surface" and self.surface_pv is None:
            raise ValueError("surface_pv est requis si donness_dispo_pv = 'Surface'")

        # Données thermiques
        if self.donnees_dispo_thermique == "prod_a" and self.thermique_saisie is None:
            raise ValueError("thermique_saisie est requis si donnees_dispo_thermique = 'prod_a'")
        if self.donnees_dispo_thermique == "surface" and self.surface_thermique is None:
            raise ValueError("surface_thermique est requis si donnees_dispo_thermique = 'Surface'")

        
        return self
