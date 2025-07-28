import pandas as pd 
from app.db.database import engine

from app.moteur_calcul.hypotheses.conversion import conversion
from app.moteur_calcul.loader import load_data_co2_cout
from app.moteur_calcul.hypotheses.conso_clim import conso_clim
from  app.moteur_calcul.hypotheses.mapping import mapping 

from app.moteur_calcul.hypotheses.Hypothèse_Prod import ZONES
from app.moteur_calcul.hypotheses.COEF_PERTE_RENDEMENT import COEF_PERTE_RENDEMENT
from app.moteur_calcul.hypotheses.Hypothèse_Surface_PV import HYPOTHESE_SURFACE_PV
from app.moteur_calcul.hypotheses.Bdd_conso_carbone import Baisse_conso_besoins






Capacité_thermique_volumique_eau = 1.162
temperature_chaude = 60 
couverture_PAC_Chauffage = 0,6
couverture_PAC_ECS = 0,6
Taux_EnR_mix_E_national_Elec  = 26/100
Taux_EnR_mix_E_national_Gaz = 1.6 / 100


## conversion des valeurs des consommations recues :
def convertir_consommation(energie: str, conso_annuelle: float) -> float:
    energie_clean = energie.strip().lower().capitalize()
    facteur = conversion.get(energie_clean, 1)
    conso_convertie = conso_annuelle / facteur
    #print(f"🔁 Conversion de {conso_annuelle} kWh pour '{energie_clean}' avec facteur {facteur} => {conso_convertie} kWh")
    return conso_convertie


##le cout et le carbone 
#def calcul_carbone_et_cout_sql(slugs_energie: list, consos: list,  reseau_principal , reseau_appoint):
 #   total_impact = 0
  #  total_cout = 0

   # for i in range(len(slugs_energie)):
     #   slug = slugs_energie[i]
      #  conso_i = float(consos[i])
       # id_reseau = None
       # if slug in ["rcu", "rfu"]:
        #    id_reseau = (
      #          reseau_principal if i == 0
       #         else reseau_appoint 
        #    )

        #data = load_data_co2_cout(slug, id_reseau)

       # facteur_co2 = float(data["grammage_co2_kgco2_kwhef"])
       # facteur_cout = float(data["cout_unitaire_euro_par_kwh"])

      #  impact = conso_i * facteur_co2
      #  cout = conso_i * facteur_cout
     #   total_impact += impact
    #    total_cout += cout

        
    #ratio_impact = round(total_impact / surface, 2)
    #ratio_cout = round(total_cout / surface, 2)

    #return total_impact, total_cout

def calcul_carbone_et_cout_sql(slugs_energie: list, consos: list, reseau_principal, reseau_appoint):
    total_impact = 0
    total_cout = 0

  #  print("\n=== Début calcul carbone et coût ===")
  #  print("Slugs énergie :", slugs_energie)
   # print("Consommations :", consos)
   # print("Réseau principal :", reseau_principal, " | Réseau appoint :", reseau_appoint)

    for i in range(len(slugs_energie)):
        slug = slugs_energie[i]
        conso_i = float(consos[i])
        id_reseau = None

        if slug in ["rcu", "rfu"]:
            id_reseau = reseau_principal if i == 0 else reseau_appoint
            print(f"\n🔁 Energie réseau détectée ({slug}), ID réseau utilisé : {id_reseau}")
        else:
            print(f"\n🔁 Energie non réseau : {slug}")

        data = load_data_co2_cout(slug, id_reseau)
     #   print("📦 Données chargées :", data)

        facteur_co2 = float(data["grammage_co2_kgco2_kwhef"])
        facteur_cout = float(data["cout_unitaire_euro_par_kwh"])
    #    print(f"🌍 Facteur CO2 : {facteur_co2} kgCO2/kWh")
    #    print(f"💶 Facteur Coût : {facteur_cout} €/kWh")

        impact = conso_i * facteur_co2
        cout = conso_i * facteur_cout
    #    print(f"📈 Consommation : {conso_i} kWh → Impact : {impact} kgCO2 | Coût : {cout} €")

        total_impact += impact
        total_cout += cout

  #  print("\n✅ Total impact carbone :", total_impact)
  #  print("✅ Total coût énergétique :", total_cout)
  #  print("=== Fin calcul carbone et coût ===\n")

    return total_impact, total_cout







def calcul_commun (zone , masque , surface_PV , prod_solaire_existante, pv_saisie , thermique_saisie , surface_thermique):
    hypothese_puissance_pv = 180  # Wc/m²   #01_Hypothèse puissance = 'BDD hypothèses ENR'!B3
    taux_autoconso_pv = 0.6  ## donné fixe  ## 'BBD Conso-Carbone'!H21 = 
    Hypothèse_rendement_ST_01 = 550

    productible_zone = ZONES[zone]  
    coef_perte = COEF_PERTE_RENDEMENT[masque]
    productible_PV = productible_zone * coef_perte
    productible_thermique = Hypothèse_rendement_ST_01 * coef_perte

    
    if prod_solaire_existante == 0:
        pv_retenue = 0
    elif pv_saisie >0  :
        pv_retenue = pv_saisie
    else:
        pv_retenue = (surface_PV * hypothese_puissance_pv * productible_PV / 1000) * taux_autoconso_pv


    if prod_solaire_existante == 0:
        thermique_retenue = 0
    elif thermique_saisie is not None and thermique_saisie > 0:
        thermique_retenue = thermique_saisie
    else:
         thermique_retenue = (surface_thermique * productible_thermique) / 1000


    P_EnR_locale_solaire_existante = thermique_retenue + pv_retenue

  ##  print (f"production_pv_retenue: {pv_retenue}, production_thermique_retenue: {thermique_retenue}, P_EnR_locale_solaire_existante: {P_EnR_locale_solaire_existante}")

    return P_EnR_locale_solaire_existante  , productible_thermique , productible_PV 



def repartition_usages(slug_principal , slug_appoint , calcul_conso_chauffage , conso_elec , rendement_production , Consommation_ventilation , Conso_specifique, Conso_eclairage,Consommations_annuelles_totales_initiales, usage_thermique,zone_climatique , surface ,  typology ,besoins_ECS , temperature_retenue , type_prod_ecs , jours_ouvrés , rendement , E_T_principal , E_T_appoint , conso_principal_1_convertie , conso_principal_2_convertie , Energie_ECS , systeme_chauffage , zone , masque , surface_PV , prod_solaire_existante, pv_saisie , thermique_saisie , surface_thermique): 
    P_EnR_locale_solaire_existante  , productible_thermique , productible_PV = calcul_commun (zone , masque , surface_PV , prod_solaire_existante, pv_saisie , thermique_saisie , surface_thermique)
##conso_surfacique_clim
    if usage_thermique in ["chauffage + clim + ecs", "chauffage + clim"]:
        conso_surfacique_clim = conso_clim[typology][zone_climatique]
    elif usage_thermique in ["chauffage + ecs", "chauffage"]:
        conso_surfacique_clim = 0
    else:
        raise ValueError(f"Type d'usage thermique non reconnu : {usage_thermique}")

#besoins_60   
    besoin_60 = (besoins_ECS * (40 - temperature_retenue)) / (60 - temperature_retenue)

