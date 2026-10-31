import pytest
from decimal import Decimal
from datetime import datetime

import processor
import profiles.granit as granit_profile
import profiles.blinkit as blinkit_profile


SAMPLE_GRANIT_PRODUCT = {
    "article_number": "ART-12345",
    "product_name": "Brake Pad Set",
    "description": "Front brake pads for BMW 3 Series",
    "manufacturer": "TestMfg",
    "brand": "TestBrand",
    "category": "Brakes",
    "subcategory": "Brake Pads",
    "product_type": "Wear Part",
    "ean_gtin": "4000000000006",
    "product_url": "https://granit-parts.com/product/12345",
    "image_url": "https://granit-parts.com/images/12345.jpg",
    "regional_pricing": [
        {
            "country": "Germany",
            "country_code": "Germany",
            "currency": "EUR",
            "net_price": "29.99",
            "vat_rate": "19",
            "gross_price": "35.69",
            "price_source": "json_ld",
            "effective_date": "2024-01-15"
        }
    ],
    "specifications": [
        {"specification_name": "Width", "specification_value": "150", "unit": "mm", "compatibility": "BMW 3 Series"}
    ],
    "compliance": [
        {"regulation": "ECE R90", "compliance_standard": "ECE", "certification": "E1", "compliance_status": "Compliant"}
    ],
    "inventory": [
        {"warehouse": "Central DE", "country": "Germany", "available_quantity": "50", "stock_status": "In Stock"}
    ],
}

SAMPLE_BLINKIT_PRODUCT = {
    "product_id": "APL-001",
    "sku": "APL-001",
    "product_name": "Organic Apples 1kg",
    "brand": "FarmFresh",
    "category": "Fruits",
    "subcategory": "Apples",
    "product_description": "Fresh organic apples from local farms",
    "barcode": "8901234567890",
    "product_url": "https://blinkit.com/product/apples-1kg",
    "image_url": "https://blinkit.com/apples.jpg",
    "pricing": [
        {
            "mrp": "150.00",
            "selling_price": "120.00",
            "discount_amount": "30.00",
            "discount_percentage": "20",
            "gst_rate": "5",
            "hsn_code": "08081000",
            "price_source": "json_ld",
            "effective_date": "2024-01-15"
        }
    ],
    "packaging": [
        {
            "net_quantity": "1",
            "unit": "kg",
            "package_type": "Bag",
            "ingredients": "Organic apples",
            "manufacturing_date": "2024-01-10",
            "expiry_date": "2024-02-10",
            "shelf_life": "30"
        }
    ],
    "supplier": [
        {
            "supplier_name": "Local Farms Co",
            "supplier_location": "Bangalore Rural",
            "procurement_type": "Direct",
            "supplier_status": "Active"
        }
    ],
    "inventory": [
        {
            "dark_store_id": "DS-001",
            "dark_store_name": "Koramangala",
            "zone": "South",
            "pincode": "560034",
            "available_quantity": "100",
            "stock_status": "In Stock",
            "last_restocked": "2024-01-14"
        }
    ],
    "delivery": [
        {
            "zone": "South",
            "pincode": "560034",
            "delivery_sla": "30",
            "serviceability_status": "Serviceable",
            "effective_date": "2024-01-15"
        }
    ],
}


class TestNormalizeWhitespace:
    def test_normalize_whitespace_basic(self):
        assert processor.normalize_whitespace("  hello   world  ") == "hello world"
    
    def test_normalize_whitespace_newlines(self):
        assert processor.normalize_whitespace("hello\n\nworld") == "hello world"
    
    def test_normalize_whitespace_tabs(self):
        assert processor.normalize_whitespace("hello\t\tworld") == "hello world"
    
    def test_normalize_whitespace_none(self):
        assert processor.normalize_whitespace(None) is None
    
    def test_normalize_whitespace_empty(self):
        assert processor.normalize_whitespace("") is None
        assert processor.normalize_whitespace("   ") is None


class TestConvertEmptyToNone:
    def test_empty_string(self):
        assert processor.convert_empty_to_none("") is None
    
    def test_null_string(self):
        assert processor.convert_empty_to_none("null") is None
        assert processor.convert_empty_to_none("None") is None
    
    def test_non_empty(self):
        assert processor.convert_empty_to_none("value") == "value"
        assert processor.convert_empty_to_none(123) == 123
        assert processor.convert_empty_to_none(0) == 0


