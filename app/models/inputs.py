from sqlmodel import SQLModel, Field
from typing import Optional , Literal
from datetime import datetime 
from zoneinfo import ZoneInfo
from pydantic import model_validator
from pydantic import BaseModel, conint, confloat, constr

from enum import Enum

class EnergieECS(str, Enum):
    geo = "geo"
    pac = "pac"
    fioul = "fioul"
    bois = "bois"
    elec = "elec"
    inco = "inco"
    gaz = "gaz"
    rcu = "rcu"

class Production (str , Enum) :
    pi = "pi" 
    pc = "pc"

class typologi(str, Enum) : 
    bu = "bu"
    lo = "lo"
    co = "co"
    re = "re"

class strategy(str , Enum) : 
    be ="be"
    bn = "bn"
    rl = "rl"
    ra  ="ra"

class zonegmi (str , Enum):
    rouge = "rouge"
    verte = "verte"
    orange = "orange"

class typesurface (str , Enum):
    su = "su"
    sdp ="sdp"
    sdo = "sdo"
    subl = "subl"

class typetoiture ( str , Enum):
    te ="te"
    it = "it"
    iba ="iba"
    iza = "iza"

class Energie(str, Enum):
    gn = "gn"           # Gaz naturel
    gbp = "gbp"         # Gaz butane/propane
    fioul = "fioul"     # Fioul
    charbon = "charbon" # Charbon
    bp = "bp"           # Bois plaquettes
    bg = "bg"           # Bois granulés
    rcu = "rcu"         # Réseau de chaleur
    rfu = "rfu"         # Réseau de froid
    aucune = "aucune"   # Aucune

class temperature (str , Enum) : 
    ht ="ht"
    mt=  "mt"
    bt =  "bt"

class encombrement(str , Enum) : 
    tl = "tl"
    peu_encombre = "peu_encombre"
    tres_encombre = "tres_encombre"

