DATASET_NAME = "granit"
DISPLAY_NAME = "GRANIT Parts - EU Region"
COLLECTION_NAME = "granit_products"

PRODUCT_FIELDS = [
    "article_number",
    "product_name",
    "description",
    "manufacturer",
    "brand",
    "supplier",
    "category",
    "subcategory",
    "product_type",
    "ean_gtin",
    "product_url",
    "image_url",
]

REGIONAL_PRICING_FIELDS = [
    "country",
    "country_code",
    "currency",
    "net_price",
    "vat_rate",
    "gross_price",
    "price_source",
    "effective_date",
]

SPECIFICATION_FIELDS = [
    "specification_name",
    "specification_value",
    "unit",
    "compatibility",
    "compatible_vehicle",
    "model",
    "year_range",
]

COMPLIANCE_FIELDS = [
    "regulation",
    "compliance_standard",
    "certification",
    "compliance_status",
    "compliance_source",
]

INVENTORY_FIELDS = [
    "warehouse",
    "country",
    "available_quantity",
    "stock_status",
    "shipping_method",
    "estimated_delivery",
    "logistics_source",
]