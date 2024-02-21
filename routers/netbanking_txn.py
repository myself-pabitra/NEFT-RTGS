from fastapi import APIRouter, status, HTTPException, Depends
from pydantic import ValidationError
from typing import List, Union
from models.imps_transaction import (
    TransactionRequest,
    TransactionResponse,
    StatusRequest,
    StatusResponse,
    StatusErrorResponse,
    Balancerequest,
)
from datetime import datetime, timedelta, timezone
from api.netbanking.apiCalls import make_payout_api_request, make_status_api_request

from database.netbanking import (
    Insert_transaction_request_data,
    Insert_transaction_response_data_and_make_wallet_transaction,
    fetch_wallet_bal,
)
from utilities.utils import generate_reference_number, extract_ip_lat_lon

# Authentication Imports
from routers.auth import get_current_merchant, get_merchant_by_id
from utilities.authutils import authenticate_request, fetch_merchant_and_code

router = APIRouter(prefix="/api", tags=["NetBanking"])


@router.post("/payout", response_model=TransactionResponse)
async def netBanking_transaction_request_(
    impsRequestData: TransactionRequest,
):
    clientReferenceNo = generate_reference_number()
    ip, latitude, longitude = extract_ip_lat_lon()
    custIpAddress = ip
    latlong = "23.8053196,86.4282231"

    """
    Initiate a Payout Request using this endpoint. First, obtain a token from the Generate Token Endpoint and then use the generated Access Token and Token Type here.
    """

    scheme, token, user_data = (
        impsRequestData.token_type,
        impsRequestData.access_token,
        impsRequestData.user_data,
    )
    authenticate_request(scheme, token)
    mcode, merchant_id = fetch_merchant_and_code(token)

    """
    inseting transaction request data into database
    """
    transaction_data = {
        "beneName": impsRequestData.user_data.beneName,
        "beneAccountNo": impsRequestData.user_data.beneAccountNo,
        "beneifsc": impsRequestData.user_data.beneifsc,
        "benePhoneNo": impsRequestData.user_data.benePhoneNo,
        "beneBankName": impsRequestData.user_data.beneBankName,
        "clientReferenceNo": clientReferenceNo,
        "requested_balance": impsRequestData.user_data.amount,
        "fundTransferType": impsRequestData.user_data.fundTransferType,
        "pincode": impsRequestData.user_data.pincode,
        "custName": impsRequestData.user_data.custName,
        "custMobNo": impsRequestData.user_data.custMobNo,
        "custIpAddress": custIpAddress,
        "merchant_id": merchant_id,
        "mcode": mcode,
        "latlong": latlong,
        "paramA": impsRequestData.user_data.paramA,
        "paramB": impsRequestData.user_data.paramB,
    }

    Insert_transaction_request_data(transaction_data, merchant_id, mcode)

    """
    Making ISERVEU API call
    """
    iServeU_response_data = make_payout_api_request(transaction_data)

    if (
        iServeU_response_data["status"] == "FAILED"
        or iServeU_response_data["subStatus"] == -2
    ):
        error_message = "API Server Error : " + iServeU_response_data["statusDesc"]
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=error_message
        )
    ISERVEU_transaction_id = iServeU_response_data["transactionId"]
    ISERVEU_sub_status = iServeU_response_data["subStatus"]
    ISERVEU_status = iServeU_response_data["status"]
    ISERVEU_status_desc = iServeU_response_data["statusDesc"]
    ISERVEU_bene_name = iServeU_response_data["beneName"]
    ISERVEU_bene_account_no = iServeU_response_data["beneAccountNo"]
    ISERVEU_bene_ifsc = iServeU_response_data["beneifsc"]
    ISERVEU_bene_phone_no = iServeU_response_data["benePhoneNo"]
    ISERVEU_bene_bank_name = iServeU_response_data["beneBankName"]
    ISERVEU_client_reference_no = iServeU_response_data["clientReferenceNo"]
    ISERVEU_latlong = iServeU_response_data["latlong"]
    ISERVEU_pincode = iServeU_response_data["pincode"]
    ISERVEU_cust_name = iServeU_response_data["custName"]
    ISERVEU_cust_mob_no = iServeU_response_data["custMobNo"]
    ISERVEU_rrn = iServeU_response_data["rrn"]
    ISERVEU_param_a = iServeU_response_data["paramA"]
    ISERVEU_param_b = iServeU_response_data["paramB"]
    ISERVEU_date_time = iServeU_response_data["dateTime"]
    ISERVEU_txn_amount = iServeU_response_data["txnAmount"]
    ISERVEU_txn_type = iServeU_response_data["txnType"]

    """
    All the Response data from iServeU will be inserted into Paythrough database here below....
    """
    api_response_data = (
        ISERVEU_status,
        ISERVEU_sub_status,
        ISERVEU_status_desc,
        ISERVEU_rrn,
        ISERVEU_transaction_id,
        ISERVEU_bene_name,
        ISERVEU_bene_account_no,
        ISERVEU_bene_ifsc,
        ISERVEU_bene_phone_no,
        ISERVEU_bene_bank_name,
        ISERVEU_client_reference_no,
        ISERVEU_txn_amount,
        ISERVEU_txn_type,
        ISERVEU_latlong,
        ISERVEU_pincode,
        ISERVEU_cust_name,
        ISERVEU_cust_mob_no,
        ISERVEU_date_time,
        ISERVEU_param_a,
        ISERVEU_param_b,
    )

    """
    Inserting transaction response data to database
    """

    Insert_transaction_response_data_and_make_wallet_transaction(
        api_response_data, merchant_id, mcode
    )

    response_data = {
        "status": ISERVEU_status,
        "subStatus": str(ISERVEU_sub_status),
        "statusDesc": ISERVEU_status_desc,
        "rrn": ISERVEU_rrn,
        "transactionId": ISERVEU_transaction_id,
        "beneName": ISERVEU_bene_name,
        "beneAccountNo": ISERVEU_bene_account_no,
        "beneifsc": ISERVEU_bene_ifsc,
        "benePhoneNo": str(ISERVEU_bene_phone_no),
        "beneBankName": ISERVEU_bene_bank_name,
        "clientReferenceNo": ISERVEU_client_reference_no,
        "txnAmount": ISERVEU_txn_amount,
        "txnType": ISERVEU_txn_type,
        "latlong": ISERVEU_latlong,
        "pincode": str(ISERVEU_pincode),
        "custName": ISERVEU_cust_name,
        "custMobNo": str(ISERVEU_cust_mob_no),
        "dateTime": ISERVEU_date_time,
        "paramA": ISERVEU_param_a,
        "paramB": ISERVEU_param_b,
    }

    return response_data


