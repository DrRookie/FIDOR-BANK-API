from requests_oauthlib import OAuth2Session
from flask import Flask, request, redirect, session, url_for, render_template
from requests.auth import HTTPBasicAuth
import requests
import json
import extraFunction
import datetime
import random
#importing the economic calender package and login to see the sample 
import tradingeconomics as te
te.login()





app = Flask(__name__)
app.config['SESSION_TYPE'] = 'memcached'
app.config['SECRET_KEY'] = '8fba5619dfeb19176f258a4919dd39b5'

client_id = "9e20266ed3fd1bbf"
client_secret = "8fba5619dfeb19176f258a4919dd39b5"
alphaApi = "YB0DJHCVODY5QJT1"
exchangeRateApi = "a5mjRfSLiNjvohHPGKeDPaEU3SLq00y3"
rapidCryptoNewsAPI = "fe77cd2360mshf88b261e3ccaf4ap1bec69jsne039ee27b3f7"

authorization_base_url = 'https://apm.tp.sandbox.fidorfzco.com/oauth/authorize'
token_url = 'https://apm.tp.sandbox.fidorfzco.com/oauth/token'
redirect_uri = 'http://localhost:5000/callback'


@app.route('/', methods=["GET"])
@app.route('/index', methods=["GET"])
def default():

    try:
        fidor = OAuth2Session(client_id, redirect_uri=redirect_uri)
        authorization_url, state = fidor.authorization_url(
            authorization_base_url)

        print("state is ="+state)
        session['oauth_state'] = state
        print("authorization URL is ="+authorization_url)
        return redirect(authorization_url)
    except KeyError:
        print("Key error in default-to return back to index")
        return redirect(url_for('default'))


@app.route("/callback", methods=["GET"])
def callback():
    try:

        fidor = OAuth2Session(state=session['oauth_state'])
        authorizationCode = request.args.get('code')
        body = 'grant_type="authorization_code&code='+authorizationCode + \
            '&redirect_uri='+redirect_uri+'&client_id='+client_id

        auth = HTTPBasicAuth(client_id, client_secret)
        token = fidor.fetch_token(
            token_url, auth=auth, code=authorizationCode, body=body, method='POST')

        session['oauth_token'] = token
        return redirect(url_for('.services'))

    except KeyError:
        print("Key error in callback-to return back to index")
        return redirect(url_for('default'))


#main page
@app.route("/services", methods=["GET"])
def services():

    try:
        token = session['oauth_token']
        url = "https://api.tp.sandbox.fidorfzco.com/accounts"

        payload = ""
        headers = {
            'Accept': "application/vnd.fidor.de;version=1;text/json",
            'Authorization': "Bearer "+token["access_token"]
        }

        response = requests.request("GET", url, data=payload, headers=headers)
        print("services=" + response.text)
        customersAccount = json.loads(response.text)
        customerDetails = customersAccount['data'][0]
        if customerDetails is None:
            return render_template('not_working.html')
        else:


            customerInformation = customerDetails['customers'][0]
            session['fidor_customer'] = customersAccount

            thing = extraFunction.cryptoprice()
            cryptoNews = extraFunction.crypto_news()

            return render_template('index.html', fID=customerInformation["id"],
                               fFirstName=customerInformation["first_name"], fLastName=customerInformation["last_name"],
                               fAccountNo=customerDetails["account_number"], fBalance=(customerDetails["balance"]/100), cryptos = thing, fcryptoNews = cryptoNews)

    except KeyError:
        print("Key error in services-to return back to index")
        return redirect(url_for('default'))


#selecting and buying crypto
@app.route("/crypto_selection", methods=["GET"])
def crypto_selection():
    return render_template('selecting_crypto.html')
@app.route("/bank_transfer", methods=["GET", "POST"])
def transfer():
    error = None
    if request.method == "POST":
        selectedCrypto = request.form["Cryptocurrency"]
        try:
            customersAccount = session['fidor_customer']
            customerDetails = customersAccount['data'][0]


            list_for_cryptoExchange = extraFunction.cryptoExchangeTO_sgd(selectedCrypto)
            session["bank_transfer"] = list_for_cryptoExchange
            random_list = random.sample(range(1, 101), 10)
            
            return render_template('buying_crypto.html', fFIDORID=customerDetails["id"],
                               fAccountNo=customerDetails["account_number"], fBalance=(customerDetails["balance"]/100), fcryptoEx = list_for_cryptoExchange, frando = random.choice(random_list))

        except KeyError:
            print("Key error in bank_transfer-to return back to index")
            return redirect(url_for('.index'))


