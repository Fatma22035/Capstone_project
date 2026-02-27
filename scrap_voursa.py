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
print("🏠 SCRAPING VOURSA.COM - VERSION 4000 ANNONCES")
print("="*60)

# Configuration du navigateur
options = Options()
options.add_argument('--headless')  # Pour que le navigateur ne s'affiche pas
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--disable-blink-features=AutomationControlled')
options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')

print("🚀 Lancement du navigateur...")
driver = webdriver.Chrome(options=options)

try:
    url = "https://voursa.com/FR/categories/real_estate"
    print(f"📄 Chargement de {url}...")
    
    driver.get(url)
    time.sleep(5)  # Attendre le chargement initial
    
    # Compter le nombre d'annonces avant clics
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    annonces_init = soup.find_all('div', class_='mb-6')
    print(f"🔍 Annonces initiales: {len(annonces_init)}")
    
    # CLIQUER SUR "VOIR PLUS" JUSQU'À ÉPUISEMENT
    clics = 0
    plus_de_bouton = False
    
    while not plus_de_bouton:
        try:
            # Chercher le bouton "Voir plus"
            voir_plus = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Voir plus')]"))
            )
            
            # Faire défiler jusqu'au bouton
            driver.execute_script("arguments[0].scrollIntoView(true);", voir_plus)
            time.sleep(1)
            
            # Cliquer
            voir_plus.click()
            clics += 1
            print(f"🖱️ Clic {clics} sur 'Voir plus'")
            
            # Attendre le chargement des nouvelles annonces
            time.sleep(4)
            
            # Vérifier combien d'annonces maintenant
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            annonces = soup.find_all('div', class_='mb-6')
            print(f"   📊 Total annonces maintenant: {len(annonces)}")
            
            # Si on a atteint 4000+, on peut s'arrêter
            if len(annonces) >= 4000:
                print(f"🎯 Objectif atteint: {len(annonces)} annonces!")
                break
                
        except Exception as e:
            print(f"✅ Plus de bouton 'Voir plus' après {clics} clics")
            plus_de_bouton = True
    
    # Récupérer le HTML final
    html = driver.page_source
    soup = BeautifulSoup(html, 'html.parser')
    
    # Trouver TOUTES les annonces
    annonces = soup.find_all('div', class_='mb-6')
    print(f"\n🔍 Total final: {len(annonces)} annonces")
    
    donnees = []
    
    for i, annonce in enumerate(annonces, 1):
        try:
            # ----- URL DE L'ANNONCE -----
            link = annonce.find('a', href=True)
            url_annonce = "https://voursa.com" + link['href'] if link and link['href'].startswith('/') else "Non spécifié"
            
            # ----- TITRE -----
            titre_elem = annonce.find('h3', class_='text-[16px] font-bold')
            titre = titre_elem.text.strip() if titre_elem else "Non spécifié"
            
            # ----- PRIX -----
            prix_elem = annonce.find('p', class_='text-lg font-[600] text-primaryBlue')
            prix = prix_elem.text.strip() if prix_elem else "Non spécifié"
            
            # ----- TYPE DE BIEN -----
            type_elem = annonce.find('span', class_='rounded-md bg-gray-200 px-2 py-1 text-[12px] text-gray-700')
            type_bien = type_elem.text.strip() if type_elem else "Non spécifié"
            
            # ----- TEXTE COMPLET POUR EXTRAIRE LES AUTRES INFOS -----
            texte_annonce = annonce.get_text(" ", strip=True)
            
            # ----- VENDEUR -----
            vendeur = "Non spécifié"
            vendeur_match = re.search(r'^([^\n]+?)\s+(?:Tevragh Zeina|Arafat|Dar Naim|Teyarett|Toujounine)', texte_annonce)
            if vendeur_match:
                vendeur = vendeur_match.group(1).strip()
            
            # ----- QUARTIER -----
            quartier = "Non spécifié"
            quartiers = ['Tevragh Zeina', 'Arafat', 'Dar Naim', 'Teyarett', 'Toujounine', 'Ksar', 'Sebkha', 'El Mina', 'Riyad']
            for q in quartiers:
                if q in texte_annonce:
                    quartier = q
                    break
            
            # ----- DATE DE PUBLICATION -----
            date_publication = "Non spécifiée"
            date_match = re.search(r'il y a (\d+)\s+(heure|heures|jour|jours)', texte_annonce)
            if date_match:
                date_publication = date_match.group(0)
            
            # ----- SURFACE -----
            surface = "Non spécifié"
            surface_match = re.search(r'Superficie · (\d+)', texte_annonce)
            if surface_match:
                surface = surface_match.group(1) + " m²"
            
            # ----- POINT DE REPÈRE -----
            point_repere = "Non spécifié"
            point_match = re.search(r'Point le plus proche · ([^\n]+?)(?:\s+\d+\s+[A-Za-z]+|$)', texte_annonce)
            if point_match:
                point_repere = point_match.group(1).strip()
            
            # ----- NOMBRE D'IMAGES -----
            nb_images = "Non spécifié"
            images_match = re.search(r'(\d+)\s*$', texte_annonce)
            if images_match:
                nb_images = images_match.group(1)
            
            # ----- IMAGE -----
            image_url = "Non spécifié"
            img_tag = annonce.find('img')
            if img_tag and img_tag.has_attr('src'):
                src = img_tag['src']
                if src.startswith('/_next'):
                    image_url = "https://voursa.com" + src
                else:
                    image_url = src
            
            donnees.append({
                'source': 'voursa.com',
                'url': url_annonce,
                'titre': titre,
                'prix': prix,
                'type_bien': type_bien,
                'quartier': quartier,
                'surface_m2': surface,
                'point_repere': point_repere,
                'vendeur': vendeur,
                'date_publication': date_publication,
                'nb_images': nb_images,
                'image_url': image_url,
                'date_scraping': datetime.now().strftime('%Y-%m-%d'),
                'ville': 'Nouakchott',
            })
            
            if i % 50 == 0:
                print(f"  ✅ {i}/{len(annonces)} annonces traitées")
            
        except Exception as e:
            print(f"  ❌ Erreur sur annonce {i}: {e}")
            continue
    
    df = pd.DataFrame(donnees)
    
    if len(df) > 0:
        # Sauvegarde
        df.to_csv('data/raw/voursa.csv', index=False, encoding='utf-8-sig')
        print(f"\n💾 Sauvegardé {len(df)} annonces dans data/raw/voursa_4000.csv")
        
        # Statistiques
        print(f"\n📊 STATISTIQUES VOURSA:")
        print(f"   - Total annonces: {len(df)}")
        print(f"   - Avec prix: {df[df['prix'] != 'Non spécifié'].shape[0]}")
        print(f"   - Avec surface: {df[df['surface_m2'] != 'Non spécifié'].shape[0]}")
        print(f"   - Avec quartier: {df[df['quartier'] != 'Non spécifié'].shape[0]}")
        print(f"   - Avec vendeur: {df[df['vendeur'] != 'Non spécifié'].shape[0]}")
        
        # Fusion avec les données existantes
        print("\n🔄 Fusion avec les données existantes...")
        
        if os.path.exists('data_raw.csv'):
            df_existant = pd.read_csv('data_raw.csv')
            df_final = pd.concat([df_existant, df], ignore_index=True)
            print(f"   Existantes: {len(df_existant)}")
            print(f"   Nouvelles: {len(df)}")
            print(f"   Total: {len(df_final)}")
        else:
            df_final = df
            print(f"   Premier fichier: {len(df)} annonces")
        
        df_final.to_csv('data_raw.csv', index=False, encoding='utf-8-sig')
        print(f"\n✅ Fichier final: data_raw.csv avec {len(df_final)} annonces")
        
        # Aperçu
        print("\n👀 Aperçu des 10 premières annonces:")
        print(df[['titre', 'prix', 'quartier', 'surface_m2']].head(10))
        
    else:
        print("❌ Aucune donnée extraite")
      
finally:
    driver.quit()
    print("\n🎉 Scraping terminé!")

