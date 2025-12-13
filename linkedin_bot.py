import os
import time
import re
import psycopg2
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from dotenv import load_dotenv
from bs4 import BeautifulSoup

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service

# --- 1. CONFIGURATION GLOBALE ---
load_dotenv()

# Configuration DEBUG
debug_env = os.getenv('DEBUG', 'False').lower()
DEBUG = debug_env == 'true' or debug_env == '1'
HEADLESS_MODE = False if DEBUG else True

# Configuration DB & LinkedIn
DB_URI = os.getenv('DB_URI')
KEYWORDS = os.getenv('MOTS_CLES', 'Data Scientist').split(',') 
USERNAME = os.getenv('USERNAME')
PASSWORD = os.getenv('PASSWORD')
SAVE_INTERVAL = 30 
MAX_SEARCH_TIME = 300 # 5 minutes max par mot-clé

# --- 2. FONCTIONS UTILITAIRES (Helpers) ---

def extract_email(text):
    """Extrait le premier email trouvé."""
    match = re.search(r'[\w.+-]+@[\w-]+\.[\w.-]+', text)
    return match.group(0) if match else None

def clean_text(text):
    if not text: return ""
    emoji_pattern = re.compile("["
        u"\U0001F600-\U0001F64F"  
        u"\U0001F300-\U0001F5FF"  
        u"\U0001F680-\U0001F6FF" 
        u"\U0001F700-\U0001F77F"  
        u"\U0001F780-\U0001F7FF"  
        u"\U0001F800-\U0001F8FF"  
        u"\U0001F900-\U0001F9FF"  
        u"\U0001FA00-\U0001FA6F"  
        u"\U0001FA70-\U0001FAFF"  
        u"\U00002700-\U000027BF"  
        u"\U00002600-\U000026FF"  
        "]+", flags=re.UNICODE)
    text = emoji_pattern.sub(r'', text)
    return text.strip()

def parse_relative_date(date_str):
    now = datetime.now()
    try:
        date_str = date_str.strip()
        if any(x in date_str for x in ['h', 'm', 'now', 'l’instant']):
            return now.strftime('%Y-%m-%d')
        elif 'j' in date_str or 'd' in date_str:
            val = int(re.search(r'(\d+)', date_str).group(1))
            return (now - timedelta(days=val)).strftime('%Y-%m-%d')
        elif 'sem' in date_str or 'w' in date_str:
            val = int(re.search(r'(\d+)', date_str).group(1))
            return (now - timedelta(weeks=val)).strftime('%Y-%m-%d')
        elif 'mois' in date_str or 'mo' in date_str:
            val = int(re.search(r'(\d+)', date_str).group(1))
            return (now - relativedelta(months=val)).strftime('%Y-%m-%d')
        elif 'an' in date_str or 'y' in date_str:
            val = int(re.search(r'(\d+)', date_str).group(1))
            return (now - relativedelta(years=val)).strftime('%Y-%m-%d')
    except:
        pass
    return now.strftime('%Y-%m-%d')

# --- 3. FONCTIONS DATABASE ---

