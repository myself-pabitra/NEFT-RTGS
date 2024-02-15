from fastapi import APIRouter, status, HTTPException, Depends
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
from database.connections import connect
from mysql.connector import Error
import random
import string
import requests
from decimal import Decimal
from database.settings import (
    CASH_TRANSFER_API_ENDPOINT,
    TRANSACTION_REPORT_ENDPOINT,
    CLIENT_ID,
    CLIENT_SECRET,
)


# Authentication Imports
from routers.auth import get_current_merchant, get_merchant_by_id


router = APIRouter(prefix="/api", tags=["NetBanking"])


def generate_reference_number(length=15):
    """
    This Function generates unique 15 digits of clientReferenceId
    """
    # Define the set of characters to choose from (only digits)
    valid_chars = string.digits

    # Generate a random string of specified length from the valid characters
    reference_number = "".join(random.choices(valid_chars, k=length))

    return reference_number


def generate_transactionId(length=20):
    """
    This Function generates unique 20 digits of TransactionId which will be replaced with actual iServeU provided tranaction ID in Production
    """
    # Define the set of characters to choose from (only digits)
    valid_chars = string.digits

    # Generate a random string of specified length from the valid characters
    transactionId = "".join(random.choices(valid_chars, k=length))

    return transactionId


def extract_ip_lat_lon():
    """
    This section of code will change with actual our implimention. currently we are using 3rd party public ip extractor
    """
    try:
        response = requests.get("https://get.geojs.io/v1/ip/geo.json")
        if response.status_code == 200:
            data = response.json()
            ip = data.get("ip")
            latitude = float(data.get("latitude"))
            longitude = float(data.get("longitude"))
            return ip, latitude, longitude
        else:
            raise HTTPException(
                status_code=500, detail="Failed to fetch data from the geojs api"
            )
            return None, None, None
    except Exception as e:
        message = f"Error: {e}"
        raise HTTPException(
            status_code=500, detail=f"Error in getting ip or lat-lon : message"
        )
        return None, None, None


ip, latitude, longitude = extract_ip_lat_lon()


