import os
import sys
from decimal import Decimal
from datetime import datetime

# Set up environment
os.environ['MONGODB_URI'] = 'mongodb://localhost:27017/'
os.environ['MONGODB_DATABASE'] = 'granit_blinkit_data'

from main import main
import sys

# We need to test export functions directly since MongoDB is unavailable
# Let's import and test the exporter functions

from exporter import export_dataset, export_granit, export_blinkit
from profiles import get_profile, PROFILES
from database import connect_db, close_db, get_database, get_collection, init_indexes, save_products, get_product_count, check_connection
from unittest.mock import patch, MagicMock

# Mock MongoDB connection
with patch('database.MongoClient') as mock_client:
    mock_instance = MagicMock()
    mock_client.return_value = mock_instance
    mock_instance.admin.command.return_value = {'ok': 1}
    
    # Test GRANIT export
    print("=" * 60)
    print("Testing GRANIT Excel Export")
    print("=" * 60)
    
    granit_profile = get_profile("granit")
    
    # Create sample GRANIT products
    products_granit = [
        {
            'source_id': 'granit:ART-001',
            'product_name': 'Brake Pad Set',
            'article_number': 'ART-001',
            'description': 'Front brake pads for BMW 3 Series',
            'brand': 'TestBrand',
            'category': 'Brakes',
            'ean_gtin': '4000000000006',
            'product_url': 'https://granit-parts.com/product/12345',
            'image_url': 'https://granit-parts.com/images/12345.jpg',
            'regional_pricing': [
                {'country': 'Germany', 'country_code': 'Germany', 'currency': 'EUR', 'net_price': Decimal('29.99'), 'vat_rate': Decimal('19'), 'gross_price': Decimal('35.69'), 'price_source': 'json_ld', 'effective_date': '2024-01-15'}
            ],
            'specifications': [{'specification_name': 'Width', 'specification_value': '150', 'unit': 'mm', 'compatibility': 'BMW 3 Series'}],
            'compliance': [{'regulation': 'ECE R90', 'compliance_standard': 'ECE', 'certification': 'E1', 'compliance_status': 'Compliant'}],
            'inventory': [{'warehouse': 'Central DE', 'country': 'Germany', 'available_quantity': '50', 'stock_status': 'In Stock'}],
            'source': 'granit',
            'collected_at': datetime.utcnow().isoformat() + 'Z',
            'dataset': 'granit',
            '_verified': True,
            '_synthetic': False
        },
        {
            'source_id': 'granit:ART-002',
            'product_name': 'Oil Filter',
            'article_number': 'ART-002',
            'description': 'Oil filter for Audi A4',
            'brand': 'TestBrand',
            'category': 'Filters',
            'ean_gtin': '4000000000013',
            'product_url': 'https://granit-parts.com/product/12346',
            'image_url': 'https://granit-parts.com/images/12346.jpg',
            'regional_pricing': [
                {'country': 'France', 'country_code': 'France', 'currency': 'EUR', 'net_price': Decimal('15.50'), 'vat_rate': Decimal('20'), 'gross_price': Decimal('18.60'), 'price_source': 'json_ld', 'effective_date': '2024-02-01'}
            ],
            'source': 'granit',
            'collected_at': datetime.utcnow().isoformat() + 'Z',
            'dataset': 'granit',
            '_verified': True,
            '_synthetic': False
        }
    ]
    
    # Test export
    output_dir = 'output'
    os.makedirs(output_dir, exist_ok=True)
    
    result = export_dataset(products_granit, "granit", output_dir)
    print(f"Export result: {result}")
    
    # Check generated files
    if result["granit"]:
        print(f"GRANIT workbook saved to: {result['granit']}")
        import openpyxl
        wb = openpyxl.load_workbook(result["granit"])
        print(f"  Worksheets: {wb.sheetnames}")
        for ws_name in wb.sheetnames:
            ws = wb[ws_name]
            print(f"  - {ws_name}: {ws.max_row} rows x {ws.max_column} cols")
    else:
        print("  No GRANIT workbook generated")
    
    if result["blinkit"]:
        print(f"Blinkit workbook saved to: {result['blinkit']}")
        import openpyxl
        wb = openpyxl.load_workbook(result["blinkit"])
        print(f"  Worksheets: {wb.sheetnames}")
        for ws_name in wb.sheetnames:
            ws = wb[ws_name]
            print(f"  - {ws_name}: {ws.max_row} x {ws.max_column}")
    else:
        print("  No Blinkit workbook generated (expected when dataset=granit)")
    
    # Test Blinkit export
    print()
    print("=" * 60)
    print("Testing Blinkit Excel Export")
    print("=" * 60)
    
    blinkit_profile = get_profile("blinkit")
    
    products_blinkit = [
        {
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
            'dataset': 'blinkit',
            '_verified': True,
            '_synthetic': False
        },
        {
            'source_id': 'blinkit:SKU-002',
            'product_name': 'Bananas 1kg',
            'product_id': 'APL-002',
            'sku': 'SKU-002',
            'brand': 'FreshFoods',
            'category': 'Fruits',
            'subcategory': 'Bananas',
            'product_description': 'Fresh ripe bananas',
            'barcode': '8901234567891',
            'product_url': 'https://blinkit.com/product/bananas-1kg',
            'image_url': 'https://blinkit.com/bananas.jpg',
            'pricing': [{'mrp': Decimal('80.00'), 'selling_price': Decimal('65.00'), 'discount_amount': Decimal('15.00'), 'discount_percentage': Decimal('25'), 'gst_rate': Decimal('5'), 'hsn_code': '08031000', 'price_source': 'json_ld', 'effective_date': '2024-02-01'}],
            'packaging': [{'net_quantity': Decimal('1'), 'unit': 'kg', 'package_type': 'Bag', 'ingredients': 'Ripe bananas', 'manufacturing_date': '2024-01-15', 'expiry_date': '2024-03-15', 'shelf_life': '20'}],
            'source': 'blinkit',
            'collected_at': datetime.utcnow().isoformat() + 'Z',
            'dataset': 'blinkit',
            '_verified': True,
            '_synthetic': False
        }
    ]
    
    result = export_dataset(products_blinkit, "blinkit", output_dir)
    print(f"Export result: {result}")
    
    # Check generated files
    if result["blinkit"]:
        print(f"Blinkit workbook saved to: {result['blinkit']}")
        import openpyxl
        wb = openpyxl.load_workbook(result["blinkit"])
        print(f"  Worksheets: {wb.sheetnames}")
        for ws_name in wb.sheetnames:
            ws = wb[ws_name]
            print(f"  - {ws_name}: {ws.max_row} rows x {ws.max_column} cols")
    else:
        print("  No Blinkit workbook generated")
    
    # Test "all" dataset export
    print()
    print("=" * 60)
    print("Testing 'all' dataset Excel Export")
    print("=" * 60)
    
    result = export_dataset(products_granit + products_blinkit, "all", output_dir)
    print(f"Export result: {result}")
    
    if result["granit"]:
        print(f"GRANIT workbook saved to: {result['granit']}")
        import openpyxl
        wb = openpyxl.load_workbook(result["granit"])
        print(f"  Worksheets: {wb.sheetnames}")
        expected_granit_sheets = ["README", "Products", "Regional Pricing", "Specifications", "Compliance", "Inventory & Logistics", "Data Quality", "Data Dictionary", "Sources & Assumptions"]
        for expected in expected_granit_sheets:
            found = expected in wb.sheetnames
            print(f"  {expected}: {'FOUND' if found else 'MISSING'}")
    
    if result["blinkit"]:
        print(f"Blinkit workbook saved to: {result['blinkit']}")
        import openpyxl
        wb = openpyxl.load_workbook(result["blinkit"])
        print(f"  Worksheets: {wb.sheetnames}")
        expected_blinkit_sheets = ["README", "Products", "Pricing & Tax", "Packaging & Ingredients", "Suppliers", "Dark Stores & Inventory", "Delivery & Zones", "Data Quality", "Data Dictionary", "Sources & Assumptions"]
        for expected in expected_blinkit_sheets:
            found = expected in wb.sheetnames
            print(f"  {expected}: {'FOUND' if found else 'MISSING'}")

print()
print("Excel export validation complete")