class TestNormalizeURL:
    def test_absolute_url(self):
        assert processor.normalize_url("https://example.com/product") == "https://example.com/product"
    
    def test_relative_url(self):
        assert processor.normalize_url("/product/123", "https://example.com") == "https://example.com/product/123"
    
    def test_relative_url_no_base(self):
        assert processor.normalize_url("/product/123") == "/product/123"
    
    def test_none_url(self):
        assert processor.normalize_url(None) is None
    
    def test_empty_url(self):
        assert processor.normalize_url("") is None


class TestParseDate:
    def test_iso_format(self):
        assert processor.parse_date("2024-01-15") == "2024-01-15"
    
    def test_dd_mm_yyyy(self):
        assert processor.parse_date("15/01/2024") == "2024-01-15"
    
    def test_dd_mm_yyyy_dash(self):
        assert processor.parse_date("15-01-2024") == "2024-01-15"
    
    def test_yyyy_mm_dd_slash(self):
        assert processor.parse_date("2024/01/15") == "2024-01-15"
    
    def test_dd_mm_yyyy_dot(self):
        assert processor.parse_date("15.01.2024") == "2024-01-15"
    
    def test_iso_datetime(self):
        assert processor.parse_date("2024-01-15T10:30:00") == "2024-01-15"
    
    def test_iso_datetime_z(self):
        assert processor.parse_date("2024-01-15T10:30:00Z") == "2024-01-15"
    
    def test_iso_datetime_microseconds(self):
        assert processor.parse_date("2024-01-15T10:30:00.123456Z") == "2024-01-15"
    
    def test_none_date(self):
        assert processor.parse_date(None) is None
    
    def test_empty_date(self):
        assert processor.parse_date("") is None
    
    def test_invalid_date(self):
        assert processor.parse_date("invalid") is None


class TestParseDecimal:
    def test_integer_string(self):
        assert processor.parse_decimal("100") == Decimal("100")
    
    def test_float_string(self):
        assert processor.parse_decimal("29.99") == Decimal("29.99")
    
    def test_with_comma(self):
        assert processor.parse_decimal("1,234.56") == Decimal("1234.56")
    
    def test_decimal_object(self):
        assert processor.parse_decimal(Decimal("29.99")) == Decimal("29.99")
    
    def test_int_object(self):
        assert processor.parse_decimal(100) == Decimal("100")
    
    def test_none(self):
        assert processor.parse_decimal(None) is None
    
    def test_invalid(self):
        assert processor.parse_decimal("invalid") is None


class TestValidateGTIN:
    def test_valid_gtin13(self):
        assert processor.validate_gtin("4000000000006") is True
    
    def test_valid_gtin14(self):
        assert processor.validate_gtin("04000000000006") is True
    
    def test_valid_upc(self):
        assert processor.validate_gtin("012345678905") is True
    
    def test_valid_ean8(self):
        assert processor.validate_gtin("12345670") is True
    
    def test_invalid_check_digit(self):
        assert processor.validate_gtin("4000000000002") is False
    
    def test_invalid_length(self):
        assert processor.validate_gtin("123") is False
        assert processor.validate_gtin("123456789012345") is False
    
    def test_with_non_digits(self):
        assert processor.validate_gtin("400-000-000-0006") is True
        assert processor.validate_gtin("400 000 000 0006") is True


class TestCleanGranitProduct:
    def test_clean_granit_product(self):
        cleaned = processor.clean_product(SAMPLE_GRANIT_PRODUCT.copy(), granit_profile)
        
        assert cleaned["article_number"] == "ART-12345"
        assert cleaned["product_name"] == "Brake Pad Set"
        assert isinstance(cleaned["regional_pricing"][0]["net_price"], Decimal)
        assert cleaned["regional_pricing"][0]["net_price"] == Decimal("29.99")
        assert cleaned["regional_pricing"][0]["vat_rate"] == Decimal("19")
        assert cleaned["regional_pricing"][0]["gross_price"] == Decimal("35.69")
        assert cleaned["regional_pricing"][0]["effective_date"] == "2024-01-15"
        assert cleaned["product_url"] == "https://granit-parts.com/product/12345"
    
    def test_clean_granit_empty_strings(self):
        product = {"article_number": "", "product_name": "Test", "regional_pricing": [{"net_price": ""}]}
        cleaned = processor.clean_product(product, granit_profile)
        
        assert cleaned["article_number"] is None
        assert cleaned["regional_pricing"][0]["net_price"] is None


