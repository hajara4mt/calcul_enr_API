import pandas as pd 
from app.db.database import engine
import json


from app.moteur_calcul.hypotheses.conversion import conversion
from app.moteur_calcul.loader import load_data_co2_cout
from app.moteur_calcul.hypotheses.conso_clim import conso_clim
from  app.moteur_calcul.hypotheses.mapping import mapping 
from  app.moteur_calcul.hypotheses.cop_table import cop_table 
from  app.moteur_calcul.hypotheses.scop_annuel import scop_annuel 

from app.moteur_calcul.hypotheses.Hypothèse_Prod import ZONES
from app.moteur_calcul.hypotheses.COEF_PERTE_RENDEMENT import COEF_PERTE_RENDEMENT
from app.moteur_calcul.hypotheses.Hypothèse_Surface_PV import HYPOTHESE_SURFACE_PV
from app.moteur_calcul.hypotheses.Bdd_conso_carbone import Baisse_conso_besoins






Capacité_thermique_volumique_eau = 1.162
temperature_chaude = 60 
couverture_PAC_Chauffage = 0.6
couverture_PAC_ECS = 0.6
Taux_EnR_mix_E_national_Elec  = 26/100
Taux_EnR_mix_E_national_Gaz = 1.6 / 100


## conversion des valeurs des consommations recues :
def convertir_consommation(energie: str, conso_annuelle: float) -> float:
    couverture_PAC_Chauffage = 0.6
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
    print("Slugs énergie :", slugs_energie)
    print("Consommations :", consos)
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
        print("📦 Données chargées :", data)

        facteur_co2 = float(data["grammage_co2_kgco2_kwhef"])
        facteur_cout = float(data["cout_unitaire_euro_par_kwh"])
        print(f"🌍 Facteur CO2 : {facteur_co2} kgCO2/kWh")
        print(f"💶 Facteur Coût : {facteur_cout} €/kWh")

        impact = conso_i * facteur_co2
        cout = conso_i * facteur_cout
        print(f"📈 Consommation : {conso_i} kWh → Impact : {impact} kgCO2 | Coût : {cout} €")

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



def repartition_usages(slug_principal , slug_appoint , calcul_conso_chauffage , conso_elec , rendement_production ,Rendement_globale,  Consommation_ventilation , Conso_specifique, Conso_eclairage,Consommations_annuelles_totales_initiales, usage_thermique,zone_climatique , surface ,  typology ,besoins_ECS , temperature_retenue , type_prod_ecs , jours_ouvrés , rendement , E_T_principal , E_T_appoint , conso_principal_1_convertie , conso_principal_2_convertie , Energie_ECS , systeme_chauffage , zone , masque , surface_PV , prod_solaire_existante, pv_saisie , thermique_saisie , surface_thermique): 
    P_EnR_locale_solaire_existante  , productible_thermique , productible_PV = calcul_commun (zone , masque , surface_PV , prod_solaire_existante, pv_saisie , thermique_saisie , surface_thermique)
##conso_surfacique_clim
    if usage_thermique in ["chauffage + clim + ecs", "chauffage + clim"]:
        conso_surfacique_clim = conso_clim[typology][zone_climatique]
    elif usage_thermique in ["chauffage + ecs", "chauffage"]:
        conso_surfacique_clim = 0
    else:
        raise ValueError(f"Type d'usage thermique non reconnu : {usage_thermique}")
   # print (f"la conso climatique esr : {conso_surfacique_clim}")

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
   # print(f"on comence par le chauffage on voit la repartirion par usage /m : {calcul_conso_chauffage}")
    climatisation = conso_surfacique_clim
    ECS = conso_E_ECS
    autres_usages = Consommation_ventilation + Conso_eclairage + Conso_specifique 
   # print(f"on decortique la conso autre usage : {autres_usages} , ventillation : {Consommation_ventilation} , eclairage : {Conso_eclairage} , specifique : {Conso_specifique}")
    total = calcul_conso_chauffage + conso_surfacique_clim + conso_E_ECS + autres_usages
#Répartition par usage (kWh/)
    chauffage_kwh = chauffage * surface
    climatisation_kwh = climatisation * surface
    ECS_kwh = ECS * surface
    autres_usages_kwh = autres_usages * surface
    total_kwh = chauffage_kwh + climatisation_kwh + ECS_kwh + autres_usages_kwh 
   # print(f"on decortique le total qu'on a : chauffage : {chauffage_kwh} , climatisation : {climatisation_kwh} , ecs : {ECS_kwh} , autres_usages : {autres_usages_kwh}")
#Répartition par usage calcul conso (%)
    chauffage_kwh_P = chauffage_kwh / total_kwh
  #  print(f" {chauffage_kwh_P} viens de le chayffage en repartition est : {chauffage_kwh} , divisé par : {total_kwh} , la surface est : {surface} et le chauffage est : {chauffage} " )
    climatisation_kwh_P = climatisation_kwh /total_kwh
    ECS_kwh_P = ECS_kwh / total_kwh
    autres_usages_kwh_P = autres_usages_kwh / total_kwh
    total_P = chauffage_kwh_P + climatisation_kwh_P + ECS_kwh_P + autres_usages_kwh_P

    repartition_conso_hors_clim = ECS_kwh /(ECS_kwh + chauffage_kwh )

 
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
   
    #print(f"🔋 Valeur  ECS : {calibration_ET1_ECS} kWh")
##chuffage

    if systeme_chauffage in [ "Electrique" , "PAC" , "Géothermie" , "Inconnu"] or  E_T_principal in ["Réseau de froid" , "Aucune"] :
        calibration_ET1_chauffage = 0
    elif Energie_ECS == systeme_chauffage :
        calibration_ET1_chauffage = conso_principal_1_convertie - calibration_ET1_ECS
    else : 
        calibration_ET1_chauffage = conso_principal_1_convertie

    ##total energie thermique 1 :
    total_thermique1 = calibration_ET1_chauffage + calibration_ET1_ECS  + calibration_ET1_clim
   # print(f"total thermique 1  : {total_thermique1} , celle de clim est : {calibration_ET1_ECS}")


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
   # print(f"total thermique 2  : {total_thermique2} ec: {calibration_ET2_ECS}")

###elec
 
 ### chauffage 
    if (calibration_ET1_chauffage + calibration_ET2_chauffage ) == 0:
        calibration_elec_chauffage = Consommations_annuelles_totales_initiales * chauffage_kwh_P
       #calibration_elec_chauffage = Consommations_annuelles_totales_initiales 

    else :
        calibration_elec_chauffage = 0 

   # print(f"calibration chuffage_elec: {calibration_elec_chauffage} , et la conso annuelle est : {Consommations_annuelles_totales_initiales} , et le chauffage kwh pourcentage est : {chauffage_kwh_P}")   


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
    #print( "on detecte le probleme !")
    #print(f"le total ele chauffage dis moi: {calibration_elec_chauffage} ; conso_elec : {conso_elec}  ")


   # print(f"calibration_elec_autres_usages : {calibration_elec_autres_usages}")
## total Elec 
    total_elec = calibration_elec_chauffage + calibration_elec_clim  + calibration_elec_ECS + calibration_elec_autres_usages
   # print(f"le total de calibartion ele est : {total_elec}")

   # print(f"total thermique 2  : {total_elec}")

    #print ("les calibrations sont ")
   # print(calibration_elec_chauffage ,calibration_ET1_chauffage , calibration_ET2_chauffage )


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
        conso_elec_PAC_1 = total_chauffage * couverture_PAC_Chauffage * Rendement_globale / rendement_production
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
   # print(f"🌲 Production EnR&R locale consommée sur site  : {round(prod_enr_locale_site, 2)} kWhEF/an")  
    

