def repartition_usages1(energis , slug_principal , slug_appoint , calcul_conso_chauffage , conso_elec , rendement_production ,Rendement_globale, conso_principal , conso_appoint ,   Consommation_ventilation , Conso_specifique, Conso_eclairage, usage_thermique,zone_climatique , surface ,  typology ,besoins_ECS , temperature_retenue , type_prod_ecs , jours_ouvrés , rendement , E_T_principal , E_T_appoint , Energie_ECS , systeme_chauffage , zone , masque , surface_PV , prod_solaire_existante, pv_saisie , thermique_saisie , surface_thermique , reseau_principal , reseau_appoint): 

    
    P_EnR_locale_solaire_existante  , productible_thermique , productible_PV = calcul_commun (zone , masque , surface_PV , prod_solaire_existante, pv_saisie , thermique_saisie , surface_thermique)
##on definit les conso : 
    conso_principal_1_convertie = convertir_consommation(E_T_principal, conso_principal)
    conso_principal_2_convertie = convertir_consommation(E_T_appoint, conso_appoint)

    Consommations_annuelles_totales_initiales = conso_elec + conso_principal_1_convertie + conso_principal_2_convertie 
    Consommations_annuelles_totales_initiales_ratio = Consommations_annuelles_totales_initiales / surface
    consos = [conso_principal_1_convertie ,conso_principal_2_convertie , conso_elec ]
    
    total_impact, total_cout = calcul_carbone_et_cout_sql(energis , consos ,reseau_principal , reseau_appoint )
    

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

    return conso_principal_2_convertie, conso_principal_1_convertie , Consommations_annuelles_totales_initiales , Consommations_annuelles_totales_initiales_ratio,  total_impact, total_cout, prod_enr_locale_site , calibration_ET1_ECS , calibration_ET1_clim , total_chauffage , total_thermique2 ,total_thermique1 ,  conso_surfacique_clim , total_ECS , besoin_60 , perte_bouclage , conso_E_ECS , round(taux_enr_initial , 2) , Prod_enr_bois , conso_elec_PAC , usages_energitiques , conso_energitiques , energie_PAC_delivre
    return conso_principal_2_convertie, conso_principal_1_convertie , Consommations_annuelles_totales_initiales , Consommations_annuelles_totales_initiales_ratio,  total_impact, total_cout,  prod_enr_locale_site , calibration_ET1_ECS , calibration_ET1_clim , total_chauffage , total_thermique2 ,total_thermique1 ,  conso_surfacique_clim , total_ECS , besoin_60 , perte_bouclage , conso_E_ECS , round(taux_enr_initial , 2) , Prod_enr_bois , conso_elec_PAC , usages_energitiques , conso_energitiques , energie_PAC_delivre
