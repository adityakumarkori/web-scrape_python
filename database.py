from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from bson import Decimal128
import config
import logging

logger = logging.getLogger(__name__)

_client = None
_database = None

# Track which datasets have been initialized
_initialized_datasets = set()


def connect_db():
    """Connect to MongoDB using the existing MONGODB_URI configuration.
    
    Returns the MongoDB client instance (backward compatible).
    Use get_database() to access the database.
    """
    global _client, _database
    
    # Check if already connected
    if _client is not None and _database is not None:
        return _client
    
    uri = config.MONGODB_URI
    if not uri:
        raise ConnectionError("MONGODB_URI not configured. Set MONGODB_URI environment variable.")
    
    timeout_ms = config.REQUEST_TIMEOUT * 1000
    
    try:
        _client = MongoClient(uri, serverSelectionTimeoutMS=timeout_ms, connectTimeoutMS=timeout_ms)
        _client.admin.command("ping")
        _database = _client[config.MONGODB_DATABASE]
        _initialized_datasets = set()
        return _client
    except (ConnectionFailure, ServerSelectionTimeoutError) as e:
        _client = None
        _database = None
        logger.error(f"Failed to connect to MongoDB: {e}")
        raise ConnectionError(f"Failed to connect to MongoDB: {e}")


def close_db():
    """Close the MongoDB connection."""
    global _client, _database
    if _client is not None:
        try:
            _client.close()
        except Exception:
            pass
    _client = None
    _database = None


def get_database():
    """Get the MongoDB database instance."""
    if _database is None:
        connect_db()
    return _database


def get_collection(dataset: str):
    """Get the appropriate collection for a dataset."""
    if dataset not in ("granit", "blinkit"):
        raise ValueError(f"Unknown dataset: {dataset}. Must be 'granit' or 'blinkit'")
    
    db = get_database()
    collection_name = f"{dataset}_products"
    return db[collection_name]


def init_indexes(dataset: str):
    """Initialize indexes for a dataset collection."""
    if dataset in _initialized_datasets:
        return
    
    collection = get_collection(dataset)
    
    if dataset == "granit":
        # Granit: primary identity is source_id + article_number
        # Also index on EAN/GTIN for additional matching
        collection.create_index([("source_id", 1), ("article_number", 1)], unique=True)
        collection.create_index([("ean_gtin", 1)], unique=False)
        collection.create_index([("product_name", "text")])
    elif dataset == "blinkit":
        # Blinkit: primary identity is source_id + SKU
        collection.create_index([("source_id", 1), ("sku", 1)], unique=True)
        collection.create_index([("barcode", 1)], unique=False)
        collection.create_index([("product_name", "text")])
    
    _initialized_datasets.add(dataset)


def save_products(products: list, dataset: str) -> dict:
    """
    Save validated products to MongoDB.
    
    Returns dict with counts:
    - inserted: number of new records inserted
    - updated: number of existing records updated
    - skipped: number of records skipped (duplicates with same data)
    - failed: number of records that failed to save
    - total: total products processed
    """
    if not products:
        return {
            "inserted": 0,
            "updated": 0,
            "skipped": 0,
            "failed": 0,
            "total": 0
        }
    
    collection = get_collection(dataset)
    init_indexes(dataset)
    
    results = {
        "inserted": 0,
        "updated": 0,
        "skipped": 0,
        "failed": 0,
        "total": len(products)
    }
    
    for product in products:
        try:
            # Ensure provenance fields are preserved
            if "source" not in product:
                product["source"] = dataset
            
            if "collected_at" not in product:
                from datetime import datetime
                product["collected_at"] = datetime.utcnow().isoformat() + "Z"
            
            if "dataset" not in product:
                product["dataset"] = dataset
            
            # Generate source_id based on dataset type
            source_id = _generate_source_id(product, dataset)
            product["source_id"] = source_id
            
            # Check for existing record
            existing = collection.find_one({"source_id": source_id})
            
            if existing:
                # Record exists - check if data is different
                existing_regional = existing.get("regional_pricing", [])
                new_regional = product.get("regional_pricing", [])
                
                # If regional pricing is different, update; otherwise skip
                if _regional_pricing_changed(existing_regional, new_regional):
                    # Update the record
                    product.pop("_id", None)
                    collection.replace_one({"source_id": source_id}, product, upsert=True)
                    results["updated"] += 1
                else:
                    # Skip - same data already exists
                    results["skipped"] += 1
            else:
                # New record - insert
                # Convert financial values to Decimal128
                _convert_decimals_to_128(product)
                
                # Ensure cleaned data
                _ensure_clean_data(product)
                
                collection.insert_one(product)
                results["inserted"] += 1
                
        except Exception as e:
            logger.error(f"Failed to save product {product.get('article_number') or product.get('sku')}: {e}")
            results["failed"] += 1
    
    return results


