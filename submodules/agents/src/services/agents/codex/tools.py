import logging
from typing import Any, Dict, List, Optional

import aiohttp

from services.secrets import get_secret

from .config import Config
from .models import NftSearchResponse, TokenFilterResult, TopHoldersResponse, TopTokensResponse
from .utils.networks import NETWORK_TO_ID_MAPPING

logger = logging.getLogger(__name__)


async def _make_graphql_request(query: str, variables: Optional[Dict[str, Any]] = None) -> Any:
    """Make a GraphQL request to Codex API."""
    # Get API key from environment
    api_key = get_secret("CodexApiKey")
    if not api_key:
        raise Exception("CODEX_API_KEY environment variable is not set")

    headers = {"Authorization": api_key, "Content-Type": "application/json"}

    data = {"query": query, "variables": variables or {}}

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(Config.GRAPHQL_URL, json=data, headers=headers) as response:
                result = await response.json()

                if response.status != 200:
                    error_msg = result.get("message", str(result))
                    raise Exception(f"API request failed with status {response.status}: {error_msg}")

                if "errors" in result:
                    error = result["errors"][0]
                    error_msg = error.get("message", "Unknown GraphQL error")
                    raise Exception(f"GraphQL error: {error_msg}")

                return result["data"]
    except Exception as e:
        logger.error(f"API request failed: {str(e)}", exc_info=True)
        raise Exception(f"Failed to fetch data: {str(e)}")


async def list_top_tokens(
    limit: Optional[int] = None,
    networks: Optional[List[str]] = None,
    resolution: Optional[str] = None,
) -> TopTokensResponse:
    """Get list of trending tokens across specified networks."""
    try:
        # Map network names to IDs if networks are provided
        network_filter = []
        if networks:
            network_filter = [
                NETWORK_TO_ID_MAPPING[network] for network in networks if network in NETWORK_TO_ID_MAPPING
            ]

        variables = {
            "limit": min(limit or 20, 50),  # Default 20, max 50
            "network_filter": network_filter,
            "resolution": resolution or "1D",  # Default to 1 day
        }

        query = """
        query ListTopTokens($limit: Int, $networkFilter: [Int!], $resolution: String) {
            listTopTokens(limit: $limit, networkFilter: $networkFilter, resolution: $resolution) {
                address
                createdAt
                decimals
                id
                imageBannerUrl
                imageLargeUrl
                imageSmallUrl
                imageThumbUrl
                isScam
                lastTransaction
                liquidity
                marketCap
                name
                networkId
                price
                priceChange
                priceChange1
                priceChange4
                priceChange12
                priceChange24
                quoteToken
                resolution
                symbol
                topPairId
                txnCount1
                txnCount4
                txnCount12
                txnCount24
                uniqueBuys1
                uniqueBuys4
                uniqueBuys12
                uniqueBuys24
                uniqueSells1
                uniqueSells4
                uniqueSells12
                uniqueSells24
                volume
            }
        }
        """

        response = await _make_graphql_request(query, variables)
        return TopTokensResponse(success=True, data=response["listTopTokens"])
    except Exception as e:
        logger.error(f"Failed to get top tokens: {str(e)}", exc_info=True)
        raise Exception(f"Failed to get top tokens: {str(e)}")


