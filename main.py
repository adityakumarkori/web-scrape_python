import argparse
import sys
import os
from profiles import get_profile, PROFILES
from database import connect_db, close_db, get_database, get_collection, save_products, get_products, get_product_count, check_connection
from scraper import scrape_products
from processor import load_input_data, process_products, print_summary
from exporter import export_dataset


def main():
    parser = argparse.ArgumentParser(
        description="GRANIT + Blinkit Data Project - Phase 3 Data Collection, Processing & Persistence"
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
    parser.add_argument(
        "--export-only",
        action="store_true",
        help="Export existing products from MongoDB without scraping or processing"
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
        
        if args.export_only:
            # Export-only mode: retrieve existing products and generate workbooks
            print(f"\nExport-only mode: retrieving existing records from MongoDB...")
            
            try:
                client, db = connect_db()
                granit_count = get_product_count("granit")
                blinkit_count = get_product_count("blinkit")
                
                if name == "granit" or name == "all":
                    if granit_count == 0:
                        print("No GRANIT products found in MongoDB. Nothing to export.")
                    else:
                        print(f"Found {granit_count} GRANIT product(s) in MongoDB.")
                        products = get_products("granit")
                        print(f"Retrieved {len(products)} GRANIT product record(s).")
                        
                        # Export to Excel
                        print("Generating GRANIT Excel workbook...")
                        from exporter import export_dataset
                        result = export_dataset(products, "granit")
                        if result["granit"]:
                            print(f"GRANIT workbook saved to: {result['granit']}")
                
                if name == "blinkit" or name == "all":
                    if blinkit_count == 0:
                        print("No Blinkit products found in MongoDB. Nothing to export.")
                    else:
                        print(f"Found {blinkit_count} Blinkit product(s) in MongoDB.")
                        products = get_products("blinkit")
                        print(f"Retrieved {len(products)} Blinkit product record(s).")
                        
                        # Export to Excel
                        print("Generating Blinkit Excel workbook...")
                        from exporter import export_dataset
                        result = export_dataset(products, "blinkit")
                        if result["blinkit"]:
                            print(f"Blinkit workbook saved to: {result['blinkit']}")
            
            except ConnectionError as e:
                print(f"MongoDB connection error: {e}")
                print("Cannot export without MongoDB connection.")
            finally:
                close_db()
            
            print(f"\n{'='*50}")
            print("Phase 3 export complete.")
            print(f"{'='*50}")
            continue

        # Normal execution mode
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
        
        # Save valid products to MongoDB
        print(f"\nSaving valid records to MongoDB...")
        save_results = save_products(result["valid_products"], name)
        print(f"MongoDB Save Results:")
        print(f"  Inserted: {save_results['inserted']}")
        print(f"  Updated: {save_results['updated']}")
        print(f"  Skipped: {save_results['skipped']}")
        print(f"  Failed: {save_results['failed']}")
        print(f"  Total: {save_results['total']}")
        
        # Report rejected products
        if result["rejected_count"] > 0:
            print(f"\n{result['rejected_count']} record(s) rejected due to validation errors:")
            for err in result["validation_errors"][:3]:
                identifier = err["product"].get("article_number") or err["product"].get("sku") or "unknown"
                print(f"  - {identifier}: {'; '.join(err['errors'])}")
            if len(result["validation_errors"]) > 3:
                print(f"  ... and {len(result['validation_errors']) - 3} more")
        
        # Print MongoDB counts
        try:
            client, db = connect_db()
            granit_count = get_product_count("granit")
            blinkit_count = get_product_count("blinkit")
            print(f"\nMongoDB Status:")
            print(f"  GRANIT products in DB: {granit_count}")
            print(f"  Blinkit products in DB: {blinkit_count}")
        except ConnectionError as e:
            print(f"  Could not verify MongoDB counts: {e}")
        finally:
            close_db()
        
        # Generate Excel workbooks
        print(f"\nGenerating Excel workbooks...")
        try:
            from exporter import export_dataset
            export_result = export_dataset(result["valid_products"], name)
            
            if name == "granit" or name == "all":
                granit_path = export_result.get("granit")
                if granit_path:
                    print(f"  GRANIT workbook: {granit_path}")
            
            if name == "blinkit" or name == "all":
                blinkit_path = export_result.get("blinkit")
                if blinkit_path:
                    print(f"  Blinkit workbook: {blinkit_path}")
        except Exception as e:
            print(f"  Excel generation error: {e}")
        
        if args.scrape and not profile.EXTRACTION_CONFIG.get("enabled"):
            print("\nNote: Web scraping is disabled by default for this dataset.")
            print("To enable, set EXTRACTION_CONFIG.enabled=True in the profile with approved domains.")

    print(f"\n{'='*50}")
    if args.export_only:
        print("Phase 3 export complete.")
    else:
        print("Phase 3 processing complete.")
        print("Records saved to MongoDB and Excel workbooks generated.")
    print(f"{'='*50}")


if __name__ == "__main__":
    main()