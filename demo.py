import requests

# ip = requests.get('https://checkip.amazonaws.com').text.strip()
# print(ip)


# async def get_public_ip_lat_lon():
#     return requests.get('https://checkip.amazonaws.com').text.strip()


import requests


def extract_ip_lat_lon():
    try:
        response = requests.get("https://get.geojs.io/v1/ip/geo.json")
        if response.status_code == 200:
            data = response.json()
            ip = data.get("ip")
            latitude = float(data.get("latitude"))
            longitude = float(data.get("longitude"))
            return ip, latitude, longitude
        else:
            print("Error: Failed to fetch data from the geojs api")
            return None, None, None
    except Exception as e:
        print(f"Error: {e}")
        return None, None, None


# Example usage

ip, latitude, longitude = extract_ip_lat_lon()
if ip is not None and latitude is not None and longitude is not None:
    print("IP:", ip)
    print("Latitude:", latitude)
    print("Longitude:", longitude)
else:
    print("Failed to fetch IP, latitude, and longitude.")
