import requests
from fastapi import HTTPException, status
from database.settings import (
    CASH_TRANSFER_API_ENDPOINT,
    TRANSACTION_REPORT_ENDPOINT,
    CLIENT_ID,
    CLIENT_SECRET,
)


def make_payout_api_request(transaction_data):
    headers = {
        "Content-Type": "application/json",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
    }
    payload = {
        "beneName": transaction_data["beneName"],
        "beneAccountNo": transaction_data["beneAccountNo"],
        "beneifsc": transaction_data["beneifsc"],
        "benePhoneNo": int(transaction_data["benePhoneNo"]),
        "beneBankName": transaction_data["beneBankName"],
        "clientReferenceNo": transaction_data["clientReferenceNo"],
        "amount": transaction_data[
            "requested_balance"
        ],  # its already in float from pydantic model
        "fundTransferType": transaction_data["fundTransferType"],
        "latlong": transaction_data["latlong"],
        "pincode": int(transaction_data["pincode"]),
        "custName": transaction_data["custName"],
        "custMobNo": int(transaction_data["custMobNo"]),
        "custIpAddress": transaction_data["custIpAddress"],
        "paramA": transaction_data["paramA"],
        "paramB": transaction_data["paramB"],
    }
    try:
        response = requests.post(
            CASH_TRANSFER_API_ENDPOINT, json=payload, headers=headers
        )
        response.raise_for_status()  # Raise an exception for HTTP errors
        return response.json()  # Return the JSON response if the request is successful
    except requests.exceptions.RequestException as e:
        # Handle network errors, connection issues, etc.
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred during the API request: {str(e)}",
        )

    except requests.exceptions.HTTPError as e:
        # Handle API-specific errors (e.g., 400 Bad Request, 403 Forbidden)
        raise HTTPException(status_code=e.response.status_code, detail=e.response.text)

    except KeyError as e:
        # Handle missing keys in API response
        error_message = f"KeyError: Required keys missing in API response: {str(e)}"
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=error_message
        )

    except Exception as e:
        # Handle other unexpected errors
        error_message = f"{str(e)}"
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=error_message
        )


def make_status_api_request(statusRequest):
    headers = {
        "Content-Type": "application/json",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
    }
    Query_Operation = statusRequest.user_status_data.Query_Operation
    Start_Date = statusRequest.user_status_data.Start_Date
    End_Date = statusRequest.user_status_data.End_Date
    ClientRefId = statusRequest.user_status_data.ClientRefId
    Transaction_ID = statusRequest.user_status_data.Transaction_ID

    payload = {
        "$1": Query_Operation,
        "$4": Start_Date,
        "$5": End_Date,
        "$6": ClientRefId,
        "$10": Transaction_ID,
    }
    try:
        response = requests.post(
            TRANSACTION_REPORT_ENDPOINT, json=payload, headers=headers
        )
        iServeU_response_data = response.json()
        return iServeU_response_data
    except requests.RequestException as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )
    except KeyError as e:
        # Handle missing keys in API response
        error_message = f"KeyError: Required keys missing in API response: {str(e)}"
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=error_message
        )
    except Exception as e:
        # Handle other unexpected errors
        error_message = f"{str(e)}"
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=error_message
        )
