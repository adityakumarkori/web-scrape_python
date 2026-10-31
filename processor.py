import csv
import json
import os
import re
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, List, Optional, Set, Tuple

import profiles.granit as granit_profile
import profiles.blinkit as blinkit_profile


class ValidationError(Exception):
    def __init__(self, errors: List[str]):
        self.errors = errors
        super().__init__("; ".join(errors))


def load_csv(file_path: str) -> List[Dict[str, Any]]:
    products = []
    with open(file_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            products.append(dict(row))
    return products


def load_json(file_path: str) -> List[Dict[str, Any]]:
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, list):
        return data
    elif isinstance(data, dict):
        return [data]
    return []


def load_input_data(dataset: str, input_dir: Optional[str] = None) -> List[Dict[str, Any]]:
    if input_dir is None:
        input_dir = f"data/{dataset}"
    
    products = []
    
    csv_path = os.path.join(input_dir, "products.csv")
    json_path = os.path.join(input_dir, "products.json")
    
    if os.path.exists(csv_path):
        products.extend(load_csv(csv_path))
    
    if os.path.exists(json_path):
        products.extend(load_json(json_path))
    
    return products


def normalize_whitespace(text: Optional[str]) -> Optional[str]:
    if text is None:
        return None
    text = re.sub(r"\s+", " ", text.strip())
    return text if text else None


def convert_empty_to_none(value: Any) -> Any:
    if value == "" or value == "null" or value == "None":
        return None
    return value


def normalize_url(url: Optional[str], base_url: Optional[str] = None) -> Optional[str]:
    if not url:
        return None
    url = url.strip()
    if base_url and not url.startswith(("http://", "https://")):
        from urllib.parse import urljoin
        url = urljoin(base_url, url)
    return url


def parse_date(date_str: Optional[str]) -> Optional[str]:
    if not date_str:
        return None
    
    date_str = str(date_str).strip()
    if not date_str:
        return None
    
    formats = [
        "%Y-%m-%d",
        "%d/%m/%Y",
        "%d-%m-%Y",
        "%Y/%m/%d",
        "%d.%m.%Y",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%dT%H:%M:%S.%fZ",
    ]
    
    for fmt in formats:
        try:
            dt = datetime.strptime(date_str, fmt)
            return dt.date().isoformat()
        except ValueError:
            continue
    
    return None


def parse_decimal(value: Any) -> Optional[Decimal]:
    if value is None:
        return None
    try:
        if isinstance(value, str):
            value = value.replace(",", "").strip()
        return Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        return None


def validate_gtin(gtin: str) -> bool:
    gtin = re.sub(r"\D", "", gtin)
    if len(gtin) not in (8, 12, 13, 14):
        return False
    
    digits = [int(d) for d in gtin]
    check_digit = digits[-1]
    digits = digits[:-1]
    
    total = 0
    for i, digit in enumerate(reversed(digits)):
        weight = 3 if i % 2 == 0 else 1
        total += digit * weight
    
    calculated_check = (10 - (total % 10)) % 10
    return calculated_check == check_digit


def clean_product(product: Dict[str, Any], profile: Any) -> Dict[str, Any]:
    cleaned = {}
    
    for key, value in product.items():
        value = convert_empty_to_none(value)
        if isinstance(value, str):
            value = normalize_whitespace(value)
        cleaned[key] = value
    
    if profile.DATASET_NAME == "granit":
        if "product_url" in cleaned:
            cleaned["product_url"] = normalize_url(cleaned["product_url"])
        if "image_url" in cleaned:
            cleaned["image_url"] = normalize_url(cleaned["image_url"])
        
        if "regional_pricing" in cleaned and isinstance(cleaned["regional_pricing"], list):
            for pricing in cleaned["regional_pricing"]:
                if isinstance(pricing, dict):
                    pricing["net_price"] = parse_decimal(pricing.get("net_price"))
                    pricing["vat_rate"] = parse_decimal(pricing.get("vat_rate"))
                    pricing["gross_price"] = parse_decimal(pricing.get("gross_price"))
                    pricing["effective_date"] = parse_date(pricing.get("effective_date"))
        
        for field in ["specifications", "compliance", "inventory"]:
            if field in cleaned and isinstance(cleaned[field], list):
                pass
    
    elif profile.DATASET_NAME == "blinkit":
        if "product_url" in cleaned:
            cleaned["product_url"] = normalize_url(cleaned["product_url"])
        if "image_url" in cleaned:
            cleaned["image_url"] = normalize_url(cleaned["image_url"])
        
        if "pricing" in cleaned and isinstance(cleaned["pricing"], list):
            for pricing in cleaned["pricing"]:
                if isinstance(pricing, dict):
                    pricing["mrp"] = parse_decimal(pricing.get("mrp"))
                    pricing["selling_price"] = parse_decimal(pricing.get("selling_price"))
                    pricing["discount_amount"] = parse_decimal(pricing.get("discount_amount"))
                    pricing["discount_percentage"] = parse_decimal(pricing.get("discount_percentage"))
                    pricing["gst_rate"] = parse_decimal(pricing.get("gst_rate"))
                    pricing["effective_date"] = parse_date(pricing.get("effective_date"))
        
        for field in ["packaging", "supplier", "inventory", "delivery"]:
            if field in cleaned and isinstance(cleaned[field], list):
                for item in cleaned[field]:
                    if isinstance(item, dict):
                        if "manufacturing_date" in item:
                            item["manufacturing_date"] = parse_date(item["manufacturing_date"])
                        if "expiry_date" in item:
                            item["expiry_date"] = parse_date(item["expiry_date"])
                        if "last_restocked" in item:
                            item["last_restocked"] = parse_date(item["last_restocked"])
                        if "effective_date" in item:
                            item["effective_date"] = parse_date(item["effective_date"])
                        if "net_quantity" in item:
                            item["net_quantity"] = parse_decimal(item["net_quantity"])
                        if "available_quantity" in item:
                            item["available_quantity"] = parse_decimal(item["available_quantity"])
                        if "delivery_sla" in item:
                            item["delivery_sla"] = parse_decimal(item["delivery_sla"])
    
    return cleaned


