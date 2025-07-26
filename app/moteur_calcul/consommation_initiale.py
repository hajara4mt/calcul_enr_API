from app.moteur_calcul.loader import load_typologie_data
from app.moteur_calcul.loader import load_rendement_ecs
from app.moteur_calcul.hypotheses.conso_clim import conso_clim
from app.moteur_calcul.loader import load_data_co2_cout
from app.moteur_calcul.loader import load_donnees_saisie
from app.moteur_calcul.loader import load_temperature_data
from app.moteur_calcul.hypotheses.conversion import conversion


##on definit les slugs utilisés :
Capacité_thermique_volumique_eau = 1.162
temperature_chaude = 60 


SLUG_TO_USAGE_THERMIQUE = {
    "ch": "chauffage",
    "ch_ecs": "chauffage + ecs",
    "ch_clim": "chauffage + clim",
    "ch_clim_ecs": "chauffage + clim + ecs"
}

SLUG_TO_PRODUCTION_ECS = {
        "pc": "production collective",
        "pi": "production individuelle" }
slug_to_typologie = {
    "bu": "Bureaux",
    "co": "Commerce",
    "re": "Résidentiel",
    "lo": "Logistique"
}

SLUG_TO_ENERGIE = {
        "gn": "Gaz naturel",
        "gbp": "Gaz butane/propane",
        "fioul": "Fioul",
        "charbon": "Charbon",
        "bp" : "Bois plaquettes" , 
        "bg": "Bois granulés", 
        "rcu" : "Réseau de chaleur" ,
        "rfu" : "Réseau de froid" , 
        "aucune" : "Aucune"   }


## on recupère le données d'entres 
donnees_saisie_test = load_donnees_saisie(id_projet)




departement_id = int(donnees_saisie_test.get("departement", 0))
conso_principal = donnees_saisie_test.get("conso_principal")
conso_appoint = donnees_saisie_test.get("conso_appoint")
conso_elec = donnees_saisie_test.get("conso_elec_initial")
slug_typologie = donnees_saisie_test.get("typologie")  # on garde tel quel (slug)
typologie = slug_to_typologie[slug_typologie]
slug_usage = donnees_saisie_test.get("usage_thermique")
usage_thermique = SLUG_TO_USAGE_THERMIQUE.get(slug_usage)
slug_e_t_p = donnees_saisie_test.get("e_t_principal")
e_t_principal = SLUG_TO_ENERGIE.get(slug_e_t_p)
slug_e_t_a = donnees_saisie_test.get("e_t_appoint")
e_t_appoint = SLUG_TO_ENERGIE.get(slug_e_t_a)
typologie_data = load_typologie_data(slug_typologie)
besoins_ECS = typologie_data["Besoins_ECS_40"]
jours_ouvrés = typologie_data["jours_ouvrés"]
temperature_consigne = typologie_data["Temperature_de_consignes"]
N_consigne_semaine =typologie_data["Temperature_de_consignes"]
N_reduit_semaine = typologie_data["nombre_de_reduit_semaine"]
temperature_reduit = typologie_data["Temperature_de_reduit"]
temp_info = load_temperature_data(departement_id)
dju = temp_info["dju_moyen"]

zone_climatique = temp_info["zone_climatique"]
temperature_retenue = temp_info["temperature_moyenne"]
rendement_data = load_rendement_ecs(energie_ecs_slug)
Rendement = rendement_data["rendement"]
efficacite_chauffage = rendement_data["efficacite_chauffage"]

hauteur_plafond = donnees_saisie_test.get("hauteur_plafond" , 0)
surface = donnees_saisie_test.get("surface" , 0)
coef_GV_amorti, coef_g = load_coefficients_gv()
coef_reduction = typologie_data["Coeff_réduction_apports_internes_et_solaires"]


## conversion des valeurs des consommations recues :
def convertir_consommation(energie: str, conso_annuelle: float) -> float:
    energie_clean = energie.strip().lower().capitalize()
    facteur = conversion.get(energie_clean, 1)
    conso_convertie = conso_annuelle / facteur
    #print(f"🔁 Conversion de {conso_annuelle} kWh pour '{energie_clean}' avec facteur {facteur} => {conso_convertie} kWh")
    return conso_convertie


def temperature_froide(departement_id , usage_thermique ):

    if not departement_id:
        raise ValueError("Champ 'departement' manquant ou invalide.")
    if not usage_thermique:
        raise ValueError(f"Slug usage_thermique inconnu : {slug_usage}")

    # Calcul conso surfacique de clim
    if usage_thermique in ["chauffage + clim + ecs", "chauffage + clim"]:
        conso_surfacique_clim = conso_clim[typologie][zone_climatique]
    elif usage_thermique in ["chauffage + ecs", "chauffage"]:
        conso_surfacique_clim = 0
    else:
        raise ValueError(f"Type d'usage thermique non reconnu : {usage_thermique}")
    
    besoin_60 = (besoins_ECS * (40 - temperature_retenue)) / (60 - temperature_retenue)
    dju = temp_info["dju_moyen"]
    temperature_retenue = temp_info["temperature_moyenne"]

    return besoin_60, temperature_retenue, temp_info["text_base"], dju, conso_surfacique_clim, temp_info["zone_ensoleillement"]


prod_ecs_slug = donnees_saisie_test.get("type_production_ecs")
if not prod_ecs_slug:
        raise ValueError("Champ 'type_production_ecs' manquant.")
    # Traduction slug → libellé
type_prod_ecs = SLUG_TO_PRODUCTION_ECS.get(prod_ecs_slug)
 # Récupération du slug
prod_ecs_slug = donnees_saisie_test.get("type_production_ecs")
if not prod_ecs_slug:
        raise ValueError("Champ 'type_production_ecs' manquant.")
    # Traduction slug → libellé
