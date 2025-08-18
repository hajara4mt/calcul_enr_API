from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime

class output_enr_r(SQLModel, table=True):
    __tablename__ = "output_enr_r"

    Id: Optional[int] = Field(default=None, primary_key=True)
    id_projet: Optional[str] = Field(default=None)
    nom_solaire: Optional[str] = Field(default=None) 

    # Solaire
    puissance_retenue_solaire: Optional[float] = None
    ratio_conso_totale_projet_solaire: Optional[float] = None
    enr_local_solaire: Optional[float] = None
    enr_local_max_solaire: Optional[float] = None
    enr_global_solaire: Optional[float] = None
    enr_globale_scenario_max_solaire: Optional[float] = None
    conso_carbone_pv_solaire: Optional[float] = None
    cout_total_pv_solaire: Optional[float] = None
    lettre_faisabilite_solaire: Optional[str] = Field(default=None, max_length=10)
    Faisabilité_calculée_solaire: Optional[str] = None

    # géothermie
    puissance_retenue_géothermie: Optional[float] = None
    ratio_conso_totale_projet_géothermie: Optional[float] = None
    enr_local_géothermie: Optional[float] = None
    enr_local_max_géothermie: Optional[float] = None
    enr_global_géothermie: Optional[float] = None
    enr_globale_scenario_max_géothermie: Optional[float] = None
    conso_carbone_géothermie: Optional[float] = None
    cout_total_géothermie: Optional[float] = None
    lettre_faisabilite_géothermie: Optional[str] = Field(default=None, max_length=10)
    Faisabilité_calculée_géothermie: Optional[str] = None

    # biomasse
    puissance_retenue_biomasse: Optional[float] = None
    ratio_conso_totale_projet_biomasse: Optional[float] = None
    enr_local_biomasse: Optional[float] = None
    enr_local_max_biomasse: Optional[float] = None
    enr_global_biomasse: Optional[float] = None
    enr_globale_scenario_max_biomasse: Optional[float] = None
    conso_carbone_biomasse: Optional[float] = None
    cout_total_biomasse: Optional[float] = None
    lettre_faisabilite_biomasse: Optional[str] = Field(default=None, max_length=10)
    Faisabilité_calculée_biomasse: Optional[str] = None

    ## Récup EU/EG :
    puissance_retenue_chaleur : Optional[float] = None
    ratio_conso_totale_projet_chaleur: Optional[float] = None
    enr_local_chaleur : Optional[float] = None
    enr_local_max_chaleur: Optional[float] = None
    enr_global_chaleur : Optional[float] = None
    enr_global_scenario_max_chaleur : Optional[float] = None
    conso_carbone_chaleur: Optional[float] = None
    cout_total_chaleur : Optional[float] = None
    lettre_faisabilite_chaleur : Optional[str] = Field(default=None, max_length=10)
    Faisabilité_calculée_chaleur : Optional[str] = None