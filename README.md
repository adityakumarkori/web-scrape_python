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
```

## Current Phase 1 Functionality

Phase 1 provides the project foundation:

- ✅ Configuration loading from `.env`
- ✅ MongoDB Atlas connection manager with ping verification
- ✅ Separate dataset profiles (GRANIT and Blinkit) with field definitions
- ✅ CLI with argparse supporting dataset selection
- ✅ Unit tests for configuration, database, and profiles
- ✅ Clean project structure

**Not yet implemented (Phase 2+):**
- Web scraping logic
- Data processing and transformation
- MongoDB product persistence
- Excel/CSV export generation

## Upcoming Development Phases

| Phase | Focus |
|-------|-------|
| Phase 2 | Web scraping implementation for both datasets |
| Phase 3 | Data processing, validation, and MongoDB persistence |
| Phase 4 | Excel/CSV export and reporting |
| Phase 5 | Scheduling, monitoring, and production hardening |

## Project Structure

```
web_scrap_python/
├── main.py              # CLI entry point
├── config.py            # Configuration management
├── database.py          # MongoDB connection manager
├── profiles/
│   ├── __init__.py      # Profile registry
│   ├── granit.py        # GRANIT dataset profile
│   └── blinkit.py       # Blinkit dataset profile
├── tests/
│   ├── test_config.py
│   ├── test_database.py
│   └── test_profiles.py
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

Tests use mocks and do not require actual MongoDB credentials.

## License

MIT License