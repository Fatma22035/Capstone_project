import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import pandas as pd
import re
from datetime import datetime
import os
import csv

print("="*60)
print("SCRAPING ELMINASSA.COM - VERSION FINALE")
print("="*60)

# Configuration du navigateur
options = Options()
options.add_argument('--headless')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--disable-blink-features=AutomationControlled')
options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')

print(" Lancement du navigateur...")
driver = webdriver.Chrome(options=options)

try:
    url = "https://www.elminassa.com/list"
    print(f"Chargement de {url}...")
    
    driver.get(url)
    time.sleep(5)
    
    # Gérer la popup de localisation si elle apparaît
    try:
        for texte in ['حسنا', 'OK', 'Fermer']:
            try:
                btn = driver.find_element(By.XPATH, f"//button[contains(text(), '{texte}')]")
                btn.click()
                print(f"✅ Popup fermée")
                time.sleep(2)
                break
            except:
                continue
    except:
        pass
    
    # CLIQUER SUR "تحميل المزيد" (Charger plus) jusqu'à épuisement
    clics = 0
    while True:
        try:
            # Chercher le bouton de chargement
            load_more = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'تحميل المزيد')]"))
            )
            driver.execute_script("arguments[0].scrollIntoView(true);", load_more)
            time.sleep(1)
            load_more.click()
            clics += 1
            print(f" Clic {clics} - تحميل المزيد")
            time.sleep(3)
        except:
            print(f"✅ Plus de bouton après {clics} clics")
            break
    
    # Récupérer le HTML final
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    
    # Trouver TOUS les conteneurs d'annonces (swiper-slide)
    # Chaque annonce est dans un div avec classe 'swiper-slide'
    annonces = soup.find_all('div', class_='swiper-slide')
    
    print(f"\n🔍 {len(annonces)} annonces trouvées")
    
    donnees = []
    
    for i, annonce in enumerate(annonces):
        try:
            # ----- PRIX -----
            prix_elem = annonce.find('span', class_='myTopRight2')
            prix = prix_elem.text.strip() if prix_elem else "Non spécifié"
            
            # ----- TYPE DE BIEN (en arabe) -----
            type_elem = annonce.find('span', class_='myTopLeftt2')
            type_arabe = type_elem.text.strip() if type_elem else ""
            
            # Convertir en français
            type_bien = "Non spécifié"
            if 'قطعة أرضية' in type_arabe:
                type_bien = 'Terrain'
            elif 'منزل' in type_arabe:
                type_bien = 'Maison'
            elif 'شقة' in type_arabe:
                type_bien = 'Appartement'
            elif 'مكتب' in type_arabe:
                type_bien = 'Bureau'
            elif 'محل تجاري' in type_arabe:
                type_bien = 'Local commercial'
            
            # ----- TITRE (description) -----
            # Le titre est dans le div avec dir="auto" lang="ar"
            titre_div = annonce.find_next('div', {'dir': 'auto', 'lang': 'ar'})
            titre = titre_div.text.strip() if titre_div else "Non spécifié"
            
            # ----- IMAGE -----
            img = annonce.find('img')
            image_url = img['src'] if img and img.has_attr('src') else "Non spécifié"
            
            # ----- URL DE L'ANNONCE (pas de lien direct, mais on peut utiliser l'image)
            # L'image est cliquable, mais le lien est dans un parent
            parent_link = annonce.find_parent('a')
            url_annonce = parent_link['href'] if parent_link and parent_link.has_attr('href') else "Non spécifié"
            if url_annonce.startswith('/'):
                url_annonce = "https://www.elminassa.com" + url_annonce
            
            # ----- EXTRAIRE LA SURFACE DU TITRE -----
            surface_m2 = "Non spécifié"
            surface_match = re.search(r'(\d+)\s*m[²2]', titre)
            if surface_match:
                surface_m2 = surface_match.group(1) + " m²"
            
            # ----- EXTRAIRE LE QUARTIER DU TITRE -----
            quartier = "Non spécifié"
            quartiers = ['تفرغ زينة', 'دار النعيم', 'لكصر', 'الميناء', 'السبخة', 'تيارت', 'الرياض', 'عرفات', 'توجنين']
            for q in quartiers:
                if q in titre:
                    # Convertir en français
                    quartier_map = {
                        'تفرغ زينة': 'Tevragh Zeina',
                        'دار النعيم': 'Dar Naim',
                        'لكصر': 'Ksar',
                        'الميناء': 'El Mina',
                        'السبخة': 'Sebkha',
                        'تيارت': 'Teyarett',
                        'الرياض': 'Riyad',
                        'عرفات': 'Arafat',
                        'توجنين': 'Toujounine'
                    }
                    quartier = quartier_map.get(q, q)
                    break
            
            # Créer l'annonce
            annonce_data = {
                'source': 'elminassa.com',
                'titre': titre,
                'prix': prix,
                'type_bien': type_bien,
                'quartier': quartier,
                'surface_m2': surface_m2,
                'point_repere': 'Non spécifié',
                'vendeur': 'elminassa.com',
                'date_publication': 'Non spécifiée',
                'nb_images': '1',
                'image_url': image_url,
                'date_scraping': datetime.now().strftime('%Y-%m-%d'),
                'ville': 'Nouakchott',
                'nb_chambres': 'Non spécifié',
                'nb_sdb': 'Non spécifié',
                'description': titre,
                'id_unique': str(i+1),
                'url': url_annonce,
                'type_annonce': 'Non spécifié',
                'nb_vues': 'Non spécifié',
                'nb_pieces_total': 'Non spécifié',
                'meuble': 'Non spécifié',
            }
            
            donnees.append(annonce_data)
            print(f"  ✅ {titre[:50]}... - {prix}")
            
        except Exception as e:
            print(f"  ❌ Erreur annonce {i}: {e}")
            continue
    
    print(f"\nTotal annonces extraites: {len(donnees)}")
    
    # Sauvegarde
    if donnees:
        df = pd.DataFrame(donnees)
        df.to_csv('data_raw/elminassa.csv', index=False, encoding='utf-8-sig')
        print(f"Données sauvegardées dans data_raw/elminassa.csv")
        
        
    else:
        print("❌ Aucune donnée extraite")
        
finally:
    driver.quit()
    print("\n🎉 Scraping terminé!")