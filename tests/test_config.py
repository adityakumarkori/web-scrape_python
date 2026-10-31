import os
import pytest
from unittest.mock import patch, MagicMock


def test_config_loads():
    with patch.dict(os.environ, {
        "MONGODB_URI": "mongodb://localhost:27017/",
        "MONGODB_DATABASE": "granit_blinkit_data",
        "REQUEST_TIMEOUT": "20",
        "REQUEST_DELAY": "2",
        "MAX_RECORDS": "100"
    }, clear=True):
        with patch("config.load_dotenv"):
            import importlib
            import config
            importlib.reload(config)
            config.reload_config()
            assert config.MONGODB_URI == "mongodb://localhost:27017/"
            assert config.MONGODB_DATABASE == "granit_blinkit_data"
            assert config.REQUEST_TIMEOUT == 20
            assert config.REQUEST_DELAY == 2.0
            assert config.MAX_RECORDS == 100


def test_missing_mongodb_uri():
    # Test validate function directly with MONGODB_URI not set
    import config
    # Save original
    orig_uri = os.environ.get("MONGODB_URI")
    # Remove from env
    if "MONGODB_URI" in os.environ:
        del os.environ["MONGODB_URI"]
    try:
        with pytest.raises(ValueError) as exc:
            config.validate()
        assert "MONGODB_URI" in str(exc.value)
    finally:
        if orig_uri:
            os.environ["MONGODB_URI"] = orig_uri


def test_config_defaults():
    with patch.dict(os.environ, {"MONGODB_URI": "mongodb://test:27017/"}, clear=True):
        with patch("config.load_dotenv"):
            import importlib
            import config
            importlib.reload(config)
            config.reload_config()
            assert config.MONGODB_DATABASE == "granit_blinkit_data"
            assert config.REQUEST_TIMEOUT == 20
            assert config.REQUEST_DELAY == 2.0
            assert config.MAX_RECORDS == 100