##perte_bouclage    
    if not type_prod_ecs:
        raise ValueError(f"Slug de type_production_ecs inconnu : {type_prod_ecs}")

    # Attribution des pertes selon le type
    if type_prod_ecs == "production individuelle":
        perte_bouclage = 0.2
    elif type_prod_ecs == "production collective":
        perte_bouclage = 0.6
    else:
        raise ValueError(f"Type de production ECS inconnu : {type_prod_ecs}")
    
##Conso_E_ecs:

    if usage_thermique in ["chauffage + clim + ecs", "chauffage + ecs"]:
        conso_E_ECS = (Capacité_thermique_volumique_eau / 1000) * besoin_60 * (temperature_chaude - temperature_retenue)* jours_ouvrés* ((100 + (perte_bouclage*100))/100) / rendement
    elif usage_thermique in ["chauffage + clim", "chauffage"]:
        conso_E_ECS = 0 
    else :
        raise ValueError(f"Type d'usage thermique inconnu : {usage_thermique}")
    


##la repartition d'usages : 
    chauffage = calcul_conso_chauffage
    climatisation = conso_surfacique_clim
    ECS = conso_E_ECS
    autres_usages = Consommation_ventilation + Conso_eclairage + Conso_specifique 
    total = calcul_conso_chauffage + conso_surfacique_clim + conso_E_ECS + autres_usages
#Répartition par usage (kWh/)
    chauffage_kwh = chauffage * surface
    climatisation_kwh = climatisation * surface
    ECS_kwh = ECS * surface
    autres_usages_kwh = autres_usages * surface
    total_kwh = chauffage_kwh + climatisation_kwh + ECS_kwh + autres_usages_kwh 
#Répartition par usage calcul conso (%)
    chauffage_kwh_P = chauffage_kwh / total_kwh
    climatisation_kwh_P = climatisation_kwh /total_kwh
    ECS_kwh_P = ECS_kwh / total_kwh
    autres_usages_kwh_P = autres_usages_kwh / total_kwh
    total_P = chauffage_kwh_P + climatisation_kwh_P + ECS_kwh_P + autres_usages_kwh_P

    repartition_conso_hors_clim = ECS_kwh /(ECS_kwh + chauffage_kwh )

  #  print("les pourcentages par usages ")

   # print(chauffage_kwh_P , climatisation_kwh_P , ECS_kwh_P , autres_usages_kwh_P ,total_P )
###Energie thermique 1 
#### Climatisation 

    if E_T_principal== "Réseau de froid":
        calibration_ET1_clim = conso_principal_1_convertie
    elif E_T_principal in  ["Aucune" , "Fioul" , "Charbon" , "Bois plaquettes", "Bois granulés" , "Réseau de chaleur" , "Gaz butane/propane" , "Gaz naturel" ]:
        calibration_ET1_clim = 0 
    else : 
        raise ValueError(f"Type d'energie principal termique inconnu : {E_T_principal}")
    
##Energie_ECS
    if Energie_ECS in [ "Electrique" , "PAC" , "Géothermie" , "Inconnu"] or E_T_principal in ["Réseau de froid" , "Aucune"] :
        calibration_ET1_ECS = 0
    elif Energie_ECS == systeme_chauffage :
        calibration_ET1_ECS = repartition_conso_hors_clim *conso_principal_1_convertie
    else : 
        calibration_ET1_ECS = conso_principal_1_convertie
   
    print(f"🔋 Valeur  ECS : {calibration_ET1_ECS} kWh")
##chuffage

    if systeme_chauffage in [ "Electrique" , "PAC" , "Géothermie" , "Inconnu"] or  E_T_principal in ["Réseau de froid" , "Aucune"] :
        calibration_ET1_chauffage = 0
    elif Energie_ECS == systeme_chauffage :
        calibration_ET1_chauffage = conso_principal_1_convertie - calibration_ET1_ECS
    else : 
        calibration_ET1_chauffage = conso_principal_1_convertie

    ##total energie thermique 1 :
    total_thermique1 = calibration_ET1_chauffage + calibration_ET1_ECS  + calibration_ET1_clim
    #print(f"total thermique 1  : {total_thermique1}")


    ###Energie thermique 2
#climatisation 

    if E_T_appoint== "Réseau de froid":
        calibration_ET2_clim = conso_principal_2_convertie
    elif E_T_appoint in  ["Aucune" , "Fioul" , "Charbon" , "Bois plaquettes", "Bois granulés" , "Réseau de chaleur" , "Gaz butane/propane" , "Gaz naturel" ]:
        calibration_ET2_clim = 0 
    else : 
        raise ValueError(f"Type d'energie principal termique inconnu : {E_T_appoint}")
    
   # print(f"🔁 la consommation énergitique de climatisation 2 est  : { calibration_ET2_clim} kWh/m²/an")

##Energie_ECS
    if Energie_ECS in [ "Electrique" , "PAC" , "Géothermie" , "Inconnu"] or E_T_appoint in ["Réseau de froid" , "Aucune"] :
        calibration_ET2_ECS = 0
    elif systeme_chauffage == Energie_ECS :
        calibration_ET2_ECS = repartition_conso_hors_clim *conso_principal_2_convertie
    else : 
        calibration_ET2_ECS = conso_principal_2_convertie
   
    #print(f"🔋 Valeur  ECS 2: {calibration_ET2_ECS} kWh")

##chuffage

    if systeme_chauffage in [ "Electrique" , "PAC" , "Géothermie" , "Inconnu"] or  E_T_appoint in ["Réseau de froid" , "Aucune"] :
        calibration_ET2_chauffage = 0
    elif Energie_ECS == systeme_chauffage :
        calibration_ET2_chauffage = conso_principal_2_convertie - calibration_ET2_ECS
    else : 
        calibration_ET2_chauffage = conso_principal_2_convertie

   # print(f"calibration chuffage 2: {calibration_ET2_chauffage}")
   
##total energie thermique 2 :
    total_thermique2 = calibration_ET2_chauffage + calibration_ET2_ECS  + calibration_ET2_clim
    #print(f"total thermique 2  : {total_thermique2}")

###elec
 
 ### chauffage 
    if (calibration_ET1_chauffage + calibration_ET2_chauffage ) == 0:
        calibration_elec_chauffage = Consommations_annuelles_totales_initiales * chauffage_kwh_P
    else :
        calibration_elec_chauffage = 0 

  #  print(f"calibration chuffage_elec: {calibration_elec_chauffage}")   

 ##Climatisation 
    if (calibration_ET1_clim + calibration_ET2_clim) == 0 :
        calibration_elec_clim = Consommations_annuelles_totales_initiales * climatisation_kwh_P
    else : 
        calibration_elec_clim = 0 
    #print(f"calibration_elec_clim: {calibration_elec_clim}")   
    
## ECS
    if (calibration_ET1_ECS + calibration_ET2_ECS)== 0 :
        calibration_elec_ECS = Consommations_annuelles_totales_initiales * ECS_kwh_P
    else : 
        calibration_elec_ECS =  0
    #print(f"calibration_elec_ECS : {calibration_elec_ECS}")
##Autres usages 
    calibration_elec_autres_usages = conso_elec - (calibration_elec_chauffage + calibration_elec_clim + calibration_elec_ECS)
   # print(f"calibration_elec_autres_usages : {calibration_elec_autres_usages}")
