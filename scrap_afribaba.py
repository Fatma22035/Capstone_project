import os
from bs4 import BeautifulSoup
import pandas as pd
import re
from datetime import datetime

print("="*60)
print("📁 PARSING AFRIBABA - VERSION AMÉLIORÉE")
print("="*60)

def clean_text(text):
    """Nettoie le texte en enlevant les espaces multiples et retours à la ligne"""
    if not text:
        return "Non spécifié"
    # Remplacer les multiples espaces par un seul espace
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def extract_ville(annonce_text):
    """Extrait proprement la ville"""
    # Cherche Nouakchott ou Nouadhibou
    match = re.search(r'(Nouakchott|Nouadhibou|Nouâdhibou)', annonce_text, re.I)
    return match.group(1) if match else "Nouakchott"

def extract_date(date_text):
    """Nettoie la date"""
    if not date_text or date_text == "Non spécifiée":
        return "Non spécifiée"
    return clean_text(date_text)

def extract_chambres(annonce_text):
    """Extrait le nombre de chambres"""
    # Cherche des patterns comme "3 Chambres" ou "3 chambres"
    patterns = [
        r'(\d+)\s*(?:chambres?|pi[èe]ces?)\b',
        r'chambres?\s*[:]?\s*(\d+)',
    ]
    for pattern in patterns:
        match = re.search(pattern, annonce_text, re.I)
        if match:
            return match.group(1)
    return "Non spécifié"

def extract_sdb(annonce_text):
    """Extrait le nombre de salles de bain"""
    patterns = [
        r'(\d+)\s*(?:salles? de bain|sdb|bains?)\b',
        r'salles? de bain\s*[:]?\s*(\d+)',
    ]
    for pattern in patterns:
        match = re.search(pattern, annonce_text, re.I)
        if match:
            return match.group(1)
    return "Non spécifié"

def extract_type_bien(titre, annonce_text):
    """Détermine le type de bien"""
    texte_complet = (titre + " " + annonce_text).lower()
    
    if 'appartement' in texte_complet:
        return 'Appartement'
    elif 'villa' in texte_complet:
        return 'Villa'
    elif 'maison' in texte_complet:
        return 'Maison'
    elif 'duplex' in texte_complet:
        return 'Duplex'
    elif 'terrain' in texte_complet:
        return 'Terrain'
    elif 'studio' in texte_complet:
        return 'Studio'
    else:
        return "Non spécifié"

def extract_surface(annonce_text):
    """Extrait la surface en m²"""
    patterns = [
        r'(\d+)\s*m[²2]',
        r'surface\s*[:]?\s*(\d+)\s*m',
    ]
    for pattern in patterns:
        match = re.search(pattern, annonce_text, re.I)
        if match:
            return match.group(1) + " m²"
    return "Non spécifié"

def extract_description(annonce_text):
    """Nettoie la description"""
    # Enlève les parties qui ne sont pas la description
    lignes = annonce_text.split('\n')
    description = ""
    for ligne in lignes:
        if (len(ligne.strip()) > 20 and 
            'Contacter' not in ligne and 
            'badge' not in ligne and
            'Offre' not in ligne):
            description += " " + ligne.strip()
    
    if description:
        return clean_text(description)
    return "Non spécifié"

