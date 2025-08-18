from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from app.db.database import get_session
from app.models.output import output
from app.models.output_enr_r import output_enr_r  
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
    result = session.exec(select(output).where(output.id_projet == id_projet)).first()

    if not result:
        raise HTTPException(status_code=404, detail="Résultat non trouvé dans output")

    # 🔹 Requête dans la table secondaire
    enr_result = session.exec(select(output_enr_r).where(output_enr_r.id_projet == id_projet)).first()

    if not enr_result:
        raise HTTPException(status_code=404, detail="Résultat ENR non trouvé pour ce projet")
    
    # 🔹 Inputs du projet
    input_result = session.exec(select(input).where(input.id_projet == id_projet)).first()
    if not input_result:
        raise HTTPException(status_code=404, detail="Inputs du projet non trouvés")


    # 🔹 Parser les données JSON de output
    data = result.model_dump(exclude={"Id"})
    for champ in ["usages_energitiques", "conso_energitiques", "Faisabilité_calculée"]:
        if isinstance(data.get(champ), str):
            try:
                data[champ] = json.loads(data[champ])
            except json.JSONDecodeError:
                pass

    nom_solaire = getattr(enr_result, "nom_solaire", None) or "solaire"

    # 🔹 Structure de réponse complète
    return {
        "message": "Résultat complet récupéré avec succès",
        "id_projet": id_projet,
        "date_modelisation_derniere": result.data_modelisation_derniere.isoformat(),
        "date_creation_projet" : input_result.date_creation , 
        "projets": input_result.model_dump(exclude={"Id", "id_projet" , "date_creation"}) , 



        
        "resultats" : { 

        "bilan_conso_initial": {
            "conso_annuelles_totales_initiales": data["conso_annuelles_totales_initiales"],
            "conso_annuelles_totales_initiales_ratio": data["conso_annuelles_totales_initiales_ratio"],
            "cout_total_initial": data["cout_total_initial"],
            "taux_enr_local_initial": data["taux_ENR_local_initial"],
            "usages_energitiques": data["usages_energitiques"],
            "conso_energitiques": data["conso_energitiques"],
            "conso_carbone_initial": data["conso_carbone_initial"]
        },

        "indicateur": {
            "enr_retenue": data["enr_retenue"] , 
            "enr_local_initial": data["taux_ENR_local_initial"]
        },
        "enr_r": { 
          nom_solaire : {
            "puissance_retenue": int(enr_result.puissance_retenue_solaire),
            "ratio_conso_totale_projet": int(enr_result.ratio_conso_totale_projet_solaire),
            "enr_local": round(enr_result.enr_local_solaire,2),
            "enr_local_max": round(enr_result.enr_local_max_solaire,2),
            "enr_global": round(enr_result.enr_global_solaire,2),
            "enr_globale_scenario_max": round(enr_result.enr_globale_scenario_max_solaire,2),
            "conso_carbone": int(enr_result.conso_carbone_pv_solaire),
            "cout_total": int(enr_result.cout_total_pv_solaire),
            "lettre_faisabilite": enr_result.lettre_faisabilite_solaire.strip(),
            "faisabilité_calculee": data["Faisabilité_calculée"],
        },
        # --- géothermie ---
        "géothermie": {
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
                },
         # --- récupération de chaleur ---
                "récupération de chaleur": {
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