type_prod_ecs = SLUG_TO_PRODUCTION_ECS.get(prod_ecs_slug)

def perte_bouclage(type_prod_ecs):
    if not type_prod_ecs:
        raise ValueError(f"Slug de type_production_ecs inconnu : {prod_ecs_slug}")

    # Attribution des pertes selon le type
    if type_prod_ecs == "production individuelle":
        perte_bouclage = 0.2
    elif type_prod_ecs == "production collective":
        perte_bouclage = 0.6
    else:
        raise ValueError(f"Type de production ECS inconnu : {type_prod_ecs}")

    return perte_bouclage

##la consommation ECS 

def conso_ECS_ventillation(usage_thermique ,jours_ouvrés , Rendement ): 
    Capacité_thermique_volumique_eau = 1.162
    temperature_chaude = 60 
    perte_bouclage_val = perte_bouclage()
    besoin_60, temperature_retenue , temp_info["text_base"], temp_info["dju_moyen"], conso_surfacique_clim, temp_info["zone_ensoleillement"] = temperature_froide()
    if usage_thermique in ["chauffage + clim + ecs", "chauffage + ecs"]:
        conso_E_ECS = (Capacité_thermique_volumique_eau / 1000) * besoin_60 * (temperature_chaude - temperature_retenue)* jours_ouvrés* ((100 + (perte_bouclage_val*100))/100) / Rendement
    elif usage_thermique in ["chauffage + clim", "chauffage"]:
        conso_E_ECS = 0 
    else :
        raise ValueError(f"Type d'usage thermique inconnu : {usage_thermique}")
    
    return conso_E_ECS

def conso_chauffage():
        Nombres_semaines_chauffage =  26
        Volume = surface * hauteur_plafond 
        dju_amorti = dju + Nombres_semaines_chauffage * 7/168 *((temperature_consigne - 18 ) * N_consigne_semaine + (temperature_reduit - 18 )* N_reduit_semaine)
        calcul_conso_chauffage = Volume * coef_GV_amorti / 1000 * 24 * dju_amorti * (1-(coef_reduction)) / (efficacite_chauffage) / surface
        return conso_chauffage


def consommation_initiale():
    conso_principal_1_convertie = convertir_consommation(e_t_principal , conso_principal)
    conso_principal_2_convertie = convertir_consommation(e_t_appoint , conso_appoint )
    Consommations_annuelles_totales_initiales = conso_elec + conso_principal_1_convertie + conso_principal_2_convertie 
    Consommations_annuelles_totales_initiales_ratio = Consommations_annuelles_totales_initiales / surface




def calcul_carbone_et_cout_sql(slugs_energie: list, consos: list, id_projet: str, donnees_input , surface):
   
    
    
    total_impact = 0
    total_cout = 0

    for i in range(len(slugs_energie)):
        slug = slugs_energie[i]
        conso_i = consos[i]

        id_reseau = None
        if slug in ["rcu", "rfu"]:
            id_reseau = (
                donnees_input.get("reseau_principal") if i == 0
                else donnees_input.get("reseau_appoint")
            )

        data = load_data_co2_cout(slug, id_reseau)

        facteur_co2 = data["grammage_co2_kgco2_kwhef"]
        facteur_cout = data["cout_unitaire_euro_par_kwh"]

        impact = conso_i * facteur_co2
        cout = conso_i * facteur_cout

        total_impact += impact
        total_cout += cout

    ratio_impact = round(total_impact / surface, 2)
    ratio_cout = round(total_cout / surface, 2)

    return total_impact, total_cout, ratio_impact, ratio_cout




def calcul_energie_thermique(
    E_T_principal: str,
    Energie_ECS: str,
    systeme_chauffage: str,
    conso_principal_1_convertie: float,
    repartition_conso_hors_clim: float
) -> dict:
    """
    Calcule les répartitions de la consommation énergétique pour le chauffage, l'ECS et la climatisation.
    """

    # 🔹 Climatisation
    if E_T_principal == "Réseau de froid":
        calibration_ET1_clim = conso_principal_1_convertie
    elif E_T_principal in ["Aucune", "Fioul", "Charbon", "Bois plaquettes", "Bois granulés",
                           "Réseau de chaleur", "Gaz butane/propane", "Gaz naturel"]:
        calibration_ET1_clim = 0
    else:
        raise ValueError(f"Type d'énergie principal thermique inconnu : {E_T_principal}")

    # 🔹 ECS

    
    if Energie_ECS in ["Electrique", "PAC", "Géothermie", "Inconnu"] or E_T_principal in ["Réseau de froid", "Aucune"]:
        calibration_ET1_ECS = 0
    elif Energie_ECS == systeme_chauffage:
        calibration_ET1_ECS = repartition_conso_hors_clim * conso_principal_1_convertie
    else:
        calibration_ET1_ECS = conso_principal_1_convertie

    # 🔹 Chauffage
    if systeme_chauffage in ["Electrique", "PAC", "Géothermie", "Inconnu"] or E_T_principal in ["Réseau de froid", "Aucune"]:
        calibration_ET1_chauffage = 0
    elif Energie_ECS == systeme_chauffage:
        calibration_ET1_chauffage = conso_principal_1_convertie - calibration_ET1_ECS
    else:
        calibration_ET1_chauffage = conso_principal_1_convertie

    # 🔹 Total
    total_thermique1 = (
        calibration_ET1_chauffage + calibration_ET1_ECS + calibration_ET1_clim
    )

    return {
        "chauffage": calibration_ET1_chauffage,
        "ECS": calibration_ET1_ECS,
        "climatisation": calibration_ET1_clim,
        "total_thermique1": total_thermique1,
    }
