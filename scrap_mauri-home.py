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
print("🏠 SCRAPING MAURI-HOME.COM - VERSION SELENIUM")
print("="*60)

# Configuration du navigateur invisible (headless)
options = Options()
options.add_argument('--headless')  # Pour que le navigateur ne s'affiche pas
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--disable-blink-features=AutomationControlled')
options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')

print("🚀 Lancement du navigateur...")
driver = webdriver.Chrome(options=options)

try:
    url = "https://www.mauri-home.com/recherche"
    print(f"📄 Chargement de {url}...")
    
    driver.get(url)
    
    # Attendre que les annonces soient chargées (max 10 secondes)
    print("⏳ Attente du chargement des annonces...")
    wait = WebDriverWait(driver, 10)
    wait.until(EC.presence_of_element_located((By.TAG_NAME, "article")))
    
    # Petit pause pour être sûr que tout est chargé
    time.sleep(3)
    
    # Récupérer le HTML complet après exécution JavaScript
    html = driver.page_source
    soup = BeautifulSoup(html, 'html.parser')
    
    # Trouver toutes les annonces
    annonces = soup.find_all('article', class_='group')
    print(f"🔍 Trouvé {len(annonces)} annonces")
    
    if len(annonces) == 0:
        print("❌ Aucune annonce trouvée avec 'article'")
        # Debug: afficher les premières balises pour comprendre
        print("📋 Aperçu du HTML (premiers 500 caractères):")
        print(html[:500])
        exit()
    
    donnees = []
    
    for annonce in annonces:
        try:
            # ----- TITRE -----
            titre_elem = annonce.find('h3', class_=re.compile('text-lg.*font-bold'))
            titre = titre_elem.text.strip() if titre_elem else "Non spécifié"
            
            # ----- PRIX -----
            prix_elem = annonce.find('span', class_='text-primary')
            if prix_elem:
                prix_text = prix_elem.text.strip()
                prix_match = re.search(r'([\d\s]+)([A-Za-z]+)?(?:/(\w+))?', prix_text)
                if prix_match:
                    prix = prix_match.group(1).replace('\u202f', '').replace(' ', '') + " MRU"
                    periode = prix_match.group(3) if prix_match.group(3) else "mois"
                    type_annonce = "Location" if "mois" in periode.lower() else "Vente"
                else:
                    prix = prix_text
                    type_annonce = "Non spécifié"
            else:
                prix = "Non spécifié"
                type_annonce = "Non spécifié"
            
            # ----- QUARTIER -----
            quartier = "Non spécifié"
            # Cherche le span avec l'icône map
            map_icon = annonce.find('svg', class_=re.compile('map-pin'))
            if map_icon:
                parent = map_icon.find_parent('div')
                if parent:
                    spans = parent.find_all('span')
                    for span in spans:
                        if span.text.strip() and not span.find('svg'):
                            quartier = span.text.strip()
                            break
            
            # ----- CHAMBRES -----
            chambres = "Non spécifié"
            bed_icon = annonce.find('svg', class_=re.compile('bed'))
            if bed_icon:
                parent = bed_icon.find_parent('span')
                if parent:
                    chambres_text = parent.text.strip()
                    chambres_match = re.search(r'(\d+)', chambres_text)
                    chambres = chambres_match.group(1) if chambres_match else "Non spécifié"
            
            # ----- SALLES DE BAIN -----
            sdb = "Non spécifié"
            bath_icon = annonce.find('svg', class_=re.compile('bath'))
            if bath_icon:
                parent = bath_icon.find_parent('span')
                if parent:
                    sdb_text = parent.text.strip()
                    sdb_match = re.search(r'(\d+)', sdb_text)
                    sdb = sdb_match.group(1) if sdb_match else "Non spécifié"
            
            # ----- SURFACE -----
            surface = "Non spécifié"
            surface_icon = annonce.find('svg', class_=re.compile('maximize'))
            if surface_icon:
                parent = surface_icon.find_parent('span')
                if parent:
                    surface_text = parent.text.strip()
                    surface_match = re.search(r'(\d+)\s*m[²2]', surface_text)
                    surface = surface_match.group(1) + " m²" if surface_match else "Non spécifié"
            
            # ----- IMAGE -----
            img_elem = annonce.find('img')
            image_url = img_elem['src'] if img_elem and img_elem.has_attr('src') else "Non spécifié"
            
            # ----- URL -----
            url_annonce = "Non spécifié"
            link = annonce.find('a', href=True)
            if link and link['href']:
                if link['href'].startswith('/'):
                    url_annonce = "https://www.mauri-home.com" + link['href']
                elif link['href'].startswith('http'):
                    url_annonce = link['href']
            
            donnees.append({
                'source': 'mauri-home.com',
                'titre': titre,
                'prix': prix,
                'type_annonce': type_annonce,
                'ville': 'Nouakchott',
                'quartier': quartier,
                'nb_chambres': chambres,
                'nb_sdb': sdb,
                'surface_m2': surface,
                'date_publication': 'Non spécifiée',
                'date_scraping': datetime.now().strftime('%Y-%m-%d'),
                'url': url_annonce,
                'image_url': image_url,
            })
            
            print(f"  ✅ {titre[:40]}... - {prix} - {quartier}")
            
        except Exception as e:
            print(f"  ❌ Erreur: {e}")
            continue
    
    df = pd.DataFrame(donnees)
    
    if len(df) > 0:
        df.to_csv('data/raw/mauri_home.csv', index=False, encoding='utf-8-sig')
        print(f"\n💾 Sauvegardé {len(df)} annonces dans data/raw/mauri_home.csv")
        
        # Fusion avec les données existantes
        print("\n🔄 Fusion avec les données existantes...")
        if os.path.exists('data_raw.csv'):
            df_existant = pd.read_csv('data_raw.csv')
            df_final = pd.concat([df_existant, df], ignore_index=True)
            df_final.to_csv('data_raw.csv', index=False, encoding='utf-8-sig')
            print(f"✅ Fichier final mis à jour: data_raw.csv avec {len(df_final)} annonces")
        else:
            df.to_csv('data_raw.csv', index=False, encoding='utf-8-sig')
            print(f"✅ Nouveau fichier créé: data_raw.csv avec {len(df)} annonces")
            
    else:
        print("❌ Aucune donnée extraite")
        
finally:
    driver.quit()
    print("\n Scraping terminé!")