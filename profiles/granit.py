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

REQUIRED_FIELDS = ["article_number", "product_name"]

EXTRACTION_CONFIG = {
    "enabled": False,
    "name": "granit_catalog",
    "allowed_domains": ["granit-parts.com", "www.granit-parts.com"],
    "base_urls": [],
    "pagination": {
        "enabled": False,
        "next_selector": "a.next-page, a.pagination-next, li.next a",
        "max_pages": 10,
    },
    "json_ld_types": ["Product", "AutoPartsProduct"],
    "field_selectors": {
        "article_number": "[data-article-number], .article-number, [itemprop=sku]",
        "product_name": "[itemprop=name], h1.product-title, .product-name",
        "description": "[itemprop=description], .product-description",
        "manufacturer": "[itemprop=manufacturer], .manufacturer",
        "brand": "[itemprop=brand], .brand",
        "category": "[itemprop=category], .category",
        "ean_gtin": "[itemprop=gtin], [itemprop=gtin13], .ean, .gtin",
        "image_url": "[itemprop=image], .product-image img",
    },
}

ISO_COUNTRY_CODES = {
    "Austria", "Belgium", "Bulgaria", "Croatia", "Cyprus", "Czech Republic",
    "Denmark", "Estonia", "Finland", "France", "Germany", "Greece", "Hungary",
    "Ireland", "Italy", "Latvia", "Lithuania", "Luxembourg", "Malta",
    "Netherlands", "Poland", "Portugal", "Romania", "Slovakia", "Slovenia",
    "Spain", "Sweden", "Switzerland", "United Kingdom", "Norway"
}

ISO_CURRENCY_CODES = {"EUR", "GBP", "CHF", "SEK", "NOK", "DKK", "PLN", "CZK", "HUF", "RON", "BGN", "HRK"}