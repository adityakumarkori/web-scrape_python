import os
import pytest
from unittest.mock import patch, MagicMock
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError


def test_connect_db_success():
    with patch("database.MongoClient") as mock_client:
        mock_instance = MagicMock()
        mock_client.return_value = mock_instance
        mock_instance.admin.command.return_value = {"ok": 1}
        
        import database
        client = database.connect_db()
        assert client == mock_instance
        mock_instance.admin.command.assert_called_once_with("ping")


def test_connect_db_failure():
    with patch("database.MongoClient") as mock_client:
        mock_client.side_effect = ConnectionFailure("Connection failed")
        
        import database
        # Reset the global _client to ensure fresh connection attempt
        database._client = None
        with pytest.raises(ConnectionError) as exc:
            database.connect_db()
        assert "Failed to connect to MongoDB" in str(exc.value)


def test_check_connection_success():
    import database
    with patch("database.connect_db") as mock_connect:
        mock_client = MagicMock()
        mock_client.admin.command.return_value = {"ok": 1}
        mock_connect.return_value = mock_client
        
        connected, msg = database.check_connection()
        assert connected is True
        assert msg == "Connected"


def test_check_connection_failure():
    import database
    with patch("database.connect_db") as mock_connect:
        mock_connect.side_effect = ConnectionError("Connection failed")
        
        connected, msg = database.check_connection()
        assert connected is False
        assert "Connection failed" in msg


def test_close_db():
    with patch("database.MongoClient") as mock_client:
        mock_instance = MagicMock()
        mock_client.return_value = mock_instance
        mock_instance.admin.command.return_value = {"ok": 1}
        
        import database
        # Reset the global _client
        database._client = None
        database.connect_db()
        database.close_db()
        mock_instance.close.assert_called_once()


def test_get_database():
    with patch("database.MongoClient") as mock_client:
        mock_instance = MagicMock()
        mock_client.return_value = mock_instance
        mock_instance.admin.command.return_value = {"ok": 1}
        mock_db = MagicMock()
        mock_instance.__getitem__.return_value = mock_db
        
        import database
        import config
        db = database.get_database()
        assert db == mock_db
        mock_instance.__getitem__.assert_called_once_with(config.MONGODB_DATABASE)