##taux enr local initial : 
    if energie_PAC_delivre > 0:
            denominateur = conso_elec + total_chauffage * Rendement_globale 

    else:
            denominateur = Consommations_annuelles_totales_initiales

    if denominateur == 0:
            denominateur = 0

    taux = prod_enr_locale_site / denominateur 
    taux_enr_initial = taux * 100

    conso_energitiques = { 
    "elec": int(round(float(ratio_elec) * 100, 0)),
    slug_principal: int(round(float(ratio_ET1) * 100, 0)),
    slug_appoint: int(round(float(ratio_ET2) * 100, 0)),
    "total": int(round(float(total_ratio) * 100, 0))}

    
    usages_energitiques = { 
    "chauffage": int(round(float(ratio_chauffage) ,0)),
    "climatisation":int( round(float(ratio_climatisation) , 0)),
    "ecs": int(round(float(ratio_ecs) , 0)),
    "autre_usages": int(round(float(ratio_autres_usages) , 0)),
    "total": int(round(float(ratio_total_final) , 0))
    }


   # print(conso_surfacique_clim , total_ECS , besoin_60 , perte_bouclage )

   # print ("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")

   # print(conso_E_ECS , round(float(taux_enr_initial) * 100, 3) , Prod_enr_bois , conso_elec_PAC )


   # print ("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")

   # print(usages_energitiques)

    print ("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
   # print(f"total autre usages est : {total_autres_usages}")

   # print(conso_energitiques)
    return  calibration_ET1_ECS , calibration_ET1_clim , total_chauffage , total_thermique2 , conso_surfacique_clim , total_ECS , besoin_60 , perte_bouclage , conso_E_ECS , round(taux_enr_initial , 2) , Prod_enr_bois , conso_elec_PAC , usages_energitiques , conso_energitiques , energie_PAC_delivre


def calcul_Pv (Rendement_globale , slug_principal , slug_appoint ,type_toiture ,conso_elec , surface , slugs_energie,  strategie , E_T_principal , E_T_appoint , reseau_principal , reseau_appoint , taux_enr_principal , taux_enr_appoint , encombrement_toiture , conso_principal_1_convertie,conso_principal_2_convertie , surface_toiture , surface_parking , zone , masque ,systeme_chauffage , typologie ,  surface_PV , prod_solaire_existante, pv_saisie , thermique_saisie , surface_thermique , calcul_conso_chauffage , rendement_production , Consommation_ventilation , Conso_specifique, Conso_eclairage ,Consommations_annuelles_totales_initiales , Energie_ECS ,  rendement , jours_ouvrés ,besoins_ECS , temperature_retenue , type_prod_ecs , usage_thermique,zone_climatique  ,  typology  ) : 
    hypothese_puissance = 180
    taux_baisse = Baisse_conso_besoins.get(strategie, 0)  

    P_EnR_locale_solaire_existante  , productible_thermique , productible_PV = calcul_commun(zone , masque , surface_PV , prod_solaire_existante, pv_saisie , thermique_saisie , surface_thermique)
   # conso_surfacique_clim , besoin_60 , perte_bouclage , conso_E_ECS , taux_enr_initial , Prod_enr_bois , conso_elec_PAC , usages_energitiques , conso_energitiques , energie_PAC_delivre = 
    calibration_ET1_ECS , calibration_ET1_clim , total_chauffage , total_thermique2 ,  conso_surfacique_clim , total_ECS , besoin_60 , perte_bouclage , conso_E_ECS , taux_enr_initial , Prod_enr_bois , conso_elec_PAC , usages_energitiques , conso_energitiques , energie_PAC_delivre = repartition_usages(slug_principal , slug_appoint , calcul_conso_chauffage , conso_elec , rendement_production , Rendement_globale ,Consommation_ventilation , Conso_specifique, Conso_eclairage,Consommations_annuelles_totales_initiales, usage_thermique,zone_climatique , surface ,  typology ,besoins_ECS , temperature_retenue , type_prod_ecs , jours_ouvrés , rendement , E_T_principal , E_T_appoint , conso_principal_1_convertie , conso_principal_2_convertie , Energie_ECS , systeme_chauffage , zone , masque , surface_PV , prod_solaire_existante, pv_saisie , thermique_saisie , surface_thermique)
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
    total_cout_pv = total_cout_pv / surface
    total_impact_pv = total_impact_pv / surface
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


    return round(Puissance_pv_retenue , 0 ) ,round(ratio_conso_totale_projet_pv , 0) ,  enr_local_pv , enr_local_max_pv , enr_globale , enr_globale_scenario_max  ,  round( total_impact_pv,0) , round(total_cout_pv , 0) , conso_thermique_appoint_proj , surface_pv_toiture_max




def calcul_thermique (Rendement_globale , slug_principal , slug_appoint , type_toiture , rendement ,conso_elec , strategie , E_T_principal , E_T_appoint , surface , slugs_energie , taux_enr_principal , taux_enr_appoint , reseau_principal , reseau_appoint ,  conso_principal_1_convertie , conso_principal_2_convertie   , zone , masque , surface_PV , prod_solaire_existante, pv_saisie , thermique_saisie , surface_thermique , calcul_conso_chauffage, rendement_production , Consommation_ventilation , Conso_specifique, Conso_eclairage,Consommations_annuelles_totales_initiales, Energie_ECS , systeme_chauffage , encombrement_toiture ,usage_thermique,zone_climatique , surface_parking ,  surface_toiture , typology ,besoins_ECS , temperature_retenue , typologie ,  type_prod_ecs , jours_ouvrés  ) : 
    hypothese_rendement_st = 550
    hypothèses_volume_ST = 50 
    Hypothese_surface_LT_ST = 4
    hypothese_taux_couverture = 60 /100 
    taux_baisse = Baisse_conso_besoins.get(strategie, 0)  

    calibration_ET1_ECS , calibration_ET1_clim , total_chauffage , total_thermique2 , conso_surfacique_clim , total_ECS , besoin_60 , perte_bouclage , conso_E_ECS , taux_enr_initial , Prod_enr_bois , conso_elec_PAC , usages_energitiques , conso_energitiques , energie_PAC_delivre = repartition_usages(slug_principal , slug_appoint , calcul_conso_chauffage , conso_elec , rendement_production , Rendement_globale, Consommation_ventilation , Conso_specifique, Conso_eclairage,Consommations_annuelles_totales_initiales, usage_thermique,zone_climatique , surface ,  typology ,besoins_ECS , temperature_retenue , type_prod_ecs , jours_ouvrés , rendement , E_T_principal , E_T_appoint , conso_principal_1_convertie , conso_principal_2_convertie , Energie_ECS , systeme_chauffage , zone , masque , surface_PV , prod_solaire_existante, pv_saisie , thermique_saisie , surface_thermique)

    P_EnR_locale_solaire_existante  , productible_solaire_thermique , productible_PV  = calcul_commun(zone , masque , surface_PV , prod_solaire_existante, pv_saisie , thermique_saisie , surface_thermique)
    Puissance_pv_retenue  ,ratio_conso_totale_projet_pv ,  enr_local_pv , enr_local_max_pv , enr_globale , enr_globale_scenario_max  ,   total_impact_pv, total_cout_pv , conso_thermique_appoint_proj , surface_pv_toiture_max =  calcul_Pv (Rendement_globale , slug_principal , slug_appoint ,type_toiture ,conso_elec , surface , slugs_energie,  strategie , E_T_principal , E_T_appoint , reseau_principal , reseau_appoint , taux_enr_principal , taux_enr_appoint , encombrement_toiture , conso_principal_1_convertie,conso_principal_2_convertie , surface_toiture , surface_parking , zone , masque ,systeme_chauffage , typologie ,  surface_PV , prod_solaire_existante, pv_saisie , thermique_saisie , surface_thermique , calcul_conso_chauffage , rendement_production , Consommation_ventilation , Conso_specifique, Conso_eclairage ,Consommations_annuelles_totales_initiales , Energie_ECS ,  rendement , jours_ouvrés ,besoins_ECS , temperature_retenue , type_prod_ecs , usage_thermique,zone_climatique  ,  typology  ) 


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
    total_impact_thermique = (total_impact_thermique / surface)
    total_cout_thermique = (  total_cout_thermique / surface)
    return  int(surface_solaire_thermique_retenue) ,  int(ratio_conso_totale_proj_thermique) , round(taux_ENR_Local_thermique, 2) , round(taux_ENR_Local_thermique_max,2) , round(enr_globale_thermique , 2)  , round(enr_globale_thermique_scenario_max ,2) ,   round(total_impact_thermique,2) ,    round(total_cout_thermique, 2)

####""----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------#######

def calcul_hybride(Rendement_globale , slug_principal , slug_appoint ,type_toiture , rendement  , conso_elec , slugs_energie , strategie , E_T_principal , E_T_appoint ,  surface , taux_enr_principal , reseau_principal , reseau_appoint , taux_enr_appoint ,  conso_principal_1_convertie , conso_principal_2_convertie , calcul_conso_chauffage ,zone , masque , surface_PV , prod_solaire_existante, pv_saisie , thermique_saisie , surface_thermique ,  rendement_production , Consommation_ventilation , Conso_specifique, Conso_eclairage,Consommations_annuelles_totales_initiales, typology ,besoins_ECS , encombrement_toiture, temperature_retenue , type_prod_ecs , jours_ouvrés ,  usage_thermique,zone_climatique , surface_toiture , surface_parking , typologie, Energie_ECS , systeme_chauffage ) :
    #P_EnR_locale_solaire_existante  , productible_solaire_thermique , productible_PV = calcul_commun
    P_EnR_locale_solaire_existante  , productible_solaire_thermique , productible_PV  = calcul_commun(zone , masque , surface_PV , prod_solaire_existante, pv_saisie , thermique_saisie , surface_thermique)

    calibration_ET1_ECS , calibration_ET1_clim ,  total_chauffage , total_thermique2 ,  conso_surfacique_clim , total_ECS , besoin_60 , perte_bouclage , conso_E_ECS , taux_enr_initial , Prod_enr_bois , conso_elec_PAC , usages_energitiques , conso_energitiques , energie_PAC_delivre = repartition_usages(slug_principal , slug_appoint ,calcul_conso_chauffage , conso_elec , rendement_production ,Rendement_globale, Consommation_ventilation , Conso_specifique, Conso_eclairage,Consommations_annuelles_totales_initiales, usage_thermique,zone_climatique , surface ,  typology ,besoins_ECS , temperature_retenue , type_prod_ecs , jours_ouvrés , rendement , E_T_principal , E_T_appoint , conso_principal_1_convertie , conso_principal_2_convertie , Energie_ECS , systeme_chauffage , zone , masque , surface_PV , prod_solaire_existante, pv_saisie , thermique_saisie , surface_thermique)

    taux_baisse = Baisse_conso_besoins.get(strategie, 0)  


    Puissance_pv_retenue  ,ratio_conso_totale_projet_pv ,  enr_local_pv , enr_local_max_pv , enr_globale , enr_globale_scenario_max  ,   total_impact_pv, total_cout_pv , conso_thermique_appoint_proj , surface_pv_toiture_max =  calcul_Pv (Rendement_globale , slug_principal , slug_appoint , type_toiture ,conso_elec , surface , slugs_energie,  strategie , E_T_principal , E_T_appoint , reseau_principal , reseau_appoint , taux_enr_principal , taux_enr_appoint , encombrement_toiture , conso_principal_1_convertie,conso_principal_2_convertie , surface_toiture , surface_parking , zone , masque ,systeme_chauffage , typologie ,  surface_PV , prod_solaire_existante, pv_saisie , thermique_saisie , surface_thermique , calcul_conso_chauffage , rendement_production , Consommation_ventilation , Conso_specifique, Conso_eclairage ,Consommations_annuelles_totales_initiales , Energie_ECS ,  rendement , jours_ouvrés ,besoins_ECS , temperature_retenue , type_prod_ecs , usage_thermique,zone_climatique  ,  typology  ) 


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
    conso_carbone_hybride = (conso_carbone_hybride / surface)
    cout_total_hybride = (cout_total_hybride / surface)
    return round(surface_solaire_hybride_retenue,1) , round(ratio_conso_totale_proj_hybride,1), round(taux_ENR_Local_hybride,2) ,round(taux_ENR_Local_hybride_scenario_max,2) , round(enr_globale_hybride,2) , round(enr_globale_hybride_scenario_max ,2)  , round(conso_carbone_hybride,1) , round(  cout_total_hybride ,1)



def faisabilite(type_toiture, situation, zone_administrative1):
    energie = "Solaire"

    # Chargement de la table SQL
    with engine.connect() as conn:
        R_faisabilite = pd.read_sql_query("SELECT * FROM dbo.régles_faisabilité", conn)

    # Mapping direct des valeurs utilisateur
    mapping_valeurs = {
        "zone administrative": zone_administrative1.strip().lower(),
        "type de toiture": type_toiture.strip().lower(),
        "acoustique": situation.strip().lower() if situation else "inconnu",
        "contribution ilot de chaleur urbain": situation.strip().lower()
    }

    # Correspondance pour adapter les clés de sortie
    remap_keys = {
        "zone administrative": "zone_administrative",
        "type de toiture": "type_toiture",
        "acoustique": "acoustique",
        "contribution ilot de chaleur urbain": "cicu"
    }

    score_total = 0
    score_max = 0
    details_impacts = {}

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

                # Utilisation des noms renommés
                clean_key = remap_keys.get(impact, impact)
                details_impacts[clean_key] = note

              #  print(f"🟩 Critère : {critere}")
              #  print(f"    ➤ Valeur saisie        : {valeur_utilisateur}")
              #  print(f"    ➤ Note trouvée         : {note}")
              #  print(f"    ➤ Pondération          : {ponderation}")
              #  print(f"    ➤ Score pondéré        : {score_pondere}")
              #  print("-" * 50)

                match_found = True
                break

        if not match_found:
            print(f"⚠️ Aucun match pour le critère : {critere} = '{valeur_utilisateur}'")

    # Calcul final
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

   # print(f"   ➤ Lettre finale    : {lettre}")
   # print(details_impacts)

    return lettre.strip(), json.dumps(details_impacts)



## Calcul Géothermie : 
def calcul_geothermie (deperdition_max , strategie , slug_strategie ,slugs_energie , reseau_principal , reseau_appoint , taux_enr_principal ,taux_enr_appoint ,  slug_temperature_emetteurs , usage_thermique ,  surface_hors_emprise , Rendement_globale ,surface_parcelle , E_T_principal  , zone , masque , surface_PV , prod_solaire_existante, pv_saisie , thermique_saisie , surface_thermique , slug_principal , slug_appoint ,calcul_conso_chauffage , conso_elec , rendement_production , Consommation_ventilation , Conso_specifique, Conso_eclairage,Consommations_annuelles_totales_initiales , zone_climatique , surface ,  typology ,besoins_ECS , temperature_retenue , type_prod_ecs , jours_ouvrés , rendement ,  E_T_appoint , conso_principal_1_convertie , conso_principal_2_convertie , Energie_ECS , systeme_chauffage  ) : 
    calibration_ET1_ECS , calibration_ET1_clim , total_chauffage , total_thermique2,  conso_surfacique_clim , total_ECS , besoin_60 , perte_bouclage , conso_E_ECS , taux_enr_initial , Prod_enr_bois , conso_elec_PAC , usages_energitiques , conso_energitiques , energie_PAC_delivre = repartition_usages(slug_principal , slug_appoint ,calcul_conso_chauffage , conso_elec , rendement_production , Rendement_globale, Consommation_ventilation , Conso_specifique, Conso_eclairage,Consommations_annuelles_totales_initiales, usage_thermique,zone_climatique , surface ,  typology ,besoins_ECS , temperature_retenue , type_prod_ecs , jours_ouvrés , rendement , E_T_principal , E_T_appoint , conso_principal_1_convertie , conso_principal_2_convertie , Energie_ECS , systeme_chauffage , zone , masque , surface_PV , prod_solaire_existante, pv_saisie , thermique_saisie , surface_thermique)
    P_EnR_locale_solaire_existante  , productible_solaire_thermique , productible_PV  = calcul_commun(zone , masque , surface_PV , prod_solaire_existante, pv_saisie , thermique_saisie , surface_thermique)

    besoin_chaud = deperdition_max
    taux_baisse = Baisse_conso_besoins.get(strategie, 0)  

    ##print(f"le besoin chaud est : {besoin_chaud}")

    besoin_froid  = 1
    with engine.connect() as conn:
       df_charges = pd.read_sql_query("SELECT * FROM dbo.TableCouverture", conn)

 #COP Nominal 
    if slug_strategie == "ra" and slug_temperature_emetteurs == "ht" : 
        cop_nominal =  cop_table["bt"][usage_thermique]
    else : 
        cop_nominal = cop_table[slug_temperature_emetteurs][usage_thermique]
    
    #print(f"la valeur de cop nominal est : {cop_nominal}")

 #SCOP annuel PAC 
    if slug_strategie == "ra" and slug_temperature_emetteurs == "ht" :
        scop_annuel_pac = scop_annuel["bt"][usage_thermique]
    else : 
        scop_annuel_pac = scop_annuel[slug_temperature_emetteurs][usage_thermique]
    
    #print(f"la valeur de scop annuel PAC est : {scop_annuel_pac}")
  # Rapport Chaudfroid 
    chaud_froid = besoin_chaud / (besoin_froid/(cop_nominal-1)*(cop_nominal))

    #print(f"la valeur du  Rapport chaud/froid est : {chaud_froid}")
#surface max sgv 
    if slug_strategie == "bn" :
       surface_max_sgv = surface_parcelle * 0.5
    else : 
        surface_max_sgv = surface_hors_emprise
    
    #print(f"la surface max SGV est : {surface_max_sgv}")
    
#nb de sonde 
    nb_sondes = surface_max_sgv * 0.03
   # print(f" le nombre de sonde est : {nb_sondes}")
##Puissance Sous Sol max
    puissance_sous_sol_max = nb_sondes * 100 * 50 / 1000
    #print(f"la puissance sous sol max est : {puissance_sous_sol_max}")
##Puissance PAC calo max (chaud)
    puissance_pac_chaud = puissance_sous_sol_max / (cop_nominal-1) * cop_nominal
    #print(f"la puissance PAC calo Max -chaud- est : {puissance_pac_chaud}")
##puissance PAC COLO Max frigo 
    puissance_pac_frigo = puissance_sous_sol_max / (cop_nominal) * (cop_nominal -1) 
    #print(f"la puissance PAC calo Max -frigo- est : {puissance_pac_frigo}")


#Puissance PAC chaud retenue  
    if slug_strategie == "bn" or E_T_principal == "aucune" : 
        if chaud_froid > 1 : 
            puissance_pac_chaud_retenue = min (chaud_froid , puissance_pac_chaud)
        else : 
            valeur1 = puissance_pac_frigo / (cop_nominal - 1) * cop_nominal
            valeur2 = besoin_froid / (cop_nominal - 1) * cop_nominal
            puissance_pac_chaud_retenue =  min(valeur1, valeur2)
    elif(  chaud_froid > (1/0.5)):
        puissance_pac_chaud_retenue = min((besoin_chaud*0.5), puissance_pac_chaud)
    else:
        puissance_pac_chaud_retenue = min((puissance_pac_frigo /(cop_nominal-1)*cop_nominal) , (besoin_froid/ (cop_nominal-1) *cop_nominal))

    puissance_pac_chaud_retenue_scenario_max = puissance_pac_chaud

    #print(f"la puissance PAC chaud retenue est : {puissance_pac_chaud_retenue}")

## % besoin chaud 
    besoin_chaud_pourcentage = round(((puissance_pac_chaud  / besoin_chaud)*100),2)
    besoin_chaud_pourcentage_scenario_max = round(((puissance_pac_chaud_retenue_scenario_max  / besoin_chaud)*100),2)
    #print(f"le % besoin chaud est : {besoin_chaud_pourcentage}")

#puissance pac froid correspondante 
    puissance_pac_froid_correspondante = puissance_pac_chaud_retenue / cop_nominal * (cop_nominal-1)
    puissance_pac_froid_correspondante_scenario_max = puissance_pac_chaud_retenue_scenario_max / cop_nominal * (cop_nominal-1)
    #print(f"la puissance pac froid correspondante : {puissance_pac_froid_correspondante}")
#Nb de sondes retenu
    nbre_sonde_retenue = puissance_pac_froid_correspondante * 1000 / (50*100)
    nbre_sonde_retenue_scenario_max = puissance_pac_froid_correspondante_scenario_max* 1000 / (50*100)
    #print(f"le nombre de sonde retenue est : {nbre_sonde_retenue}")
#Surface max SGV scénario optimisé 
    surface_max_sgv_optimise = nbre_sonde_retenue / 0.03
    surface_max_sgv_maximum= nbre_sonde_retenue_scenario_max/ 0.03
    #print(f"la surface max SGv est : {surface_max_sgv_optimise}")
#Surface local technique nécessaire
    surface_locale_te = max(50 , (puissance_pac_chaud_retenue* 0.150 ))  
    #print(f"surface locale technique nécessaire est : {surface_locale_te}")  
#taux couverture _optimisé : 
## On va arrondir au plus proche possible ( le plus grand proche ) 
# On arrondit au multiple de 5 le plus proche

    palier = round(besoin_chaud_pourcentage / 5) * 5
    palier = max(0, min(100, palier))  
    # Filtrage de la ligne correspondante
    ligne = df_charges[df_charges["PuissancePct"] == palier]
    
    if ligne.empty:
        raise ValueError(f"Aucune ligne trouvée pour {palier}% de puissance")

    if typology not in df_charges.columns:
        raise ValueError(f"Typologie inconnue : {typology}")

    taux_couverture =  int(ligne[typology].values[0])
    #print(f"le Taux couverture des besoins chaud par la PAC est : {taux_couverture}")
   # print(f"le total de conso chauffage utilisé est : {total_chauffage}")
    #print(f"le taux baisse est : {taux_baisse}")
    #print(f"le rendement globale est : {Rendement_globale}")

#taux couverture _scenario_maximum :
    palier_max = round(besoin_chaud_pourcentage_scenario_max / 5) * 5
    palier_max = max(0, min(100, palier_max))  
    # Filtrage de la ligne correspondante
    ligne = df_charges[df_charges["PuissancePct"] == palier_max]
    
    if ligne.empty:
        raise ValueError(f"Aucune ligne trouvée pour {palier_max}% de puissance")

    if typology not in df_charges.columns:
        raise ValueError(f"Typologie inconnue : {typology}")

    taux_couverture_scenario_max =  int(ligne[typology].values[0])
    #print(f"le Taux couverture des besoins chaud par la PAC en scenario max est : {taux_couverture_scenario_max}")


##besoins thermiques 
    besoins_thermiques = total_chauffage * (1-taux_baisse)* Rendement_globale
    #print(f"les nesoins thermiques sont : {besoins_thermiques}")
#besoins_chaud_couverts par la géothermie
    besoins_chauds_geothermie = besoins_thermiques * (taux_couverture/100)
    besoins_chauds_geothermie_max = besoins_thermiques * (taux_couverture_scenario_max/100)

    #print(f"Besoins chauds couverts par la Géothermie (sortie PAC) : {besoins_chauds_geothermie}")
#besoins chauds couverts par l'appoint 
    besoins_chauds_appoint = besoins_thermiques - besoins_chauds_geothermie
    besoins_chauds_appoint_scenario_max = besoins_thermiques - besoins_chauds_geothermie_max

    #print(f"les besoins chauds couverts par l'appint sont : {besoins_chauds_appoint}")
# Consommations élec PAC géothermique
    conso_ele_pac_geothermie =  besoins_chauds_geothermie / scop_annuel_pac
    conso_ele_pac_geothermie_scenario_max =  besoins_chauds_geothermie_max / scop_annuel_pac

    #print(f"Consommations élec PAC géothermique : {conso_ele_pac_geothermie}")
#part enr geothermie 
    part_enr_geo = besoins_chauds_geothermie - conso_ele_pac_geothermie
    part_enr_geo_max = besoins_chauds_geothermie_max - conso_ele_pac_geothermie_scenario_max
    #print(f"production ENR locale solaire existante : {P_EnR_locale_solaire_existante}")
# production enr locale totale 
    Prod_enr_locale_totale_geothermie =  part_enr_geo +P_EnR_locale_solaire_existante + energie_PAC_delivre - conso_elec_PAC + Prod_enr_bois
    Prod_enr_locale_totale_geothermie_scenario_max =  part_enr_geo_max +P_EnR_locale_solaire_existante + energie_PAC_delivre - conso_elec_PAC + Prod_enr_bois

    #print(f"production enr locale totale : {Prod_enr_locale_totale_geothermie}")
# conso elec totale projetée 
    conso_elec_proj_geothermie = conso_elec * (1- taux_baisse) + conso_ele_pac_geothermie
    conso_elec_proj_geothermie_max = conso_elec * (1- taux_baisse) + conso_ele_pac_geothermie_scenario_max

    if E_T_principal == "Aucune":
        conso_elec_proj_geothermie = conso_elec_proj_geothermie - ((besoins_chauds_geothermie + besoins_chauds_appoint )/Rendement_globale)
        conso_elec_proj_geothermie_max = conso_elec_proj_geothermie_max - ((besoins_chauds_geothermie_max + besoins_chauds_appoint_scenario_max )/Rendement_globale)

    else:
        conso_elec_proj_geothermie = conso_elec_proj_geothermie
        conso_elec_proj_geothermie_max = conso_elec_proj_geothermie_max

   # print(f"La consommation elec projetée pour la geothermie est : {conso_elec_proj_geothermie}")
##Consommation thermique principale projetée (combustible ou RCU)

    if E_T_principal == "Aucune" :
        conso_thermique_principale_proj_geothermie = 0 
        conso_thermique_principale_proj_geothermie_max=0
    elif E_T_principal == "Réseau de froid" :
        conso_thermique_principale_proj_geothermie =  calibration_ET1_clim
        conso_thermique_principale_proj_geothermie_max = calibration_ET1_clim
    else : 
        conso_thermique_principale_proj_geothermie = besoins_chauds_appoint / Rendement_globale + calibration_ET1_ECS
        conso_thermique_principale_proj_geothermie_max = besoins_chauds_appoint_scenario_max / Rendement_globale + calibration_ET1_ECS

   # print(f"Consommation thermique principale projetée : {conso_thermique_principale_proj_geothermie}")

#consommation thermique appoint projetée 
   # conso_thermique_appoint_proj_geothermie = conso_principal_2_convertie * (1 - taux_baisse) * Rendement_globale
    conso_thermique_appoint_proj_geothermie = conso_principal_2_convertie * (1 - taux_baisse) 

  #  print(f"conso_principal_2_convertie est : {conso_principal_2_convertie}")
   # print(f"consommation thermique appoint projetée est : {conso_thermique_appoint_proj_geothermie}")
## conso_totale_projetée

    conso_totale_proj_geothermie = conso_elec_proj_geothermie + conso_thermique_principale_proj_geothermie + conso_thermique_appoint_proj_geothermie
    ratio_conso_totale_proj_geothermie = conso_totale_proj_geothermie  / surface 
    conso_totale_proj_geothermie_scenario_max = conso_elec_proj_geothermie_max + conso_thermique_principale_proj_geothermie_max + conso_thermique_appoint_proj_geothermie

 #   print(f"consommation totale projetée : {conso_totale_proj_geothermie}")
##Taux enr locale geothermie 
    enr_local_geothermie = round(((Prod_enr_locale_totale_geothermie /( besoins_thermiques +conso_elec_proj_geothermie ))*100),2)
    enr_local_geothermie_scenario_max = round(((Prod_enr_locale_totale_geothermie_scenario_max /( besoins_thermiques +conso_elec_proj_geothermie ))*100),2)
  #  print(f"enr local : {enr_local_geothermie}")
##Production EnR RCU
    part_reseau1 = taux_enr_principal * conso_thermique_principale_proj_geothermie if E_T_principal == "Réseau de chaleur" else 0
    part_reseau1_max = taux_enr_principal * conso_thermique_principale_proj_geothermie_max if E_T_principal == "Réseau de chaleur" else 0


    part_reseau2 = taux_enr_appoint * conso_thermique_appoint_proj_geothermie if E_T_appoint ==  "Réseau de chaleur" else 0

    prod_enr_rcu_geothermie = round(((part_reseau1 + part_reseau2)*100),0)
    prod_enr_rcu_geothermie_max = round(((part_reseau1_max + part_reseau2)*100),0)


 #   print(f"Production EnR RCU : {prod_enr_rcu_geothermie}")

##Production EnR mix élec et gaz
    prod_enr_mix_geothermie =  conso_elec_proj_geothermie * Taux_EnR_mix_E_national_Elec
    prod_enr_mix_geothermie_max = conso_elec_proj_geothermie_max * Taux_EnR_mix_E_national_Elec

    if E_T_principal == "Gaz naturel":
      prod_enr_mix_geothermie += conso_thermique_principale_proj_geothermie * Taux_EnR_mix_E_national_Gaz
      prod_enr_mix_geothermie_max += conso_thermique_principale_proj_geothermie_max * Taux_EnR_mix_E_national_Gaz

    if E_T_appoint == "Gaz naturel":
      prod_enr_mix_geothermie += conso_thermique_appoint_proj_geothermie * Taux_EnR_mix_E_national_Gaz
      prod_enr_mix_geothermie_max += conso_thermique_appoint_proj_geothermie * Taux_EnR_mix_E_national_Gaz

    
  #  print(f"Production EnR mix élec et gaz : {prod_enr_mix_geothermie}")

##production enr globale geothermie 
    prod_enr_globale_geothermie = ( Prod_enr_locale_totale_geothermie + prod_enr_rcu_geothermie + prod_enr_mix_geothermie)
    prod_enr_globale_geothermie_scenario_max = ( Prod_enr_locale_totale_geothermie_scenario_max + prod_enr_rcu_geothermie + prod_enr_mix_geothermie_max)

 #   print(f"production enr&r globale : {prod_enr_globale_geothermie}")
##Taux enR&R global 
    enr_globale_geothermie = round((  (prod_enr_globale_geothermie / (besoins_thermiques+ conso_elec_proj_geothermie))*100),2)
    enr_globale_geothermie_scenario_max = round((  (prod_enr_globale_geothermie_scenario_max / (besoins_thermiques+ conso_elec_proj_geothermie_max))*100),2)

 #   print(f"le taux enr&r global est : {enr_globale_geothermie}")
##cout et impact carbone 
    conso_thermique = [ conso_thermique_principale_proj_geothermie , conso_thermique_appoint_proj_geothermie  , conso_elec_proj_geothermie]
    conso_thermique_scenario_max = [ conso_thermique_principale_proj_geothermie_max , conso_thermique_appoint_proj_geothermie  , conso_elec_proj_geothermie_max]

    total_impact_geothermie, total_cout_geothermie = calcul_carbone_et_cout_sql(slugs_energie , conso_thermique ,reseau_principal , reseau_appoint )
    total_impact_geothermie_max, total_cout_geothermie_max = calcul_carbone_et_cout_sql(slugs_energie , conso_thermique_scenario_max ,reseau_principal , reseau_appoint )

    total_impact_geothermie = (total_impact_geothermie / surface)
    total_cout_geothermie = (  total_cout_geothermie / surface)
 #   print(f"les couts sont : {total_cout_geothermie*surface} et les impacts sont : {total_impact_geothermie*surface}")

    return round(puissance_pac_chaud_retenue,1) ,round(ratio_conso_totale_proj_geothermie,1)  , enr_local_geothermie , enr_local_geothermie_scenario_max ,  enr_globale_geothermie , enr_globale_geothermie_scenario_max , round(total_impact_geothermie,1) , round(total_cout_geothermie,1)







    

 


def calcul_faisabilite_geothermie(zone_gmi , situation , slug_temperature_emetteurs , slug_strategie  , slug_usage , prod_ch_f  ):

    total_note = 0
    lettre_forcee = None 
    details_impacts = {}


    TABLE_FAISABILITE = "dbo.régles_faisabilité" 
    print(f"la strategie est : {slug_strategie}")

    inputs = {
        "zone_gmi": zone_gmi.lower(), # rouge 
        "situation": situation.lower() , # urbain 
        "regime_temperature_emetteurs": slug_temperature_emetteurs, ## slugs 
        "strategie": slug_strategie, ## slugs 
        "usage_thermique": slug_usage , ## slugs 
        "type_production": prod_ch_f
                

    }
    # Correspondance pour adapter les clés de sortie
    remap_keys = {
        "cartographie nationale géothermie (gmi)": "carto_gmi",
        "contribution ilot de chaleur urbain": "cicu",
        "acoustique": "acoustique",
        "installation existante émetteur _ régime de température": "installation_emetteur",
        "installation existante production": "installation_production"
    }




    print(f"la production chaud et froid : {prod_ch_f}")
    # Mappings pour les critères
    STRATEGIES_SANS_RENO = ["be", "bn", "rl"]
    USAGES_SANS_CLIM = ["ch", "ch_ecs"]
    
    usage_clim = "Sans clim" if inputs["usage_thermique"] in USAGES_SANS_CLIM else "Avec Clim"
    strategie_humaine = "Sans réno ou réno légère" if inputs["strategie"] in STRATEGIES_SANS_RENO else "Réno lourde"

    # Cas particulier 1 : zone GMI rouge → classe E directe
    if inputs["zone_gmi"] == "rouge":
        print("⚠️ Cas particulier : Zone GMI rouge → faisabilité forcée à E")
        lettre_forcee = "E" 
        

    # Cas particulier 2 : stratégie ≠ réno lourde et prod = individuelle
    if strategie_humaine != "Réno lourde" and inputs["type_production"] == "production individuelle":
        print("⚠️ Cas particulier : stratégie ≠ réno lourde + production individuelle → faisabilité forcée à E")
        lettre_forcee="E"
        
    

    # Récupérer la table complète
    with engine.connect() as conn:
        df = pd.read_sql(f"SELECT * FROM {TABLE_FAISABILITE}", conn)

    df_geo = df[df["Géothermie"].notnull()] ## filtrer sur la colonne geothermie qu'on veut 

    critères = [
        # zone_gmi => Cartographie nationale géothermie
        {
            "Impacts": "Cartographie nationale géothermie (GMI)",
            "Caractéristiques": inputs["zone_gmi"].lower()
        },
        # situation => Contribution ilot de chaleur
        {
            "Impacts": "Contribution ilot de chaleur urbain",
            "Caractéristiques": inputs["situation"]
        },
        # situation => Acoustique
        {
            "Impacts": "Acoustique",
            "Caractéristiques": inputs["situation"]
        },
        # régime température + usage_clim => Installation existante émetteur
        {
            "Impacts": "Installation existante émetteur _ Régime de température",
            "Caractéristiques": inputs["regime_temperature_emetteurs"].lower(),
            "Usage_climatisation": usage_clim,
            "Stratégie_de_rénovation": strategie_humaine
        },
        # type_production => Installation existante production
        {
            "Impacts": "Installation existante production",
            "Caractéristiques": inputs["type_production"].lower(),
            "Usage_climatisation": usage_clim,
            "Stratégie_de_rénovation": strategie_humaine
        }
    ]


    for crit in critères:
        filtres = (df_geo["Impacts"].str.lower() == crit["Impacts"].lower()) & (df_geo["Caractéristiques"].str.lower() == crit["Caractéristiques"].lower())

        if "Usage_climatisation" in crit:
            filtres &= (df_geo["Usage_climatisation"].str.lower() == crit["Usage_climatisation"].lower())
        if "Stratégie_de_rénovation" in crit:
            filtres &=(
                (df_geo["Stratégie_de_rénovation"].isna()) |
                (df_geo["Stratégie_de_rénovation"].str.lower() == crit["Stratégie_de_rénovation"].lower())
            
            ) 
            
            
        ligne = df_geo[filtres]

        if ligne.empty:
            print(f"[WARN] Ligne manquante pour critère {crit}")
            continue

        note = ligne["Géothermie"].values[0]
        ponderation = ligne["Pondération"].values[0]
        if pd.isna(ponderation):
            print(f"[WARN] Pondération manquante pour critère : {crit} → ignoré")
            continue

        total_note += note * ponderation
         # Utilisation des noms renommés
        impact = crit["Impacts"].lower()
        clean_key = remap_keys.get(impact, impact)
        details_impacts[clean_key] = note

        

        print(f"🟩 Critère : {crit}")
        details_impacts_geothermie = {
       remap_keys.get(k.lower(), k.lower()): int(round(float(v)))
       for k, v in details_impacts.items() }
        #print(f"    ➤ Valeur saisie        : {valeur_utilisateur}")
       #print(f"    ➤ Note trouvée         : {note}")
        #print(f"    ➤ Pondération          : {ponderation}")
        #print(f"    ➤ Score pondéré        : {total_note}")



    # Attribution de lettre selon barème
    if total_note >= 49:
        lettre = "A"
    elif total_note >= 37:
        lettre = "B"
    elif total_note >= 25:
        lettre = "C"
    elif total_note >= 13:
        lettre =  "D"
    else:
        lettre = "E"

     # --- Lettre finale: forcée si défini, sinon barème ---
    final_letter = lettre_forcee or lettre

    print(f"le details impacts est : {json.dumps(details_impacts_geothermie)} , lettre choisie est : {final_letter}" )

    return final_letter , json.dumps(details_impacts_geothermie, ensure_ascii=False)




def calcul_biomase(deperdition_max , slug_strategie , strategie , typology, slugs_energie , reseau_principal , reseau_appoint  ,Rendement_globale , slug_principal , taux_enr_principal ,taux_enr_appoint , slug_appoint ,calcul_conso_chauffage , conso_elec , rendement_production , Consommation_ventilation , Conso_specifique, Conso_eclairage,Consommations_annuelles_totales_initiales,  usage_thermique,zone_climatique , surface  ,besoins_ECS , temperature_retenue , type_prod_ecs , jours_ouvrés , rendement , E_T_principal , E_T_appoint , conso_principal_1_convertie , conso_principal_2_convertie , Energie_ECS , systeme_chauffage , zone , masque , surface_PV , prod_solaire_existante, pv_saisie , thermique_saisie , surface_thermique ):
    calibration_ET1_ECS , calibration_ET1_clim , total_chauffage , total_thermique2 ,  conso_surfacique_clim , total_ECS , besoin_60 , perte_bouclage , conso_E_ECS , taux_enr_initial , Prod_enr_bois , conso_elec_PAC , usages_energitiques , conso_energitiques , energie_PAC_delivre = repartition_usages(slug_principal , slug_appoint ,calcul_conso_chauffage , conso_elec , rendement_production , Rendement_globale, Consommation_ventilation , Conso_specifique, Conso_eclairage,Consommations_annuelles_totales_initiales, usage_thermique,zone_climatique , surface ,  typology ,besoins_ECS , temperature_retenue , type_prod_ecs , jours_ouvrés , rendement , E_T_principal , E_T_appoint , conso_principal_1_convertie , conso_principal_2_convertie , Energie_ECS , systeme_chauffage , zone , masque , surface_PV , prod_solaire_existante, pv_saisie , thermique_saisie , surface_thermique)
    P_EnR_locale_solaire_existante  , productible_solaire_thermique , productible_PV  = calcul_commun(zone , masque , surface_PV , prod_solaire_existante, pv_saisie , thermique_saisie , surface_thermique)

    rendement_global_bois = 0.766785


    with engine.connect() as conn:
       df_charges = pd.read_sql_query("SELECT * FROM dbo.TableCouverture", conn)
    besoin_chaud = deperdition_max
    taux_baisse = Baisse_conso_besoins.get(strategie, 0) 
   # print(f"deperdition max est : {deperdition_max}") 

    
    #Puissance PAC chaud retenue - Biomasse-
    if slug_strategie in ["bn" , "aucune"] :
        puissance_biomasse_retenue = besoin_chaud
    else : 
        puissance_biomasse_retenue = besoin_chaud * 0.5
  #  print(f"la puissance biomasse retenue est : {puissance_biomasse_retenue}")
    puissance_biomasse_retenue_scenario_max = besoin_chaud
    #% besoin chaud 
    besoin_chaud_pourcentage = round(((puissance_biomasse_retenue /besoin_chaud)*100),2)
    besoin_chaud_pourcentage_scenario_max = round(((puissance_biomasse_retenue_scenario_max / besoin_chaud)*100),2)
 #   print(f"le % besoin chaud est : {besoin_chaud_pourcentage} , le scenario max est : {besoin_chaud_pourcentage_scenario_max}")
    ## surface locale technique nécessaire 
    surface_locale_biomasse = max(puissance_biomasse_retenue * 0.3 , 100 )
    surface_locale_biomasse_scenario_max = max(besoin_chaud *0.3 , 100)
  #  print(f"la surface locale technique est : {surface_locale_biomasse} , celle de scenario max est : {surface_locale_biomasse_scenario_max}")

    #taux couverture _optimisé : 
## On va arrondir au plus proche possible ( le plus grand proche ) 
# On arrondit au multiple de 5 le plus proche

    palier = round(besoin_chaud_pourcentage / 5) * 5
    palier = max(0, min(100, palier))  
    # Filtrage de la ligne correspondante
    ligne = df_charges[df_charges["PuissancePct"] == palier]
    
    if ligne.empty:
        raise ValueError(f"Aucune ligne trouvée pour {palier}% de puissance")

    if typology not in df_charges.columns:
        raise ValueError(f"Typologie inconnue : {typology}")

    taux_couverture_besoins_chauds =  int(ligne[typology].values[0])
   # print(f"le Taux couverture des besoins chaud par la PAC est : {taux_couverture_besoins_chauds}")
  #  print(f"le total de conso chauffage utilisé est : {total_chauffage}")
   # print(f"le taux baisse est : {taux_baisse}")
   # print(f"le rendement globale est : {Rendement_globale}")

#taux couverture _scenario_maximum :
    palier_max = round(besoin_chaud_pourcentage_scenario_max / 5) * 5
    palier_max = max(0, min(100, palier_max))  
    # Filtrage de la ligne correspondante
    ligne = df_charges[df_charges["PuissancePct"] == palier_max]
    
    if ligne.empty:
        raise ValueError(f"Aucune ligne trouvée pour {palier_max}% de puissance")

    if typology not in df_charges.columns:
        raise ValueError(f"Typologie inconnue : {typology}")

    taux_couverture_scenario_max =  int(ligne[typology].values[0])
   # print(f"le Taux couverture des besoins chaud par la PAC en scenario max est : {taux_couverture_scenario_max}")



   ##taux_couverture_besoins_ecs 
    if typology == "Résidentiel" and Energie_ECS not in ["Electrique" , "PAC"]:
       taux_couverture_besoins_ecs = taux_couverture_besoins_chauds
    else : 
        taux_couverture_besoins_ecs = 0 
   # print(f"le taux de couverture des besoins ecs est : {taux_couverture_besoins_ecs}")

    ##besoins_thermiques
    besoins_thermiques = total_chauffage * (1-taux_baisse)* Rendement_globale
 #   print({Rendement_globale} , {taux_baisse})
  #  print(f"les besoins thermiques sont : {besoins_thermiques}")
    #Besoins chauds couverts par la biomasse
    besoin_chaud_biomasse = besoins_thermiques * (taux_couverture_besoins_chauds/100)
    besoin_chaud_biomasse_scenario_max = besoins_thermiques *(taux_couverture_scenario_max/100)
 #   print(f"Besoins chauds couverts par la biomasse : {besoin_chaud_biomasse} , et le scenario maximum : {besoin_chaud_biomasse_scenario_max}")
    #besoins chauds couverts par l'appoint 
    besoin_chaud_appoint = besoins_thermiques - besoin_chaud_biomasse
    besoin_chaud_appoint_scenario_max = besoins_thermiques - besoin_chaud_biomasse_scenario_max
  #  print(f"besoin chaud couvert par l'appoint : {besoin_chaud_appoint} , et le scenario maximum : {besoin_chaud_appoint_scenario_max}")
    ##besoin ECS
    besoins_ecs = total_ECS * rendement
  #  print(f"besoin ECS : {besoins_ecs}")
    #besoins ecs couverts par la biomasse :
    besoins_ecs_biomasse =  taux_couverture_besoins_ecs * besoins_ecs
  #  print(f"besoins ecs couverts par la biomasse : {besoins_ecs_biomasse}")
    ##besoins ecs couverts par l'appoint 
    if taux_couverture_besoins_ecs == 0 :
        besoins_ecs_appoint = 0 
    else:
        besoins_ecs_appoint = besoins_ecs - besoins_ecs_biomasse
 #   print(f"Besoins ECS couverts par l'appoint : {besoins_ecs_appoint}")
    ##Consommations enr Biomasse CH:
    conso_enr_biomasse_CH = besoin_chaud_biomasse / rendement_global_bois 
    conso_enr_biomasse_CH_scenario_max  = besoin_chaud_biomasse_scenario_max / rendement_global_bois 

   # print(f"Consommation EnR Biomasse CH : {conso_enr_biomasse_CH} et le scenario max : {conso_enr_biomasse_CH_scenario_max}")


    ##Consommation EnR Biomasse ECS
    conso_enr_biomasse_ECS = besoins_ecs_biomasse / 0.87
  #  print(f"Consommation EnR Biomasse ECS : {conso_enr_biomasse_ECS}")
    conso_enr_biomasse_ecs_ch = conso_enr_biomasse_ECS + conso_enr_biomasse_CH
    conso_enr_biomasse_ecs_ch_scenario_max = conso_enr_biomasse_ECS + conso_enr_biomasse_CH_scenario_max
  #  print(f"Consommation EnR Biomasse CH+ECS : {conso_enr_biomasse_ecs_ch} et le scenario max est : {conso_enr_biomasse_ecs_ch_scenario_max}")
    #Production EnR locale totale (existante + biomasse)
    Prod_enr_locale_totale_biomasse =  conso_enr_biomasse_ecs_ch +P_EnR_locale_solaire_existante + energie_PAC_delivre - conso_elec_PAC + Prod_enr_bois
    Prod_enr_locale_totale_biomasse_scenario_max =  conso_enr_biomasse_ecs_ch_scenario_max +P_EnR_locale_solaire_existante + energie_PAC_delivre - conso_elec_PAC + Prod_enr_bois
  #  print(f"Energie délivrée PAC existante : {energie_PAC_delivre} , conso_elec_PAC: {conso_elec_PAC} , Prod_enr_bois:{Prod_enr_bois} , conso_enr_biomasse_ecs_ch : {conso_enr_biomasse_ecs_ch} ")

   # print(f"Production EnR locale totale (existante + biomasse) : {Prod_enr_locale_totale_biomasse} et le scenario max est : {Prod_enr_locale_totale_biomasse_scenario_max}")
    ##Consommation élec projetée :
    conso_elec_proj_biomasse = conso_elec * (1-taux_baisse )
    if E_T_principal =="Aucune":
        conso_elec_proj_biomasse-=conso_enr_biomasse_ecs_ch
    else : 
        conso_elec_proj_biomasse
  #  print(f"Consommation élec projetée par la biomasse : {conso_elec_proj_biomasse}")
##Consommation thermique principale projetée (combustible ou RCU)

    if E_T_principal == "Aucune" :
        conso_thermique_principale_proj_biomasse = 0 
        conso_thermique_principale_proj_biomasse_max=0
    elif E_T_principal == "Réseau de froid" :
        conso_thermique_principale_proj_biomasse =  calibration_ET1_clim
        conso_thermique_principale_proj_biomasse_max = calibration_ET1_clim
    else : 
        conso_thermique_principale_proj_biomasse = besoin_chaud_appoint / Rendement_globale + calibration_ET1_ECS - conso_enr_biomasse_ECS + besoins_ecs_appoint /Rendement_globale

        conso_thermique_principale_proj_biomasse_max = besoin_chaud_appoint_scenario_max / Rendement_globale + calibration_ET1_ECS - conso_enr_biomasse_ECS + besoins_ecs_appoint / Rendement_globale
       # conso_thermique_principale_proj_biomasse_max = besoins_chauds_appoint_scenario_max / Rendement_globale + calibration_ET1_ECS

   # print(f"Consommation thermique principale projetée_biomasse : {conso_thermique_principale_proj_biomasse} , Rendement_globale : {Rendement_globale} , calibration ecs : {calibration_ET1_ECS} le scenario max est : {conso_thermique_principale_proj_biomasse_max}")

#consommation thermique appoint projetée 
   # conso_thermique_appoint_proj_geothermie = conso_principal_2_convertie * (1 - taux_baisse) * Rendement_globale
    conso_thermique_appoint_proj_biomasse = total_thermique2 * (1 - taux_baisse) 


  #  print(f"conso_principal_2_convertie est : {conso_principal_2_convertie}")
  #  print(f"consommation thermique appoint projetée est : {conso_thermique_appoint_proj_biomasse}")
## conso_totale_projetée

    conso_totale_proj_biomasse = round((conso_elec_proj_biomasse + conso_thermique_principale_proj_biomasse + conso_thermique_appoint_proj_biomasse + conso_enr_biomasse_ecs_ch),1)
    conso_totale_proj_biomasse_scenario_max = conso_elec_proj_biomasse + conso_thermique_principale_proj_biomasse_max + conso_thermique_appoint_proj_biomasse + conso_enr_biomasse_ecs_ch_scenario_max
    ratio_conso_totale_proj_biomasse = conso_totale_proj_biomasse  / surface 
   # conso_totale_proj_geothermie_scenario_max = conso_elec_proj_geothermie_max + conso_thermique_principale_proj_geothermie_max + conso_thermique_appoint_proj_geothermie
  #  print(f"consommation totale projetée : {conso_totale_proj_biomasse} et le scenario max : {conso_totale_proj_biomasse_scenario_max}")

##Taux enr locale Biomasse 

    enr_local_biomasse = round(((Prod_enr_locale_totale_biomasse /( energie_PAC_delivre + conso_totale_proj_biomasse ))*100),2)
    enr_local_biomasse_scenario_max  = round(((Prod_enr_locale_totale_biomasse_scenario_max /( energie_PAC_delivre + conso_totale_proj_biomasse_scenario_max ))*100),2)

  ##  enr_local_geothermie_scenario_max = round(((Prod_enr_locale_totale_geothermie_scenario_max /( besoins_thermiques +conso_elec_proj_geothermie ))*100),2)
   # print(f"enr local : {enr_local_biomasse} et enr locale scenario max est : {enr_local_biomasse_scenario_max}")
##Production EnR RCU
    part_reseau1 = taux_enr_principal * conso_thermique_principale_proj_biomasse if E_T_principal == "Réseau de chaleur" else 0
    part_reseau1_max = taux_enr_principal * conso_thermique_principale_proj_biomasse_max if E_T_principal == "Réseau de chaleur" else 0


    part_reseau2 = taux_enr_appoint * conso_thermique_appoint_proj_biomasse if E_T_appoint ==  "Réseau de chaleur" else 0

    prod_enr_rcu_biomasse = round(((part_reseau1 + part_reseau2)*100),0)
    prod_enr_rcu_biomasse_max = round(((part_reseau1_max + part_reseau2)*100),0)
   ## prod_enr_rcu_geothermie_max = round(((part_reseau1_max + part_reseau2)*100),0)


   # print(f"Production EnR RCU _biomasse : {prod_enr_rcu_biomasse}, et le scenario max : {prod_enr_rcu_biomasse_max}")

##Production EnR mix élec et gaz
    prod_enr_mix_biomasse =  conso_elec_proj_biomasse * Taux_EnR_mix_E_national_Elec
  ##  prod_enr_mix_geothermie_max = conso_elec_proj_geothermie_max * Taux_EnR_mix_E_national_Elec

    if E_T_principal == "Gaz naturel":
      prod_enr_mix_biomasse += conso_thermique_principale_proj_biomasse * Taux_EnR_mix_E_national_Gaz
     # prod_enr_mix_geothermie_max += conso_thermique_principale_proj_geothermie_max * Taux_EnR_mix_E_national_Gaz

    if E_T_appoint == "Gaz naturel":
      prod_enr_mix_biomasse += conso_thermique_appoint_proj_biomasse * Taux_EnR_mix_E_national_Gaz
      #prod_enr_mix_geothermie_max += conso_thermique_appoint_proj_geothermie * Taux_EnR_mix_E_national_Gaz

    
   # print(f"Production EnR mix élec et gaz -Biomasse-: {prod_enr_mix_biomasse}")

##production enr globale geothermie 
    prod_enr_globale_biomasse = ( Prod_enr_locale_totale_biomasse + prod_enr_rcu_biomasse + prod_enr_mix_biomasse)
    prod_enr_globale_biomasse_scenario_max = ( Prod_enr_locale_totale_biomasse_scenario_max + prod_enr_rcu_biomasse_max + prod_enr_mix_biomasse)

   ## prod_enr_globale_geothermie_scenario_max = ( Prod_enr_locale_totale_geothermie_scenario_max + prod_enr_rcu_geothermie + prod_enr_mix_geothermie_max)

  #  print(f"production enr&r globale-Biomasse- : {prod_enr_globale_biomasse} et le scenario max est : {prod_enr_globale_biomasse_scenario_max}")
##Taux enR&R global 
####### à corriger 
    enr_globale_biomasse = round((  (prod_enr_globale_biomasse / (energie_PAC_delivre + conso_totale_proj_biomasse))*100),2)
    enr_globale_biomasse_scenario_max = round((  (prod_enr_globale_biomasse_scenario_max / (energie_PAC_delivre + conso_totale_proj_biomasse_scenario_max))*100),2)

 #   enr_globale_geothermie_scenario_max = round((  (prod_enr_globale_geothermie_scenario_max / (besoins_thermiques+ conso_elec_proj_geothermie_max))*100),2)

   # print(f"le taux enr&r global-Biomasse- est : {enr_globale_biomasse} , le taux global en scenario max ets : {enr_globale_biomasse_scenario_max}")
##cout et impact carbone 
    conso_thermique = [ conso_thermique_principale_proj_biomasse , conso_thermique_appoint_proj_biomasse  , conso_elec_proj_biomasse]
    conso_thermique_max = [ conso_thermique_principale_proj_biomasse_max , conso_thermique_appoint_proj_biomasse  , conso_elec_proj_biomasse]

    #conso_thermique_scenario_max = [ conso_thermique_principale_proj_geothermie_max , conso_thermique_appoint_proj_geothermie  , conso_elec_proj_geothermie_max]

    total_impact_biomasse, total_cout_biomasse = calcul_carbone_et_cout_sql(slugs_energie , conso_thermique ,reseau_principal , reseau_appoint )
    total_impact_biomasse_max, total_cout_biomasse_max = calcul_carbone_et_cout_sql(slugs_energie , conso_thermique_max ,reseau_principal , reseau_appoint )

   # total_impact_geothermie_max, total_cout_geothermie_max = calcul_carbone_et_cout_sql(slugs_energie , conso_thermique_scenario_max ,reseau_principal , reseau_appoint )

    total_impact_biomasse +=  conso_enr_biomasse_ecs_ch * 0.03
    total_impact_biomasse_max += conso_enr_biomasse_CH_scenario_max * 0.03
    total_impact_biomasse = (total_impact_biomasse / surface)

    total_cout_biomasse = ( total_cout_biomasse / surface)
  #  print(f"les couts sont : {total_cout_biomasse} et les impacts sont : {total_impact_biomasse} , et le maximum est : {total_cout_biomasse_max} et le carbone : {total_impact_biomasse_max}")

    return round(puissance_biomasse_retenue , 2) , round(ratio_conso_totale_proj_biomasse, 1)  , enr_local_biomasse , enr_local_biomasse_scenario_max,  enr_globale_biomasse , enr_globale_biomasse_scenario_max,  round(total_impact_biomasse,2) , round(total_cout_biomasse,2)

def calcul_faisabilite_biomasse (zone_administrative1 ,situation , slug_temperature_emetteurs ,  slug_strategie , slug_usage , prod_ch_f  ):
    total_note = 0
    lettre_forcee = None 
    details_impacts = {}
    TABLE_FAISABILITE = "dbo.régles_faisabilité" 

   # print(f"la strategie est : {slug_strategie}")

    inputs = {
        "zone_administrative1": zone_administrative1.lower(), # rouge 
        "situation": situation.lower() , # urbain 
        "regime_temperature_emetteurs": slug_temperature_emetteurs, ## slugs 
        "strategie": slug_strategie, ## slugs 
        "usage_thermique": slug_usage , ## slugs 
        "type_production": prod_ch_f
         }
                

    # Correspondance pour adapter les clés de sortie
    remap_keys = {
        "zone administrative": "zone_administrative",
        "densité urbaine": "densite_urbaine",
        "contribution ilot de chaleur urbain" :  "cicu" , 
        "acoustique": "acoustique",
        "installation existante émetteur _ régime de température": "installation_emetteur",
        "installation existante production": "installation_production"
        
    }
    
   
    STRATEGIES_SANS_RENO = ["be", "bn", "rl"]
    USAGES_SANS_CLIM = ["ch", "ch_ecs"]
    
    usage_clim = "Sans clim" if inputs["usage_thermique"] in USAGES_SANS_CLIM else "Avec Clim"
    strategie_humaine = "Sans réno ou réno légère" if inputs["strategie"] in STRATEGIES_SANS_RENO else "Réno lourde"

     ##Cas particulier 3 : situation urbain 
    if situation == "urbain":
        print("⚠️ Cas particulier : la situation est urbaine ! ")
        lettre_forcee = "D"
##Cas particulier 1 
    if inputs["zone_administrative1"] == "bâtiment classé":
        print("⚠️ Cas particulier : Bâtiment classé→ faisabilité forcée à E")
        lettre_forcee = "E"
        
    
    # Cas particulier 2 : stratégie ≠ réno lourde et prod = individuelle
    if strategie_humaine != "Réno lourde" and inputs["type_production"] == "production individuelle":
        print("⚠️ Cas particulier : stratégie ≠ réno lourde + production individuelle → faisabilité forcée à E")
        lettre_forcee = "E"

    
   
    
    # Récupérer la table complète
    with engine.connect() as conn:
        df = pd.read_sql(f"SELECT * FROM {TABLE_FAISABILITE}", conn)

    df_geo = df[df["Biomasse"].notnull()] ## filtrer sur la colonne biomasse qu'on veut 

    critères = [
        # zone_gmi => Cartographie nationale géothermie
        {
            "Impacts": "zone administrative",
            "Caractéristiques": inputs["zone_administrative1"]
        },
        # situation => Contribution ilot de chaleur
        {
            "Impacts": "densité urbaine",
            "Caractéristiques": inputs["situation"]
        },
        {
            "Impacts": "Contribution ilot de chaleur urbain",
            "Caractéristiques": inputs["situation"]
        },
        # situation => Acoustique
        {
            "Impacts": "Acoustique",
            "Caractéristiques": inputs["situation"]
        },
        # régime température + usage_clim => Installation existante émetteur
        {
            "Impacts": "Installation existante émetteur _ Régime de température",
            "Caractéristiques": inputs["regime_temperature_emetteurs"].lower(),
            "Usage_climatisation": usage_clim,
            "Stratégie_de_rénovation": strategie_humaine
        },
        # type_production => Installation existante production
        {
            "Impacts": "Installation existante production",
            "Caractéristiques": inputs["type_production"].lower(),
            "Usage_climatisation": usage_clim,
            "Stratégie_de_rénovation": strategie_humaine
        }
    ]


    for crit in critères:
        print(crit)
        filtres = (df_geo["Impacts"].str.lower() == crit["Impacts"].lower()) & (df_geo["Caractéristiques"].str.lower() == crit["Caractéristiques"].lower())

        if "Usage_climatisation" in crit:
            filtres &= (df_geo["Usage_climatisation"].str.lower() == crit["Usage_climatisation"].lower())
        if "Stratégie_de_rénovation" in crit:
            filtres &=(
                (df_geo["Stratégie_de_rénovation"].isna()) |
                (df_geo["Stratégie_de_rénovation"].str.lower() == crit["Stratégie_de_rénovation"].lower())
            
            ) 
            
            
        ligne = df_geo[filtres]

        if ligne.empty:
            print(f"[WARN] Ligne manquante pour critère {crit}")
            continue

        note = ligne["Biomasse"].values[0]
        ponderation = ligne["Pondération"].values[0]
        if pd.isna(ponderation):
            print(f"[WARN] Pondération manquante pour critère : {crit} → ignoré")
            continue

        total_note += note * ponderation
        # Utilisation des noms renommés
        impact = crit["Impacts"].lower()
        clean_key = remap_keys.get(impact, impact)
        details_impacts[clean_key] = note


        print(f"🟩 Critère : {crit}")
        # print(f"    ➤ Valeur saisie        : {valeur_utilisateur}")
        print(f"    ➤ Note trouvée         : {note}")
        print(f"    ➤ Pondération          : {ponderation}")
        print(f"    ➤ Score pondéré        : {total_note}")



    # Attribution de lettre selon barème
    if total_note >= 81:
        lettre = "A"
    elif total_note >= 61:
        lettre = "B"
    elif total_note >= 41:
        lettre = "C"
    elif total_note >= 21:
        lettre =  "D"
    else:
        lettre = "E"
    
     # --- Lettre finale: forcée si défini, sinon barème ---
    final_letter = lettre_forcee or lettre
    details_impacts_clean = {
    remap_keys.get(k.lower(), k.lower()): int(round(float(v)))
    for k, v in details_impacts.items()
}

# Affichage lisible
    print("le details impacts est :", json.dumps(details_impacts_clean, ensure_ascii=False, indent=2))

   

    return final_letter , json.dumps(details_impacts_clean, ensure_ascii=False)

 


