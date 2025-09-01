# test_enr.py

from calcul_enr import ProjetCalcul
import json

if __name__ == "__main__":
    
    id_projet = "PROJET-20250829-8894"
    print(f"🚀 Lancement du calcul ENR pour le projet : {id_projet}")
    projet = ProjetCalcul(id_projet)
    resultats = projet.run()

    print("\n✅ Résultats du calcul ENR :")
    print(json.dumps(resultats, indent=4, ensure_ascii=False))
