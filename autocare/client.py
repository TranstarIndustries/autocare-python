"""
AutoCare API Client

A comprehensive Python client for interacting with AutoCare databases and services.
Provides functionality for authentication, database operations, and data management
with proper error handling, logging, and type safety.
"""

import json
import logging
import time
from typing import Dict, List, Optional, Any, Iterator
from dataclasses import dataclass
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AutoCareError(Exception):
    """Base exception class for AutoCare API errors."""

    pass


class AuthenticationError(AutoCareError):
    """Raised when authentication fails."""

    pass


class APIConnectionError(AutoCareError):
    """Raised when unable to connect to the API."""

    pass


class APIResponseError(AutoCareError):
    """Raised when API returns an error response."""

    pass


class DataValidationError(AutoCareError):
    """Raised when data validation fails."""

    pass


class PaginationError(AutoCareError):
    """Raised when pagination parsing fails."""

    pass


@dataclass
class DatabaseInfo:
    """Information about an AutoCare database."""

    name: str
    version: str
    description: Optional[str] = None
    tables: Optional[List[str]] = None


@dataclass
class TableInfo:
    """Information about a database table."""

    name: str
    database: str
    record_count: Optional[int] = None
    columns: Optional[List[str]] = None


@dataclass
class APIResponse:
    """Standardized API response wrapper."""

    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    status_code: Optional[int] = None
    headers: Optional[Dict[str, str]] = None


