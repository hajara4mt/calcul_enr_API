from app.moteur_calcul.loader  import load_donnees_saisie , load_rendement_ecs , get_puissance_ventilation , load_efficacite_chauffage
from datetime import datetime, timezone
from app.models.output_enr_r import output_enr_r
from sqlmodel import select



from app.moteur_calcul.loader  import load_typologie_data , load_temperature_data , load_coefficients_gv
from app.moteur_calcul.hypotheses.conversion import conversion
from app.moteur_calcul.conso_initial import convertir_consommation  , calcul_commun , repartition_usages , calcul_Pv ,faisabilite_recup_chaleur ,  faisabilite , calcul_thermique , calcul_hybride , calcul_geothermie , calcul_faisabilite_geothermie , calcul_biomase , calcul_faisabilite_biomasse , recuperation_chaleur
from app.moteur_calcul.conso_initial import calcul_carbone_et_cout_sql
from app.models.output import output  # à adapter selon ton arborescence
from app.db.database import get_session
import json
from sqlalchemy import text
from app.db.database import engine

Capacité_thermique_volumique_eau = 1.162
temperature_chaude = 60 
Nombres_semaines_chauffage =  26
couverture_PAC_Chauffage = 0,6
couverture_PAC_ECS = 0,6
Taux_EnR_mix_E_national_Elec  = 26/100
Taux_EnR_mix_E_national_Gaz = 1,6 / 100

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

SLUG_TO_TYPE_ECS = {
    "inco": "Inconnu",
    "elec": "Electrique",
    "fioul": "Fioul",
    "gaz": "Gaz",
    "bois": "Bois",
    "pac": "PAC",
    "geo": "Géothermie",
    "rcu": "rcu"}


SLUG_TO_PRODUCTION_ECS = {
        "pc": "production collective",
        "pi": "production individuelle" }

SLUG_USAGE_THERMIQUE = {
    "ch": "chauffage",
    "ch_ecs": "chauffage + ecs",
    "ch_clim": "chauffage + clim",
    "ch_clim_ecs": "chauffage + clim + ecs"
}



SLUG_TO_STRATEGIE = {
    "be": "Aucune (Bâtiment existant)",
    "bn": "Aucune (Bâtiment neuf)",
    "rl": "Rénovation légère (Quick Win)",
    "ra": "Rénovation d'ampleur (grand saut)"
}

SLUG_TO_TOITURE = {
    "te": "Terrasse",
    "it": "Inclinée tuiles",
    "iba": "Inclinée bac acier ou autres",
    "iza": "Inclinée zinc/ardoise (type bâtiment haussmannien ou similaire)"
}

SLUG_TO_SITUATION = {
    "urbain": "Urbain",
    "p_urbain": "Péri-urbain",
    "rural": "Rural"
}
SLUG_ENCOMBREMENT_TOITURE = {
    "tl": "Toiture libre",
    "peu_encombre": "Peu encombrée (gaines, extracteurs…)",
    "tres_encombre": "Très encombrée (équipements techniques, gaines etc…)"
}

SLUG_MASQUE = {
    "batiment_moins_lh": "Bâtiment à moins de L=H",
    "vegetation_dense_haute": "Végétation dense et haute",
    "vegetation_peu_impactante": "Végétation peu impactante",
    "aucun": "Aucun"
}

SLUG_PATRIMOINE = {
    "so": "Sans objet",
    "bc": "Bâtiment classé",
    "abf": "Périmètre ABF / abords des monuments historiques"
}




