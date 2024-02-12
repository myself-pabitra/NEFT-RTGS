from fastapi import FastAPI, status, HTTPException, Request
import socket
from routers.netbanking_txn import router as netbankingRouter
from routers.auth import router as authRouter

app = FastAPI(redoc_url=None, docs_url=None)
# app = FastAPI(docs_url=None, redoc_url=None)

app.include_router(netbankingRouter)
app.include_router(authRouter)


@app.get("/")
async def root():
    return {"message": "From Payments application"}
