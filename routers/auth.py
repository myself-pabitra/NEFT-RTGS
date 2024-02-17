from fastapi import APIRouter, HTTPException, status, Depends
from typing import Annotated, Optional
from models.auth import Token, GenerateTokenIn
from jose import JWTError, jwt, ExpiredSignatureError
from datetime import datetime, timedelta, timezone
from database.connections import connect
from database.settings import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES


router = APIRouter(prefix="/api")


def get_merchant_by_api_credentials(
    client_id: str, client_secret: str
) -> Optional[dict]:
    try:
        with connect() as conn:
            with conn.cursor() as cursor:
                query = "SELECT * FROM merchant_credentials WHERE client_id = %s AND client_secreat = %s"
                cursor.execute(query, (client_id, client_secret))
                result = cursor.fetchone()
                if result:
                    columns = [desc[0] for desc in cursor.description]
                    merchant_details = dict(zip(columns, result))
                    return merchant_details
                else:
                    return None
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error fetching merchant details: {e}"
        )


def get_merchant_by_id(id: int) -> Optional[dict]:
    try:
        with connect() as conn:
            with conn.cursor() as cursor:
                query = "SELECT * FROM merchants WHERE id = %s"
                cursor.execute(query, (id,))
                merchant = cursor.fetchone()
                if merchant:
                    columns = [desc[0] for desc in cursor.description]
                    merchant_details = dict(zip(columns, merchant))
                    return merchant_details
                else:
                    return None
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error fetching merchant details: {e}"
        )


def create_access_token(data: dict):
    to_encode = data.copy()
    now = datetime.utcnow()
    expire = now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "iat": now})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


@router.post("/generate-token", response_model=Token)
async def generate_access_token(request: GenerateTokenIn) -> Token:
    merchant_details = get_merchant_by_api_credentials(
        client_id=request.client_id, client_secret=request.client_secret
    )
    if not merchant_details:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
        )

    merchant_id = merchant_details.get("merchant_id")
    merchant = get_merchant_by_id(id=merchant_id)

    if not merchant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Merchant not found"
        )

    merchant_name = merchant.get("name")
    merchant_id = merchant.get("id")
    mcode = merchant.get("mCode")

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


def get_current_merchant(token: str) -> Optional[int]:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        merchant_id: int = payload.get("id")
        return merchant_id
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Token Expired"
        )
    except JWTError as e:
        raise credentials_exception


# ---------------------------------------------------------------------------


# """ Intitate Payment Request """
# scheme, token, user = request.token_type, request.access_token, request.user

# if scheme.lower() != "bearer":

#     raise HTTPException(
#         status_code=status.HTTP_401_UNAUTHORIZED,
#         detail="Not authenticated",
#         headers={"WWW-Authenticate": "Bearer"},
#     )

# merchant_id = get_current_merchant(token=token)
# merchant = crud.get_merchant_by_id(id=merchant_id)

# if not merchant:
#     raise HTTPException(
#         status_code=status.HTTP_404_NOT_FOUND, detail="Invalid Credentials"
#     )

# mcode = merchant.get("mcode")
