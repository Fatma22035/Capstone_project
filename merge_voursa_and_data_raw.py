import pandas as pd
import os
import numpy as np
import csv

print("="*60)
print("🔄 FUSION ROBUSTE - SOURCE EN PREMIÈRE COLONNE")
print("="*60)

# Chemins des fichiers
fichier_voursa = 'data_raw/voursa_raw.csv'
fichier_final = 'data_raw/final_data_raw.csv'
fichier_sortie = 'data_raw/dataset_complet.csv'

# Vérifier que les fichiers existent
if not os.path.exists(fichier_voursa):
    print(f"❌ Fichier voursa non trouvé: {fichier_voursa}")
    exit()

if not os.path.exists(fichier_final):
    print(f"❌ Fichier final non trouvé: {fichier_final}")
    exit()

print("📂 Chargement du fichier voursa...")
df_voursa = pd.read_csv(fichier_voursa)
print(f"✅ Voursa: {len(df_voursa)} lignes")

# ============================================
# CHARGEMENT ROBUSTE DU FICHIER FINAL
# ============================================
print("\n🔧 Chargement du fichier final avec gestion des erreurs...")

# Lire le fichier ligne par ligne avec le module csv
lignes_valides = []
en_tete = None
lignes_ignorees = 0

with open(fichier_final, 'r', encoding='utf-8') as f:
    reader = csv.reader(f, quotechar='"', delimiter=',', quoting=csv.QUOTE_ALL)
    
    for i, ligne in enumerate(reader):
        if i == 0:
            en_tete = ligne
            lignes_valides.append(ligne)
            print(f"📋 En-tête ({len(ligne)} champs): {ligne}")
        else:
            if len(ligne) == len(en_tete):
                lignes_valides.append(ligne)
            else:
                lignes_ignorees += 1
                print(f"⚠️ Ligne {i+1} ignorée: {len(ligne)} champs au lieu de {len(en_tete)}")
                print(f"   Début: {str(ligne)[:100]}...")

print(f"\n📊 Statistiques de chargement:")
print(f"   - Lignes valides: {len(lignes_valides)}")
print(f"   - Lignes ignorées: {lignes_ignorees}")

# Créer un DataFrame à partir des lignes valides
if len(lignes_valides) > 1:  # Au moins l'en-tête + 1 ligne
    # Convertir en DataFrame
    df_final = pd.DataFrame(lignes_valides[1:], columns=lignes_valides[0])
    print(f"✅ Final chargé: {len(df_final)} lignes")
else:
    print("❌ Aucune ligne valide dans le fichier final")
    exit()

# ============================================
# ALIGNEMENT DES COLONNES
# ============================================
print("\n🔄 Analyse des colonnes...")

colonnes_voursa = list(df_voursa.columns)
colonnes_final = list(df_final.columns)

print(f"\n📋 Colonnes Voursa ({len(colonnes_voursa)}):")
for col in colonnes_voursa:
    print(f"   - {col}")

print(f"\n📋 Colonnes Final ({len(colonnes_final)}):")
for col in colonnes_final:
    print(f"   - {col}")

# Créer la liste de toutes les colonnes
toutes_colonnes = list(set(colonnes_voursa + colonnes_final))
print(f"\n📋 Total colonnes avant réorganisation: {len(toutes_colonnes)}")

# ============================================
# RÉORGANISATION - METTRE 'source' EN PREMIER
# ============================================
print("\n🔄 Réorganisation des colonnes...")

# S'assurer que 'source' est dans la liste
if 'source' not in toutes_colonnes:
    toutes_colonnes.append('source')

# Mettre 'source' en premier, puis toutes les autres colonnes triées
autres_colonnes = [col for col in toutes_colonnes if col != 'source']
autres_colonnes.sort()  # Tri alphabétique pour le reste
colonnes_ordonnees = ['source'] + autres_colonnes

