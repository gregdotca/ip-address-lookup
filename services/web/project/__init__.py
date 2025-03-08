#!/usr/bin/env python3
from flask import Flask, render_template, request
from time import sleep
import requests

app = Flask(__name__, static_folder="assets")

APP_TITLE = "IP Address Lookup"


@app.route("/<ip_address>", methods=["GET"])
def home_ip(ip_address):
    sleep(0.25)
    page_body = ""

    if ip_address == get_users_ip_address():
        page_body += "<strong>Your Public IP Address</strong><BR>"

    page_body += process_ip_address(ip_address)

    return display_homepage(ip_address, page_body)


@app.route("/", methods=["GET"])
def home():
    sleep(0.25)

    ip_address = get_users_ip_address()

    page_body = "<strong>Your Public IP Address</strong><BR>"
    page_body += process_ip_address(ip_address)

    return display_homepage(ip_address, page_body)


@app.route("/", methods=["POST"])
def home_post():
    page_body = ""

    sleep(0.25)

    submitted_ip_address = str(request.form["ip_address"])

    if submitted_ip_address == "":
        submitted_ip_address = get_users_ip_address()

    if submitted_ip_address == get_users_ip_address():
        page_body += "<strong>Your Public IP Address</strong><BR>"

    page_body += process_ip_address(submitted_ip_address)

    return display_homepage(submitted_ip_address, page_body)


def get_users_ip_address():
    return request.environ.get("HTTP_X_FORWARDED_FOR", request.remote_addr)


def process_ip_address(ip_address):
    page_body = ""

    try:
        api_url = "http://ip-api.com/json/" + ip_address
        result = requests.get(api_url).json()

        page_body += "<strong>" + result["query"] + "</strong><BR>"
        page_body += "ISP: " + result["isp"] + "<BR>"
        page_body += "Org: " + result["org"] + "<BR>"
        page_body += "AS: " + result["as"] + "<BR>"
        page_body += (
            "Location: <strong>"
            + result["city"]
            + ", "
            + result["regionName"]
            + " ("
            + result["region"]
            + ")"
            + ", "
            + result["country"]
            + " ("
            + result["countryCode"]
            + ")"
            + "</strong>"
            + "<BR>"
        )
        page_body += "Postal Code: " + result["zip"] + "<BR>"
        page_body += "Time Zone: " + result["timezone"] + "<BR>"
        page_body += (
            "Latitude & Longitude: "
            + str(result["lat"])
            + ", "
            + str(result["lon"])
            + "<BR>"
        )

        # result = result.replace("success\n", "")
        # result = result.replace("\n", "<BR>")
        # page_body += result

    except Exception:
        page_body += "Unable to lookup IP address, please try again."

    return page_body


def display_homepage(ip_address, page_body):
    return render_template(
        "home.html", app_title=APP_TITLE, ip_address=ip_address, page_body=page_body
    )


if __name__ == "__main__":
    app.run()
