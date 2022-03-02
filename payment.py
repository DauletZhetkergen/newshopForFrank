API = '1RE90YM-YTZM0G2-NANNC61-J0H1STZ'
from random import randint

import requests
import json


# API = 'HF36K9W-KJXMJER-H7MG208-ENZPV9M'
TOKEN = "1401709439:AAF1G1VbZKEWg8sVs3OcBQ8hL0GeAsePBuY"


def get_usd_to_btc(amount):
    url = "https://api.nowpayments.io/v1/estimate?amount={}&currency_from=usd&currency_to=btc".format(amount)

    payload = {}
    headers = {
        'x-api-key': API
    }

    response = requests.request("GET", url, headers=headers, data=payload)

    finished_price = response.json()['estimated_amount']
    finished_price = round(float(finished_price),5)
    return finished_price

def get_payment_btc(amount,uid):
    url = "https://api.nowpayments.io/v1/payment"
    price = get_usd_to_btc(amount)
    order_id = random_with_N_digits(5)
    payload = json.dumps({
        "price_amount":amount,
        "price_currency": "usd",
        "pay_amount": price,
        "pay_currency": "btc",
        "ipn_callback_url": "https://api.telegram.org/bot{}/sendMessage?chat_id={}&text='{}$%20is%20deposited%20click%20Check'".format(TOKEN,uid,amount),
        "order_id": order_id,
        "order_description": "Deposit {}".format(amount)
    })
    headers = {
        'x-api-key': API,
        'Content-Type': 'application/json'
    }
    response = requests.request("POST", url, headers=headers, data=payload)
    print(response.text)
    address = response.json()['pay_address']
    payment_id = response.json()['payment_id']
    return address,payment_id,price






def get_usd_to_eth(amount):
    url = "https://api.nowpayments.io/v1/estimate?amount={}&currency_from=usd&currency_to=eth".format(amount)

    payload = {}
    headers = {
        'x-api-key': API
    }

    response = requests.request("GET", url, headers=headers, data=payload)

    finished_price = response.json()['estimated_amount']
    finished_price = round(float(finished_price),5)
    print(finished_price)
    return finished_price

def get_payment_eth(amount,uid):
    url = "https://api.nowpayments.io/v1/payment"
    price = get_usd_to_eth(amount)
    order_id = random_with_N_digits(5)
    payload = json.dumps({
        "price_amount":amount,
        "price_currency": "usd",
        "pay_amount": price,
        "pay_currency": "eth",
        "ipn_callback_url": "https://api.telegram.org/bot{}/sendMessage?chat_id={}&text='{}$%20is%20deposited%20click%20Check'".format(TOKEN,uid,amount),
        "order_id": order_id,
        "order_description": "Deposit {}".format(amount)
    })
    headers = {
        'x-api-key': API,
        'Content-Type': 'application/json'
    }
    response = requests.request("POST", url, headers=headers, data=payload)
    print(response.text)
    address = response.json()['pay_address']
    payment_id = response.json()['payment_id']
    return address,payment_id,price






def random_with_N_digits(n):
    range_start = 10**(n-1)
    range_end = (10**n)-1
    return randint(range_start, range_end)

def check_status_payment(pid):
    url = "https://api.nowpayments.io/v1/payment/{}".format(pid)
    payload = {}
    headers = {
        'x-api-key': API
    }

    response = requests.request("GET", url, headers=headers, data=payload)
    print(response.text)
    if response.json()['payment_status'] == 'finished':
        return True,response.json()['price_amount']
    else:
        return False,response.json()['payment_status']