@router.post("/payout", response_model=TransactionResponse)
async def netBanking_transaction_request_(
    impsRequestData: TransactionRequest,
):
    """Intitate Payment Request"""
    scheme, token, user_data = (
        impsRequestData.token_type,
        impsRequestData.access_token,
        impsRequestData.user_data,
    )
    if scheme.lower() != "bearer":

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    merchant_id = get_current_merchant(token=token)
    merchant = get_merchant_by_id(id=merchant_id)

    if not merchant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Invalid Credentials"
        )

    mcode = merchant.get("mCode")
    """
    Extra_request_data_from backend to request model..
    """
    clientReferenceNo = generate_reference_number()
    custIpAddress = ip
    latlong = "23.8053196,86.4282231"

    """
    All the Request model data will be inserted into Paythrough database with system generated clientReferenceNo and users IP address and users LatLon
    """
    try:
        conn = connect()

        if conn.is_connected():
            cursor = conn.cursor()
            try:
                """
                Balance check and debiting wallet balnce section of current transaction
                """
                requested_balnce = impsRequestData.user_data.amount  # in Decimal
                print(type(impsRequestData.user_data.amount))
                merchnat_wallet_balance = fetch_wallet_bal(merchant_id)
                if not merchnat_wallet_balance:
                    raise HTTPException(
                        status_code=404, detail="Could't fetch wallet balance."
                    )

                if requested_balnce > merchnat_wallet_balance:
                    raise HTTPException(
                        status_code=400,
                        detail="You don't have sufficient wallet balance to perform this transaction",
                    )

                insert_transaction_request_data_query = "INSERT INTO netbanking_requests (beneName,beneAccountNo,beneifsc,benePhoneNo,beneBankName,clientReferenceNo,amount,fundTransferType,pincode,custName,custMobNo,custIpAddress,merchant_id,mcode,latlong,paramA,paramB) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"

                request_data = (
                    impsRequestData.user_data.beneName,
                    impsRequestData.user_data.beneAccountNo,
                    impsRequestData.user_data.beneifsc,
                    impsRequestData.user_data.benePhoneNo,
                    impsRequestData.user_data.beneBankName,
                    clientReferenceNo,
                    requested_balnce,
                    impsRequestData.user_data.fundTransferType,
                    impsRequestData.user_data.pincode,
                    impsRequestData.user_data.custName,
                    impsRequestData.user_data.custMobNo,
                    custIpAddress,
                    merchant_id,
                    mcode,
                    latlong,
                    impsRequestData.user_data.paramA,
                    impsRequestData.user_data.paramB,
                )
                cursor.execute(insert_transaction_request_data_query, request_data)
                conn.commit()

            except Error as e:
                conn.rollback()
                message = f"Error: {e}"
                raise HTTPException(status_code=500, detail=message)
            finally:
                cursor.close()
        else:
            raise HTTPException(
                status_code=500, detail="Database not connected Properly."
            )
    except Exception as err:
        # Handle database errors
        message = f"Error: {err}"
        raise HTTPException(status_code=500, detail=message)
    finally:
        if conn.is_connected():
            conn.close()

    """
    Here we will call iServeU api with our request data for transaction completiotion..... below

    TODO
    """

    payout_api_url = CASH_TRANSFER_API_ENDPOINT
    client_id = CLIENT_ID
    client_secret = CLIENT_SECRET

    headers = {
        "Content-Type": "application/json",
        "client_id": client_id,
        "client_secret": client_secret,
    }

    payload = {
        "beneName": impsRequestData.user_data.beneName,
        "beneAccountNo": impsRequestData.user_data.beneAccountNo,
        "beneifsc": impsRequestData.user_data.beneifsc,
        "benePhoneNo": int(impsRequestData.user_data.benePhoneNo),
        "beneBankName": impsRequestData.user_data.beneBankName,
        "clientReferenceNo": clientReferenceNo,
        "amount": float(requested_balnce),
        "fundTransferType": impsRequestData.user_data.fundTransferType,
        "latlong": latlong,
        "pincode": int(impsRequestData.user_data.pincode),
        "custName": impsRequestData.user_data.custName,
        "custMobNo": int(impsRequestData.user_data.custMobNo),
        "custIpAddress": custIpAddress,
        "paramA": impsRequestData.user_data.paramA,
        "paramB": impsRequestData.user_data.paramB,
    }

    print("data from payload :", payload)
    print("data from payload :", payload["amount"])

    response = requests.post(payout_api_url, json=payload, headers=headers)
    print(response.text)

    """
    Extra_response_data_from backend to response model.. for UAT in productio there should be api response data from iserveU
    """

    def generate_random_status():

        statuses = [
            ("FAILED", "-1", "Failed from Bank"),
            ("FAILED", "2", "Failed from wallet"),
            ("FAILED", "-2", "Failed from IServeU"),
            ("INPROGRESS", "1", "Transaction In Progress"),
            ("SUCCESS", "0", "Transaction success"),
        ]
        return random.choice(statuses)

    # Set variables to randomly generated values
    status, subStatus, statusDesc = generate_random_status()

    status = status  # For UAT its Static status for transaction Response
    print("status:", status)
    subStatus = subStatus  # For UAT its static subStatus
    statusDesc = statusDesc  # For UAT its static subStatusDescription
    rrn = generate_transactionId(
        10
    )  # This unique number will generated by the bank/NPCI for each transaction
    transactionId = (
        generate_transactionId()
    )  # This will iServeU system generated unique transaction id
    tnx_dateTime = str(datetime.now(timezone.utc).strftime("%m-%d-%Y %H:%M:%S"))
    wallet_transaction_reference = generate_transactionId(15)
    wallet_transaction_type = "Dr"
    """
    All the Response data from iServeU will be inserted into Paythrough database here below....
    """
    try:
        conn = connect()

        if conn.is_connected():

            cursor = conn.cursor()
            try:
                conn.start_transaction()
                """
                    here I have to do a transaction in wallet and update the database according to the response of iServeU
                    TODO
                """
                # Deduct wallet balance only if status is 'SUCCESS' or 'INPROGRESS'
                if status in ["SUCCESS", "INPROGRESS"]:
                    updated_balance = merchnat_wallet_balance - requested_balnce

                    """ Update Wallet Balance if transaction after deduction is transaction is successful """
                    update_balance_query = "UPDATE merchants_wallet SET balance = %s WHERE merchant_id = %s"
                    cursor.execute(update_balance_query, (updated_balance, merchant_id))

                    """ Do The wallet Transaction """
                    wallet_transaction_query = "INSERT INTO merchant_wallet_transactions (clientReferenceNo,merchant_id,mcode,wallet_transaction_reference,transaction_amount,transaction_type,current_balance) VALUES (%s,%s,%s,%s,%s,%s,%s)"

                    wallet_transaction_data = (
                        clientReferenceNo,
                        merchant_id,
                        mcode,
                        wallet_transaction_reference,
                        requested_balnce,
                        wallet_transaction_type,
                        updated_balance,
                    )

                    cursor.execute(wallet_transaction_query, wallet_transaction_data)
                else:

                    updated_balance = (
                        merchnat_wallet_balance  # No deduction if transaction fails
                    )

                insert_transaction_response_data_query = "INSERT INTO netbanking_response (status,subStatus,statusDesc,rrn,transactionId,beneName,beneAccountNo,beneifsc,benePhoneNo,beneBankName,clientReferenceNo,txnAmount,txnType,latlong,pincode,custName,custMobNo,dateTime,paramA,paramB) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"

                """
                here we will insert iServeU api response data... In Production

                TODO
                """
                api_response_data = (
                    status,
                    subStatus,
                    statusDesc,
                    rrn,
                    transactionId,
                    impsRequestData.user_data.beneName,
                    impsRequestData.user_data.beneAccountNo,
                    impsRequestData.user_data.beneifsc,
                    impsRequestData.user_data.benePhoneNo,
                    impsRequestData.user_data.beneBankName,
                    clientReferenceNo,
                    requested_balnce,
                    impsRequestData.user_data.fundTransferType,
                    latlong,
                    impsRequestData.user_data.pincode,
                    impsRequestData.user_data.custName,
                    impsRequestData.user_data.custMobNo,
                    tnx_dateTime,
                    impsRequestData.user_data.paramA,
                    impsRequestData.user_data.paramB,
                )
                cursor.execute(
                    insert_transaction_response_data_query, api_response_data
                )
                conn.commit()

            except Error as e:
                conn.rollback()
                message = f"Error: {e}"
                raise HTTPException(status_code=500, detail=message)
            finally:
                cursor.close()
        else:
            raise HTTPException(
                status_code=500, detail="Database not connected Properly."
            )
    except Exception as err:
        # Handle database errors
        message = f"Error: {err}"
        raise HTTPException(status_code=500, detail=message)
    finally:
        if conn.is_connected():
            conn.close()

    response_data = {
        "status": status,
        "subStatus": subStatus,
        "statusDesc": statusDesc,
        "rrn": rrn,
        "transactionId": transactionId,
        "beneName": impsRequestData.user_data.beneName,
        "beneAccountNo": impsRequestData.user_data.beneAccountNo,
        "beneifsc": impsRequestData.user_data.beneifsc,
        "benePhoneNo": impsRequestData.user_data.benePhoneNo,
        "beneBankName": impsRequestData.user_data.beneBankName,
        "clientReferenceNo": clientReferenceNo,
        "txnAmount": requested_balnce,
        "txnType": impsRequestData.user_data.fundTransferType,
        "latlong": latlong,
        "pincode": impsRequestData.user_data.pincode,
        "custName": impsRequestData.user_data.custName,
        "custMobNo": impsRequestData.user_data.custMobNo,
        "dateTime": tnx_dateTime,
        "paramA": impsRequestData.user_data.paramA,
        "paramB": impsRequestData.user_data.paramB,
    }

    return response_data


