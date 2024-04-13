from flask import Flask, render_template, request
from bs4 import BeautifulSoup
import requests
from cachecontrol import CacheControl

from email.mime.text import MIMEText
import smtplib
import traceback

sessionCached = CacheControl(requests.session())
application = Flask(__name__)


@application.route('/', methods=['GET', 'POST'])
def index():
    try:
        r = sessionCached.get('https://www.etax.nat.gov.tw/etw-main/ETW183W1/')
        r.encoding = 'utf-8'
        soup = BeautifulSoup(r.text, "html.parser")
        link = soup.find_all(
            "a",
            {"href": lambda s: s and s.find("/etw-main/ETW183W2_") != -1})[:2]
        link = [x["href"][-5:] for x in link]

        month = request.values.get("month")
        if month is None:
            month = link[0]

        chkRadio = [" active" if month == x else "" for x in link]

        r = sessionCached.get(
            'https://www.etax.nat.gov.tw/etw-main/ETW183W2_' + month)
        r.encoding = 'utf-8'
        soup = BeautifulSoup(r.text, "html.parser")
        prize = {}
        prize[soup.find("th", string="特別獎").parent.td.text.strip()] = "特別獎"
        prize[soup.find("th", string="特獎").parent.td.text.strip()] = "特獎"
        for e in soup.find("th", string="頭獎").parent.td.text.split():
            prize[e] = "頭獎"
        if soup.find("th", string="增開六獎"):
            for e in soup.find("th", string="增開六獎").parent.td.text.split():
                prize["xxxxx" + e] = "增開六獎"

        prize = sorted(prize.items(), key=lambda x: x[0])

        digit = {-1: set(), -2: set(), -3: set()}

        for e in prize:
            for i in digit:
                digit[i] |= set(e[0][i])

        digitMin = min(digit, key=lambda x: len(digit.get(x)))

        bucket = {}
        for e in prize:
            if e[0][digitMin] not in bucket:
                bucket[e[0][digitMin]] = {}
            bucket[e[0][digitMin]][e[0]] = e[1]

        bucket = sorted(bucket.items(), key=lambda x: x[0])

        strMonth = []
        for e in link:
            strMonth.append(e[-2:].lstrip("0") + "-" + str(int(e[-2:]) + 1) +
                            "月" + e[:3])

        return render_template("index.html",
                               bucket=bucket,
                               digitMin=digitMin,
                               link=link,
                               chkRadio=chkRadio,
                               digit=" ".join(sorted(digit[digitMin])),
                               strMonth=strMonth)
    except:
        msg = MIMEText(traceback.format_exc())
        msg["From"] = "jyunkai.hu@gmail.com"
        msg["To"] = "jyunkai.hu@gmail.com"
        msg["Subject"] = "INVOICE CHECKING EXCEPTION OCCURS!!"
        smtp = smtplib.SMTP("smtp.gmail.com", 587)
        smtp.starttls()
        smtp.login("jyunkai.hu@gmail.com", "pdzbinllbhrjcfxm")
        smtp.sendmail(msg["From"], msg["To"], msg.as_string())
        smtp.quit()