print(f"\n📋 Ordre des colonnes:")
for i, col in enumerate(colonnes_ordonnees):
    print(f"   {i+1:2}. {col}")

# ============================================
# PRÉPARATION DES DATAFRAMES
# ============================================
print("\n🔄 Alignement des colonnes...")

# Préparer df_voursa avec toutes les colonnes dans le bon ordre
df_voursa_prepare = pd.DataFrame()
for col in colonnes_ordonnees:
    if col in df_voursa.columns:
        df_voursa_prepare[col] = df_voursa[col]
    else:
        df_voursa_prepare[col] = np.nan

# S'assurer que source est 'voursa.com' pour ces lignes
df_voursa_prepare['source'] = 'voursa.com'

# Préparer df_final avec toutes les colonnes dans le bon ordre
df_final_prepare = pd.DataFrame()
for col in colonnes_ordonnees:
    if col in df_final.columns:
        df_final_prepare[col] = df_final[col]
    else:
        df_final_prepare[col] = np.nan

# ============================================
# FUSION
# ============================================
print("\n🔄 Fusion des DataFrames...")

df_fusion = pd.concat([df_final_prepare, df_voursa_prepare], ignore_index=True)

print(f"\n📊 STATISTIQUES APRÈS FUSION:")
print(f"   - Total lignes: {len(df_fusion)}")
print(f"   - Total colonnes: {len(df_fusion.columns)}")
print(f"   - Première colonne: {df_fusion.columns[0]}")

# ============================================
# STATISTIQUES PAR SOURCE
# ============================================
print(f"\n📊 RÉPARTITION PAR SOURCE:")
if 'source' in df_fusion.columns:
    sources = df_fusion['source'].value_counts()
    for source, count in sources.items():
        print(f"   - {source}: {count} annonces")

# ============================================
# ANALYSE DES COLONNES
# ============================================
print(f"\n📋 TAUX DE REMPLISSAGE (10 premières colonnes):")
for i, col in enumerate(df_fusion.columns[:10]):
    non_null = df_fusion[col].notna().sum()
    pct = (non_null / len(df_fusion)) * 100
    print(f"   {i+1:2}. {col}: {non_null}/{len(df_fusion)} ({pct:.1f}%)")

# ============================================
# SAUVEGARDE
# ============================================
print(f"\n💾 Sauvegarde du fichier fusionné...")

# Sauvegarder avec protection des guillemets
df_fusion.to_csv(fichier_sortie, index=False, encoding='utf-8-sig', quoting=csv.QUOTE_ALL)
print(f"✅ Fichier sauvegardé: {fichier_sortie}")

# ============================================
# VERSION ALLÉGÉE
# ============================================
print(f"\n📦 Création d'une version allégée...")

colonnes_essentielles = [
    'source', 'titre', 'prix', 'type_bien', 'type_annonce',
    'quartier', 'ville', 'surface_m2', 'nb_chambres', 'nb_sdb',
    'nb_salons', 'description', 'date_publication', 'vendeur',
    'caracteristiques'
]

colonnes_presentes = [col for col in colonnes_essentielles if col in df_fusion.columns]
df_light = df_fusion[colonnes_presentes].copy()
fichier_light = 'data_raw/dataset_light.csv'
df_light.to_csv(fichier_light, index=False, encoding='utf-8-sig', quoting=csv.QUOTE_ALL)
print(f"✅ Version allégée sauvegardée: {fichier_light}")

# ============================================
# APERÇU
# ============================================
print(f"\n👀 Aperçu des 10 premières lignes (premières colonnes):")
colonnes_apercu = df_fusion.columns[:6].tolist()  # 6 premières colonnes
print(df_fusion[colonnes_apercu].head(10).to_string())

print("\n🎉 Fusion terminée avec succès!")
print(f"📁 Fichiers générés:")
print(f"   - Complet (source en 1ère): {fichier_sortie}")
print(f"   - Light: {fichier_light}")