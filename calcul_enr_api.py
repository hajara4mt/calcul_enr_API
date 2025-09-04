from app.moteur_calcul.loader  import load_donnees_saisie , load_rendement_ecs , get_puissance_ventilation , load_efficacite_chauffage
from datetime import datetime, timezone
from app.models.output_enr_r import output_enr_r
from sqlmodel import select
import pytz 



from app.moteur_calcul.loader  import load_typologie_data , load_temperature_data , load_coefficients_gv
from app.moteur_calcul.hypotheses.conversion import conversion
from app.moteur_calcul.conso_test import convertir_consommation  , calcul_commun ,repartition_usages1 , repartition_usages2 ,  repartition_usages , calcul_Pv ,faisabilite_recup_chaleur ,  faisabilite , calcul_thermique , calcul_hybride , calcul_geothermie , calcul_faisabilite_geothermie , calcul_biomase , calcul_faisabilite_biomasse , recuperation_chaleur
from app.moteur_calcul.conso_test import calcul_carbone_et_cout_sql , calcul_aerothermie , faisabilite_aerothermie
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
    def __init__(self , id_projet:str ,  donnees_saisie: dict = None):
        self.id_projet = id_projet

        #self.id_projet = self._recuperer_dernier_id_projet()
        self.donnees_saisie = donnees_saisie  
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
        self.conso_elec1 = self.donnees_saisie["conso_elec_initial"]
        self.surface_parcelle = self.donnees_saisie["surface_parcelle"]
        self.surface_emprise_sol = self.donnees_saisie["surface_emprise_sol"]


        





        self.encombrement_toiture_slug = self.donnees_saisie["encombrement_toiture"]
        self.encombrement_toiture = SLUG_ENCOMBREMENT_TOITURE.get(self.encombrement_toiture_slug)


        self.surface_toiture = self.donnees_saisie["surface_toiture"]
        self.saisie_conso = self.donnees_saisie["saisie_conso"]
        self.surface_parking = self.donnees_saisie["surface_parking"]
        self.cons_ann_kwh = self.donnees_saisie["conso_elec_initial"]
        self.slug_strategie = self.donnees_saisie["strategie"]
        self.strategie = SLUG_TO_STRATEGIE.get(self.slug_strategie)
      #  print(f"on voir c'est quoi la strategie : {self.slug_strategie}")

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
        self.slug_principal = self.donnees_saisie["e_t_principal"]
        self.slug_appoint = self.donnees_saisie["e_t_appoint"]
        self.prod_ecs_slug = self.donnees_saisie.get("type_production_ecs")  
        self.type_prod_ecs = SLUG_TO_PRODUCTION_ECS.get(self.prod_ecs_slug)
      
        
        

        


    def _recuperer_dernier_id_projet(self) -> str:
        """Récupère le dernier id_projet inséré dans la table `input`"""
        query = text("SELECT TOP 1 id_projet FROM input ORDER BY date_creation DESC")
        with engine.connect() as conn:
            result = conn.execute(query).fetchone()
            if not result:
                raise ValueError("❌ Aucun projet trouvé dans la table 'input'")
            return result[0]
        
    

    def run(self):
        if not self.donnees_saisie:
            # fallback si jamais aucune donnée passée
            self.donnees_saisie = load_donnees_saisie(self.id_projet)        
        prod_ch_f_slug = self.donnees_saisie.get("type_production_ch_f")  
        rendement = self.load_rendement_ecs.get("rendement")
        reseau_principal = self.donnees_saisie.get("reseau_principal")
        reseau_appoint = self.donnees_saisie.get("reseau_appoint")
        self.prod_ch_f = SLUG_TO_PRODUCTION_ECS.get(prod_ch_f_slug) 

        ##les calculs :

        self.Consommation_ventilation  = self.debit * self.puissance_ventilation /1000 * self.heures_F * self.modulation + self.debit * self.puissance_ventilation /1000 * self.heures_f_I * self.reduction_debit
      #  print(f"{self.Consommation_ventilation} : Débit de ventilation Réglementaire : {self.debit} ,puissance_ventilation : {self.puissance_ventilation} , Heures fonctionnement occupation : {self.heures_F} , Modulation débit en occupation  : {self.modulation} , heures fonctio innocupaton : {self.heures_f_I} , reduction_debit: {self.reduction_debit}")
        self.Conso_eclairage = (self.Puissance_surfacique * self.heures_Fonctionnement)/1000
      #  print(f"{self.Conso_eclairage} : on decortique la conso eclairage ; Puissance_surfacique : {self.Puissance_surfacique} , heures_Fonctionnement : {self.heures_Fonctionnement} ")
        self.Volume = self.hauteur_plafond * self.surface
      #  print(f"le volume est : {self.Volume} , coef_GV_amorti : {self.coef_GV_amorti} , {self.temperature_consigne }, {self.T_exterieur_base}")
        self.deperdition_max = self.Volume * self.coef_GV_amorti * (self.temperature_consigne - self.T_exterieur_base)/1000
       # print(f"deperdition est : {self.deperdition_max}")
        self.dju_amorti = self.dju + Nombres_semaines_chauffage * 7/168 *((self.temperature_consigne - 18 ) * self.N_consigne_semaine + (self.temperature_reduit - 18 )* self.N_reduit_semaine)
        self.calcul_conso_chauffage = self.coef_GV_amorti * self.Volume  / 1000 * 24 * self.dju_amorti * (1-(self.coef_reduction)) / (self.efficacite_chauffage) / self.surface
        self.Conso_specifique = (self.C_USE - self.Conso_eclairage)



    # 2. Mapper vers libellés
        E_T_principal = SLUG_TO_ENERGIE.get(self.slug_principal)
        E_T_appoint = SLUG_TO_ENERGIE.get(self.slug_appoint)


        if not E_T_principal or not E_T_appoint:
           raise ValueError("Slug énergie inconnu (principal ou appoint)")

    # 3. Extraire les conso
        self.conso_principal = self.donnees_saisie["conso_principal"] if self.saisie_conso else 0
        self.conso_appoint = self.donnees_saisie["conso_appoint"] if self.saisie_conso else 0 
        self.conso_elec1 = self.donnees_saisie["conso_elec_initial"] if self.saisie_conso else 0 
        surface = self.donnees_saisie["surface"]

    #la liste des energis pour les ratio initiaux 

        self.energis = [self.slug_principal , self.slug_appoint , "elec"]
       # print(f"les slug initiaux : {self.energis}")

       
      ##  calcul_commun (self.zone , self.masque , self.surface_pv , self.prod_solaire_existante, self.pv_saisie , self.thermique_saisie , self.surface_thermique)
