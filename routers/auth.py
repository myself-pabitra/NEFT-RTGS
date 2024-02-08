from fastapi import APIRouter, HTTPException, status
from models.auth import Token, GenerateTokenIn
from jose import JWTError, jwt
from datetime import datetime, timedelta, timezone

from fastapi.security import (
    OAuth2PasswordBearer,
    OAuth2PasswordRequestForm,
    SecurityScopes,
)
from database.settings import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES


router = APIRouter()


def create_access_token(data: dict):
    to_encode = data.copy()
    now = datetime.utcnow()
    expire = now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "iat": now})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def get_current_merchant(token: str):

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        merchant_id: int = payload.get("id")
        return merchant_id
    except JWTError as e:
        raise credentials_exception


@router.post("/token", response_model=Token)
async def generate_access_token(request: GenerateTokenIn):
    """Generate Token"""

    merchant_details = crud.get_merchant_by_api_credentials(request=request)

    if not merchant_details:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Invalid Credentials."
        )

    merchant_id = merchant_details.get("merchant_id")
    merchant = crud.get_merchant_by_id(id=merchant_id)

    if not merchant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Invalid Credentials"
        )

    merchant_name = merchant.get("name")
    merchant_id = merchant.get("id")
    mcode = merchant.get("mcode")

    access_token = create_access_token(
        data={
            "id": merchant_id,
            "mcode": mcode,
            "name": merchant_name,
            "type": "merchant",
            "iss": "urn:paythrough",
        }
    )

    return {"access_token": access_token, "token_type": "bearer"}


# """ Intitate Payment Request """
#     scheme, token, user = request.token_type, request.access_token, request.user

#     if scheme.lower() != "bearer":

#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Not authenticated",
#             headers={"WWW-Authenticate": "Bearer"},
#         )

#     merchant_id = get_current_merchant(token=token)
#     merchant = crud.get_merchant_by_id(id=merchant_id)

#     if not merchant:
#         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invalid Credentials")

#     mcode = merchant.get("mcode")
