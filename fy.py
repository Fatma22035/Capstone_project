import pandas as pd
import re

print("="*60)
print("🧹 NETTOYAGE DU FICHIER CSV UNTOITENRIM")
print("="*60)

# Charger le fichier brut en gérant les lignes mal formées
fichier_brut = 'data_raw/untoitenrim.csv'
fichier_nettoye = 'data_raw/untoitenrim_propre.csv'

print(f"📂 Lecture du fichier: {fichier_brut}")

# Lire le fichier ligne par ligne pour gérer les retours à la ligne
with open(fichier_brut, 'r', encoding='utf-8') as f:
    lignes = f.readlines()

print(f"📊 Nombre de lignes brutes: {len(lignes)}")

# Reconstitution des lignes CSV
lignes_propres = []
ligne_en_cours = ""

for ligne in lignes:
    # Si la ligne commence par "untoitenrin.com", c'est une nouvelle annonce
    if ligne.startswith('untoitenrin.com'):
        if ligne_en_cours:
            lignes_propres.append(ligne_en_cours)
        ligne_en_cours = ligne.strip()
    else:
        # Sinon, c'est la suite de l'annonce précédente
        ligne_en_cours += " " + ligne.strip()

# Ajouter la dernière ligne
if ligne_en_cours:
    lignes_propres.append(ligne_en_cours)

print(f"📊 Lignes reconstituées: {len(lignes_propres)}")

# Écrire le fichier nettoyé
with open(fichier_nettoye, 'w', encoding='utf-8') as f:
    for ligne in lignes_propres:
        f.write(ligne + '\n')

print(f"💾 Fichier nettoyé sauvegardé: {fichier_nettoye}")

# Maintenant, charger le fichier nettoyé avec pandas
try:
    df = pd.read_csv(fichier_nettoye)
    print(f"\n✅ Chargement réussi: {len(df)} lignes")
    print(f"\n📋 Colonnes: {list(df.columns)}")
    
    # Nettoyer les descriptions (enlever les guillemets superflus)
    if 'description' in df.columns:
        df['description'] = df['description'].str.replace('"', '').str.replace("'", "")
    
    # Afficher un aperçu
    print("\n👀 Aperçu des données nettoyées:")
    print(df[['titre', 'prix', 'type_bien', 'quartier']].head(10))
    
    # Sauvegarder la version propre
    df.to_csv('data_raw/untoitenrim_final.csv', index=False, encoding='utf-8-sig')
    print(f"\n💾 Version finale sauvegardée: data_raw/untoitenrim_final.csv")
    
    # Fusion avec le fichier final
    print("\n🔄 Fusion avec le fichier final...")
    
    fichier_final = 'data_raw/final_data_raw.csv'
    
    if os.path.exists(fichier_final):
        df_final = pd.read_csv(fichier_final)
        print(f"📂 Fichier final existant: {len(df_final)} lignes")
        
        # Aligner les colonnes
        for col in df_final.columns:
            if col not in df.columns:
                df[col] = "Non spécifié"
        
        df_aligné = df[df_final.columns]
        df_combined = pd.concat([df_final, df_aligné], ignore_index=True)
        df_combined = df_combined.drop_duplicates(subset=['id_unique', 'source'], keep='first')
        df_combined.to_csv(fichier_final, index=False, encoding='utf-8-sig')
        print(f"✅ Fichier final mis à jour: {len(df_combined)} annonces")
    else:
        df.to_csv(fichier_final, index=False, encoding='utf-8-sig')
        print(f"✅ Nouveau fichier final créé: {len(df)} annonces")
        
except Exception as e:
    print(f"❌ Erreur lors du chargement: {e}")
    print("\n📝 Tentative de correction manuelle...")
    
    # Essayer de lire avec différents paramètres
    df = pd.read_csv(fichier_nettoye, quotechar='"', doublequote=True)
    print(f"✅ Lecture avec quotechar: {len(df)} lignes")
    df.to_csv('data_raw/untoitenrim_corrige.csv', index=False, encoding='utf-8-sig')