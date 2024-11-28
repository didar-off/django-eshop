from decimal import Decimal
import requests

def fetch_exchange_rates():
    response = requests.get("https://api.exchangerate-api.com/v4/latest/USD")
    data = response.json()

    return {
        'INR': Decimal(data['rates']['INR']),
        'NGN': Decimal(data['rates']['NGN']),
    }


exchange_rates = fetch_exchange_rates()


def get_usd_to_inr_rate():
    return exchange_rates['INR']

def get_usd_to_ngn_rate():
    return exchange_rates['NGN']


def convert_usd_inr(usd_amount):
    inr_rate = get_usd_to_inr_rate()
    return usd_amount * inr_rate

def convert_usd_kobo(usd_amount):
    ngn_rate = get_usd_to_ngn_rate()
    ngn_amount = usd_amount * ngn_rate
    return int(ngn_amount * 100)

def convert_usd_ngn(usd_amount):
    ngn_rate = get_usd_to_ngn_rate()
    return usd_amount * ngn_rate