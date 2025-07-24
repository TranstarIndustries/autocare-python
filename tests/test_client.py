"""
Test suite for AutoCare API Client

Comprehensive tests covering:
- Authentication and token management
- Database and table operations
- Record fetching with pagination
- Error handling and validation
- Session management
"""

import pytest
import time
from unittest.mock import patch
from requests.exceptions import ConnectionError, Timeout

from autocare.client import (
    AutoCareAPI,
    AuthenticationError,
    APIConnectionError,
    APIResponseError,
    DataValidationError,
    DatabaseInfo,
    TableInfo,
    APIResponse,
    create_client,
)


class TestAutoCarAPIInitialization:
    """Test API client initialization and configuration."""

    def test_init_with_required_params(self):
        """Test initialization with required parameters."""
        with patch.object(AutoCareAPI, "authenticate", return_value="test-token"):
            client = AutoCareAPI(
                client_id="test-id",
                client_secret="test-secret",
                username="test-user",
                password="test-pass",
            )

            assert client.client_id == "test-id"
            assert client.client_secret == "test-secret"
            assert client.username == "test-user"
            assert client.password == "test-pass"
            assert client.scope == AutoCareAPI.DEFAULT_SCOPE
            assert client.timeout == AutoCareAPI.DEFAULT_TIMEOUT

            client.close()

    def test_init_with_custom_params(self):
        """Test initialization with custom parameters."""
        with patch.object(AutoCareAPI, "authenticate", return_value="test-token"):
            client = AutoCareAPI(
                client_id="test-id",
                client_secret="test-secret",
                username="test-user",
                password="test-pass",
                scope="custom-scope",
                timeout=60,
                max_retries=5,
                base_url="https://custom.api.com",
                auth_url="https://custom.auth.com",
            )

            assert client.scope == "custom-scope"
            assert client.timeout == 60
            assert client.base_url == "https://custom.api.com"
            assert client.auth_url == "https://custom.auth.com"

            client.close()

    def test_session_configuration(self):
        """Test that session is properly configured with retry strategy."""
        with patch.object(AutoCareAPI, "authenticate", return_value="test-token"):
            client = AutoCareAPI("id", "secret", "user", "pass")

            assert client.session is not None
            assert "User-Agent" in client.session.headers
            assert client.session.headers["User-Agent"] == "AutoCare-API-Client/2.0"

            client.close()


class TestAuthentication:
    """Test authentication functionality."""

    def test_successful_authentication(self, requests_mock):
        """Test successful authentication flow."""
        token_response = {
            "access_token": "test-access-token",
            "expires_in": 3600,
            "refresh_token": "test-refresh-token",
        }

        requests_mock.post(AutoCareAPI.AUTH_URL, json=token_response)

        client = AutoCareAPI("id", "secret", "user", "pass")

        assert client.token == "test-access-token"
        assert client.refresh_token == "test-refresh-token"
        assert client.token_expires_at > time.time()

        # Verify request was made with correct data
        request = requests_mock.last_request
        assert "grant_type=password" in request.text
        assert "username=user" in request.text
        assert "password=pass" in request.text

        client.close()

    def test_authentication_failure(self, requests_mock):
        """Test authentication failure handling."""
        requests_mock.post(AutoCareAPI.AUTH_URL, status_code=401, text="Unauthorized")

        with pytest.raises(AuthenticationError, match="Failed to authenticate"):
            AutoCareAPI("id", "secret", "user", "pass")

    def test_authentication_invalid_response(self, requests_mock):
        """Test handling of invalid authentication response."""
        requests_mock.post(AutoCareAPI.AUTH_URL, json={"error": "invalid_grant"})

        with pytest.raises(AuthenticationError, match="missing 'access_token'"):
            AutoCareAPI("id", "secret", "user", "pass")

    def test_token_refresh(self, requests_mock):
        """Test token refresh functionality."""
        # Initial auth response
        initial_token = {
            "access_token": "initial-token",
            "expires_in": 3600,
            "refresh_token": "refresh-token",
        }
        requests_mock.post(AutoCareAPI.AUTH_URL, json=initial_token)

        client = AutoCareAPI("id", "secret", "user", "pass")

        # Setup refresh response
        refresh_response = {
            "access_token": "new-token",
            "expires_in": 3600,
            "refresh_token": "new-refresh-token",
        }
        requests_mock.post(AutoCareAPI.AUTH_URL, json=refresh_response)

        # Force token expiration
        client.token_expires_at = time.time() - 1

        new_token = client.refresh_access_token()

        assert new_token == "new-token"
        assert client.token == "new-token"
        assert client.refresh_token == "new-refresh-token"

        client.close()

    def test_automatic_token_refresh(self, requests_mock):
        """Test automatic token refresh when making requests."""
        # Initial auth
        requests_mock.post(
            AutoCareAPI.AUTH_URL,
            json={
                "access_token": "initial-token",
                "expires_in": 3600,
                "refresh_token": "refresh-token",
            },
        )

        client = AutoCareAPI("id", "secret", "user", "pass")

        # Setup refresh response
        requests_mock.post(
            AutoCareAPI.AUTH_URL,
            json={"access_token": "refreshed-token", "expires_in": 3600},
        )

        # Setup API endpoint
        requests_mock.get(f"{client.base_url}/databases", json=[])

        # Force token to expire soon
        client.token_expires_at = time.time() + 100  # Less than TOKEN_REFRESH_BUFFER

        headers = client._get_headers()

        assert "Authorization" in headers
        assert "refreshed-token" in headers["Authorization"]

        client.close()