##on applique directe la repartition d'usages ! 
        
        self.conso_elec , self.conso_principal_2_convertie, self.conso_principal_1_convertie , self.Consommations_annuelles_totales_initiales , self.Consommations_annuelles_totales_initiales_ratio, self.total_impact, self.total_cout, self.prod_enr_locale_site , self.calibration_ET1_ECS , self.calibration_ET1_clim , self.total_chauffage , self.total_thermique2 ,self.total_thermique1 , self.conso_surfacique_clim , self.total_ECS , self.besoin_60 , self.perte_bouclage , self.conso_E_ECS , self.taux_enr_initial , self.Prod_enr_bois , self.conso_elec_PAC , self.usages_energitiques1 , self.conso_energitiques1 , self.energie_PAC_delivre , self.conso_energitiques_1 = repartition_usages( calcul_conso_initial=self.saisie_conso, energis=self.energis, slug_principal=self.slug_principal, slug_appoint=self.slug_appoint, calcul_conso_chauffage=self.calcul_conso_chauffage, conso_elec=self.conso_elec1, conso_principal=self.conso_principal, conso_appoint=self.conso_appoint, rendement_production=self.rendement_production, Rendement_globale=self.Rendement_globale, Consommation_ventilation=self.Consommation_ventilation, Conso_specifique=self.Conso_specifique, Conso_eclairage=self.Conso_eclairage, usage_thermique=self.usage_thermique, zone_climatique=self.zone_climatique, surface=self.surface, typology=self.typology, besoins_ECS=self.besoins_ecs_40, temperature_retenue=self.temperature_retenue, type_prod_ecs=self.type_prod_ecs, jours_ouvrés=self.jours_ouvrés, rendement=self.rendement, E_T_principal=E_T_principal, E_T_appoint=E_T_appoint, Energie_ECS=self.Energie_ecs, systeme_chauffage=self.systeme_chauffage, zone=self.zone, masque=self.masque, surface_PV=self.surface_pv, prod_solaire_existante=self.prod_solaire_existante, pv_saisie=self.pv_saisie, thermique_saisie=self.thermique_saisie, surface_thermique=self.surface_thermique, reseau_principal=reseau_principal, reseau_appoint=reseau_appoint )
        resultat_repartition= [self.conso_principal_2_convertie, self.conso_principal_1_convertie , self.Consommations_annuelles_totales_initiales , self.Consommations_annuelles_totales_initiales_ratio, self.total_impact, self.total_cout, self.prod_enr_locale_site , self.calibration_ET1_ECS ,self.calibration_ET1_clim , self.total_chauffage ,  self.total_thermique2 , self.total_thermique1 ,   self.conso_surfacique_clim , self.total_ECS , self.besoin_60 , self.perte_bouclage , self.conso_E_ECS , self.taux_enr_initial , self.Prod_enr_bois , self.conso_elec_PAC , self.usages_energitiques1 , self.conso_energitiques1 , self.energie_PAC_delivre ]
        
        #print(f"les ration sont {ratio_elec}")
       # print("type usages =", type(self.usages_energitiques1))
       # print("type conso =", type(self.conso_energitiques1))
    

        usages_energitiques = json.dumps(self.usages_energitiques1)
        conso_energitiques = json.dumps(self.conso_energitiques1)
        conso_energitiques1 = json.dumps(self.conso_energitiques_1)
        #print("✅ CONTROLE AVANT CALCUL_PV :")
        #print("taux_enr_principal =", self.taux_enr_principal)
        #print("taux_enr_appoint =", self.taux_enr_appoint)
        #print("surface_pv =", self.surface_pv)
        #print("surface_thermique =", self.surface_thermique)
        #print("encombrement_toiture =", self.encombrement_toiture)
        #print("typologie =", self.typologie)
       # print(f"chaud et froid : {self.prod_ch_f}")
        #print("on execute le solaire pv")

        self.Puissance_pv_retenue  ,self.ratio_conso_totale_projet_pv ,  self.enr_local_pv , self.enr_local_max_pv , self.enr_globale , self.enr_globale_scenario_max  ,   self.total_impact_pv, self.total_cout_pv , self.conso_thermique_appoint_proj , self.surface_pv_toiture_max , self.Production_EnR_locale_PV_autoconsommée , self.production_globale , self.Prod_enr_locale_totale = calcul_Pv (self.Rendement_globale , self.slug_principal , self.slug_appoint , self.type_toiture ,self.conso_elec1 , self.surface , self.energis,  self.strategie , E_T_principal , E_T_appoint , reseau_principal , reseau_appoint , self.taux_enr_principal , self.taux_enr_appoint , self.encombrement_toiture , self.surface_toiture , self.surface_parking , self.zone , self.masque ,self.systeme_chauffage , self.typologie ,  self.surface_pv , self.prod_solaire_existante, self.pv_saisie , self.thermique_saisie , self.surface_thermique , self.calcul_conso_chauffage , self.rendement_production , self.Consommation_ventilation , self.Conso_specifique, self.Conso_eclairage , self.Energie_ecs ,  self.rendement , self.jours_ouvrés ,self.besoins_ecs_40 , self.temperature_retenue , self.type_prod_ecs , self.usage_thermique, self.zone_climatique , self.typology , self.saisie_conso , self.conso_principal ,self.conso_appoint  )  
          
        self.pv_resultat = [ self.Puissance_pv_retenue  ,self.ratio_conso_totale_projet_pv ,  self.enr_local_pv , self.enr_local_max_pv , self.enr_globale , self.enr_globale_scenario_max  ,   self.total_impact_pv,self.total_cout_pv , self.conso_thermique_appoint_proj , self.surface_pv_toiture_max , self.Production_EnR_locale_PV_autoconsommée]
        self.lettre_pv , self.details_impacts = faisabilite ( self.type_toiture, self.situation, self.zone_administrative1)
        self.details_impacts = str(self.details_impacts)
       # print(f"details impaaaacts , {self.details_impacts}")
        

        self.surface_solaire_thermique_retenue , self.ratio_conso_totale_proj_thermique , self.taux_ENR_Local_thermique , self.taux_ENR_Local_thermique_max , self.enr_globale_thermique , self.enr_globale_thermique_scenario_max ,  self.total_impact_thermique ,    self.total_cout_thermique = calcul_thermique (self.Rendement_globale , self.slug_principal , self.slug_appoint , self.type_toiture , self.rendement ,self.conso_elec1 , self.strategie , E_T_principal , E_T_appoint , self.surface , self.energis , self.taux_enr_principal , self.taux_enr_appoint , reseau_principal , reseau_appoint   , self.zone , self.masque , self.surface_pv , self.prod_solaire_existante, self.pv_saisie , self.thermique_saisie , self.surface_thermique , self.calcul_conso_chauffage, self.rendement_production , self.Consommation_ventilation , self.Conso_specifique, self.Conso_eclairage, self.Energie_ecs , self.systeme_chauffage , self.encombrement_toiture ,self.usage_thermique, self.zone_climatique , self.surface_parking ,  self.surface_toiture , self.typology ,self.besoins_ecs_40 , self.temperature_retenue , self.typologie ,  self.type_prod_ecs , self.jours_ouvrés ,  self.saisie_conso  , self.conso_principal ,self.conso_appoint  ) 
        self.thermique_resultat = [self.surface_solaire_thermique_retenue ,  self.ratio_conso_totale_proj_thermique , self.taux_ENR_Local_thermique , self.taux_ENR_Local_thermique_max , self.enr_globale_thermique , self.enr_globale_thermique_scenario_max ,  self.total_impact_thermique ,    self.total_cout_thermique
]
       # print(f"les resultats sont : {thermique_resultat[2]}")
        self.surface_solaire_hybride_retenue , self.ratio_conso_totale_proj_hybride, self.taux_ENR_Local_hybride ,self.taux_ENR_Local_hybride_scenario_max, self.enr_globale_hybride , self.enr_globale_hybride_scenario_max   , self.conso_carbone_hybride, self.cout_total_hybride = calcul_hybride(self.Rendement_globale , self.slug_principal , self.slug_appoint ,self.type_toiture , self.rendement  , self.conso_elec1 , self.energis , self.strategie , E_T_principal , E_T_appoint ,  self.surface , self.taux_enr_principal , reseau_principal , reseau_appoint , self.taux_enr_appoint ,   self.calcul_conso_chauffage ,self.zone , self.masque , self.surface_pv , self.prod_solaire_existante, self.pv_saisie , self.thermique_saisie , self.surface_thermique ,  self.rendement_production , self.Consommation_ventilation , self.Conso_specifique, self.Conso_eclairage, self.typology ,self.besoins_ecs_40 , self.encombrement_toiture, self.temperature_retenue , self.type_prod_ecs , self.jours_ouvrés ,  self.usage_thermique, self.zone_climatique , self.surface_toiture , self.surface_parking , self.typologie, self.Energie_ecs , self.systeme_chauffage , self.saisie_conso  , self.conso_principal ,self.conso_appoint  ) 
        self.hybride_resultat = [self.surface_solaire_hybride_retenue , self.ratio_conso_totale_proj_hybride, self.taux_ENR_Local_hybride ,self.taux_ENR_Local_hybride_scenario_max, self.enr_globale_hybride , self.enr_globale_hybride_scenario_max   , self.conso_carbone_hybride, self.cout_total_hybride 
]
        self.meilleur , self.details , self.nom_solaire = self.choisir_meilleur_solaire(self.pv_resultat, self.thermique_resultat, self.hybride_resultat , self.type_toiture, self.situation, self.zone_administrative1)
       # print(f"les resultats de meilleur sont : {meilleur}")      #  print(f"la valeur de la typologie est : {self.typologie}")
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
      ##  print("iciii c'est laaa Biomasse  :")


