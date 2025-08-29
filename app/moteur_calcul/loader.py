import pandas as pd
from sqlalchemy import create_engine
from urllib.parse import quote_plus

import pandas as pd
from sqlalchemy import text

from app.db.database import engine


slug_to_label = {
        "inco": "Inconnu",
        "naturelle": "Naturelle",
        "sf": "Simple flux",
        "df": "Double flux"
    }


# 🔁 Réutiliser la même chaîne de connexion que ton API
connection_string ="mssql+pyodbc://CloudSAe6b1e60b:" + quote_plus("KaRa1035*") + "@calcul-enr.database.windows.net:1433/data_calculatrice""?driver=ODBC+Driver+18+for+SQL+Server&Encrypt=yes&TrustServerCertificate=no"

engine = create_engine(connection_string)



def load_donnees_saisie(id_projet: str):
    try:
        query = text("""
            SELECT * FROM input
            WHERE id_projet = :id
        """)
        with engine.connect() as conn:
            result = conn.execute(query, {"id": id_projet})
            row = result.fetchone()

            if not row:
                raise ValueError(f"Aucune donnée trouvée pour id_projet = {id_projet}")

            return dict(row._mapping)

    except Exception as e:
        raise RuntimeError(f"Erreur lors du chargement des données saisies : {e}")

#on recupere de la table departement_temperature 
def load_temperature_data(departement_id: int):
    
    try:
        query = text("""
            SELECT * FROM dbo.departements_temperatures
            WHERE ID = :dep_id
        """)

        with engine.connect() as connection:
            result = connection.execute(query, {"dep_id": departement_id})
            row = result.fetchone()

            if not row:
                raise ValueError(f"Aucune donnée trouvée pour le département ID={departement_id}")

            # Convertir en dictionnaire
            keys = result.keys()
            data = dict(zip(keys, row))
            return data

    except Exception as e:
        raise RuntimeError(f"Erreur lors du chargement des données température : {e}")
    

    ### 
    # moteur/loader.py (à la suite de load_temperature_data)
####"""Récupère la ligne de la table dbo.besoins_ECS40 correspondant à un slug donné (bu, co, re, lo).

slug_to_typologie = {
    "bu": "Bureaux",
    "co": "Commerce",
    "re": "Résidentiel",
    "lo": "Logistique"
}

###nesoins_ecs_40
def load_typologie_data(slug_typologie: str):
    slug_to_typologie = {
    "bu": "Bureaux",
    "co": "Commerce",
    "re": "Résidentiel",
    "lo": "Logistique"
}
    
    if slug_typologie not in slug_to_typologie:
        raise ValueError(f"Slug de typologie inconnu : {slug_typologie}")

    typologie = slug_to_typologie[slug_typologie]

    query = text("""
        SELECT * FROM dbo.besoins_ECS40
        WHERE typologie = :typologie
    """)

    try:
        with engine.connect() as connection:
            result = connection.execute(query, {"typologie": typologie})
            row = result.fetchone()

            if not row:
                raise ValueError(f"Aucune donnée trouvée pour la typologie : {typologie}")

            keys = result.keys()
            return dict(zip(keys, row))

    except Exception as e:
        raise RuntimeError(f"Erreur lors du chargement des données typologie : {e}")


#"""
   ## Charge les coefficients GV depuis la table dbo.Coefficient_GV_reduction
    ##en fonction de l'année de construction.
   ## Retourne un dictionnaire avec les clés : annee_renovation, coef_g, coef_g_1.


