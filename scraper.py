import re
import time
import ipaddress
from urllib.parse import urlparse, urljoin
from datetime import datetime
from typing import Optional, Dict, List, Any
from decimal import Decimal

import requests
from bs4 import BeautifulSoup

import config


class URLSafetyError(Exception):
    pass


class ScraperError(Exception):
    pass


def is_safe_url(url: str, allowed_domains: Optional[List[str]] = None) -> bool:
    parsed = urlparse(url)
    
    if parsed.scheme not in ("http", "https"):
        return False
    
    hostname = parsed.hostname
    if not hostname:
        return False
    
    if hostname in ("localhost", "127.0.0.1", "::1"):
        return False
    
    try:
        ip = ipaddress.ip_address(hostname)
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved:
            return False
    except ValueError:
        pass
    
    if allowed_domains:
        if not any(hostname == d or hostname.endswith("." + d) for d in allowed_domains):
            return False
    
    return True


def validate_redirect(url: str, allowed_domains: Optional[List[str]] = None) -> str:
    parsed = urlparse(url)
    if not is_safe_url(url, allowed_domains):
        raise URLSafetyError(f"Unsafe redirect URL: {url}")
    return url


def fetch_page(url: str, timeout: Optional[int] = None, delay: Optional[float] = None,
               user_agent: Optional[str] = None, allowed_domains: Optional[List[str]] = None) -> requests.Response:
    if not is_safe_url(url, allowed_domains):
        raise URLSafetyError(f"URL not allowed: {url}")
    
    timeout = timeout or config.REQUEST_TIMEOUT
    delay = delay or config.REQUEST_DELAY
    user_agent = user_agent or "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    
    time.sleep(delay)
    
    headers = {"User-Agent": user_agent}
    
    try:
        response = requests.get(url, timeout=timeout, headers=headers, allow_redirects=True)
        response.raise_for_status()
        
        final_url = response.url
        if not is_safe_url(final_url, allowed_domains):
            raise URLSafetyError(f"Redirected to unsafe URL: {final_url}")
        
        return response
    except requests.exceptions.Timeout:
        raise ScraperError(f"Request timeout for {url}")
    except requests.exceptions.ConnectionError as e:
        raise ScraperError(f"Connection error for {url}: {e}")
    except requests.exceptions.HTTPError as e:
        raise ScraperError(f"HTTP error for {url}: {e}")
    except requests.exceptions.RequestException as e:
        raise ScraperError(f"Request failed for {url}: {e}")


def parse_html(html: str, url: str) -> BeautifulSoup:
    return BeautifulSoup(html, "html.parser")


def extract_json_ld(soup: BeautifulSoup) -> List[Dict[str, Any]]:
    json_ld_data = []
    scripts = soup.find_all("script", type="application/ld+json")
    for script in scripts:
        try:
            import json
            data = json.loads(script.string)
            if isinstance(data, list):
                json_ld_data.extend(data)
            else:
                json_ld_data.append(data)
        except (json.JSONDecodeError, TypeError):
            continue
    return json_ld_data


def extract_metadata(soup: BeautifulSoup) -> Dict[str, Optional[str]]:
    metadata = {
        "og_title": None,
        "og_description": None,
        "og_image": None,
        "og_url": None,
        "og_type": None,
        "twitter_card": None,
        "twitter_title": None,
        "twitter_description": None,
        "twitter_image": None,
        "canonical_url": None,
        "description": None,
        "keywords": None,
    }
    
    for meta in soup.find_all("meta"):
        prop = meta.get("property") or meta.get("name")
        content = meta.get("content")
        
        if not prop or not content:
            continue
        
        prop = prop.lower()
        
        if prop == "og:title":
            metadata["og_title"] = content
        elif prop == "og:description":
            metadata["og_description"] = content
        elif prop == "og:image":
            metadata["og_image"] = content
        elif prop == "og:url":
            metadata["og_url"] = content
        elif prop == "og:type":
            metadata["og_type"] = content
        elif prop == "twitter:card":
            metadata["twitter_card"] = content
        elif prop == "twitter:title":
            metadata["twitter_title"] = content
        elif prop == "twitter:description":
            metadata["twitter_description"] = content
        elif prop == "twitter:image":
            metadata["twitter_image"] = content
        elif prop == "description":
            metadata["description"] = content
        elif prop == "keywords":
            metadata["keywords"] = content
    
    canonical = soup.find("link", rel="canonical")
    if canonical and canonical.get("href"):
        metadata["canonical_url"] = canonical["href"]
    
    return metadata