##la biomasse 
        self.puissance_biomasse_retenue , self.ratio_conso_totale_proj_biomasse , self.enr_local_biomasse ,self.enr_local_biomasse_scenario_max, self.enr_globale_biomasse , self.enr_globale_biomasse_scenario_max, self.total_impact_biomasse , self.total_cout_biomasse , self.conso_elec_proj_biomasse , self.Prod_enr_locale_totale_biomasse , self.conso_totale_proj_biomasse ,self.prod_enr_globale_biomasse,  self.besoin_chaud_biomasse , self.surface_locale_biomasse =  calcul_biomase(self.deperdition_max , self.slug_strategie , self.strategie , self.typology, self.energis , reseau_principal , reseau_appoint  ,self.Rendement_globale , self.slug_principal , self.taux_enr_principal ,self.taux_enr_appoint , self.slug_appoint , self.calcul_conso_chauffage , self.conso_elec1 , self.rendement_production , self.Consommation_ventilation , self.Conso_specifique, self.Conso_eclairage,  self.usage_thermique, self.zone_climatique , surface  ,self.besoins_ecs_40 , self.temperature_retenue , self.type_prod_ecs , self.jours_ouvrés , rendement , E_T_principal , E_T_appoint  , self.Energie_ecs ,  self.systeme_chauffage , self.zone , self.masque , self.surface_pv , self.prod_solaire_existante, self.pv_saisie , self.thermique_saisie , self.surface_thermique , self.saisie_conso ,self.conso_principal ,self.conso_appoint  )

       
       # print(f"la faisabilite de la biomasse est ::::")
        self.lettre_biomasse , self.details_impacts_biomasse =  calcul_faisabilite_biomasse(self.zone_administrative1 ,self.situation ,   self.slug_temperature_emetteurs , self.slug_strategie  , self.slug_usage , self.prod_ch_f)
        self.resultat_biomasse = [self.puissance_biomasse_retenue , self.ratio_conso_totale_proj_biomasse , self.enr_local_biomasse ,self.enr_local_biomasse_scenario_max, self.enr_globale_biomasse ,self.enr_globale_biomasse_scenario_max, self.total_impact_biomasse , self.total_cout_biomasse , self.Prod_enr_locale_totale_biomasse,  self.conso_elec_proj_biomasse  , self.conso_totale_proj_biomasse ,  self.prod_enr_globale_biomasse , self.lettre_biomasse , self.besoin_chaud_biomasse  ]
     #   print(f"les resultat de biomasse sont : {self.resultat_biomasse}")
