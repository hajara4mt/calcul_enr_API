from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from app.db.database import get_session
from app.models.output import output
from app.models.output_enr_r import output_enr_r  
from app.models.project_model import Projects
from app.models.inputs import input
from app.models.response_modele_output import GetOutputByIdResponse
import json

router = APIRouter()
def _safe_json_load(val):
    if val is None:
        return None
    if isinstance(val, (dict, list)):
        return val
    if isinstance(val, str):
        try:
            return json.loads(val)
        except json.JSONDecodeError:
            return val  # renvoie la chaîne brute si ce n'est pas du JSON
    return val


@router.get("/resultats/{id_projet}" , response_model=GetOutputByIdResponse)
def get_output_by_id(id_projet: str, session: Session = Depends(get_session)):
    # 🔹 Requête dans la table principale
    enr_projet = session.exec ( select(Projects).where(Projects.id_projet == id_projet)).first()
    result = session.exec(select(output).where(output.id_projet == id_projet)).first()
    enr_result = session.exec(select(output_enr_r).where(output_enr_r.id_projet == id_projet)).first()
    input_result = session.exec(select(input).where(input.id_projet == id_projet)).first()

    present = {
        "projet" : bool(enr_projet) ,
        "output": bool(result),
        "output_enr_r": bool(enr_result),
        "input": bool(input_result)
    }

    # Cas 1 : projet totalement inconnu
    if not any(present.values()):
        raise HTTPException( status_code=404, detail="Projet inconnu : Résultat ENR non trouvé pour ce projet")
    
    if not present["projet"] : 
        raise HTTPException( status_code=404, detail="Projet inconnu : Résultat ENR non trouvé pour ce projet")

    
    if not present["output"] and (present["input"] or present["output_enr_r"]):
        raise HTTPException(status_code=404, detail="Projet existant - Résultat ENR non trouvé pour ce projet ")
    
    if not present["output_enr_r"] and (present["input"] or present["projet"]):
        raise HTTPException(status_code=404, detail="Projet existant - Résultat ENR non trouvé pour ce projet ")
    
    if not present["input"]:
        raise HTTPException(status_code=404, detail="Projet non existant - Résultat ENR non trouvé pour ce projet ")
  

 # 🔹 Parser les données JSON de output
    data = result.model_dump(exclude={"Id"})
    for champ in ["usages_energitiques", "conso_energitiques", "Faisabilité_calculée" , "conso_energitiques1"]:
        if isinstance(data.get(champ), str):
            try:
                data[champ] = json.loads(data[champ])
            except json.JSONDecodeError:
                pass

    nom_solaire = getattr(enr_result, "nom_solaire", None) or "solaire"

# 🔹 Transformation des inputs
    projets_data = input_result.model_dump(exclude={"Id", "id" ,"id_projet", "date_creation"})

