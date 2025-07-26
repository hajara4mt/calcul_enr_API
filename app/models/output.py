from sqlmodel import SQLModel, Field
from typing import Optional, List, Dict
from sqlalchemy import Column
from uuid import UUID
from sqlalchemy import JSON as SQLAlchemyJSON
from typing import Any



class output(SQLModel, table=True):
    __tablename__ = "output_conso_initiales"

    Id: Optional[int] = Field(default=None, primary_key=True)
    id_projet: Optional[int] = Field(default=None)
    conso_annuelles_totales_initiales: Optional[int] = Field(default=None)
    conso_annuelles_totales_initiales_ratio: Optional[int] = Field(default=None)
    cout_total_initial: Optional[int] = Field(default=None)
    conso_carbone_initial: Optional[int] = Field(default=None)

   
    usages_energitiques: Optional[Any] = Field(default=None, sa_column=Column(SQLAlchemyJSON))
    conso_energitiques: Optional[Any] = Field(default=None, sa_column=Column(SQLAlchemyJSON))

    enr_retenue: Optional[str] = Field(default=None)
    puissance_retenue: Optional[float] = Field(default=None)
    ratio_conso_totale_projet: Optional[float] = Field(default=None)
    enr_local: Optional[float] = Field(default=None)
    enr_local_max: Optional[float] = Field(default=None)
    enr_global: Optional[float] = Field(default=None)
    enr_globale_scenario_max: Optional[float] = Field(default=None)
    conso_carbone_pv: Optional[float] = Field(default=None)
    cout_total_pv: Optional[float] = Field(default=None)
    lettre_faisabilite: Optional[str] = Field(default=None)





    #usages_energitiques: Optional[str] = Field(default=None, sa_column_kwargs={"type_": JSON})
    #conso_energitiques: Optional[str] = Field(default=None, sa_column_kwargs={"type_": JSON})