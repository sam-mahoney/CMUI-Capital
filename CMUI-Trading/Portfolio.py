# CMUI Trading
# By Sam Mahoney

# TODO
# Webapp? nah
# Add new assets? nah
# Add price alerts!
# Add holding alerts!
# Log File!

import mysql.connector as mysql
import requests
from bs4 import BeautifulSoup
import time
import schedule
import datetime
import smtplib




class CryptoFetch:
    """The class to monitor prices and send updates"""
    def __init__(self):
        # connect to db// Change these values
        self.conn = mysql.connect(host="ip",
                                    user="user",
                                    passwd="pass",
                                    db="db")
        self.cursor = self.conn.cursor()
        pricepage = requests.get("https://coinmarketcap.com/all/views/all/").text
        self.pricepage = BeautifulSoup(pricepage, 'lxml')
        self.forexurl = "https://api.ratesapi.io/api/latest?base=USD&symbols=GBP"



    def currencyConverter(self):
        #GET REQUEST TO API TO FETCH EXCHANGE RATE
        rateData = requests.get(self.forexurl)
        #CONVERT DATA TO FLAOT
        rate = float(rateData.text[29:39])
        sqlq = "SELECT holdings.individualHoldings, id FROM holdings"
        self.cursor.execute(sqlq)
        holdings = self.cursor.fetchall()
        sHolding = round((float(holdings[0][0]) * rate), 2)
        tHoldings = round((float(holdings[1][0]) * rate), 2)
        sqlq = "SELECT total.total FROM total"
        self.cursor.execute(sqlq)
        totals = self.cursor.fetchall()
        total = round((float(totals[0][0]) * rate), 2)
        sqlq = "UPDATE total SET total.total = {0} WHERE total.id = 1".format(total)
        self.cursor.execute(sqlq)
        sqlq = "UPDATE holdings SET holdings.individualHoldings = {0} WHERE holdings.user_id = 1".format(sHolding)
        self.cursor.execute(sqlq)
        sqlq = "UPDATE holdings SET holdings.individualHoldings = {0} WHERE holdings.user_id = 2".format(tHoldings)
        self.cursor.execute(sqlq)
        self.conn.commit()


    def updatePrices(self):
        print()
        time.sleep(2)
        print("[*] Updating Prices!")
        print("-------------------------")
        coins = ["id-ethereum", "id-icon", "id-enjin-coin", "id-get-protocol", "id-ark"]
        for x in coins:
            table = self.pricepage.find('table', id='currencies-all')
            for row in table.find_all("tr", id=x):
                try:
                    symbol = row.find('td', class_='text-left col-symbol').text
                    price = row.find('a', class_='price').text
                except AttributeError:
                    continue
            price = float(price[1:])
            try:
                sqlq = "UPDATE portfolio SET portfolio.CurrentPrice = {0} WHERE portfolio.Asset = '{1}'".format(price, symbol)
                self.cursor.execute(sqlq)
                print("[$] ", symbol, price)
                print("-------------------------")
            except Exception as e:
                print(e)
                continue
        self.conn.commit()
        print("[*] Prices Updated Successfully")

    def percentageHoldings(self):
        # get the percentage holdings
        print()
        print("[*] Updating Percentage Holdings")
        # Get invested
        sqlq = "SELECT holdings.investment FROM holdings"
        self.cursor.execute(sqlq)
        investment = self.cursor.fetchall()
        s = float(investment[0][0])
        t = float(investment[1][0])
        totali = s + t
        spercent = round(s / totali, 3) * 100
        tpercent = round(t / totali, 3) * 100
        sqlq = "UPDATE holdings SET holdings.percentage = {0} WHERE holdings.user_id = {1}".format(spercent, 1)
        self.cursor.execute(sqlq)
        sqlq = "UPDATE holdings SET holdings.percentage = {0} WHERE holdings.user_id = {1}".format(tpercent, 2)
        self.cursor.execute(sqlq)
        self.conn.commit()

    def oldPriceUpdate(self):
        print()
        print("[*] Updating Old Prices")
        # Percentage increase from last check
        sqlq = "SELECT id, CurrentPrice FROM portfolio"
        self.cursor.execute(sqlq)
        oldPriceData = self.cursor.fetchall()
        for data in oldPriceData:
            portfolioId = int(data[0])
            oldPrice = float(data[1])
            sqlq = "UPDATE portfolio SET portfolio.OldPrice = {0} WHERE portfolio.id = {1}".format(oldPrice, portfolioId)
            self.cursor.execute(sqlq)
        self.conn.commit()

    def percentageChange(self):
        print()
        print("[*] Updating percentage Change")
        # Calculates the percentage change from last week
        sqlq = "SELECT portfolio.CurrentPrice, portfolio.OldPrice, portfolio.id FROM portfolio"
        self.cursor.execute(sqlq)
        priceList = self.cursor.fetchall()
        for prices in priceList:
            currentPrice = float(prices[0])
            oldPrice = float(prices[1])
            portfolioId = int(prices[2])
            percentageChange = round(((currentPrice - oldPrice) / oldPrice * 100), 3)
            sqlq = "UPDATE portfolio SET portfolio.PercentageChange = {0} WHERE portfolio.id = {1}".format(percentageChange, portfolioId)
            self.cursor.execute(sqlq)
        self.conn.commit()


    def oldHoldingUpdate(self):
        print()
        print("[*] Calculating the Percentage Increase on Individual Holdings")
        sqlq = "SELECT user_id, individualHoldings FROM holdings"
        self.cursor.execute(sqlq)
        oldHoldingsData = self.cursor.fetchall()
        for data in oldHoldingsData:
            userId = int(data[0])
            oldHoldings = float(data[1])
            sqlq = "UPDATE holdings SET holdings.OldHoldings = {0} WHERE holdings.user_id = {1}".format(oldHoldings,
                                                                                                   userId)
            self.cursor.execute(sqlq)
        self.conn.commit()


    def holdingPercentageChange(self):
        # Percentage Change
        sqlq = "SELECT user_id, individualHoldings, OldHoldings FROM holdings"
        self.cursor.execute(sqlq)
        percentageData = self.cursor.fetchall()
        for data in percentageData:
            userId = int(data[0])
            iHoldings = float(data[1])
            oHoldings = float(data[2])
            percentageChange = round(((iHoldings - oHoldings) / oHoldings * 100), 3)
            sqlq = "UPDATE holdings SET holdings.PercentageChange = {0} WHERE holdings.user_id = {1}".format(
                percentageChange, userId)
            self.cursor.execute(sqlq)

        self.conn.commit()



    def emailer(self):
        print()
        print("[*] Sending Weekly Update")
        #fetch emails
        gmail_sender = 'cmuicaptial@gmail.com'
        gmail_passwd = 'Trading1234'
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.ehlo()
        server.starttls()
        server.login(gmail_sender, gmail_passwd)

        sqlq = "SELECT Name, email, id FROM accounts"
        self.cursor.execute(sqlq)
        emailData = self.cursor.fetchall()

        for account in emailData:
            user = account[0]
            email = account[1]
            userId = int(account[2])
            sqlq = "SELECT individualHoldings, PercentageChange FROM holdings WHERE user_id = {}".format(userId)
            self.cursor.execute(sqlq)
            holdings = self.cursor.fetchone()
            sqlq = "SELECT PercentageReturn FROM total"
            self.cursor.execute(sqlq)
            preturn = self.cursor.fetchone()
            preturn = preturn[0]
            iHoldings = holdings[0]
            pChange = holdings[1]

            TO = email
            SUBJECT = 'CMUI Capital Update'

            TEXT = 'Hi {0}!\nYour weekly update is below! \n \nPercentage Change: {1}% \nTotal Holdings: GBP:{2} \nTotal Return: {3}% \n \n CMUI Capital Automated System'.format(user, pChange, iHoldings, preturn )

            BODY = '\r\n'.join(['To: %s' % TO,
                                'From: %s' % gmail_sender,
                                'Subject: %s' % SUBJECT,
                                '', TEXT])
            try:
                server.sendmail(gmail_sender, [TO], BODY)
                print('[!] Email Sent To {0} with address {1}'.format(user, email))
            except Exception as e:
                print(e)

        server.quit()

    def profitCalc(self):
        #Calculate Profits
        print()
        print("[*] Calculating Profit")
        self.cursor.execute("SELECT total.Total, total.Invested FROM total")
        data = self.cursor.fetchone()
        holdings = int(data[0])
        invested = int(data[1])
        sum = (holdings - invested) / invested
        preturn = sum * 100
        preturn = round(preturn, 2)
        sqlq = "UPDATE total SET PercentageReturn = {}".format(preturn)
        self.cursor.execute(sqlq)
        self.conn.commit()

    def totalCalcHoldings(self):
        print()
        # Calculates Total Holding
        data = []
        print("[*] Calculating Totals")
        sqlq = "SELECT portfolio.Holdings, portfolio.CurrentPrice, portfolio.Asset FROM portfolio"
        self.cursor.execute(sqlq)
        sum = self.cursor.fetchall()
        for data in sum:
            total = data[0] * data[1]
            total = round(total, 2)
            sqlq = "UPDATE portfolio SET portfolio.Total = {0} WHERE portfolio.Asset = '{1}'".format(total, data[2])
            self.cursor.execute(sqlq)
        self.conn.commit()
        sqlq = "SELECT SUM(portfolio.Total) AS TotalHoldings FROM portfolio;"
        self.cursor.execute(sqlq)
        TotalHoldings = self.cursor.fetchone()
        TotalHoldings = round(TotalHoldings[0], 2)
        sqlq = "UPDATE total SET Total = {}".format(TotalHoldings)
        self.cursor.execute(sqlq)
        #Calc individual holdings

        sqlq = "SELECT user_id, percentage FROM holdings"
        self.cursor.execute(sqlq)
        holdingData = self.cursor.fetchall()
        for user in holdingData:
            userId = user[0]
            percentage = user[1]
            holdings = (percentage / 100) * TotalHoldings
            sqlq = "UPDATE holdings SET individualHoldings = {0} WHERE holdings.user_id = {1}".format(holdings, userId)
            self.cursor.execute(sqlq)
        self.conn.commit()