class TestCleanBlinkitProduct:
    def test_clean_blinkit_product(self):
        cleaned = processor.clean_product(SAMPLE_BLINKIT_PRODUCT.copy(), blinkit_profile)
        
        assert cleaned["sku"] == "APL-001"
        assert cleaned["product_name"] == "Organic Apples 1kg"
        assert isinstance(cleaned["pricing"][0]["mrp"], Decimal)
        assert cleaned["pricing"][0]["mrp"] == Decimal("150.00")
        assert cleaned["pricing"][0]["selling_price"] == Decimal("120.00")
        assert cleaned["pricing"][0]["gst_rate"] == Decimal("5")
        assert cleaned["pricing"][0]["effective_date"] == "2024-01-15"
        assert isinstance(cleaned["packaging"][0]["net_quantity"], Decimal)
        assert cleaned["packaging"][0]["manufacturing_date"] == "2024-01-10"
        assert cleaned["packaging"][0]["expiry_date"] == "2024-02-10"
        assert isinstance(cleaned["inventory"][0]["available_quantity"], Decimal)
        assert cleaned["inventory"][0]["last_restocked"] == "2024-01-14"
        assert isinstance(cleaned["delivery"][0]["delivery_sla"], Decimal)
        assert cleaned["delivery"][0]["effective_date"] == "2024-01-15"
    
    def test_clean_blinkit_empty_strings(self):
        product = {"sku": "", "product_name": "Test", "pricing": [{"mrp": ""}]}
        cleaned = processor.clean_product(product, blinkit_profile)
        
        assert cleaned["sku"] is None
        assert cleaned["pricing"][0]["mrp"] is None


class TestValidateGranitProduct:
    def test_valid_granit_product(self):
        cleaned = processor.clean_product(SAMPLE_GRANIT_PRODUCT.copy(), granit_profile)
        errors = processor.validate_granit_product(cleaned)
        assert errors == []
    
    def test_missing_required_fields(self):
        product = {"article_number": "", "product_name": ""}
        cleaned = processor.clean_product(product, granit_profile)
        errors = processor.validate_granit_product(cleaned)
        
        assert "Missing required field: article_number" in errors
        assert "Missing required field: product_name" in errors
    
    def test_product_name_too_short(self):
        product = {"article_number": "ART-001", "product_name": "A"}
        cleaned = processor.clean_product(product, granit_profile)
        errors = processor.validate_granit_product(cleaned)
        
        assert "Product name too short" in errors
    
    def test_invalid_product_url(self):
        product = {"article_number": "ART-001", "product_name": "Test", "product_url": "not-a-url"}
        cleaned = processor.clean_product(product, granit_profile)
        errors = processor.validate_granit_product(cleaned)
        
        assert "Invalid product URL format" in errors
    
    def test_invalid_gtin(self):
        product = {"article_number": "ART-001", "product_name": "Test", "ean_gtin": "123"}
        cleaned = processor.clean_product(product, granit_profile)
        errors = processor.validate_granit_product(cleaned)
        
        assert "Invalid GTIN/EAN check digit" in errors
    
    def test_invalid_country_code(self):
        product = {
            "article_number": "ART-001",
            "product_name": "Test",
            "regional_pricing": [{"country_code": "XX", "currency": "EUR", "net_price": "10"}]
        }
        cleaned = processor.clean_product(product, granit_profile)
        errors = processor.validate_granit_product(cleaned)
        
        assert "Invalid ISO country code: XX" in errors
    
    def test_invalid_currency_code(self):
        product = {
            "article_number": "ART-001",
            "product_name": "Test",
            "regional_pricing": [{"country_code": "DE", "currency": "XXX", "net_price": "10"}]
        }
        cleaned = processor.clean_product(product, granit_profile)
        errors = processor.validate_granit_product(cleaned)
        
        assert "Invalid ISO currency code: XXX" in errors
    
    def test_vat_rate_out_of_range(self):
        product = {
            "article_number": "ART-001",
            "product_name": "Test",
            "regional_pricing": [{"country_code": "DE", "currency": "EUR", "net_price": "10", "vat_rate": Decimal("150")}]
        }
        cleaned = processor.clean_product(product, granit_profile)
        errors = processor.validate_granit_product(cleaned)
        
        assert "VAT rate must be between 0 and 100" in errors
    
    def test_net_price_negative(self):
        product = {
            "article_number": "ART-001",
            "product_name": "Test",
            "regional_pricing": [{"country_code": "DE", "currency": "EUR", "net_price": "-10"}]
        }
        cleaned = processor.clean_product(product, granit_profile)
        errors = processor.validate_granit_product(cleaned)
        
        assert "Net price cannot be negative" in errors
    
    def test_net_gross_inconsistency(self):
        product = {
            "article_number": "ART-001",
            "product_name": "Test",
            "regional_pricing": [{"country_code": "DE", "currency": "EUR", "net_price": "100", "vat_rate": "19", "gross_price": "150"}]
        }
        cleaned = processor.clean_product(product, granit_profile)
        errors = processor.validate_granit_product(cleaned)
        
        assert "Net/gross price inconsistency with VAT rate" in errors