## total Elec 
    total_elec = calibration_elec_chauffage + calibration_elec_clim  + calibration_elec_ECS + calibration_elec_autres_usages
   # print(f"total thermique 2  : {total_elec}")

 #   print ("les calibrations sont ")
  #  print(calibration_elec_chauffage ,calibration_ET1_chauffage , calibration_ET2_chauffage )


#le total des troix : 
    total_chauffage = calibration_elec_chauffage + calibration_ET1_chauffage +calibration_ET2_chauffage
    total_climatisation = calibration_elec_clim + calibration_ET1_clim +calibration_ET2_clim
    total_ECS = calibration_elec_ECS + calibration_ET1_ECS + calibration_ET2_ECS
    total_autres_usages = calibration_elec_autres_usages 
    total_final = total_ECS +total_chauffage + total_climatisation +total_autres_usages 

    ratio_chauffage = total_chauffage / surface
    ratio_climatisation = total_climatisation / surface
    ratio_ecs = total_ECS / surface
    ratio_autres_usages = total_autres_usages / surface
    ratio_total_final = total_final / surface


###ratio_consommation par usaaage 
    ratio_ET1 = total_thermique1 / total_final
    ratio_ET2 = total_thermique2 / total_final
    ratio_elec= conso_elec / total_final
    total_ratio = ratio_ET1 + ratio_ET2 + ratio_elec
 

## energie_PAC_delivre_existante
    if systeme_chauffage in [ "PAC" , "Géothermie" ] :
        energie_PAC_delivre1 = total_chauffage * couverture_PAC_Chauffage
    else :
        energie_PAC_delivre1 = 0

    if Energie_ECS in ["PAC" , "Géothermie"] :
        energie_PAC_delivre2 = total_ECS * couverture_PAC_ECS
    else :
        energie_PAC_delivre2 = 0

    energie_PAC_delivre = energie_PAC_delivre2 + energie_PAC_delivre1

##Consommation élec PAC calculée 
    
    if systeme_chauffage in [ "PAC" , "Géothermie" ] :
        conso_elec_PAC_1 = total_chauffage * couverture_PAC_Chauffage * rendement * rendement_production
    else :
        conso_elec_PAC_1 = 0

    if Energie_ECS in ["PAC" , "Géothermie"] :
        conso_elec_PAC_2 = total_ECS * couverture_PAC_ECS / rendement
    
    else :
        conso_elec_PAC_2 = 0
    
    conso_elec_PAC = conso_elec_PAC_1 + conso_elec_PAC_2



##Production EnR locale Bois
    if E_T_principal in ["Bois plaquettes", "Bois granulés"] : 
        Prod_enr_bois1 = conso_principal_1_convertie
    else :
        Prod_enr_bois1 = 0 

    if E_T_appoint in ["Bois plaquettes", "Bois granulés"] :
        Prod_enr_bois2 = conso_principal_2_convertie
    else : 
        Prod_enr_bois2 = 0 

    Prod_enr_bois = Prod_enr_bois1 + Prod_enr_bois2


######Production EnR&R locale consommée sur site 

    energies_biomasse = ["Bois plaquettes", "Bois granulés"]

    # Standardisation

 #   print(f"energie_PAC_delivre : {energie_PAC_delivre}")
  #  print(f"P_EnR_locale_solaire_existante : {P_EnR_locale_solaire_existante}")

    prod_enr_locale_site = 0
    if E_T_principal in energies_biomasse:
        prod_enr_locale_site += conso_principal_1_convertie

    if E_T_appoint in energies_biomasse:
        prod_enr_locale_site += conso_principal_2_convertie

    prod_enr_locale_site += energie_PAC_delivre + P_EnR_locale_solaire_existante - conso_elec_PAC
    print(f"🌲 Production EnR&R locale consommée sur site  : {round(prod_enr_locale_site, 2)} kWhEF/an")  
    

##taux enr local initial : 
    if energie_PAC_delivre > 0:
            denominateur = conso_elec + (total_chauffage * rendement )
    else:
            denominateur = Consommations_annuelles_totales_initiales

    if denominateur == 0:
            denominateur = 0

    taux = prod_enr_locale_site / denominateur 
    taux_enr_initial = taux * 100

    conso_energitiques = [
    {"elec": round(float(ratio_elec) * 100, 2)},
    {slug_principal: round(float(ratio_ET1) * 100, 2)},
    {slug_appoint: round(float(ratio_ET2) * 100, 2)},
    {"total_cons_energ": round(float(total_ratio) * 100, 2)}
]
    
    usages_energitiques = [
    {"chauffage": round(float(ratio_chauffage) , 2)},
    {"climatisation": round(float(ratio_climatisation) , 2)},
    {"ecs": round(float(ratio_ecs) , 2)},
    {"autre_usages": round(float(ratio_autres_usages) , 2)},
    {"total_usages_energ": round(float(ratio_total_final) , 2)}
]


   # print(conso_surfacique_clim , total_ECS , besoin_60 , perte_bouclage )

   # print ("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")

   # print(conso_E_ECS , round(float(taux_enr_initial) * 100, 3) , Prod_enr_bois , conso_elec_PAC )


    print ("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")

    print(usages_energitiques)

    print ("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")

    print(conso_energitiques)
    return conso_surfacique_clim , total_ECS , besoin_60 , perte_bouclage , conso_E_ECS , taux_enr_initial , Prod_enr_bois , conso_elec_PAC , usages_energitiques , conso_energitiques , energie_PAC_delivre


def calcul_Pv (slug_principal , slug_appoint ,type_toiture ,conso_elec , surface , slugs_energie,  strategie , E_T_principal , E_T_appoint , reseau_principal , reseau_appoint , taux_enr_principal , taux_enr_appoint , encombrement_toiture , conso_principal_1_convertie,conso_principal_2_convertie , surface_toiture , surface_parking , zone , masque ,systeme_chauffage , typologie ,  surface_PV , prod_solaire_existante, pv_saisie , thermique_saisie , surface_thermique , calcul_conso_chauffage , rendement_production , Consommation_ventilation , Conso_specifique, Conso_eclairage ,Consommations_annuelles_totales_initiales , Energie_ECS ,  rendement , jours_ouvrés ,besoins_ECS , temperature_retenue , type_prod_ecs , usage_thermique,zone_climatique  ,  typology  ) : 
    hypothese_puissance = 180
    taux_baisse = Baisse_conso_besoins.get(strategie, 0)  

    P_EnR_locale_solaire_existante  , productible_thermique , productible_PV = calcul_commun(zone , masque , surface_PV , prod_solaire_existante, pv_saisie , thermique_saisie , surface_thermique)
   # conso_surfacique_clim , besoin_60 , perte_bouclage , conso_E_ECS , taux_enr_initial , Prod_enr_bois , conso_elec_PAC , usages_energitiques , conso_energitiques , energie_PAC_delivre = 
    conso_surfacique_clim , total_ECS , besoin_60 , perte_bouclage , conso_E_ECS , taux_enr_initial , Prod_enr_bois , conso_elec_PAC , usages_energitiques , conso_energitiques , energie_PAC_delivre = repartition_usages(slug_principal , slug_appoint , calcul_conso_chauffage , conso_elec , rendement_production , Consommation_ventilation , Conso_specifique, Conso_eclairage,Consommations_annuelles_totales_initiales, usage_thermique,zone_climatique , surface ,  typology ,besoins_ECS , temperature_retenue , type_prod_ecs , jours_ouvrés , rendement , E_T_principal , E_T_appoint , conso_principal_1_convertie , conso_principal_2_convertie , Energie_ECS , systeme_chauffage , zone , masque , surface_PV , prod_solaire_existante, pv_saisie , thermique_saisie , surface_thermique)
  #  print("productible photovo")
  #  print(productible_PV)

    with engine.connect() as conn:
        df_charges = pd.read_sql_query("SELECT * FROM dbo.courbes_charge_electrique", conn)
        df_occup = pd.read_sql_query("SELECT * FROM [dbo].[dimensionnement PV1]", conn)

       
        df_Profil_solaire = pd.read_sql_query("SELECT * FROM dbo.profil_solaire_pas_horaire", conn)

    
        df_charges["Date_Heure"] = pd.to_datetime(df_charges["Date_Heure"])
        df_occup["date_heure"] = pd.to_datetime(df_occup["date_heure"])
        df_Profil_solaire["Date_Heure"] = pd.to_datetime(df_Profil_solaire["Date_Heure"])




    # 1 - Calcul Surface PV toiture max
    coef_surface_pv = HYPOTHESE_SURFACE_PV[(type_toiture, encombrement_toiture)]
    surface_pv_toiture_max = surface_toiture * coef_surface_pv

    # 2 - Surface PV parking max
    surface_pv_parking_max = surface_parking * 0.9
    productible_zone = ZONES[zone]  
    coef_perte = COEF_PERTE_RENDEMENT[masque]
    productible = productible_zone * coef_perte

    puissance_pv_max = ((surface_pv_toiture_max + surface_pv_parking_max) * hypothese_puissance)/1000
