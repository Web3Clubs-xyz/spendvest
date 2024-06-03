
import requests
import os 
from dotenv import load_dotenv
import base64 
from requests.auth import HTTPBasicAuth
import random, string 

load_dotenv()

consumer_key = os.getenv('consumer_key')

consumer_secret = os.getenv('consumer_secret')

concatenated = f"{consumer_key}:{consumer_secret}"

concatenated_bytes = concatenated.encode('utf-8')

print(f"concatinated_bytes is : {concatenated_bytes}")

base64_encoded = base64.b64encode(concatenated_bytes)

print(f"base64 encoding is : {base64_encoded}")

def generate_uid(length=10):
    chars = string.ascii_letters  + string.digits
    uid = "".join(random.choice(chars) for _ in range(length))
    return uid


def get_api_auth_token():
    api_URL  = "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"
    response = requests.get(api_URL, auth=HTTPBasicAuth(consumer_key, consumer_secret))
    print(f"token request response : {response.json()}")
    token = response.json()['access_token']
    print(f"response from api is , {token}")
    return token
    

auth_token = get_api_auth_token()

def reg_ingress_saf_url():
    pass 

def make_stk_push(business_shortcode, online_passkey, timestamp, amount, phone, callback_url):
    """Make an STK push to Daraja API."""
    
    # Encode business_shortcode, online_passkey, and current_time (yyyyMMhhmmss) to base64
    encode_data = f"{business_shortcode}{online_passkey}{timestamp}".encode('utf-8')
    passkey = base64.b64encode(encode_data).decode('utf-8')
    
    try:
        # Get access_token
        access_token = get_api_auth_token()
        
        # STK push request URL
        api_url = "https://sandbox.safaricom.co.ke/mpesa/stkpush/v3/processrequest"
        
        # Put access_token in request headers
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        # Define request body
        request_body = {
            "BusinessShortCode": business_shortcode,
            "Password": passkey,
            "Timestamp": timestamp,  # timestamp format: yyyyMMddHHmmss 
            "TransactionType": "CustomerPayBillOnline",
            "Amount": amount,
            "PartyA": phone,
            "PartyB": business_shortcode,
            "PhoneNumber": phone,
            "CallBackURL": callback_url,
            "AccountReference": "UNIQUE_REFERENCE",
            "TransactionDesc": "Payment to spendvest_bot"
        }
        
        # Make request and catch response
        response = requests.post(api_url, json=request_body, headers=headers)
        
        # Check response code for errors and return response
        if response.status_code > 299:
            return {
                "success": False,
                "message": "Sorry, something went wrong. Please try again later."
            }, 400
        
        # Return a response to the user
        return {
            "data": response.json()
        }, 200
    
    except Exception as e:
        # Catch error and return response
        return {
            "success": False,
            "message": f"Sorry, something went wrong. Please try again. Error: {str(e)}"
        }, 400


sec_cred = "JEl0XH9UcbpbwF4d44/29T6tO07wR3difA0dgRn+xBkbkAXVfvs2bJIA1+Suy3j3I8CQlGEiEeDtn9oOtcZ7UGZJ6diAIhO4HcXL3LmDKfR0A0KkIM5W9H+fsomrzfwGCfN5kJc44H4ES388yGL3cvG/mWP3p875jEIJ7Ib+RCQniETK4n4+P0wKxM0yxiVPs9YVEOC29uAbB6d2u9RRpQa/OumJrYlv/hIJz2CJPpQRcFkufmO/CjMWJXhWP9wChQTaMopI3m8Oeg1+CBUDu+ejpKyr+6zOt7aaC3OVkgSp8jrtCZE165qbYnpGK5FW/+Xas2ocFTogK84IlDcHww=="

def send_business_payment(amount, party_a, party_b):
    url = "https://sandbox.safaricom.co.ke/mpesa/b2c/v1/paymentrequest"

    new_token = get_api_auth_token()
    print(f"new token is : {new_token}")

    headers = {
        "Authorization": f"Bearer {new_token}",
        "Content-Type": "application/json"
    }

    body = {
        "OriginatorConversationID": generate_uid(15),
        "InitiatorName": "testapi",
        "SecurityCredential": sec_cred,
        "CommandID": "BusinessPayment",
        "Amount": amount,
        "PartyA": party_a,
        "PartyB": party_b,
        "Remarks": "testing",
        "QueueTimeOutURL": "https://5099-102-217-172-2.ngrok-free.app/mpesa_callback_timeout",
        "ResultURL": "https://5099-102-217-172-2.ngrok-free.app/mpesa_callback",
        "Occasion": "testing"
    }

    response = requests.post(url, headers=headers, json=body)

    if response.status_code == 200:
        response_data = response.json()
        return response_data
    else:
        print(f"Failed to send payment. Status code: {response.status_code}")
        print(f"Response: {response.text}")
        return None
 

 
if __name__ == "__main__":
    make_stk_push("174379", 
                  "bfb279f9aa9bdbcf158e97dd71a467cd2e0c893059b10f78e6b72ada1ed2c919", 
                  "20240517130554", 
                  10, 
                  "254703103960", 
                  "https://6201-102-217-172-2.ngrok-free.app/mpesa_callback")