def normalize_url(url: Optional[str], base_url: str) -> Optional[str]:
    if not url:
        return None
    return urljoin(base_url, url)


def extract_product_data(page_data: Dict[str, Any], profile: Any) -> List[Dict[str, Any]]:
    products = []
    
    json_ld_list = page_data.get("json_ld", [])
    metadata = page_data.get("metadata", {})
    source_url = page_data.get("source_url", "")
    source_name = page_data.get("source_name", "")
    
    for item in json_ld_list:
        product_type = item.get("@type") or item.get("type")
        if not product_type:
            continue
        
        product_type_lower = str(product_type).lower()
        
        if profile.DATASET_NAME == "granit" and "product" in product_type_lower:
            product = extract_granit_product(item, metadata, source_url, source_name)
            if product:
                products.append(product)
        elif profile.DATASET_NAME == "blinkit" and "product" in product_type_lower:
            product = extract_blinkit_product(item, metadata, source_url, source_name)
            if product:
                products.append(product)
    
    return products


def extract_granit_product(item: Dict[str, Any], metadata: Dict[str, Any], 
                           source_url: str, source_name: str) -> Optional[Dict[str, Any]]:
    product = {
        "source": "granit",
        "source_url": source_url,
        "source_name": source_name,
        "collected_at": datetime.utcnow().isoformat() + "Z",
        "article_number": None,
        "product_name": None,
        "description": None,
        "manufacturer": None,
        "brand": None,
        "supplier": None,
        "category": None,
        "subcategory": None,
        "product_type": None,
        "ean_gtin": None,
        "product_url": None,
        "image_url": None,
        "regional_pricing": [],
        "specifications": [],
        "compliance": [],
        "inventory": [],
    }
    
    product["product_name"] = item.get("name") or metadata.get("og_title")
    product["description"] = item.get("description") or metadata.get("og_description")
    product["product_url"] = item.get("url") or metadata.get("og_url") or metadata.get("canonical_url") or source_url
    product["image_url"] = item.get("image") or metadata.get("og_image") or metadata.get("twitter_image")
    
    sku = item.get("sku")
    if sku:
        product["article_number"] = str(sku)
    
    gtin = item.get("gtin") or item.get("gtin13") or item.get("gtin14") or item.get("ean")
    if gtin:
        product["ean_gtin"] = str(gtin)
    
    brand = item.get("brand")
    if isinstance(brand, dict):
        product["brand"] = brand.get("name")
    elif isinstance(brand, str):
        product["brand"] = brand
    
    manufacturer = item.get("manufacturer")
    if isinstance(manufacturer, dict):
        product["manufacturer"] = manufacturer.get("name")
    elif isinstance(manufacturer, str):
        product["manufacturer"] = manufacturer
    
    category = item.get("category")
    if isinstance(category, str):
        product["category"] = category
    
    offers = item.get("offers")
    if offers:
        if isinstance(offers, list):
            for offer in offers:
                pricing = extract_granit_pricing(offer)
                if pricing:
                    product["regional_pricing"].append(pricing)
        else:
            pricing = extract_granit_pricing(offers)
            if pricing:
                product["regional_pricing"].append(pricing)
    
    return product