async def _filter_tokens(token_name: str, network: str) -> TokenFilterResult:
    """Helper function to find a token ID by name and network."""
    try:
        network_id = NETWORK_TO_ID_MAPPING.get(network)
        if not network_id:
            raise Exception(f"Invalid network: {network}")

        variables = {
            "phrase": token_name,
            "filters": {
                "network": [network_id],
                "liquidity": {"gt": 100000},
                "txnCount24": {"gt": 200},
            },
            "limit": 1,
        }

        query = """
        query FilterTokens($phrase: String, $filters: TokenFilters, $limit: Int) {
            filterTokens(phrase: $phrase, filters: $filters, limit: $limit) {
                results {
                    buyCount1
                    high1
                    txnCount1
                    uniqueTransactions1
                    volume1
                    liquidity
                    marketCap
                    priceUSD
                    pair {
                        token0
                        token1
                    }
                    exchanges {
                        name
                    }
                    token {
                        address
                        decimals
                        id
                        name
                        networkId
                        symbol
                    }
                }
            }
        }
        """
        logger.info(f"Making GraphQL request to filter tokens with query: {query} and variables: {variables}")
        response = await _make_graphql_request(query, variables)
        logger.info(f"Received filter tokens response: {response}")

        results = response["filterTokens"]["results"]
        logger.info(f"Found {len(results)} matching tokens")

        if not results:
            logger.warning(f"No token found matching {token_name} on {network}")
            raise Exception(f"No token found matching {token_name} on {network}")

        token_info = TokenFilterResult(**results[0])
        logger.info(f"Selected token info: {token_info}")
        return token_info

    except Exception as e:
        logger.error(f"Failed to filter tokens: {str(e)}", exc_info=True)
        raise Exception(f"Failed to filter tokens: {str(e)}")


async def get_top_holders_percent(token_name: str, network: str) -> TopHoldersResponse:
    """Get percentage owned by top 10 holders for a token."""
    try:
        logger.info(f"Getting top holders percentage for token {token_name} on {network}")
        # Strip special characters from token name
        token_name = "".join(c for c in token_name if c.isalnum() or c.isspace())
        token_name = token_name.strip()

        if not token_name:
            raise Exception("Token name cannot be empty after stripping special characters")

        logger.info(f"Sanitized token name: {token_name}")
        # First get the token info by filtering tokens
        logger.info("Filtering tokens to get token info")
        token_info = await _filter_tokens(token_name, network)
        logger.info(f"Found token info: {token_info}")

        if not token_info.token:
            raise Exception("Token info missing token details")

        # Then get top holders percentage using token ID
        variables = {"tokenId": token_info.token.id}
        logger.info(f"Getting top holders with variables: {variables}")

        query = """
        query GetTop10HoldersPercent($tokenId: String!) {
            top10HoldersPercent(tokenId: $tokenId)
        }
        """

        logger.info("Making GraphQL request for top holders percentage")
        response = await _make_graphql_request(query, variables)
        logger.info(f"Received top holders response: {response}")

        percentage = response["top10HoldersPercent"]
        logger.info(f"Top 10 holders own {percentage}% of token {token_name}")

        return TopHoldersResponse(success=True, data=percentage, token_info=token_info)
    except Exception as e:
        logger.error(f"Failed to get top holders percentage: {str(e)}", exc_info=True)
        raise Exception(f"Failed to get top holders percentage: {str(e)}")


async def search_nfts(
    search: str,
    limit: Optional[int] = None,
    network_filter: Optional[List[int]] = None,
    filter_wash_trading: Optional[bool] = None,
    window: Optional[str] = None,
) -> NftSearchResponse:
    """Search for NFT collections by name or address."""
    try:
        variables = {
            "search": search,
            "limit": limit or 20,  # Default to 20 results
            "networkFilter": network_filter or [],
            "filterWashTrading": filter_wash_trading or False,
            "window": window or "1d",  # Default to 1 day
        }

        query = """
        query SearchNFTs($search: String!, $limit: Int, $networkFilter: [Int!], $filterWashTrading: Boolean,
        $window: String) {
            searchNfts(search: $search, limit: $limit, networkFilter: $networkFilter,
            filterWashTrading: $filterWashTrading, window: $window) {
                hasMore
                items {
                    address
                    average
                    ceiling
                    floor
                    id
                    imageUrl
                    name
                    networkId
                    symbol
                    tradeCount
                    tradeCountChange
                    volume
                    volumeChange
                    window
                }
            }
        }
        """

        response = await _make_graphql_request(query, variables)
        return NftSearchResponse(
            success=True,
            hasMore=response["searchNfts"]["hasMore"],
            items=response["searchNfts"]["items"],
        )
    except Exception as e:
        logger.error(f"Failed to search NFTs: {str(e)}", exc_info=True)
        raise Exception(f"Failed to search NFTs: {str(e)}")