def validate_granit_product(product: Dict[str, Any]) -> List[str]:
    errors = []
    
    required = granit_profile.REQUIRED_FIELDS
    for field in required:
        if not product.get(field):
            errors.append(f"Missing required field: {field}")
    
    if product.get("product_name"):
        name = str(product["product_name"]).strip()
        if len(name) < 2:
            errors.append("Product name too short")
    
    if product.get("product_url"):
        url = product["product_url"]
        if not url.startswith(("http://", "https://")):
            errors.append("Invalid product URL format")
    
    if product.get("ean_gtin"):
        if not validate_gtin(product["ean_gtin"]):
            errors.append("Invalid GTIN/EAN check digit")
    
    for pricing in product.get("regional_pricing", []):
        if not isinstance(pricing, dict):
            continue
        
        country_code = pricing.get("country_code")
        if country_code and country_code not in granit_profile.ISO_COUNTRY_CODES:
            errors.append(f"Invalid ISO country code: {country_code}")
        
        currency = pricing.get("currency")
        if currency and currency not in granit_profile.ISO_CURRENCY_CODES:
            errors.append(f"Invalid ISO currency code: {currency}")
        
        vat_rate = pricing.get("vat_rate")
        if vat_rate is not None:
            if not isinstance(vat_rate, Decimal):
                try:
                    vat_rate = Decimal(str(vat_rate))
                except:
                    errors.append("VAT rate must be a valid decimal")
            else:
                if vat_rate < 0 or vat_rate > 100:
                    errors.append("VAT rate must be between 0 and 100")
        
        net_price = pricing.get("net_price")
        gross_price = pricing.get("gross_price")
        if net_price is not None and gross_price is not None and vat_rate is not None:
            try:
                expected_gross = net_price * (1 + vat_rate / 100)
                if abs(gross_price - expected_gross) > Decimal("0.01"):
                    errors.append("Net/gross price inconsistency with VAT rate")
            except:
                pass
        
        if net_price is not None and net_price < 0:
            errors.append("Net price cannot be negative")
        if gross_price is not None and gross_price < 0:
            errors.append("Gross price cannot be negative")
    
    return errors


def validate_blinkit_product(product: Dict[str, Any]) -> List[str]:
    errors = []
    
    required = blinkit_profile.REQUIRED_FIELDS
    for field in required:
        if not product.get(field):
            errors.append(f"Missing required field: {field}")
    
    if product.get("product_name"):
        name = str(product["product_name"]).strip()
        if len(name) < 2:
            errors.append("Product name too short")
    
    if product.get("product_url"):
        url = product["product_url"]
        if not url.startswith(("http://", "https://")):
            errors.append("Invalid product URL format")
    
    if product.get("barcode"):
        if not validate_gtin(product["barcode"]):
            errors.append("Invalid barcode/GTIN check digit")
    
    for pricing in product.get("pricing", []):
        if not isinstance(pricing, dict):
            continue
        
        mrp = pricing.get("mrp")
        selling_price = pricing.get("selling_price")
        
        if mrp is not None and mrp < 0:
            errors.append("MRP cannot be negative")
        if selling_price is not None and selling_price < 0:
            errors.append("Selling price cannot be negative")
        
        if mrp is not None and selling_price is not None:
            if selling_price > mrp:
                errors.append("Selling price exceeds MRP")
        
        gst_rate = pricing.get("gst_rate")
        if gst_rate is not None:
            if not isinstance(gst_rate, Decimal):
                try:
                    gst_rate = Decimal(str(gst_rate))
                except:
                    errors.append("GST rate must be a valid decimal")
            else:
                if gst_rate not in blinkit_profile.GST_RATES:
                    errors.append(f"Invalid GST rate: {gst_rate}. Must be one of {blinkit_profile.GST_RATES}")
    
    for packaging in product.get("packaging", []):
        if not isinstance(packaging, dict):
            continue
        
        mfg_date = packaging.get("manufacturing_date")
        exp_date = packaging.get("expiry_date")
        
        if mfg_date and exp_date:
            try:
                mfg = datetime.strptime(mfg_date, "%Y-%m-%d").date()
                exp = datetime.strptime(exp_date, "%Y-%m-%d").date()
                if exp < mfg:
                    errors.append("Expiry date cannot precede manufacturing date")
            except:
                pass
    
    for inventory in product.get("inventory", []):
        if not isinstance(inventory, dict):
            continue
        
        pincode = inventory.get("pincode")
        if pincode and pincode not in blinkit_profile.BENGALURU_PINCODES:
            errors.append(f"Pincode {pincode} not in Bengaluru range")
        
        qty = inventory.get("available_quantity")
        if qty is not None and qty < 0:
            errors.append("Available quantity cannot be negative")
    
    return errors


