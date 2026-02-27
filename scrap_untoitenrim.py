import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
from datetime import datetime
import os
import time
import csv  # ← Ajout pour un meilleur contrôle du CSV

print("="*60)
print("🏠 SCRAPING UNTOITENRIM.COM - VERSION CORRIGÉE")
print("="*60)

# Créer le dossier data_raw s'il n'existe pas
os.makedirs('data_raw', exist_ok=True)

# Configuration
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7',
}

def nettoyer_texte(texte):
    """Nettoie le texte pour le CSV (enlève les retours à la ligne et les virgules problématiques)"""
    if not texte or texte == "Non spécifié":
        return "Non spécifié"
    # Remplacer les retours à la ligne par des espaces
    texte = texte.replace('\n', ' ').replace('\r', ' ')
    # Remplacer les virgules par des points-virgules pour ne pas casser le CSV
    texte = texte.replace(',', ';')
    # Supprimer les guillemets doubles
    texte = texte.replace('"', "'")
    # Supprimer les espaces multiples
    texte = re.sub(r'\s+', ' ', texte)
    return texte.strip()

def extraire_infos_annonce(url_detail):
    """Extrait les informations de la page de détail"""
    try:
        response = requests.get(url_detail, headers=headers, timeout=30)
        time.sleep(2)
        
        if response.status_code != 200:
            return {}
        
        soup = BeautifulSoup(response.content, 'html.parser')
        infos = {}
        
        # ----- CONTACT (Vendeur et Téléphone) -----
        contact_card = soup.find('div', class_='card shadow-sm sticky-top')
        if contact_card:
            # Vendeur
            vendeur_p = contact_card.find('p', class_='mb-1')
            if vendeur_p:
                vendeur_strong = vendeur_p.find('strong')
                if vendeur_strong:
                    infos['vendeur'] = nettoyer_texte(vendeur_strong.text)
            
            # Téléphone
            tel_p = contact_card.find('p', string=re.compile(r'\d+'))
            if tel_p:
                tel_match = re.search(r'(\d+)', tel_p.text)
                if tel_match:
                    infos['telephone'] = tel_match.group(1)
        
        # ----- DESCRIPTION (détaillée) -----
        desc_div = soup.find('div', class_='mb-4')
        if desc_div:
            desc_p = desc_div.find('p', class_='text-muted')
            if desc_p:
                infos['description_detail'] = nettoyer_texte(desc_p.text)
        
        return infos
        
    except Exception as e:
        print(f"❌ Erreur détail {url_detail}: {e}")
        return {}