def _generate_source_id(product: dict, dataset: str) -> str:
    """Generate a stable source identifier for the product."""
    if dataset == "granit":
        article = product.get("article_number", "")
        ean = product.get("ean_gtin", "")
        if article:
            return f"granit:{article}"
        elif ean:
            return f"granit:ean:{ean}"
        else:
            return f"granit:unknown:{hash(str(product)[:100]) % 10000}"
    
    elif dataset == "blinkit":
        sku = product.get("sku", "")
        product_id = product.get("product_id", "")
        if sku:
            return f"blinkit:sku:{sku}"
        elif product_id:
            return f"blinkit:id:{product_id}"
        else:
            return f"blinkit:unknown:{hash(str(product)[:100]) % 10000}"
    
    return f"{dataset}:unknown"


def _regional_pricing_changed(existing: list, new_pricing: list) -> bool:
    """Check if regional pricing has actually changed."""
    if len(existing) != len(new_pricing):
        return True
    
    existing_map = {}
    for item in existing:
        country = item.get("country", "")
        if country:
            existing_map[country] = item
    
    new_map = {}
    for item in new_pricing:
        country = item.get("country", "")
        if country:
            new_map[country] = item
    
    if set(existing_map.keys()) != set(new_map.keys()):
        return True
    
    for country in existing_map:
        if country in new_map:
            existing_item = existing_map[country]
            new_item = new_map[country]
            # Compare key financial fields
            for key in ["net_price", "vat_rate", "gross_price", "currency"]:
                if existing_item.get(key) != new_item.get(key):
                    return True
    
    return False


def _convert_decimals_to_128(product: dict):
    """Convert Decimal values to BSON Decimal128 for MongoDB storage."""
    for key, value in product.items():
        if isinstance(value, Decimal):
            product[key] = Decimal128(value)
        elif isinstance(value, list):
            _convert_list_decimals_to_128(value)
        elif isinstance(value, dict):
            _convert_dict_decimals_to_128(value)


def _convert_list_decimals_to_128(lst: list):
    """Convert Decimal values in a list."""
    for i, item in enumerate(lst):
        if isinstance(item, Decimal):
            lst[i] = Decimal128(item)
        elif isinstance(item, dict):
            _convert_dict_decimals_to_128(item)


def _convert_dict_decimals_to_128(d: dict):
    """Convert Decimal values in a dict."""
    for key, value in d.items():
        if isinstance(value, Decimal):
            d[key] = Decimal128(value)
        elif isinstance(value, Decimal):
            d[key] = Decimal128(value)
        elif isinstance(value, list):
            _convert_list_decimals_to_128(value)
        elif isinstance(value, dict):
            _convert_dict_decimals_to_128(value)


def _ensure_clean_data(product: dict):
    """Ensure product has properly cleaned/normalized fields."""
    # Ensure regional_pricing financial values are Decimal128
    for pricing in product.get("regional_pricing", []):
        if isinstance(pricing.get("net_price"), Decimal):
            pricing["net_price"] = Decimal128(pricing["net_price"])
        if isinstance(pricing.get("vat_rate"), Decimal):
            pricing["vat_rate"] = Decimal128(pricing["vat_rate"])
        if isinstance(pricing.get("gross_price"), Decimal):
            pricing["gross_price"] = Decimal128(pricing["gross_price"])
    
    # Ensure pricing financial values are Decimal128
    for pricing in product.get("pricing", []):
        for key in ["mrp", "selling_price", "discount_amount", "discount_percentage", "gst_rate"]:
            if isinstance(pricing.get(key), Decimal):
                pricing[key] = Decimal128(pricing[key])
    
    # Ensure inventory financial values
    for inv in product.get("inventory", []):
        for key in ["available_quantity", "net_quantity", "delivery_sla"]:
            if isinstance(inv.get(key), Decimal):
                inv[key] = Decimal128(inv[key])


def get_products(dataset: str, filters: dict = None) -> list:
    """Retrieve products from MongoDB with optional filters."""
    collection = get_collection(dataset)
    
    query = {}
    if filters:
        query.update(filters)
    
    # Exclude internal metadata fields
    projection = {
        "_id": 0,
        "source_id": 1,
        "product_name": 1,
        "collected_at": 1
    }
    
    products = list(collection.find(query, projection))
    return products


def get_product_count(dataset: str) -> int:
    """Get the count of products in a dataset collection."""
    collection = get_collection(dataset)
    return collection.count_documents({})


def get_rejected_products(dataset: str) -> list:
    """Retrieve products that were rejected during validation."""
    # This is a placeholder - in a full implementation, 
    # we might have a separate rejected collection
    return []


def get_validation_errors(dataset: str) -> list:
    """Retrieve validation errors from previous runs."""
    # This is a placeholder
    return []


def check_connection():
    """Check MongoDB connection status (backward compatible)."""
    try:
        client = connect_db()
        client.admin.command("ping")
        return True, "Connected"
    except ConnectionError as e:
        return False, str(e)