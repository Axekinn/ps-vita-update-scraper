import os
import time
import json
import random
import hashlib
import hmac
import requests
import pandas as pd
from pathlib import Path
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import xml.etree.ElementTree as ET
import csv

# Import Selenium
try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.options import Options
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False
    print("⚠️  Selenium not available. Installing...")
    os.system("pip install selenium")

requests.packages.urllib3.disable_warnings()

class PSVitaTitlesScraper:
    """PS Vita Titles scraper for Renascene.com"""

    def __init__(self):
        self.base_url = "https://renascene.com/psv/"
        self.params = {
            'target': 'list',
            'sort': 'ID',
            'ord': '',
            'gr': ''
        }
        self.games_data = []
        self.driver = None
        self.setup_driver()

    def setup_driver(self):
        """Setup Chrome driver"""
        if not SELENIUM_AVAILABLE:
            print("❌ Selenium not available for scraping")
            return

        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            print("✅ Chrome driver initialized successfully")
        except Exception as e:
            print(f"❌ Error setting up driver: {e}")
            self.driver = None

    def scrape_page(self, page_num):
        """Scraper une page de titres PS Vita sur Renascene"""
        if not self.driver:
            print("❌ Chrome driver not available")
            return []

        url = f"{self.base_url}?target={self.params['target']}&sort={self.params['sort']}&ord={self.params['ord']}&gr={self.params['gr']}&page={page_num}"
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                print(f"🔗 Loading PS Vita page {page_num}...")
                self.driver.get(url)
                
                # Attendre que la page se charge
                time.sleep(3)
                
                # Chercher la table avec l'ID "tabloid" (trouvé dans le HTML)
                try:
                    table = self.driver.find_element(By.ID, "tabloid")
                    print(f"    ✅ Found main table with ID 'tabloid'")
                except:
                    print(f"    ❌ Table with ID 'tabloid' not found")
                    if attempt == max_retries - 1:
                        return []
                    time.sleep(5)
                    continue
                    
                rows = table.find_elements(By.TAG_NAME, "tr")
                
                if len(rows) <= 1:
                    print(f"❌ No data rows in main table on page {page_num}")
                    if attempt == max_retries - 1:
                        return []
                    time.sleep(5)
                    continue
                    
                page_games = []
                
                # Parcourir les lignes (sauf l'en-tête)
                for row_idx, row in enumerate(rows[1:], 1):
                    try:
                        cells = row.find_elements(By.TAG_NAME, "td")
                        
                        # D'après le HTML, la structure est:
                        # [0] Status icon, [1] ID, [2] TITLE, [3] REGION, [4] Media ID, [5] Box ID, [6] GENRE, [7] RELEASED
                        if len(cells) >= 8:
                            # Ignorer la première colonne (status icon)
                            game_id = cells[1].text.strip()
                            title = cells[2].text.strip()
                            region_element = cells[3]
                            media_id = cells[4].text.strip()
                            box_id = cells[5].text.strip()
                            genre = cells[6].text.strip()
                            released = cells[7].text.strip()
                            
                            # Extraire la région depuis l'image
                            region = "Unknown"
                            try:
                                region_img = region_element.find_element(By.TAG_NAME, "img")
                                region_src = region_img.get_attribute("src")
                                if "jp.gif" in region_src:
                                    region = "JP"
                                elif "us.gif" in region_src:
                                    region = "US"
                                elif "eu.gif" in region_src:
                                    region = "EU"
                                # Ajouter d'autres régions si nécessaire
                            except:
                                region = "Unknown"
                            
                            # Nettoyer le titre (enlever les liens HTML)
                            try:
                                title_link = cells[2].find_element(By.TAG_NAME, "a")
                                title = title_link.text.strip()
                            except:
                                title = cells[2].text.strip()
                            
                            if title and media_id:
                                game_data = {
                                    'ID': game_id,
                                    'Title': title,
                                    'Region': region,
                                    'Media_ID': media_id,
                                    'Box_ID': box_id,
                                    'Genre': genre,
                                    'Released': released
                                }
                                page_games.append(game_data)
                                
                    except Exception as e:
                        print(f"⚠️ Error parsing row {row_idx}: {e}")
                        continue
                        
                print(f"✅ PS Vita Page {page_num}: {len(page_games)} titles found")
                return page_games
                
            except Exception as e:
                print(f"❌ Attempt {attempt + 1} failed for page {page_num}: {e}")
                if attempt == max_retries - 1:
                    return []
                time.sleep(random.uniform(3, 6))
            
        return []

    def scrape_all_titles(self, max_pages=39, start_page=1):
        """Scraper toutes les pages de titles PS Vita"""
        if start_page == 1:
            self.games_data = []

        # Charger les données existantes si on reprend
        if start_page > 1:
            try:
                with open('psvita_titles_progress.json', 'r', encoding='utf-8') as f:
                    progress_data = json.load(f)
                    self.games_data = progress_data.get('games_data', [])
                    print(f"📂 Loaded {len(self.games_data)} existing titles")
            except FileNotFoundError:
                print("⚠️ No previous progress found, starting fresh")

        consecutive_empty_pages = 0

        print(f"🚀 Starting to scrape PS Vita titles pages {start_page} to {max_pages}")
        print(f"🎯 Expected total: ~3,000+ PS Vita titles from Renascene")
        print("=" * 60)

        start_time = time.time()

        for page in range(start_page, max_pages + 1):
            progress = ((page - start_page + 1) / (max_pages - start_page + 1)) * 100
            elapsed = time.time() - start_time
            estimated_total = elapsed / (page - start_page + 1) * (max_pages - start_page + 1) if page > start_page else 0
            remaining = estimated_total - elapsed if page > start_page else 0

            print(f"\n📄 Page {page}/{max_pages} ({progress:.1f}%) - ETA: {remaining/60:.1f} min")

            page_data = self.scrape_page(page)

            if not page_data:
                consecutive_empty_pages += 1
                print(f"⚠️ Empty page {page} (consecutive: {consecutive_empty_pages})")
                if consecutive_empty_pages >= 3:
                    print("🛑 3 consecutive empty pages, stopping scraping")
                    break
            else:
                consecutive_empty_pages = 0
                self.games_data.extend(page_data)
                print(f"📊 Total titles so far: {len(self.games_data)}")

            # Sauvegarder tous les 5 pages
            if page % 5 == 0:
                self.save_progress(page)

            # Rate limiting
            time.sleep(random.uniform(1, 3))

        return self.games_data

    def save_progress(self, current_page):
        """Sauvegarder le progrès"""
        progress_data = {
            'current_page': current_page,
            'total_games': len(self.games_data),
            'last_updated': time.strftime('%Y-%m-%d %H:%M:%S'),
            'games_data': self.games_data
        }
        
        with open('psvita_titles_progress.json', 'w', encoding='utf-8') as f:
            json.dump(progress_data, f, indent=2, ensure_ascii=False)
        print(f"💾 Progress saved: {len(self.games_data)} titles")

    def save_to_csv(self, filename='psvita_titles.csv'):
        """Save games data to CSV file"""
        if not self.games_data:
            print("❌ No data to save")
            return

        try:
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                # Adapter les en-têtes pour Renascene
                fieldnames = ['ID', 'Title', 'Region', 'Media_ID', 'Box_ID', 'Genre', 'Released']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                writer.writeheader()
                for game in self.games_data:
                    writer.writerow(game)
            
            print(f"✅ Saved {len(self.games_data)} PS Vita titles to {filename}")
            
        except Exception as e:
            print(f"❌ Error saving to CSV: {e}")

    def close_driver(self):
        """Fermer le driver"""
        if self.driver:
            self.driver.quit()
            print("🔒 Driver closed")

