"""
Script de scraping pour voursa.com
Combine Selenium pour la collecte des URLs et requests/BeautifulSoup pour l'extraction des données.
Projet Capstone - Prédiction des prix immobiliers en Mauritanie
Master 1 - SupNum - Février 2026
Extraction des champs : titre, type_bien, type_annonce, prix, surface_m2,
nb_chambres, nb_salons, nb_sdb, quartier, ville, description, source,
date_publication, caracteristiques
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import re
import json
from urllib.parse import urljoin
import logging
from datetime import datetime

# ================== CONFIGURATION ==================
BASE_URL = "https://voursa.com"
SOURCE = "voursa.com"
MAX_ADS = 6000  # Nombre maximal d'annonces à collecter (mettre 0 pour illimité)
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
DELAY = 1  # Délai entre les requêtes HTTP (respect du site)
HOME_URL = urljoin(BASE_URL, "/FR/categories/real_estate")

# Mapping des types de biens
TYPE_BIEN_MAPPING = {
    "Immobilier résidentiel": "Appartement/Maison",
    "Terrain": "Terrain",
    "Bureau": "Bureau",
    "Entrepôt": "Entrepôt",
    "Boutique": "Local commercial",
    "Immobilier commercial et industriel": "Local commercial/industriel",
    "Appartement": "Appartement",
    "Maison": "Maison",
    "Villa": "Villa",
    "Duplex": "Duplex",
    "Studio": "Studio",
    "Autre": "Autre"
}
# Mots-clés pour les caractéristiques
CARAC_KEYWORDS = [
    "garage", "parking", "piscine", "climatisation", "chauffage", "terrasse",
    "balcon", "jardin", "cour", "meublé", "ascenseur", "interphone", "gardien",
    "alarme", "vue", "mer", "plage", "proche", "centre", "calme", "sécurisé",
    "cuisine équipée", "buanderie", "dressing", "cave", "cellier", "véranda",
    "cheminée", "double vitrage", "volets", "store", "pompe à chaleur", "loge",
    "remise", "hall", "douche", "bureau", "caméra de sécurité", "titre foncier",
    "location au mois", "location à l'année", "studio", "chambre", "salon",
    "salle d'eau", "toilette", "wc", "espace vert", "clôturé", "électrique",
    "eau", "internet", "câble", "satellite", "piscine", "jacuzzi", "sauna",
    "hammam", "salle de sport", "gym", "parking couvert", "parking extérieur",
    "porte blindée", "digicode", "vidéophone", "interphone", "alarme",
    "caméra", "sécurité 24h/24", "gardien", "résidence fermée", "calme",
    "ensoleillé", "vue mer", "vue dégagée", "proche commodités", "proche écoles",
    "proche commerces", "proche transport", "centre ville", "quartier résidentiel"
]

# ================== CONFIGURATION LOGGING ==================
logging.basicConfig(level=logging.INFO,format='%(asctime)s - %(levelname)s - %(message)s')

# ================== FONCTIONS UTILITAIRES ==================
def extract_number(text):
    """Extrait le premier nombre entier d'une chaîne."""
    match = re.search(r'(\d+)', str(text))
    return int(match.group(1)) if match else None

def get_soup(url, retries=3):
    """Récupère le contenu HTML d'une URL avec BeautifulSoup."""
    headers = {"User-Agent": USER_AGENT}
    for i in range(retries):
        try:
            time.sleep(DELAY)
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            response.encoding = 'utf-8'
            return BeautifulSoup(response.text,'html.parser')
        except requests.exceptions.RequestException as e:
            logging.warning(f"Tentative {i+1}/{retries} échouée pour {url} : {e}")
            time.sleep(DELAY * 2)
    logging.error(f"Impossible de récupérer {url} après {retries} tentatives.")
    return None