def load_coefficients_gv(annee_construction , ventilation_slug):
    ventilation_label = slug_to_label.get(ventilation_slug.lower())
    if not ventilation_label:
        raise ValueError(f"Slug de ventilation inconnu : {ventilation_slug}")
    
    query = text("SELECT * FROM dbo.Coefficient_GV_reduction ORDER BY annee_renovation ASC")

    try:
        with engine.connect() as conn:
            result = conn.execute(query)
            df = pd.DataFrame(result.fetchall(), columns=result.keys())

        # Convertir les années en int (pour éviter les erreurs de comparaison)
        df["annee_renovation"] = pd.to_numeric(df["annee_renovation"], errors="coerce")
        annee_construction = int(annee_construction)

        

        # Recherche de l'année correspondante par intervalle
        annee_match = None
        for i in range(len(df) - 1):
            annee_debut = df.iloc[i]["annee_renovation"]
            annee_suivante = df.iloc[i + 1]["annee_renovation"]
            if annee_debut <= annee_construction < annee_suivante:
                annee_match = annee_debut
                break

        if annee_match is None:
            # Si aucune correspondance, on prend la dernière année
            annee_match = df.iloc[-1]["annee_renovation"]

        # Extraction des coefficients
        ligne = df[df["annee_renovation"] == annee_match].iloc[0]
        coef_g = ligne["G"]
        coef_g_1 = ligne["Coeff_augmentation_GV_lié_déper_ventil_si_SF"]
        coef_g_2 = ligne["Coeff_augmentation_GV_si_déper_ventil_si_naturelle_par_ouverture_fenêtre"]

        # Application du coefficient d’augmentation selon la ventilation
        if ventilation_label.lower() == "simple flux":
            coef_augmentation = coef_g_1
        elif ventilation_label.lower() == "naturelle":
            coef_augmentation = coef_g_2
        else:
            coef_augmentation = 1  # Pas de majoration

        coef_GV_amorti = coef_g * coef_augmentation
       
        return coef_GV_amorti, coef_g

    except Exception as e:
        raise RuntimeError(f"Erreur lors du chargement des coefficients GV : {e}")

{
    "detail": "Erreur serveur : Erreur lors du chargement des coefficients GV : 'Coeff augmentation GV  lié  déper ventil (si SF)'"
}





### la table conso ventillation 


def get_puissance_ventilation( ventilation_slug: str):
    slug_to_label = {
        "inco": "Inconnu",
        "naturelle": "Naturelle",
        "sf": "Simple flux",
        "df": "Double flux"
    }

    # Vérification
    if ventilation_slug not in slug_to_label:
        raise ValueError(f"❌ Slug ventilation inconnu : {ventilation_slug}")

    label_ventilation = slug_to_label[ventilation_slug]

    # Requête SQL
    query = text("SELECT * FROM dbo.conso_ventillation WHERE Ventilation = :vent")
    
    with engine.connect() as conn:
        df = pd.read_sql_query(query, conn, params={"vent": label_ventilation})
    
    if df.empty:
        raise ValueError(f"🚫 Aucun résultat trouvé pour la ventilation : {label_ventilation}")

    puissance = df.iloc[0]["puissance"]

    return puissance

## on utilise la table rendement_type_ecs 

def load_rendement_ecs(energie_ecs_slug: str):

    SLUG_TO_TYPE_ECS = {
    "inco": "Inconnu",
    "elec": "Electrique",
    "fioul": "Fioul",
    "gaz": "Gaz",
    "bois": "Bois",
    "pac": "PAC",
    "geo": "Géothermie",
    "rcu": "rcu"}

    
    # Mapper slug vers nom réel
    type_ecs_label = SLUG_TO_TYPE_ECS.get(energie_ecs_slug)
    if not type_ecs_label:
        raise ValueError(f"Slug ECS inconnu : {energie_ecs_slug}")
   

    # Requête SQL sécurisée (liaison de paramètre)
    query = text("SELECT rendement  FROM dbo.rendements_systems_ecs WHERE Type_ecs = :type ")
    with engine.connect() as conn:
        result = conn.execute(query, {"type": type_ecs_label})
        row = result.fetchone()
        if not row:
            raise ValueError(f"Aucune correspondance trouvée pour Type_ecs = {type_ecs_label}")
        
        return dict(row._mapping)

