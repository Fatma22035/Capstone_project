import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import re
from datetime import datetime
import os

print("="*60)
print("SCRAPING L'AGENCE MR - IMMOBILIER MAURITANIE")
print("="*60)

# Créer le dossier data/raw s'il n'existe pas
os.makedirs('data/raw', exist_ok=True)

# Configuration
headers = {
    'User-Agent': 'MauritaniaHousingProject/1.0 (etudiante) - Projet academique'
}

# URLs des pages d'annonces
urls = [
    "https://lagence-mr.com/",
    "https://lagence-mr.com/page/2/",
    "https://lagence-mr.com/page/3/",  
    "https://lagence-mr.com/page/4/", 
    "https://lagence-mr.com/page/5/",
    "https://lagence-mr.com/page/6/",
    "https://lagence-mr.com/page/7/",
    "https://lagence-mr.com/page/8/",
    "https://lagence-mr.com/page/9/", 
    "https://lagence-mr.com/page/10/",
    "https://lagence-mr.com/page/11/",
    "https://lagence-mr.com/page/12/",
    "https://lagence-mr.com/page/13/",
    "https://lagence-mr.com/page/14/",
]

def clean_price(price_text):
    """Nettoie le texte du prix"""
    if not price_text:
        return "Non spécifié"
    price_text = price_text.strip()
    match = re.search(r'(\d+[\s\d]*)\s*([A-Za-z]+)', price_text)
    if match:
        numbers = match.group(1).replace(' ', '')
        currency = match.group(2)
        return f"{numbers} {currency}"
    return price_text

def extract_date_from_text(text):
    """Extrait une date si présente dans le texte"""
    if not text:
        return "Non spécifiée"

    # Formats de date possibles
    patterns = [
        r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',  # 12/02/2026 ou 12-02-2026
        r'(\d{4}[/-]\d{1,2}[/-]\d{1,2})',     # 2026-02-12
        r'(\d{1,2}\s+(janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)\s+\d{4})',  # 12 février 2026
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.I)
        if match:
            return match.group(1)
    
    return "Non spécifiée"

def scrape_lagence_mr():
    """Fonction principale de scraping"""
    
    toutes_annonces = []
    
    for page_num, url in enumerate(urls, 1):
        print(f"\n Scraping page {page_num}: {url}")
        
        try:
            response = requests.get(url, headers=headers, timeout=30)
            time.sleep(3)
            
            if response.status_code != 200:
                print(f" Erreur page {page_num}: {response.status_code}")
                continue
                
            soup = BeautifulSoup(response.content, 'html.parser')
            annonces = soup.find_all('div', class_=re.compile('jet-listing-grid__item'))
            
            print(f"🔍 Trouvé {len(annonces)} annonces sur cette page")
            
            for annonce in annonces:
                try:
                    # ----- TITRE -----
                    titre_elem = annonce.find('h5', class_='elementor-heading-title')
                    titre = titre_elem.text.strip() if titre_elem else "Non spécifié"
                    
                    # ----- PRIX -----
                    prix_elem = annonce.find('p', class_='elementor-heading-title')
                    prix = clean_price(prix_elem.text) if prix_elem else "Non spécifié"
                    
                    # ----- TYPE D'ANNONCE -----
                    type_elem = annonce.find('span', class_='elementor-icon-list-text')
                    type_annonce = type_elem.text.strip() if type_elem else "Non spécifié"
                    
                    # ----- LOCALISATION / QUARTIER -----
                    quartier = "Non spécifié"
                    icon_loc = annonce.find('i', class_='fa-map-marker-alt')
                    if icon_loc:
                        li_parent = icon_loc.find_parent('li')
                        if li_parent:
                            span_loc = li_parent.find('span', class_='elementor-icon-list-text')
                            quartier = span_loc.text.strip() if span_loc else "Non spécifié"
                    
                    # ----- NOMBRE DE CHAMBRES -----
                    nb_chambres = "Non spécifié"
                    icon_bed = annonce.find('i', class_='fa-bed')
                    if icon_bed:
                        li_parent = icon_bed.find_parent('li')
                        if li_parent:
                            span_bed = li_parent.find('span', class_='elementor-icon-list-text')
                            if span_bed:
                                chambres_text = span_bed.text.strip()
                                chambres = re.search(r'(\d+)', chambres_text)
                                nb_chambres = chambres.group(1) if chambres else "Non spécifié"
                    
                    # ----- SURFACE -----
                    surface = "Non spécifié"
                    icon_ruler = annonce.find('i', class_='fa-ruler-combined')
                    if icon_ruler:
                        li_parent = icon_ruler.find_parent('li')
                        if li_parent:
                            span_ruler = li_parent.find('span', class_='elementor-icon-list-text')
                            if span_ruler and span_ruler.text.strip():
                                surface = span_ruler.text.strip()
                    
                    # ----- URL DE L'ANNONCE -----
                    url_elem = annonce.find('a', class_='jet-engine-listing-overlay-link')
                    url_annonce = url_elem['href'] if url_elem and url_elem.has_attr('href') else "Non spécifié"
                    
                    # ----- IMAGE -----
                    image_url = "Non spécifié"
                    style_elem = annonce.find('div', style=re.compile('background-image'))
                    if style_elem and style_elem.has_attr('style'):
                        style_text = style_elem['style']
                        match = re.search(r'url\(["\']?([^"\')]+)["\']?\)', style_text)
                        if match:
                            image_url = match.group(1)
                    
                    # ----- ID UNIQUE -----
                    post_id = annonce.get('data-post-id', 'Non spécifié')
                    
                    # ----- DATE DE PUBLICATION -----
                    # Cherche la date dans différents endroits
                    date_publication = "Non spécifiée"
                    
                    # 1. Cherche dans un élément avec classe contenant "date"
                    date_elem = annonce.find(class_=re.compile('date', re.I))
                    if date_elem:
                        date_publication = extract_date_from_text(date_elem.text)
                    
                    # 2. Cherche dans les métadonnées si pas trouvé
                    if date_publication == "Non spécifiée":
                        # Regarde dans le texte général de l'annonce
                        annonce_text = annonce.get_text()
                        date_publication = extract_date_from_text(annonce_text)
                    
                    # 3. Si toujours pas trouvé, cherche dans l'URL ou l'ID
                    if date_publication == "Non spécifiée" and post_id != "Non spécifié":
                        # Parfois l'ID contient une date (ex: 5336 pourrait être 2025-33-6? Non fiable)
                        pass
                    
                    # Créer le dictionnaire avec TOUTES les données
                    annonce_data = {
                        # Identifiants
                        'id_unique': post_id,
                        'source': 'lagence-mr.com',
                        
                        # Infos principales
                        'titre': titre,
                        'prix': prix,
                        'type_annonce': type_annonce,
                        'quartier': quartier,
                        'ville': 'Nouakchott',
                        'nb_chambres': nb_chambres,
                        'surface_m2': surface,
                        
                        # Dates
                        'date_publication': date_publication,
                        'date_scraping': datetime.now().strftime('%Y-%m-%d'),
                        
                        # URLs et média
                        'url': url_annonce,
                        'image_url': image_url,
                        
                        # Autres (pour compatibilité avec wassit)
                        'nb_vues': 'Non spécifié',  # Pour wassit
                        'description': 'Non spécifié',
                        'nb_pieces_total': 'Non spécifié',
                        'nb_sdb': 'Non spécifié',
                        'meuble': 'Non spécifié',
                    }
                    
                    toutes_annonces.append(annonce_data)
                    print(f"  ✅ {titre[:30]}... - {prix} - Date: {date_publication[:20]}")
                    
                except Exception as e:
                    print(f"  ❌ Erreur sur une annonce: {e}")
                    continue
                    
        except Exception as e:
            print(f"❌ Erreur sur la page {page_num}: {e}")
            continue
    
    return pd.DataFrame(toutes_annonces)