def scrape_untoitenrim():
    """Scrape toutes les annonces de untoitenrim.com"""
    
    url = "https://untoitenrim.com/annonces.php"
    print(f"📄 Scraping: {url}")
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        time.sleep(3)
        
        if response.status_code != 200:
            print(f"❌ Erreur: {response.status_code}")
            return pd.DataFrame()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Trouver toutes les annonces
        annonces = soup.find_all('div', class_='col-md-6 col-lg-4')
        
        print(f"🔍 Trouvé {len(annonces)} annonces")
        
        donnees = []
        
        for i, annonce in enumerate(annonces, 1):
            try:
                # ----- URL DE L'ANNONCE -----
                link = annonce.find('a', href=True)
                if link and link['href'].startswith('annonce_detail.php'):
                    url_detail = "https://untoitenrim.com/" + link['href']
                    id_match = re.search(r'id=(\d+)', link['href'])
                    id_unique = id_match.group(1) if id_match else "Non spécifié"
                else:
                    url_detail = "Non spécifié"
                    id_unique = "Non spécifié"
                
                # ----- TITRE -----
                titre_elem = annonce.find('h5', class_='card-title')
                titre = nettoyer_texte(titre_elem.text) if titre_elem else "Non spécifié"
                
                # ----- PRIX -----
                prix_elem = annonce.find('span', class_='fw-bold text-success')
                prix = nettoyer_texte(prix_elem.text) if prix_elem else "Non spécifié"
                
                # ----- STATUT -----
                statut_elem = annonce.find('span', class_='badge')
                statut = nettoyer_texte(statut_elem.text) if statut_elem else "Non spécifié"
                
                # ----- DESCRIPTION (aperçu) -----
                desc_elem = annonce.find('p', class_='card-text text-truncate')
                description = nettoyer_texte(desc_elem.text) if desc_elem else "Non spécifié"
                
                # ----- IMAGE -----
                img_elem = annonce.find('img', class_='card-img-top')
                if img_elem and img_elem.has_attr('src'):
                    image_url = "https://untoitenrim.com/" + img_elem['src']
                else:
                    image_url = "Non spécifié"
                
                # ----- TYPE DE BIEN -----
                type_bien = "Non spécifié"
                titre_lower = titre.lower()
                if 'appartement' in titre_lower:
                    type_bien = 'Appartement'
                elif 'villa' in titre_lower:
                    type_bien = 'Villa'
                elif 'maison' in titre_lower:
                    type_bien = 'Maison'
                elif 'terrain' in titre_lower:
                    type_bien = 'Terrain'
                elif 'studio' in titre_lower:
                    type_bien = 'Studio'
                elif 'magasin' in titre_lower or 'local' in titre_lower:
                    type_bien = 'Local commercial'
                
                # ----- TYPE D'ANNONCE -----
                type_annonce = "Non spécifié"
                if 'louer' in titre_lower or 'location' in titre_lower:
                    type_annonce = 'Location'
                elif 'vente' in titre_lower:
                    type_annonce = 'Vente'
                
                # ----- QUARTIER -----
                quartier = "Non spécifié"
                quartiers_connus = ['Tevragh Zeina', 'Cité Plage', 'Dar Naim', 'Ilot K', 'Arafat', 'Teyarett', 'Toujounine']
                for q in quartiers_connus:
                    if q.lower() in titre_lower:
                        quartier = q
                        break
                
                # ----- SURFACE -----
                surface_m2 = "Non spécifié"
                surface_match = re.search(r'(\d+)\s*m[²2]', titre + " " + description)
                if surface_match:
                    surface_m2 = surface_match.group(1) + " m²"
                
                # ----- CHAMBRES -----
                nb_chambres = "Non spécifié"
                chambres_match = re.search(r'(\d+)\s*chambres?', description, re.I)
                if chambres_match:
                    nb_chambres = chambres_match.group(1)
                
                # ----- SALLES DE BAIN -----
                nb_sdb = "Non spécifié"
                sdb_match = re.search(r'(\d+)\s*(?:douche|salle de bain|toilette)', description, re.I)
                if sdb_match:
                    nb_sdb = sdb_match.group(1)
                
                # Aller chercher les détails supplémentaires
                print(f"  🔍 Récupération détails pour annonce {i}...")
                details = extraire_infos_annonce(url_detail) if url_detail != "Non spécifié" else {}
                
                # Créer l'annonce avec TOUS les champs
                annonce_data = {
                    'source': 'untoitenrim.com',
                    'titre': titre,
                    'prix': prix,
                    'type_bien': type_bien,
                    'quartier': quartier,
                    'surface_m2': surface_m2,
                    'point_repere': 'Non spécifié',
                    'vendeur': details.get('vendeur', 'Non spécifié'),
                    'date_publication': 'Non spécifiée',
                    'nb_images': '1',
                    'image_url': image_url,
                    'date_scraping': datetime.now().strftime('%Y-%m-%d'),
                    'ville': 'Nouakchott',
                    'nb_chambres': nb_chambres,
                    'nb_sdb': nb_sdb,
                    'description': description,
                    'page': '1',
                    'id_unique': id_unique,
                    'type_annonce': type_annonce,
                    'nb_vues': statut,
                    'nb_pieces_total': 'Non spécifié',
                    'meuble': 'Non spécifié',
                    'telephone': details.get('telephone', 'Non spécifié'),
                }
                
                donnees.append(annonce_data)
                print(f"  ✅ {titre[:40]}... - {prix}")
                
            except Exception as e:
                print(f"  ❌ Erreur sur annonce {i}: {e}")
                continue
        
        # Créer le DataFrame
        df = pd.DataFrame(donnees)
        
        # Sauvegarder avec quoting pour protéger les descriptions
        df.to_csv('data_raw/untoitenrim.csv', 
                  index=False, 
                  encoding='utf-8-sig',
                  quoting=csv.QUOTE_ALL,  # ← Met TOUS les champs entre guillemets
                  escapechar='\\')         # ← Échappe les caractères spéciaux
        
        return df
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return pd.DataFrame()

# Exécution
df_untoitenrim = scrape_untoitenrim()

if len(df_untoitenrim) > 0:
    print(f"\n💾 Sauvegardé {len(df_untoitenrim)} annonces dans data_raw/untoitenrim.csv")
    
    # Statistiques
    print(f"\n📊 STATISTIQUES:")
    print(f"   - Total annonces: {len(df_untoitenrim)}")
    print(f"   - Types de biens: {df_untoitenrim['type_bien'].unique()}")
    print(f"   - Types d'annonces: {df_untoitenrim['type_annonce'].unique()}")
    
    # Fusion avec le fichier final
    print("\n🔄 Fusion avec les données existantes...")
    
    fichier_final = 'data_raw/final_data_raw.csv'
    
    if os.path.exists(fichier_final):
        df_final = pd.read_csv(fichier_final)
        print(f"📂 Fichier final existant: {len(df_final)} lignes")
        
        # Aligner les colonnes
        for col in df_final.columns:
            if col not in df_untoitenrim.columns:
                df_untoitenrim[col] = "Non spécifié"
        
        df_untoitenrim_aligné = df_untoitenrim[df_final.columns]
        df_combined = pd.concat([df_final, df_untoitenrim_aligné], ignore_index=True)
        df_combined = df_combined.drop_duplicates(subset=['id_unique', 'source'], keep='first')
        
        # Sauvegarder avec quoting
        df_combined.to_csv(fichier_final, 
                          index=False, 
                          encoding='utf-8-sig',
                          quoting=csv.QUOTE_ALL,
                          escapechar='\\')
        
        print(f"✅ Fichier final mis à jour: {len(df_combined)} annonces")
    else:
        df_untoitenrim.to_csv(fichier_final, 
                             index=False, 
                             encoding='utf-8-sig',
                             quoting=csv.QUOTE_ALL,
                             escapechar='\\')
        print(f"✅ Nouveau fichier final créé: {len(df_untoitenrim)} annonces")
    
    print("\n👀 Aperçu:")
    print(df_untoitenrim[['titre', 'prix', 'type_bien', 'quartier']].head(10))
    
else:
    print("❌ Aucune donnée récupérée")