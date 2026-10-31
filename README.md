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
| Phase 3 | MongoDB persistence, bulk operations, indexing | ✅ Complete |
| Phase 4 | Excel/CSV export and reporting | ✅ Complete |
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

## Phase 4: Final Testing & Delivery

This phase validates the complete data collection and export pipeline:

### Excel Export Validation
- Generated `output/GRANIT_Parts_EU_Sample_Dataset.xlsx` with all 9 worksheets:
  - README, Products, Regional Pricing, Specifications, Compliance, 
    Inventory & Logistics, Data Quality, Data Dictionary, Sources & Assumptions
- Generated `output/Blinkit_Bengaluru_Sample_Dataset.xlsx` with all 10 worksheets:
  - README, Products, Pricing & Tax, Packaging & Ingredients, Suppliers,
    Dark Stores & Inventory, Delivery & Zones, Data Quality, Data Dictionary, 
    Sources & Assumptions
- Verified correct headers, column ordering, currency/percentage/VAT formatting
- Decimal128 financial precision maintained
- Data provenance and source attribution preserved
- Synthetic/unverified records clearly labelled

### CLI End-to-End Testing
All commands validated:
- `python main.py --help` - Shows CLI help
- `python main.py --dataset granit` - Processes GRANIT dataset
- `python main.py --dataset blinkit` - Processes Blinkit dataset
- `python main.py --dataset all` - Processes both datasets
- `python main.py --dataset all --export-only` - Exports without scraping

### Security Review
- `.env` is gitignored (verified in `.gitignore`)
- No credentials or connection strings with passwords committed
- `.env.example` contains placeholders only (`<username>`, `<password>`, `<cluster>`)
- Database errors do not expose credentials
- Source URLs and collection timestamps preserved
- Missing internal business information is not fabricated

### Test Execution
- `pytest -q` runs all 139 tests successfully
- All tests use mocks; no live MongoDB or website access required

## CSV/JSON Input Instructions

Input data can be provided via CSV or JSON files in `data/<dataset>/`:

### CSV Format
```csv
article_number,product_name
ART-001,Brake Pad Set
```

Supported fields depend on dataset profile (GRANIT or Blinkit).

### JSON Format
```json
[{"article_number": "ART-001", "product_name": "Brake Pad Set"}]
```

Single objects are also supported and will be wrapped in a list.

### CLI Input Directory
Use `--input` flag to specify custom input directory:
```bash
python main.py --dataset granit --input ./data/granit
```

## Data Provenance and Limitations

### GRANIT Parts - EU Region
- Regional pricing covers EU countries with VAT rates varying by country
- Compliance status based on manufacturer declarations (not independently verified)
- EAN/GTIN check digits validated algorithmically
- Inventory levels are real-time snapshots at collection time
- Some products may lack complete specification data
- Currency codes are ISO 4217 standard

### Blinkit - Bengaluru
- GST rates are Indian national rates (5%, 12%, 18%, 28%)
- Pincodes limited to Bengaluru region (560001-560109)
- MRP regulated under Legal Metrology Act
- Delivery SLA limited to serviceable areas
- Available quantity is store-specific
- GST rates based on product category

### General
- Synthetic records are clearly marked with `_synthetic: True`
- Unverified records are marked with `validation_status: "invalid"`
- No website scraping is performed without explicit `--scrape` flag and approved configuration
- All financial values use Decimal128 precision for MongoDB storage