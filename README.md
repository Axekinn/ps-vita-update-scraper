# PS Vita Update Scraper 🎮

A modern Python scraper to automatically retrieve PS Vita game updates from Sony servers and the Renascene database.
Same thing for [PS3](https://github.com/Axekinn/ps3-update-scraper), the goal is to be able to copy everything at once and paste it into [Jdownloader](https://jdownloader.org/jdownloader2).
I'm too lazy to rewrite the same description, go see for yourself.

## 📋 Features

- 🔍 **Automatic scraping**: Crawls through 39 Renascene pages to retrieve PS Vita game information
- 🔐 **HMAC authentication**: Uses HMAC authentication to access Sony's secure servers
- 📦 **Update extraction**: Retrieves direct download links, versions, and metadata
- 🧹 **Clean data**: Generates clean JSON with only essential information
- ⚡ **Multi-threading**: Parallel processing for optimal performance
- 🛡️ **Robust error handling**: Automatic retry and timeout management

## 🚀 Installation

### Prerequisites

- Python 3.7 or higher
- pip (Python package manager)

### Environment Setup

1. **Clone the repository**
```bash
git clone https://github.com/Axekinn/ps-vita-update-scraper.git
cd ps-vita-update-scraper
```

2. **Create a virtual environment**
```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# or
.venv\Scripts\activate     # Windows
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

### Required Dependencies

Create a `requirements.txt` file with:
```txt
requests>=2.31.0
beautifulsoup4>=4.12.0
lxml>=4.9.0
urllib3>=2.0.0
```

## 📖 Usage

### 1. Scrape PS Vita Data

Run the main scraper to retrieve all information:

```bash
python vita_scraper.py
```

This script will:
- Crawl through 39 Renascene pages
- Extract PS Vita Title IDs
- Query Sony servers for updates
- Generate `ps_vita_updates.json` with all data

### 2. Extract Essential Data

To get a clean JSON with only name, version, and link:

```bash
python extract_updates.py
```

This generates `ps_vita_updates_extracted.json` in the format:
```json
[
  {
    "nom_jeu": "Russian Subway Dogs",
    "version_update": "01.01",
    "lien_telechargement": "http://gs.ww.np.dl.playstation.net/ppkg/np/PCSE01226/..."
  }
]
```

## 📁 Project Structure

```
ps-vita-update-scraper/
├── vita_scraper.py              # Main scraping script
├── extract_updates.py           # Essential data extractor
├── requirements.txt             # Python dependencies
├── ps_vita_updates.json         # Complete data (generated)
├── ps_vita_updates_extracted.json  # Clean data (generated)
└── README.md                    # This file
```

## ⚙️ Configuration

### Important variables in `vita_scraper.py`

```python
TOTAL_PAGES = 39          # Number of Renascene pages to scrape
MAX_WORKERS = 8           # Number of threads for requests
REQUEST_TIMEOUT = 30      # HTTP request timeout
RETRY_COUNT = 3           # Number of retry attempts on failure
VERIFY_SSL = False        # SSL verification (disabled by default)
```

### PS Vita Title ID Format

The scraper looks for Title IDs in the format: `PC[A-Z]{2}[0-9]{5}`
- Examples: `PCSE01226`, `PCSH10263`, `PCSB01464`

## 🔧 Technical Details

### 1. Sony Authentication

The script uses the same HMAC authentication method as official tools:

```python
key = bytearray.fromhex('E5E278AA1EE34082A088279C83F9BBC806821C52F2AB5D2B4ABD995450355114')
id_bytes = bytes('np_' + title_id, 'UTF-8')
hash_value = hmac.new(key, id_bytes, hashlib.sha256).hexdigest()
```

### 2. Sony Server URLs

- **Primary**: `https://gs-sec.ww.np.dl.playstation.net/pl/np/{title_id}/{hash}/{title_id}-ver.xml`
- **Fallback**: `https://a0.ww.np.dl.playstation.net/tpl/np/{title_id}/{title_id}-ver.xml`

### 3. XML Parsing

The script analyzes update XML files to extract:
- Package download URLs
- Update versions
- SHA1 hashes for verification
- File sizes

## 📊 Expected Results

The script typically generates:
- **~2,700+ updates** for PS Vita games
- **Complete data**: Renascene metadata + update information
- **Clean format**: game name, version, download link only

## 🛠️ Troubleshooting

### Common Errors

**SSL Certificate errors**
```bash
# Solution: Disable SSL verification
VERIFY_SSL = False
```

**Timeout errors**
```bash
# Solution: Increase timeout
REQUEST_TIMEOUT = 60
```

**Rate limiting**
```bash
# Solution: Reduce number of workers
MAX_WORKERS = 4
```

### Logs

Detailed logs are displayed during execution:
```
2025-08-13 10:30:15 INFO: Scraping PS Vita renascene across 39 pages...
2025-08-13 10:30:16 INFO: PS Vita page 1: 75 entries
2025-08-13 10:32:45 INFO: Unique valid PS Vita Title IDs: 1247
2025-08-13 10:35:20 INFO: Wrote 2738 PS Vita records with updates
```

## 📝 License

This project is licensed under the MIT License. See the `LICENSE` file for more details.

## ⚠️ Disclaimer

This script is intended for educational and preservation purposes. Please respect Sony's and Renascene's terms of service when using their services.

## 🤝 Contributing

Contributions are welcome! Feel free to:
- Open issues to report bugs
- Propose improvements via pull requests
- Improve documentation

## 📞 Support

If you encounter problems:
1. Check error logs
2. Consult the troubleshooting section
3. Open an issue on GitHub with error details

---

**Developed with ❤️ for the PS Vita community**