def extract_property_data(property_url):
    """Extrait les données d'une annonce à partir de son URL."""
    logging.info(f"Traitement de {property_url}")
    soup = get_soup(property_url)
    if not soup:
        return None

    # Recherche du div contenant les données JSON
    ad_detail_div = soup.find('div', attrs={'data-ad-detail': True})
    if not ad_detail_div:
        logging.warning(f"Pas de données JSON trouvées pour {property_url}")
        return None

    try:
        json_str = ad_detail_div['data-ad-detail']
        ad_data = json.loads(json_str)
    except (json.JSONDecodeError, KeyError) as e:
        logging.error(f"Erreur de parsing JSON pour {property_url} : {e}")
        return None

    # Initialisation du dictionnaire de données
    data = {
        "titre": None,
        "type_bien": None,
        "type_annonce": None,
        "prix": None,
        "surface_m2": None,
        "nb_chambres": None,
        "nb_salons": None,
        "nb_sdb": None,
        "quartier": None,
        "ville": "Nouakchott",  # valeur par défaut
        "description": None,
        "source": SOURCE,
        "date_publication": None,
        "caracteristiques": []
    }

    # -------------------- Extraction depuis le JSON --------------------
    if 'title' in ad_data:
        data['titre'] = ad_data['title']
    if 'subcategoryName' in ad_data:
        subcat = ad_data['subcategoryName']
        data['type_bien'] = TYPE_BIEN_MAPPING.get(subcat, subcat)
    if 'price' in ad_data:
        try:
            price_str = str(ad_data['price']).replace(' ', '').replace(',', '')
            data['prix'] = int(float(price_str))
        except:
            pass
    if 'location' in ad_data:
        data['quartier'] = ad_data['location']
    if 'description' in ad_data:
        data['description'] = ad_data['description']
    if 'postedAt' in ad_data:
        try:
            date_obj = datetime.fromisoformat(ad_data['postedAt'].split('.')[0])
            data['date_publication'] = date_obj.strftime('%Y-%m-%d')
        except:
            pass

    # Détection du type d'annonce (Vente/Location)
    if data['titre']:
        titre_lower = data['titre'].lower()
        if 'à louer' in titre_lower or 'location' in titre_lower:
            data['type_annonce'] = "Location"
        elif 'à vendre' in titre_lower or 'vente' in titre_lower:
            data['type_annonce'] = "Vente"
    if 'details' in ad_data:
        for detail in ad_data['details']:
            key = detail.get('key', '').lower()
            val = detail.get('value', '').lower()
            if 'type de location' in key:
                if 'mois' in val or 'location au mois' in val:
                    data['type_annonce'] = "Location"
                elif 'vente' in val:
                    data['type_annonce'] = "Vente"
    if not data['type_annonce'] and data['prix']:
        if data['prix'] < 200000:
            data['type_annonce'] = "Location"
        else:
            data['type_annonce'] = "Vente"

    # Extraction depuis le tableau 'details'
    if 'details' in ad_data and isinstance(ad_data['details'], list):
        for detail in ad_data['details'] :
            key = detail.get('key', '').lower()
            value = detail.get('value')
            if not value:
                continue
            if 'chambres' in key or 'rooms' in key:
                data['nb_chambres'] = extract_number(value)
            elif 'salle de bain' in key or 'bathrooms' in key:
                data['nb_sdb'] = extract_number(value)
            elif 'salles' in key or 'halls' in key:
                if not data['nb_salons']:
                    data['nb_salons'] = extract_number(value)
            elif 'balcons' in key:
                nb = extract_number(value)
                if nb and nb > 0:
                    data['caracteristiques'].append(f"{nb} balcon(s)")
            elif 'titre foncier' in key:
                if value.lower() == 'oui':
                    data['caracteristiques'].append("Titre foncier")
            elif any(kw in key for kw in ['garage', 'parking', 'piscine', 'climatisation']):
                data['caracteristiques'].append(f"{key}: {value}")
            else:
                carac = f"{key}: {value}"
                if carac not in data['caracteristiques'] and len(carac) < 100:
                    data['caracteristiques'].append(carac)

    # Extraction depuis le tableau 'overview'
    if 'overview' in ad_data and isinstance(ad_data['overview'], list):
        for overview in ad_data['overview']:
            key = overview.get('key', '').lower()
            value = overview.get('value')
            if not value:
                continue
            if 'superficie' in key or 'area size' in key:
                try:
                    data['surface_m2'] = int(float(value))
                except:
                    pass
            elif 'point le plus proche' in key:
                data['caracteristiques'].append(f"Proche de: {value}")
            elif 'taille de la rue' in key:
                data['caracteristiques'].append(f"Taille rue: {value}")
            else:
                carac = f"{key}: {value}"
                if carac not in data['caracteristiques'] and len(carac) < 100:
                    data['caracteristiques'].append(carac)

    # Extraction depuis le tableau 'features'
    if 'features' in ad_data and isinstance(ad_data['features'], list):
        for feature in ad_data['features']:
            if 'key' in feature:
                feat = feature['key']
                if feat not in data['caracteristiques']:
                    data['caracteristiques'].append(feat)

    # -------------------- Extraction depuis la description (complément) --------------------
    if data['description']:
        desc = data['description']

        if not data['surface_m2']:
            surface_match = re.search(r'(\d+)\s*(m[²2]|m²|m2)', desc, re.I)
            if surface_match:
                data['surface_m2'] = int(surface_match.group(1))
            else:
                surface_match = re.search(r'(superficie|surface)[^\d]*(\d+)', desc, re.I)
                if surface_match:
                    data['surface_m2'] = int(surface_match.group(2))

        if not data['nb_chambres']:
            ch_match = re.search(r'(\d+)\s*(chambre|chambres)', desc, re.I)
            if ch_match:
                data['nb_chambres'] = int(ch_match.group(1))

        if not data['nb_sdb']:
            sdb_match = re.search(r'(\d+)\s*(salle de bain|salles de bains|sdb|douche)', desc, re.I)
            if sdb_match:
                data['nb_sdb'] = int(sdb_match.group(1))

        if not data['nb_salons']:
            salon_count = len(re.findall(r'\b(salon|séjour|living)\b', desc, re.I))
            if salon_count > 0:
                data['nb_salons'] = salon_count

        if 'nouadhibou' in desc.lower():
            data['ville'] = "Nouadhibou"
        elif 'nouakchott' in desc.lower():
            data['ville'] = "Nouakchott"

        if not data['quartier']:
            quartiers = ["Tevragh Zeina", "Ksar", "Teyarett", "Dar Naim", "Arafat", "Riyadh",
                         "Cité Plage", "Centre Émetteur", "Ilot K", "Ilot M", "Las Palmas",
                         "Socogim", "Mégafoot", "Module M", "Soukouk", "Sahraoui", "Toujounine",
                         "Mederdra", "Ouad Naga"]
            for q in quartiers:
                if q.lower() in desc.lower():
                    data['quartier'] = q
                    break

        for kw in CARAC_KEYWORDS:
            if kw.lower() in desc.lower() and kw not in data['caracteristiques']:
                data['caracteristiques'].append(kw)

    # Nettoyage des caractéristiques
    data['caracteristiques'] = list(dict.fromkeys(data['caracteristiques']))
    data['caracteristiques'] = " | ".join(data['caracteristiques']) if data['caracteristiques'] else ""

    return data