#the buy result
@app.route("/process", methods=["POST"])
def process():
    if request.method == "POST":
        token = session['oauth_token']
        customersAccount = session['fidor_customer']
        customerDetails = customersAccount['data'][0]


        fidorID = customerDetails['id']
        custEmail = request.form['customerEmailAdd']
        transferAmt = int(float(request.form['transferAmount'])*100)
        transferRemarks = request.form['transferRemarks']
        transactionID = request.form['transactionID']

        cryptoInfo = session["bank_transfer"]
        crypto_purchased = (float(cryptoInfo[2]) * float(request.form['transferAmount'])) 
        bought_crypto = cryptoInfo[0]
        
        cryptoInfo.append(crypto_purchased)
        session["bank_transfer"] = cryptoInfo


        url = "https://api.tp.sandbox.fidorfzco.com/internal_transfers"

        payload = "{\n\t\"account_id\": \""+fidorID+"\",\n\t\"receiver\": \"" + \
            custEmail+"\",\n\t\"external_uid\": \""+transactionID+"\",\n\t\"amount\": " + \
            str(transferAmt)+",\n\t\"subject\": \""+transferRemarks+"\"\n}\n"

        headers = {
            'Authorization': "Bearer "+token["access_token"],
            'Accept': 'application/vnd.fidor.de;version=1;text/json',
            'Content-Type': 'application/json'
        }

        response = requests.request("POST", url, headers=headers, data=payload)

        print("process="+response.text)

        transactionDetails = json.loads(response.text)
        return render_template('buyResult.html', fTransactionID=transactionDetails["id"],
                               custEmail=transactionDetails["receiver"], fRemarks=transactionDetails["subject"],
                               famount=(
                                   float(transactionDetails["amount"])/100),
                               fRecipientName=transactionDetails["recipient_name"], fcryptoPurchased = crypto_purchased, fcryptobought = bought_crypto)


#transaction history
@app.route("/transaction_details", methods=["GET"])
def transaction_details():
    # Fetching a protected resource using an OAuth 2 token.
    try:
        token = session['oauth_token']
        url = "https://api.tp.sandbox.fidorfzco.com/transactions"

        payload = ""
        headers = {
            'Authorization': "Bearer " + token["access_token"],
            'Accept': "application/vnd.fidor.de;version=1,text/json",
            'Content-Type': "application/json"
        }

        response = requests.request("GET", url, data=payload, headers=headers)

        transactionDetails = json.loads(response.text)
        transactionDetails = transactionDetails['data']

        cryptoInfo = session["bank_transfer"]
        bought_cryptoCODE = cryptoInfo[0]
        bought_cryptoprice = cryptoInfo[1]
      

        transaction_dates = []
        for i in transactionDetails:
            transaction_dates.append(str(i["created_at"]))


        count = 0
        for k in transaction_dates:
            dt = datetime.datetime.fromisoformat(k)
            formattedTime = dt.strftime('%d-%m-%Y %H:%M:%S')
            transaction_dates[count] = formattedTime
            count+=1

        for j in range(len(transaction_dates)):
            transactionDetails[j]["created_at"] = transaction_dates[j]


        return render_template('transactionsPage.html',
                               fDetails=transactionDetails,  fcryptoCode = bought_cryptoCODE, fcryptoprice = bought_cryptoprice
                               )
    except KeyError:
        print("Key error in services-to return back to index")
        return redirect(url_for('default'))


#profile 
@app.route("/profile_details", methods = ["GET"])
def profile_details():
    #Fetching a protected resource using an OAuth 2 token.
    try:
        token = session['oauth_token']
        url = "https://api.tp.sandbox.fidorfzco.com/customers"

        payload = ""
        headers = {
            'Authorization': "Bearer " + token["access_token"],
            'Accept': "application/vnd.fidor.de;version=1,text/json",
            'Content-Type': "application/json"
        }

        response = requests.request("GET", url, data=payload, headers=headers)

        profileDetails = json.loads(response.text)
        profileInformation = profileDetails['data'][0]
        customersAccount = session['fidor_customer']
        customerDetails = customersAccount['data'][0]

        cryptoWallet = session["bank_transfer"]
        bought_cryptoCODE = cryptoWallet[0]
        bought_cryptoprice = cryptoWallet[2]
        cryptopriceSGD = "{:.2f}".format(float(bought_cryptoprice) * float(cryptoWallet[1]))


        return render_template('profilePage.html', fFirstName=profileInformation["first_name"], fAccID = profileInformation["id"], fLastName=profileInformation["last_name"],
                               fEmail=profileInformation["email"],  faccount = profileInformation["account_type"], faccNumber = customerDetails["account_number"], fbalance=(customerDetails["balance"]/100), fcryptocode = bought_cryptoCODE, fcryptoprice = bought_cryptoprice, fcpSGD = cryptopriceSGD)

    except KeyError:
        print("Key error in services-to return back to index")
        return redirect(url_for('default'))

#economic Calender
@app.route("/economicCal", methods = ["GET"])
def economicCal():

    response = te.getCalendarData(importance = '3' ,output_type='df')
    getdate = response.to_dict(orient='records')

    return render_template("economicCal.html", getdate=getdate)


#candlestick chart
@app.route("/graph", methods=["GET"])
def graph():
    return render_template("graph.html")
