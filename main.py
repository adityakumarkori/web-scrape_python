import argparse
import sys
from profiles import get_profile, PROFILES
from database import check_connection


def main():
    parser = argparse.ArgumentParser(
        description="GRANIT + Blinkit Data Project - Phase 1 Foundation"
    )
    parser.add_argument(
        "--dataset",
        choices=["granit", "blinkit", "all"],
        required=True,
        help="Dataset to process: granit, blinkit, or all"
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

        print(f"Dataset: {profile.DISPLAY_NAME}")
        print(f"Collection: {profile.COLLECTION_NAME}")

        connected, msg = check_connection()
        if connected:
            print(f"MongoDB: Connected")
        else:
            print(f"MongoDB: {msg}")

        print()

    print("Scraping and processing will be added in subsequent phases.")


if __name__ == "__main__":
    main()