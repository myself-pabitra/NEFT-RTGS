from fastapi import HTTPException, status
from database.connections import connect
from utilities.utils import (
    generate_reference_number,
    extract_ip_lat_lon,
    generate_transactionId,
)
from mysql.connector import Error


"""
Extra_request_data_from backend to request model..
"""
wallet_transaction_reference = generate_transactionId(15)
wallet_transaction_type = "Dr"


def Insert_transaction_request_data(transaction_data, merchant_id, mcode):

    try:
        # conn = connect()
        with connect() as conn:

            if conn.is_connected():
                # cursor = conn.cursor()
                with conn.cursor() as cursor:
                    try:
                        conn.start_transaction()
                        """
                        Balance check and debiting wallet balnce section of current transaction
                        """
                        query = "SELECT balance FROM merchants_wallet WHERE merchant_id = %s"
                        cursor.execute(query, (merchant_id,))
                        balance = cursor.fetchone()

                        if not balance:
                            raise HTTPException(
                                status_code=status.HTTP_404_NOT_FOUND,
                                detail="Could't fetch wallet balance.",
                            )
                        merchnat_wallet_balance = float(balance[0])
                        requested_balance = transaction_data["requested_balance"]

                        if requested_balance > merchnat_wallet_balance:
                            raise HTTPException(
                                status_code=400,
                                detail="You don't have sufficient wallet balance to perform this transaction",
                            )

                        insert_transaction_request_data_query = "INSERT INTO netbanking_requests (beneName,beneAccountNo,beneifsc,benePhoneNo,beneBankName,clientReferenceNo,amount,fundTransferType,pincode,custName,custMobNo,custIpAddress,merchant_id,mcode,latlong,paramA,paramB) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"

                        transaction_request_data = (
                            transaction_data["beneName"],
                            transaction_data["beneAccountNo"],
                            transaction_data["beneifsc"],
                            transaction_data["benePhoneNo"],
                            transaction_data["beneBankName"],
                            transaction_data["clientReferenceNo"],
                            transaction_data["requested_balance"],
                            transaction_data["fundTransferType"],
                            transaction_data["pincode"],
                            transaction_data["custName"],
                            transaction_data["custMobNo"],
                            transaction_data["custIpAddress"],
                            transaction_data["merchant_id"],
                            transaction_data["mcode"],
                            transaction_data["latlong"],
                            transaction_data["paramA"],
                            transaction_data["paramB"],
                        )

                        cursor.execute(
                            insert_transaction_request_data_query,
                            transaction_request_data,
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


def Insert_transaction_response_data_and_make_wallet_transaction(
    api_response_data, merchant_id, mcode
):
    ISERVEU_status = api_response_data[0]
    ISERVEU_txn_amount = float(api_response_data[11])
    ISERVEU_client_reference_no = api_response_data[10]

    try:
        with connect() as conn:

            if conn.is_connected():

                with conn.cursor() as cursor:

                    try:
                        conn.start_transaction()
                        query = "SELECT balance FROM merchants_wallet WHERE merchant_id = %s"
                        cursor.execute(query, (merchant_id,))
                        balance = cursor.fetchone()

                        if not balance:
                            raise HTTPException(
                                status_code=status.HTTP_404_NOT_FOUND,
                                detail="Could't fetch wallet balance.",
                            )
                        merchnat_wallet_balance = float(balance[0])

                        # Deduct wallet balance only if status is 'SUCCESS' or 'INPROGRESS'
                        if ISERVEU_status in [
                            "SUCCESS",
                            "INPROGRESS",
                        ]:
                            updated_balance = round(
                                merchnat_wallet_balance - ISERVEU_txn_amount, 2
                            )

                            """ Update Wallet Balance if transaction after deduction is transaction is successful """
                            update_balance_query = "UPDATE merchants_wallet SET balance = %s WHERE merchant_id = %s"
                            cursor.execute(
                                update_balance_query, (updated_balance, merchant_id)
                            )

                            """ Do The wallet Transaction """
                            wallet_transaction_query = "INSERT INTO merchant_wallet_transactions (clientReferenceNo,merchant_id,mcode,wallet_transaction_reference,transaction_amount,transaction_type,current_balance) VALUES (%s,%s,%s,%s,%s,%s,%s)"

                            wallet_transaction_data = (
                                ISERVEU_client_reference_no,
                                merchant_id,
                                mcode,
                                wallet_transaction_reference,
                                ISERVEU_txn_amount,
                                wallet_transaction_type,
                                updated_balance,
                            )

                            cursor.execute(
                                wallet_transaction_query, wallet_transaction_data
                            )
                        else:

                            updated_balance = merchnat_wallet_balance  # No deduction if transaction fails

                        insert_transaction_response_data_query = "INSERT INTO netbanking_response (status,subStatus,statusDesc,rrn,transactionId,beneName,beneAccountNo,beneifsc,benePhoneNo,beneBankName,clientReferenceNo,txnAmount,txnType,latlong,pincode,custName,custMobNo,dateTime,paramA,paramB) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"

                        cursor.execute(
                            insert_transaction_response_data_query, api_response_data
                        )
                        conn.commit()

                    except Error as e:
                        conn.rollback()
                        message = f"Error Occoured: {e}"
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
Function to fetch Merchnats Wallet Balance
"""


def fetch_wallet_bal(merchant_id: int):
    try:
        with connect() as conn:

            if conn.is_connected():
                with conn.cursor() as cursor:

                    try:
                        conn.start_transaction()
                        query = "SELECT balance FROM merchants_wallet WHERE merchant_id = %s"
                        cursor.execute(query, (merchant_id,))
                        balance = cursor.fetchone()
                        if balance is not None:
                            return float(balance[0])
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