def parse_afribaba_html(html_file, page_num):
    """Parse un fichier HTML sauvegardé d'Afribaba"""
    
    print(f"\n📄 Parsing page {page_num}: {html_file}")
    
    if not os.path.exists(html_file):
        print(f"❌ Fichier non trouvé: {html_file}")
        return []
    
    with open(html_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    soup = BeautifulSoup(content, 'html.parser')
    
    # Trouver toutes les annonces
    annonces = soup.find_all('div', class_='card')
    
    print(f"🔍 Trouvé {len(annonces)} annonces")
    
    donnees = []
    
    for annonce in annonces:
        try:
            # ----- TITRE ET URL -----
            titre_elem = annonce.find('h3', class_='card-title')
            if titre_elem and titre_elem.find('a'):
                titre = clean_text(titre_elem.find('a').text)
                url_annonce = titre_elem.find('a')['href']
                if url_annonce.startswith('//'):
                    url_annonce = 'https:' + url_annonce
            else:
                titre = "Non spécifié"
                url_annonce = "Non spécifié"
            
            # ----- PRIX -----
            prix_elem = annonce.find('span', class_='badge-primary')
            if prix_elem:
                prix = clean_text(prix_elem.text)
            else:
                price_match = re.search(r'(\d[\d\s]*\d*\s*(?:MRO|UM))', annonce.get_text())
                prix = clean_text(price_match.group(1)) if price_match else "Non spécifié"
            
            # ----- DATE DE PUBLICATION -----
            date_elem = annonce.find('span', class_='date')
            date_publication = extract_date(date_elem.text) if date_elem else "Non spécifiée"
            
            # ----- TEXTE COMPLET POUR ANALYSE -----
            texte_annonce = annonce.get_text(" ", strip=True)
            
            # ----- VILLE -----
            ville = extract_ville(texte_annonce)
            
            # ----- TYPE DE BIEN -----
            type_bien = extract_type_bien(titre, texte_annonce)
            
            # ----- CHAMBRES -----
            nb_chambres = extract_chambres(texte_annonce)
            
            # ----- SALLES DE BAIN -----
            nb_sdb = extract_sdb(texte_annonce)
            
            # ----- SURFACE -----
            surface = extract_surface(texte_annonce)
            
            # ----- DESCRIPTION PROPRE -----
            description = extract_description(texte_annonce)
            
            # ----- FILTRE: GARDER SEULEMENT L'IMMOBILIER -----
            mots_cles_immobilier = ['appartement', 'villa', 'maison', 'duplex', 'terrain', 'studio', 
                                   'chambre', 'bureau', 'local', 'immeuble', 'logement']
            
            texte_check = (titre + " " + type_bien + " " + description).lower()
            est_immobilier = any(mot in texte_check for mot in mots_cles_immobilier)
            
            # Exclure les services non immobiliers
            services_exclus = ['ingénieur', 'bâtiment', 'chantier', 'construction', 'agence']
            est_service = any(mot in texte_check for mot in services_exclus)
            
            if not est_immobilier or est_service:
                print(f"  ⚠️ Exclu (non immobilier): {titre[:30]}")
                continue
            
            donnees.append({
                'source': 'afribaba.com',
                'titre': titre,
                'prix': prix,
                'ville': ville,
                'quartier': "Non spécifié",  # À extraire plus tard
                'type_bien': type_bien,
                'nb_chambres': nb_chambres,
                'nb_sdb': nb_sdb,
                'surface_m2': surface,
                'date_publication': date_publication,
                'date_scraping': datetime.now().strftime('%Y-%m-%d'),
                'url': url_annonce,
                'description': description,
                'page': page_num
            })
            
            print(f"  ✅ {titre[:30]}... - {prix} - {type_bien} - {nb_chambres} ch")
            
        except Exception as e:
            print(f"  ❌ Erreur: {e}")
            continue
    
    return donnees

# Traiter les 3 fichiers
toutes_annonces = []

for i in range(1, 4):
    html_file = f'data/raw/Immobilier Location - Vente Page {i} - Petites annonces Mauritanie.html'
    annonces = parse_afribaba_html(html_file, i)
    toutes_annonces.extend(annonces)

# Créer le DataFrame
if toutes_annonces:
    df = pd.DataFrame(toutes_annonces)
    
    # Sauvegarde
    df.to_csv('data/raw/afribaba_propre.csv', index=False, encoding='utf-8-sig')
    
    print("\n" + "="*60)
    print("📊 RÉSULTAT - AFRIBABA NETTOYÉ")
    print("="*60)
    print(f"✅ Total annonces immobilières: {len(df)}")
    print(f"\n📋 Répartition par type de bien:")
    print(df['type_bien'].value_counts())
    print(f"\n📋 Répartition par ville:")
    print(df['ville'].value_counts())
    print(f"\n📋 Statistiques:")
    print(f"   - Annonces avec chambres: {df[df['nb_chambres'] != 'Non spécifié'].shape[0]}")
    print(f"   - Annonces avec surface: {df[df['surface_m2'] != 'Non spécifié'].shape[0]}")
    print(f"   - Annonces avec date: {df[df['date_publication'] != 'Non spécifiée'].shape[0]}")
    
    print("\n👀 Aperçu des données nettoyées:")
    print(df[['titre', 'prix', 'type_bien', 'nb_chambres', 'surface_m2']].head(10))
    
    # Fusion avec les données existantes
    print("\n🔄 Fusion avec les données existantes...")
    
    # Charger wassit et lagence
    fichiers_existants = []
    if os.path.exists('data/raw/wassit_immobilier.csv'):
        df_wassit = pd.read_csv('data/raw/wassit_immobilier.csv')
        fichiers_existants.append(df_wassit)
        print(f"✅ wassit: {len(df_wassit)} annonces")
    
    if os.path.exists('data/raw/lagence.csv'):
        df_lagence = pd.read_csv('data/raw/lagence.csv')
        fichiers_existants.append(df_lagence)
        print(f"✅ lagence: {len(df_lagence)} annonces")
    
    # Fusionner tout
    fichiers_existants.append(df)
    df_final = pd.concat(fichiers_existants, ignore_index=True, sort=False)
    
    # Sauvegarder le final
    df_final.to_csv('data_raw.csv', index=False, encoding='utf-8-sig')
    print(f"\n✅ Fichier final: data_raw.csv avec {len(df_final)} annonces")
    
else:
    print("❌ Aucune donnée")