##talon locale PV 

    if systeme_chauffage== "Electrique" : 
        systeme_chauffage1 = 'Electrique'
    else : 
        systeme_chauffage1 = 'Autre'

    profil_horaire = mapping[(typology, systeme_chauffage1)]
    df_occup['charge_electrique'] = df_charges[profil_horaire] * conso_elec
    df_occupation = df_occup[df_occup["occupation_label"] == "Occupation"]

    # Moyenne pondérée à la main
    total = df_occupation.groupby("mois")["charge_electrique"].sum().sum()
    n_total = df_occupation.groupby("mois")["charge_electrique"].count().sum()
    puissance_talon_elec = total / n_total

    Puissance_pv_retenue = min(puissance_pv_max, puissance_talon_elec)
    Production_EnR_local_PV = Puissance_pv_retenue * productible 
    production_ENR_local_PV_max = Puissance_pv_retenue *productible

  #  print ("les productions retenue ")
  #  print(Production_EnR_local_PV)

    
    ## Production EnR locale PV autoconsommée optimisé et maximal 
    df_occup['kWh produit scénario optimisé'] =  (df_Profil_solaire[zone] * Production_EnR_local_PV).round(2)
  #  print(df_occup['kWh produit scénario optimisé'].head(20) )
  #  print(df_occup["charge_electrique"].head(20))
    df_occup["kWh produit scénario optimisé"] = pd.to_numeric(df_occup["kWh produit scénario optimisé"], errors="coerce").fillna(0)
    df_occup["charge_electrique"] = pd.to_numeric(df_occup["charge_electrique"], errors="coerce").fillna(0)

    df_occup["Autoconso PV scénario optimisé"] = df_occup[["kWh produit scénario optimisé", "charge_electrique"]].min(axis=1).round(2)




    Production_EnR_locale_PV_autoconsommée = df_occup["Autoconso PV scénario optimisé"].sum()
 #   print(df_occup['Autoconso PV scénario optimisé'].head(20))

    taux_autoconsommation_solaire = round(Production_EnR_locale_PV_autoconsommée / Production_EnR_local_PV)

   # print(Production_EnR_locale_PV_autoconsommée)

    ## Production EnR locale PV autoconsommée optimisé et maximal 
    df_occup['kWh produit scénario max'] =  (df_Profil_solaire[zone] * production_ENR_local_PV_max).round(2)
    df_occup["kWh produit scénario max"] =   pd.to_numeric(df_occup["kWh produit scénario max"], errors="coerce").fillna(0)


    
    df_occup['Autoconso PV scénario max'] = (df_occup[["kWh produit scénario max", "charge_electrique"]].min(axis=1)).round(2)
    Production_EnR_locale_PV_autoconsommée_max = df_occup["Autoconso PV scénario max"].sum()
    taux_autoconsommation_solaire_max = round(Production_EnR_locale_PV_autoconsommée_max / production_ENR_local_PV_max)

   
   
##Production EnR locale totale (existante + solaire PV)
    Prod_enr_locale_totale = P_EnR_locale_solaire_existante +energie_PAC_delivre - conso_elec_PAC + Prod_enr_bois + Production_EnR_locale_PV_autoconsommée
    Prod_enr_locale_totale_scenario_max =  P_EnR_locale_solaire_existante +energie_PAC_delivre - conso_elec_PAC + Prod_enr_bois + Production_EnR_locale_PV_autoconsommée_max
    #print(f"Production EnR locale totale (existante + solaire PV) : {Prod_enr_locale_totale}")

### les consommations projettées : 
#0 . Consommation élec projetée
    conso_elec_proj = conso_elec * (1 - taux_baisse) - Production_EnR_locale_PV_autoconsommée
    conso_elec_proj_scenario_max = conso_elec * (1 - taux_baisse) - Production_EnR_locale_PV_autoconsommée_max
 # 1. Consommation thermique principale projetée

    conso_thermique_principale_proj = conso_principal_1_convertie * (1 - taux_baisse)

# 2. Consommation appoint projetée
    conso_thermique_appoint_proj = conso_principal_2_convertie * (1 - taux_baisse)

# 3. Somme globale
    conso_totale_proj_PV = conso_elec_proj + conso_thermique_principale_proj + conso_thermique_appoint_proj
    ratio_conso_totale_proj_PV = conso_totale_proj_PV / surface 

 #4. Taux ENR&R locale : (optimisé & maximum)

    enr_local_pv = (Prod_enr_locale_totale /( conso_totale_proj_PV +energie_PAC_delivre ))*100
    enr_local_max_pv = (Prod_enr_locale_totale_scenario_max /( conso_totale_proj_PV +energie_PAC_delivre ))*100

##on passe au calcul rcu : 
    conso_elec_rcu = conso_elec_proj
    conso_principal_rcu = conso_thermique_principale_proj

    # Calculs selon les types d'énergie
    enr_principale = conso_principal_rcu * taux_enr_principal if E_T_principal == "Réseau de chaleur" else 0
    enr_appoint = conso_thermique_appoint_proj * taux_enr_appoint if E_T_appoint == "Réseau de chaleur" else 0

    production_enr_rcu = enr_principale + enr_appoint
  #  print(f"conso_thermique_principale_proj : {conso_thermique_principale_proj} ")
  #  print(f"conso_thermique_appoint_proj : {conso_thermique_appoint_proj} ")




   # print("Type conso_principal_rcu:", type(conso_principal_rcu))
  #  print("Valeur conso_principal_rcu:", conso_principal_rcu)

      
