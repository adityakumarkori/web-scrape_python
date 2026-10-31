import os
from datetime import datetime
from decimal import Decimal
from collections import OrderedDict

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side, numbers
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation

from profiles import get_profile


def _get_currency_format(dataset: str) -> str:
    """Get the appropriate currency format string."""
    return '$#,##0.00'


def _get_decimal_format() -> str:
    """Get the appropriate decimal format string."""
    return '#,##0.00'


def _safe_value(value, default=None):
    """Safely get a value, returning default if None or empty."""
    if value is None or value == "":
        return default
    return value


def _convert_decimal_values(obj):
    """Recursively convert Decimal values to float for Excel compatibility."""
    if isinstance(obj, Decimal):
        return float(obj)
    elif isinstance(obj, dict):
        return {k: _convert_decimal_values(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_convert_decimal_values(item) for item in obj]
    return obj


def _format_currency_cell(cell, value):
    """Format a cell as currency."""
    if value is not None and value != "":
        try:
            cell.number_format = '$#,##0.00'
            cell.value = float(value)
        except (ValueError, TypeError):
            pass


def _format_percentage_cell(cell, value):
    """Format a cell as percentage."""
    if value is not None and value != "":
        try:
            cell.number_format = '0.00'
            cell.value = float(value) / 100 if abs(float(value)) <= 100 else float(value)
        except (ValueError, TypeError):
            pass


def _set_cell_style(cell, is_header=False, is_currency=False, is_percentage=False):
    """Apply consistent styling to a cell."""
    if is_header:
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
        cell.font.size = 11
    else:
        cell.font.size = 10
    
    cell.alignment = Alignment(wrap_text=True, vertical="center")
    cell.border = Border(
        bottom=Side(style="thin")
    )
    
    if is_currency:
        cell.number_format = '$#,##0.00'
    if is_percentage:
        cell.number_format = '0.00'


def _set_header_style(worksheet, max_col):
    """Apply header styling to the first row."""
    for col in range(1, max_col + 1):
        cell = worksheet.cell(row=1, column=col)
        _set_cell_style(cell, is_header=True)


def _set_column_widths(worksheet, headers, min_width=10, max_width=30):
    """Set appropriate column widths based on header names."""
    for col_idx, header in enumerate(headers, 1):
        # Estimate width based on header text length
        header_len = len(str(header))
        width = min(max(header_len + 3, min_width), max_width)
        worksheet.column_dimensions[get_column_letter(col_idx)].width = width


def _write_missing_value_note(worksheet, row, col, note="NOT_VERIFIED"):
    """Write a note for missing values."""
    cell = worksheet.cell(row=row, column=col)
    cell.value = note
    cell.fill = PatternFill(start_color="FFFFCC", end_color="FFFFCC", fill_type="solid")


# ============================================================
# GRANIT Export Functions
# ============================================================

def export_granit(products, output_path):
    """
    Export GRANIT products to Excel workbook.
    
    Creates worksheets:
    1. README
    2. Products
    3. Regional Pricing
    4. Specifications
    5. Compliance
    6. Inventory & Logistics
    7. Data Quality
    8. Data Dictionary
    9. Sources & Assumptions
    """
    wb = Workbook()
    
    # Remove default sheet
    ws_default = wb.active
    wb.remove(ws_default)
    
    # Define field mappings for GRANIT
    granit_fields = {
        "Products": [
            ("article_number", "Article Number", ""),
            ("product_name", "Product Name", ""),
            ("description", "Description", ""),
            ("manufacturer", "Manufacturer", ""),
            ("brand", "Brand", ""),
            ("category", "Category", ""),
            ("subcategory", "Subcategory", ""),
            ("product_type", "Product Type", ""),
            ("ean_gtin", "EAN/GTIN", ""),
            ("product_url", "Product URL", ""),
            ("image_url", "Image URL", ""),
        ],
        "Regional Pricing": [
            ("article_number", "Article Number", True),
            ("country", "Country", True),
            ("country_code", "Country Code", True),
            ("currency", "Currency", True),
            ("net_price", "Net Price", True, "currency"),
            ("vat_rate", "VAT Rate (%)", True, "percentage"),
            ("gross_price", "Gross Price", True, "currency"),
            ("price_source", "Price Source", False),
            ("effective_date", "Effective Date", False, "date"),
        ],
        "Specifications": [
            ("specification_name", "Specification Name", ""),
            ("specification_value", "Specification Value", ""),
            ("unit", "Unit", ""),
            ("compatibility", "Compatibility", ""),
            ("compatible_vehicle", "Compatible Vehicle", ""),
            ("model", "Model", ""),
            ("year_range", "Year Range", ""),
        ],
        "Compliance": [
            ("regulation", "Regulation", ""),
            ("compliance_standard", "Compliance Standard", ""),
            ("certification", "Certification", ""),
            ("compliance_status", "Compliance Status", ""),
        ],
        "Inventory & Logistics": [
            ("warehouse", "Warehouse", ""),
            ("country", "Country", ""),
            ("available_quantity", "Available Qty", True, "numeric"),
            ("stock_status", "Stock Status", ""),
            ("shipping_method", "Shipping Method", ""),
            ("estimated_delivery", "Est. Delivery", ""),
        ],
        "Data Quality": [
            ("product_identifier", "Product Identifier", ""),
            ("validation_status", "Validation Status", ""),
            ("missing_fields", "Missing Fields", ""),
            ("validation_errors", "Validation Errors", ""),
            ("duplicate_status", "Duplicate Status", ""),
            ("verification_status", "Verification Status", ""),
        ],
        "Data Dictionary": [
            ("column_name", "Column Name", ""),
            ("description", "Description", ""),
            ("data_type", "Data Type", ""),
            ("mandatory", "Mandatory", ""),
            ("validation_rule", "Validation Rule", ""),
            ("availability", "Availability Notes", ""),
        ],
        "Sources & Assumptions": [
            ("source_name", "Source Name", ""),
            ("source_url", "Source URL", ""),
            ("source_id", "Source ID", ""),
            ("collection_timestamp", "Collection Timestamp", ""),
            ("data_origin", "Data Origin", ""),
            ("record_classification", "Record Classification", ""),
        ],
    }
    
    # ---- README worksheet ----
    readme_ws = wb.create_sheet("README")
    _write_readme_worksheet(readme_ws, products, "granit")
    
    # ---- Products worksheet ----
    products_ws = wb.create_sheet("Products")
    _write_granit_products(products_ws, products)
    
    # ---- Regional Pricing worksheet ----
    pricing_ws = wb.create_sheet("Regional Pricing")
    _write_granit_regional_pricing(pricing_ws, products)
    
    # ---- Specifications worksheet ----
    specs_ws = wb.create_sheet("Specifications")
    _write_granit_specifications(specs_ws, products)
    
    # ---- Compliance worksheet ----
    compliance_ws = wb.create_sheet("Compliance")
    _write_granit_compliance(compliance_ws, products)
    
    # ---- Inventory & Logistics worksheet ----
    inventory_ws = wb.create_sheet("Inventory & Logistics")
    _write_granit_inventory(inventory_ws, products)
    
    # ---- Data Quality worksheet ----
    quality_ws = wb.create_sheet("Data Quality")
    _write_granit_data_quality(quality_ws, products)
    
    # ---- Data Dictionary worksheet ----
    dict_ws = wb.create_sheet("Data Dictionary")
    _write_granit_data_dictionary(dict_ws)
    
    # ---- Sources & Assumptions worksheet ----
    sources_ws = wb.create_sheet("Sources & Assumptions")
    _write_granit_sources(sources_ws, products)
    
    # Apply formatting
    _apply_granit_formatting(wb, products)
    
    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
    
    wb.save(output_path)


def _write_readme_worksheet(ws, products, dataset_name):
    """Write the README worksheet."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    verified = [p for p in products if p.get("validation_status") == "valid"]
    rejected = [p for p in products if p.get("validation_status") != "valid"]
    synthetic = [p for p in products if p.get("_synthetic", False)]
    
    data = [
        ["GRANIT EU Dataset Export"],
        [""],
        ["Dataset Name:", dataset_name],
        ["Region:", "European Union"],
        ["Generation Timestamp:", now],
        ["", "Record Counts"],
        ["Total Records:", len(products)],
        ["Verified Records:", len(verified)],
        ["Rejected Records:", len(rejected)],
        ["Synthetic Records:", len(synthetic)],
        ["", "Dataset Limitations"],
        ["- Regional pricing covers EU countries only"],
        ["- VAT rates vary by country"],
        ["- Compliance status based on manufacturer declarations"],
        ["- Inventory levels are real-time snapshots"],
        ["", "Missing-Data Explanation"],
        ["- Some products may lack complete specification data"],
        ["- Compliance certifications may not be verified"],
        ["- EAN/GTIN check digits validated algorithmically"],
        ["- Pricing sourced from JSON-LD structured data"],
    ]
    
    for r, row_data in enumerate(data, 1):
        for c, value in enumerate(row_data, 1):
            cell = ws.cell(row=r, column=c, value=value)
            if r == 1 or c == 1:
                _set_cell_style(cell, is_header=True)


def _write_granit_products(ws, products):
    """Write the Products worksheet."""
    headers = [
        "Article Number", "Product Name", "Description", "Manufacturer",
        "Brand", "Category", "Subcategory", "Product Type",
        "EAN/GTIN", "Product URL", "Image URL"
    ]
    
    _set_header_style(ws, len(headers))
    
    for col_idx, header in enumerate(headers, 1):
        ws.cell(row=1, column=col_idx, value=header)
    
    for row_idx, product in enumerate(products, 2):
        # Get article number for identifier
        article = product.get("article_number", "") or product.get("source_id", "").replace("granit:", "")
        
        values = [
            article,
            _safe_value(product.get("product_name")),
            _safe_value(product.get("description")),
            _safe_value(product.get("manufacturer")),
            _safe_value(product.get("brand")),
            _safe_value(product.get("category")),
            _safe_value(product.get("subcategory")),
            _safe_value(product.get("product_type")),
            _safe_value(product.get("ean_gtin")),
            _safe_value(product.get("product_url")),
            _safe_value(product.get("image_url")),
        ]
        
        for col_idx, value in enumerate(values, 1):
            cell = ws.cell(row=row_idx, column=col_idx, value=value)
            _set_cell_style(cell)


def _write_granit_regional_pricing(ws, products):
    """Write the Regional Pricing worksheet."""
    headers = [
        "Article Number", "Country", "Country Code", "Currency",
        "Net Price", "VAT Rate (%)", "Gross Price", "Price Source", "Effective Date"
    ]
    
    _set_header_style(ws, len(headers))
    
    row_idx = 2
    for product in products:
        article = product.get("article_number", "") or product.get("source_id", "").replace("granit:", "")
        regional_pricing = product.get("regional_pricing", [])
        
        for pricing in regional_pricing:
            values = [
                article,
                _safe_value(pricing.get("country")),
                _safe_value(pricing.get("country_code")),
                _safe_value(pricing.get("currency")),
                _safe_value(pricing.get("net_price")),
                _safe_value(pricing.get("vat_rate")),
                _safe_value(pricing.get("gross_price")),
                _safe_value(pricing.get("price_source")),
                _safe_value(pricing.get("effective_date")),
            ]
            
            for col_idx, value in enumerate(values, 1):
                cell = ws.cell(row=row_idx, column=col_idx, value=value)
                _set_cell_style(cell)
                
                # Format currency and percentage columns
                if col_idx == 5:  # Net Price
                    _format_currency_cell(cell, value)
                elif col_idx == 7:  # Gross Price
                    _format_currency_cell(cell, value)
                elif col_idx == 6:  # VAT Rate (%)
                    _format_percentage_cell(cell, value)
            
            row_idx += 1


def _write_granit_specifications(ws, products):
    """Write the Specifications worksheet."""
    headers = ["Specification Name", "Specification Value", "Unit", "Compatibility", 
                 "Compatible Vehicle", "Model", "Year Range"]
    
    _set_header_style(ws, len(headers))
    
    row_idx = 2
    for product in products:
        specs = product.get("specifications", [])
        for spec in specs:
            values = [
                _safe_value(spec.get("specification_name")),
                _safe_value(spec.get("specification_value")),
                _safe_value(spec.get("unit")),
                _safe_value(spec.get("compatibility")),
                _safe_value(spec.get("compatible_vehicle")),
                _safe_value(spec.get("model")),
                _safe_value(spec.get("year_range")),
            ]
            
            for col_idx, value in enumerate(values, 1):
                cell = ws.cell(row=row_idx, column=col_idx, value=value)
                _set_cell_style(cell)
            
            row_idx += 1


def _write_granit_compliance(ws, products):
    """Write the Compliance worksheet."""
    headers = ["Regulation", "Compliance Standard", "Certification", "Compliance Status"]
    
    _set_header_style(ws, len(headers))
    
    row_idx = 2
    for product in products:
        compliance = product.get("compliance", [])
        for comp in compliance:
            values = [
                _safe_value(comp.get("regulation")),
                _safe_value(comp.get("compliance_standard")),
                _safe_value(comp.get("certification")),
                _safe_value(comp.get("compliance_status")),
            ]
            
            for col_idx, value in enumerate(values, 1):
                cell = ws.cell(row=row_idx, column=col_idx, value=value)
                _set_cell_style(cell)
            
            row_idx += 1


def _write_granit_inventory(ws, products):
    """Write the Inventory & Logistics worksheet."""
    headers = ["Warehouse", "Country", "Available Quantity", "Stock Status",
                 "Shipping Method", "Est. Delivery"]
    
    _set_header_style(ws, len(headers))
    
    row_idx = 2
    for product in products:
        inventory = product.get("inventory", [])
        for inv in inventory:
            values = [
                _safe_value(inv.get("warehouse")),
                _safe_value(inv.get("country")),
                _safe_value(inv.get("available_quantity")),
                _safe_value(inv.get("stock_status")),
                _safe_value(inv.get("shipping_method")),
                _safe_value(inv.get("estimated_delivery")),
            ]
            
            for col_idx, value in enumerate(values, 1):
                cell = ws.cell(row=row_idx, column=col_idx, value=value)
                _set_cell_style(cell)
                
                # Format available quantity as numeric
                if col_idx == 3:
                    try:
                        cell.number_format = _get_decimal_format()
                        cell.value = float(value) if value and value != "" else None
                    except (ValueError, TypeError):
                        pass
            
            row_idx += 1


def _write_granit_data_quality(ws, products):
    """Write the Data Quality worksheet."""
    headers = ["Product Identifier", "Validation Status", "Missing Fields",
                 "Validation Errors", "Duplicate Status", "Verification Status"]
    
    _set_header_style(ws, len(headers))
    
    row_idx = 2
    for product in products:
        # Get article number as identifier
        article = product.get("article_number", "") or product.get("source_id", "").replace("granit:", "")
        
        # Determine validation status
        errors = product.get("validation_errors", [])
        if not errors:
            validation_status = "valid"
        elif isinstance(errors, list) and all("Missing required field" in e for e in errors):
            validation_status = "invalid_missing"
        else:
            validation_status = "invalid"
        
        # Get missing fields
        missing = product.get("missing_fields", [])
        missing_str = "; ".join(str(m) for m in missing) if missing else ""
        
        # Get validation errors summary
        errors_str = "; ".join(str(e) for e in errors) if errors else ""
        
        # Determine duplicate status
        is_dup = product.get("is_duplicate", False)
        dup_status = "duplicate" if is_dup else "original"
        
        # Verification status
        verif_status = product.get("_verified", True)  # Default to True unless marked synthetic
        if product.get("_synthetic", False):
            verif_status = "synthetic"
        
        values = [
            article,
            validation_status,
            missing_str,
            errors_str,
            dup_status,
            verif_status,
        ]
        
        for col_idx, value in enumerate(values, 1):
            cell = ws.cell(row=row_idx, column=col_idx, value=value)
            _set_cell_style(cell)
        
        row_idx += 1


def _write_granit_data_dictionary(ws):
    """Write the Data Dictionary worksheet with all GRANIT columns."""
    dd_data = [
        ("article_number", "Article Number", "Text", "Mandatory", 
         "Must be present; validated for format"),
        ("product_name", "Product Name", "Text", "Mandatory", 
         "Must be present; min 2 characters"),
        ("description", "Description", "Text", "Optional", 
         "Free text description"),
        ("manufacturer", "Manufacturer", "Text", "Optional", 
         "Manufacturer name"),
        ("brand", "Brand", "Text", "Optional", 
         "Brand/trade name"),
        ("category", "Category", "Text", "Optional", 
         "Product category"),
        ("subcategory", "Subcategory", "Text", "Optional", 
         "Sub-category within main category"),
        ("product_type", "Product Type", "Text", "Optional", 
         "Product classification type"),
        ("ean_gtin", "EAN/GTIN", "Text", "Conditional", 
         "Must pass check digit validation if present"),
        ("product_url", "Product URL", "URL", "Optional", 
         "Must be valid HTTP/HTTPS URL"),
        ("image_url", "Image URL", "URL", "Optional", 
         "Must be valid HTTP/HTTPS URL"),
        ("regional_pricing", "Regional Pricing", "JSON", "Optional", 
         "Country-specific pricing entries"),
        ("specifications", "Specifications", "JSON", "Optional", 
         "Technical specification entries"),
        ("compliance", "Compliance", "JSON", "Optional", 
         "Regulation and certification entries"),
        ("inventory", "Inventory", "JSON", "Optional", 
         "Stock and logistics entries"),
    ]
    
    _set_header_style(ws, 3)
    
    # Headers: Column Name, Description, Data Type
    ws.cell(row=1, column=1, value="Column Name")
    ws.cell(row=1, column=2, value="Description")
    ws.cell(row=1, column=3, value="Data Type")
    _set_cell_style(ws.cell(row=1, column=1), is_header=True)
    _set_cell_style(ws.cell(row=1, column=2), is_header=True)
    _set_cell_style(ws.cell(row=1, column=3), is_header=True)
    
    for r, (col_name, desc, dtype, mandatory, rule) in enumerate(dd_data, 2):
        ws.cell(row=r, column=1, value=col_name)
        ws.cell(row=r, column=2, value=desc)
        ws.cell(row=r, column=3, value=dtype)
        
        _set_cell_style(ws.cell(row=r, column=1))
        _set_cell_style(ws.cell(row=r, column=2))
        _set_cell_style(ws.cell(row=r, column=3))
        
        # Add mandatory info to description if applicable
        if mandatory == "Mandatory":
            ws.cell(row=r, column=2).value = f"{desc} (Mandatory)"
        
        # Set column widths
        ws.column_dimensions['A'].width = 25
        ws.column_dimensions['B'].width = 50
        ws.column_dimensions['C'].width = 15


def _write_granit_sources(ws, products):
    """Write the Sources & Assumptions worksheet."""
    headers = ["Source Name", "Source URL", "Source ID", "Collection Timestamp",
                 "Data Origin", "Record Classification"]
    
    _set_header_style(ws, len(headers))
    
    row_idx = 2
    for product in products:
        source_name = product.get("source", "granit_catalog")
        source_url = product.get("product_url", "")
        source_id = product.get("source_id", "")
        collected_at = product.get("collected_at", "")
        
        # Determine data origin and classification
        data_origin = "web_scraping"
        if product.get("_synthetic", False):
            data_origin = "synthetic"
        elif product.get("_verified", True) and not product.get("_synthetic", False):
            data_origin = "verified"
        else:
            data_origin = "unverified"
        
        record_classification = "verified"
        if product.get("_synthetic", False):
            record_classification = "synthetic"
        elif not product.get("_verified", True):
            record_classification = "unverified"
        
        values = [
            source_name,
            _safe_value(source_url),
            _safe_value(source_id),
            _safe_value(collected_at),
            data_origin,
            record_classification,
        ]
        
        for col_idx, value in enumerate(values, 1):
            cell = ws.cell(row=row_idx, column=col_idx, value=value)
            _set_cell_style(cell)
        
        row_idx += 1


# ============================================================
# Blinkit Export Functions
# ============================================================

def export_blinkit(products, output_path):
    """
    Export Blinkit products to Excel workbook.
    
    Creates worksheets:
    1. README
    2. Products
    3. Pricing & Tax
    4. Packaging & Ingredients
    5. Suppliers
    6. Dark Stores & Inventory
    7. Delivery & Zones
    8. Data Quality
    9. Data Dictionary
    10. Sources & Assumptions
    """
    wb = Workbook()
    
    # Remove default sheet
    ws_default = wb.active
    wb.remove(ws_default)
    
    # Define field mappings for Blinkit
    blinkit_fields = {
        "Products": [
            ("sku", "SKU", ""),
            ("product_id", "Product ID", ""),
            ("product_name", "Product Name", ""),
            ("brand", "Brand", ""),
            ("category", "Category", ""),
            ("subcategory", "Subcategory", ""),
            ("product_description", "Product Description", ""),
            ("barcode", "Barcode/GTIN", ""),
            ("product_url", "Product URL", ""),
            ("image_url", "Image URL", ""),
        ],
        "Pricing & Tax": [
            ("sku", "SKU", True),
            ("mrp", "MRP", True, "currency"),
            ("selling_price", "Selling Price", True, "currency"),
            ("discount_amount", "Discount Amount", True, "currency"),
            ("discount_percentage", "Discount %", True, "percentage"),
            ("gst_rate", "GST Rate (%)", True, "percentage"),
            ("hsn_code", "HSN Code", False),
            ("price_source", "Price Source", False),
            ("effective_date", "Effective Date", False, "date"),
        ],
        "Packaging & Ingredients": [
            ("net_quantity", "Net Quantity", True, "numeric"),
            ("unit", "Unit", ""),
            ("package_type", "Package Type", ""),
            ("ingredients", "Ingredients", ""),
            ("manufacturing_date", "Manufacturing Date", False, "date"),
            ("expiry_date", "Expiry Date", False, "date"),
            ("shelf_life", "Shelf Life", ""),
        ],
        "Suppliers": [
            ("supplier_name", "Supplier Name", ""),
            ("supplier_location", "Supplier Location", ""),
            ("procurement_type", "Procurement Type", ""),
            ("supplier_status", "Supplier Status", ""),
        ],
        "Dark Stores & Inventory": [
            ("dark_store_id", "Dark Store ID", ""),
            ("dark_store_name", "Dark Store Name", ""),
            ("zone", "Zone", ""),
            ("pincode", "Pincode", ""),
            ("available_quantity", "Available Qty", True, "numeric"),
            ("stock_status", "Stock Status", ""),
            ("last_restocked", "Last Restocked", False, "date"),
        ],
        "Delivery & Zones": [
            ("zone", "Zone", ""),
            ("pincode", "Pincode", ""),
            ("delivery_sla", "Delivery SLA", True, "numeric"),
            ("serviceability_status", "Serviceability Status", ""),
            ("effective_date", "Effective Date", False, "date"),
        ],
        "Data Quality": [
            ("product_identifier", "Product Identifier", ""),
            ("validation_status", "Validation Status", ""),
            ("missing_fields", "Missing Fields", ""),
            ("validation_errors", "Validation Errors", ""),
            ("duplicate_status", "Duplicate Status", ""),
            ("verification_status", "Verification Status", ""),
        ],
        "Data Dictionary": [
            ("column_name", "Column Name", ""),
            ("description", "Description", ""),
            ("data_type", "Data Type", ""),
            ("mandatory", "Mandatory", ""),
            ("validation_rule", "Validation Rule", ""),
            ("availability", "Availability Notes", ""),
        ],
        "Sources & Assumptions": [
            ("source_name", "Source Name", ""),
            ("source_url", "Source URL", ""),
            ("source_id", "Source ID", ""),
            ("collection_timestamp", "Collection Timestamp", ""),
            ("data_origin", "Data Origin", ""),
            ("record_classification", "Record Classification", ""),
        ],
    }
    
    # ---- README worksheet ----
    readme_ws = wb.create_sheet("README")
    _write_blinkit_readme(readme_ws, products)
    
    # ---- Products worksheet ----
    products_ws = wb.create_sheet("Products")
    _write_blinkit_products(products_ws, products)
    
    # ---- Pricing & Tax worksheet ----
    pricing_ws = wb.create_sheet("Pricing & Tax")
    _write_blinkit_pricing(pricing_ws, products)
    
    # ---- Packaging & Ingredients worksheet ----
    packaging_ws = wb.create_sheet("Packaging & Ingredients")
    _write_blinkit_packaging(packaging_ws, products)
    
    # ---- Suppliers worksheet ----
    suppliers_ws = wb.create_sheet("Suppliers")
    _write_blinkit_suppliers(suppliers_ws, products)
    
    # ---- Dark Stores & Inventory worksheet ----
    inventory_ws = wb.create_sheet("Dark Stores & Inventory")
    _write_blinkit_inventory(inventory_ws, products)
    
    # ---- Delivery & Zones worksheet ----
    delivery_ws = wb.create_sheet("Delivery & Zones")
    _write_blinkit_delivery(delivery_ws, products)
    
    # ---- Data Quality worksheet ----
    quality_ws = wb.create_sheet("Data Quality")
    _write_blinkit_data_quality(quality_ws, products)
    
    # ---- Data Dictionary worksheet ----
    dict_ws = wb.create_sheet("Data Dictionary")
    _write_blinkit_data_dictionary(dict_ws)
    
    # ---- Sources & Assumptions worksheet ----
    sources_ws = wb.create_sheet("Sources & Assumptions")
    _write_blinkit_sources(sources_ws, products)
    
    # Apply formatting
    _apply_blinkit_formatting(wb, products)
    
    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
    
    wb.save(output_path)


def _write_blinkit_readme(ws, products):
    """Write the README worksheet for Blinkit."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    verified = [p for p in products if p.get("validation_status") == "valid"]
    rejected = [p for p in products if p.get("validation_status") != "valid"]
    synthetic = [p for p in products if p.get("_synthetic", False)]
    
    data = [
        ["Blinkit Bengaluru Dataset Export"],
        [""],
        ["Dataset Name:", "Blinkit"],
        ["Region:", "Bengaluru, Karnataka"],
        ["Generation Timestamp:", now],
        ["", "Record Counts"],
        ["Total Records:", len(products)],
        ["Verified Records:", len(verified)],
        ["Rejected Records:", len(rejected)],
        ["Synthetic Records:", len(synthetic)],
        ["", "Dataset Limitations"],
        ["- GST rates are Indian national rates (5%, 12%, 18%, 28%)"],
        ["- Pincodes limited to Bengaluru region"],
        ["- MRP regulated under Legal Metrology Act"],
        ["- Delivery SLA limited to serviceable areas"],
        ["", "Missing-Data Explanation"],
        ["- Some products may lack full supplier details"],
        ["- Packaging information may be incomplete"],
        ["- Delivery SLA varies by pincode and zone"],
        ["- GST rates based on product category"],
        ["- Available quantity is store-specific"],
    ]
    
    for r, row_data in enumerate(data, 1):
        for c, value in enumerate(row_data, 1):
            cell = ws.cell(row=r, column=c, value=value)
            if r == 1 or c == 1:
                _set_cell_style(cell, is_header=True)


def _write_blinkit_products(ws, products):
    """Write the Products worksheet for Blinkit."""
    headers = ["SKU", "Product ID", "Product Name", "Brand", "Category",
                 "Subcategory", "Barcode/GTIN", "Product URL", "Image URL"]
    
    _set_header_style(ws, len(headers))
    
    for col_idx, header in enumerate(headers, 1):
        ws.cell(row=1, column=col_idx, value=header)
    
    for row_idx, product in enumerate(products, 2):
        sku = product.get("sku", "") or product.get("source_id", "").replace("blinkit:", "")
        
        values = [
            sku,
            _safe_value(product.get("product_id")),
            _safe_value(product.get("product_name")),
            _safe_value(product.get("brand")),
            _safe_value(product.get("category")),
            _safe_value(product.get("subcategory")),
            _safe_value(product.get("barcode")),
            _safe_value(product.get("product_url")),
            _safe_value(product.get("image_url")),
        ]
        
        for col_idx, value in enumerate(values, 1):
            cell = ws.cell(row=row_idx, column=col_idx, value=value)
            _set_cell_style(cell)


def _write_blinkit_pricing(ws, products):
    """Write the Pricing & Tax worksheet for Blinkit."""
    headers = ["SKU", "MRP", "Selling Price", "Discount Amount",
                 "Discount %", "GST Rate (%)", "HSN Code", "Price Source", "Effective Date"]
    
    _set_header_style(ws, len(headers))
    
    row_idx = 2
    for product in products:
        sku = product.get("sku", "") or product.get("source_id", "").replace("blinkit:", "")
        pricing = product.get("pricing", [])
        
        for p in pricing:
            values = [
                sku,
                _safe_value(p.get("mrp")),
                _safe_value(p.get("selling_price")),
                _safe_value(p.get("discount_amount")),
                _safe_value(p.get("discount_percentage")),
                _safe_value(p.get("gst_rate")),
                _safe_value(p.get("hsn_code")),
                _safe_value(p.get("price_source")),
                _safe_value(p.get("effective_date")),
            ]
            
            for col_idx, value in enumerate(values, 1):
                cell = ws.cell(row=row_idx, column=col_idx, value=value)
                _set_cell_style(cell)
                
                # Format currency columns
                if col_idx == 3:  # Selling Price
                    _format_currency_cell(cell, value)
                elif col_idx == 5:  # MRP (col 1=SKU, 2=MRP, 3=Selling, 4=Discount Amt, 5=Discount %)
                    _format_currency_cell(cell, value)
                elif col_idx == 2:  # MRP
                    _format_currency_cell(cell, value)
                
                # Format percentage columns
                if col_idx == 6:  # GST Rate (%)
                    _format_percentage_cell(cell, value)
                elif col_idx == 5:  # Discount %
                    _format_percentage_cell(cell, value)
            
            row_idx += 1


def _write_blinkit_packaging(ws, products):
    """Write the Packaging & Ingredients worksheet for Blinkit."""
    headers = ["Net Quantity", "Unit", "Package Type", "Ingredients",
                 "Manufacturing Date", "Expiry Date", "Shelf Life"]
    
    _set_header_style(ws, len(headers))
    
    row_idx = 2
    for product in products:
        packaging = product.get("packaging", [])
        for pkg in packaging:
            values = [
                _safe_value(pkg.get("net_quantity")),
                _safe_value(pkg.get("unit")),
                _safe_value(pkg.get("package_type")),
                _safe_value(pkg.get("ingredients")),
                _safe_value(pkg.get("manufacturing_date")),
                _safe_value(pkg.get("expiry_date")),
                _safe_value(pkg.get("shelf_life")),
            ]
            
            for col_idx, value in enumerate(values, 1):
                cell = ws.cell(row=row_idx, column=col_idx, value=value)
                _set_cell_style(cell)
                
                # Format net quantity as numeric
                if col_idx == 1:
                    try:
                        cell.number_format = _get_decimal_format()
                        cell.value = float(value) if value and value != "" else None
                    except (ValueError, TypeError):
                        pass
            
            row_idx += 1


def _write_blinkit_suppliers(ws, products):
    """Write the Suppliers worksheet for Blinkit."""
    headers = ["Supplier Name", "Supplier Location", "Procurement Type",
                 "Supplier Status"]
    
    _set_header_style(ws, len(headers))
    
    row_idx = 2
    for product in products:
        suppliers = product.get("supplier", [])
        for sup in suppliers:
            values = [
                _safe_value(sup.get("supplier_name")),
                _safe_value(sup.get("supplier_location")),
                _safe_value(sup.get("procurement_type")),
                _safe_value(sup.get("supplier_status")),
            ]
            
            for col_idx, value in enumerate(values, 1):
                cell = ws.cell(row=row_idx, column=col_idx, value=value)
                _set_cell_style(cell)
            
            row_idx += 1


def _write_blinkit_inventory(ws, products):
    """Write the Dark Stores & Inventory worksheet for Blinkit."""
    headers = ["Dark Store ID", "Dark Store Name", "Zone", "Pincode",
                 "Available Quantity", "Stock Status", "Last Restocked"]
    
    _set_header_style(ws, len(headers))
    
    row_idx = 2
    for product in products:
        inventory = product.get("inventory", [])
        for inv in inventory:
            values = [
                _safe_value(inv.get("dark_store_id")),
                _safe_value(inv.get("dark_store_name")),
                _safe_value(inv.get("zone")),
                _safe_value(inv.get("pincode")),
                _safe_value(inv.get("available_quantity")),
                _safe_value(inv.get("stock_status")),
                _safe_value(inv.get("last_restocked")),
            ]
            
            for col_idx, value in enumerate(values, 1):
                cell = ws.cell(row=row_idx, column=col_idx, value=value)
                _set_cell_style(cell)
                
                # Format available quantity as numeric
                if col_idx == 5:
                    try:
                        cell.number_format = _get_decimal_format()
                        cell.value = float(value) if value and value != "" else None
                    except (ValueError, TypeError):
                        pass
            
            row_idx += 1


def _write_blinkit_delivery(ws, products):
    """Write the Delivery & Zones worksheet for Blinkit."""
    headers = ["Zone", "Pincode", "Delivery SLA", "Serviceability Status", "Effective Date"]
    
    _set_header_style(ws, len(headers))
    
    row_idx = 2
    for product in products:
        delivery = product.get("delivery", [])
        for d in delivery:
            values = [
                _safe_value(d.get("zone")),
                _safe_value(d.get("pincode")),
                _safe_value(d.get("delivery_sla")),
                _safe_value(d.get("serviceability_status")),
                _safe_value(d.get("effective_date")),
            ]
            
            for col_idx, value in enumerate(values, 1):
                cell = ws.cell(row=row_idx, column=col_idx, value=value)
                _set_cell_style(cell)
                
                # Format delivery SLA as numeric
                if col_idx == 3:
                    try:
                        cell.number_format = _get_decimal_format()
                        cell.value = float(value) if value and value != "" else None
                    except (ValueError, TypeError):
                        pass
            
            row_idx += 1


def _write_blinkit_data_quality(ws, products):
    """Write the Data Quality worksheet for Blinkit."""
    headers = ["Product Identifier", "Validation Status", "Missing Fields",
                 "Validation Errors", "Duplicate Status", "Verification Status"]
    
    _set_header_style(ws, len(headers))
    
    row_idx = 2
    for product in products:
        # Get SKU as identifier
        sku = product.get("sku", "") or product.get("source_id", "").replace("blinkit:", "")
        
        # Determine validation status
        errors = product.get("validation_errors", [])
        if not errors:
            validation_status = "valid"
        else:
            validation_status = "invalid"
        
        # Get missing fields
        missing = product.get("missing_fields", [])
        missing_str = "; ".join(str(m) for m in missing) if missing else ""
        
        # Get validation errors summary
        errors_str = "; ".join(str(e) for e in errors) if errors else ""
        
        # Determine duplicate status
        is_dup = product.get("is_duplicate", False)
        dup_status = "duplicate" if is_dup else "original"
        
        # Verification status
        verif_status = product.get("_verified", True)
        if product.get("_synthetic", False):
            verif_status = "synthetic"
        
        values = [
            sku,
            validation_status,
            missing_str,
            errors_str,
            dup_status,
            verif_status,
        ]
        
        for col_idx, value in enumerate(values, 1):
            cell = ws.cell(row=row_idx, column=col_idx, value=value)
            _set_cell_style(cell)
        
        row_idx += 1


def _write_blinkit_data_dictionary(ws):
    """Write the Data Dictionary worksheet with all Blinkit columns."""
    dd_data = [
        ("sku", "SKU", "Text", "Mandatory",
         "Must be present; unique per product"),
        ("product_id", "Product ID", "Text", "Conditional",
         "Alternative product identifier"),
        ("product_name", "Product Name", "Text", "Mandatory",
         "Must be present; min 2 characters"),
        ("brand", "Brand", "Text", "Optional",
         "Brand/trade name"),
        ("category", "Category", "Text", "Optional",
         "Product category"),
        ("subcategory", "Subcategory", "Text", "Optional",
         "Sub-category within main category"),
        ("product_description", "Product Description", "Text", "Optional",
         "Free text description"),
        ("barcode", "Barcode/GTIN", "Text", "Conditional",
         "Must pass check digit validation if present"),
        ("product_url", "Product URL", "URL", "Optional",
         "Must be valid HTTP/HTTPS URL"),
        ("image_url", "Image URL", "URL", "Optional",
         "Must be valid HTTP/HTTPS URL"),
        ("pricing", "Pricing", "JSON", "Optional",
         "Price entries with MRP, selling price, GST"),
        ("packaging", "Packaging", "JSON", "Optional",
         "Net quantity, ingredients, dates"),
        ("supplier", "Supplier", "JSON", "Optional",
         "Supplier name, location, status"),
        ("inventory", "Inventory", "JSON", "Optional",
         "Dark store stock, pincodes, quantities"),
        ("delivery", "Delivery", "JSON", "Optional",
         "Zone, pincode, SLA, serviceability"),
    ]
    
    _set_header_style(ws, 3)
    
    # Headers: Column Name, Description, Data Type
    ws.cell(row=1, column=1, value="Column Name")
    ws.cell(row=1, column=2, value="Description")
    ws.cell(row=1, column=3, value="Data Type")
    _set_cell_style(ws.cell(row=1, column=1), is_header=True)
    _set_cell_style(ws.cell(row=1, column=2), is_header=True)
    _set_cell_style(ws.cell(row=1, column=3), is_header=True)
    
    for r, (col_name, desc, dtype, mandatory, rule) in enumerate(dd_data, 2):
        ws.cell(row=r, column=1, value=col_name)
        ws.cell(row=r, column=2, value=desc)
        ws.cell(row=r, column=3, value=dtype)
        
        _set_cell_style(ws.cell(row=r, column=1))
        _set_cell_style(ws.cell(row=r, column=2))
        _set_cell_style(ws.cell(row=r, column=3))
        
        # Add mandatory info to description if applicable
        if mandatory == "Mandatory":
            ws.cell(row=r, column=2).value = f"{desc} (Mandatory)"
        
        # Set column widths
        ws.column_dimensions['A'].width = 25
        ws.column_dimensions['B'].width = 50
        ws.column_dimensions['C'].width = 15


def _write_blinkit_sources(ws, products):
    """Write the Sources & Assumptions worksheet for Blinkit."""
    headers = ["Source Name", "Source URL", "Source ID", "Collection Timestamp",
                 "Data Origin", "Record Classification"]
    
    _set_header_style(ws, len(headers))
    
    row_idx = 2
    for product in products:
        source_name = product.get("source", "blinkit_grocery")
        source_url = product.get("product_url", "")
        source_id = product.get("source_id", "")
        collected_at = product.get("collected_at", "")
        
        # Determine data origin and classification
        data_origin = "web_scraping"
        if product.get("_synthetic", False):
            data_origin = "synthetic"
        elif product.get("_verified", True) and not product.get("_synthetic", False):
            data_origin = "verified"
        else:
            data_origin = "unverified"
        
        record_classification = "verified"
        if product.get("_synthetic", False):
            record_classification = "synthetic"
        elif not product.get("_verified", True):
            record_classification = "unverified"
        
        values = [
            source_name,
            _safe_value(source_url),
            _safe_value(source_id),
            _safe_value(collected_at),
            data_origin,
            record_classification,
        ]
        
        for col_idx, value in enumerate(values, 1):
            cell = ws.cell(row=row_idx, column=col_idx, value=value)
            _set_cell_style(cell)
        
        row_idx += 1


# ============================================================
# Formatting Functions
# ============================================================

def _apply_granit_formatting(wb, products):
    """Apply formatting to GRANIT workbook."""
    # Set column widths for all sheets
    for sheet_name in wb.sheetnames:
        ws = wb[sheet_name]
        if sheet_name == "Products":
            _set_column_widths(ws, [
                "Article Number", "Product Name", "Description", "Manufacturer",
                "Brand", "Category", "Subcategory", "Product Type",
                "EAN/GTIN", "Product URL", "Image URL"
            ])
        elif sheet_name == "Regional Pricing":
            _set_column_widths(ws, [
                "Article Number", "Country", "Country Code", "Currency",
                "Net Price", "VAT Rate (%)", "Gross Price", "Price Source", "Effective Date"
            ])
        elif sheet_name == "Data Dictionary":
            pass  # Widths already set in _write_granit_data_dictionary


def _apply_blinkit_formatting(wb, products):
    """Apply formatting to Blinkit workbook."""
    # Set column widths for all sheets
    for sheet_name in wb.sheetnames:
        ws = wb[sheet_name]
        if sheet_name == "Products":
            _set_column_widths(ws, ["SKU", "Product ID", "Product Name", "Brand",
                                      "Category", "Subcategory", "Barcode/GTIN",
                                      "Product URL", "Image URL"])
        elif sheet_name == "Pricing & Tax":
            _set_column_widths(ws, ["SKU", "MRP", "Selling Price", "Discount Amount",
                                      "Discount %", "GST Rate (%)", "HSN Code",
                                      "Price Source", "Effective Date"])
        elif sheet_name == "Data Dictionary":
            pass  # Widths already set in _write_blinkit_data_dictionary


# ============================================================
# Export Controller
# ============================================================

def export_dataset(products, dataset: str, output_dir: str = "output") -> dict:
    """
    Export a dataset to Excel workbooks.
    
    Returns dict with paths to generated files.
    """
    os.makedirs(output_dir, exist_ok=True)
    
    results = {"granit": None, "blinkit": None}
    
    if dataset in ("granit", "all"):
        granit_path = os.path.join(output_dir, "GRANIT_Parts_EU_Sample_Dataset.xlsx")
        export_granit(products, granit_path)
        results["granit"] = granit_path
    
    if dataset in ("blinkit", "all"):
        blinkit_path = os.path.join(output_dir, "Blinkit_Bengaluru_Sample_Dataset.xlsx")
        export_blinkit(products, blinkit_path)
        results["blinkit"] = blinkit_path
    
    return results