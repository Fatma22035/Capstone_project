import time
import pandas as pd
import re
from datetime import datetime, timedelta
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import csv

print("="*60)
print(" SCRAPING VOURSA - 50 ANNONCES À LA FOIS")
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

# Fichier de sortie
fichier_sortie = 'data/raw/voursa.csv'

# Créer le fichier avec en-tête s'il n'existe pas
if not os.path.exists(fichier_sortie):
    with open(fichier_sortie, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        writer.writerow([
            'source', 'url', 'titre', 'prix', 'type_bien', 'quartier',
            'surface_m2', 'point_repere', 'vendeur', 'date_publication',
            'nb_images', 'image_url', 'date_scraping', 'ville'
        ])

def convertir_date_relative(date_texte):
    """Convertit 'il y a X heures/jours/semaines/mois/ans' en date réelle"""
    if not date_texte or date_texte == "Non spécifiée":
        return "Non spécifiée"
    
    maintenant = datetime.now()
    date_texte = date_texte.lower()
    
    # Pattern: "il y a X heures"
    heures_match = re.search(r'il y a (\d+)\s+heure', date_texte)
    if heures_match:
        heures = int(heures_match.group(1))
        return (maintenant - timedelta(hours=heures)).strftime('%Y-%m-%d')
    
    # Pattern: "il y a X jours"
    jours_match = re.search(r'il y a (\d+)\s+jour', date_texte)
    if jours_match:
        jours = int(jours_match.group(1))
        return (maintenant - timedelta(days=jours)).strftime('%Y-%m-%d')
    
    # Pattern: "il y a X semaines"
    semaines_match = re.search(r'il y a (\d+)\s+semaine', date_texte)
    if semaines_match:
        semaines = int(semaines_match.group(1))
        return (maintenant - timedelta(weeks=semaines)).strftime('%Y-%m-%d')
    
    # Pattern: "il y a X mois"
    mois_match = re.search(r'il y a (\d+)\s+mois', date_texte)
    if mois_match:
        mois = int(mois_match.group(1))
        # Approximation: 1 mois = 30 jours
        return (maintenant - timedelta(days=mois*30)).strftime('%Y-%m-%d')
    
    # Pattern: "il y a X ans"
    ans_match = re.search(r'il y a (\d+)\s+an', date_texte)
    if ans_match:
        ans = int(ans_match.group(1))
        # Approximation: 1 an = 365 jours
        return (maintenant - timedelta(days=ans*365)).strftime('%Y-%m-%d')
    
    # Pattern: dates formatées comme "29 Juin 2023"
    date_formattee = re.search(r'(\d{1,2})\s+(janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)\s+(\d{4})', date_texte, re.I)
    if date_formattee:
        jour = int(date_formattee.group(1))
        mois_texte = date_formattee.group(2).lower()
        annee = int(date_formattee.group(3))
        
        mois_map = {
            'janvier': 1, 'février': 2, 'mars': 3, 'avril': 4, 'mai': 5, 'juin': 6,
            'juillet': 7, 'août': 8, 'septembre': 9, 'octobre': 10, 'novembre': 11, 'décembre': 12
        }
        mois = mois_map.get(mois_texte, 1)
        
        try:
            return datetime(annee, mois, jour).strftime('%Y-%m-%d')
        except:
            pass
    
    return date_texte

def extraire_toutes_annonces(soup, urls_deja_vues):
    """Extrait TOUTES les annonces présentes dans la page"""
    
    annonces = soup.find_all('div', class_='mb-6')
    nouvelles_annonces = []
    
    for annonce in annonces:
        try:
            # URL
            link = annonce.find('a', href=True)
            if not link:
                continue
            url_annonce = "https://voursa.com" + link['href']
            
            # Ignorer si déjà vue
            if url_annonce in urls_deja_vues:
                continue
            
            # Titre
            titre_elem = annonce.find('h3')
            titre = titre_elem.text.strip() if titre_elem else "Non spécifié"
            
            # Prix
            prix_elem = annonce.find('p', class_='text-primaryBlue')
            prix = prix_elem.text.strip() if prix_elem else "Non spécifié"
            
            # Date relative
            date_elem = annonce.find('span', string=re.compile(r'il y a'))
            date_relative = date_elem.text.strip() if date_elem else "Non spécifiée"
            date_publication = convertir_date_relative(date_relative)
            
            # Type de bien
            type_elem = annonce.find('span', class_='bg-gray-200')
            type_bien = type_elem.text.strip() if type_elem else "Non spécifié"
            
            # Quartier
            texte_annonce = annonce.get_text(" ", strip=True)
            quartier = "Non spécifié"
            for q in ['Tevragh Zeina', 'Arafat', 'Dar Naim', 'Teyarett', 'Toujounine']:
                if q in texte_annonce:
                    quartier = q
                    break
            
            # Vendeur
            vendeur = "Non spécifié"
            vendeur_match = re.search(r'^([^\n]+?)\s+(?:Tevragh Zeina|Arafat|Dar Naim|Teyarett|Toujounine)', texte_annonce)
            if vendeur_match:
                vendeur = vendeur_match.group(1).strip()
            
            # Surface
            surface = "Non spécifié"
            surface_match = re.search(r'Superficie · (\d+)', texte_annonce)
            if surface_match:
                surface = surface_match.group(1) + " m²"
            
            # Point de repère
            point_repere = "Non spécifié"
            point_match = re.search(r'Point le plus proche · ([^\n]+?)(?:\s+\d+\s+[A-Za-z]+|$)', texte_annonce)
            if point_match:
                point_repere = point_match.group(1).strip()
            
            # Nombre d'images
            nb_images = "1"
            images_match = re.search(r'(\d+)\s*$', texte_annonce)
            if images_match:
                nb_images = images_match.group(1)
            
            # Image URL
            image_url = "Non spécifié"
            img_tag = annonce.find('img')
            if img_tag and img_tag.has_attr('src'):
                src = img_tag['src']
                image_url = "https://voursa.com" + src if src.startswith('/_next') else src
            
            nouvelles_annonces.append({
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
                'ville': 'Nouakchott'
            })
            
        except Exception as e:
            print(f"❌ Erreur: {e}")
            continue
    
    return nouvelles_annonces

# ============================================
# SCRAPING OPTIMISÉ
# ============================================

try:
    # Charger la page
    url = "https://voursa.com/FR/categories/real_estate"
    print(f" Chargement de {url}...")
    driver.get(url)
    time.sleep(5)
    
    # URLs déjà vues
    urls_deja_vues = set()
    if os.path.exists(fichier_sortie):
        df_existant = pd.read_csv(fichier_sortie)
        if 'url' in df_existant.columns:
            urls_deja_vues = set(df_existant['url'].dropna().tolist())
            print(f" {len(urls_deja_vues)} annonces déjà scrappées")
    
    total_annonces = len(urls_deja_vues)
    clics = 0
    
    print("\n🚀 DÉBUT DU SCRAPING PAR LOTS")
    print("="*60)
    
    while True:
        try:
            # Récupérer le HTML actuel
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            
            # Extraire TOUTES les annonces de la page en UNE SEULE FOIS
            nouvelles_annonces = extraire_toutes_annonces(soup, urls_deja_vues)
            
            if nouvelles_annonces:
                # Sauvegarder TOUTES les nouvelles annonces d'un coup
                with open(fichier_sortie, 'a', newline='', encoding='utf-8-sig') as f:
                    writer = csv.writer(f)
                    for annonce in nouvelles_annonces:
                        writer.writerow([
                            annonce['source'], annonce['url'], annonce['titre'],
                            annonce['prix'], annonce['type_bien'], annonce['quartier'],
                            annonce['surface_m2'], annonce['point_repere'],
                            annonce['vendeur'], annonce['date_publication'],
                            annonce['nb_images'], annonce['image_url'],
                            annonce['date_scraping'], annonce['ville']
                        ])
                        urls_deja_vues.add(annonce['url'])
                
                total_annonces += len(nouvelles_annonces)
                print(f"\n LOT DE {len(nouvelles_annonces)} ANNONCES")
                print(f" TOTAL: {total_annonces} annonces")
                print(f"   Exemple: {nouvelles_annonces[0]['titre'][:30]}...")
            
            # Cliquer sur "Voir plus" pour charger la suite
            try:
                voir_plus = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Voir plus')]"))
                )
                driver.execute_script("arguments[0].scrollIntoView(true);", voir_plus)
                time.sleep(1)
                voir_plus.click()
                clics += 1
                print(f" Clic {clics} - Chargement du lot suivant...")
                time.sleep(4)
                
                # Backup périodique
                if total_annonces % 500 == 0:
                    df_backup = pd.read_csv(fichier_sortie)
                    df_backup.to_csv('data/raw/voursa_backup.csv', index=False)
                    print(f" Backup: {total_annonces} annonces")
                    
            except Exception as e:
                print(f"\n✅ Plus de bouton 'Voir plus' après {clics} clics")
                break
                
        except KeyboardInterrupt:
            print(f"\n\n ARRÊT DEMANDÉ - {total_annonces} annonces sauvegardées")
            
            
finally:
    driver.quit()
    print("\n🎉 Scraping terminé!")