## Production enr mix electrique & gaz 
    production_enr_elec = conso_elec_rcu * Taux_EnR_mix_E_national_Elec
    if isinstance(conso_principal_rcu, str):
       conso_principal_rcu = float(conso_principal_rcu)

    enr_gaz_principal = (
      conso_principal_rcu * Taux_EnR_mix_E_national_Gaz
      if E_T_principal.strip().lower() == "gaz naturel"
      else 0
)


    if isinstance(conso_thermique_appoint_proj, str):
      conso_thermique_appoint_proj = float(conso_thermique_appoint_proj)

    enr_gaz_appoint = (
    conso_thermique_appoint_proj * Taux_EnR_mix_E_national_Gaz
    if E_T_appoint.strip().lower() == "gaz naturel"
    else 0
)


    production_enr_mix = production_enr_elec + enr_gaz_principal + enr_gaz_appoint
    #print(f"production_enr_mix electrique & gaz : {production_enr_mix}")

    ## production ENR globale 
    production_globale = production_enr_mix + production_enr_rcu + Prod_enr_locale_totale
    production_globale_scenario_max  = production_enr_mix + production_enr_rcu + Prod_enr_locale_totale_scenario_max
    #print(f"production enr globale : {production_globale}")

    ## Taux enr globale 
    enr_globale = (production_globale / (conso_totale_proj_PV + energie_PAC_delivre))*100
    enr_globale_scenario_max = (production_globale_scenario_max / (conso_totale_proj_PV + energie_PAC_delivre))*100
    consos = [conso_thermique_principale_proj , conso_thermique_appoint_proj , conso_elec_proj]

    ratio_conso_totale_projet_pv = conso_totale_proj_PV / surface

    total_impact_pv, total_cout_pv = calcul_carbone_et_cout_sql(slugs_energie , consos ,reseau_principal , reseau_appoint )
    
   # print(pmoy_mensuelle)
   # print(f"puissance_talon_elec : {puissance_talon_elec}")
#    print(f"puissance retenue est : {Puissance_pv_retenue}")
 #   print(f"Production_EnR_locale_PV_autoconsommée : {Production_EnR_locale_PV_autoconsommée}")
  #  print(f"Production_EnR_locale_PV_autoconsommée_scénario_maximum : {Production_EnR_locale_PV_autoconsommée_max}")
  #  print(f"taux enr local : {enr_local_pv}")
 #   print(f"Consommation totale projetée:{conso_totale_proj_PV}")
  #  print(production_enr_rcu)
   # print(production_enr_mix)



   # print(f"Production_EnR_local_PV:{Production_EnR_local_PV}")
   # print(f"taux_autoconsommation_solaire : {taux_autoconsommation_solaire * 100} %")
   # print(f"Taux ENR&r GLOBALE : {enr_globale } %")
   # print(f"Taux ENR&r GLOBALE _ scénario max : {enr_globale_scenario_max } %")
   # print(f"production enr globale : {production_globale}")
   # print(f"cout total  : {total_cout_pv}")
   # print(f"projection carbone total  : {total_impact_pv}")


    return Puissance_pv_retenue  ,ratio_conso_totale_projet_pv ,  enr_local_pv , enr_local_max_pv , enr_globale , enr_globale_scenario_max  ,   total_impact_pv, total_cout_pv , conso_thermique_appoint_proj , surface_pv_toiture_max









def calcul_thermique (slug_principal , slug_appoint , type_toiture , rendement ,conso_elec , strategie , E_T_principal , E_T_appoint , surface , slugs_energie , taux_enr_principal , taux_enr_appoint , reseau_principal , reseau_appoint ,  conso_principal_1_convertie , conso_principal_2_convertie   , zone , masque , surface_PV , prod_solaire_existante, pv_saisie , thermique_saisie , surface_thermique , calcul_conso_chauffage, rendement_production , Consommation_ventilation , Conso_specifique, Conso_eclairage,Consommations_annuelles_totales_initiales, Energie_ECS , systeme_chauffage , encombrement_toiture ,usage_thermique,zone_climatique , surface_parking ,  surface_toiture , typology ,besoins_ECS , temperature_retenue , typologie ,  type_prod_ecs , jours_ouvrés  ) : 
    hypothese_rendement_st = 550
    hypothèses_volume_ST = 50 
    Hypothese_surface_LT_ST = 4
    hypothese_taux_couverture = 60 /100 
    taux_baisse = Baisse_conso_besoins.get(strategie, 0)  

    conso_surfacique_clim , total_ECS , besoin_60 , perte_bouclage , conso_E_ECS , taux_enr_initial , Prod_enr_bois , conso_elec_PAC , usages_energitiques , conso_energitiques , energie_PAC_delivre = repartition_usages(slug_principal , slug_appoint , calcul_conso_chauffage , conso_elec , rendement_production , Consommation_ventilation , Conso_specifique, Conso_eclairage,Consommations_annuelles_totales_initiales, usage_thermique,zone_climatique , surface ,  typology ,besoins_ECS , temperature_retenue , type_prod_ecs , jours_ouvrés , rendement , E_T_principal , E_T_appoint , conso_principal_1_convertie , conso_principal_2_convertie , Energie_ECS , systeme_chauffage , zone , masque , surface_PV , prod_solaire_existante, pv_saisie , thermique_saisie , surface_thermique)

    P_EnR_locale_solaire_existante  , productible_solaire_thermique , productible_PV  = calcul_commun(zone , masque , surface_PV , prod_solaire_existante, pv_saisie , thermique_saisie , surface_thermique)
    Puissance_pv_retenue  ,ratio_conso_totale_projet_pv ,  enr_local_pv , enr_local_max_pv , enr_globale , enr_globale_scenario_max  ,   total_impact_pv, total_cout_pv , conso_thermique_appoint_proj , surface_pv_toiture_max =  calcul_Pv (slug_principal , slug_appoint ,type_toiture ,conso_elec , surface , slugs_energie,  strategie , E_T_principal , E_T_appoint , reseau_principal , reseau_appoint , taux_enr_principal , taux_enr_appoint , encombrement_toiture , conso_principal_1_convertie,conso_principal_2_convertie , surface_toiture , surface_parking , zone , masque ,systeme_chauffage , typologie ,  surface_PV , prod_solaire_existante, pv_saisie , thermique_saisie , surface_thermique , calcul_conso_chauffage , rendement_production , Consommation_ventilation , Conso_specifique, Conso_eclairage ,Consommations_annuelles_totales_initiales , Energie_ECS ,  rendement , jours_ouvrés ,besoins_ECS , temperature_retenue , type_prod_ecs , usage_thermique,zone_climatique  ,  typology  ) 


##surface solaire thermique max

    if type_toiture == "Inclinée bac acier ou autres":
       surface_solaire_thermique_max = 0
    else : 
        surface_solaire_thermique_max = surface_pv_toiture_max

   # print(f"la  Production Solaire Thermique max est : {surface_solaire_thermique_max}")
  #  print(f"la  Production Solaire Thermique max est : {productible_solaire_thermique}")



    
    # Production Solaire Thermique max
    Production_Solaire_Thermique_max = productible_solaire_thermique * surface_solaire_thermique_max
  #  print(f"la  Production Solaire Thermique max est : {Production_Solaire_Thermique_max}")
#stockage ECS Solaire 
    Stockage_ecs_solaire = hypothèses_volume_ST * surface_solaire_thermique_max
  #  print(f"stockage ECS Solaire est : {Stockage_ecs_solaire}")