def extract_granit_pricing(offer: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    pricing = {
        "country": None,
        "country_code": None,
        "currency": None,
        "net_price": None,
        "vat_rate": None,
        "gross_price": None,
        "price_source": "json_ld",
        "effective_date": None,
    }
    
    price = offer.get("price")
    if price is not None:
        try:
            pricing["net_price"] = Decimal(str(price))
        except:
            pricing["net_price"] = None
    
    price_currency = offer.get("priceCurrency")
    if price_currency:
        pricing["currency"] = price_currency
    
    availability = offer.get("availability")
    if availability:
        pricing["price_source"] = str(availability)
    
    vat = offer.get("vatRate") or offer.get("taxRate")
    if vat is not None:
        try:
            pricing["vat_rate"] = Decimal(str(vat))
        except:
            pricing["vat_rate"] = None
    
    return pricing


def extract_blinkit_product(item: Dict[str, Any], metadata: Dict[str, Any],
                            source_url: str, source_name: str) -> Optional[Dict[str, Any]]:
    product = {
        "source": "blinkit",
        "source_url": source_url,
        "source_name": source_name,
        "collected_at": datetime.utcnow().isoformat() + "Z",
        "product_id": None,
        "sku": None,
        "product_name": None,
        "brand": None,
        "category": None,
        "subcategory": None,
        "product_description": None,
        "barcode": None,
        "product_url": None,
        "image_url": None,
        "pricing": [],
        "packaging": [],
        "supplier": [],
        "inventory": [],
        "delivery": [],
    }
    
    product["product_name"] = item.get("name") or metadata.get("og_title")
    product["product_description"] = item.get("description") or metadata.get("og_description")
    product["product_url"] = item.get("url") or metadata.get("og_url") or metadata.get("canonical_url") or source_url
    product["image_url"] = item.get("image") or metadata.get("og_image") or metadata.get("twitter_image")
    
    sku = item.get("sku")
    if sku:
        product["sku"] = str(sku)
        product["product_id"] = str(sku)
    
    gtin = item.get("gtin") or item.get("gtin13") or item.get("gtin14") or item.get("barcode")
    if gtin:
        product["barcode"] = str(gtin)
    
    brand = item.get("brand")
    if isinstance(brand, dict):
        product["brand"] = brand.get("name")
    elif isinstance(brand, str):
        product["brand"] = brand
    
    category = item.get("category")
    if isinstance(category, str):
        product["category"] = category
    
    offers = item.get("offers")
    if offers:
        if isinstance(offers, list):
            for offer in offers:
                pricing = extract_blinkit_pricing(offer)
                if pricing:
                    product["pricing"].append(pricing)
        else:
            pricing = extract_blinkit_pricing(offers)
            if pricing:
                product["pricing"].append(pricing)
    
    return product


def extract_blinkit_pricing(offer: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    pricing = {
        "mrp": None,
        "selling_price": None,
        "discount_amount": None,
        "discount_percentage": None,
        "gst_rate": None,
        "hsn_code": None,
        "price_source": "json_ld",
        "effective_date": None,
    }
    
    price = offer.get("price")
    if price is not None:
        try:
            pricing["selling_price"] = Decimal(str(price))
        except:
            pricing["selling_price"] = None
    
    high_price = offer.get("highPrice") or offer.get("priceValidUntil")
    if high_price is not None:
        try:
            pricing["mrp"] = Decimal(str(high_price))
        except:
            pricing["mrp"] = None
    
    return pricing


def scrape_products(source_config: Dict[str, Any], profile: Any, max_records: int = 100) -> List[Dict[str, Any]]:
    all_products = []
    
    if not source_config.get("enabled", False):
        return all_products
    
    allowed_domains = source_config.get("allowed_domains", [])
    base_urls = source_config.get("base_urls", [])
    pagination = source_config.get("pagination", {})
    
    for base_url in base_urls:
        if len(all_products) >= max_records:
            break
        
        url = base_url
        page_count = 0
        max_pages = pagination.get("max_pages", 10)
        
        while url and page_count < max_pages and len(all_products) < max_records:
            try:
                response = fetch_page(url, allowed_domains=allowed_domains)
                soup = parse_html(response.text, url)
                
                json_ld = extract_json_ld(soup)
                metadata = extract_metadata(soup)
                
                page_data = {
                    "json_ld": json_ld,
                    "metadata": metadata,
                    "source_url": response.url,
                    "source_name": source_config.get("name", "unknown"),
                }
                
                products = extract_product_data(page_data, profile)
                all_products.extend(products)
                
                page_count += 1
                
                if pagination.get("enabled", False) and page_count < max_pages:
                    next_url = extract_next_page(soup, url, pagination)
                    if next_url and is_safe_url(next_url, allowed_domains):
                        url = next_url
                    else:
                        break
                else:
                    break
                    
            except (ScraperError, URLSafetyError) as e:
                break
    
    return all_products[:max_records]


def extract_next_page(soup: BeautifulSoup, current_url: str, pagination: Dict[str, Any]) -> Optional[str]:
    selector = pagination.get("next_selector")
    if not selector:
        return None
    
    next_link = soup.select_one(selector)
    if next_link and next_link.get("href"):
        return normalize_url(next_link["href"], current_url)
    
    return None