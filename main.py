from fastapi import FastAPI, status, HTTPException, Request
import socket
from routers.netbanking_txn import router as netbankingRouter
from routers.auth import router as authRouter

# app = FastAPI(redoc_url=None, docs_url=None)
app = FastAPI(
    title="Paythrough Payout",
    version="1.0.0",
    swagger_ui_parameters={
        "syntaxHighlight.theme": "obsidian",
        "defaultModelsExpandDepth": -1,
    },
)

app.include_router(netbankingRouter)
app.include_router(authRouter)


@app.get("/")
async def root(request: Request):
    ip = request.client.host
    print(ip)

    return {"message": "From Payments application"}