class TestValidateBlinkitProduct:
    def test_valid_blinkit_product(self):
        cleaned = processor.clean_product(SAMPLE_BLINKIT_PRODUCT.copy(), blinkit_profile)
        errors = processor.validate_blinkit_product(cleaned)
        assert errors == []
    
    def test_missing_required_fields(self):
        product = {"sku": "", "product_name": ""}
        cleaned = processor.clean_product(product, blinkit_profile)
        errors = processor.validate_blinkit_product(cleaned)
        
        assert "Missing required field: sku" in errors
        assert "Missing required field: product_name" in errors
    
    def test_product_name_too_short(self):
        product = {"sku": "SKU-001", "product_name": "A"}
        cleaned = processor.clean_product(product, blinkit_profile)
        errors = processor.validate_blinkit_product(cleaned)
        
        assert "Product name too short" in errors
    
    def test_invalid_barcode(self):
        product = {"sku": "SKU-001", "product_name": "Test", "barcode": "123"}
        cleaned = processor.clean_product(product, blinkit_profile)
        errors = processor.validate_blinkit_product(cleaned)
        
        assert "Invalid barcode/GTIN check digit" in errors
    
    def test_selling_price_exceeds_mrp(self):
        product = {
            "sku": "SKU-001",
            "product_name": "Test",
            "pricing": [{"mrp": "100", "selling_price": "150"}]
        }
        cleaned = processor.clean_product(product, blinkit_profile)
        errors = processor.validate_blinkit_product(cleaned)
        
        assert "Selling price exceeds MRP" in errors
    
    def test_negative_mrp(self):
        product = {"sku": "SKU-001", "product_name": "Test", "pricing": [{"mrp": "-10"}]}
        cleaned = processor.clean_product(product, blinkit_profile)
        errors = processor.validate_blinkit_product(cleaned)
        
        assert "MRP cannot be negative" in errors
    
    def test_invalid_gst_rate(self):
        product = {"sku": "SKU-001", "product_name": "Test", "pricing": [{"gst_rate": "10"}]}
        cleaned = processor.clean_product(product, blinkit_profile)
        errors = processor.validate_blinkit_product(cleaned)
        
        assert "Invalid GST rate: 10" in str(errors)
        assert "Must be one of" in str(errors)
    
    def test_expiry_before_manufacturing(self):
        product = {
            "sku": "SKU-001",
            "product_name": "Test",
            "packaging": [{"manufacturing_date": "2024-02-01", "expiry_date": "2024-01-01"}]
        }
        cleaned = processor.clean_product(product, blinkit_profile)
        errors = processor.validate_blinkit_product(cleaned)
        
        assert "Expiry date cannot precede manufacturing date" in errors
    
    def test_invalid_pincode(self):
        product = {
            "sku": "SKU-001",
            "product_name": "Test",
            "inventory": [{"pincode": "110001", "available_quantity": "10"}]
        }
        cleaned = processor.clean_product(product, blinkit_profile)
        errors = processor.validate_blinkit_product(cleaned)
        
        assert "Pincode 110001 not in Bengaluru range" in errors
    
    def test_negative_quantity(self):
        product = {"sku": "SKU-001", "product_name": "Test", "inventory": [{"pincode": "560034", "available_quantity": "-5"}]}
        cleaned = processor.clean_product(product, blinkit_profile)
        errors = processor.validate_blinkit_product(cleaned)
        
        assert "Available quantity cannot be negative" in errors


