import argparse
import sys
import os
from profiles import get_profile, PROFILES
from database import check_connection
from scraper import scrape_products
from processor import load_input_data, process_products, print_summary


def main():
    parser = argparse.ArgumentParser(
        description="GRANIT + Blinkit Data Project - Phase 2 Data Collection & Processing"
    )
    parser.add_argument(
        "--dataset",
        choices=["granit", "blinkit", "all"],
        required=True,
        help="Dataset to process: granit, blinkit, or all"
    )
    parser.add_argument(
        "--input",
        help="Input directory path (default: data/<dataset>/)"
    )
    parser.add_argument(
        "--scrape",
        action="store_true",
        help="Enable web scraping (requires approved source configuration)"
    )
    parser.add_argument(
        "--max-records",
        type=int,
        default=100,
        help="Maximum records to process (default: 100)"
    )
    args = parser.parse_args()

    datasets = []
    if args.dataset == "all":
        datasets = list(PROFILES.keys())
    else:
        datasets = [args.dataset]

    for name in datasets:
        profile = get_profile(name)
        if not profile:
            print(f"Unknown dataset: {name}")
            sys.exit(1)

        print(f"\n{'='*50}")
        print(f"Dataset: {profile.DISPLAY_NAME}")
        print(f"Collection: {profile.COLLECTION_NAME}")
        print(f"{'='*50}")

        connected, msg = check_connection()
        if connected:
            print(f"MongoDB: Connected")
        else:
            print(f"MongoDB: {msg} (continuing without persistence)")

        input_dir = args.input or f"data/{name}"
        
        print(f"\nLoading input data from: {input_dir}")
        products = load_input_data(name, input_dir)
        
        if not products:
            print(f"No input files found in {input_dir}")
            print("  Expected: products.csv and/or products.json")
            if args.scrape:
                print("Scraping enabled - attempting to scrape...")
                scrape_config = profile.EXTRACTION_CONFIG
                if scrape_config.get("enabled"):
                    scraped = scrape_products(scrape_config, profile, args.max_records)
                    print(f"Scraped {len(scraped)} products")
                    products.extend(scraped)
                else:
                    print("Scraping not configured for this dataset (EXTRACTION_CONFIG.enabled=False)")
            else:
                print("Use --scrape to enable scraping (requires approved source config)")
        
        if not products:
            print("No data to process. Skipping.")
            continue

        print(f"\nProcessing {len(products)} records...")
        result = process_products(products, profile)
        print_summary(result, profile)
        
        if args.scrape and not profile.EXTRACTION_CONFIG.get("enabled"):
            print("\nNote: Web scraping is disabled by default for this dataset.")
            print("To enable, set EXTRACTION_CONFIG.enabled=True in the profile with approved domains.")

    print(f"\n{'='*50}")
    print("Phase 2 processing complete.")
    print("Ready for Phase 3: MongoDB persistence.")
    print(f"{'='*50}")


if __name__ == "__main__":
    main()