@router.post("/status")
async def check_transaction_status(statusRequest: StatusRequest):
    """
    Check Transaction Status From this endpoint. First, obtain a token from the Generate Token Endpoint and then use the generated Access Token and Token Type here
    """
    scheme, token, user_status_data = (
        statusRequest.token_type,
        statusRequest.access_token,
        statusRequest.user_status_data,
    )

    authenticate_request(scheme, token)
    mcode, merchant_id = fetch_merchant_and_code(token)

    iServeU_response_data = make_status_api_request(statusRequest)

    return iServeU_response_data


"""
This endpoint will fetch the merchant's avaliabel wallet balance
"""


@router.post("/get-balance/")
async def get_wallet_balance(request: Balancerequest):
    """
    Check your Wallet Balnce from this endpoint. First, obtain a token from the Generate Token Endpoint and then use the generated Access Token and Token Type here
    """
    try:

        scheme, token = request.token_type, request.access_token

        authenticate_request(scheme, token)
        mcode, merchant_id = fetch_merchant_and_code(token)

        merchnat_wallet_balance = fetch_wallet_bal(merchant_id)
        if not merchnat_wallet_balance:
            raise HTTPException(status_code=404, detail="Could't fetch wallet balance.")

        return {"Available wallet balance": str(merchnat_wallet_balance)}
    except Exception as err:
        # Handle database errors
        message = f"Error: {err}"
        raise HTTPException(status_code=500, detail=message)
