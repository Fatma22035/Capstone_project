import time
import pandas as pd
import re
from datetime import datetime
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup

print("="*60)
print("SCRAPING MENAZEL.ORG - VERSION SELENIUM")
print("="*60)

# Configuration du navigateur
options = Options()
# options.add_argument('--headless')  # Décommente pour exécuter en arrière-plan
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--disable-blink-features=AutomationControlled')
options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')

print("Lancement du navigateur...")
driver = webdriver.Chrome(options=options)

try:
    toutes_annonces = []
    
    # Scraper les pages 1 à 7
    for page in range(1, 8):
        url = f"https://menazel.org/fr/search?page={page}&sort=Newest"
        print(f"\nChargement page {page}/7: {url}")
        
        driver.get(url)
        
        # Attendre que les annonces soient chargées
        print("⏳ Attente du chargement des annonces...")
        time.sleep(5)
        
        # Faire défiler la page pour déclencher le chargement
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        
        # Récupérer le HTML après exécution JavaScript
        html = driver.page_source
        soup = BeautifulSoup(html, 'html.parser')
        
        # Chercher les annonces
        annonces = soup.find_all('div', class_='group')
        
        if not annonces:
            print(f" Aucune annonce trouvée page {page}")
            # Afficher un extrait du HTML pour debug
            print(" Extrait du HTML:")
            print(html[:500])
            continue
        
        print(f"🔍 Trouvé {len(annonces)} annonces sur cette page")
        
        for annonce in annonces:
            try:
                # URL et ID
                link = annonce.find('a', href=True)
                if link and link['href'].startswith('/fr/property/'):
                    url_annonce = "https://menazel.org" + link['href']
                    id_unique = link['href'].split('/')[-1]
                else:
                    continue
                
                # Titre
                titre_elem = annonce.find('a', class_='text-lg')
                titre = titre_elem.text.strip() if titre_elem else "Non spécifié"
                
                # Prix
                prix_span = annonce.find('span', attrs={'dir': 'ltr'})
                if prix_span:
                    prix_texte = prix_span.text.strip()
                    prix_texte = re.sub(r'[^\d]', '', prix_texte)
                    prix = f"{prix_texte} MRU"
                else:
                    prix = "Non spécifié"
                
                # Type de bien
                type_bien = "Non spécifié"
                if 'appartement' in titre.lower():
                    type_bien = 'Appartement'
                elif 'villa' in titre.lower():
                    type_bien = 'Villa'
                elif 'terrain' in titre.lower():
                    type_bien = 'Terrain'
                elif 'studio' in titre.lower():
                    type_bien = 'Studio'
                
                # Chambres
                nb_chambres = "Non spécifié"
                chambres_i = annonce.find('i', class_='mdi-door-sliding')
                if chambres_i:
                    span = chambres_i.find_next('span')
                    if span:
                        nb_chambres = span.text.strip()
                
                # Salles de bain
                nb_sdb = "Non spécifié"
                sdb_i = annonce.find('i', class_='mdi-shower')
                if sdb_i:
                    span = sdb_i.find_next('span')
                    if span:
                        nb_sdb = span.text.strip()
                
                # Image
                image_url = "Non spécifié"
                img = annonce.find('img')
                if img and img.has_attr('src'):
                    src = img['src']
                    if src.startswith('http'):
                        image_url = src
                    else:
                        image_url = "https://menazel.org" + src
                
                # Contact
                telephone = "Non spécifié"
                whatsapp = "Non spécifié"
                for link in annonce.find_all('a', href=True):
                    href = link['href']
                    if href.startswith('tel:'):
                        telephone = href.replace('tel:', '')
                    elif 'wa.me' in href:
                        whatsapp = href
                
                # Quartier (dans le titre)
                quartier = "Non spécifié"
                for q in ['Tevragh Zeina', 'Arafat', 'Dar Naim', 'Teyarett', 'Toujounine']:
                    if q in titre:
                        quartier = q
                        break
                
                # Surface
                surface_m2 = "Non spécifié"
                surface_match = re.search(r'(\d+)\s*m[²2]', titre)
                if surface_match:
                    surface_m2 = surface_match.group(1) + " m²"
                
                toutes_annonces.append({
                    'source': 'menazel.org',
                    'url': url_annonce,
                    'titre': titre,
                    'prix': prix,
                    'type_bien': type_bien,
                    'quartier': quartier,
                    'surface_m2': surface_m2,
                    'vendeur': 'Non spécifié',
                    'date_publication': 'Non spécifiée',
                    'nb_images': '1',
                    'image_url': image_url,
                    'date_scraping': datetime.now().strftime('%Y-%m-%d'),
                    'ville': 'Nouakchott',
                    'nb_chambres': nb_chambres,
                    'nb_sdb': nb_sdb,
                    'description': 'Non spécifié',
                    'id_unique': id_unique,
                    'telephone': telephone,
                    'whatsapp': whatsapp,
                })
                
                print(f"  ✅ {titre[:30]}... - {prix}")
                
            except Exception as e:
                print(f"  ❌ Erreur: {e}")
                continue
        
        # Pause entre les pages
        if page < 7:
            print(f"Pause avant page {page+1}...")
            time.sleep(3)
    
    # Sauvegarde
    df = pd.DataFrame(toutes_annonces)
    
    if len(df) > 0:
        df.to_csv('data_raw/menazel.csv', index=False, encoding='utf-8-sig')
        print(f"\n Sauvegardé {len(df)} annonces")
        
        # Fusion avec data_raw.csv
        if os.path.exists('data_raw/final_data_raw.csv'):
            df_existant = pd.read_csv('data_raw/final_data_raw.csv')
            df_combined = pd.concat([df_existant, df], ignore_index=True)
            df_combined = df_combined.drop_duplicates(subset=['url'], keep='last')
            df_combined.to_csv('data_raw/final_data_raw.csv', index=False)
            print(f"✅ Fichier final mis à jour: {len(df_combined)} annonces")
        else:
            df.to_csv('data_raw/final_data_raw.csv', index=False)
            print(f"✅ Nouveau fichier final créé: {len(df)} annonces")
    else:
        print("❌ Aucune donnée récupérée")
        
finally:
    driver.quit()
    print("\n Scraping terminé!")