# ============================================
# FONCTION POUR CHARGER LES DONNÉES EXISTANTES
# ============================================

def charger_donnees_existantes():
    """Charge les données de wassit si le fichier existe"""
    fichier_wassit = 'data_raw.csv'
    
    if os.path.exists(fichier_wassit):
        print(f"\n📂 Chargement des données wassit existantes...")
        df_wassit = pd.read_csv(fichier_wassit)
        print(f"✅ {len(df_wassit)} annonces wassit chargées")
        return df_wassit
    else:
        print(f"\n Fichier non trouvé: {fichier_wassit}")
        return pd.DataFrame()

# ============================================
# EXÉCUTION PRINCIPALE
# ============================================

print("\n DÉBUT DU SCRAPING LAGENCE...")
df_lagence = scrape_lagence_mr()

if len(df_lagence) > 0:
    # Sauvegarde individuelle de lagence
    df_lagence.to_csv('data/raw/lagence.csv', index=False, encoding='utf-8-sig')
    print(f"\n lagence.csv sauvegardé avec {len(df_lagence)} annonces")
    
    # Charger les données wassit existantes
    df_wassit = charger_donnees_existantes()
    
    # COMBINER LES DEUX DATAFRAMES
    print("\n🔄Fusion des données...")
    
    if len(df_wassit) > 0:
        df_final = pd.concat([df_wassit, df_lagence], ignore_index=True, sort=False)
        print(f"✅ Fusion réussie: {len(df_wassit)} wassit + {len(df_lagence)} lagence = {len(df_final)} total")
    else:
        df_final = df_lagence
        print(f"✅ Seulement lagence: {len(df_final)} annonces")
    
    # Sauvegarder le fichier final UNIQUE
    fichier_final = 'data_raw.csv'
    df_final.to_csv(fichier_final, index=False, encoding='utf-8-sig')
    
    print("\n" + "="*60)
    print("RÉSULTAT FINAL - FUSION COMPLÈTE")
    print("="*60)
    print(f" Fichier final: {fichier_final}")
    print(f" Total annonces: {len(df_final)}")
    print(f"\n Répartition par source:")
    print(df_final['source'].value_counts())
    
    print(f"\n Colonnes disponibles ({len(df_final.columns)}):")
    for col in df_final.columns:
        non_null = df_final[col].notna().sum()
        pct = (non_null/len(df_final))*100
        print(f"   - {col}: {non_null}/{len(df_final)} ({pct:.1f}%)")
    
    print(f"\n Dates de publication trouvées:")
    dates_trouvees = df_final[df_final['date_publication'] != 'Non spécifiée']
    print(f"   - lagence: {len(dates_trouvees[dates_trouvees['source']=='lagence-mr.com'])} dates")
    if 'wassit.info' in df_final['source'].values:
        print(f"   - wassit: {len(dates_trouvees[dates_trouvees['source']=='wassit.info'])} dates")
    
    print("\n👀 Aperçu des 3 premières annonces:")
    print(df_final[['source', 'titre', 'prix', 'date_publication']].head(3))
    
else:
    print("❌ Aucune donnée lagence récupérée!")

print("\n🎉 Scraping terminé!")