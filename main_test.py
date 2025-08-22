# test_enr.py

from calcul_enr_test import ProjetCalcul
import json

if __name__ == "__main__":
    # 🔁 Mets ici l'ID du projet à tester (il doit exister dans ta base input)
    id_projet = "PROJET-20250822-2207"
    print(f"🚀 Lancement du calcul ENR pour le projet : {id_projet}")
    projet = ProjetCalcul(id_projet)
    resultats = projet.run()

    print("\n✅ Résultats du calcul ENR :")
    print(json.dumps(resultats, indent=4, ensure_ascii=False))