# besoins
    besoins_ECS_thermique = rendement * total_ECS
 #   print(f"besoin ECS du solaire thermique est : {besoins_ECS_thermique}")
#surface_solaire_thermique_calculée 
    surface_solaire_thermique_calcule = besoins_ECS_thermique *  hypothese_taux_couverture / hypothese_rendement_st 
 #   print(f"surface solaire thermique calculée est : {surface_solaire_thermique_calcule}")

#surface_solaire_thermique_calculée 
    surface_solaire_thermique_calcule = besoins_ECS_thermique *  hypothese_taux_couverture / hypothese_rendement_st 
 #   print(f"surface solaire thermique calculée est : {surface_solaire_thermique_calcule}")
#surface solaire thermique retenue 
    surface_solaire_thermique_retenue = min(surface_solaire_thermique_max , surface_solaire_thermique_calcule )
 #   print(f"surface solaire thermique retenue : {surface_solaire_thermique_retenue}")
#surface locale technique 
    Surface_locale_tec = surface_solaire_thermique_retenue / 1000 * Hypothese_surface_LT_ST + 20 
 #   print(f"la  surface locale technique thermique  est : {Surface_locale_tec}")
#production ENR locale solaire thermique 
    prod_enr_locale_solaire_thermique = surface_solaire_thermique_retenue * productible_solaire_thermique
  #  print(f"production ENR locale solaire thermique : {prod_enr_locale_solaire_thermique}")
 #   print(f"production ENR locale solaire existante : {P_EnR_locale_solaire_existante}")

#Production EnR locale totale (existante + solaire thermique)
    Prod_enr_locale_totale_thermique = P_EnR_locale_solaire_existante + energie_PAC_delivre - conso_elec_PAC + Prod_enr_bois + prod_enr_locale_solaire_thermique
  #  print(f"Production EnR locale totale _ thermique__ (existante + solaire PV) : {Prod_enr_locale_totale_thermique}")


# les Consommation élec projetée : 
    conso_elec_proj_thermique = conso_elec * (1 - taux_baisse) 
    
    # Si pas d’énergie thermique principale, retirer la production solaire thermique
    if E_T_principal.strip().lower() == "Aucune":
         conso_elec_proj_thermique -= prod_enr_locale_solaire_thermique
    
  #  print(f"le taux de baisse est : {taux_baisse}")
  #  print(f"la consommation elec -thermique- projetée : {conso_elec_proj_thermique}")
  #  print(f"prod_enr_locale_solaire_thermique1: {prod_enr_locale_solaire_thermique}")

    # 1. Consommation thermique principale projetée

    conso_thermique_principale_proj_thermique = conso_principal_1_convertie * (1 - taux_baisse)

    if E_T_principal in ["Charbon" ,"Gaz naturel" , "Gaz butane/propane" , "Fioul" , "Bois plaquettes" , "Bois granulés" , "Réseau de chaleur"  ] :
        conso_thermique_principale_proj_thermique -= prod_enr_locale_solaire_thermique
   # print(f"la consommation thermique principale projetée-thermique- de l'energie : {E_T_principal} est : {conso_thermique_principale_proj_thermique}")

    # 2. Consommation appoint projetée :
    conso_thermique_appoint_proj_thermique = conso_principal_2_convertie * (1 - taux_baisse)
  #  print(f"la consommation thermique d'appoint projetée-thermique : {conso_thermique_appoint_proj_thermique}")
    # 3. Somme globale :
    conso_totale_proj_thermique = conso_elec_proj_thermique + conso_thermique_principale_proj_thermique + conso_thermique_appoint_proj_thermique
    ratio_conso_totale_proj_thermique = conso_totale_proj_thermique / surface 

   # print(f"la consommation totale projetée : {conso_totale_proj_thermique}")
    #Taux EnR&R local
    taux_ENR_Local_thermique = ((Prod_enr_locale_totale_thermique / (conso_totale_proj_thermique + energie_PAC_delivre))*100)
    taux_ENR_Local_thermique_max = taux_ENR_Local_thermique
  #  print(f"Taux EnR&R local : {taux_ENR_Local_thermique}")
 #   print(f"Taux EnR&R local_maximal  : {taux_ENR_Local_thermique_max}")







    #Production ENR RCU 
    ##on passe au calcul rcu : 
    conso_elec_rcu = conso_elec_proj_thermique
    conso_principal_rcu = conso_thermique_principale_proj_thermique

    # Calculs selon les types d'énergie
    enr_principale = conso_principal_rcu * taux_enr_principal if E_T_principal == "Réseau de chaleur" else 0
    enr_appoint = conso_thermique_appoint_proj_thermique * taux_enr_appoint if E_T_appoint == "Réseau de chaleur" else 0

    production_enr_rcu_thermique = enr_principale + enr_appoint
      
## Production enr mix electrique & gaz 
    production_enr_elec = conso_elec_rcu * Taux_EnR_mix_E_national_Elec

    enr_gaz_principal = (
        conso_principal_rcu * Taux_EnR_mix_E_national_Gaz
        if E_T_principal.strip().lower() == "gaz naturel"
        else 0 )

    enr_gaz_appoint = (
        conso_thermique_appoint_proj_thermique * Taux_EnR_mix_E_national_Gaz
        if E_T_appoint.strip().lower() == "gaz naturel"
        else 0)

    production_enr_mix_thermique = production_enr_elec + enr_gaz_principal + enr_gaz_appoint
    ## production ENR&R globale  
    prod_ENR_globale_Thermique = production_enr_rcu_thermique + production_enr_mix_thermique + Prod_enr_locale_totale_thermique
   # print (f"production enr Globale Thermique : {prod_ENR_globale_Thermique}")

    ##Taux ENR&R globale Thermique
    enr_globale_thermique =  (prod_ENR_globale_Thermique / (conso_totale_proj_thermique + energie_PAC_delivre))*100 
    enr_globale_thermique_scenario_max = enr_globale_thermique
  #  print(f"le taux ENR&R global thermique est : {enr_globale_thermique}")

    conso_thermique = [ conso_thermique_principale_proj_thermique , conso_thermique_appoint_proj  , conso_elec_proj_thermique]
    total_impact_thermique, total_cout_thermique = calcul_carbone_et_cout_sql(slugs_energie , conso_thermique ,reseau_principal , reseau_appoint )

    return  surface_solaire_thermique_retenue ,  ratio_conso_totale_proj_thermique , taux_ENR_Local_thermique , taux_ENR_Local_thermique_max , enr_globale_thermique , enr_globale_thermique_scenario_max ,  total_impact_thermique ,    total_cout_thermique






####""----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------#######

