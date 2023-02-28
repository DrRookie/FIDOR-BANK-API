from requests_oauthlib import OAuth2Session
from flask import Flask, request, redirect, session, url_for, render_template
from requests.auth import HTTPBasicAuth
import requests
import json

rapidCryptoNewsAPI = "fe77cd2360mshf88b261e3ccaf4ap1bec69jsne039ee27b3f7"
alphaApi = "YB0DJHCVODY5QJT1"

#function for getting exchange rate info by giving crypto code as parameter
def cryptoExchangeTO_sgd(fromcrypto):
    
    exchangeRate_url = "https://www.alphavantage.co/query?function=CURRENCY_EXCHANGE_RATE&from_currency=" + \
        fromcrypto+"&to_currency=SGD&apikey=YB0DJHCVODY5QJT1"

            
    headers = {}

    exchangeRate_response = requests.request("GET", exchangeRate_url, headers=headers)
    exchangeRate_Data = json.loads(exchangeRate_response.text)

    currentOneCryptoPriceSGD = "{:.2f}".format(float(exchangeRate_Data["Realtime Currency Exchange Rate"]["5. Exchange Rate"]))
    cryptoPrice = "{:.14f}".format(1/float(currentOneCryptoPriceSGD))

    bidPrice = "{:.2f}".format(float(exchangeRate_Data["Realtime Currency Exchange Rate"]["8. Bid Price"]))
    askPrice = "{:.2f}".format(float(exchangeRate_Data["Realtime Currency Exchange Rate"]["9. Ask Price"]))


    result = [fromcrypto, currentOneCryptoPriceSGD, cryptoPrice, bidPrice, askPrice]
        

    return result

#not in use
def get_coverted_money (priceUSD):

    exchangerateurl = "https://api.apilayer.com/exchangerates_data/convert?to=SGD&from=USD&amount="+str(priceUSD)

    
    headers= {
        "apikey": "a5mjRfSLiNjvohHPGKeDPaEU3SLq00y3"
    }

    exchangerate_response = requests.request("GET", exchangerateurl, headers=headers)
    exchangerate_data = json.loads(exchangerate_response.text)

    #from usd to sgd result 
    covertedamount = "{:.2f}".format(exchangerate_data["result"])

    return float(covertedamount)


#function for getting trading info about crypto by giving the response for api and cryptocode
def get_crypto_info(data, code):
    info = {}

    last_refreshed = data["Meta Data"]["6. Last Refreshed"][:10]
    latest_prices = data['Time Series (Digital Currency Daily)'][last_refreshed]
    latest_closing_price = float(latest_prices["4a. close (SGD)"])


    second_date = list(data['Time Series (Digital Currency Daily)'].keys())[1]
    second_date_Closeprice = float(data['Time Series (Digital Currency Daily)'][second_date]["4a. close (SGD)"])
    percent24Hchange = (((latest_closing_price - second_date_Closeprice))/latest_closing_price)*100
    
    info['code'] = code
    info['full_name'] = data['Meta Data']['3. Digital Currency Name']
    info['closing_price'] = latest_closing_price
    info['volume'] = "{:.2f}".format(float(latest_prices["5. volume"]))
    info['date'] = last_refreshed
    info['percentage_change'] = "{:.4f}".format(percent24Hchange)


    return info

#function for the api for getting the crypto trading Info
def cryptoprice():
    api_key = alphaApi

    urls = {
        'BTC': "https://www.alphavantage.co/query?function=DIGITAL_CURRENCY_DAILY&symbol=BTC&market=SGD&apikey="+api_key,
        'ETH': "https://www.alphavantage.co/query?function=DIGITAL_CURRENCY_DAILY&symbol=ETH&market=SGD&apikey="+api_key,
        'DOT': "https://www.alphavantage.co/query?function=DIGITAL_CURRENCY_DAILY&symbol=DOT&market=SGD&apikey="+api_key,
    }

    cryptos = []
    for code, url in urls.items():
            
        response = requests.get(url)
        data = json.loads(response.text)
        crypto_info = get_crypto_info(data, code)
        cryptos.append(crypto_info)

    return cryptos



def crypto_news():
    #Fetching a protected resource using an OAuth 2 token.
    try:
        token = session['oauth_token']
        url = "https://crypto-news16.p.rapidapi.com/news/top/5"

        headers = {
            'Authorization': "Bearer " + token["access_token"],
	        "X-RapidAPI-Key": rapidCryptoNewsAPI,
	        "X-RapidAPI-Host": "crypto-news16.p.rapidapi.com"
        }

        

        response = requests.request("GET", url, headers=headers)

        print(response.text)

        cryptoNews = json.loads(response.text)

        

        return cryptoNews

    except KeyError:
        print("Key error in services-to return back to index")
        return redirect(url_for('default'))


