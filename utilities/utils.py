import random
import time
import string
import requests
from fastapi import HTTPException


def generate_reference_number(length=15):
    """
    This Function generates unique 15 digits of clientReferenceId
    """
    # Define the set of characters to choose from (only digits)
    valid_chars = string.digits

    # Generate a random string of specified length from the valid characters
    reference_number = "".join(random.choices(valid_chars, k=length))
    print("Generated : ", reference_number)

    return reference_number


# def generate_reference_number(length=15):
#     """
#     This function generates a unique reference number using the current time (hours, minutes, and seconds)
#     and a random string of digits.
#     """
#     # Get the current time
#     current_time = time.localtime()

#     # Extract hours, minutes, and seconds from the current time
#     hh_mm_ss = "{:02d}{:02d}{:02d}".format(
#         current_time.tm_hour, current_time.tm_min, current_time.tm_sec
#     )

#     # Calculate the number of random digits required
#     remaining_length = length - len(hh_mm_ss)

#     # Generate a random string of digits of the specified length
#     random_part = "".join(random.choices("0123456789", k=remaining_length))

#     # Combine the current time string and the random string
#     reference_number = hh_mm_ss + random_part

#     print(reference_number)

#     return reference_number


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
