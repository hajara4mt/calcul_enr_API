from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from app.db.database import get_session
from app.models.output import output
from app.models.output_enr_r import output_enr_r  # ⚠️ Assure-toi que ce modèle existe bien
import json

router = APIRouter()

@router.get("/resultats/{id_projet}")
def get_output_by_id(id_projet: str, session: Session = Depends(get_session)):
    # 🔹 Requête dans la table principale
    result = session.exec(select(output).where(output.id_projet == id_projet)).first()

    if not result:
        raise HTTPException(status_code=404, detail="Résultat non trouvé dans output")

    # 🔹 Requête dans la table secondaire
    enr_result = session.exec(select(output_enr_r).where(output_enr_r.id_projet == id_projet)).first()

    if not enr_result:
        raise HTTPException(status_code=404, detail="Résultat ENR non trouvé pour ce projet")

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

        "Bilan de consommation initial": {
            "conso_annuelles_totales_initiales": data["conso_annuelles_totales_initiales"],
            "conso_annuelles_totales_initiales_ratio": data["conso_annuelles_totales_initiales_ratio"],
            "cout_total_initial": data["cout_total_initial"],
            "taux_ENR_local_initial": data["taux_ENR_local_initial"],
            "usages_energitiques": data["usages_energitiques"],
            "conso_energitiques": data["conso_energitiques"],
            "conso_carbone_initial": data["conso_carbone_initial"]
        },

        "Indicateur": {
            "enr_retenue": data["enr_retenue"]
        },

        "Solaire": {
            "puissance_retenue": enr_result.puissance_retenue_solaire,
            "ratio_conso_totale_projet": enr_result.ratio_conso_totale_projet_solaire,
            "enr_local": enr_result.enr_local_solaire,
            "enr_local_max": enr_result.enr_local_max_solaire,
            "enr_global": enr_result.enr_global_solaire,
            "enr_globale_scenario_max": enr_result.enr_globale_scenario_max_solaire,
            "conso_carbone": enr_result.conso_carbone_pv_solaire,
            "cout_total": enr_result.cout_total_pv_solaire,
            "lettre_faisabilite": enr_result.lettre_faisabilite_solaire,
            "Faisabilité_calculée": data["Faisabilité_calculée"],
        },

        "Thermique": {
            "puissance_retenue": enr_result.puissance_retenue_thermique,
            "ratio_conso_totale_projet": enr_result.ratio_conso_totale_projet_thermique,
            "enr_local": enr_result.enr_local_thermique,
            "enr_local_max": enr_result.enr_local_max_thermique,
            "enr_global": enr_result.enr_global_thermique,
            "enr_globale_scenario_max": enr_result.enr_globale_scenario_max_thermique,
            "conso_carbone": enr_result.conso_carbone_pv_thermique,
            "cout_total": enr_result.cout_total_pv_thermique,
            "lettre_faisabilite": enr_result.lettre_faisabilite_thermique
        },

        "Hybride": {
            "puissance_retenue": enr_result.puissance_retenue_hybride,
            "ratio_conso_totale_projet": enr_result.ratio_conso_totale_projet_hybride,
            "enr_local": enr_result.enr_local_hybride,
            "enr_local_max": enr_result.enr_local_max_hybride,
            "enr_global": enr_result.enr_global_hybride,
            "enr_globale_scenario_max": enr_result.enr_globale_scenario_max_hybride,
            "conso_carbone": enr_result.conso_carbone_pv_hybride,
            "cout_total": enr_result.cout_total_pv_hybride,
            "lettre_faisabilite": enr_result.lettre_faisabilite_hybride
        }
    }
