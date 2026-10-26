"""Health-check endpoints for application and blockchain connectivity."""

from fastapi import APIRouter
from web3 import Web3
from web3.exceptions import Web3Exception

from app.core.config import get_settings
from app.schemas.health import BlockchainHealthResponse, HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    """Return basic application liveness status."""
    settings = get_settings()
    return HealthResponse(
        status="ok",
        service=settings.app_name,
        environment=settings.app_env,
    )


@router.get("/health/blockchain", response_model=BlockchainHealthResponse)
async def blockchain_health() -> BlockchainHealthResponse:
    """Probe the configured EVM RPC endpoint without fabricating success."""
    settings = get_settings()
    rpc_url = settings.blockchain_rpc_url

    try:
        w3 = Web3(Web3.HTTPProvider(rpc_url, request_kwargs={"timeout": 3}))
        if not w3.is_connected():
            return BlockchainHealthResponse(
                status="unavailable",
                connected=False,
                rpc_url=rpc_url,
                detail="RPC endpoint did not respond as connected",
            )

        chain_id = w3.eth.chain_id
        block_number = w3.eth.block_number
        return BlockchainHealthResponse(
            status="ok",
            connected=True,
            rpc_url=rpc_url,
            chain_id=chain_id,
            latest_block=block_number,
            expected_chain_id=settings.blockchain_chain_id,
            detail="Connected to blockchain RPC",
        )
    except (Web3Exception, OSError, TimeoutError, ValueError) as exc:
        return BlockchainHealthResponse(
            status="unavailable",
            connected=False,
            rpc_url=rpc_url,
            detail=f"Blockchain RPC unreachable: {exc.__class__.__name__}",
        )
