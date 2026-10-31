DATASET_NAME = "blinkit"
DISPLAY_NAME = "Blinkit - Bengaluru"
COLLECTION_NAME = "blinkit_products"

PRODUCT_FIELDS = [
    "product_id",
    "sku",
    "product_name",
    "brand",
    "category",
    "subcategory",
    "product_description",
    "barcode",
    "product_url",
    "image_url",
]

PRICING_FIELDS = [
    "mrp",
    "selling_price",
    "discount_amount",
    "discount_percentage",
    "gst_rate",
    "hsn_code",
    "price_source",
    "effective_date",
]

PACKAGING_FIELDS = [
    "net_quantity",
    "unit",
    "package_type",
    "ingredients",
    "nutritional_information",
    "manufacturing_date",
    "expiry_date",
    "shelf_life",
]

SUPPLIER_FIELDS = [
    "supplier_name",
    "supplier_location",
    "supplier_contact",
    "procurement_type",
    "supplier_status",
    "data_source",
]

INVENTORY_FIELDS = [
    "dark_store_id",
    "dark_store_name",
    "zone",
    "pincode",
    "available_quantity",
    "stock_status",
    "last_restocked",
    "inventory_source",
]

DELIVERY_FIELDS = [
    "zone",
    "pincode",
    "delivery_sla",
    "serviceability_status",
    "delivery_source",
    "effective_date",
]