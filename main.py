import requests
import time
import random
import string
import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

# 2Captcha API Key
API_KEY = '2_captcha_key'
SITE_KEY = '6LdlrVYUAAAAAOHEyZRW90UOilvrHDj9T1S_Vkig'  # extracted from the URL
PAGE_URL = 'https://na.redmagic.gg/'  # base URL for the CAPTCHA challenge
POST_URL = 'https://workflow.fastgrowth.app/raffle/rm_10pro_teasing/prize/draw'


# Function to generate a random email with the specified domain
def generate_random_email(domain="your_catchall_email_domain.app"):
    random_string = ''.join(
        random.choices(string.ascii_lowercase + string.digits, k=10))
    return f"{random_string}@{domain}"


# Function to handle a single CAPTCHA solve and post request
def solve_captcha_and_submit():
    # Step 1: Submit CAPTCHA solution request to 2Captcha
    captcha_id_request = requests.post(
        f"http://2captcha.com/in.php?key={API_KEY}&method=userrecaptcha&googlekey={SITE_KEY}&pageurl={PAGE_URL}"
    )
    if "OK|" in captcha_id_request.text:
        captcha_id = captcha_id_request.text.split('|')[1]
    else:
        print("Error in CAPTCHA submission:", captcha_id_request.text)
        time.sleep(10)  # Wait before retrying
        return

    # Step 2: Poll for CAPTCHA solution
    captcha_token = None
    for _ in range(30):
        time.sleep(3)  # Wait before checking for completion
        captcha_result = requests.get(
            f"http://2captcha.com/res.php?key={API_KEY}&action=get&id={captcha_id}"
        )
        if captcha_result.text.startswith('OK|'):
            captcha_token = captcha_result.text.split('|')[1]
            break
        elif captcha_result.text != 'CAPCHA_NOT_READY':
            print("CAPTCHA error:", captcha_result.text)
            time.sleep(1)  # Wait before retrying
            return

    if captcha_token:
        # Step 3: Send POST request with CAPTCHA token
        headers = {
            "accept": "*/*",
            "accept-language": "en-US,en;q=0.9",
            "content-type": "application/json",
            "origin": PAGE_URL,
            "referer": PAGE_URL,
            "user-agent":
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
            "x-fstln-google-recaptcha-token": captcha_token,
            "x-shopify-shop-domain": "redmagic-na.myshopify.com"
        }
        # Generate a random email for each request
        email = generate_random_email()
        payload = {"email": email, "language_code": "na-en"}

        response = requests.post(POST_URL, headers=headers, json=payload)

        # Decode the response as JSON
        try:
            response_data = response.json()
            prize_info = response_data.get("prize", {})

            # Format the required fields
            prize_tier_key = prize_info.get("prize_tier_key", "N/A")
            code = prize_info.get("code", "N/A")
            email = prize_info.get("email", "N/A")
            status = prize_info.get("status", "N/A")

            # Write the formatted output to results.txt
            with open("results.txt", "a") as file:
                file.write(f"{prize_tier_key}:{code}:{email}:{status}\n")

            print("Result saved:", prize_tier_key, code, email, status)
        except json.JSONDecodeError:
            print("Failed to decode response as JSON:", response.text)


# Main function to handle multiple threads
def main():
    with ThreadPoolExecutor(max_workers=5) as executor:
        while True:
            # Submit up to 5 tasks at a time
            futures = [
                executor.submit(solve_captcha_and_submit) for _ in range(5)
            ]
            # Wait for each task to complete
            for future in as_completed(futures):
                future.result()  # Process any raised exceptions

            # Add a delay between batches of requests to avoid spamming
            time.sleep(10)


# Run the main function
if __name__ == "__main__":
    main()