def calcul_hybride(slug_principal , slug_appoint ,type_toiture , rendement  , conso_elec , slugs_energie , strategie , E_T_principal , E_T_appoint ,  surface , taux_enr_principal , reseau_principal , reseau_appoint , taux_enr_appoint ,  conso_principal_1_convertie , conso_principal_2_convertie , calcul_conso_chauffage ,zone , masque , surface_PV , prod_solaire_existante, pv_saisie , thermique_saisie , surface_thermique ,  rendement_production , Consommation_ventilation , Conso_specifique, Conso_eclairage,Consommations_annuelles_totales_initiales, typology ,besoins_ECS , encombrement_toiture, temperature_retenue , type_prod_ecs , jours_ouvrés ,  usage_thermique,zone_climatique , surface_toiture , surface_parking , typologie, Energie_ECS , systeme_chauffage ) :
    #P_EnR_locale_solaire_existante  , productible_solaire_thermique , productible_PV = calcul_commun
    P_EnR_locale_solaire_existante  , productible_solaire_thermique , productible_PV  = calcul_commun(zone , masque , surface_PV , prod_solaire_existante, pv_saisie , thermique_saisie , surface_thermique)

    conso_surfacique_clim , total_ECS , besoin_60 , perte_bouclage , conso_E_ECS , taux_enr_initial , Prod_enr_bois , conso_elec_PAC , usages_energitiques , conso_energitiques , energie_PAC_delivre = repartition_usages(slug_principal , slug_appoint ,calcul_conso_chauffage , conso_elec , rendement_production , Consommation_ventilation , Conso_specifique, Conso_eclairage,Consommations_annuelles_totales_initiales, usage_thermique,zone_climatique , surface ,  typology ,besoins_ECS , temperature_retenue , type_prod_ecs , jours_ouvrés , rendement , E_T_principal , E_T_appoint , conso_principal_1_convertie , conso_principal_2_convertie , Energie_ECS , systeme_chauffage , zone , masque , surface_PV , prod_solaire_existante, pv_saisie , thermique_saisie , surface_thermique)

    taux_baisse = Baisse_conso_besoins.get(strategie, 0)  


    Puissance_pv_retenue  ,ratio_conso_totale_projet_pv ,  enr_local_pv , enr_local_max_pv , enr_globale , enr_globale_scenario_max  ,   total_impact_pv, total_cout_pv , conso_thermique_appoint_proj , surface_pv_toiture_max =  calcul_Pv (slug_principal , slug_appoint , type_toiture ,conso_elec , surface , slugs_energie,  strategie , E_T_principal , E_T_appoint , reseau_principal , reseau_appoint , taux_enr_principal , taux_enr_appoint , encombrement_toiture , conso_principal_1_convertie,conso_principal_2_convertie , surface_toiture , surface_parking , zone , masque ,systeme_chauffage , typologie ,  surface_PV , prod_solaire_existante, pv_saisie , thermique_saisie , surface_thermique , calcul_conso_chauffage , rendement_production , Consommation_ventilation , Conso_specifique, Conso_eclairage ,Consommations_annuelles_totales_initiales , Energie_ECS ,  rendement , jours_ouvrés ,besoins_ECS , temperature_retenue , type_prod_ecs , usage_thermique,zone_climatique  ,  typology  ) 


    Hypotheses_puissance_PV_hybride = 425/(1.899 * 1.096)
    Hypothese_rendement_PV = 1.07
    hypothese_rendement_st_hybride = 0.9
    hypothese_puissance_PAC_hybride =10/70
    hypothese_stockage_ST_hybride = 300
    hypothese_taux_couverture = 85 /100 
    hypothese_COP_PAC_ST =3.5
##Surface  solaire Hybride max
    if type_toiture == "Inclinée bac acier ou autres":
       surface_solaire_hybride_max_hybride = 0
    else : 
        surface_solaire_thermique_max_hybride = surface_pv_toiture_max
    
  #  print(f"la surface solaire hybride max _ hybride _ est : {surface_solaire_thermique_max_hybride}")

##Puissance PV max_système hybride
    puissance_pv_max_hybride = surface_solaire_thermique_max_hybride * Hypotheses_puissance_PV_hybride /1000
   # print(f"la Puissance PV max_système hybride est : {puissance_pv_max_hybride} ")

#Productible PV_système hybride (kWh/kWc)
    productible_PV_hybride = productible_PV * Hypothese_rendement_PV
   # print(f"Productible PV_système hybride (kWh/kWc) est : {productible_PV_hybride} ")

##Production PV max_système hybride
    prod_PV_max_hybride = productible_PV_hybride * puissance_pv_max_hybride
   # print(f"Production PV max_système hybride : {prod_PV_max_hybride}")

#Productible Thermique_système hybride (kWh/m²)
    productible_thermique_hybride = productible_solaire_thermique * hypothese_rendement_st_hybride
   # print(f"Productible Thermique_système hybride (kWh/m²): {productible_thermique_hybride}")

#Production Thermique max_système hybride
    prod_thermique_max_hybride = surface_solaire_thermique_max_hybride * productible_thermique_hybride
   # print(f"Production Thermique max_système hybride: {prod_thermique_max_hybride}")
#Puissance PAC AES
    puissance_pac_aes = round(surface_solaire_thermique_max_hybride * hypothese_puissance_PAC_hybride)
   # print(f"la puissance PAC AES : {puissance_pac_aes}")

##Stockage ECS Solaire
    Stockage_ECS_Solaire_hybride = puissance_pac_aes * hypothese_stockage_ST_hybride
   # print(f"Stockage ECS Solaire : {Stockage_ECS_Solaire_hybride}")

##Besoins_ECS 
    besoins_ECS_hybride = rendement * total_ECS
   # print(f"besoin ECS du solaire thermique est : {besoins_ECS_hybride}")
# Surface Solaire Hybride calculée 
    surface_solaire_hybride_calcule = besoins_ECS_hybride *  hypothese_taux_couverture / productible_thermique_hybride 
   # print(f"surface solaire hybride calculée est : {surface_solaire_hybride_calcule}")

#Surface Solaire Hybride retenue  
    surface_solaire_hybride_retenue = min(surface_solaire_thermique_max_hybride , surface_solaire_hybride_calcule )
   # print(f"surface solaire thermique retenue : {surface_solaire_hybride_retenue}")

#Production EnR locale Solaire PV_système hybride
    prod_enr_locale_solaire_PV_hybride = Hypotheses_puissance_PV_hybride * surface_solaire_hybride_retenue * productible_PV_hybride /1000
   # print(f"Production EnR locale Solaire PV_système hybride : {prod_enr_locale_solaire_PV_hybride}")

#Production EnR locale Solaire Thermique_système hybride
    prod_enr_locale_solaire_thermique_hybride = surface_solaire_hybride_retenue * productible_thermique_hybride
   # print(f"Production EnR locale Solaire Thermique_système hybride : {prod_enr_locale_solaire_thermique_hybride}")

##Production EnR locale totale (existante + solaire thermique)
    Prod_enr_locale_totale_hybride = P_EnR_locale_solaire_existante + energie_PAC_delivre - conso_elec_PAC + Prod_enr_bois + prod_enr_locale_solaire_PV_hybride + prod_enr_locale_solaire_thermique_hybride
  #  print(f"Production EnR locale totale _ hybride __ (existante + solaire PV) : {Prod_enr_locale_totale_hybride}")

##Consommation élec PAC SOLAIRE + Appoint :
    conso_elec_pac_solaire_hybride = besoins_ECS_hybride * hypothese_taux_couverture / hypothese_COP_PAC_ST + (1 - hypothese_taux_couverture) * besoins_ECS_hybride
  #  print(f"Consommation élec PAC SOLAIRE + Appoint : {conso_elec_pac_solaire_hybride}")

