from fastapi import FastAPI,status,HTTPException

from routers.netbanking_txn import router as netbankingRouter

app = FastAPI()

app.include_router(netbankingRouter)

    