####la geothermie 

        self.puissance_pac_chaud_retenue , self.ratio_conso_totale_proj_geothermie , self.enr_local_geothermie , self.enr_local_geothermie_scenario_max , self.enr_globale_geothermie , self.enr_globale_geothermie_scenario_max , self.total_impact_geothermie , self.total_cout_geothermie , self.conso_elec_proj_geothermie , self.Prod_enr_locale_totale_geothermie , self.conso_totale_proj_geothermie , self.prod_enr_globale_geothermie ,  self.besoins_chauds_geothermie , self.besoins_thermiques_geothermie , self.surface_locale_geothermie  = calcul_geothermie (self.deperdition_max , self.strategie , self.slug_strategie ,self.energis , reseau_principal , reseau_appoint , self.taux_enr_principal ,self.taux_enr_appoint ,  self.slug_temperature_emetteurs , self.usage_thermique ,  self.surface_hors_emprise , self.Rendement_globale ,self.surface_parcelle , E_T_principal  , self.zone , self.masque , self.surface_pv , self.prod_solaire_existante, self.pv_saisie , self.thermique_saisie , self.surface_thermique , self.slug_principal , self.slug_appoint , self.calcul_conso_chauffage , self.conso_elec1
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            , self.rendement_production , self.Consommation_ventilation , self.Conso_specifique, self.Conso_eclairage,   self.zone_climatique , surface ,  self.typology ,self.besoins_ecs_40 , self.temperature_retenue , self.type_prod_ecs , self.jours_ouvrés , self.rendement ,  E_T_appoint  , self.Energie_ecs , self.systeme_chauffage , self.saisie_conso , self.conso_principal , self.conso_appoint  )
        self.lettre_geothermie , self.details_impacts_geothermie =  calcul_faisabilite_geothermie(self.zone_gmi ,self.situation ,   self.slug_temperature_emetteurs , self.slug_strategie  , self.slug_usage , self.prod_ch_f)


        self.resultat_geothermie = [self.puissance_pac_chaud_retenue , self.ratio_conso_totale_proj_geothermie , self.enr_local_geothermie , self.enr_local_geothermie_scenario_max , self.enr_globale_geothermie , self.enr_globale_geothermie_scenario_max , self.total_impact_geothermie , self.total_cout_geothermie , self.Prod_enr_locale_totale_geothermie ,  self.conso_elec_proj_geothermie  , self.conso_totale_proj_geothermie , self.prod_enr_globale_geothermie ,self.lettre_geothermie,  self.besoins_chauds_geothermie , self.besoins_thermiques_geothermie]
      
      
       # print("les résultats de la recuperation de chaleur  sont : ")
        self.energie_eu_eg  , self.ratio_conso_total_chaleur  , self.enr_local_chaleur , self.enr_local_max_chaleur,  self.enr_global_chaleur , self.enr_global_scenario_max_chaleur,  self.total_impact_chaleur , self.total_cout_chaleur , self.Prod_enr_locale_totale_recuperation , self.conso_elec_proj_recuperation_chaleur , self.conso_totale_proj_chaleur , self.prod_enr_globale_chaleur= recuperation_chaleur( self.energis  ,reseau_principal , reseau_appoint , self.taux_enr_principal , self.taux_enr_appoint ,  self.strategie , self.prod_ecs_slug , self.slug_strategie , self.slug_principal , self.slug_appoint , self.calcul_conso_chauffage , self.conso_elec1 , self.rendement_production , self.Rendement_globale ,self.Consommation_ventilation , self.Conso_specifique, self.Conso_eclairage, self.usage_thermique, self.zone_climatique , surface ,  self.typology ,self.besoins_ecs_40 , self.temperature_retenue , self.type_prod_ecs , self.jours_ouvrés , self.rendement , E_T_principal , E_T_appoint , self.Energie_ecs , self.systeme_chauffage , self.zone , self.masque , self.surface_pv , self.prod_solaire_existante, self.pv_saisie , self.thermique_saisie , self.surface_thermique , self.saisie_conso , self.conso_principal , self.conso_appoint)  

       
        self.lettre_chaleur , self.details_chaleur = faisabilite_recup_chaleur(self.zone_administrative1 ,self.situation  )
        self.resultat_eu_eg = [self.energie_eu_eg  , self.ratio_conso_total_chaleur  , self.enr_local_chaleur , self.enr_local_max_chaleur,  self.enr_global_chaleur , self.enr_global_scenario_max_chaleur,  self.total_impact_chaleur , self.total_cout_chaleur , self.Prod_enr_locale_totale_recuperation , self.conso_elec_proj_recuperation_chaleur , self.conso_totale_proj_chaleur , self.prod_enr_globale_chaleur , self.lettre_chaleur]

      #  print(f"les resultatas de l'aérothermie sont : ")
        self.puissance_pac_chaud_retenue_aerothermie , self.ratio_conso_totale_proj_aerothermie , self.enr_local_aerothermie , self.enr_local_aerothermie_scenario_max , self.enr_globale_aerothermie , self.enr_globale_aerothermie_scenario_max , self.total_impact_aerothermie , self.total_cout_aerothermie , self.conso_elec_proj_aerothermie , self.Prod_enr_locale_totale_aerothermie , self.conso_totale_proj_aerothermie , self.prod_enr_globale_aerothermiee , self.besoins_chauds_aerothermie , self.besoins_thermiques , self.surface_local_aerothermie = calcul_aerothermie  (self.deperdition_max , self.strategie , self.slug_strategie ,self.energis , reseau_principal , reseau_appoint , self.taux_enr_principal ,self.taux_enr_appoint ,  self.slug_temperature_emetteurs , self.usage_thermique ,  self.surface_hors_emprise , self.Rendement_globale ,self.surface_parcelle , E_T_principal  , self.zone , self.masque , self.surface_pv , self.prod_solaire_existante, self.pv_saisie , self.thermique_saisie , self.surface_thermique , self.slug_principal , self.slug_appoint , self.calcul_conso_chauffage , self.conso_elec1
              , self.rendement_production , self.Consommation_ventilation , self.Conso_specifique, self.Conso_eclairage,   self.zone_climatique , surface ,  self.typology ,self.besoins_ecs_40 , self.temperature_retenue , self.type_prod_ecs , self.jours_ouvrés , self.rendement ,  E_T_appoint  , self.Energie_ecs , self.systeme_chauffage , self.saisie_conso , self.conso_principal , self.conso_appoint  )
        
        self.lettre_aerothermie , self.detail_aerothermie =  faisabilite_aerothermie (self.zone_administrative1 , self.situation , self.slug_temperature_emetteurs , self.slug_strategie  , self.slug_usage , self.prod_ch_f  )

        
        self.resultat_aerothermie = [self.puissance_pac_chaud_retenue_aerothermie , self.ratio_conso_totale_proj_aerothermie , self.enr_local_aerothermie , self.enr_local_aerothermie_scenario_max , self.enr_globale_aerothermie , self.enr_globale_aerothermie_scenario_max , self.total_impact_aerothermie , self.total_cout_aerothermie , self.conso_elec_proj_aerothermie , self.Prod_enr_locale_totale_aerothermie , self.conso_totale_proj_aerothermie , self.prod_enr_globale_aerothermiee , self.lettre_aerothermie , self.besoins_chauds_aerothermie , self.besoins_thermiques ]                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 


        self.enr_retenue_finale = self.choisir_meilleure_enr_nom()
        self.enraaa = self.choisir_meilleure_enr_exceptSOLAIRE()
       ## print(f"le resultat de choix de meilleur est : {self.enr_retenue_finale} , spart le solare : {self.enraaa}")
       ## print("les resultats de la combinaison est : ")
        (self.enr_combinaison , self.ratio_conso_total_combinaison , self.enr_local_combinaison , self.enr_global_combinaison , self.total_impact_combinaison, self.total_cout_combinaison, self.lettre_combinaison) =self.combinaison_enr()
