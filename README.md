# 🎮 PS Vita Titles Scraper & Update Tool

A comprehensive Python tool for scraping PS Vita game titles from Renascene.com and discovering direct download links for game updates from Sony's servers.

## ✨ Features

- 🕷️ **Web Scraping**: Automatically scrapes ~3,000 PS Vita titles from Renascene.com
- 📦 **Update Discovery**: Finds direct download links for PS Vita game updates (.pkg files)
- 🔍 **Smart Search**: Uses HMAC-SHA256 authentication to query Sony's servers
- 📊 **Progress Tracking**: Resume scraping from where you left off
- 💾 **Multiple Formats**: Export data to CSV and JSON formats
- 🚀 **Batch Processing**: Process thousands of titles efficiently
- 📈 **Statistics**: Detailed reporting and progress tracking

## 🛠️ Installation

### Prerequisites

- Python 3.7+
- Chrome/Chromium browser installed
- Internet connection

### Setup

1. **Clone the repository**
```bash
git clone https://github.com/Axekinn/ps-vita-scraper.git
cd ps-vita-scraper
```

2. **Create virtual environment**
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Install ChromeDriver** (if not already installed)
```bash
# Ubuntu/Debian
sudo apt-get install chromium-chromedriver

# Or download from: https://chromedriver.chromium.org/
```

## 📋 Requirements

Create a `requirements.txt` file:
```txt
selenium>=4.15.0
requests>=2.31.0
pandas>=2.1.0
lxml>=4.9.3
```

## 🚀 Usage

Run the main script:
```bash
python "import os.py"
```

### Menu Options

```
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
```

## 📖 How It Works

### 1. Title Scraping
- Scrapes PS Vita game information from Renascene.com
- Extracts: Game ID, Title, Region, Media ID, Genre, Release Date
- Handles pagination automatically
- Saves progress every 5 pages

### 2. Update Discovery
- Uses Sony's official update servers
- Implements HMAC-SHA256 authentication
- Queries XML endpoints for update information
- Extracts direct download links for .pkg files

### 3. Data Processing
- Processes titles sequentially to avoid server overload
- Implements rate limiting and retry mechanisms
- Supports resume functionality for large batches

## 📁 Output Files

- `psvita_titles.csv` - Complete list of PS Vita titles
- `psvita_updates_final.json` - Detailed update information (JSON)
- `psvita_updates_results.csv` - Update links in CSV format
- `psvita_titles_progress.json` - Progress tracking file

## 🔧 Configuration

### Update Discovery Settings
```python
# Rate limiting (seconds between requests)
time.sleep(random.uniform(0.5, 1.5))

# Timeout settings
timeout=30  # XML requests
timeout=15  # Package discovery
```

### Web Scraping Settings
```python
# Chrome options
chrome_options.add_argument('--headless')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')
```

## 📊 Example Output

### Title Information
```csv
ID,Title,Region,Media_ID,Box_ID,Genre,Released
1,Uncharted: Golden Abyss,US,PCSA00029,PCSA-00029,Action/Adventure,2012-02-15
2,Persona 4 Golden,US,PCSE00120,PCSE-00120,RPG,2012-11-20
```

### Update Information
```json
{
  "media_id": "PCSE00120",
  "title_name": "Persona 4 Golden",
  "region": "US",
  "has_updates": true,
  "updates_count": 1,
  "updates": [
    {
      "version": "01.01",
      "url": "http://gs.ww.np.dl.playstation.net/ppkg/np/PCSE00120/...",
      "sha1": "A1B2C3D4E5F6...",
      "size": 45678912,
      "filename": "PCSE00120_update.pkg",
      "type": "XML Direct Link"
    }
  ]
}
```

## ⚡ Performance Tips

1. **Batch Size**: Process titles in smaller batches (25-100) for testing
2. **Rate Limiting**: Respect Sony's servers with appropriate delays
3. **Resume Feature**: Use progress files for large datasets
4. **Error Handling**: Monitor logs for failed requests

## 🚨 Important Notes

- **Rate Limiting**: The tool implements delays to avoid overwhelming Sony's servers
- **Legal Compliance**: Only accesses publicly available update information
- **Server Load**: Designed to be respectful of Sony's infrastructure
- **Data Accuracy**: Cross-references multiple sources for reliability

## 🔍 Troubleshooting

### Common Issues

1. **ChromeDriver Issues**
```bash
# Update ChromeDriver
sudo apt-get update
sudo apt-get install chromium-chromedriver
```

2. **Selenium Import Error**
```bash
pip install selenium
```

3. **Connection Timeouts**
- Check internet connection
- Verify Sony servers are accessible
- Increase timeout values if needed

## 📈 Statistics

- **~3,000+ PS Vita titles** from Renascene database
- **Multiple regions**: US, EU, JP, and others
- **Update success rate**: Varies by title availability
- **Processing speed**: ~1-3 titles per second (with rate limiting)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## 📄 License

This project is for educational and research purposes. Please respect Sony's terms of service and copyright policies.

## ⚠️ Disclaimer

This tool is designed for legitimate backup and preservation purposes. Users are responsible for complying with applicable laws and terms of service. The authors are not responsible for any misuse of this software.

## 🔗 Links

- [Renascene.com](https://renascene.com/psv/) - PS Vita Games Database
- [PlayStation Vita](https://en.wikipedia.org/wiki/PlayStation_Vita) - Console Information

---

**Author**: Axekinn  
**Version**: 1.0.0  
**Last Updated**: August 2025