@router.post("/status", response_model=Union[StatusResponse, StatusErrorResponse])
async def check_transaction_status(statusRequest: StatusRequest):
    """Intitate Payment Request"""
    scheme, token, user_status_data = (
        statusRequest.token_type,
        statusRequest.access_token,
        statusRequest.user_status_data,
    )

    if scheme.lower() != "bearer":

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    merchant_id = get_current_merchant(token=token)
    merchant = get_merchant_by_id(id=merchant_id)

    if not merchant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Invalid Credentials"
        )

    mcode = merchant.get("mCode")

    Query_Operation = statusRequest.user_status_data.Query_Operation
    Start_Date = statusRequest.user_status_data.Start_Date
    End_Date = statusRequest.user_status_data.End_Date
    ClientRefId = statusRequest.user_status_data.ClientRefId
    Transaction_ID = statusRequest.user_status_data.Transaction_ID

    try:
        conn = connect()

        if conn.is_connected():
            print("Database connected successfully..")
            cursor = conn.cursor()
            try:
                conn.start_transaction()
                query = (
                    "SELECT * FROM netbanking_response "
                    "WHERE clientReferenceNo = %s "
                    "AND transactionId = %s"
                )
                """
                here we will insert iServeU api response data... In Production

                TODO
                """
                values = (ClientRefId, Transaction_ID)
                cursor.execute(query, values)

                columns = [desc[0] for desc in cursor.description]

                transaction_details = cursor.fetchone()
                print(transaction_details)

                if not transaction_details:
                    response_data = {
                        "status": 0,
                        "message": "Query error: Unrecognized name: undefined at [12:29]",
                    }

                else:
                    transaction_details_data = dict(zip(columns, transaction_details))
                    response_data = {
                        "status": 200,
                        "message": "Success",
                        "length": 1,
                        "results": [
                            {
                                "transactionId": int(
                                    transaction_details_data["transactionId"]
                                ),
                                "subStatus": int(transaction_details_data["subStatus"]),
                                "status": transaction_details_data["status"],
                                "statusDesc": transaction_details_data["statusDesc"],
                                "beneName": transaction_details_data["beneName"],
                                "beneAccountNo": transaction_details_data[
                                    "beneAccountNo"
                                ],
                                "beneifsc": transaction_details_data["beneifsc"],
                                "benePhoneNo": int(
                                    transaction_details_data["benePhoneNo"]
                                ),
                                "beneBankName": transaction_details_data[
                                    "beneBankName"
                                ],
                                "clientReferenceNo": transaction_details_data[
                                    "clientReferenceNo"
                                ],
                                "latlong": transaction_details_data["latlong"],
                                "pincode": int(transaction_details_data["pincode"]),
                                "custName": transaction_details_data["custName"],
                                "custMobNo": int(transaction_details_data["custMobNo"]),
                                "rrn": transaction_details_data["rrn"],
                                "paramA": transaction_details_data["paramA"],
                                "paramB": transaction_details_data["paramB"],
                                "dateTime": transaction_details_data["dateTime"],
                                "txnAmount": str(transaction_details_data["txnAmount"]),
                                "txnType": transaction_details_data["txnType"],
                            }
                        ],
                    }

            except Error as e:
                conn.rollback()
                message = f"Error: {e}"
                raise HTTPException(status_code=500, detail=message)
            finally:
                cursor.close()
        else:
            raise HTTPException(
                status_code=500, detail="Database not connected Properly."
            )
    except Exception as err:
        # Handle database errors
        message = f"Error: {err}"
        raise HTTPException(status_code=500, detail=message)
    finally:
        if conn.is_connected():
            conn.close()

    return response_data