## 
       ## conso_json = json.dumps(self.conso_energitiques1)

        raw_db_output_enr  ={ 
         "id_projet" : self.id_projet,
         "nom_solaire" : self.nom_solaire , 

    # Résultats solaire
         "puissance_retenue_solaire" : self.meilleur["puissance_retenue"],
         "ratio_conso_totale_projet_solaire":self.meilleur["ratio_conso_totale_projet"],
         "enr_local_solaire" :  self.meilleur["enr_local"],
         "enr_local_max_solaire":self.meilleur["enr_local_max"],
         "enr_global_solaire": self.meilleur["enr_global"],
         "enr_globale_scenario_max_solaire" : self.meilleur["enr_globale_scenario_max"],
         "conso_carbone_pv_solaire": self.meilleur["conso_carbone_pv"],
         "cout_total_pv_solaire" : self.total_cout_pv,
         "lettre_faisabilite_solaire" : self.meilleur["lettre_faisabilite"],
         "Faisabilité_calculée_solaire" : self.details_impacts,

    # géothermie
        "puissance_retenue_géothermie" : self.puissance_pac_chaud_retenue,
        "ratio_conso_totale_projet_géothermie": self.ratio_conso_totale_proj_geothermie,
        "enr_local_géothermie": self.enr_local_geothermie,
        "enr_local_max_géothermie" : self.enr_local_geothermie_scenario_max,
        "enr_global_géothermie": self.enr_globale_geothermie,
        "enr_globale_scenario_max_géothermie": self.enr_globale_geothermie_scenario_max,
        "conso_carbone_géothermie": self.total_impact_geothermie , 
        "cout_total_géothermie" : self.total_cout_geothermie,
        "lettre_faisabilite_géothermie":self.lettre_geothermie , 
        "Faisabilité_calculée_géothermie" : self.details_impacts_geothermie,
        "surface_locale_geothermie": self.surface_locale_geothermie , 

    # Résultats biomasse 
        "puissance_retenue_biomasse" : self.puissance_biomasse_retenue,
        "ratio_conso_totale_projet_biomasse":self.ratio_conso_totale_proj_biomasse,
        "enr_local_biomasse" : self.enr_local_biomasse,
        "enr_local_max_biomasse": self.enr_local_biomasse_scenario_max,
        "enr_global_biomasse": self.enr_globale_biomasse,
        "enr_globale_scenario_max_biomasse" : self.enr_globale_biomasse_scenario_max,
        "conso_carbone_biomasse": self.total_impact_biomasse,
        "cout_total_biomasse": self.total_cout_biomasse,
        "lettre_faisabilite_biomasse" : self.lettre_biomasse,
        "Faisabilité_calculée_biomasse": self.details_impacts_biomasse , 
        "surface_locale_biomasse" :  self.surface_locale_biomasse,
    
    # Résultats Récup EU / EG 
        "puissance_retenue_chaleur":  self.energie_eu_eg , 
        "ratio_conso_totale_projet_chaleur" : self.ratio_conso_total_chaleur , 
        "enr_local_chaleur" :  self.enr_local_chaleur , 
        "enr_local_max_chaleur" :  self.enr_local_max_chaleur , 
        "enr_global_chaleur" :  self.enr_global_chaleur , 
        "enr_global_scenario_max_chaleur" : self.enr_global_scenario_max_chaleur , 
        "conso_carbone_chaleur" :  self.total_impact_chaleur , 
        "cout_total_chaleur" : self.total_cout_chaleur , 
        "lettre_faisabilite_chaleur" :  self.lettre_chaleur , 
        "Faisabilité_calculée_chaleur" :  self.details_chaleur , 
    
    ## Aérothermie 
        "puissance_retenue_aerothermie" : self.puissance_pac_chaud_retenue_aerothermie, 
        "ratio_conso_totale_projet_aerothermie" : self.ratio_conso_totale_proj_aerothermie , 
        "enr_local_aerothermie" : self.enr_local_aerothermie , 
        "enr_local_max_aerothermie" : self.enr_local_aerothermie_scenario_max , 
        "enr_global_aerothermie" : self.enr_globale_aerothermie , 
        "enr_global_scenario_max_aerothermie" : self.enr_globale_aerothermie_scenario_max ,
        "conso_carbone_aerothermie": self.conso_totale_proj_aerothermie, 
        "cout_total_aerothermie" :  self.total_cout_aerothermie , 
        "lettre_faisabilite_aerothermie" :  self.lettre_aerothermie , 
        "Faisabilité_calculée_aerothermie" :  self.detail_aerothermie ,
        "surface_locale_aerothermie":  self.surface_local_aerothermie

        }
        
        





        raw_db_output  = { 
        "id_projet" :self.id_projet,
       "conso_annuelles_totales_initiales" : round(self.Consommations_annuelles_totales_initiales, 0),
        "conso_annuelles_totales_initiales_ratio": round (self.Consommations_annuelles_totales_initiales_ratio, 0) ,
        "cout_total_initial": round(self.total_cout, 0),
        
        "conso_carbone_initial": round(self.total_impact, 0),
       # usages_energitiques=usages_json,
        "usages_energitiques" : usages_energitiques,
        
        "conso_energitiques":  conso_energitiques , 
        "conso_energitiques1" : conso_energitiques1 , 
        "enr_retenue" : self.enr_retenue_finale,
        "puissance_retenue": self.meilleur["puissance_retenue"],
        "ratio_conso_totale_projet" : self.meilleur["ratio_conso_totale_projet"],
        "enr_local" : self.meilleur["enr_local"],
        "enr_local_max" : self.meilleur["enr_local_max"],
       "enr_global"  :self.meilleur["enr_global"],
        "enr_globale_scenario_max" : self.meilleur["enr_globale_scenario_max"],
        "conso_carbone_pv" : self.meilleur["conso_carbone_pv"],
        "cout_total_pv" : self.meilleur["cout_total_pv"],
        "lettre_faisabilite" : self.meilleur["lettre_faisabilite"],
        "taux_ENR_local_initial"  : self.taux_enr_initial,
        "Faisabilité_calculée" : self.details_impacts ,
        "data_modelisation_derniere" : datetime.now(pytz.timezone("Europe/Paris")) ,
        "enr_combinaison" : self.enr_combinaison , 
        "enr_local_combinaison" : self.enr_local_combinaison , 
        "lettre_faisabilite_combinaison" : self.lettre_combinaison , 
        "enr_global_combinaison" : self.enr_global_combinaison , 
        "ratio_conso_total_combinaison" : self.ratio_conso_total_combinaison , 
        "total_impact_combinaison" : self.total_impact_combinaison , 
        "total_cout_combinaison" : self.total_cout_combinaison
        }
    


















        # Retourner en JSON pour l'api
        #return result_obj.model_dump(exclude={"Id"})
        api_response = {
           
           "date_modelisation" : raw_db_output["data_modelisation_derniere"].isoformat() ,  
            
            "bilan_conso_initial": {
                "conso_annuelles_totales_initiales": int(raw_db_output["conso_annuelles_totales_initiales"]),
                "conso_annuelles_totales_initiales_ratio": int(raw_db_output["conso_annuelles_totales_initiales_ratio"]),
                "cout_total_initial": int(raw_db_output["cout_total_initial"]),
                "enr_local_initial": raw_db_output["taux_ENR_local_initial"],
               # "usages_energitiques": raw_output["usages_energitiques"],
                "usages_energitiques" : json.loads(raw_db_output["usages_energitiques"]) ,
                "distributions_energitiques": json.loads(raw_db_output["conso_energitiques"]),
                "conso_carbone_initial": int(raw_db_output["conso_carbone_initial"]),
                "conso_energitiques" : json.loads(raw_db_output["conso_energitiques1"])
            },
            "indicateur":{"enr_retenue":self.enr_retenue_finale,
                          "enr_combinaison" : self.enr_combinaison , 
                           "enr_local_initial" : raw_db_output["taux_ENR_local_initial"]                           
                           },
            "combinaison" : {
               "ratio_conso_totale_projet" : self.ratio_conso_total_combinaison , 
               "enr_local" : self.enr_local_combinaison , 
               "enr_global" : self.enr_global_combinaison , 
               "lettre_faisabilite" : self.lettre_combinaison , 
               "conso_carbone" : self.total_impact_combinaison , 
               "cout_total" : self.total_cout_combinaison

            } , 

            "enr_r":{ 
               

        ## à noter que pour le solaire on ressort les donnes du solaires meilleurs , PV ou thermique ou hybride ! 
               self.nom_solaire : {
                  "puissance_retenue" : int(raw_db_output["puissance_retenue"] ), 
                  "ratio_conso_totale_projet" : int(self.ratio_conso_totale_projet_pv ), 
                "enr_local": round((raw_db_output["enr_local"]) ,2), 
                "enr_local_max": round((raw_db_output["enr_local_max"]),2),
                "enr_global": round((raw_db_output["enr_global"]),2),
                "enr_global_max": round((raw_db_output["enr_globale_scenario_max"]) , 2),
                "conso_carbone" : int(raw_db_output["conso_carbone_pv"]), 
                "cout_total": int(self.total_cout_pv),
                "lettre_faisabilite": raw_db_output["lettre_faisabilite"],
                "faisabilite_calculee":  json.loads(raw_db_output["Faisabilité_calculée"])
        
            },
     

    "geothermie": {
        "puissance_retenue": int(self.puissance_pac_chaud_retenue),
        "ratio_conso_totale_projet":int( self.ratio_conso_totale_proj_geothermie),
        "enr_local": self.enr_local_geothermie,
        "enr_local_max": self.enr_local_geothermie_scenario_max,
        "enr_global": self.enr_globale_geothermie,
        "enr_global_max": self.enr_globale_geothermie_scenario_max,
        "conso_carbone": int(self.total_impact_geothermie),
        "cout_total": int(self.total_cout_geothermie),
        "lettre_faisabilite": self.lettre_geothermie,
                "faisabilite_calculee":   json.loads(self.details_impacts_geothermie) ,
                "surface_locale" : int(self.surface_locale_geothermie)
        
    },


    "biomasse": {
        "puissance_retenue": round(self.puissance_biomasse_retenue),
        "ratio_conso_totale_projet":round(  self.ratio_conso_totale_proj_biomasse),
        "enr_local": self.enr_local_biomasse,
        "enr_local_max": self.enr_local_biomasse_scenario_max,
        "enr_global": self.enr_globale_biomasse,
        "enr_global_max": self.enr_globale_biomasse_scenario_max,
        "conso_carbone": round(self.total_impact_biomasse),
        "cout_total": round(self.total_cout_biomasse),
        "lettre_faisabilite": self.lettre_biomasse,
        "faisabilite_calculee":  json.loads(self.details_impacts_biomasse) ,
        "surface_locale" : int(self.surface_locale_biomasse)
        
    } , 

    "aerothermie": {
        "puissance_retenue": round(self.puissance_pac_chaud_retenue_aerothermie),
        "ratio_conso_totale_projet":round(  self.ratio_conso_totale_proj_aerothermie),
        "enr_local": self.enr_local_aerothermie,
        "enr_local_max": self.enr_local_aerothermie_scenario_max,
        "enr_global": self.enr_globale_aerothermie,
        "enr_global_max": self.enr_globale_aerothermie_scenario_max,
        "conso_carbone": round(self.total_impact_aerothermie),
        "cout_total": round(self.total_cout_aerothermie),
        "lettre_faisabilite": self.lettre_aerothermie ,
        "faisabilite_calculee":  json.loads(self.detail_aerothermie) ,
        "surface_locale" : int(self.surface_local_aerothermie)
        
    } , 



    "recuperation_de_chaleur" : {
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

        return {
        "db_output": raw_db_output,
        "db_output_enr": raw_db_output_enr,
        "api_response": api_response,
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
     if nom == "solaire_pv":
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
     elif nom == "solaire_thermique":
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

    # print(f"✅ Meilleur scénario : {nom} avec {round(taux, 2)}% EnR locaux")
     return data , details_impacts , nom



    def choisir_meilleure_enr_nom(self) -> str:
     ##bareme des taux enr 
     enr_barème = [
        (0, 5, 1), (5, 10, 2), (10, 15, 3), (15, 20, 4),
        (20, 25, 5), (25, 30, 6), (30, 35, 7), (35, 40, 8),
        (40, 45, 9), (45, 50, 10), (50, 55, 11), (55, 60, 12),
        (60, 65, 13), (65, 70, 14), (70, 75, 15), (75, 80, 16),
        (80, 85, 17), (85, 90, 18), (90, 95, 19), (95, 101, 20),  # 101 pour inclure 100
    ]
     def note_enr(taux: float) -> int:
        """Associe un taux ENR (%) à une note selon le barème"""
        if taux is None:
            return 0
        for bas, haut, note in enr_barème:
            if bas <= taux < haut:
                return note
        return 0
     
     note_lettre = {"A": 5, "B": 4, "C": 3, "D": 2, "E": 1}

     def score_final(taux, lettre):
        """Retourne la moyenne entre la note ENR et la note faisabilité"""
        if not lettre or lettre.upper() == "E":
            return -1  # exclure les E
        return (note_enr(taux) + note_lettre.get(lettre.upper(), 0)) / 2


     cand_solaire = {
        "name": "solaire",
        "taux": self.meilleur.get("enr_local") if hasattr(self, "meilleur") and self.meilleur else None,
        "lettre": (self.meilleur.get("lettre_faisabilite") or "").upper() if hasattr(self, "meilleur") and self.meilleur else "E",
    }
     cand_geo = {
        "name": "geothermie",
        "taux": self.enr_local_geothermie,
        "lettre": (self.lettre_geothermie or "").upper(),
    }
     cand_bio = {
        "name": "biomasse",
        "taux": self.enr_local_biomasse,
        "lettre": (self.lettre_biomasse or "").upper(),
    }
     cand_rcu = {
         "name" : "recuperation_de_chaleur" ,
         "taux" : self.enr_local_chaleur , 
         "lettre" : (self.lettre_chaleur or "").upper() , 
      }
     cand_aero = {
         "name" : "aerothermie" ,
         "taux" : self.enr_local_aerothermie , 
         "lettre" : (self.lettre_aerothermie or "").upper() , 
      }
     candidats = [cand_solaire, cand_geo, cand_bio, cand_rcu, cand_aero]

    # Calculer les scores
     for c in candidats:
        c["score"] = score_final(c["taux"], c["lettre"])

    # Filtrer ceux avec un score valide (>0)
     valides = [c for c in candidats if c["score"] > 0]
     if not valides:
        return "aucune"

    # Choisir le meilleur
     gagnant = max(valides, key=lambda c: c["score"])
     return gagnant["name"]
    
###le meilleur des enr a part le solaire pour la combinaison 

    def choisir_meilleure_enr_exceptSOLAIRE(self) -> str:
   
     ##bareme des taux enr 
     enr_barème = [
        (0, 5, 1), (5, 10, 2), (10, 15, 3), (15, 20, 4),
        (20, 25, 5), (25, 30, 6), (30, 35, 7), (35, 40, 8),
        (40, 45, 9), (45, 50, 10), (50, 55, 11), (55, 60, 12),
        (60, 65, 13), (65, 70, 14), (70, 75, 15), (75, 80, 16),
        (80, 85, 17), (85, 90, 18), (90, 95, 19), (95, 101, 20),  # 101 pour inclure 100
    ]
     def note_enr(taux: float) -> int:
        """Associe un taux ENR (%) à une note selon le barème"""
        if taux is None:
            return 0
        for bas, haut, note in enr_barème:
            if bas <= taux < haut:
                return note
        return 0
     
     note_lettre = {"A": 5, "B": 4, "C": 3, "D": 2, "E": 1}

     def score_final(taux, lettre):
        """Retourne la moyenne entre la note ENR et la note faisabilité"""
        if not lettre or lettre.upper() == "E":
            return -1  # exclure les E
        return (note_enr(taux) + note_lettre.get(lettre.upper(), 0)) / 2

     cand_geo = {
        "name": "geothermie",
        "taux": self.enr_local_geothermie,
        "lettre": (self.lettre_geothermie or "").upper(),
    }
     cand_bio = {
        "name": "biomasse",
        "taux": self.enr_local_biomasse,
        "lettre": (self.lettre_biomasse or "").upper(),
    }
     cand_rcu = {
         "name" : "recuperation_de_chaleur" ,
         "taux" : self.enr_local_chaleur , 
         "lettre" : (self.lettre_chaleur or "").upper() , 
      }
     cand_aero = {
         "name" : "aerothermie" ,
         "taux" : self.enr_local_aerothermie , 
         "lettre" : (self.lettre_aerothermie or "").upper() , 
      }

     candidats = [ cand_geo, cand_bio, cand_rcu , cand_aero]

    # Calculer les scores
     for c in candidats:
        c["score"] = score_final(c["taux"], c["lettre"])

    # Filtrer ceux avec un score valide (>0)
     valides = [c for c in candidats if c["score"] > 0]
     if not valides:
        return "aucune"

    # Choisir le meilleur
     gagnant = max(valides, key=lambda c: c["score"])
     return gagnant["name"]
    
    
##### les combinaisons 
    def combinaison_enr(self):
       # print(f"conso_total_proj_combinaison : {conso_total_proj_combinaison }")
        meilleure_hors_solaire = self.choisir_meilleure_enr_exceptSOLAIRE()
        solaire = "solaire"

        enr_combinaison =  [meilleure_hors_solaire , solaire ]

        if meilleure_hors_solaire == "geothermie":
            autre_resultat = self.resultat_geothermie
            type_enr = "geothermie"
        elif meilleure_hors_solaire == "biomasse":
            autre_resultat = self.resultat_biomasse
            type_enr = "biomasse"
        elif meilleure_hors_solaire == "recuperation_de_chaleur":
            autre_resultat = self.resultat_eu_eg
            type_enr = "recuperation_de_chaleur"
        elif meilleure_hors_solaire =="aerothermie" :
            autre_resultat = self.resultat_aerothermie
            type_enr = "aerothermie"
        else:
            return None
        
        solaire = self.pv_resultat

       
    ##les resultats calculés !
        besoins_thermiques_combinaison = self.besoins_thermiques_geothermie
        prod_enr_r_total_combinaison = self.Prod_enr_locale_totale + autre_resultat[8] - self.prod_enr_locale_site
        conso_elec_projete_combinaison =  autre_resultat[9] - self.Production_EnR_locale_PV_autoconsommée
        conso_total_proj_combinaison = autre_resultat[10] - self.Production_EnR_locale_PV_autoconsommée
        ratio_conso_total_combinaison = conso_total_proj_combinaison / self.surface
     #   print(f"conso_total_proj_combinaison : {conso_total_proj_combinaison }  ")


        if type_enr in ["geothermie", "aerothermie"]:
          denominateur = besoins_thermiques_combinaison + conso_elec_projete_combinaison
          energie_PAC_delivre_combinaison = autre_resultat[13]
        else:
          denominateur = conso_total_proj_combinaison
          energie_PAC_delivre_combinaison = 0 
       # print(f"conso_total_proj_combinaison : {energie_PAC_delivre_combinaison}  ")

        enr_local_combinaison = round(((prod_enr_r_total_combinaison / denominateur if denominateur else 0)*100),2)
      #  print(f"on veut voir ya quoi la : {prod_enr_r_total_combinaison} , denominateur : {denominateur} ,autre_resultat[9] : {autre_resultat[9]} , Production_EnR_locale_PV_autoconsommée: {self.Production_EnR_locale_PV_autoconsommée} ")
      #  print(f"on decortique la prod global  conso_total_proj_combinaison : {conso_total_proj_combinaison} et ca besoins_thermiques_combinaison ;{besoins_thermiques_combinaison}  ")

       

        ##Production EnR&R globale_ combinaison 

        prod_global_combinaison = round((autre_resultat[11] +self.Production_EnR_locale_PV_autoconsommée  - (self.Production_EnR_locale_PV_autoconsommée * 0.26)),1)
       
        enr_global_combinaison = round(((prod_global_combinaison / (conso_total_proj_combinaison + self.energie_PAC_delivre + energie_PAC_delivre_combinaison))*100),2)
        
        
        ## emission carbone et cout 
        total_impact_combinaison = round((autre_resultat[6] - (self.Production_EnR_locale_PV_autoconsommée * 0.064 / self.surface)),1)
        total_cout_combinaison = round((autre_resultat[7] - (self.Production_EnR_locale_PV_autoconsommée * 0.25 / self.surface)),1)

        ##La faisabilité : 
        lettre_pv = self.lettre_pv                # ⚠️ doit être défini quelque part
        lettre_autre = autre_resultat[12]         # faisabilité autre ENR

        ordre = {"A": 1, "B": 2, "C": 3, "D": 4}  # plus petit chiffre = meilleure faisabilité

    # On choisit la moins bonne (le max des deux)
        lettre_combinaison = lettre_pv if ordre[lettre_pv] > ordre[lettre_autre] else lettre_autre
       # print(f"la combinaison mise en place est : {enr_combinaison}")


        return    enr_combinaison , int(ratio_conso_total_combinaison) , enr_local_combinaison , enr_global_combinaison , int(total_impact_combinaison), int(total_cout_combinaison), lettre_combinaison.strip()

        
