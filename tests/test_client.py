# tests/test_client.py
import pytest
from unittest.mock import patch, Mock
from smartscout import SmartScoutClient
from smartscout.exceptions import SmartScoutAPIError, AuthenticationError

def test_client_initialization():
    client = SmartScoutClient(api_key="test_key")
    assert client.api_key == "test_key"

@patch('smartscout.client.requests.Session.request')
def test_search_products(mock_request):
    mock_response = Mock()
    mock_response.json.return_value = {"data": [{"asin": "B123", "title": "Test Product"}]}
    mock_response.raise_for_status.return_value = None
    mock_request.return_value = mock_response

    client = SmartScoutClient(api_key="test_key")
    response = client.search_products({"marketplace": "US"})

    assert response.data[0].asin == "B123"
    assert response.data[0].title == "Test Product"

def test_authentication_error():
    with pytest.raises(AuthenticationError):
        client = SmartScoutClient(api_key="invalid_key")
        client.search_products({"marketplace": "US"})

# tests/models/test_requests.py
import pytest
from smartscout.models.requests import SearchProductsRequest
from smartscout.models.enums import MarketplaceId
from pydantic import ValidationError

def test_search_products_request():
    request = SearchProductsRequest(
        marketplace=MarketplaceId.US,
        brand_name="Example Brand",
        review_count={"min": 100}
    )
    assert request.marketplace == MarketplaceId.US
    assert request.brand_name.filter == "Example Brand"
    assert request.review_count.min == 100

def test_invalid_search_products_request():
    with pytest.raises(ValidationError):
        SearchProductsRequest(
            marketplace="Invalid",
            brand_name="Example Brand"
        )

# tests/models/test_responses.py
from smartscout.models.responses import Product

def test_product_response():
    product_data = {
        "asin": "B123",
        "title": "Test Product",
        "price": {"amount": 19.99, "currency": "USD"},
        "sales_rank": 1000,
        "reviews": {"average_rating": 4.5, "total_reviews": 100}
    }
    product = Product(**product_data)
    assert product.asin == "B123"
    assert product.title == "Test Product"
    assert product.price.amount == 19.99
    assert product.sales_rank == 1000
    assert product.reviews.average_rating == 4.5

# tests/test_exceptions.py
from smartscout.exceptions import SmartScoutAPIError, RateLimitError

def test_smartscout_api_error():
    error = SmartScoutAPIError("Test error", status_code=400)
    assert str(error) == "API Error: Test error"
    assert error.status_code == 400

def test_rate_limit_error():
    error = RateLimitError()
    assert str(error) == "Rate Limit Error: Rate limit exceeded"