class TestDatabaseOperations:
    """Test database-related operations."""

    def setup_method(self):
        """Set up test fixtures."""
        with patch.object(AutoCareAPI, "authenticate", return_value="test-token"):
            self.client = AutoCareAPI("id", "secret", "user", "pass")

    def teardown_method(self):
        """Clean up after tests."""
        self.client.close()

    def test_list_databases_success(self, requests_mock):
        """Test successful database listing."""
        # Mock authentication
        requests_mock.post(
            AutoCareAPI.AUTH_URL,
            json={"access_token": "test-token", "expires_in": 3600},
        )

        mock_databases = [
            {
                "databaseName": "vcdb",
                "version": "2.0",
                "description": "Vehicle Database",
            },
            {
                "databaseName": "pcdb",
                "version": "2.0",
                "description": "Product Database",
            },
            "qdb",  # Test string format as well
        ]

        requests_mock.get(f"{self.client.base_url}/databases", json=mock_databases)

        databases = self.client.list_databases()

        assert len(databases) == 3
        assert databases[0].name == "vcdb"
        assert databases[0].version == "2.0"
        assert databases[0].description == "Vehicle Database"
        assert databases[2].name == "qdb"
        assert databases[2].version == ""

    def test_list_databases_failure(self, requests_mock):
        """Test database listing failure."""
        # Mock authentication
        requests_mock.post(
            AutoCareAPI.AUTH_URL,
            json={"access_token": "test-token", "expires_in": 3600},
        )

        requests_mock.get(
            f"{self.client.base_url}/databases", status_code=500, text="Server Error"
        )

        with pytest.raises(APIResponseError, match="Failed to list databases"):
            self.client.list_databases()

    def test_list_tables_success(self, requests_mock):
        """Test successful table listing."""
        # Mock authentication
        requests_mock.post(
            AutoCareAPI.AUTH_URL,
            json={"access_token": "test-token", "expires_in": 3600},
        )

        mock_tables = [
            {
                "TableName": "Vehicle",
                "recordCount": 1000,
                "columns": ["VehicleID", "Year"],
            },
            {"TableName": "Make", "recordCount": 50},
            "Model",  # Test string format
        ]

        requests_mock.get(
            f"{self.client.base_url}/databases/vcdb/tables", json=mock_tables
        )

        tables = self.client.list_tables("vcdb")

        assert len(tables) == 3
        assert tables[0].name == "Vehicle"
        assert tables[0].database == "vcdb"
        assert tables[0].record_count == 1000
        assert tables[0].columns == ["VehicleID", "Year"]
        assert tables[2].name == "Model"
        assert tables[2].database == "vcdb"

    def test_list_tables_empty_db_name(self):
        """Test table listing with empty database name."""
        with pytest.raises(DataValidationError, match="Database name is required"):
            self.client.list_tables("")

    def test_get_table_info(self, requests_mock):
        """Test getting specific table information."""
        # Mock authentication
        requests_mock.post(
            AutoCareAPI.AUTH_URL,
            json={"access_token": "test-token", "expires_in": 3600},
        )

        mock_tables = [
            {"TableName": "Vehicle", "recordCount": 1000},
            {"TableName": "Make", "recordCount": 50},
        ]

        requests_mock.get(
            f"{self.client.base_url}/databases/vcdb/tables", json=mock_tables
        )

        table_info = self.client.get_table_info("vcdb", "Vehicle")

        assert table_info is not None
        assert table_info.name == "Vehicle"
        assert table_info.record_count == 1000

        # Test non-existent table
        non_existent = self.client.get_table_info("vcdb", "NonExistent")
        assert non_existent is None


