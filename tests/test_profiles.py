import pytest
from profiles import get_profile, PROFILES
import profiles.granit as granit
import profiles.blinkit as blinkit


def test_granit_profile_fields():
    assert granit.DATASET_NAME == "granit"
    assert granit.DISPLAY_NAME == "GRANIT Parts - EU Region"
    assert granit.COLLECTION_NAME == "granit_products"
    assert isinstance(granit.PRODUCT_FIELDS, list)
    assert len(granit.PRODUCT_FIELDS) == 12
    assert "article_number" in granit.PRODUCT_FIELDS
    assert "product_name" in granit.PRODUCT_FIELDS


def test_blinkit_profile_fields():
    assert blinkit.DATASET_NAME == "blinkit"
    assert blinkit.DISPLAY_NAME == "Blinkit - Bengaluru"
    assert blinkit.COLLECTION_NAME == "blinkit_products"
    assert isinstance(blinkit.PRODUCT_FIELDS, list)
    assert len(blinkit.PRODUCT_FIELDS) == 10
    assert "product_id" in blinkit.PRODUCT_FIELDS
    assert "sku" in blinkit.PRODUCT_FIELDS


def test_collection_names():
    assert granit.COLLECTION_NAME == "granit_products"
    assert blinkit.COLLECTION_NAME == "blinkit_products"
    assert granit.COLLECTION_NAME != blinkit.COLLECTION_NAME


def test_profile_separation():
    granit_fields = set(granit.PRODUCT_FIELDS)
    blinkit_fields = set(blinkit.PRODUCT_FIELDS)
    assert granit_fields != blinkit_fields
    assert "article_number" in granit_fields
    assert "article_number" not in blinkit_fields
    assert "product_id" in blinkit_fields
    assert "product_id" not in granit_fields


def test_get_profile_granit():
    profile = get_profile("granit")
    assert profile is not None
    assert profile.DATASET_NAME == "granit"


def test_get_profile_blinkit():
    profile = get_profile("blinkit")
    assert profile is not None
    assert profile.DATASET_NAME == "blinkit"


def test_get_profile_invalid():
    profile = get_profile("invalid")
    assert profile is None


def test_profiles_dict():
    assert "granit" in PROFILES
    assert "blinkit" in PROFILES
    assert len(PROFILES) == 2