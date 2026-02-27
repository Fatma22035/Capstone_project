import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
from datetime import datetime

print("="*60)
print(" SCRAPING MULTI-PAGES WASSIT.INFO")
print("="*60)

# Configuration
headers = {
    'User-Agent': 'MauritaniaHousingProject/1.0 (etudiante) - Projet academique'
}

# Fonction pour scraper une page donnée
def scrape_page(page_num=1):
    """Scrape une page spécifique de wassit.info"""
    
    # Construction de l'URL selon le numéro de page
    if page_num == 1:
        url = "http://wassit.info/immobilier.html"
    else:
        # À ADAPTER selon la vraie structure des URLs
        # url = f"http://wassit.info/immobilier.html?page={page_num}"
        url = f"http://wassit.info/immobilier/{page_num}-3-2.html"  # À modifier !
    
    print(f"\nScraping page {page_num}: {url}")
    
    try:
        response = requests.get(url, headers=headers)
        time.sleep(3)  # Pause entre les pages
        
        if response.status_code != 200:
            print(f" Page {page_num} non trouvée (code {response.status_code})")
            return None
            
        soup = BeautifulSoup(response.content, "html.parser")
        annonces = soup.find_all('div', class_="block")
        
        print(f" Annonces trouvées sur page {page_num}: {len(annonces)}")
        
        if len(annonces) == 0:
            print(f" Plus d'annonces sur page {page_num} - arrêt")
            return None
            
        donnees_page = []
        
        for annonce in annonces:
            try:
                center_div = annonce.find('div', class_='center')
                if center_div:
                    # ----- TITRE -----
                    title_div = center_div.find('div', class_='title')
                    if title_div:
                        h2_tag = title_div.find('h2')
                        if h2_tag:
                            a_tag = h2_tag.find('a')
                            titre = a_tag.text.strip() if a_tag else h2_tag.text.strip()
                        else:
                            titre = "Non spécifié"
                    else:
                        titre = "Non spécifié"
                    
                    # ----- PRIX -----
                    price_div = center_div.find('div', class_='price')
                    if price_div:
                        prix = price_div.text.strip()
                        prix = prix.replace('UM', '').replace('&nbsp;', '').strip()
                    else:
                        prix = "Non spécifié"
                    
                    # ----- VILLE/QUARTIER -----
                    city_div = center_div.find('div', class_='city')
                    ville = city_div.text.strip() if city_div else "Nouakchott"
                    
                    # ----- DATE/VUES -----
                    date_div = center_div.find('div', class_='date')
                    date_texte = date_div.text.strip() if date_div else ""
                    
                    # ----- URL DÉTAIL -----
                    if title_div and title_div.find('a'):
                        url_annonce = title_div.find('a')['href']
                        url_complete = f"https://wassit.info{url_annonce}"
                    else:
                        url_complete = ""
                    
                    donnees_page.append({
                        'titre': titre,
                        'prix': prix,
                        'ville': ville,
                        'date_publication': date_texte,
                        'url': url_complete,
                        'source': 'wassit.info',
                        'page': page_num,
                        'date_scraping': datetime.now().strftime('%Y-%m-%d')
                    })
                    
                    print(f"  ✅ {titre[:30]}... - {prix}")
                    
            except Exception as e:
                print(f"  ❌ Erreur: {e}")
                continue
        
        return donnees_page
        
    except Exception as e:
        print(f"❌ Erreur sur page {page_num}: {e}")
        return None

# SCRAPER TOUTES LES PAGES

toutes_donnees = []
page = 1
max_pages = 10  # Limite de sécurité

while page <= max_pages:
    donnees_page = scrape_page(page)
    
    if donnees_page is None or len(donnees_page) == 0:
        print(f"\n🏁 Plus de données à la page {page}. Arrêt du scraping.")
        break
    
    toutes_donnees.extend(donnees_page)
    print(f"\n Total cumulé: {len(toutes_donnees)} annonces")
    
    page += 1
    
    # Petite pause entre les pages
    time.sleep(2)

# SAUVEGARDE

if toutes_donnees:
    df = pd.DataFrame(toutes_donnees)
    
    print("\n" + "="*60)
    print(" RÉSULTAT FINAL")
    print("="*60)
    print(f" Total annonces scrapées: {len(df)}")
    print(f" Nombre de pages: {df['page'].nunique()}")
    print(f" Répartition par page:\n{df['page'].value_counts().sort_index()}")
    
    # Sauvegarde
    df.to_csv('data_raw.csv', index=False)
    print(f"\n Données sauvegardées dans data_raw.csv")
    
    # Aperçu
    print("\n Aperçu des 5 premières annonces:")
    print(df[['titre', 'prix', 'ville']].head())
    
else:
    print(" Aucune donnée récupérée")

