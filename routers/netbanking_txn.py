from fastapi import APIRouter, status, HTTPException
from typing import List, Union
from models.imps_transaction import (
    TransactionRequest,
    TransactionResponse,
    StatusRequest,
    StatusResponse,
    StatusErrorResponse,
)
from datetime import datetime, timedelta, timezone
from database.connections import connect
from mysql.connector import Error
import random
import string
import requests

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
async def netBanking_transaction_request_(impsRequestData: TransactionRequest):
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
            print("Database connected successfully..")
            cursor = conn.cursor()
            try:
                """
                Balance check and debiting wallet balnce section of current transaction
                """
                requested_balnce = impsRequestData.amount
                mcode = "VIPL"  # get the merchnat code from the jwt token
                merchant_id = "1"  # get the merchnat id from the jwt token
                merchnat_wallet_balance = fetch_wallet_bal(mcode)

                if requested_balnce > merchnat_wallet_balance:
                    raise HTTPException(
                        status_code=400,
                        detail="You don't have sufficient wallet balance to perform this transaction",
                    )
                else:
                    updated_balance = merchnat_wallet_balance - requested_balnce

                    conn.start_transaction()
                    update_balace_query = (
                        "UPDATE merchants_wallet SET balance = %s WHERE mcode = %s"
                    )
                    cursor.execute(update_balace_query, (updated_balance, mcode))

                    insert_transaction_request_data_query = "INSERT INTO netbanking_requests (beneName,beneAccountNo,beneifsc,benePhoneNo,beneBankName,clientReferenceNo,amount,fundTransferType,pincode,custName,custMobNo,custIpAddress,merchant_id,mcode,latlong,paramA,paramB) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"

                    request_data = (
                        impsRequestData.beneName,
                        impsRequestData.beneAccountNo,
                        impsRequestData.beneifsc,
                        impsRequestData.benePhoneNo,
                        impsRequestData.beneBankName,
                        clientReferenceNo,
                        impsRequestData.amount,
                        impsRequestData.fundTransferType,
                        impsRequestData.pincode,
                        impsRequestData.custName,
                        impsRequestData.custMobNo,
                        custIpAddress,
                        merchant_id,
                        mcode,
                        latlong,
                        impsRequestData.paramA,
                        impsRequestData.paramB,
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
    subStatus = subStatus  # For UAT its static subStatus
    statusDesc = statusDesc  # For UAT its static subStatusDescription
    rrn = generate_transactionId(
        10
    )  # This unique number will generated by the bank/NPCI for each transaction
    transactionId = (
        generate_transactionId()
    )  # This will iServeU system generated unique transaction id
    tnx_dateTime = str(datetime.now(timezone.utc).strftime("%m-%d-%Y %H:%M:%S"))

    """
    All the Response data from iServeU will be inserted into Paythrough database here below....
    """
    try:
        conn = connect()

        if conn.is_connected():
            print("Database connected successfully..")
            cursor = conn.cursor()
            try:
                conn.start_transaction()
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
                    impsRequestData.beneName,
                    impsRequestData.beneAccountNo,
                    impsRequestData.beneifsc,
                    impsRequestData.benePhoneNo,
                    impsRequestData.beneBankName,
                    clientReferenceNo,
                    impsRequestData.amount,
                    impsRequestData.fundTransferType,
                    latlong,
                    impsRequestData.pincode,
                    impsRequestData.custName,
                    impsRequestData.custMobNo,
                    tnx_dateTime,
                    impsRequestData.paramA,
                    impsRequestData.paramB,
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
        "beneName": impsRequestData.beneName,
        "beneAccountNo": impsRequestData.beneAccountNo,
        "beneifsc": impsRequestData.beneifsc,
        "benePhoneNo": impsRequestData.benePhoneNo,
        "beneBankName": impsRequestData.beneBankName,
        "clientReferenceNo": clientReferenceNo,
        "txnAmount": impsRequestData.amount,
        "txnType": impsRequestData.fundTransferType,
        "latlong": latlong,
        "pincode": impsRequestData.pincode,
        "custName": impsRequestData.custName,
        "custMobNo": impsRequestData.custMobNo,
        "dateTime": tnx_dateTime,
        "paramA": impsRequestData.paramA,
        "paramB": impsRequestData.paramB,
    }

    return response_data


@router.post("/status", response_model=Union[StatusResponse, StatusErrorResponse])
async def check_transaction_status(statusRequest: StatusRequest):

    Query_Operation = statusRequest.Query_Operation
    Start_Date = statusRequest.Start_Date
    End_Date = statusRequest.End_Date
    ClientRefId = statusRequest.ClientRefId
    Transaction_ID = statusRequest.Transaction_ID

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
                print(query)
                """
                here we will insert iServeU api response data... In Production

                TODO
                """
                values = (
                    statusRequest.ClientRefId,
                    statusRequest.Transaction_ID,
                )
                cursor.execute(query, values)

                columns = [desc[0] for desc in cursor.description]

                transaction_details = cursor.fetchone()

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
                                "txnAmount": int(transaction_details_data["txnAmount"]),
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

    print("Final : ", response_data)

    return response_data


"""
Function to fetch Merchnats Wallet Balance
"""


def fetch_wallet_bal(mcode: str) -> Union[float, None]:
    try:
        conn = connect()

        if conn.is_connected():
            cursor = conn.cursor()
            try:
                conn.start_transaction()
                query = "SELECT balance FROM merchants_wallet WHERE mcode = %s"
                cursor.execute(query, (mcode,))
                balance = cursor.fetchone()
                if balance is not None:
                    return balance[0]  # Return the balance if found
                else:
                    # Return None if merchant not found
                    return None

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
This endpoint will get the merchant's wallet balance
"""


@router.get("/get-balance/{mcode}")
async def get_wallet_balance(mcode: str) -> Union[float, None]:
    try:
        cleared_balance = fetch_wallet_bal(mcode)
        return cleared_balance
    except Exception as err:
        # Handle database errors
        message = f"Error: {err}"
        raise HTTPException(status_code=500, detail=message)