##Consommation élec projetée pour l'hybrride
    conso_elec_proj_hybride = conso_elec * (1 - taux_baisse) - prod_enr_locale_solaire_PV_hybride + conso_elec_pac_solaire_hybride
    if E_T_principal == "Aucune":
        conso_elec_proj_hybride = conso_elec_proj_hybride - prod_enr_locale_solaire_thermique_hybride
    else:
        conso_elec_proj_hybride = conso_elec_proj_hybride
  #  print(f"La consommation elec projetée pour l'hybride est : {conso_elec_proj_hybride}")

##Consommation thermique principale projetée (combustible ou RCU)
    conso_thermique_principale_proj_hybride = conso_principal_1_convertie * (1- taux_baisse)

    if E_T_principal in ["Charbon" ,"Gaz naturel" , "Gaz butane/propane" , "Fioul" , "Bois plaquettes" , "Bois granulés" , "Réseau de chaleur"  ] :
        conso_thermique_principale_proj_hybride -= prod_enr_locale_solaire_thermique_hybride
        
  #  print(f"la consommation thermique principale projetée-hybride - de l'energie : {E_T_principal} est : {conso_thermique_principale_proj_hybride}")

##Consommation thermique appoint projetée (combustible ou RCU)
    conso_thermique_appoint_proj_hybride = conso_principal_2_convertie * (1 - taux_baisse)
  #  print(f"la consommation thermique d'appoint projetée-thermique : {conso_thermique_appoint_proj_hybride}")

##consommation totale projetée : 
    conso_totale_proj_hybride = conso_elec_proj_hybride + conso_thermique_principale_proj_hybride + conso_thermique_appoint_proj_hybride
    ratio_conso_totale_proj_hybride = conso_totale_proj_hybride / surface 
  #  print(f"la consommation totale projetée : {conso_totale_proj_hybride}")


##Taux ENR&R locale _ hybride _
    taux_ENR_Local_hybride = round((Prod_enr_locale_totale_hybride / (conso_totale_proj_hybride + energie_PAC_delivre)*100),2)
    taux_ENR_Local_hybride_scenario_max = taux_ENR_Local_hybride
 #   print(f"le taux ENR&R local hybride : {taux_ENR_Local_hybride } le max est {taux_ENR_Local_hybride_scenario_max} %")

##production enr RCU 
    ##on passe au calcul rcu : 
    conso_elec_rcu = conso_elec_proj_hybride
    conso_principal_rcu = conso_thermique_principale_proj_hybride

    # Calculs selon les types d'énergie
    enr_principale = conso_principal_rcu * taux_enr_principal if E_T_principal == "Réseau de chaleur" else 0
    enr_appoint = conso_thermique_appoint_proj_hybride * taux_enr_appoint if E_T_appoint == "Réseau de chaleur" else 0

    production_enr_rcu_hybride = enr_principale + enr_appoint
      
## Production enr mix electrique & gaz 
    production_enr_elec = conso_elec_rcu * Taux_EnR_mix_E_national_Elec

    enr_gaz_principal = (
        conso_principal_rcu * Taux_EnR_mix_E_national_Gaz
        if E_T_principal.strip().lower() == "gaz naturel"
        else 0 )

    enr_gaz_appoint = (
        conso_thermique_appoint_proj_hybride * Taux_EnR_mix_E_national_Gaz
        if E_T_appoint.strip().lower() == "gaz naturel"
        else 0)

    production_enr_mix_hybride = production_enr_elec + enr_gaz_principal + enr_gaz_appoint

##production ENR GLOBALE _hybride _
    prod_ENR_globale_hybride = production_enr_rcu_hybride + production_enr_mix_hybride + conso_elec_pac_solaire_hybride
 #   print (f"production enr Globale hybride  : {prod_ENR_globale_hybride}")

    ##Taux ENR&R globale hybride
    enr_globale_hybride =  round((prod_ENR_globale_hybride / (conso_totale_proj_hybride + energie_PAC_delivre) *100) , 2)
    enr_globale_hybride_scenario_max = enr_globale_hybride
#    print(f"le taux ENR&R global hybride est : {enr_globale_hybride} , le maximun global est {enr_globale_hybride_scenario_max}")

    #Impact carbone et cout energitique annuel 
    conso_hybride = [ conso_thermique_principale_proj_hybride , conso_thermique_appoint_proj_hybride  , conso_elec_proj_hybride]
  
    conso_carbone_hybride, cout_total_hybride = calcul_carbone_et_cout_sql(slugs_energie , conso_hybride ,reseau_principal , reseau_appoint )
    
    return surface_solaire_hybride_retenue , ratio_conso_totale_proj_hybride, taux_ENR_Local_hybride ,taux_ENR_Local_hybride_scenario_max, enr_globale_hybride , enr_globale_hybride_scenario_max   , conso_carbone_hybride, cout_total_hybride 



def faisabilite( type_toiture, situation, zone_administrative1):
   
    energie = "Solaire"

    # Chargement de la table SQL
    with engine.connect() as conn:
        R_faisabilite = pd.read_sql_query("SELECT * FROM dbo.régles_faisabilité", conn)

    # Mapping direct des valeurs
    mapping_valeurs = {
        "zone administrative": zone_administrative1.strip().lower(),
        "type de toiture": type_toiture.strip().lower(),
        "acoustique": situation.strip().lower() if situation else "inconnu" ,
        "contribution ilot de chaleur urbain": situation.strip().lower()
    }

    score_total = 0
    score_max = 0
    details_impacts = []

    for critere, valeur_utilisateur in mapping_valeurs.items():
        match_found = False

        for _, ligne in R_faisabilite.iterrows():
            impact = str(ligne["Impacts"]).strip().lower()
            caract = str(ligne.get("Caractéristiques", "")).strip().lower()
            note = ligne.get(energie.capitalize())
            ponderation = ligne.get("Pondération", 0)

            if pd.isna(note) or pd.isna(ponderation):
                continue

            if impact == critere and caract == valeur_utilisateur:
                note = int(note)
                ponderation = int(ponderation)
                score_pondere = note * ponderation
                score_total += score_pondere
                score_max += 5 * ponderation

                details_impacts.append({
                    impact,
                  
                     note
                    
                })

                print(f"🟩 Critère : {critere}")
                print(f"    ➤ Valeur saisie        : {valeur_utilisateur}")
                print(f"    ➤ Note trouvée         : {note}")
                print(f"    ➤ Pondération          : {ponderation}")
                print(f"    ➤ Score pondéré        : {score_pondere}")
                print("-" * 50)

                match_found = True
                break

        if not match_found:
            print(f"🟥 Aucune correspondance trouvée pour le critère : {critere} ({valeur_utilisateur})")
         #   print("-" * 50)
            
        if not match_found:
            print(f"⚠️ Aucun match pour le critère : {critere} = '{valeur_utilisateur}'")

    # Pourcentage et notation
    pourcentage = (score_total / score_max) * 100 if score_max else 0
    notation = round(score_total, 1)

    if notation >= 57:
        lettre = "A"
    elif notation >= 43:
        lettre = "B"
    elif notation >= 29:
        lettre = "C"
    elif notation >= 15:
        lettre = "D"
    else:
        lettre = "E"

   # print(f"\n✅ Résumé pour l’énergie : {energie}")
   # print(f"   ➤ Score total      : {notation}")
   # print(f"   ➤ Score maximum    : {score_max}")
   # print(f"   ➤ Pourcentage      : {round(pourcentage, 1)} %")
    print(f"   ➤ Lettre finale    : {lettre}")
    print(details_impacts)

    return lettre , details_impacts











 