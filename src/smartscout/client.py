# src/smartscout/client.py

import requests
from typing import Dict, Any, Type, TypeVar, Generic
from .models.base import BaseRequest, BaseResponse, PagedResponse

from .models.enums import MarketplaceId
from .models.requests import (
    SearchBrandsRequest,
    SearchProductsRequest,
    SearchSearchTermsRequest,
    SearchSellersRequest,
    GetOrganicRanksRequest,
    GetProductHistoryScopeRequest,
    GetRelevantProductsRequest,
    GetSubcategoryBrandsRequest,
    GetBrandSalesHistoryRequest,
    GetBrandSalesHistoryBySubcategoriesRequest,
    GetBrandScopeRequest,
    GetBrandScopeTopProductsRequest,
    GetRelevantSearchTermsRequest,
    GetSearchTermHistoryRequest
)
from .models.responses import (
    Brand,
    Product,
    Seller,
    SearchTerm,
    BrandSalesHistory,
    ProductSalesHistory,
    SellerPerformance,
    CategoryTrend,
    CompetitorAnalysis,
    BrandPagedResponse,
    ProductPagedResponse,
    SellerPagedResponse,
    SearchTermPagedResponse,
    # Remove OrganicRank if it's not defined in responses.py
    # OrganicRank,
)
from .exceptions import SmartScoutAPIError, RateLimitError, AuthenticationError

T = TypeVar('T', bound=BaseResponse)

