import pytest
from unittest.mock import patch, MagicMock
from bs4 import BeautifulSoup
import requests

import scraper
import profiles.granit as granit_profile
import profiles.blinkit as blinkit_profile


SAMPLE_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Test Product</title>
    <meta property="og:title" content="Test Product Title">
    <meta property="og:description" content="Test product description">
    <meta property="og:image" content="https://example.com/image.jpg">
    <meta property="og:url" content="https://example.com/product/123">
    <meta property="og:type" content="product">
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:title" content="Twitter Title">
    <meta name="twitter:description" content="Twitter description">
    <meta name="twitter:image" content="https://example.com/twitter.jpg">
    <meta name="description" content="Page description">
    <meta name="keywords" content="test, product">
    <link rel="canonical" href="https://example.com/product/123">
    <script type="application/ld+json">
    {
        "@context": "https://schema.org/",
        "@type": "Product",
        "name": "Test Product",
        "description": "A test product",
        "sku": "ART-12345",
        "gtin13": "4000000000001",
        "brand": {"@type": "Brand", "name": "TestBrand"},
        "manufacturer": {"@type": "Organization", "name": "TestMfg"},
        "category": "Auto Parts",
        "image": "https://example.com/product.jpg",
        "offers": {
            "@type": "Offer",
            "price": "29.99",
            "priceCurrency": "EUR",
            "availability": "https://schema.org/InStock"
        }
    }
    </script>
</head>
<body>
    <h1>Test Product</h1>
    <a class="next-page" href="/products?page=2">Next</a>
</body>
</html>
"""

SAMPLE_HTML_BLINKIT = """
<!DOCTYPE html>
<html>
<head>
    <title>Blinkit Product</title>
    <meta property="og:title" content="Organic Apples 1kg">
    <meta property="og:description" content="Fresh organic apples">
    <meta property="og:image" content="https://blinkit.com/apples.jpg">
    <meta property="og:url" content="https://blinkit.com/product/apples-1kg">
    <script type="application/ld+json">
    {
        "@context": "https://schema.org/",
        "@type": "Product",
        "name": "Organic Apples 1kg",
        "description": "Fresh organic apples from local farms",
        "sku": "APL-001",
        "gtin13": "8901234567890",
        "brand": {"@type": "Brand", "name": "FarmFresh"},
        "category": "Fruits",
        "image": "https://blinkit.com/apples.jpg",
        "offers": {
            "@type": "Offer",
            "price": "120.00",
            "priceCurrency": "INR",
            "highPrice": "150.00",
            "availability": "https://schema.org/InStock"
        }
    }
    </script>
</head>
<body>
    <h1>Organic Apples 1kg</h1>
</body>
</html>
"""

HTML_NO_JSON_LD = """
<!DOCTYPE html>
<html>
<head>
    <title>No JSON-LD</title>
    <meta property="og:title" content="Product Without JSON-LD">
</head>
<body>
    <h1>Product Without JSON-LD</h1>
    <a class="next-page" href="/products?page=2">Next</a>
</body>
</html>
"""

HTML_MULTIPLE_PRODUCTS = """
<!DOCTYPE html>
<html>
<head>
    <script type="application/ld+json">
    [
        {
            "@type": "Product",
            "name": "Product 1",
            "sku": "SKU-001",
            "offers": {"@type": "Offer", "price": "10.00", "priceCurrency": "EUR"}
        },
        {
            "@type": "Product",
            "name": "Product 2",
            "sku": "SKU-002",
            "offers": {"@type": "Offer", "price": "20.00", "priceCurrency": "EUR"}
        }
    ]
    </script>