class ProjetCalcul:
    def __init__(self , id_projet:str):
        self.id_projet = id_projet

        #self.id_projet = self._recuperer_dernier_id_projet()
        self.donnees_saisie = load_donnees_saisie(self.id_projet)
        self.typologie = load_typologie_data(self.donnees_saisie["typologie"])
        self.temperature_data = load_temperature_data(self.donnees_saisie["departement"])
        self.load_rendement_ecs = load_rendement_ecs(self.donnees_saisie["energie_ecs"])
        self.rendement = self.load_rendement_ecs["rendement"]
        self.slug_energi_ecs = self.donnees_saisie["energie_ecs"]
        self.slug_temperature_emetteurs = self.donnees_saisie["regime_temperature_emetteurs"]
        self.Energie_ecs = SLUG_TO_TYPE_ECS.get(self.slug_energi_ecs)
        self.slug_sus_chauffage = self.donnees_saisie["systeme_chauffage"]
        self.systeme_chauffage = SLUG_TO_TYPE_ECS.get(self.slug_sus_chauffage)
        self.load_efficacite_chauffage = load_efficacite_chauffage(self.donnees_saisie["systeme_chauffage"])

        self.efficacite_chauffage = self.load_efficacite_chauffage["efficacite_chauffage"]
        self.rendement_production = self.load_efficacite_chauffage["Rendement_production"]
        self.Rendement_globale = self.load_efficacite_chauffage["Rendement_global"]
        self.ventilation_slug = self.donnees_saisie["ventilation"]
        self.puissance_ventilation = get_puissance_ventilation(self.ventilation_slug)
        self.annee_construction = self.donnees_saisie["annee_construction"]
        self.coef_GV_amorti, self.coef_g = load_coefficients_gv(self.annee_construction, self.ventilation_slug)
        self.slug_usage = self.donnees_saisie["usage_thermique"]
        self.usage_thermique = SLUG_USAGE_THERMIQUE.get(self.slug_usage)
        self.hauteur_plafond = self.donnees_saisie["hauteur_plafond"]
        self.surface = self.donnees_saisie["surface"]
        self.surface_pv = self.donnees_saisie.get("surface_pv") or 0
        #print("🕵️‍♀️ rendement ecs est =", self.rendement)
       # print("📦 Contenu complet de donnees_saisie :", self.donnees_saisie)

        self.prod_solaire_existante = self.donnees_saisie["prod_solaire_existante"]
        self.thermique_saisie = self.donnees_saisie["thermique_saisie"]
        self.surface_thermique = self.donnees_saisie["surface_thermique"]
        self.slug_type_toiture = self.donnees_saisie["type_toiture"]
        self.type_toiture = SLUG_TO_TOITURE.get(self.slug_type_toiture)
        self.slug_situation = self.donnees_saisie["situation"]
        self.situation = SLUG_TO_SITUATION.get(self.slug_situation)
        self.slug_zone = self.donnees_saisie["zone_administrative"]
        self.zone_administrative1 = SLUG_PATRIMOINE.get(self.slug_zone)
        self.slug_msq = self.donnees_saisie["masque"]
        self.masque = SLUG_MASQUE.get(self.slug_msq)
        self.conso_elec = self.donnees_saisie["conso_elec_initial"]
        self.surface_parcelle = self.donnees_saisie["surface_parcelle"]
        self.surface_emprise_sol = self.donnees_saisie["surface_emprise_sol"]


        





        self.encombrement_toiture_slug = self.donnees_saisie["encombrement_toiture"]
        self.encombrement_toiture = SLUG_ENCOMBREMENT_TOITURE.get(self.encombrement_toiture_slug)


        self.surface_toiture = self.donnees_saisie["surface_toiture"]
        self.surface_parking = self.donnees_saisie["surface_parking"]
        self.cons_ann_kwh = self.donnees_saisie["conso_elec_initial"]
        self.slug_strategie = self.donnees_saisie["strategie"]
        self.strategie = SLUG_TO_STRATEGIE.get(self.slug_strategie)
        print(f"on voir c'est quoi la strategie : {self.slug_strategie}")

     #### Vérification et récupération du taux ENR principal
        # Taux ENR principal
        taux_enr_principal_val = self.donnees_saisie.get("taux_enr_principal")
        self.taux_enr_principal = (taux_enr_principal_val or 0) / 100