class SmartScoutAPIClient:
    """
    A client for interacting with the SmartScout API.
    """

    BASE_URL = "https://api.smartscout.com/v1"

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        })

    def _make_request(self, method: str, endpoint: str, data: Dict[str, Any] = None, params: Dict[str, Any] = None, verbose: bool = False) -> Dict[str, Any]:
        """
        Make a request to the SmartScout API.
        """
        url = f"{self.BASE_URL}{endpoint}"
        
        if verbose:
            curl_command = f"curl -X {method.upper()} '{url}'"
            for header, value in self.session.headers.items():
                curl_command += f" -H '{header}: {value}'"
            if data:
                curl_command += f" -d '{json.dumps(data)}'"
            if params:
                curl_command += f" -G {' '.join([f'-d {k}={shlex.quote(str(v))}' for k, v in params.items()])}"
            print(f"CURL command:\n{curl_command}")

        try:
            response = self.session.request(method, url, json=data, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                raise RateLimitError("Rate limit exceeded")
            elif e.response.status_code == 401:
                raise AuthenticationError("Invalid API key")
            else:
                raise SmartScoutAPIError(f"HTTP error occurred: {e}")
        except requests.exceptions.RequestException as e:
            raise SmartScoutAPIError(f"An error occurred: {e}")

    def _paged_request(self, endpoint: str, request: BaseRequest, response_model: Type[T], verbose: bool = False) -> PagedResponse[T]:
        """
        Make a paged request to the SmartScout API.
        """
        data = request.dict(exclude_none=True)
        response_data = self._make_request("POST", endpoint, data=data, verbose=verbose)
        return PagedResponse[response_model](**response_data)

    def search_brands(self, request: SearchBrandsRequest, verbose: bool = False) -> PagedResponse[Brand]:
        """
        Search for brands based on the given criteria.
        """
        return self._paged_request("/brands/search", request, Brand, verbose=verbose)

    def search_products(
        self, 
        request: SearchProductsRequest, 
        verbose: bool = False
    ) -> PagedResponse[Product]:
        """
        Search for products based on specified criteria.

        This method allows users to search for products within the SmartScout database by providing various filtering criteria encapsulated
        within a `SearchProductsRequest` object. The search results are returned in a paginated format, facilitating efficient data retrieval.

        Args:
            request (SearchProductsRequest): 
                An instance of `SearchProductsRequest` containing the search parameters. This may include filters such as 
                marketplace ID, brand name, category, price range, and other relevant product attributes.
            
            verbose (bool, optional): 
                If set to `True`, the method will output detailed information about the API request being made, including the 
                constructed CURL command for debugging purposes. Defaults to `False`.

        Returns:
            PagedResponse[Product]: 
                A `PagedResponse` object containing a list of `Product` instances that match the search criteria. It also includes 
                pagination metadata such as total results, page number, and page size.

        Raises:
            SmartScoutAPIError:
                Raised when an unexpected error occurs during the API request that is not related to rate limiting or authentication.
            
            RateLimitError:
                Raised when the API rate limit has been exceeded. Users should implement retry logic with exponential backoff in this case.
            
            AuthenticationError:
                Raised when the provided API key is invalid or has insufficient permissions to perform the search operation.

        Example:
            ```python
            from smartscout.client import SmartScoutAPIClient
            from smartscout.models.requests import SearchProductsRequest
            from smartscout.models.enums import MarketplaceId

            # Initialize the API client with your API key
            client = SmartScoutAPIClient(api_key="your_api_key_here")

            # Create a search request with desired criteria
            product_request = SearchProductsRequest(
                marketplace=MarketplaceId.US,
                brand_name="Example Brand",
                category="Electronics",
                price_min=50.00,
                price_max=500.00
            )

            # Perform the product search with verbose output
            try:
                product_response = client.search_products(product_request, verbose=True)
                for product in product_response.data:
                    print(f"ASIN: {product.asin}, Title: {product.title}, Price: ${product.price}")
            except AuthenticationError:
                print("Invalid API key provided.")
            except RateLimitError:
                print("Rate limit exceeded. Please try again later.")
            except SmartScoutAPIError as e:
                print(f"An error occurred: {e}")
            ```

        Notes:
            - Ensure that the `SearchProductsRequest` is populated with all necessary fields to obtain accurate and relevant search results.
            - When `verbose` is enabled, sensitive information such as API keys will appear in the output. Use this feature primarily for debugging purposes in a secure environment.
        """
        return self._paged_request("/products/search", request, Product, verbose=verbose)

    def search_search_terms(self, request: SearchSearchTermsRequest, verbose: bool = False) -> PagedResponse[SearchTerm]:
        """
        Search for search terms based on the given criteria.
        """
        return self._paged_request("/search-terms/search", request, SearchTerm, verbose=verbose)

    def search_sellers(self, request: SearchSellersRequest, verbose: bool = False) -> PagedResponse[Seller]:
        """
        Search for sellers based on the given criteria.
        """
        return self._paged_request("/sellers/search", request, Seller, verbose=verbose)

    def get_organic_ranks(self, request: GetOrganicRanksRequest, verbose: bool = False) -> PagedResponse[Product]:
        """
        Get organic ranks for products based on the given criteria.
        """
        return self._paged_request("/products/organic-ranks", request, Product, verbose=verbose)

    def get_product_history_scope(self, request: GetProductHistoryScopeRequest, verbose: bool = False) -> PagedResponse[ProductSalesHistory]:
        """
        Get product history scope based on the given criteria.
        """
        return self._paged_request("/products/history/scope", request, ProductSalesHistory, verbose=verbose)

    def get_relevant_products(self, request: GetRelevantProductsRequest, verbose: bool = False) -> PagedResponse[Product]:
        """
        Get relevant products based on the given criteria.
        """
        return self._paged_request("/products/relevant", request, Product, verbose=verbose)

    def get_subcategory_brands(self, request: GetSubcategoryBrandsRequest, verbose: bool = False) -> PagedResponse[Brand]:
        """
        Get brands in a subcategory based on the given criteria.
        """
        return self._paged_request("/subcategories/brands", request, Brand, verbose=verbose)

    def get_brand_sales_history(self, request: GetBrandSalesHistoryRequest, verbose: bool = False) -> PagedResponse[BrandSalesHistory]:
        """
        Get brand sales history based on the given criteria.
        """
        return self._paged_request("/brands/history/sales", request, BrandSalesHistory, verbose=verbose)

    def get_brand_sales_history_by_subcategories(self, request: GetBrandSalesHistoryBySubcategoriesRequest, verbose: bool = False) -> PagedResponse[BrandSalesHistory]:
        """
        Get brand sales history by subcategories based on the given criteria.
        """
        return self._paged_request("/brands/history/sales-by-subcategories", request, BrandSalesHistory, verbose=verbose)

    def get_brand_scope(self, request: GetBrandScopeRequest, verbose: bool = False) -> PagedResponse[Brand]:
        """
        Get brand scope based on the given criteria.
        """
        return self._paged_request("/brands/scope", request, Brand, verbose=verbose)

    def get_brand_scope_top_products(self, request: GetBrandScopeTopProductsRequest, verbose: bool = False) -> PagedResponse[Product]:
        """
        Get top products in a brand scope based on the given criteria.
        """
        return self._paged_request("/brands/scope/top-products", request, Product, verbose=verbose)

    def get_relevant_search_terms(self, request: GetRelevantSearchTermsRequest, verbose: bool = False) -> PagedResponse[SearchTerm]:
        """
        Get relevant search terms based on the given criteria.
        """
        return self._paged_request("/search-terms/relevant", request, SearchTerm, verbose=verbose)

    def get_search_term_history(self, request: GetSearchTermHistoryRequest, verbose: bool = False) -> PagedResponse[SearchTerm]:
        """
        Get search term history based on the given criteria.
        """
        return self._paged_request("/search-terms/history", request, SearchTerm, verbose=verbose)

    # Add more methods for other API endpoints as needed

# Example usage
if __name__ == "__main__":
    client = SmartScoutAPIClient(api_key="your_api_key_here")
    
    # Search for brands with verbose output
    brand_request = SearchBrandsRequest(marketplace=MarketplaceId.US, brand_name="Example Brand")
    brand_response = client.search_brands(brand_request, verbose=True)
    brand_response = client.search_brands(brand_request, verbose=True)
    
    for brand in brand_response.data:
        print(f"Brand: {brand.brand_name}, Monthly Revenue: ${brand.monthly_revenue}")
    
    # Search for brands
    brand_request = SearchBrandsRequest(marketplace=MarketplaceId.US, brand_name="Example Brand")
    brand_response = client.search_brands(brand_request)
    
    for brand in brand_response.data:
        print(f"Brand: {brand.brand_name}, Monthly Revenue: ${brand.monthly_revenue}")

    # Search for products
    product_request = SearchProductsRequest(marketplace=MarketplaceId.US, brand_name="Example Brand")
    product_response = client.search_products(product_request)
    
    for product in product_response.data:
        print(f"Product: {product.asin}, Title: {product.title}")

    # Add more examples for other API endpoints as needed