</head>
<body></body>
</html>
"""


class TestURLSafety:
    def test_safe_https_url(self):
        assert scraper.is_safe_url("https://example.com/product") is True
    
    def test_safe_http_url(self):
        assert scraper.is_safe_url("http://example.com/product") is True
    
    def test_unsafe_ftp_url(self):
        assert scraper.is_safe_url("ftp://example.com/file") is False
    
    def test_unsafe_localhost(self):
        assert scraper.is_safe_url("http://localhost:8080") is False
        assert scraper.is_safe_url("http://127.0.0.1") is False
        assert scraper.is_safe_url("http://[::1]") is False
    
    def test_unsafe_private_ip(self):
        assert scraper.is_safe_url("http://192.168.1.1") is False
        assert scraper.is_safe_url("http://10.0.0.1") is False
        assert scraper.is_safe_url("http://172.16.0.1") is False
    
    def test_unsafe_link_local(self):
        assert scraper.is_safe_url("http://169.254.1.1") is False
    
    def test_allowed_domains(self):
        assert scraper.is_safe_url("https://example.com", ["example.com"]) is True
        assert scraper.is_safe_url("https://sub.example.com", ["example.com"]) is True
        assert scraper.is_safe_url("https://other.com", ["example.com"]) is False


class TestFetchPage:
    @patch("scraper.requests.get")
    def test_fetch_page_success(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = SAMPLE_HTML
        mock_response.url = "https://example.com/product"
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response
        
        response = scraper.fetch_page("https://example.com/product", allowed_domains=["example.com"])
        assert response.status_code == 200
        mock_get.assert_called_once()
    
    @patch("scraper.requests.get")
    def test_fetch_page_timeout(self, mock_get):
        mock_get.side_effect = requests.exceptions.Timeout()
        
        with pytest.raises(scraper.ScraperError) as exc:
            scraper.fetch_page("https://example.com/product")
        assert "timeout" in str(exc.value).lower()
    
    @patch("scraper.requests.get")
    def test_fetch_page_connection_error(self, mock_get):
        mock_get.side_effect = requests.exceptions.ConnectionError("Connection refused")
        
        with pytest.raises(scraper.ScraperError) as exc:
            scraper.fetch_page("https://example.com/product")
        assert "connection" in str(exc.value).lower()
    
    @patch("scraper.requests.get")
    def test_fetch_page_http_error(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("404 Not Found")
        mock_get.return_value = mock_response
        
        with pytest.raises(scraper.ScraperError) as exc:
            scraper.fetch_page("https://example.com/product")
        assert "http" in str(exc.value).lower()
    
    def test_fetch_page_unsafe_url(self):
        with pytest.raises(scraper.URLSafetyError):
            scraper.fetch_page("http://localhost:8080")
    
    @patch("scraper.requests.get")
    def test_fetch_page_redirect_to_unsafe(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = SAMPLE_HTML
        mock_response.url = "http://192.168.1.1/admin"
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response
        
        with pytest.raises(scraper.URLSafetyError):
            scraper.fetch_page("https://example.com/product", allowed_domains=["example.com"])


class TestParseHTML:
    def test_parse_html(self):
        soup = scraper.parse_html(SAMPLE_HTML, "https://example.com")
        assert isinstance(soup, BeautifulSoup)
        assert soup.title.string == "Test Product"
    
    def test_parse_html_empty(self):
        soup = scraper.parse_html("", "https://example.com")
        assert isinstance(soup, BeautifulSoup)


class TestExtractJSONLD:
    def test_extract_json_ld_single(self):
        soup = scraper.parse_html(SAMPLE_HTML, "https://example.com")
        json_ld = scraper.extract_json_ld(soup)
        assert len(json_ld) == 1
        assert json_ld[0]["@type"] == "Product"
        assert json_ld[0]["name"] == "Test Product"
    
    def test_extract_json_ld_multiple(self):
        soup = scraper.parse_html(HTML_MULTIPLE_PRODUCTS, "https://example.com")
        json_ld = scraper.extract_json_ld(soup)
        assert len(json_ld) == 2
        assert json_ld[0]["sku"] == "SKU-001"
        assert json_ld[1]["sku"] == "SKU-002"
    
    def test_extract_json_ld_none(self):
        soup = scraper.parse_html(HTML_NO_JSON_LD, "https://example.com")
        json_ld = scraper.extract_json_ld(soup)
        assert json_ld == []
    
    def test_extract_json_ld_invalid(self):
        html = '<script type="application/ld+json">{invalid json}</script>'
        soup = scraper.parse_html(html, "https://example.com")
        json_ld = scraper.extract_json_ld(soup)
        assert json_ld == []


class TestExtractMetadata:
    def test_extract_metadata_full(self):
        soup = scraper.parse_html(SAMPLE_HTML, "https://example.com")
        metadata = scraper.extract_metadata(soup)
        
        assert metadata["og_title"] == "Test Product Title"
        assert metadata["og_description"] == "Test product description"
        assert metadata["og_image"] == "https://example.com/image.jpg"
        assert metadata["og_url"] == "https://example.com/product/123"
        assert metadata["og_type"] == "product"
        assert metadata["twitter_card"] == "summary_large_image"
        assert metadata["twitter_title"] == "Twitter Title"
        assert metadata["twitter_description"] == "Twitter description"
        assert metadata["twitter_image"] == "https://example.com/twitter.jpg"
        assert metadata["canonical_url"] == "https://example.com/product/123"
        assert metadata["description"] == "Page description"
        assert metadata["keywords"] == "test, product"
    
    def test_extract_metadata_minimal(self):
        soup = scraper.parse_html(HTML_NO_JSON_LD, "https://example.com")
        metadata = scraper.extract_metadata(soup)
        
        assert metadata["og_title"] == "Product Without JSON-LD"
        assert metadata["canonical_url"] is None


class TestExtractProductData:
    def test_extract_granit_product(self):
        soup = scraper.parse_html(SAMPLE_HTML, "https://example.com")
        json_ld = scraper.extract_json_ld(soup)
        metadata = scraper.extract_metadata(soup)
        
        page_data = {
            "json_ld": json_ld,
            "metadata": metadata,
            "source_url": "https://example.com/product/123",
            "source_name": "granit_catalog",
        }
        
        products = scraper.extract_product_data(page_data, granit_profile)
        assert len(products) == 1
        product = products[0]
        
        assert product["source"] == "granit"
        assert product["article_number"] == "ART-12345"
        assert product["product_name"] == "Test Product"
        assert product["description"] == "A test product"
        assert product["brand"] == "TestBrand"
        assert product["manufacturer"] == "TestMfg"
        assert product["category"] == "Auto Parts"
        assert product["ean_gtin"] == "4000000000001"
        assert product["product_url"] == "https://example.com/product/123"
        assert product["image_url"] == "https://example.com/product.jpg"
        assert len(product["regional_pricing"]) == 1
        pricing = product["regional_pricing"][0]
        assert float(pricing["net_price"]) == 29.99
        assert pricing["currency"] == "EUR"
        assert pricing["price_source"] == "https://schema.org/InStock"
    
    def test_extract_blinkit_product(self):
        soup = scraper.parse_html(SAMPLE_HTML_BLINKIT, "https://blinkit.com")
        json_ld = scraper.extract_json_ld(soup)
        metadata = scraper.extract_metadata(soup)
        
        page_data = {
            "json_ld": json_ld,
            "metadata": metadata,
            "source_url": "https://blinkit.com/product/apples-1kg",
            "source_name": "blinkit_grocery",
        }
        
        products = scraper.extract_product_data(page_data, blinkit_profile)
        assert len(products) == 1
        product = products[0]
        
        assert product["source"] == "blinkit"
        assert product["sku"] == "APL-001"
        assert product["product_id"] == "APL-001"
        assert product["product_name"] == "Organic Apples 1kg"
        assert product["brand"] == "FarmFresh"
        assert product["category"] == "Fruits"
        assert product["barcode"] == "8901234567890"
        assert product["product_url"] == "https://blinkit.com/product/apples-1kg"
        assert len(product["pricing"]) == 1
        pricing = product["pricing"][0]
        assert pricing["selling_price"] == 120.00
        assert pricing["mrp"] == 150.00
    
    def test_extract_product_data_no_json_ld(self):
        soup = scraper.parse_html(HTML_NO_JSON_LD, "https://example.com")
        json_ld = scraper.extract_json_ld(soup)
        metadata = scraper.extract_metadata(soup)
        
        page_data = {
            "json_ld": json_ld,
            "metadata": metadata,
            "source_url": "https://example.com/product",
            "source_name": "test",
        }
        
        products = scraper.extract_product_data(page_data, granit_profile)
        assert products == []


class TestScrapeProducts:
    @patch("scraper.fetch_page")
    def test_scrape_products_disabled(self, mock_fetch):
        config = {"enabled": False}
        products = scraper.scrape_products(config, granit_profile)
        assert products == []
        mock_fetch.assert_not_called()
    
    @patch("scraper.fetch_page")
    def test_scrape_products_enabled(self, mock_fetch):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = SAMPLE_HTML
        mock_response.url = "https://granit-parts.com/products"
        mock_response.raise_for_status = MagicMock()
        mock_fetch.return_value = mock_response
        
        config = {
            "enabled": True,
            "allowed_domains": ["granit-parts.com"],
            "base_urls": ["https://granit-parts.com/products"],
            "pagination": {"enabled": False},
        }
        
        products = scraper.scrape_products(config, granit_profile, max_records=10)
        assert len(products) == 1
        assert products[0]["article_number"] == "ART-12345"
    
    @patch("scraper.fetch_page")
    def test_scrape_products_pagination(self, mock_fetch):
        mock_response1 = MagicMock()
        mock_response1.status_code = 200
        mock_response1.text = SAMPLE_HTML
        mock_response1.url = "https://granit-parts.com/products?page=1"
        mock_response1.raise_for_status = MagicMock()
        
        mock_response2 = MagicMock()
        mock_response2.status_code = 200
        mock_response2.text = HTML_NO_JSON_LD
        mock_response2.url = "https://granit-parts.com/products?page=2"
        mock_response2.raise_for_status = MagicMock()
        
        mock_fetch.side_effect = [mock_response1, mock_response2]
        
        config = {
            "enabled": True,
            "allowed_domains": ["granit-parts.com"],
            "base_urls": ["https://granit-parts.com/products"],
            "pagination": {
                "enabled": True,
                "next_selector": "a.next-page",
                "max_pages": 2,
            },
        }
        
        products = scraper.scrape_products(config, granit_profile, max_records=10)
        assert mock_fetch.call_count == 2
    
    @patch("scraper.fetch_page")
    def test_scrape_products_max_records(self, mock_fetch):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = HTML_MULTIPLE_PRODUCTS
        mock_response.url = "https://granit-parts.com/products"
        mock_response.raise_for_status = MagicMock()
        mock_fetch.return_value = mock_response
        
        config = {
            "enabled": True,
            "allowed_domains": ["granit-parts.com"],
            "base_urls": ["https://granit-parts.com/products"],
            "pagination": {"enabled": False},
        }
        
        products = scraper.scrape_products(config, granit_profile, max_records=1)
        assert len(products) == 1


class TestExtractNextPage:
    def test_extract_next_page_found(self):
        html = '<a class="next-page" href="/products?page=2">Next</a>'
        soup = scraper.parse_html(html, "https://example.com/products")
        pagination = {"next_selector": "a.next-page"}
        
        next_url = scraper.extract_next_page(soup, "https://example.com/products", pagination)
        assert next_url == "https://example.com/products?page=2"
    
    def test_extract_next_page_not_found(self):
        html = '<a class="prev-page" href="/products?page=1">Prev</a>'
        soup = scraper.parse_html(html, "https://example.com/products")
        pagination = {"next_selector": "a.next-page"}
        
        next_url = scraper.extract_next_page(soup, "https://example.com/products", pagination)
        assert next_url is None
    
    def test_extract_next_page_no_selector(self):
        soup = scraper.parse_html(SAMPLE_HTML, "https://example.com")
        pagination = {}
        
        next_url = scraper.extract_next_page(soup, "https://example.com", pagination)
        assert next_url is None


class TestNormalizeURL:
    def test_normalize_absolute(self):
        url = scraper.normalize_url("https://example.com/product", "https://example.com")
        assert url == "https://example.com/product"
    
    def test_normalize_relative(self):
        url = scraper.normalize_url("/product/123", "https://example.com")
        assert url == "https://example.com/product/123"
    
    def test_normalize_none(self):
        url = scraper.normalize_url(None, "https://example.com")
        assert url is None