"""
Function to fetch Merchnats Wallet Balance
"""


def fetch_wallet_bal(merchant_id: int) -> Union[float, None]:
    try:
        conn = connect()

        if conn.is_connected():
            cursor = conn.cursor()
            try:
                conn.start_transaction()
                query = "SELECT balance FROM merchants_wallet WHERE merchant_id = %s"
                cursor.execute(query, (merchant_id,))
                balance = cursor.fetchone()
                if balance is not None:
                    return Decimal(balance[0])  # Return the balance if found in Decimal
                else:
                    # Return None if merchant not found
                    return None

            except Error as e:
                conn.rollback()
                message = f"Error: {e}"
                print(message)
                raise HTTPException(status_code=500, detail=message)
            finally:
                cursor.close()
        else:
            raise HTTPException(
                status_code=500, detail="Database not connected Properly."
            )
    except Exception as err:
        # Handle database errors
        message = f"Error: {err}"
        raise HTTPException(status_code=500, detail=message)
    finally:
        if conn.is_connected():
            conn.close()


"""
This endpoint will fetch the merchant's avaliabel wallet balance
"""


@router.post("/get-balance/")
async def get_wallet_balance(request: Balancerequest):
    try:
        """Intitate Payment Request"""
        scheme, token = request.token_type, request.access_token

        if scheme.lower() != "bearer":

            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated",
                headers={"WWW-Authenticate": "Bearer"},
            )

        merchant_id = get_current_merchant(token=token)
        merchant = get_merchant_by_id(id=merchant_id)

        if not merchant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Invalid Credentials"
            )

        merchnat_wallet_balance = fetch_wallet_bal(merchant_id)
        if not merchnat_wallet_balance:
            raise HTTPException(status_code=404, detail="Could't fetch wallet balance.")

        return {"Available wallet balance": str(merchnat_wallet_balance)}
    except Exception as err:
        # Handle database errors
        message = f"Error: {err}"
        raise HTTPException(status_code=500, detail=message)