class TestValidateProduct:
    def test_granit_dispatch(self):
        product = {"article_number": "ART-001", "product_name": "Test"}
        cleaned = processor.clean_product(product, granit_profile)
        errors = processor.validate_product(cleaned, granit_profile)
        assert "Missing required field: article_number" not in errors
    
    def test_blinkit_dispatch(self):
        product = {"sku": "SKU-001", "product_name": "Test"}
        cleaned = processor.clean_product(product, blinkit_profile)
        errors = processor.validate_product(cleaned, blinkit_profile)
        assert "Missing required field: sku" not in errors


class TestGetDeduplicationKey:
    def test_granit_with_article_and_ean(self):
        product = {"article_number": "ART-001", "ean_gtin": "4000000000001"}
        key = processor.get_deduplication_key(product, granit_profile)
        assert key == "granit:ART-001:4000000000001"
    
    def test_granit_with_article_only(self):
        product = {"article_number": "ART-001"}
        key = processor.get_deduplication_key(product, granit_profile)
        assert key == "granit:ART-001"
    
    def test_granit_with_ean_only(self):
        product = {"ean_gtin": "4000000000001"}
        key = processor.get_deduplication_key(product, granit_profile)
        assert key == "granit:ean:4000000000001"
    
    def test_blinkit_with_sku_and_product_id(self):
        product = {"sku": "SKU-001", "product_id": "PROD-001"}
        key = processor.get_deduplication_key(product, blinkit_profile)
        assert key == "blinkit:SKU-001:PROD-001"
    
    def test_blinkit_with_sku_only(self):
        product = {"sku": "SKU-001"}
        key = processor.get_deduplication_key(product, blinkit_profile)
        assert key == "blinkit:SKU-001"
    
    def test_blinkit_with_product_id_only(self):
        product = {"product_id": "PROD-001"}
        key = processor.get_deduplication_key(product, blinkit_profile)
        assert key == "blinkit:id:PROD-001"
    
    def test_blinkit_with_barcode_only(self):
        product = {"barcode": "8901234567890"}
        key = processor.get_deduplication_key(product, blinkit_profile)
        assert key == "blinkit:barcode:8901234567890"
    
    def test_no_identifiers(self):
        product = {"product_name": "Test"}
        key = processor.get_deduplication_key(product, granit_profile)
        assert key is None


class TestDeduplicateProducts:
    def test_deduplicate_granit(self):
        product1 = {"article_number": "ART-001", "product_name": "Product 1"}
        product2 = {"article_number": "ART-001", "product_name": "Product 1 Duplicate"}
        product3 = {"article_number": "ART-002", "product_name": "Product 2"}
        
        products = [product1, product2, product3]
        unique, duplicates, explanations = processor.deduplicate_products(products, granit_profile)
        
        assert len(unique) == 2
        assert len(duplicates) == 1
        assert duplicates[0]["article_number"] == "ART-001"
        assert len(explanations) == 1
    
    def test_deduplicate_blinkit(self):
        product1 = {"sku": "SKU-001", "product_name": "Product 1"}
        product2 = {"sku": "SKU-001", "product_name": "Product 1 Duplicate"}
        
        products = [product1, product2]
        unique, duplicates, explanations = processor.deduplicate_products(products, blinkit_profile)
        
        assert len(unique) == 1
        assert len(duplicates) == 1
    
    def test_no_duplicates(self):
        product1 = {"article_number": "ART-001", "product_name": "Product 1"}
        product2 = {"article_number": "ART-002", "product_name": "Product 2"}
        
        products = [product1, product2]
        unique, duplicates, explanations = processor.deduplicate_products(products, granit_profile)
        
        assert len(unique) == 2
        assert len(duplicates) == 0
        assert len(explanations) == 0
    
    def test_no_identifiers_no_dedup(self):
        product1 = {"product_name": "Product 1"}
        product2 = {"product_name": "Product 2"}
        
        products = [product1, product2]
        unique, duplicates, explanations = processor.deduplicate_products(products, granit_profile)
        
        assert len(unique) == 2
        assert len(duplicates) == 0