def load_efficacite_chauffage( systeme_chauffage_slug:str):
    SLUG_TO_TYPE_ECS = {
      "inco": "Inconnu",
      "elec": "Electrique",
      "fioul": "Fioul",
      "gaz": "Gaz",
      "bois": "Bois",
      "pac": "PAC",
      "geo": "Géothermie",
      "rcu": "rcu"}


    type_chauffage = SLUG_TO_TYPE_ECS.get(systeme_chauffage_slug)
    if not type_chauffage:
        raise ValueError(f"Slug chauffage  inconnu : {systeme_chauffage_slug}")
    
    query = text("SELECT efficacite_chauffage  , Rendement_global , Rendement_production FROM dbo.rendements_systems_ecs WHERE Type_ecs = :type ")
    with engine.connect() as conn:
        result = conn.execute(query, {"type": type_chauffage})
        row = result.fetchone()
        if not row:
            raise ValueError(f"Aucune correspondance trouvée pour Type_ecs = {type_chauffage}")
        
        return dict(row._mapping)


###le cout et l'impact carbone
SLUG_TO_ENERGIE = {
        "gn": "Gaz naturel",
        "gbp": "Gaz butane/propane",
        "fioul": "Fioul",
        "charbon": "Charbon",
        "bp" : "Bois plaquettes" , 
        "bg": "Bois granulés", 
        "rcu" : "Réseau de chaleur" ,
        "rfu" : "Réseau de froid" , 
        "aucune" : "Aucune" , 
          "elec" : "electricité"  }

def load_data_co2_cout(slug_energie: str, id_reseau: str = None):
    """
    Retourne les facteurs CO2 et coût pour une énergie.
    Si l'énergie est un réseau (rcu/rfu), on utilise aussi la table reseau_enr avec id_reseau.
    """

    type_energie = SLUG_TO_ENERGIE.get(slug_energie)
    if not type_energie:
        raise ValueError(f"❌ Slug énergie inconnu : {slug_energie}")

    try:
        with engine.connect() as conn:

            # Cas des réseaux de chaleur / froid
            if type_energie in ["Réseau de chaleur", "Réseau de froid"]:
                if not id_reseau:
                    raise ValueError("❌ id_reseau requis pour une énergie de type réseau")

                # 1. Coût unitaire depuis conversion_CO2
                query_cost = text("""
                    SELECT cout_unitaire_euro_par_kwh
                    FROM dbo.conversion_CO2 
                    WHERE type_energie = :type
                """)
                cost_row = conn.execute(query_cost, {"type": type_energie}).fetchone()
                if not cost_row:
                    raise ValueError(f"❌ Coût unitaire introuvable pour l'énergie : {type_energie}")

                # 2. CO2 depuis reseau_enr (filtrage par ID)
                query_co2 = text("""
                    SELECT contenu_co2 AS co2 
                    FROM dbo.taux_enr_reseaux 
                    WHERE id_reseau = :id
                """)
                co2_row = conn.execute(query_co2, {"id": id_reseau}).fetchone()
                if not co2_row:
                    raise ValueError(f"❌ Réseau avec ID '{id_reseau}' non trouvé")

                return {
                    "type_energie": type_energie,
                    "cout_unitaire_euro_par_kwh": cost_row[0],
                    "grammage_co2_kgco2_kwhef": co2_row[0]
                }

            # Cas général
            else:
                query = text("""
                    SELECT * 
                    FROM dbo.conversion_CO2 
                    WHERE type_energie = :type
                """)
                row = conn.execute(query, {"type": type_energie}).fetchone()
                if not row:
                    raise ValueError(f"❌ Aucune donnée trouvée pour l'énergie : {type_energie}")
                return dict(row._mapping)

    except Exception as e:
        raise RuntimeError(f"Erreur chargement CO2/cout : {e}")