def init_db():
    """Initialise la connexion DB et la table."""
    try:
        connection = psycopg2.connect(DB_URI)
        cursor = connection.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS INPOSTS(
            id SERIAL PRIMARY KEY,
            author VARCHAR(255),
            content TEXT,
            likes_count VARCHAR(50), 
            shares_count VARCHAR(50),
            comments_count VARCHAR(50),
            post_date DATE,
            keywords VARCHAR(255),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP )''')
        
        cursor.execute("""
            ALTER TABLE INPOSTS
            ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'PENDING'
        """)
        connection.commit()
        cursor.close()
        print("💾 Base de données connectée et vérifiée.")
        return connection
    except Exception as e:
        print(f"❌ Erreur critique DB : {e}")
        exit(1)

def save_current_page_data(driver, connection, keyword):
    """Scrape la page visible et sauvegarde dans la DB."""
    try:
        print(f"   [Sauvegarde] Analyse des posts visibles pour '{keyword}'...")
        soup = BeautifulSoup(driver.page_source.encode("utf-8"), "html.parser")
        
        # Sélecteur robuste (plusieurs types de classes LinkedIn)
        posts_cards = soup.find_all('div', class_=re.compile(r'feed-shared-update-v2|occludable-update'))
        if not posts_cards:
            posts_cards = soup.select('div[data-urn]') 

        print(f"    🔍 {len(posts_cards)} cartes de posts trouvées.")
        
        cursor = connection.cursor()
        count_saved = 0

        for card in posts_cards:
            try:
                # Extraction
                author_tag = card.find('span', class_='update-components-actor__name') or card.find('span', class_='update-components-actor__title')
                author = author_tag.get_text(strip=True).split('\n')[0] if author_tag else "Inconnu"

                content_tag = card.find('div', class_='update-components-text') or card.find('span', class_='break-words')
                content_raw = content_tag.get_text(separator="\n", strip=True) if content_tag else ""
                content = clean_text(content_raw)
                
                if len(content) < 5: continue

                date_tag = card.find('span', class_='update-components-actor__sub-description')
                raw_date = date_tag.get_text(strip=True).split('•')[0] if date_tag else ""
                post_date = parse_relative_date(raw_date)

                # Metriques
                likes = card.find('li', class_='social-details-social-counts__reactions').get_text(strip=True) if card.find('li', class_='social-details-social-counts__reactions') else "0"
                
                comments, shares = "0", "0"
                for item in card.find_all('li', class_='social-details-social-counts__item'):
                    text = item.get_text(strip=True).lower()
                    if 'comment' in text: comments = text.split()[0]
                    elif 'repost' in text or 'diffusion' in text: shares = text.split()[0]

                email_detected = extract_email(content_raw)

                # Insertion (Anti-doublon)
                sql_check = "SELECT id FROM INPOSTS WHERE author = %s AND content = %s"
                cursor.execute(sql_check, (author, content))
                
                if not cursor.fetchone():
                    sql_insert = """
                        INSERT INTO INPOSTS (author, content, likes_count, shares_count, comments_count, post_date, keywords) 
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """
                    cursor.execute(sql_insert, (author, content, likes, shares, comments, post_date, keyword))
                    connection.commit()
                    count_saved += 1
                    if email_detected: print(f"         📧 Email trouvé : {email_detected}")

            except Exception:
                continue

        cursor.close()
        if count_saved > 0: print(f"   ✅ {count_saved} nouveaux posts ajoutés.")

    except Exception as e:
        print(f"   ⚠️ Erreur sauvegarde : {e}")

# --- 4. FONCTIONS SELENIUM ---

def init_driver():
    """Initialise le driver Chrome avec la logique Docker/Local."""
    options = Options()
    
    # Profil persistant
    current_dir = os.getcwd()
    profile_path = os.path.join(current_dir, "selenium_profile")
    options.add_argument(f"user-data-dir={profile_path}")

    # Options de performance et stabilité
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    
    # Configuration du mode Headless
    if HEADLESS_MODE:
        print("🖥️  Mode HEADLESS activé.")
        options.add_argument("--headless=new")
        options.add_argument("--window-size=1920,1080")
    else:
        print("👀  Mode VISUEL activé.")
        options.add_argument("--start-maximized")

    # Détection Docker vs Local
    try:
        if os.path.exists("/usr/bin/chromedriver"):
            # Docker Environment
            service = Service(executable_path="/usr/bin/chromedriver")
            options.binary_location = "/usr/bin/chromium"
            driver = webdriver.Chrome(service=service, options=options)
        else:
            # Local Environment
            driver = webdriver.Chrome(options=options)
        return driver
    except Exception as e:
        print(f"❌ Erreur lancement Chrome: {e}")
        exit(1)

def login_linkedin(driver):
    """Gère la vérification de session et le login avec attente mobile."""
    try:
        print("🌍 Vérification de la session...")
        driver.get("https://www.linkedin.com/feed/")
        time.sleep(5)
        
        current_url = driver.current_url
        
        # Si redirection vers Login / Guest
        if any(x in current_url for x in ["login", "guest", "signup"]):
            print("🔑 Session expirée. Tentative de connexion...")
            
            driver.get("https://www.linkedin.com/login")
            time.sleep(3)
            
            # Remplissage Formulaire
            try:
                driver.find_element(By.ID, "username").send_keys(USERNAME)
                pwd = driver.find_element(By.ID, "password")
                pwd.send_keys(PASSWORD)
                pwd.submit()
            except Exception as e:
                print(f"⚠️ Erreur formulaire (peut-être déjà rempli): {e}")

            print("📨 Identifiants envoyés.")
            print("📲 EN ATTENTE : Validez la connexion sur votre application mobile LinkedIn.")
            
            # Boucle de Polling (2 minutes max)
            max_retries = 24 
            for i in range(max_retries):
                if "feed" in driver.current_url or "search" in driver.current_url:
                    print("✅ Validation mobile détectée ! Accès autorisé.")
                    return True
                
                print(f"   ... En attente ({i+1}/{max_retries}) ...")
                time.sleep(5)
            
            raise Exception("Timeout : Pas de validation mobile détectée.")
        
        print("✅ Déjà connecté.")
        return True

    except Exception as e:
        print(f"❌ Échec Login : {e}")
        return False

def scrape_keyword(driver, connection, keyword):
    """Exécute la recherche et le scroll pour un mot clé."""
    print(f"\n--- 🔎 Recherche : {keyword} ---")
    url = f"https://www.linkedin.com/search/results/content/?keywords={keyword}&sortBy=\"date_posted\""
    driver.get(url)
    time.sleep(5)

    start_time = time.time()
    last_save_time = start_time
    last_height = driver.execute_script("return document.body.scrollHeight")
    
    print("   (Défilement et analyse en cours...)")

    while True:
        # 1. Scroll
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        
        # 2. Clic "Voir plus"
        try:
            btns = driver.find_elements(By.CLASS_NAME, "feed-shared-inline-show-more-text__see-more-less-toggle")
            for b in btns: driver.execute_script("arguments[0].click();", b)
        except: pass

        # 3. Sauvegarde Intermédiaire
        if time.time() - last_save_time > SAVE_INTERVAL:
            save_current_page_data(driver, connection, keyword)
            last_save_time = time.time()

        # 4. Vérification Fin de Page
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            time.sleep(4)
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                print("   ⏹️  Fin de page atteinte.")
                break
        last_height = new_height

        # 5. Timeout
        if time.time() - start_time > MAX_SEARCH_TIME:
            print("   ⏱️  Temps limite atteint.")
            break
    
    # Sauvegarde finale
    save_current_page_data(driver, connection, keyword)

# --- 5. MAIN ORCHESTRATOR ---

def main():
    # 1. Init DB
    connection = init_db()
    
    # 2. Init Driver
    driver = init_driver()
    
    try:
        # 3. Login Flow
        if login_linkedin(driver):
            # 4. Scraping Flow
            print("🚀 Démarrage du scraping...")
            for word in KEYWORDS:
                word = word + 'Hiring'
                scrape_keyword(driver, connection, word.strip())
        else:
            print("🛑 Arrêt du script : Impossible de se connecter.")

    except Exception as e:
        print(f"❌ Erreur Globale : {e}")
    finally:
        print("👋 Fermeture du driver et de la connexion.")
        driver.quit()
        if connection: connection.close()

if __name__ == "__main__":
    main()