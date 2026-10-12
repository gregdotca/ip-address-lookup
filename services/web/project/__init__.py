#!/usr/bin/env python3
import requests
from urllib.parse import quote
from flask import Flask, redirect, render_template, request, url_for
from time import sleep
from werkzeug.middleware.proxy_fix import ProxyFix

app = Flask(__name__, static_folder="assets")

# prod runs behind one reverse proxy (Caddy), so trust only the last
# X-Forwarded-For entry, the one that proxy adds
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1)

APP_TITLE = "IP Address Lookup"

# seconds to wait for ip-api before showing the error
API_TIMEOUT = 5

RESULT_FIELDS = (
    "query",
    "isp",
    "org",
    "as",
    "city",
    "regionName",
    "region",
    "country",
    "countryCode",
    "zip",
    "timezone",
    "lat",
    "lon",
)


@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "GET":
        ip_address = get_user_ip_address()
    else:
        ip_address = str(request.form["ip_address"]).strip()

        if ip_address == "":
            return redirect(url_for("home"))

    # url_for() encodes the address, so the redirect always stays on this site
    return redirect(url_for("home_ip", ip_address=ip_address))


@app.route("/<ip_address>", methods=["GET"])
def home_ip(ip_address):
    sleep(0.25)
    is_user_ip = ip_address == get_user_ip_address()
    result = lookup_ip_address(ip_address)

    return display_homepage(ip_address, is_user_ip, result)


def get_user_ip_address():
    return request.remote_addr


def lookup_ip_address(ip_address):
    try:
        # encode the address so it can't add a path or query string to the request
        api_url = "http://ip-api.com/json/" + quote(ip_address, safe="")
        result = requests.get(api_url, timeout=API_TIMEOUT).json()

        if result["status"] != "success":
            return None

        if any(field not in result for field in RESULT_FIELDS):
            return None

        return result

    except Exception:
        return None


def display_homepage(ip_address, is_user_ip, result):
    return render_template(
        "home.html",
        app_title=APP_TITLE,
        ip_address=ip_address,
        is_user_ip=is_user_ip,
        result=result,
    )


if __name__ == "__main__":
    app.run()