class TestRecordFetching:
    """Test record fetching functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        with patch.object(AutoCareAPI, "authenticate", return_value="test-token"):
            self.client = AutoCareAPI("id", "secret", "user", "pass")

    def teardown_method(self):
        """Clean up after tests."""
        self.client.close()

    def test_fetch_records_single_page(self, requests_mock):
        """Test fetching records from a single page."""
        # Mock authentication
        requests_mock.post(
            AutoCareAPI.AUTH_URL,
            json={"access_token": "test-token", "expires_in": 3600},
        )

        mock_records = [
            {"VehicleID": 1, "Year": 2020, "Make": "Toyota"},
            {"VehicleID": 2, "Year": 2021, "Make": "Honda"},
        ]

        requests_mock.get(
            "https://vcdb.autocarevip.com/api/v1.0/vcdb/Vehicle", json=mock_records
        )

        records = list(self.client.fetch_records("vcdb", "Vehicle"))

        assert len(records) == 2
        assert records[0]["VehicleID"] == 1
        assert records[1]["Make"] == "Honda"

    def test_fetch_records_with_pagination(self, requests_mock):
        """Test fetching records with pagination."""
        # Mock authentication
        requests_mock.post(
            AutoCareAPI.AUTH_URL,
            json={"access_token": "test-token", "expires_in": 3600},
        )

        # First page
        page1_records = [{"VehicleID": 1}, {"VehicleID": 2}]
        page1_headers = {
            "X-Pagination": '{"nextPageLink": "https://vcdb.autocarevip.com/api/v1.0/vcdb/Vehicle?page=2"}'
        }

        # Second page
        page2_records = [{"VehicleID": 3}, {"VehicleID": 4}]

        requests_mock.get(
            "https://vcdb.autocarevip.com/api/v1.0/vcdb/Vehicle",
            json=page1_records,
            headers=page1_headers,
        )
        requests_mock.get(
            "https://vcdb.autocarevip.com/api/v1.0/vcdb/Vehicle?page=2",
            json=page2_records,
        )

        records = list(self.client.fetch_records("vcdb", "Vehicle"))

        assert len(records) == 4
        assert records[0]["VehicleID"] == 1
        assert records[3]["VehicleID"] == 4

    def test_fetch_records_with_limit(self, requests_mock):
        """Test fetching records with a limit."""
        # Mock authentication
        requests_mock.post(
            AutoCareAPI.AUTH_URL,
            json={"access_token": "test-token", "expires_in": 3600},
        )

        mock_records = [{"VehicleID": i} for i in range(1, 6)]  # 5 records

        requests_mock.get(
            "https://vcdb.autocarevip.com/api/v1.0/vcdb/Vehicle", json=mock_records
        )

        records = list(self.client.fetch_records("vcdb", "Vehicle", limit=3))

        assert len(records) == 3
        assert records[2]["VehicleID"] == 3

    def test_fetch_records_invalid_params(self):
        """Test fetch records with invalid parameters."""
        with pytest.raises(
            DataValidationError, match="Database name and table name are required"
        ):
            list(self.client.fetch_records("", "Vehicle"))

        with pytest.raises(
            DataValidationError, match="Database name and table name are required"
        ):
            list(self.client.fetch_records("vcdb", ""))

    def test_fetch_all_records(self, requests_mock):
        """Test fetching all records as a list."""
        # Mock authentication
        requests_mock.post(
            AutoCareAPI.AUTH_URL,
            json={"access_token": "test-token", "expires_in": 3600},
        )

        mock_records = [{"VehicleID": 1}, {"VehicleID": 2}]

        requests_mock.get(
            "https://vcdb.autocarevip.com/api/v1.0/vcdb/Vehicle", json=mock_records
        )

        records = self.client.fetch_all_records("vcdb", "Vehicle")

        assert isinstance(records, list)
        assert len(records) == 2
        assert records[0]["VehicleID"] == 1


class TestErrorHandling:
    """Test error handling scenarios."""

    def setup_method(self):
        """Set up test fixtures."""
        with patch.object(AutoCareAPI, "authenticate", return_value="test-token"):
            self.client = AutoCareAPI("id", "secret", "user", "pass")

    def teardown_method(self):
        """Clean up after tests."""
        self.client.close()

    def test_api_error_with_json_response(self, requests_mock):
        """Test API error with JSON error response."""
        # Mock authentication
        requests_mock.post(
            AutoCareAPI.AUTH_URL,
            json={"access_token": "test-token", "expires_in": 3600},
        )

        error_response = {"error": "Invalid database name", "code": "DB001"}
        requests_mock.get(
            f"{self.client.base_url}/databases/invalid",
            json=error_response,
            status_code=404,
        )

        response = self.client._make_request(
            "GET", f"{self.client.base_url}/databases/invalid"
        )

        assert response.success is False
        assert response.error == "Invalid database name"
        assert response.status_code == 404

    def test_api_error_with_text_response(self, requests_mock):
        """Test API error with text error response."""
        # Mock authentication
        requests_mock.post(
            AutoCareAPI.AUTH_URL,
            json={"access_token": "test-token", "expires_in": 3600},
        )

        requests_mock.get(
            f"{self.client.base_url}/databases", text="Server Error", status_code=500
        )

        response = self.client._make_request("GET", f"{self.client.base_url}/databases")

        assert response.success is False
        assert response.error == "Server Error"
        assert response.status_code == 500

    @patch("autocare.client.requests.Session.request")
    def test_connection_timeout(self, mock_request):
        """Test handling of connection timeout."""
        # Set up client with valid token to avoid authentication during test
        self.client.token = "test-token"
        self.client.token_expires_at = time.time() + 3600  # Token valid for 1 hour

        mock_request.side_effect = Timeout("Request timed out")

        with pytest.raises(APIConnectionError, match="Request timed out"):
            self.client._make_request("GET", f"{self.client.base_url}/databases")

    @patch("autocare.client.requests.Session.request")
    def test_connection_error(self, mock_request):
        """Test handling of connection error."""
        # Set up client with valid token to avoid authentication during test
        self.client.token = "test-token"
        self.client.token_expires_at = time.time() + 3600  # Token valid for 1 hour

        mock_request.side_effect = ConnectionError("Failed to connect")

        with pytest.raises(APIConnectionError, match="Failed to connect to API"):
            self.client._make_request("GET", f"{self.client.base_url}/databases")


class TestUtilityMethods:
    """Test utility and helper methods."""

    def setup_method(self):
        """Set up test fixtures."""
        with patch.object(AutoCareAPI, "authenticate", return_value="test-token"):
            self.client = AutoCareAPI("id", "secret", "user", "pass")

    def teardown_method(self):
        """Clean up after tests."""
        self.client.close()

    def test_validate_credentials_success(self, requests_mock):
        """Test successful credential validation."""
        # Mock authentication
        requests_mock.post(
            AutoCareAPI.AUTH_URL,
            json={"access_token": "test-token", "expires_in": 3600},
        )

        requests_mock.get(f"{self.client.base_url}/databases", json=[])

        assert self.client.validate_credentials() is True

    def test_validate_credentials_failure(self, requests_mock):
        """Test failed credential validation."""
        # Mock authentication
        requests_mock.post(
            AutoCareAPI.AUTH_URL,
            json={"access_token": "test-token", "expires_in": 3600},
        )

        requests_mock.get(f"{self.client.base_url}/databases", status_code=401)

        assert self.client.validate_credentials() is False

    def test_context_manager(self):
        """Test context manager functionality."""

        def mock_authenticate(self):
            self.token = "test-token"
            return "test-token"

        with patch.object(AutoCareAPI, "authenticate", mock_authenticate):
            with AutoCareAPI("id", "secret", "user", "pass") as client:
                assert client.token == "test-token"
                # Client should be automatically closed after exiting context

    def test_string_representation(self):
        """Test string representation of client."""
        repr_str = repr(self.client)
        assert "AutoCareAPI" in repr_str
        assert self.client.client_id[:8] in repr_str
        assert self.client.base_url in repr_str


class TestConvenienceFunctions:
    """Test convenience functions."""

    @patch.object(AutoCareAPI, "authenticate", return_value="test-token")
    def test_create_client(self, mock_auth):
        """Test create_client convenience function."""
        client = create_client("id", "secret", "user", "pass", timeout=60)

        assert isinstance(client, AutoCareAPI)
        assert client.client_id == "id"
        assert client.timeout == 60

        client.close()


class TestDataClasses:
    """Test data classes and structures."""

    def test_database_info_creation(self):
        """Test DatabaseInfo dataclass creation."""
        db_info = DatabaseInfo(
            name="vcdb",
            version="2.0",
            description="Vehicle Database",
            tables=["Vehicle", "Make"],
        )

        assert db_info.name == "vcdb"
        assert db_info.version == "2.0"
        assert db_info.description == "Vehicle Database"
        assert len(db_info.tables) == 2

    def test_table_info_creation(self):
        """Test TableInfo dataclass creation."""
        table_info = TableInfo(
            name="Vehicle",
            database="vcdb",
            record_count=1000,
            columns=["VehicleID", "Year", "Make"],
        )

        assert table_info.name == "Vehicle"
        assert table_info.database == "vcdb"
        assert table_info.record_count == 1000
        assert len(table_info.columns) == 3

    def test_api_response_creation(self):
        """Test APIResponse dataclass creation."""
        response = APIResponse(
            success=True,
            data={"key": "value"},
            status_code=200,
            headers={"Content-Type": "application/json"},
        )

        assert response.success is True
        assert response.data["key"] == "value"
        assert response.status_code == 200
        assert response.headers["Content-Type"] == "application/json"


# Integration tests (require actual API credentials)
class TestIntegration:
    """Integration tests - run with actual API credentials."""

    @pytest.mark.integration
    @pytest.mark.skip(reason="Requires actual API credentials")
    def test_full_workflow(self):
        """Test complete workflow with real API."""
        import os

        client_id = os.getenv("AUTOCARE_CLIENT_ID")
        client_secret = os.getenv("AUTOCARE_CLIENT_SECRET")
        username = os.getenv("AUTOCARE_USERNAME")
        password = os.getenv("AUTOCARE_PASSWORD")

        if not all([client_id, client_secret, username, password]):
            pytest.skip("API credentials not available")

        with AutoCareAPI(client_id, client_secret, username, password) as api:
            # Test authentication
            assert api.token is not None

            # Test database listing
            databases = api.list_databases()
            assert len(databases) > 0

            # Test table listing
            if databases:
                tables = api.list_tables(databases[0].name)
                assert len(tables) >= 0

                # Test record fetching (limit to avoid long test)
                if tables:
                    records = list(
                        api.fetch_records(databases[0].name, tables[0].name, limit=5)
                    )
                    assert len(records) <= 5


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
