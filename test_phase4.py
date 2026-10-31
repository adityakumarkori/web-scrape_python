import os
import shutil

os.environ['MONGODB_URI'] = 'mongodb://localhost:27017/'
os.environ['MONGODB_DATABASE'] = 'granit_blinkit_data'

from main import main
import sys
from decimal import Decimal
from datetime import datetime

# Setup test data in MongoDB first
from database import connect_db, close_db, get_collection, init_indexes, save_products, get_product_count

# Clear existing test data
client, db = connect_db()

collection_granit = db['granit_products']
collection_granit.delete_many({})
collection_blinkit = db['blinkit_products']
collection_blinkit.delete_many({})

# Insert test GRANIT product
test_granit = {
    'source_id': 'granit:ART-001',
    'product_name': 'Brake Pad Set',
    'description': 'Front brake pads for BMW 3 Series',
    'article_number': 'ART-001',
    'brand': 'TestBrand',
    'category': 'Brakes',
    'ean_gtin': '4000000000006',
    'product_url': 'https://granit-parts.com/product/12345',
    'image_url': 'https://granit-parts.com/images/12345.jpg',
    'regional_pricing': [{'country': 'Germany', 'country_code': 'Germany', 'currency': 'EUR', 'net_price': Decimal('29.99'), 'vat_rate': Decimal('19'), 'gross_price': Decimal('35.69'), 'price_source': 'json_ld', 'effective_date': '2024-01-15'}],
    'specifications': [{'specification_name': 'Width', 'specification_value': '150', 'unit': 'mm', 'compatibility': 'BMW 3 Series'}],
    'compliance': [{'regulation': 'ECE R90', 'compliance_standard': 'ECE', 'certification': 'E1', 'compliance_status': 'Compliant'}],
    'inventory': [{'warehouse': 'Central DE', 'country': 'Germany', 'available_quantity': '50', 'stock_status': 'In Stock'}],
    'source': 'granit',
    'collected_at': datetime.utcnow().isoformat() + 'Z',
    'dataset': 'granit'
}
collection_granit.insert_one(test_granit)
close_db()

# Insert test Blinkit product
test_blinkit = {
    'source_id': 'blinkit:SKU-001',
    'product_name': 'Organic Apples 1kg',
    'product_id': 'APL-001',
    'sku': 'SKU-001',
    'brand': 'FarmFresh',
    'category': 'Fruits',
    'subcategory': 'Apples',
    'product_description': 'Fresh organic apples from local farms',
    'barcode': '8901234567890',
    'product_url': 'https://blinkit.com/product/apples-1kg',
    'image_url': 'https://blinkit.com/apples.jpg',
    'pricing': [{'mrp': Decimal('150.00'), 'selling_price': Decimal('120.00'), 'discount_amount': Decimal('30.00'), 'discount_percentage': Decimal('20'), 'gst_rate': Decimal('5'), 'hsn_code': '08081000', 'price_source': 'json_ld', 'effective_date': '2024-01-15'}],
    'packaging': [{'net_quantity': Decimal('1'), 'unit': 'kg', 'package_type': 'Bag', 'ingredients': 'Organic apples', 'manufacturing_date': '2024-01-10', 'expiry_date': '2024-02-10', 'shelf_life': '30'}],
    'supplier': [{'supplier_name': 'Local Farms Co', 'supplier_location': 'Bangalore Rural', 'procurement_type': 'Direct', 'supplier_status': 'Active'}],
    'inventory': [{'dark_store_id': 'DS-001', 'dark_store_name': 'Koramangala', 'zone': 'South', 'pincode': '560034', 'available_quantity': '100', 'stock_status': 'In Stock', 'last_restocked': '2024-01-14'}],
    'delivery': [{'zone': 'South', 'pincode': '560034', 'delivery_sla': Decimal('30'), 'serviceability_status': 'Serviceable', 'effective_date': '2024-01-15'}],
    'source': 'blinkit',
    'collected_at': datetime.utcnow().isoformat() + 'Z',
    'dataset': 'blinkit'
}
collection_blinkit.insert_one(test_blinkit)
close_db()

# Run export-only
sys.argv = ['main.py', '--dataset', 'all', '--export-only']
try:
    main()
except SystemExit as e:
    print(f'Exit code: {e.code}')

# Check output files
print()
print('Checking output files:')
output_dir = 'output'
if os.path.exists(output_dir):
    for f in os.listdir(output_dir):
        print(f'  {f}')
else:
    print('  (output directory does not exist)')

# Cleanup test data
client = connect_db()
db = client[os.environ['MONGODB_DATABASE']]
collection_granit = db['granit_products']
collection_blinkit = db['blinkit_products']
collection_granit.delete_many({})
collection_blinkit.delete_many({})
close_db()

# Remove output directory
if os.path.exists('output'):
    shutil.rmtree('output')
print()
print('Test cleanup complete')