class PSVitaUpdateDownloader:
    """PS Vita update downloader inspired by PySN"""

    def __init__(self, download_path='./psvita_titles_updates/'):
        self.download_path = Path(download_path)
        self.download_path.mkdir(parents=True, exist_ok=True)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
        })

    def request_update(self, title_id):
        """Request PS Vita update info from Sony servers with fallbacks"""
        try:
            # Clean title_id
            original_id = title_id
            title_id = title_id.strip().upper().replace('-', '')
            
            # Méthode 1: HMAC-SHA256 standard
            id = bytes('np_' + title_id, 'UTF-8')
            key = bytearray.fromhex('E5E278AA1EE34082A088279C83F9BBC806821C52F2AB5D2B4ABD995450355114')
            hash_value = hmac.new(key, id, hashlib.sha256).hexdigest()
            
            urls_to_try = [
                f'https://gs-sec.ww.np.dl.playstation.net/pl/np/{title_id}/{hash_value}/{title_id}-ver.xml',
                f'http://gs-sec.ww.np.dl.playstation.net/pl/np/{title_id}/{hash_value}/{title_id}-ver.xml',
                f'https://gs.ww.np.dl.playstation.net/pl/np/{title_id}/{hash_value}/{title_id}-ver.xml'
            ]
            
            # Essai avec plusieurs formats d'URL
            for idx, xml_url in enumerate(urls_to_try):
                print(f"      🌐 Tentative URL #{idx+1}: {xml_url}")
                try:
                    response = self.session.get(xml_url, stream=True, verify=False, timeout=30)
                    print(f"      📡 Status: {response.status_code}, Length: {len(response.content)}")
                    
                    if response.status_code == 200 and response.content and len(response.content) > 10:
                        # Trouvé un XML valide
                        root = ET.fromstring(response.content)
                        return root, "Success"
                except Exception as e:
                    print(f"      ⚠️ Erreur URL #{idx+1}: {str(e)}")
                    continue
                
            # Méthode de secours: recherche directe par motif de package
            # Note: cette partie nécessiterait une approche différente pour trouver directement les packages
            
            return None, 'No update XML found'
        
        except Exception as e:
            print(f"⚠️ Error processing {title_id}: {e}")
            return None, 'Error'

    def get_filename_from_url(self, url):
        """Extract filename from URL"""
        if not url:
            return "unknown_file.pkg"

        parsed = urlparse(url)
        filename = os.path.basename(parsed.path)

        if not filename or not filename.endswith('.pkg'):
            path_parts = parsed.path.split('/')
            for part in reversed(path_parts):
                if part.endswith('.pkg'):
                    filename = part
                    break
            else:
                filename = "unknown_file.pkg"

        return filename

    def discover_direct_packages(self, title_id):
        """Découvre les packages directs en utilisant les patterns observés"""
        title_id = title_id.strip().upper().replace('-', '')
        
        # Étendre les patterns observés pour inclure plus de variants
        t_variants = ['T0', 'T1', 'T2', 'T3', 'T4', 'T5', 'T6', 'T7', 'T8', 'T9', 'T10', 'T11', 'T12']
        base_url = f"http://gs.ww.np.dl.playstation.net/ppkg/np/{title_id}/{title_id}_"
        
        discovered_packages = []
        
        print(f"      🔍 Recherche de packages directs pour {title_id}...")
        
        for t_val in t_variants:
            folder_url = f"{base_url}{t_val}/"
            
            try:
                # Test si le dossier existe
                response = self.session.head(folder_url, timeout=15, allow_redirects=True)
                
                if response.status_code == 200:
                    print(f"      ✅ Dossier trouvé: {folder_url}")
                    
                    # Essayer de lister le contenu ou faire une requête GET pour voir la structure
                    try:
                        get_response = self.session.get(folder_url, timeout=15)
                        if get_response.status_code == 200:
                            content = get_response.text
                            
                            # Chercher des patterns de hash dans le HTML de listing
                            import re
                            # Pattern plus flexible pour les hash (peut être 16+ caractères)
                            hash_pattern = r'href="([a-f0-9]{16,})/"'
                            hash_matches = re.findall(hash_pattern, content)
                            
                            for hash_val in hash_matches:
                                hash_url = f"{folder_url}{hash_val}/"
                                print(f"        📁 Hash trouvé: {hash_val}")
                                
                                # Essayer de lister le contenu du dossier hash
                                hash_response = self.session.get(hash_url, timeout=15)
                                if hash_response.status_code == 200:
                                    hash_content = hash_response.text
                                    
                                    # Chercher des fichiers .pkg
                                    pkg_pattern = r'href="([^"]*\.pkg)"'
                                    pkg_matches = re.findall(pkg_pattern, hash_content)
                                    
                                    for pkg_file in pkg_matches:
                                        pkg_url = f"{hash_url}{pkg_file}"
                                        
                                        # Extraire les informations du nom de fichier
                                        version = "Unknown"
                                        if "-V" in pkg_file:
                                            version_match = re.search(r'-V(\d{4})', pkg_file)
                                            if version_match:
                                                v_num = version_match.group(1)
                                                version = f"{v_num[:2]}.{v_num[2:]}"
                                        
                                        # Obtenir la taille du fichier
                                        size = 0
                                        try:
                                            pkg_head = self.session.head(pkg_url, timeout=10)
                                            if 'content-length' in pkg_head.headers:
                                                size = int(pkg_head.headers['content-length'])
                                        except:
                                            pass
                                        
                                        package_info = {
                                            'version': version,
                                            'url': pkg_url,
                                            'sha1': 'N/A',
                                            'size': size,
                                            'filename': pkg_file,
                                            'type': 'Direct Discovery',
                                            'hash': hash_val,
                                            't_variant': t_val
                                        }
                                        
                                        discovered_packages.append(package_info)
                                        print(f"        📦 Package trouvé: {pkg_file} ({size/1024/1024:.1f} MB)")
                    
                    except Exception as e:
                        print(f"        ⚠️ Erreur lors de l'exploration: {e}")
                        
            except Exception as e:
                continue
        
        return discovered_packages

    def request_update_enhanced(self, title_id):
        """Version simplifiée qui extrait directement les liens du XML"""
        # Essayer la méthode XML standard
        xml_root, status = self.request_update(title_id)
        xml_updates = []
        
        if xml_root is not None:
            for item in xml_root.iter('package'):
                ver = item.get('version')
                url = item.get('url')  # C'est déjà le lien direct !
                sha1 = item.get('sha1sum')
                size = item.get('size')
                
                if url and ver:
                    filename = self.get_filename_from_url(url)
                    xml_updates.append({
                        'version': ver,
                        'url': url,  # Lien direct vers le .pkg
                        'sha1': sha1 if sha1 else 'N/A',
                        'size': int(size) if size else 0,
                        'filename': filename,
                        'type': 'XML Direct Link'
                    })
        
        if xml_updates:
            print(f"      📦 Total trouvé: {len(xml_updates)} liens directs depuis XML")
        
        return xml_updates

    def get_update_info(self, title_id):
        """Version mise à jour qui utilise la méthode améliorée"""
        updates = self.request_update_enhanced(title_id)
        return updates if updates else None

    def process_single_title(self, title_data):
        """Process a single PS Vita title and return update links"""
        media_id = title_data.get('Media_ID', '').strip().replace('-', '')
        title_name = title_data.get('Title', 'Unknown')
        region = title_data.get('Region', 'Unknown')
        genre = title_data.get('Genre', 'Unknown')
        
        try:
            print(f"🔍 Checking PS Vita {media_id} ({title_name})...")
            updates = self.get_update_info(media_id)

            if updates:
                # Séparer par type pour les statistiques
                xml_updates = [u for u in updates if u['type'] == 'XML Standard']
                direct_updates = [u for u in updates if u['type'] == 'Direct Discovery']
                
                result = {
                    'media_id': media_id,
                    'title_name': title_name,
                    'region': region,
                    'genre': genre,
                    'has_updates': True,
                    'updates_count': len(updates),
                    'xml_updates_count': len(xml_updates),
                    'direct_updates_count': len(direct_updates),
                    'total_size_bytes': sum(u['size'] for u in updates),
                    'updates': updates,
                    'status': 'success'
                }
                print(f"      ✅ {len(updates)} updates found ({len(xml_updates)} XML + {len(direct_updates)} direct)")
            else:
                result = {
                    'media_id': media_id,
                    'title_name': title_name,
                    'region': region,
                    'genre': genre,
                    'has_updates': False,
                    'status': 'no_updates'
                }
                print(f"      ❌ No updates")

            return result

        except Exception as e:
            return {
                'media_id': media_id,
                'title_name': title_name,
                'region': region,
                'genre': genre,
                'has_updates': False,
                'status': 'error',
                'error': str(e)
            }

    def batch_get_update_links(self, csv_file='psvita_titles.csv', max_titles=None, max_workers=6):
        """Process multiple PS Vita titles to get update links"""
        try:
            # Charger les données du CSV
            df = pd.read_csv(csv_file)
            titles_list = df.to_dict('records')
            
            if max_titles:
                titles_list = titles_list[:max_titles]
            
            total_titles = len(titles_list)
            print(f"🚀 Processing {total_titles} PS Vita titles with {max_workers} workers...")
            
            results = []
            successful_updates = 0
            errors = 0
            no_updates = 0
            
            start_time = time.time()
            
            # Traitement séquentiel pour éviter de surcharger les serveurs Sony
            for idx, title_data in enumerate(titles_list, 1):
                progress = (idx / total_titles) * 100
                elapsed = time.time() - start_time
                estimated_total = elapsed / idx * total_titles if idx > 0 else 0
                remaining = estimated_total - elapsed if idx > 0 else 0
                
                print(f"\n📄 [{idx}/{total_titles}] ({progress:.1f}%) - ETA: {remaining/60:.1f} min")
                
                result = self.process_single_title(title_data)
                results.append(result)
                
                # Statistiques
                if result['status'] == 'success' and result['has_updates']:
                    successful_updates += 1
                elif result['status'] == 'no_updates':
                    no_updates += 1
                else:
                    errors += 1
                
                # Sauvegarder le progrès tous les 50 titres
                if idx % 50 == 0:
                    self.save_batch_results(results, f'psvita_updates_progress_{idx}.json')
                    print(f"💾 Progress saved: {idx} titles processed")
                
                # Rate limiting pour éviter de surcharger les serveurs
                time.sleep(random.uniform(0.5, 1.5))
            
            # Sauvegarder les résultats finaux
            self.save_batch_results(results, 'psvita_updates_final.json')
            self.save_results_to_csv(results, 'psvita_updates_results.csv')
            
            # Statistiques finales
            total_time = time.time() - start_time
            print(f"\n" + "="*60)
            print(f"📊 FINAL STATISTICS:")
            print(f"   Total processed: {total_titles}")
            print(f"   ✅ With updates: {successful_updates}")
            print(f"   ❌ No updates: {no_updates}")
            print(f"   ⚠️ Errors: {errors}")
            print(f"   ⏱️ Total time: {total_time/60:.1f} minutes")
            print(f"   📈 Success rate: {(successful_updates/total_titles)*100:.1f}%")
            print(f"="*60)
            
            return results
            
        except Exception as e:
            print(f"❌ Error in batch processing: {e}")
            return []

    def save_batch_results(self, results, filename):
        """Save batch results to JSON file"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"⚠️ Error saving to {filename}: {e}")

    def save_results_to_csv(self, results, filename):
        """Save results to CSV file"""
        try:
            csv_data = []
            for result in results:
                base_row = {
                    'Media_ID': result['media_id'],
                    'Title': result['title_name'],
                    'Region': result['region'],
                    'Genre': result['genre'],
                    'Has_Updates': result['has_updates'],
                    'Status': result['status'],
                    'Updates_Count': result.get('updates_count', 0),
                    'XML_Updates': result.get('xml_updates_count', 0),
                    'Direct_Updates': result.get('direct_updates_count', 0),
                    'Total_Size_MB': result.get('total_size_bytes', 0) / 1024 / 1024 if result.get('total_size_bytes') else 0
                }
                
                if result['has_updates'] and 'updates' in result:
                    # Une ligne par update
                    for update in result['updates']:
                        row = base_row.copy()
                        row.update({
                            'Update_Version': update['version'],
                            'Update_URL': update['url'],
                            'Update_SHA1': update['sha1'],
                            'Update_Size_MB': update['size'] / 1024 / 1024 if update['size'] else 0,
                            'Update_Filename': update['filename'],
                            'Update_Type': update['type']
                        })
                        csv_data.append(row)
                else:
                    # Pas d'updates, une seule ligne
                    csv_data.append(base_row)
            
            df = pd.DataFrame(csv_data)
            df.to_csv(filename, index=False, encoding='utf-8')
            print(f"✅ Results saved to {filename}")
            
        except Exception as e:
            print(f"❌ Error saving CSV: {e}")

TOTAL_EXPECTED_TITLES = 3000

def print_banner():
    """Print application banner"""
    banner = """
    ╔═══════════════════════════════════════════════════════════╗
    ║          PS Vita Titles Scraper & Update Tool            ║
    ║              Renascene.com - PS Vita Section             ║
    ║               ~3,000+ PS Vita Titles                     ║
    ║             With Sony Update Links Collection            ║
    ╚═══════════════════════════════════════════════════════════╝
    """
    print(banner)

def print_menu():
    """Print main menu"""
    menu = """
    📋 Main Menu:
    ┌─────────────────────────────────────────────────────────────┐
    │ 1. 🕷️  Start full PS Vita titles scraping (39 pages)       │
    │ 2. ⏭️  Resume PS Vita titles scraping from last position   │
    │ 3. 📂 Load existing PS Vita titles CSV data                │
    │ 4. 🔍 Search for PS Vita updates by Media ID               │
    │ 5. 🔗 Get update links for first 25 titles (test)         │
    │ 6. 📦 Get update links for ALL PS Vita titles (~3k)       │
    │ 7. 📊 Show statistics from loaded data                     │
    │ 8. 🧪 Test scraping on page 1 of PS Vita titles           │
    │ 9. 🚪 Exit                                                 │
    └─────────────────────────────────────────────────────────────┘
    """
    print(menu)

def main():
    """Main CLI application"""
    print_banner()

    scraper = None
    downloader = PSVitaUpdateDownloader()
    titles_data = []

    try:
        while True:
            print_menu()
            choice = input("🎯 Choose an option (1-9): ").strip()

            if choice == '1':
                # Start full scraping
                scraper = PSVitaTitlesScraper()
                if scraper.driver:
                    titles_data = scraper.scrape_all_titles()  # Utilisera la valeur par défaut (24)
                    scraper.save_to_csv('psvita_titles.csv')
                    scraper.close_driver()
                else:
                    print("❌ Cannot start scraping without Selenium")

            elif choice == '2':
                # Resume scraping
                try:
                    with open('psvita_titles_progress.json', 'r') as f:
                        progress = json.load(f)
                        last_page = progress['current_page'] + 1
                        print(f"📂 Resuming from page {last_page}")
                        
                    scraper = PSVitaTitlesScraper()
                    if scraper.driver:
                        titles_data = scraper.scrape_all_titles(start_page=last_page)  # Utilisera la valeur par défaut (24)
                        scraper.save_to_csv('psvita_titles.csv')
                        scraper.close_driver()
                    else:
                        print("❌ Cannot resume scraping without Selenium")
                except FileNotFoundError:
                    print("❌ No previous progress found")

            elif choice == '3':
                # Load existing CSV
                try:
                    df = pd.read_csv('psvita_titles.csv')
                    titles_data = df.to_dict('records')
                    print(f"✅ Loaded {len(titles_data)} PS Vita titles from CSV")
                except FileNotFoundError:
                    print("❌ psvita_titles.csv not found")

            elif choice == '4':
                # Single title search
                media_id = input("🔍 Enter PS Vita Media ID (e.g., PCSE00000): ").strip().upper()
                if media_id:
                    result = downloader.process_single_title({
                        'Media_ID': media_id,
                        'Title': 'Manual Search',
                        'Region': 'N/A',
                        'Genre': 'N/A'
                    })
                    print(f"\n📊 Result: {json.dumps(result, indent=2)}")

            elif choice == '5':
                # Test with first 25 titles
                if not titles_data:
                    print("❌ No titles loaded. Load CSV first (option 3)")
                    continue
                
                print("🧪 Testing with first 25 titles...")
                results = downloader.batch_get_update_links(
                    csv_file='psvita_titles.csv',
                    max_titles=25,
                    max_workers=3
                )

            elif choice == '6':
                # Get all update links
                if not os.path.exists('psvita_titles.csv'):
                    print("❌ psvita_titles.csv not found. Run scraping first (option 1)")
                    continue
                
                confirm = input("⚠️  This will process ALL PS Vita titles. Continue? (y/N): ")
                if confirm.lower() == 'y':
                    results = downloader.batch_get_update_links(
                        csv_file='psvita_titles.csv',
                        max_workers=6
                    )

            elif choice == '7':
                # Show statistics
                if titles_data:
                    total = len(titles_data)
                    regions = {}
                    for title in titles_data:
                        region = title.get('Region', 'Unknown')
                        regions[region] = regions.get(region, 0) + 1
                    
                    print(f"\n📊 PS Vita Titles Statistics:")
                    print(f"   Total titles: {total}")
                    print(f"   Regions distribution:")
                    for region, count in sorted(regions.items()):
                        print(f"     {region}: {count}")
                else:
                    print("❌ No data loaded")


            elif choice == '8':
                # Test page 1
                scraper = PSVitaTitlesScraper()
                if scraper.driver:
                    test_data = scraper.scrape_page(1)
                    print(f"✅ Found {len(test_data)} titles on page 1")
                    if test_data:
                        print("📋 Sample titles:")
                        for i, title in enumerate(test_data[:5]):
                            print(f"   {i+1}. {title['Media_ID']} - {title['Title']}")

                        # Sauvegarder les données de test
                        save_option = input("📂 Voulez-vous sauvegarder ces résultats de test dans un CSV? (y/N): ")
                        if save_option.lower() == 'y':
                         scraper.games_data = test_data
                         scraper.save_to_csv('psvita_titles.csv')
                         print(f"✅ Données de test sauvegardées dans psvita_titles.csv")

                    scraper.close_driver()


            elif choice == '9':
                print("👋 Goodbye!")
                break

            else:
                print("❌ Invalid choice. Please select 1-9.")

    finally:
        if scraper:
            scraper.close_driver()

if __name__ == "__main__":
    main()
