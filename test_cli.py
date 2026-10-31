import os
import sys

# Set env vars BEFORE importing main
os.environ['MONGODB_URI'] = 'mongodb://localhost:27017/'
os.environ['MONGODB_DATABASE'] = 'granit_blinkit_data'

from main import main
import shutil

# Setup test data in MongoDB using mocked connection
from unittest.mock import patch, MagicMock

# Mock MongoDB
with patch('database.MongoClient') as mock_client:
    mock_instance = MagicMock()
    mock_client.return_value = mock_instance
    mock_instance.admin.command.return_value = {'ok': 1}
    
    # Test 1: --help
    print("=" * 60)
    print("CLI Test 1: python main.py --help")
    print("=" * 60)
    sys.argv = ['main.py', '--help']
    try:
        main()
    except SystemExit:
        pass

    # Test 2: --dataset granit
    print("\n" + "=" * 60)
    print("CLI Test 2: python main.py --dataset granit")
    print("=" * 60)
    sys.argv = ['main.py', '--dataset', 'granit']
    try:
        main()
    except SystemExit as e:
        print(f"Exit code: {e.code}")

    # Test 3: --dataset blinkit
    print("\n" + "=" * 60)
    print("CLI Test 3: python main.py --dataset blinkit")
    print("=" * 60)
    sys.argv = ['main.py', '--dataset', 'blinkit']
    try:
        main()
    except SystemExit as e:
        print(f"Exit code: {e.code}")

    # Test 4: --dataset all
    print("\n" + "=" * 60)
    print("CLI Test 4: python main.py --dataset all")
    print("=" * 60)
    sys.argv = ['main.py', '--dataset', 'all']
    try:
        main()
    except SystemExit as e:
        print(f"Exit code: {e.code}")

    # Test 5: --dataset all --export-only
    print("\n" + "=" * 60)
    print("CLI Test 5: python main.py --dataset all --export-only")
    print("=" * 60)
    sys.argv = ['main.py', '--dataset', 'all', '--export-only']
    try:
        main()
    except SystemExit as e:
        print(f"Exit code: {e.code}")

# Cleanup generated Excel files
if os.path.exists('output'):
    shutil.rmtree('output')
    print("\nCleaned up output directory")

print("\n" + "=" * 60)
print("CLI Testing Complete")
print("=" * 60)