def validate_product(product: Dict[str, Any], profile: Any) -> List[str]:
    if profile.DATASET_NAME == "granit":
        return validate_granit_product(product)
    elif profile.DATASET_NAME == "blinkit":
        return validate_blinkit_product(product)
    return []


def get_deduplication_key(product: Dict[str, Any], profile: Any) -> Optional[str]:
    if profile.DATASET_NAME == "granit":
        article = product.get("article_number")
        ean = product.get("ean_gtin")
        if article and ean:
            return f"granit:{article}:{ean}"
        elif article:
            return f"granit:{article}"
        elif ean:
            return f"granit:ean:{ean}"
    elif profile.DATASET_NAME == "blinkit":
        sku = product.get("sku")
        product_id = product.get("product_id")
        barcode = product.get("barcode")
        if sku and product_id:
            return f"blinkit:{sku}:{product_id}"
        elif sku:
            return f"blinkit:{sku}"
        elif product_id:
            return f"blinkit:id:{product_id}"
        elif barcode:
            return f"blinkit:barcode:{barcode}"
    return None


def deduplicate_products(products: List[Dict[str, Any]], profile: Any) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[str]]:
    seen: Dict[str, Dict[str, Any]] = {}
    duplicates = []
    duplicate_explanations = []
    no_key_products = []
    
    for product in products:
        key = get_deduplication_key(product, profile)
        if key and key in seen:
            duplicates.append(product)
            original = seen[key]
            duplicate_explanations.append(
                f"Duplicate detected: {key} - "
                f"original article/sku={original.get('article_number') or original.get('sku')}, "
                f"duplicate article/sku={product.get('article_number') or product.get('sku')}"
            )
        elif key:
            seen[key] = product
        else:
            no_key_products.append(product)
    
    unique_products = list(seen.values()) + no_key_products
    return unique_products, duplicates, duplicate_explanations


def process_products(products: List[Dict[str, Any]], profile: Any) -> Dict[str, Any]:
    input_count = len(products)
    
    cleaned_products = [clean_product(p, profile) for p in products]
    
    valid_products = []
    rejected_products = []
    validation_errors = []
    
    for product in cleaned_products:
        errors = validate_product(product, profile)
        if errors:
            rejected_products.append(product)
            validation_errors.append({
                "product": product,
                "errors": errors
            })
        else:
            valid_products.append(product)
    
    unique_products, duplicates, duplicate_explanations = deduplicate_products(valid_products, profile)
    
    for i, dup in enumerate(duplicates):
        rejected_products.append(dup)
        validation_errors.append({
            "product": dup,
            "errors": [duplicate_explanations[i]] if i < len(duplicate_explanations) else ["Duplicate record"]
        })
    
    return {
        "input_count": input_count,
        "valid_count": len(unique_products),
        "rejected_count": len(rejected_products),
        "duplicate_count": len(duplicates),
        "valid_products": unique_products,
        "rejected_products": rejected_products,
        "validation_errors": validation_errors,
    }


def print_summary(result: Dict[str, Any], profile: Any) -> None:
    print(f"\n{profile.DISPLAY_NAME}")
    print(f"Input records: {result['input_count']}")
    print(f"Valid: {result['valid_count']}")
    print(f"Rejected: {result['rejected_count']}")
    print(f"Duplicates: {result['duplicate_count']}")
    
    if result["validation_errors"]:
        print(f"\nValidation Errors (first 5):")
        for i, err in enumerate(result["validation_errors"][:5]):
            product = err["product"]
            identifier = product.get("article_number") or product.get("sku") or product.get("product_id") or "unknown"
            print(f"  {i+1}. {identifier}: {'; '.join(err['errors'])}")