class input(SQLModel, table=True):
    __tablename__ = "input"
      
    id: Optional[int] = Field(default=None ,description="id sur la table Input " ,primary_key=True)
    id_projet: str = Field(description = "Id du projet envoyé dans le JSON ")
    #id_utilisateur_primaire : str = Field(description="le id de l'utilisateur envoyé dans le JSON "")
   # id_projet: str 
   # ✅ Alias ici
    id_utilisateur_primaire: str = Field(
        description="ID utilisateur interne (primaire)",
        alias="id_utilisateur"
    )

    typologie_projet: str = Field(description = "Typologie de projet ")
    nom_projet: str = Field(description="Nom du projet")
    adresse: str = Field(description="Adresse postale du bâtiment")
    code_ville: str = Field(description="Code postal de la ville ")
    departement: str = Field(description="Département dans lequel se situe le projet")
    situation: str = Field(description="Situation géographique du bâtiment " )
    structure: str = Field( description = "Type de structure du bâtiment")
    typologie: typologi = Field( description="Typologie du bâtiment" )
    strategie: strategy = Field(description="Stratégie énergétique du projet")
                         
    annee_construction: float = Field(description="Année de construction du bâtiment")
    zone_administrative: str = Field(description="Zone administrative du projet")
    zone_gmi: zonegmi = Field(description="Zone GMI applicable au projet" ) 
                          #example = "verte - rouge - orange")
    proximite_rcu: bool = Field(description = "Le bâtiment est-il proche d’un réseau de chaleur ?"  )
                                #, example = "true, false")
    zone_rcu_prioritaire: bool = Field(description ="Est-ce une zone prioritaire pour le RCU ?")
     # , example = "true , false")
    rcu_proximite: str = Field( description ="Type de proximité au réseau de chaleur")
    taux_enr_rcu: float = Field(description = "Taux d’énergie renouvelable du RCU (entre 0 et 100%)")
    type_surface: typesurface = Field(description = "Type de surface mesurée  \
                                      'su' = Surface Utile, \
'sdp' = Surface de Plancher, \
'sdo' = Surface d'Oeuvre, \
'subl' = Surface Utile Brute" )
                              # example = "su _ sdp _ sdo _ subl")
    surface: float = Field(description ="surface en m² ")
    hauteur_plafond: float
    surface_parcelle: float = Field(description="Surface totale de la parcelle en (m²)")
    surface_emprise_sol: float = Field(description = "Surface bâtie au sol (emprise) en (m²) ")
    surface_parking: float = Field(description = "Surface de parking disponible en (m²)")
    surface_toiture: float = Field(description="Surface totale de la toiture en (m²)")
    type_toiture: typetoiture = Field( description="Type de toiture ")
    encombrement_toiture: encombrement = Field(description = "Niveau d’encombrement de la toiture")
                                      #example="tl , peu_encombre , tres_encombre")
    masque: str = Field( description="Présence de masques solaires (ombres)" )
    #example = "batiment_moins_lh , vegetation_dense_haute , vegetation_peu_impactante" )
    surface_terrasse_disponible: float = Field(description = "Surface disponible pour installation en toiture en (m²) ")
    type_production_ch_f: Production = Field (description="Type de production de chauffage et de froid")
                                      
    regime_temperature_emetteurs: temperature = Field (description="Régime de température des émetteurs" )
                                               
                                            # example = "ht - mt - bt" )
    type_production_ecs: Production = Field(description =  "Type de production d'eau chaude sanitaire (ECS)" )
                                     # example = "pi _ pc")
    usage_thermique: str = Field(description= "Usage principal de la chaleur" )
                                 #example = "ch - ch_ecs - ch_clim , ch_clim_ecs" )
    perimetre_consommation: str = Field(description="Périmètre des consommations énergétiques")
                                        #example="batiment - pc")
    systeme_chauffage: EnergieECS = Field(description="Système principal de chauffage")
                                   # example = "geo - pac - fioul - bois - elec - inco - gaz - rcu  ")
    energie_ecs: EnergieECS  = Field(description = "Énergie utilisée pour l'ECS" )
    ventilation: str = Field(description="Type de ventilation",)

    # Champs dépendants
    saisie_conso: Optional[bool] = None
    conso_elec_initial: Optional[float] = Field(
    default=None,
    description="Consommation électrique initiale en kWh/an (requis si 'saisie_conso' est True) en kWhEF")
    e_t_principal:Energie = Field(default = None , description= "l'énergie thermique principale")
    reseau_principal: Optional[str] = Field(default = None , description= "le nom du réseau de cette energie thermique SI :l'énergie thermique principale == RCU ou RFU ")
    taux_enr_principal: Optional[float]  = Field(default = None , description= "Taux Enr du réseau principal %")
    conso_principal: Optional[float] = Field(default = None , description = "la consommation annuelle du réseau d'energie therique principale en (kWheu)")
    e_t_appoint: Energie = Field(default = None , description= "l'énergie thermique d'appoint")
    reseau_appoint:  Optional[str] = Field(default = None , description= "le numéro du réseau de cette energie thermique SI :l'énergie thermique d'appoint == RCU ou RFU ")
    taux_enr_appoint: Optional[float] = Field(default = None , description= "Taux Enr du réseau d'appoint %")
    conso_appoint: Optional[float] =Field(default = None , description = "la consommation annuelle du réseau d'energie therique d'appoint en (kWheu)")
    prod_solaire_existante: Optional[bool]  = Field(default = None , description= "la production solaire est existante ?")
    donnees_dispo_pv: Optional[str] = Field(default = None , description = "Type de données disponibles pour la production photovoltaïque. \
    Valeurs possibles : 'pv_saisie' (production annuelle), 'surface_pv' (surface installée).")
    pv_saisie: Optional[float] = Field(default = None , description="Production photovoltaïque saisie en (kWhEF). Requis si 'donnees_dispo_pv' = 'pv_saisie'")
    surface_pv: Optional[float] = Field(default = None , description="Surface de panneaux photovoltaïques installée en (m²). Requis si 'donnees_dispo_pv' = 'surface_pv'.")
    donnees_dispo_thermique: Optional[str] = Field(default = None,description="Type de données disponibles pour la production solaire thermique. \
    Valeurs possibles : 'thermique_saisie' (production annuelle), 'surface_thermique' (surface installée).")
    thermique_saisie: Optional[float] = Field(default = None , description="Production solaire thermique saisie en kWhEF. Requis si 'donnees_dispo_thermique' = 'prod_a'.")
    surface_thermique: Optional[float] = Field(default = None , description="Surface de capteurs solaires thermiques installée en m²")
    date_creation: datetime = Field( default_factory=lambda: datetime.now(ZoneInfo("Europe/Paris")),description="date de création de projet")

    
    @model_validator(mode="after")
    def check_dependencies(self):
    
        # Champs obligatoires si saisie_conso est True
        if self.saisie_conso:
            champs = [
                "conso_elec_initial", "e_t_principal",
                "conso_principal", "e_t_appoint", 
                "conso_appoint", "prod_solaire_existante" 
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
        
        #zone rcu 
        if self.proximite_rcu is False:
            if self.zone_rcu_prioritaire:
                raise ValueError("zone_rcu_prioritaire ne doit pas être renseigné si proximite_rcu = False")
            if self.rcu_proximite:
                raise ValueError("rcu_proximite ne doit pas être renseigné si proximite_rcu = False")
            if self.taux_enr_rcu not in (None, 0):
                raise ValueError("taux_enr_rcu ne doit pas être renseigné si proximite_rcu = False")

    
    

        
        return self