# Taux ENR appoint
        taux_enr_appoint_val = self.donnees_saisie.get("taux_enr_appoint")
        self.taux_enr_appoint = (taux_enr_appoint_val or 0) / 100
        self.surface_hors_emprise = self.surface_parcelle - self.surface_emprise_sol





        
       

       ## les sorties de besoins_ecs40 : 
        self.typology = self.typologie["typologie"]
        self.besoins_ecs_40 = self.typologie["Besoins_ECS_40"]
        self.jours_ouvrés = self.typologie["jours_ouvrés"]
        self.heures_Fonctionnement = self.typologie["heures_fonctionnement"]
        self.debit = self.typologie["Debit_de_ventilation"]
        self.heures_F = self.typologie["Heures_fonctionnement_occupation"]
        self.modulation = self.typologie["Modulation_débit_en_occupation"]
        self.heures_f_I = self.typologie["Heures_fonctionnement_inoccupation"]
        self.reduction_debit = self.typologie["Réduction_de_débit_en_inoccupation"]
        self.Puissance_surfacique = self.typologie["W_mm"]
        self.C_USE = self.typologie["C_USE"]
        self.N_consigne_semaine = self.typologie["nombre_de_consigne_semaine"]
        self.N_reduit_semaine = self.typologie["nombre_de_reduit_semaine"]
        self.temperature_consigne = self.typologie["Temperature_de_consignes"]
        self.temperature_reduit = self.typologie["Temperature_de_reduit"]
        self.coef_reduction = self.typologie["Coeff_réduction_apports_internes_et_solaires"]
        self.pv_saisie = self.donnees_saisie.get("pv_saisie")

        ## sortie de temperature_froide 
        self.zone_climatique = self.temperature_data["zone_climatique"]
        self.T_exterieur_base = self.temperature_data["Text_de_base"]
        self.dju = self.temperature_data["DJU_moyen_Base_18_2000_2020"]
        self.zone = self.temperature_data["zone_ensoleillement"]
        self.temperature_retenue = self.temperature_data["temperature_moyenne"]
        self.zone_gmi = self.donnees_saisie["zone_gmi"]

        

        


    def _recuperer_dernier_id_projet(self) -> str:
        """Récupère le dernier id_projet inséré dans la table `input`"""
        query = text("SELECT TOP 1 id_projet FROM input ORDER BY date_creation DESC")
        with engine.connect() as conn:
            result = conn.execute(query).fetchone()
            if not result:
                raise ValueError("❌ Aucun projet trouvé dans la table 'input'")
            return result[0]
        
    

    def run(self):
        self.donnees_saisie = load_donnees_saisie(self.id_projet)

        self.slug_principal = self.donnees_saisie["e_t_principal"]
        self.slug_appoint = self.donnees_saisie["e_t_appoint"]
        reseau_principal = self.donnees_saisie.get("reseau_principal")
        reseau_appoint = self.donnees_saisie.get("reseau_appoint")
        self.prod_ecs_slug = self.donnees_saisie.get("type_production_ecs")  
        prod_ch_f_slug = self.donnees_saisie.get("type_production_ch_f")  

        rendement = self.load_rendement_ecs.get("rendement")

        ##les calculs :

        self.Consommation_ventilation  = self.debit * self.puissance_ventilation /1000 * self.heures_F * self.modulation + self.debit * self.puissance_ventilation /1000 * self.heures_f_I * self.reduction_debit
      #  print(f"{self.Consommation_ventilation} : Débit de ventilation Réglementaire : {self.debit} ,puissance_ventilation : {self.puissance_ventilation} , Heures fonctionnement occupation : {self.heures_F} , Modulation débit en occupation  : {self.modulation} , heures fonctio innocupaton : {self.heures_f_I} , reduction_debit: {self.reduction_debit}")
        self.Conso_eclairage = (self.Puissance_surfacique * self.heures_Fonctionnement)/1000
      #  print(f"{self.Conso_eclairage} : on decortique la conso eclairage ; Puissance_surfacique : {self.Puissance_surfacique} , heures_Fonctionnement : {self.heures_Fonctionnement} ")
        self.Volume = self.hauteur_plafond * self.surface
        self.deperdition_max = self.Volume * self.coef_GV_amorti * (self.temperature_consigne - self.T_exterieur_base)/1000
        self.dju_amorti = self.dju + Nombres_semaines_chauffage * 7/168 *((self.temperature_consigne - 18 ) * self.N_consigne_semaine + (self.temperature_reduit - 18 )* self.N_reduit_semaine)
        self.calcul_conso_chauffage = self.coef_GV_amorti * self.Volume  / 1000 * 24 * self.dju_amorti * (1-(self.coef_reduction)) / (self.efficacite_chauffage) / self.surface
        self.Conso_specifique = (self.C_USE - self.Conso_eclairage)



    # 2. Mapper vers libellés
        E_T_principal = SLUG_TO_ENERGIE.get(self.slug_principal)
        E_T_appoint = SLUG_TO_ENERGIE.get(self.slug_appoint)
        self.type_prod_ecs = SLUG_TO_PRODUCTION_ECS.get(self.prod_ecs_slug)
        self.prod_ch_f = SLUG_TO_PRODUCTION_ECS.get(prod_ch_f_slug) 


        if not E_T_principal or not E_T_appoint:
           raise ValueError("Slug énergie inconnu (principal ou appoint)")

    # 3. Extraire les conso
        conso_principal = self.donnees_saisie["conso_principal"]
        conso_appoint = self.donnees_saisie["conso_appoint"]
        conso_elec = self.donnees_saisie["conso_elec_initial"]
        surface = self.donnees_saisie["surface"]

    # 4. Convertir les consommations
        conso_principal_1_convertie = convertir_consommation(E_T_principal, conso_principal)
        conso_principal_2_convertie = convertir_consommation(E_T_appoint, conso_appoint)

        self.Consommations_annuelles_totales_initiales = conso_elec + conso_principal_1_convertie + conso_principal_2_convertie 
        self.Consommations_annuelles_totales_initiales_ratio = self.Consommations_annuelles_totales_initiales / surface
        consos = [conso_principal_1_convertie ,conso_principal_2_convertie , conso_elec ]
       # print(f"les consommations initiales : {consos}")

        self.energis = [self.slug_principal , self.slug_appoint , "elec"]
       # print(f"les slug initiaux : {self.energis}")
        self.total_impact, self.total_cout = calcul_carbone_et_cout_sql(self.energis , consos ,reseau_principal , reseau_appoint )

       
      ##  calcul_commun (self.zone , self.masque , self.surface_pv , self.prod_solaire_existante, self.pv_saisie , self.thermique_saisie , self.surface_thermique)
       # repartition_usages(self.calcul_conso_chauffage , conso_elec , self.rendement_production , self.Consommation_ventilation , self.Conso_specifique, self.Conso_eclairage,self.Consommations_annuelles_totales_initiales, self.usage_thermique,self.zone_climatique , self.surface ,  self.typology ,self.besoins_ecs_40 , self.temperature_retenue , self.type_prod_ecs , self.jours_ouvrés , self.rendement , E_T_principal , E_T_appoint , conso_principal_1_convertie , conso_principal_2_convertie , self.Energie_ecs , self.systeme_chauffage , self.zone , self.masque , self.surface_pv , self.prod_solaire_existante, self.pv_saisie , self.thermique_saisie , self.surface_thermique)
       # print(self.encombrement_toiture_slug)
        
        
        self.calibration_ET1_ECS ,self.calibration_ET1_clim , self.total_chauffage ,  self.total_thermique2 , self.total_thermique1 ,   self.conso_surfacique_clim , self.total_ECS , self.besoin_60 , self.perte_bouclage , self.conso_E_ECS , self.taux_enr_initial , self.Prod_enr_bois , self.conso_elec_PAC , self.usages_energitiques1 , self.conso_energitiques1 , self.energie_PAC_delivre = repartition_usages(self.slug_principal , self.slug_appoint ,self.calcul_conso_chauffage , self.conso_elec , self.rendement_production , self.Rendement_globale , self.Consommation_ventilation , self.Conso_specifique, self.Conso_eclairage,self.Consommations_annuelles_totales_initiales, self.usage_thermique,self.zone_climatique , self.surface ,  self.typology ,self.besoins_ecs_40 , self.temperature_retenue , self.type_prod_ecs , self.jours_ouvrés , self.rendement , E_T_principal , E_T_appoint , conso_principal_1_convertie , conso_principal_2_convertie , self.Energie_ecs , self.systeme_chauffage , self.zone , self.masque , self.surface_pv , self.prod_solaire_existante, self.pv_saisie , self.thermique_saisie , self.surface_thermique)
        #print(f"les ration sont {ratio_elec}")
       # print("type usages =", type(self.usages_energitiques1))
       # print("type conso =", type(self.conso_energitiques1))
    

        usages_energitiques = json.dumps(self.usages_energitiques1)
        conso_energitiques = json.dumps(self.conso_energitiques1)
        #print("✅ CONTROLE AVANT CALCUL_PV :")
        #print("taux_enr_principal =", self.taux_enr_principal)
        #print("taux_enr_appoint =", self.taux_enr_appoint)
        #print("surface_pv =", self.surface_pv)
        #print("surface_thermique =", self.surface_thermique)
        #print("encombrement_toiture =", self.encombrement_toiture)
        #print("typologie =", self.typologie)

        self.Puissance_pv_retenue  ,self.ratio_conso_totale_projet_pv ,  self.enr_local_pv , self.enr_local_max_pv , self.enr_globale , self.enr_globale_scenario_max  ,   self.total_impact_pv, self.total_cout_pv , self.conso_thermique_appoint_proj , self.surface_pv_toiture_max = calcul_Pv (self.Rendement_globale , self.slug_principal , self.slug_appoint , self.type_toiture ,self.conso_elec , self.surface , self.energis,  self.strategie , E_T_principal , E_T_appoint , reseau_principal , reseau_appoint , self.taux_enr_principal , self.taux_enr_appoint , self.encombrement_toiture , conso_principal_1_convertie,conso_principal_2_convertie , self.surface_toiture , self.surface_parking , self.zone , self.masque ,self.systeme_chauffage , self.typologie ,  self.surface_pv , self.prod_solaire_existante, self.pv_saisie , self.thermique_saisie , self.surface_thermique , self.calcul_conso_chauffage , self.rendement_production , self.Consommation_ventilation , self.Conso_specifique, self.Conso_eclairage ,self.Consommations_annuelles_totales_initiales , self.Energie_ecs ,  self.rendement , self.jours_ouvrés ,self.besoins_ecs_40 , self.temperature_retenue , self.type_prod_ecs , self.usage_thermique, self.zone_climatique , self.typology  )  
        self.pv_resultat = [ self.Puissance_pv_retenue  ,self.ratio_conso_totale_projet_pv ,  self.enr_local_pv , self.enr_local_max_pv , self.enr_globale , self.enr_globale_scenario_max  ,   self.total_impact_pv,self.total_cout_pv , self.conso_thermique_appoint_proj , self.surface_pv_toiture_max
]
        lettre , self.details_impacts =faisabilite( self.type_toiture, self.situation, self.zone_administrative1)
        self.details_impacts = str(self.details_impacts)
       # print(f"details impaaaacts , {self.details_impacts}")
        
        self.surface_solaire_thermique_retenue ,  self.ratio_conso_totale_proj_thermique , self.taux_ENR_Local_thermique , self.taux_ENR_Local_thermique_max , self.enr_globale_thermique , self.enr_globale_thermique_scenario_max ,  self.total_impact_thermique ,    self.total_cout_thermique =calcul_thermique (self.Rendement_globale , self.slug_principal , self.slug_appoint , self.type_toiture , self.rendement ,conso_elec , self.strategie , E_T_principal , E_T_appoint , self.surface , self.energis , self.taux_enr_principal , self.taux_enr_appoint , reseau_principal , reseau_appoint ,  conso_principal_1_convertie , conso_principal_2_convertie   , self.zone , self.masque , self.surface_pv , self.prod_solaire_existante, self.pv_saisie , self.thermique_saisie , self.surface_thermique , self.calcul_conso_chauffage, self.rendement_production , self.Consommation_ventilation , self.Conso_specifique, self.Conso_eclairage,self.Consommations_annuelles_totales_initiales, self.Energie_ecs , self.systeme_chauffage , self.encombrement_toiture ,self.usage_thermique, self.zone_climatique , self.surface_parking ,  self.surface_toiture , self.typology ,self.besoins_ecs_40 , self.temperature_retenue , self.typologie ,  self.type_prod_ecs , self.jours_ouvrés  ) 
        self.thermique_resultat = [    self.surface_solaire_thermique_retenue ,  self.ratio_conso_totale_proj_thermique , self.taux_ENR_Local_thermique , self.taux_ENR_Local_thermique_max , self.enr_globale_thermique , self.enr_globale_thermique_scenario_max ,  self.total_impact_thermique ,    self.total_cout_thermique
]
       # print(f"les resultats sont : {thermique_resultat[2]}")
        
        self.surface_solaire_hybride_retenue , self.ratio_conso_totale_proj_hybride, self.taux_ENR_Local_hybride ,self.taux_ENR_Local_hybride_scenario_max, self.enr_globale_hybride , self.enr_globale_hybride_scenario_max   , self.conso_carbone_hybride, self.cout_total_hybride = calcul_hybride(self.Rendement_globale , self.slug_principal , self.slug_appoint ,self.type_toiture , self.rendement  , conso_elec , self.energis , self.strategie , E_T_principal , E_T_appoint ,  self.surface , self.taux_enr_principal , reseau_principal , reseau_appoint , self.taux_enr_appoint ,  conso_principal_1_convertie , conso_principal_2_convertie , self.calcul_conso_chauffage ,self.zone , self.masque , self.surface_pv , self.prod_solaire_existante, self.pv_saisie , self.thermique_saisie , self.surface_thermique ,  self.rendement_production , self.Consommation_ventilation , self.Conso_specifique, self.Conso_eclairage,self.Consommations_annuelles_totales_initiales, self.typology ,self.besoins_ecs_40 , self.encombrement_toiture, self.temperature_retenue , self.type_prod_ecs , self.jours_ouvrés ,  self.usage_thermique, self.zone_climatique , self.surface_toiture , self.surface_parking , self.typologie, self.Energie_ecs , self.systeme_chauffage ) 
        self.hybride_resultat = [   self.surface_solaire_hybride_retenue , self.ratio_conso_totale_proj_hybride, self.taux_ENR_Local_hybride ,self.taux_ENR_Local_hybride_scenario_max, self.enr_globale_hybride , self.enr_globale_hybride_scenario_max   , self.conso_carbone_hybride, self.cout_total_hybride 
]
        self.meilleur , self.details , self.nom_solaire = self.choisir_meilleur_solaire(self.pv_resultat, self.thermique_resultat, self.hybride_resultat , self.type_toiture, self.situation, self.zone_administrative1)
       # print(f"les resultats de meilleur sont : {meilleur}")

      #  print(f"la valeur de la typologie est : {self.typologie}")
       # print(f"la valeur de la typologie est : {self.typology}")
        #print (f"la valeur du volume de deperdition : {self.Volume}")
       # print(f" la valeur de self.coef_GV_amorti : {self.coef_GV_amorti} et le dju amorti est : {self.dju_amorti} et la surface est : {self.surface}")
        #print(f"la valeur de temperature_consigne : {self.temperature_consigne}")
       # print(f"la valeur de T_exterieur_base : {self.T_exterieur_base}")
       # print(f"lefficacite du chauffae est : {self.efficacite_chauffage}")
       # print (f"le coefficient  coef reduction est : {self.coef_reduction}")
        #print(f"le rendement globale est : {self.Rendement_globale}")
        #print(f"le dju est : {self.dju} , le nombre de semaines : {Nombres_semaines_chauffage} et le N_consigne_semaine : {self.N_consigne_semaine} et la temperature reduit est : {self.temperature_reduit} et N_reduit_semaine : {self.N_reduit_semaine} ")

       # self.dju_amorti = self.dju + Nombres_semaines_chauffage * 7/168 *((self.temperature_consigne - 18 ) * self.N_consigne_semaine + (self.temperature_reduit - 18 )* self.N_reduit_semaine)

       # self.calcul_conso_chauffage = self.coef_GV_amorti * self.Volume  / 1000 * 24 * self.dju_amorti * (1-(self.coef_reduction)) / (self.efficacite_chauffage) / self.surface

      #  print("les résultats de la géothermie sont : ")
        print("iciii c'est laaa Biomasse  :")
      #  print(f"la productio nn chaud f est : {prod_ch_f_slug}")
       # print(f"la typologi comme ca est : {self.typology}")



        self.puissance_biomasse_retenue , self.ratio_conso_totale_proj_biomasse , self.enr_local_biomasse ,self.enr_local_biomasse_scenario_max, self.enr_globale_biomasse , self.enr_globale_biomasse_scenario_max, self.total_impact_biomasse , self.total_cout_biomasse = calcul_biomase(self.deperdition_max , self.slug_strategie , self.strategie , self.typology, self.energis , reseau_principal , reseau_appoint  ,self.Rendement_globale , self.slug_principal , self.taux_enr_principal ,self.taux_enr_appoint , self.slug_appoint , self.calcul_conso_chauffage , conso_elec , self.rendement_production , self.Consommation_ventilation , self.Conso_specifique, self.Conso_eclairage, self.Consommations_annuelles_totales_initiales,  self.usage_thermique, self.zone_climatique , surface  ,self.besoins_ecs_40 , self.temperature_retenue , self.type_prod_ecs , self.jours_ouvrés , rendement , E_T_principal , E_T_appoint , conso_principal_1_convertie , conso_principal_2_convertie  , self.Energie_ecs ,  self.systeme_chauffage , self.zone , self.masque , self.surface_pv , self.prod_solaire_existante, self.pv_saisie , self.thermique_saisie , self.surface_thermique )

        print(f"la faisabilite de la biomasse est ::::")
        self.lettre_biomasse , self.details_impacts_biomasse =  calcul_faisabilite_biomasse(self.zone_administrative1 ,self.situation ,   self.slug_temperature_emetteurs , self.slug_strategie  , self.slug_usage , self.prod_ch_f)
        #print(f"la faisabilite de la biomasse est ::::{lettre_biomasse} et le total est : {total_note_biomasse}")

        self.lettre_geothermie , self.details_impacts_geothermie =  calcul_faisabilite_geothermie(self.zone_gmi ,self.situation ,   self.slug_temperature_emetteurs , self.slug_strategie  , self.slug_usage , self.prod_ch_f)

        self.puissance_pac_chaud_retenue , self.ratio_conso_totale_proj_geothermie , self.enr_local_geothermie , self.enr_local_geothermie_scenario_max , self.enr_globale_geothermie , self.enr_globale_geothermie_scenario_max , self.total_impact_geothermie , self.total_cout_geothermie = calcul_geothermie (self.deperdition_max , self.strategie , self.slug_strategie ,self.energis , reseau_principal , reseau_appoint , self.taux_enr_principal ,self.taux_enr_appoint ,  self.slug_temperature_emetteurs , self.usage_thermique ,  self.surface_hors_emprise , self.Rendement_globale ,self.surface_parcelle , E_T_principal  , self.zone , self.masque , self.surface_pv , self.prod_solaire_existante, self.pv_saisie , self.thermique_saisie , self.surface_thermique , self.slug_principal , self.slug_appoint , self.calcul_conso_chauffage , conso_elec , self.rendement_production , self.Consommation_ventilation , self.Conso_specifique, self.Conso_eclairage, self.Consommations_annuelles_totales_initiales , self.zone_climatique , surface ,  self.typology ,self.besoins_ecs_40 , self.temperature_retenue , self.type_prod_ecs , self.jours_ouvrés , self.rendement ,  E_T_appoint , conso_principal_1_convertie , conso_principal_2_convertie , self.Energie_ecs , self.systeme_chauffage )
       # print("les résultats de la recuperation de chaleur  sont : ")
        self.energie_eu_eg  , self.ratio_conso_total_chaleur  , self.enr_local_chaleur , self.enr_local_max_chaleur,  self.enr_global_chaleur , self.enr_global_scenario_max_chaleur,  self.total_impact_chaleur , self.total_cout_chaleur= recuperation_chaleur( self.energis  ,reseau_principal , reseau_appoint , self.taux_enr_principal , self.taux_enr_appoint ,  self.strategie , self.prod_ecs_slug , self.slug_strategie , self.slug_principal , self.slug_appoint , self.calcul_conso_chauffage , conso_elec , self.rendement_production , self.Rendement_globale ,self.Consommation_ventilation , self.Conso_specifique, self.Conso_eclairage,self.Consommations_annuelles_totales_initiales, self.usage_thermique, self.zone_climatique , surface ,  self.typology ,self.besoins_ecs_40 , self.temperature_retenue , self.type_prod_ecs , self.jours_ouvrés , self.rendement , E_T_principal , E_T_appoint , conso_principal_1_convertie , conso_principal_2_convertie , self.Energie_ecs , self.systeme_chauffage , self.zone , self.masque , self.surface_pv , self.prod_solaire_existante, self.pv_saisie , self.thermique_saisie , self.surface_thermique )  
        print("la faisabilite RCU ")
        self.lettre_chaleur , self.details_chaleur = faisabilite_recup_chaleur(self.zone_administrative1 ,self.situation  )
        self.enr_retenue_finale = self.choisir_meilleure_enr_nom()
        print(f"le resultat de choix de meilleur est : {self.enr_retenue_finale}")
       ## conso_json = json.dumps(self.conso_energitiques1)

        output_enr = output_enr_r( 
         id_projet=self.id_projet,
         nom_solaire = self.nom_solaire , 

    # Résultats solaire
         puissance_retenue_solaire= self.meilleur["puissance_retenue"],
         ratio_conso_totale_projet_solaire=self.meilleur["ratio_conso_totale_projet"],
         enr_local_solaire= self.meilleur["enr_local"],
         enr_local_max_solaire=self.meilleur["enr_local_max"],
         enr_global_solaire=self.meilleur["enr_global"],
         enr_globale_scenario_max_solaire=self.meilleur["enr_globale_scenario_max"],
         conso_carbone_pv_solaire=self.meilleur["conso_carbone_pv"],
         cout_total_pv_solaire=self.total_cout_pv,
         lettre_faisabilite_solaire=self.meilleur["lettre_faisabilite"],
         Faisabilité_calculée_solaire=self.details_impacts,

    # géothermie
        puissance_retenue_géothermie=self.puissance_pac_chaud_retenue,
        ratio_conso_totale_projet_géothermie=self.ratio_conso_totale_proj_geothermie,
        enr_local_géothermie=self.enr_local_geothermie,
        enr_local_max_géothermie=self.enr_local_geothermie_scenario_max,
        enr_global_géothermie =self.enr_globale_geothermie,
        enr_globale_scenario_max_géothermie =self.enr_globale_geothermie_scenario_max,
        conso_carbone_géothermie=self.total_impact_geothermie , 
        cout_total_géothermie=self.total_cout_geothermie,
        lettre_faisabilite_géothermie=self.lettre_geothermie , 
        Faisabilité_calculée_géothermie=self.details_impacts_geothermie,

    # Résultats biomasse 
        puissance_retenue_biomasse =self.puissance_biomasse_retenue,
        ratio_conso_totale_projet_biomasse=self.ratio_conso_totale_proj_biomasse,
        enr_local_biomasse=self.enr_local_biomasse,
        enr_local_max_biomasse=self.enr_local_biomasse_scenario_max,
        enr_global_biomasse =self.enr_globale_biomasse,
        enr_globale_scenario_max_biomasse =self.enr_globale_biomasse_scenario_max,
        conso_carbone_biomasse =self.total_impact_biomasse,
        cout_total_biomasse =self.total_cout_biomasse,
        lettre_faisabilite_biomasse =self.lettre_biomasse,
        Faisabilité_calculée_biomasse =self.details_impacts_biomasse , 
    
    # Résultats Récup EU / EG 
        puissance_retenue_chaleur = self.energie_eu_eg , 
        ratio_conso_totale_projet_chaleur = self.ratio_conso_total_chaleur , 
        enr_local_chaleur = self.enr_local_chaleur , 
        enr_local_max_chaleur = self.enr_local_max_chaleur , 
        enr_global_chaleur = self.enr_global_chaleur , 
        enr_global_scenario_max_chaleur= self.enr_global_scenario_max_chaleur , 
        conso_carbone_chaleur= self.total_impact_chaleur , 
        cout_total_chaleur = self.total_cout_chaleur , 
        lettre_faisabilite_chaleur= self.lettre_chaleur , 
        Faisabilité_calculée_chaleur = self.details_chaleur

        
)
        
        

        with get_session() as session:
            existing_output_enr = session.exec(
               select(output_enr_r).where(output_enr_r.id_projet == self.id_projet)).first()

            if existing_output_enr : 
        # 🔁 Mise à jour champ par champ
               for field, value in output_enr.model_dump(exclude={"Id"}).items():
                 setattr(existing_output_enr, field, value)
            else:
               session.add(output_enr)

            session.commit()
            #session.refresh(output_enr)

    
   




        result_obj = output(
        id_projet=self.id_projet,
        conso_annuelles_totales_initiales= round(self.Consommations_annuelles_totales_initiales, 0),
        conso_annuelles_totales_initiales_ratio= round (self.Consommations_annuelles_totales_initiales_ratio, 0) ,
        cout_total_initial= round(self.total_cout, 0),
        
        conso_carbone_initial=round(self.total_impact, 0),
       # usages_energitiques=usages_json,
        usages_energitiques=usages_energitiques,
        
        conso_energitiques= conso_energitiques , 
        enr_retenue=self.enr_retenue_finale,
        puissance_retenue=self.meilleur["puissance_retenue"],
        ratio_conso_totale_projet=self.meilleur["ratio_conso_totale_projet"],
        enr_local=self.meilleur["enr_local"],
        enr_local_max=self.meilleur["enr_local_max"],
        enr_global=self.meilleur["enr_global"],
        enr_globale_scenario_max=self.meilleur["enr_globale_scenario_max"],
        conso_carbone_pv=self.meilleur["conso_carbone_pv"],
        cout_total_pv=self.meilleur["cout_total_pv"],
        lettre_faisabilite=self.meilleur["lettre_faisabilite"],
        taux_ENR_local_initial  = self.taux_enr_initial,
        Faisabilité_calculée = self.details_impacts ,
        data_modelisation_derniere =datetime.now(timezone.utc) )
        #usages_energitiques = usages_energitiques1 ,
        #conso_energitiques = conso_energitiques1)
        #usages_energitiques=json.dumps(usages_energitiques1),
        #conso_energitiques=json.dumps(conso_energitiques1))

        raw_output = result_obj.model_dump(exclude={"Id"})


        # Stocker dans la base output de sql server !
        
        with get_session() as session:
            existing_output = session.exec(
                select(output).where(output.id_projet == self.id_projet)).first()

            if existing_output:
                 print("🔁 Ligne output existante → mise à jour")
        # Mettre à jour tous les champs sauf l’ID
                 for field, value in result_obj.model_dump(exclude={"Id"}).items():
                     setattr(existing_output, field, value)
                 session.commit()
                 session.refresh(existing_output)
                 result_obj_final = existing_output
            else:
                 print("🆕 Aucune ligne output existante → insertion")
                 session.add(result_obj)
                 session.commit()
                 session.refresh(result_obj)
                 result_obj_final = result_obj


















        # Retourner en JSON pour l'api
        #return result_obj.model_dump(exclude={"Id"})
        return {
           
           "date_modelisation" : result_obj.data_modelisation_derniere.isoformat() ,  
            
            "bilan_conso_initial": {
                "conso_annuelles_totales_initiales": int(raw_output["conso_annuelles_totales_initiales"]),
                "conso_annuelles_totales_initiales_ratio": int(raw_output["conso_annuelles_totales_initiales_ratio"]),
                "cout_total_initial": int(raw_output["cout_total_initial"]),
                "enr_local_initial": raw_output["taux_ENR_local_initial"],
               # "usages_energitiques": raw_output["usages_energitiques"],
                "usages_energitiques" : json.loads(raw_output["usages_energitiques"]) ,
                "conso_energitiques": json.loads(raw_output["conso_energitiques"]),
                "conso_carbone_initial": int(raw_output["conso_carbone_initial"])
            },
            "indicateur":{"enr_retenue":self.enr_retenue_finale,
                           "enr_local_initial" : raw_output["taux_ENR_local_initial"]                           
                           },
            "enr_r":{ 
               

        ## à noter que pour le solaire on ressort les donnes du solaires meilleurs , PV ou thermique ou hybride ! 
               self.nom_solaire : {
                  "puissance_retenue" : int(raw_output["puissance_retenue"] ), 
                  "ratio_conso_totale_projet" : int(self.ratio_conso_totale_projet_pv ), 
                "enr_local": round((raw_output["enr_local"]) ,2), 
                "enr_local_max": round((raw_output["enr_local_max"]),2),
                "enr_global": round((raw_output["enr_global"]),2),
                "enr_global_max": round((raw_output["enr_globale_scenario_max"]) , 2),
                "conso_carbone" : int(raw_output["conso_carbone_pv"]), 
                "cout_total": int(self.total_cout_pv),
                "lettre_faisabilite": raw_output["lettre_faisabilite"],
                "faisabilite_calculee":  json.loads(raw_output["Faisabilité_calculée"])
        
            },
     

    "géothermie": {
        "puissance_retenue": int(self.puissance_pac_chaud_retenue),
        "ratio_conso_totale_projet":int( self.ratio_conso_totale_proj_geothermie),
        "enr_local": self.enr_local_geothermie,
        "enr_local_max": self.enr_local_geothermie_scenario_max,
        "enr_global": self.enr_globale_geothermie,
        "enr_global_max": self.enr_globale_geothermie_scenario_max,
        "conso_carbone": int(self.total_impact_geothermie),
        "cout_total": int(self.total_cout_geothermie),
        "lettre_faisabilite": self.lettre_geothermie,
                "faisabilite_calculee":   json.loads(self.details_impacts_geothermie)
        
    },


    "biomasse": {
        "puissance_retenue": int(self.puissance_biomasse_retenue),
        "ratio_conso_totale_projet":int(  self.ratio_conso_totale_proj_biomasse),
        "enr_local": self.enr_local_biomasse,
        "enr_local_max": self.enr_local_biomasse_scenario_max,
        "enr_global": self.enr_globale_biomasse,
        "enr_global_max": self.enr_globale_biomasse_scenario_max,
        "conso_carbone": int(self.total_impact_biomasse),
        "cout_total": int(self.total_cout_biomasse),
        "lettre_faisabilite": self.lettre_biomasse,
                "faisabilite_calculee":  json.loads(self.details_impacts_biomasse)
        
    } , 

    "récupération de chaleur" : {
        "puissance_retenue": int(self.energie_eu_eg),
        "ratio_conso_totale_projet":int(  self.ratio_conso_total_chaleur),
        "enr_local": self.enr_local_chaleur,
        "enr_local_max": self.enr_local_max_chaleur,
        "enr_global": self.enr_global_chaleur,
        "enr_global_max": self.enr_global_scenario_max_chaleur,
        "conso_carbone": int(self.total_impact_chaleur),
        "cout_total": int(self.total_cout_chaleur),
        "lettre_faisabilite": self.lettre_chaleur,
                "faisabilite_calculee":  json.loads(self.details_chaleur)
    }
}
        }   






    def choisir_meilleur_solaire(self, pv_resultat, thermique_resultat, hybride_resultat , type_toiture, situation,zone_administrative1):
     lettre  , details_impacts=      faisabilite( type_toiture, situation, zone_administrative1)

    
     enr_local_pv = pv_resultat[1]               # 2ème élément
     taux_enr_thermique = thermique_resultat[2]  # 3ème élément
     taux_enr_hybride = hybride_resultat[4]      # 5ème élément

     scenarios = [
        ("solaire_pv", pv_resultat[2], pv_resultat),             # enr_local_pv
        ("solaire_thermique", thermique_resultat[2], thermique_resultat),  # taux_ENR_Local_thermique
        ("solaire_hybride", hybride_resultat[2], hybride_resultat)         # taux_ENR_Local_hybride
    ]

     meilleur = max(scenarios, key=lambda x: x[1])  # x[1] = taux ENR
     nom, taux, result = meilleur

    # 3. Mapper dynamiquement le résultat
     if nom == "pv":
        data = {
            "puissance_retenue": result[0],
            "ratio_conso_totale_projet": result[1],
            "enr_local": result[2],
            "enr_local_max": result[3],
            "enr_global": result[4],
            "enr_globale_scenario_max": result[5],
            "conso_carbone_pv": result[6],
            "cout_total_pv": result[7],
            "lettre_faisabilite": lettre,
        }
     elif nom == "thermique":
        data = {
            "puissance_retenue": result[0],
            "ratio_conso_totale_projet": result[1],
            "enr_local": result[2],
            "enr_local_max": result[3],
            "enr_global": result[4],
            "enr_globale_scenario_max": result[5],
            "conso_carbone_pv": result[6],
            "cout_total_pv": result[7],
            "lettre_faisabilite": lettre,
        }
     else:  # Hybride
        data = {
            "puissance_retenue": result[0],
            "ratio_conso_totale_projet": result[1],
            "enr_local": result[2],
            "enr_local_max": result[3],
            "enr_global": result[4],
            "enr_globale_scenario_max": result[5],
            "conso_carbone_pv": result[6],
            "cout_total_pv": result[7],
            "lettre_faisabilite": lettre,
        }

    # 4. Ajouter les infos globales
     data.update({
        "enr_retenue": nom,
        })

     print(f"✅ Meilleur scénario : {nom} avec {round(taux, 2)}% EnR locaux")
     return data , details_impacts , nom



    def choisir_meilleure_enr_nom(self) -> str:
     """
    Retourne uniquement le nom de l'ENR retenue:
    'solaire' (meilleur des PV/thermique/hybride), 'géothermie', 'biomasse' ou 'aucune'.
    Règle: exclut faisabilité 'E', puis max sur le taux d'ENR local.
    """
    # petite normalisation pour comparer 0–1 et 0–100
     def _norm_rate(x):
        if x is None:
            return float("-inf")
        x = float(x)
        return x * 100 if 0 <= x <= 1 else x

     _rank = {"A": 4, "B": 3, "C": 2, "D": 1, "E": 0}

    # suppose que self.meilleur est déjà rempli par choisir_meilleur_solaire(...)
    # self.meilleur['enr_local'] = taux solaire du meilleur scénario
    # self.meilleur['lettre_faisabilite'] = lettre commune solaire
     cand_solaire = {
        "name": "solaire",
        "taux": self.meilleur.get("enr_local") if hasattr(self, "meilleur") and self.meilleur else None,
        "lettre": (self.meilleur.get("lettre_faisabilite") or "").upper() if hasattr(self, "meilleur") and self.meilleur else "E",
    }
     cand_geo = {
        "name": "géothermie",
        "taux": self.enr_local_geothermie,
        "lettre": (self.lettre_geothermie or "").upper(),
    }
     cand_bio = {
        "name": "biomasse",
        "taux": self.enr_local_biomasse,
        "lettre": (self.lettre_biomasse or "").upper(),
    }
     cand_rcu = {
         "name" : "récupération de chaleur" ,
         "taux" : self.enr_local_chaleur , 
         "lettre" : (self.lettre_chaleur or "").upper() , 
      }

    # 1) filtrer: faisabilité ≠ E et taux existant
     candidats = [c for c in (cand_solaire, cand_geo, cand_bio , cand_rcu) if c["taux"] is not None and c["lettre"] != "E"]
     if not candidats:
        return "aucune"

    # 2) choisir: max par taux ENR local, puis meilleure lettre en tie-break
     gagnant = max(candidats, key=lambda c: (_norm_rate(c["taux"]), _rank.get(c["lettre"], -1)))
     return gagnant["name"]