class TestProcessProducts:
    def test_process_products_granit_valid(self):
        products = [SAMPLE_GRANIT_PRODUCT.copy()]
        result = processor.process_products(products, granit_profile)
        
        assert result["input_count"] == 1
        assert result["valid_count"] == 1
        assert result["rejected_count"] == 0
        assert result["duplicate_count"] == 0
        assert len(result["valid_products"]) == 1
    
    def test_process_products_granit_invalid(self):
        products = [{"article_number": "", "product_name": ""}]
        result = processor.process_products(products, granit_profile)
        
        assert result["input_count"] == 1
        assert result["valid_count"] == 0
        assert result["rejected_count"] == 1
        assert len(result["validation_errors"]) == 1
    
    def test_process_products_blinkit_valid(self):
        products = [SAMPLE_BLINKIT_PRODUCT.copy()]
        result = processor.process_products(products, blinkit_profile)
        
        assert result["input_count"] == 1
        assert result["valid_count"] == 1
        assert result["rejected_count"] == 0
        assert len(result["valid_products"]) == 1
    
    def test_process_products_deduplication(self):
        products = [
            SAMPLE_GRANIT_PRODUCT.copy(),
            {**SAMPLE_GRANIT_PRODUCT, "product_name": "Duplicate Name"}
        ]
        result = processor.process_products(products, granit_profile)
        
        assert result["input_count"] == 2
        assert result["valid_count"] == 1
        assert result["duplicate_count"] == 1
        assert result["rejected_count"] == 1
    
    def test_process_products_mixed_valid_invalid(self):
        products = [
            SAMPLE_GRANIT_PRODUCT.copy(),
            {"article_number": "", "product_name": ""}
        ]
        result = processor.process_products(products, granit_profile)
        
        assert result["input_count"] == 2
        assert result["valid_count"] == 1
        assert result["rejected_count"] == 1
        assert len(result["validation_errors"]) == 1


class TestLoadInputData:
    def test_load_csv(self, tmp_path):
        csv_file = tmp_path / "products.csv"
        csv_file.write_text("article_number,product_name\nART-001,Product 1\nART-002,Product 2")
        
        products = processor.load_csv(str(csv_file))
        
        assert len(products) == 2
        assert products[0]["article_number"] == "ART-001"
        assert products[1]["product_name"] == "Product 2"
    
    def test_load_json_array(self, tmp_path):
        json_file = tmp_path / "products.json"
        json_file.write_text('[{"article_number": "ART-001"}, {"article_number": "ART-002"}]')
        
        products = processor.load_json(str(json_file))
        
        assert len(products) == 2
    
    def test_load_json_object(self, tmp_path):
        json_file = tmp_path / "products.json"
        json_file.write_text('{"article_number": "ART-001"}')
        
        products = processor.load_json(str(json_file))
        
        assert len(products) == 1
        assert products[0]["article_number"] == "ART-001"
    
    def test_load_input_data_csv(self, tmp_path):
        csv_file = tmp_path / "products.csv"
        csv_file.write_text("article_number,product_name\nART-001,Product 1")
        
        products = processor.load_input_data("granit", str(tmp_path))
        
        assert len(products) == 1
    
    def test_load_input_data_json(self, tmp_path):
        json_file = tmp_path / "products.json"
        json_file.write_text('[{"article_number": "ART-001"}]')
        
        products = processor.load_input_data("granit", str(tmp_path))
        
        assert len(products) == 1
    
    def test_load_input_data_both(self, tmp_path):
        csv_file = tmp_path / "products.csv"
        csv_file.write_text("article_number,product_name\nART-001,Product 1")
        json_file = tmp_path / "products.json"
        json_file.write_text('[{"article_number": "ART-002"}]')
        
        products = processor.load_input_data("granit", str(tmp_path))
        
        assert len(products) == 2


class TestPrintSummary:
    def test_print_summary(self, capsys):
        result = {
            "input_count": 10,
            "valid_count": 8,
            "rejected_count": 2,
            "duplicate_count": 1,
            "validation_errors": [
                {"product": {"article_number": "ART-001"}, "errors": ["Missing field"]},
                {"product": {"article_number": "ART-002"}, "errors": ["Invalid GTIN"]},
            ]
        }
        
        processor.print_summary(result, granit_profile)
        captured = capsys.readouterr()
        
        assert "GRANIT Parts - EU Region" in captured.out
        assert "Input records: 10" in captured.out
        assert "Valid: 8" in captured.out
        assert "Rejected: 2" in captured.out
        assert "Duplicates: 1" in captured.out
        assert "Validation Errors" in captured.out
        assert "ART-001" in captured.out