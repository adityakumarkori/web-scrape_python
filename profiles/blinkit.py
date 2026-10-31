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

REQUIRED_FIELDS = ["sku", "product_name"]

EXTRACTION_CONFIG = {
    "enabled": False,
    "name": "blinkit_grocery",
    "allowed_domains": ["blinkit.com", "www.blinkit.com"],
    "base_urls": [],
    "pagination": {
        "enabled": False,
        "next_selector": "a.next-page, a.pagination-next, li.next a",
        "max_pages": 10,
    },
    "json_ld_types": ["Product", "GroceryProduct"],
    "field_selectors": {
        "sku": "[data-sku], .sku, [itemprop=sku]",
        "product_name": "[itemprop=name], h1.product-title, .product-name",
        "product_description": "[itemprop=description], .product-description",
        "brand": "[itemprop=brand], .brand",
        "category": "[itemprop=category], .category",
        "barcode": "[itemprop=gtin], [itemprop=gtin13], .barcode, .gtin",
        "image_url": "[itemprop=image], .product-image img",
        "mrp": "[itemprop=highPrice], .mrp, .original-price",
        "selling_price": "[itemprop=price], .selling-price, .current-price",
        "gst_rate": "[itemprop=taxRate], .gst-rate",
    },
}

BENGALURU_PINCODES = {
    "560001", "560002", "560003", "560004", "560005", "560006", "560007", "560008",
    "560009", "560010", "560011", "560012", "560013", "560014", "560015", "560016",
    "560017", "560018", "560019", "560020", "560021", "560022", "560023", "560024",
    "560025", "560026", "560027", "560028", "560029", "560030", "560031", "560032",
    "560033", "560034", "560035", "560036", "560037", "560038", "560039", "560040",
    "560041", "560042", "560043", "560044", "560045", "560046", "560047", "560048",
    "560049", "560050", "560051", "560052", "560053", "560054", "560055", "560056",
    "560057", "560058", "560059", "560060", "560061", "560062", "560063", "560064",
    "560065", "560066", "560067", "560068", "560069", "560070", "560071", "560072",
    "560073", "560074", "560075", "560076", "560077", "560078", "560079", "560080",
    "560081", "560082", "560083", "560084", "560085", "560086", "560087", "560088",
    "560089", "560090", "560091", "560092", "560093", "560094", "560095", "560096",
    "560097", "560098", "560099", "560100", "560101", "560102", "560103", "560104",
    "560105", "560106", "560107", "560108", "560109", "560110",
}

GST_RATES = {0, 5, 12, 18, 28}

INTERNAL_FIELDS_NOT_PUBLIC = {
    "dark_store_id", "dark_store_name", "zone", "pincode", "available_quantity",
    "stock_status", "last_restocked", "inventory_source", "delivery_sla",
    "serviceability_status", "procurement_type", "supplier_contact", "supplier_status",
    "supplier_name", "supplier_location"
}