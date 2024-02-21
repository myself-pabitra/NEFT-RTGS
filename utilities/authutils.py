from fastapi import HTTPException, status
from routers.auth import get_current_merchant, get_merchant_by_id


def authenticate_request(token_type: str, access_token: str):
    if token_type.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )


def fetch_merchant_and_code(token: str):
    merchant_id = get_current_merchant(token=token)
    merchant = get_merchant_by_id(id=merchant_id)
    if not merchant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Invalid Credentials"
        )
    return merchant.get("mCode"), merchant_id
