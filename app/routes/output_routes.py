from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from app.db.database import get_session
from app.models.output import output
from app.models.output_enr_r import output_enr_r  
from app.models.inputs import input
from app.models.response_modele_output import GetOutputByIdResponse
import json

router = APIRouter()

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
            "enr_retenue": data["enr_retenue"]
        },
        "enr_r": { 
          "solaire_pv": {
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

          "thermique": {
            "puissance_retenue": int(enr_result.puissance_retenue_thermique),
            "ratio_conso_totale_projet": int(enr_result.ratio_conso_totale_projet_thermique),
            "enr_local": round(enr_result.enr_local_thermique,2),
            "enr_local_max": round(enr_result.enr_local_max_thermique,2),
            "enr_global": round(enr_result.enr_global_thermique,2),
            "enr_globale_scenario_max": round(enr_result.enr_globale_scenario_max_thermique,2),
            "conso_carbone": int(enr_result.conso_carbone_pv_thermique),
            "cout_total": int(enr_result.cout_total_pv_thermique),
            "lettre_faisabilite": enr_result.lettre_faisabilite_thermique.strip()
        },

          "hybride": {
            "puissance_retenue": int(enr_result.puissance_retenue_hybride),
            "ratio_conso_totale_projet": int(enr_result.ratio_conso_totale_projet_hybride),
            "enr_local": round(enr_result.enr_local_hybride,2),
            "enr_local_max": round(enr_result.enr_local_max_hybride,2),
            "enr_global": round(enr_result.enr_global_hybride,2),
            "enr_globale_scenario_max": round(enr_result.enr_globale_scenario_max_hybride,2),
            "conso_carbone": int(enr_result.conso_carbone_pv_hybride),
            "cout_total": int(enr_result.cout_total_pv_hybride),
            "lettre_faisabilite": enr_result.lettre_faisabilite_hybride.strip()
        }
    }}}
