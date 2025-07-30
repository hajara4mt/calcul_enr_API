from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime

class output_enr_r(SQLModel, table=True):
    __tablename__ = "output_enr_r"

    Id: Optional[int] = Field(default=None, primary_key=True)
    id_projet: Optional[str] = Field(default=None)

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

    # Thermique
    puissance_retenue_thermique: Optional[float] = None
    ratio_conso_totale_projet_thermique: Optional[float] = None
    enr_local_thermique: Optional[float] = None
    enr_local_max_thermique: Optional[float] = None
    enr_global_thermique: Optional[float] = None
    enr_globale_scenario_max_thermique: Optional[float] = None
    conso_carbone_pv_thermique: Optional[float] = None
    cout_total_pv_thermique: Optional[float] = None
    lettre_faisabilite_thermique: Optional[str] = Field(default=None, max_length=10)
    Faisabilité_calculée_thermique: Optional[str] = None

    # Hybride
    puissance_retenue_hybride: Optional[float] = None
    ratio_conso_totale_projet_hybride: Optional[float] = None
    enr_local_hybride: Optional[float] = None
    enr_local_max_hybride: Optional[float] = None
    enr_global_hybride: Optional[float] = None
    enr_globale_scenario_max_hybride: Optional[float] = None
    conso_carbone_pv_hybride: Optional[float] = None
    cout_total_pv_hybride: Optional[float] = None
    lettre_faisabilite_hybride: Optional[str] = Field(default=None, max_length=10)
    Faisabilité_calculée_hybride: Optional[str] = None