# Renommer la clé Id_utilisateur -> id_utilisateur_primaire
    if "Id_utilisateur" in projets_data:
      projets_data["id_utilisateur_primaire"] = projets_data.pop("Id_utilisateur")


    # 🔹 Structure de réponse complète
    return {
        "message": "Résultat complet récupéré avec succès",
        "id_projet": id_projet,
        "date_modelisation_derniere": result.data_modelisation_derniere.isoformat(),
        "date_creation_projet" : input_result.date_creation , 
        "projets": projets_data , 



        
        "resultats" : { 

        "bilan_conso_initial": {
            "conso_annuelles_totales_initiales": data["conso_annuelles_totales_initiales"],
            "conso_annuelles_totales_initiales_ratio": data["conso_annuelles_totales_initiales_ratio"],
            "cout_total_initial": data["cout_total_initial"],
            "taux_enr_local_initial": data["taux_ENR_local_initial"],
            "usages_energitiques": data["usages_energitiques"],
            "distributions_energitiques": data["conso_energitiques"],
            "conso_energitiques" : data["conso_energitiques1"] , 

            "conso_carbone_initial": data["conso_carbone_initial"]
        },

        "indicateur": {
            "enr_retenue": data["enr_retenue"] , 
            "enr_combinaison" : data["enr_combinaison"] , 
            "enr_local_initial": data["taux_ENR_local_initial"]
            
        },
         "combinaison" : {
               "ratio_conso_totale_projet" : data["ratio_conso_total_combinaison"] , 
               "enr_local" : data["enr_local_combinaison"] , 
               "enr_global" : data["enr_global_combinaison"] , 
               "lettre_faisabilite" : data["lettre_faisabilite_combinaison"].strip() , 
               "conso_carbone" : data["total_impact_combinaison"] , 
               "cout_total" : data["total_cout_combinaison"]

            } , 
        "enr_r": { 
          nom_solaire : {
            "puissance_retenue": int(enr_result.puissance_retenue_solaire),
            "ratio_conso_totale_projet": int(enr_result.ratio_conso_totale_projet_solaire),
            "enr_local": round(enr_result.enr_local_solaire,2),
            "enr_local_max": round(enr_result.enr_local_max_solaire,2),
            "enr_global": round(enr_result.enr_global_solaire,2),
            "enr_global_max": round(enr_result.enr_globale_scenario_max_solaire,2),
            "conso_carbone": int(enr_result.conso_carbone_pv_solaire),
            "cout_total": int(enr_result.cout_total_pv_solaire),
            "lettre_faisabilite": enr_result.lettre_faisabilite_solaire.strip(),
            "faisabilité_calculee": data["Faisabilité_calculée"],
        },
        # --- géothermie ---
        "geothermie": {
                    "puissance_retenue": int(enr_result.puissance_retenue_géothermie),
                    "ratio_conso_totale_projet": int(enr_result.ratio_conso_totale_projet_géothermie),
                    "enr_local": enr_result.enr_local_géothermie,
                    "enr_local_max": enr_result.enr_local_max_géothermie,
                    "enr_global": enr_result.enr_global_géothermie,
                    "enr_global_max": enr_result.enr_globale_scenario_max_géothermie,
                    "conso_carbone": int(enr_result.conso_carbone_géothermie),
                    "cout_total": int(enr_result.cout_total_géothermie),
                    "lettre_faisabilite": enr_result.lettre_faisabilite_géothermie.strip(),
                    "faisabilite_calculee": _safe_json_load(getattr(enr_result, "Faisabilité_calculée_géothermie", None)),
                    "surface_locale" : int( enr_result.surface_locale_geothermie)

                },
         # --- biomasse ---
        "biomasse": {
                    "puissance_retenue": int(enr_result.puissance_retenue_biomasse),
                    "ratio_conso_totale_projet": int(enr_result.ratio_conso_totale_projet_biomasse),
                    "enr_local": enr_result.enr_local_biomasse,
                    "enr_local_max": enr_result.enr_local_max_biomasse,
                    "enr_global": enr_result.enr_global_biomasse,
                    "enr_global_max": enr_result.enr_globale_scenario_max_biomasse,
                    "conso_carbone": int(enr_result.conso_carbone_biomasse),
                    "cout_total": int(enr_result.cout_total_biomasse),
                    "lettre_faisabilite": enr_result.lettre_faisabilite_biomasse.strip(),
                    "faisabilite_calculee": _safe_json_load(getattr(enr_result, "Faisabilité_calculée_biomasse", None)),
                    "surface_locale" : int(enr_result.surface_locale_biomasse)
                },

        "aerothermie": {
                  "puissance_retenue": int(enr_result.puissance_retenue_aerothermie),
                  "ratio_conso_totale_projet":round(  enr_result.ratio_conso_totale_projet_aerothermie),
                  "enr_local": enr_result.enr_local_aerothermie,
                  "enr_local_max": enr_result.enr_local_max_aerothermie,
                  "enr_global": enr_result.enr_global_aerothermie,
                   "enr_global_max": enr_result.enr_global_scenario_max_aerothermie,
                  "conso_carbone": int(enr_result.conso_carbone_aerothermie),
                 "cout_total": round(enr_result.cout_total_aerothermie),
                 "lettre_faisabilite": enr_result.lettre_faisabilite_aerothermie ,
                  "faisabilite_calculee": _safe_json_load(getattr(enr_result, "Faisabilité_calculée_aerothermie", None)),
                  "surface_locale" : int(enr_result.surface_locale_aerothermie)
        
    } , 


         # --- récupération de chaleur ---
                "recuperation_de_chaleur": {
                    "puissance_retenue": int(enr_result.puissance_retenue_chaleur),
                    "ratio_conso_totale_projet": int(enr_result.ratio_conso_totale_projet_chaleur),
                    "enr_local": enr_result.enr_local_chaleur,
                    "enr_local_max": enr_result.enr_local_max_chaleur,
                    "enr_global": enr_result.enr_global_chaleur,
                    "enr_global_max": enr_result.enr_global_scenario_max_chaleur,
                    "conso_carbone": int(enr_result.conso_carbone_chaleur),
                    "cout_total": int(enr_result.cout_total_chaleur),
                    "lettre_faisabilite": enr_result.lettre_faisabilite_chaleur.strip(),
                    "faisabilite_calculee": _safe_json_load(getattr(enr_result, "Faisabilité_calculée_chaleur", None)),
                },
        

        















    }}}

    

            
        

