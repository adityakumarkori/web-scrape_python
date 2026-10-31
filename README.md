# GRANIT + Blinkit Data Project

A Python project for scraping and managing data from two independent datasets:
- **GRANIT Parts** — EU Region
- **Blinkit** — Bengaluru

## Project Purpose

This project provides a clean foundation for collecting, storing, and managing product data from GRANIT (European auto parts catalog) and Blinkit (Indian quick-commerce platform). The application shares common infrastructure while maintaining completely separate dataset profiles.

## Prerequisites

- Python 3.12+
- MongoDB Atlas account (or local MongoDB instance)
- Virtual environment tool (venv, conda, etc.)

## Installation

```bash
# Clone the repository
git clone <repository-url>
cd web_scrap_python

# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
.venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt
```

## MongoDB Atlas Setup

1. Create a MongoDB Atlas account at https://www.mongodb.com/atlas
2. Create a new cluster (free tier available)
3. Create a database user with read/write permissions
4. Whitelist your IP address (or use 0.0.0.0/0 for development)
5. Get the connection string (URI) from the "Connect" dialog

## Configuration

Copy the example environment file and configure it:

```bash
cp .env.example .env
```

Edit `.env` with your actual values:

```env
MONGODB_URI=mongodb+srv://<username>:<password>@<cluster>/
MONGODB_DATABASE=granit_blinkit_data

REQUEST_TIMEOUT=20
REQUEST_DELAY=2
MAX_RECORDS=100
```

**Important**: Never commit `.env` to version control. It's included in `.gitignore`.

## CLI Commands

```bash
# Show help
python main.py --help

# Process GRANIT dataset
python main.py --dataset granit

# Process Blinkit dataset
python main.py --dataset blinkit

# Process both datasets
python main.py --dataset all

# Enable web scraping (requires approved source configuration)
python main.py --dataset granit --scrape

# Limit records processed
python main.py --dataset all --max-records 50

# Specify custom input directory
python main.py --dataset granit --input ./data/granit
```

## Current Phase 2 Functionality

Phase 2 provides web scraping and data processing capabilities:

- ✅ **Reusable Synchronous Scraper** (`scraper.py`)
  - URL safety validation (SSRF protection: blocks localhost, private IPs, link-local)
  - Configurable request timeout, delay, and user-agent
  - HTTP/HTTPS only, redirect validation against allowed domains
  - HTML parsing with BeautifulSoup4
  - JSON-LD structured data extraction (schema.org Product types)
  - Open Graph / Twitter Card / metadata extraction
  - CSS selector-based field extraction (configurable per profile)
  - Pagination support with configurable next-page selectors

- ✅ **Dataset Profiles with Extraction Configuration** (`profiles/granit.py`, `profiles/blinkit.py`)
  - GRANIT: Article number, EAN/GTIN, regional pricing (multi-country, VAT), specifications, compliance, inventory
  - Blinkit: SKU, barcode, pricing (MRP, selling price, GST), packaging, supplier, inventory, delivery (Bengaluru pincodes)
  - Extraction config with allowed domains, base URLs, JSON-LD types, field selectors

- ✅ **Data Processor** (`processor.py`)
  - Input loading from CSV and JSON files
  - Data cleaning: whitespace normalization, empty-to-null, URL normalization, date parsing, decimal parsing
  - Dataset-specific validation:
    - GRANIT: Required fields, GTIN/EAN check digit, ISO country/currency codes, VAT range, net/gross price consistency
    - Blinkit: Required fields, barcode/GTIN check digit, GST rate validation, MRP vs selling price, expiry vs manufacturing date, Bengaluru pincode validation
  - Deduplication by composite keys (article_number+EAN for GRANIT, SKU+product_id for Blinkit)
  - Processing pipeline with summary statistics

- ✅ **CLI Integration** (`main.py`)
  - `--dataset`: granit, blinkit, or all
  - `--input`: custom input directory
  - `--scrape`: enable web scraping
  - `--max-records`: limit records processed

**Not yet implemented (Phase 3+):**
- MongoDB product persistence
- Excel/CSV export generation

## Development Phases

| Phase | Focus | Status |
|-------|-------|--------|
| Phase 1 | Project foundation, config, MongoDB, profiles, CLI | ✅ Complete |
| Phase 2 | Web scraping, data processing, validation, deduplication | ✅ Complete |
| Phase 3 | MongoDB persistence, bulk operations, indexing | 🔄 Planned |
| Phase 4 | Excel/CSV export and reporting | 🔄 Planned |
| Phase 5 | Scheduling, monitoring, production hardening | 🔄 Planned |

## Project Structure

```
web_scrap_python/
├── main.py              # CLI entry point
├── config.py            # Configuration management
├── database.py          # MongoDB connection manager
├── scraper.py           # Web scraping module
├── processor.py         # Data processing & validation
├── profiles/
│   ├── __init__.py      # Profile registry
│   ├── granit.py        # GRANIT dataset profile
│   └── blinkit.py       # Blinkit dataset profile
├── tests/
│   ├── test_config.py
│   ├── test_database.py
│   ├── test_profiles.py
│   ├── test_scraper.py
│   └── test_processor.py
├── output/              # Generated files (gitignored)
├── .env                 # Local environment (gitignored)
├── .env.example         # Template environment
├── .gitignore
├── requirements.txt
└── README.md
```

## Running Tests

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest tests/ -v
```

Tests use mocks and do not require actual MongoDB credentials or internet access.

## License

MIT License