class AutoCareAPI:
    """
    Enhanced AutoCare API Client

    Provides comprehensive access to AutoCare databases with:
    - OAuth authentication with automatic token refresh
    - Robust error handling and retry logic
    - Proper logging and monitoring
    - Type safety and validation
    - Context manager support
    """

    BASE_URL = "https://common.autocarevip.com/api/v1.0"
    AUTH_URL = "https://autocare-identity.autocare.org/connect/token"
    DEFAULT_SCOPE = "CommonApis QDBApis PcadbApis BrandApis VcdbApis offline_access"
    DEFAULT_TIMEOUT = 30
    DEFAULT_RETRIES = 3
    TOKEN_REFRESH_BUFFER = 300  # Refresh token 5 minutes before expiry

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        username: str,
        password: str,
        scope: str = DEFAULT_SCOPE,
        timeout: int = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_RETRIES,
        base_url: Optional[str] = None,
        auth_url: Optional[str] = None,
    ):
        """
        Initialize the AutoCare API client.

        Args:
            client_id: OAuth client ID
            client_secret: OAuth client secret
            username: User credentials username
            password: User credentials password
            scope: OAuth scope string
            timeout: Request timeout in seconds
            max_retries: Maximum retry attempts
            base_url: Override default base URL
            auth_url: Override default auth URL
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.username = username
        self.password = password
        self.scope = scope
        self.timeout = timeout

        self.base_url = base_url or self.BASE_URL
        self.auth_url = auth_url or self.AUTH_URL

        # Token management
        self.token = None
        self.token_expires_at = 0
        self.refresh_token = None

        # Configure session with retry strategy
        self.session = requests.Session()
        retry_strategy = Retry(
            total=max_retries,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS", "POST"],
            backoff_factor=0.3,
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

        # Set default headers
        self.session.headers.update(
            {"User-Agent": "AutoCare-API-Client/2.0", "Accept": "application/json"}
        )

        # Authenticate on initialization
        self.authenticate()

    def authenticate(self) -> str:
        """
        Authenticate with the AutoCare API using OAuth2 password flow.

        Returns:
            Access token

        Raises:
            AuthenticationError: If authentication fails
        """
        data = {
            "grant_type": "password",
            "username": self.username,
            "password": self.password,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "scope": self.scope,
        }

        headers = {"Content-Type": "application/x-www-form-urlencoded"}

        try:
            logger.info("Authenticating with AutoCare API...")
            response = self.session.post(
                self.auth_url, data=data, headers=headers, timeout=self.timeout
            )
            response.raise_for_status()

            token_data = response.json()
            self.token = token_data["access_token"]

            # Handle token expiration
            expires_in = token_data.get("expires_in", 3600)
            self.token_expires_at = time.time() + expires_in

            # Store refresh token if available
            self.refresh_token = token_data.get("refresh_token")

            logger.info("Authentication successful")
            return self.token  # type: ignore  # token is guaranteed to be set above

        except requests.exceptions.RequestException as e:
            logger.error(f"Authentication request failed: {str(e)}")
            raise AuthenticationError(f"Failed to authenticate: {str(e)}")
        except KeyError as e:
            logger.error(f"Invalid authentication response: missing {str(e)}")
            raise AuthenticationError(
                f"Invalid response from auth server: missing {str(e)}"
            )
        except json.JSONDecodeError:
            logger.error("Invalid JSON in authentication response")
            raise AuthenticationError("Invalid response format from auth server")

    def refresh_access_token(self) -> str:
        """
        Refresh the access token using refresh token.

        Returns:
            New access token

        Raises:
            AuthenticationError: If token refresh fails
        """
        if not self.refresh_token:
            logger.info("No refresh token available, re-authenticating...")
            return self.authenticate()

        data = {
            "grant_type": "refresh_token",
            "refresh_token": self.refresh_token,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }

        headers = {"Content-Type": "application/x-www-form-urlencoded"}

        try:
            logger.info("Refreshing access token...")
            response = self.session.post(
                self.auth_url, data=data, headers=headers, timeout=self.timeout
            )
            response.raise_for_status()

            token_data = response.json()
            self.token = token_data["access_token"]

            expires_in = token_data.get("expires_in", 3600)
            self.token_expires_at = time.time() + expires_in

            # Update refresh token if provided
            if "refresh_token" in token_data:
                self.refresh_token = token_data["refresh_token"]

            logger.info("Token refresh successful")
            return self.token

        except requests.exceptions.RequestException as e:
            logger.warning(f"Token refresh failed: {str(e)}, re-authenticating...")
            return self.authenticate()

    def _ensure_valid_token(self) -> None:
        """Ensure we have a valid access token."""
        current_time = time.time()
        if not self.token or current_time >= (
            self.token_expires_at - self.TOKEN_REFRESH_BUFFER
        ):
            self.refresh_access_token()

    def _get_headers(self) -> Dict[str, str]:
        """
        Get headers with current authentication token.

        Returns:
            Dictionary of headers including authorization
        """
        self._ensure_valid_token()
        return {"Authorization": f"Bearer {self.token}"}

    def _make_request(
        self,
        method: str,
        url: str,
        params: Optional[Dict] = None,
        data: Optional[Dict] = None,
        headers: Optional[Dict] = None,
    ) -> APIResponse:
        """
        Make an authenticated HTTP request.

        Args:
            method: HTTP method
            url: Request URL
            params: Query parameters
            data: Request body data
            headers: Additional headers

        Returns:
            APIResponse object

        Raises:
            APIConnectionError: If request fails
            APIResponseError: If API returns error
        """
        request_headers = self._get_headers()
        if headers:
            request_headers.update(headers)

        try:
            logger.debug(f"Making {method} request to {url}")
            response = self.session.request(
                method=method,
                url=url,
                params=params,
                json=data,
                headers=request_headers,
                timeout=self.timeout,
            )

            # Handle response
            if response.status_code >= 400:
                error_msg = f"API request failed with status {response.status_code}"
                try:
                    error_data = response.json()
                    if "error" in error_data:
                        error_msg = error_data["error"]
                    elif "message" in error_data:
                        error_msg = error_data["message"]
                except json.JSONDecodeError:
                    error_msg = response.text or error_msg

                logger.error(f"API error: {error_msg}")
                return APIResponse(
                    success=False,
                    error=error_msg,
                    status_code=response.status_code,
                    headers=dict(response.headers),
                )

            # Parse response data
            try:
                response_data = response.json()
            except json.JSONDecodeError:
                response_data = response.text

            return APIResponse(
                success=True,
                data=response_data,
                status_code=response.status_code,
                headers=dict(response.headers),
            )

        except requests.exceptions.Timeout:
            error_msg = f"Request timed out after {self.timeout} seconds"
            logger.error(error_msg)
            raise APIConnectionError(error_msg)
        except requests.exceptions.ConnectionError as e:
            error_msg = f"Failed to connect to API: {str(e)}"
            logger.error(error_msg)
            raise APIConnectionError(error_msg)
        except requests.exceptions.RequestException as e:
            error_msg = f"Request failed: {str(e)}"
            logger.error(error_msg)
            raise APIConnectionError(error_msg)

    def list_databases(self) -> List[DatabaseInfo]:
        """
        List available AutoCare databases.

        Returns:
            List of DatabaseInfo objects

        Raises:
            APIConnectionError: If request fails
            APIResponseError: If API returns error
        """
        response = self._make_request("GET", f"{self.base_url}/databases")

        if not response.success:
            raise APIResponseError(f"Failed to list databases: {response.error}")

        databases = []
        if response.data is not None:
            for db_data in response.data:
                if isinstance(db_data, dict):
                    databases.append(
                        DatabaseInfo(
                            name=db_data.get("databaseName", ""),
                            version=db_data.get("version", ""),
                            description=db_data.get("description"),
                        )
                    )
                elif isinstance(db_data, str):
                    databases.append(DatabaseInfo(name=db_data, version=""))

        logger.info(f"Found {len(databases)} databases")
        return databases

    def list_tables(self, db_name: str) -> List[TableInfo]:
        """
        List tables in a specific database.

        Args:
            db_name: Database name

        Returns:
            List of TableInfo objects

        Raises:
            APIConnectionError: If request fails
            APIResponseError: If API returns error
        """
        if not db_name:
            raise DataValidationError("Database name is required")

        url = f"{self.base_url}/databases/{db_name}/tables"
        response = self._make_request("GET", url)

        if not response.success:
            raise APIResponseError(
                f"Failed to list tables for {db_name}: {response.error}"
            )

        tables = []
        if response.data is not None:
            for table_data in response.data:
                if isinstance(table_data, dict):
                    tables.append(
                        TableInfo(
                            name=table_data.get("TableName", ""),
                            database=db_name,
                            record_count=table_data.get("recordCount"),
                            columns=table_data.get("columns"),
                        )
                    )
                elif isinstance(table_data, str):
                    tables.append(TableInfo(name=table_data, database=db_name))

        logger.info(f"Found {len(tables)} tables in database {db_name}")
        return tables

    def fetch_records(
        self,
        db_name: str,
        table_name: str,
        version: str = "1.0",
        limit: Optional[int] = None,
        page_size: Optional[int] = None,
    ) -> Iterator[Dict[str, Any]]:
        """
        Fetch records from a database table with pagination support.

        Args:
            db_name: Database name
            table_name: Table name
            version: API version
            limit: Maximum number of records to fetch (None for all)
            page_size: Records per page for pagination

        Yields:
            Individual records as dictionaries

        Raises:
            APIConnectionError: If request fails
            APIResponseError: If API returns error
            PaginationError: If pagination parsing fails
        """
        if not db_name or not table_name:
            raise DataValidationError("Database name and table name are required")

        base_url = (
            f"https://{db_name}.autocarevip.com/api/v{version}/{db_name}/{table_name}"
        )
        next_page: Optional[str] = base_url
        records_fetched = 0

        params = {}
        if page_size:
            params["pageSize"] = page_size

        logger.info(f"Fetching records from {db_name}.{table_name}")

        while next_page:
            try:
                # Make request with current pagination URL
                current_url = next_page if not params else next_page
                if params and next_page == base_url:
                    # Add params only to the first request
                    response = self._make_request("GET", current_url, params=params)
                else:
                    response = self._make_request("GET", current_url)

                if not response.success:
                    raise APIResponseError(f"Failed to fetch records: {response.error}")

                # Yield records from current page
                page_records = response.data
                if not isinstance(page_records, list):
                    logger.warning(f"Unexpected response format: {type(page_records)}")
                    break

                for record in page_records:
                    if limit and records_fetched >= limit:
                        logger.info(f"Reached record limit: {limit}")
                        return

                    yield record
                    records_fetched += 1

                # Handle pagination
                next_page = None
                if response.headers and "X-Pagination" in response.headers:
                    try:
                        # Safely parse pagination header
                        pagination_header = response.headers["X-Pagination"]
                        # Replace eval with json.loads for security
                        pagination_data = json.loads(
                            pagination_header.replace("'", '"')
                        )
                        next_page = pagination_data.get("nextPageLink")
                    except (json.JSONDecodeError, KeyError, AttributeError) as e:
                        logger.warning(f"Failed to parse pagination header: {e}")
                        break

                if not page_records:  # No more records
                    break

            except Exception as e:
                logger.error(f"Error fetching records: {str(e)}")
                raise

        logger.info(f"Fetched {records_fetched} records from {db_name}.{table_name}")

    def fetch_all_records(
        self, db_name: str, table_name: str, version: str = "1.0"
    ) -> List[Dict[str, Any]]:
        """
        Fetch all records from a table and return as a list.

        Args:
            db_name: Database name
            table_name: Table name
            version: API version

        Returns:
            List of all records
        """
        return list(self.fetch_records(db_name, table_name, version))

    def get_table_info(self, db_name: str, table_name: str) -> Optional[TableInfo]:
        """
        Get detailed information about a specific table.

        Args:
            db_name: Database name
            table_name: Table name

        Returns:
            TableInfo object or None if not found
        """
        try:
            tables = self.list_tables(db_name)
            for table in tables:
                if table.name == table_name:
                    return table
        except Exception as e:
            logger.warning(f"Could not get table info: {e}")

        return None

    def validate_credentials(self) -> bool:
        """
        Validate API credentials by attempting to list databases.

        Returns:
            True if credentials are valid, False otherwise
        """
        try:
            self.list_databases()
            return True
        except Exception:
            return False

    def close(self) -> None:
        """Close the HTTP session."""
        if hasattr(self, "session"):
            self.session.close()
            logger.info("API client session closed")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()

    def __repr__(self) -> str:
        """String representation of the client."""
        return f"AutoCareAPI(client_id='{self.client_id[:8]}...', base_url='{self.base_url}')"


# Convenience functions for backward compatibility and ease of use
def create_client(
    client_id: str, client_secret: str, username: str, password: str, **kwargs
) -> AutoCareAPI:
    """
    Create an AutoCare API client with the provided credentials.

    Args:
        client_id: OAuth client ID
        client_secret: OAuth client secret
        username: Username for authentication
        password: Password for authentication
        **kwargs: Additional client configuration

    Returns:
        Configured AutoCareAPI client
    """
    return AutoCareAPI(
        client_id=client_id,
        client_secret=client_secret,
        username=username,
        password=password,
        **kwargs,
    )
