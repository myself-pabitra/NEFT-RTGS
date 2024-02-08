from pydantic import BaseModel


class GenerateTokenIn(BaseModel):
    client_id: str
    client_secret: str


class Token(BaseModel):
    access_token: str
    token_type: str