def weekly():
    print("[!] Running Weekly Task")
    weeklyUpdate = CryptoFetch()
    weeklyUpdate.updatePrices()
    weeklyUpdate.totalCalcHoldings()
    weeklyUpdate.currencyConverter()
    weeklyUpdate.percentageChange()
    weeklyUpdate.holdingPercentageChange()
    weeklyUpdate.emailer()
    weeklyUpdate.oldHoldingUpdate()
    weeklyUpdate.oldPriceUpdate()
    timestamp = datetime.datetime.now().strftime("%A, %d. %B %Y %I:%M%p")
    print("-------------------------")
    print("[!] Weekly Update Finished @ ", timestamp)
    print("-------------------------")
    return



def hourly():
    print("[!] Running Hourly Task")
    hourlyCypto = CryptoFetch()
    hourlyCypto.updatePrices()
    hourlyCypto.percentageChange()
    hourlyCypto.totalCalcHoldings()
    hourlyCypto.currencyConverter()
    hourlyCypto.percentageHoldings()
    hourlyCypto.profitCalc()
    hourlyCypto.holdingPercentageChange()
    timestamp = datetime.datetime.now().strftime("%A, %d. %B %Y %I:%M%p")
    print("-------------------------")
    print("[!] Hourly Update Finished @ ", timestamp)
    print("-------------------------")
    return

def main():
    print("""
   _____ __  __ _    _ _____    _____            _ _        _ 
  / ____|  \/  | |  | |_   _|  / ____|          (_) |      | |
 | |    | \  / | |  | | | |   | |     __ _ _ __  _| |_ __ _| |
 | |    | |\/| | |  | | | |   | |    / _` | '_ \| | __/ _` | |
 | |____| |  | | |__| |_| |_  | |___| (_| | |_) | | || (_| | |
  \_____|_|  |_|\____/|_____|  \_____\__,_| .__/|_|\__\__,_|_|
                                          | |                 
                                          |_|                 
    """)

    schedule.every().monday.at("06:05").do(weekly)
    schedule.every().hour.do(hourly)
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == '__main__':
    main()
