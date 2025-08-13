import requests
from bs4 import BeautifulSoup
import time
import json
import logging
from urllib.parse import urljoin, urlparse
import re
import hmac
import hashlib
import xml.etree.ElementTree as ET
from typing import List, Dict, Optional


class RenasceneViScraper:
    """
    A web scraper for extracting PlayStation Vita game data from Renascene.com
    with official Sony download links generation
    """
    
    def __init__(self, base_url: str = "https://renascene.com/psv/", delay: float = 1.0):
        """
        Initialize the scraper
        
        Args:
            base_url: Base URL for the Renascene PSV section
            delay: Delay between requests in seconds
        """
        self.base_url = base_url
        self.delay = delay
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        # Setup logging
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)
        
        # Disable SSL warnings
        requests.packages.urllib3.disable_warnings()
        
    def make_request(self, url: str, retries: int = 3) -> Optional[requests.Response]:
        """
        Make a request with error handling and retries
        """
        for attempt in range(retries):
            try:
                response = self.session.get(url, timeout=30, verify=False)
                response.raise_for_status()
                return response
            except requests.exceptions.RequestException as e:
                self.logger.warning(f"Request failed (attempt {attempt + 1}/{retries}): {e}")
                if attempt < retries - 1:
                    time.sleep(self.delay * (attempt + 1))
                else:
                    self.logger.error(f"Failed to fetch {url} after {retries} attempts")
                    return None
        return None
    
    def generate_sony_download_links(self, title_id: str) -> List[Dict[str, str]]:
        """
        Generate official Sony download links for a given title ID
        Based on PySN.py logic
        """
        download_links = []
        
        try:
            # PlayStation Vita key (from PySN.py)
            key = bytearray.fromhex('E5E278AA1EE34082A088279C83F9BBC806821C52F2AB5D2B4ABD995450355114')
            id_bytes = bytes('np_' + title_id, 'UTF-8')
            hash_value = hmac.new(key, id_bytes, hashlib.sha256).hexdigest()
            
            # Generate the XML URL for PS Vita updates
            xml_url = f'https://gs-sec.ww.np.dl.playstation.net/pl/np/{title_id}/{hash_value}/{title_id}-ver.xml'
            
            self.logger.debug(f"Requesting update info for {title_id}: {xml_url}")
            
            response = self.make_request(xml_url)
            if response and response.status_code == 200 and response.text:
                try:
                    root = ET.fromstring(response.content)
                    
                    # Extract update information
                    for package in root.iter('package'):
                        version = package.get('version', 'Unknown')
                        url = package.get('url', '')
                        sha1 = package.get('sha1sum', 'N/A')
                        size = package.get('size', '0')
                        
                        if url:
                            download_links.append({
                                'version': version,
                                'url': url,
                                'sha1': sha1,
                                'size': size,
                                'type': 'Official Update'
                            })
                    
                    # Also check for DRM-free updates
                    for url_elem in root.iter('url'):
                        url = url_elem.get('url', '')
                        sha1 = url_elem.get('sha1sum', 'N/A')
                        size = url_elem.get('size', '0')
                        
                        if url:
                            download_links.append({
                                'version': 'DRM-Free',
                                'url': url,
                                'sha1': sha1,
                                'size': size,
                                'type': 'DRM-Free Update'
                            })
                            
                except ET.ParseError as e:
                    self.logger.error(f"XML parsing error for {title_id}: {e}")
            
        except Exception as e:
            self.logger.error(f"Error generating Sony links for {title_id}: {e}")
        
        return download_links
    
    def extract_title_id_from_media_id(self, media_id: str) -> str:
        """
        Extract title ID from Media ID and remove hyphens
        """
        if not media_id:
            return ""
        
        # Media ID format is usually like "PCSH-10315 (BOX ID: VLAS-40096)"
        # We want the first part without the hyphen
        title_id = media_id.split()[0] if media_id else ""
        # Remove hyphens to get the correct format (PCSH10315 instead of PCSH-10315)
        title_id = title_id.replace('-', '')
        return title_id.strip()
    
    def extract_game_data(self, game_card) -> Dict[str, str]:
        """
        Extract game data from a game card div
        """
        game_data = {
            "Title": "",
            "Developer": "",
            "Publisher": "",
            "Genre": "",
            "Language": "",
            "Media ID": "",
            "Update": "",
            "Dump status": "",
            "Download Links": []
        }
        
        try:
            # Extract game title from the header or title area
            title_element = game_card.find('a') or game_card.find('strong')
            if title_element:
                game_data["Title"] = self.clean_text(title_element.get_text())
            
            # Look for all text content and extract specific fields
            card_text = game_card.get_text()
            
            # Extract Developer
            dev_match = re.search(r'Developer\s*([^\n\r]+)', card_text)
            if dev_match:
                game_data["Developer"] = self.clean_text(dev_match.group(1))
            
            # Extract Publisher
            pub_match = re.search(r'Publisher\s*([^\n\r]+)', card_text)
            if pub_match:
                game_data["Publisher"] = self.clean_text(pub_match.group(1))
            
            # Extract Genre
            genre_match = re.search(r'Genre\s*([^\n\r]+)', card_text)
            if genre_match:
                game_data["Genre"] = self.clean_text(genre_match.group(1))
            
            # Extract Language
            lang_match = re.search(r'Language\s*([^\n\r]+)', card_text)
            if lang_match:
                game_data["Language"] = self.clean_text(lang_match.group(1))
            
            # Extract Media ID
            media_match = re.search(r'Media ID\s*([^\n\r]+)', card_text)
            if media_match:
                game_data["Media ID"] = self.clean_text(media_match.group(1))
            
            # Extract Update info
            update_match = re.search(r'Update\s*([^\n\r]+)', card_text)
            if update_match:
                game_data["Update"] = self.clean_text(update_match.group(1))
            
            # Extract Dump status
            dump_match = re.search(r'Dump status\s*([^\n\r]+)', card_text)
            if dump_match:
                game_data["Dump status"] = self.clean_text(dump_match.group(1))
            
            # Generate official Sony download links based on Media ID
            if game_data["Media ID"]:
                title_id = self.extract_title_id_from_media_id(game_data["Media ID"])
                if title_id:
                    self.logger.info(f"Generating Sony links for {title_id}")
                    sony_links = self.generate_sony_download_links(title_id)
                    game_data["Download Links"] = sony_links
                
        except Exception as e:
            self.logger.error(f"Error extracting game data: {e}")
            
        return game_data
    
    def clean_text(self, text: str) -> str:
        """
        Clean and normalize text data
        """
        if not text:
            return ""
        return re.sub(r'\s+', ' ', text.strip())
    
    def scrape_page(self, page_num: int) -> List[Dict[str, str]]:
        """
        Scrape data from a single page
        """
        url = f"{self.base_url}?target=title&sort=Array&page={page_num}"
        self.logger.info(f"Scraping page {page_num}: {url}")
        
        response = self.make_request(url)
        if not response:
            return []
        
        try:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find game cards - based on the HTML structure
            game_cards = []
            
            # Try multiple selectors to find game entries
            selectors = [
                'tr[bgcolor]',  # Table rows with background color
                'tr:has(td)',   # Table rows with td elements
                'div.game',     # Div with game class (if exists)
                'div[id*="game"]',  # Div with id containing "game"
            ]
            
            for selector in selectors:
                found_cards = soup.select(selector)
                if found_cards:
                    game_cards = found_cards
                    self.logger.debug(f"Found {len(game_cards)} game cards using selector: {selector}")
                    break
            
            # If no specific selectors work, look for table rows
            if not game_cards:
                table = soup.find('table')
                if table:
                    rows = table.find_all('tr')
                    # Skip the first row (header) and filter rows that have enough content
                    game_cards = [row for row in rows[1:] if row.find('td')]
            
            if not game_cards:
                self.logger.warning(f"No game cards found on page {page_num}")
                # Debug: save the HTML to see the structure
                with open(f'debug_page_{page_num}.html', 'w', encoding='utf-8') as f:
                    f.write(soup.prettify())
                self.logger.info(f"Saved HTML to debug_page_{page_num}.html for inspection")
                return []
            
            page_data = []
            for card in game_cards:
                game_data = self.extract_game_data(card)
                # Only add if we extracted meaningful data
                if game_data["Title"] or game_data["Developer"] or game_data["Media ID"]:
                    page_data.append(game_data)
            
            self.logger.info(f"Extracted {len(page_data)} games from page {page_num}")
            return page_data
            
        except Exception as e:
            self.logger.error(f"Error parsing page {page_num}: {e}")
            return []
    
    def scrape_all_pages(self, max_pages: int = 130) -> List[Dict[str, str]]:
        """
        Scrape data from all pages
        """
        all_data = []
        
        for page_num in range(1, max_pages + 1):
            try:
                page_data = self.scrape_page(page_num)
                all_data.extend(page_data)
                
                # Add delay between requests to be respectful
                time.sleep(self.delay)
                
                # Log progress every 10 pages
                if page_num % 10 == 0:
                    self.logger.info(f"Progress: {page_num}/{max_pages} pages completed. Total games: {len(all_data)}")
                    
            except KeyboardInterrupt:
                self.logger.info("Scraping interrupted by user")
                break
            except Exception as e:
                self.logger.error(f"Error on page {page_num}: {e}")
                continue
        
        self.logger.info(f"Scraping completed. Total games extracted: {len(all_data)}")
        return all_data
    
    def save_data(self, data: List[Dict[str, str]], filename: str = "psv_games_data.json"):
        """
        Save scraped data to a JSON file
        """
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            self.logger.info(f"Data saved to {filename}")
        except Exception as e:
            self.logger.error(f"Error saving data: {e}")

def main():
    """
    Main function to run the scraper
    """
    # Initialize scraper
    scraper = RenasceneViScraper(delay=2.0)  # 2 second delay between requests
    
    print("Starting PlayStation Vita game data scraping...")
    print("This will extract game info from Renascene and generate official Sony download links")
    print("Please ensure this complies with the website's terms of service and robots.txt")
    
    # Test with just the first few pages initially
    all_game_data = scraper.scrape_all_pages(max_pages=5)  # Start with 5 pages for testing
    
    # Save data
    scraper.save_data(all_game_data, "psv_games_data_with_sony_links.json")
    
    # Print summary
    print(f"\nScraping Summary:")
    print(f"Total games extracted: {len(all_game_data)}")
    
    if all_game_data:
        print(f"\nSample data structure:")
        sample_game = all_game_data[0]
        print(json.dumps(sample_game, indent=2))
        
        # Count games with download links
        games_with_links = sum(1 for game in all_game_data if game.get("Download Links"))
        print(f"\nGames with official download links: {games_with_links}")

if __name__ == "__main__":
    main()