# ================== ÉTAPE 1 : COLLECTE DES URLs AVEC SELENIUM ==================
def collect_urls(max_ads=MAX_ADS):
    """Utilise Selenium pour collecter les URLs des annonces jusqu'à max_ads."""
    logging.info("Configuration du driver Selenium...")
    options = webdriver.ChromeOptions()
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument(f"user-agent={USER_AGENT}")

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )
    wait = WebDriverWait(driver, 10)

    logging.info(f"Chargement de {HOME_URL}")
    driver.get(HOME_URL)
    time.sleep(5)

    all_links = set()
    last_count = 0
    no_change = 0

    while True:
        # Récupérer les liens
        cards = driver.find_elements(By.CSS_SELECTOR, "a[href*='/ads/']")
        for c in cards:
            href = c.get_attribute("href")
            if href:
                all_links.add(href)
        logging.info(f"Total URLs collectées : {len(all_links)}")

        if max_ads > 0 and len(all_links) >= max_ads:
            logging.info(f"Nombre maximal d'URLs atteint ({max_ads}).")
            break

        # Chercher le bouton "Voir plus"
        try:
            bouton = driver.find_element(By.XPATH, "//button[contains(text(), 'Voir plus') or contains(text(), 'Charger plus')]")
            if bouton.is_enabled():
                driver.execute_script("arguments[0].click();", bouton)
                time.sleep(3)  # Attente chargement
                continue
        except NoSuchElementException:
            pass

        # Si plus de bouton et plus de nouvelles URLs, on arrête
        if len(all_links) == last_count:
            no_change += 1
            if no_change > 2:
                logging.info("Plus de nouvelles URLs après plusieurs tentatives. Fin de la collecte.")
                break
        else:
            no_change = 0
        last_count = len(all_links)

        # Scroll (au cas où)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)

    driver.quit()
    # Limiter au nombre demandé
    all_links = list(all_links)
    if max_ads > 0 and len(all_links) > max_ads:
        all_links = all_links[:max_ads]
    logging.info(f"Collecte terminée : {len(all_links)} URLs.")
    return all_links

# ================== ÉTAPE 2 : SCRAPING DES DONNÉES ==================
def scrape_urls(urls, batch_size=100):
    """Scrape les URLs et sauvegarde par lots."""
    all_data = []
    for i, url in enumerate(urls, 1):
        data = extract_property_data(url)
        if data:
            all_data.append(data)
        if i % batch_size == 0:
            # Sauvegarde intermédiaire
            df_temp = pd.DataFrame(all_data)
            df_temp.to_csv(f"voursa_backup_{i}.csv", index=False, encoding='utf-8')
            logging.info(f"Backup sauvegardé ({i} annonces).")
    return all_data

# ================== MAIN ==================
def main():
    logging.info("Début du processus de scraping.")
    # Collecte des URLs
    urls = collect_urls(max_ads=MAX_ADS)
    if not urls:
        logging.error("Aucune URL collectée. Arrêt.")
        return

    # Scraping des données
    logging.info(f"Début du scraping de {len(urls)} annonces.")
    data = scrape_urls(urls, batch_size=100)

    if not data:
        logging.error("Aucune donnée extraite.")
        return

    # Création du DataFrame final
    df = pd.DataFrame(data)

    # Réorganisation des colonnes
    column_order = [
        "titre", "type_bien", "type_annonce", "prix", "surface_m2",
        "nb_chambres", "nb_salons", "nb_sdb", "quartier", "ville",
        "description", "source", "date_publication", "caracteristiques"
    ]
    for col in column_order:
        if col not in df.columns:
            df[col] = None
    df = df[column_order]

    output_file = "voursa_raw.csv"
    df.to_csv(output_file, index=False, encoding='utf-8')
    logging.info(f"Scraping terminé. {len(df)} annonces sauvegardées dans {output_file}")

if __name__ == "__main__":
    main()