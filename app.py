import os
import secrets
import requests
from flask import Flask, redirect, request, session, render_template, url_for
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET", secrets.token_hex(32))

CLIENT_ID = os.environ.get("CLIENT_ID")
CLIENT_SECRET = os.environ.get("CLIENT_SECRET")
REDIRECT_URI = "https://project-zero-production-073d.up.railway.app/callback"

DISCORD_API = "https://discord.com/api"


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/login")
def login():
    state = secrets.token_hex(16)
    session["oauth_state"] = state
    url = (
        f"https://discord.com/oauth2/authorize"
        f"?client_id={CLIENT_ID}"
        f"&redirect_uri={REDIRECT_URI}"
        f"&response_type=code"
        f"&scope=identify"
        f"&state={state}"
    )
    return redirect(url)


@app.route("/callback")
def callback():
    code = request.args.get("code")
    state = request.args.get("state")
    if not code or state != session.get("oauth_state"):
        return "OAuth error", 400

    data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI,
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    r = requests.post(f"{DISCORD_API}/oauth2/token", data=data, headers=headers)
    if r.status_code != 200:
        return f"Token error: {r.text}", 400

    token = r.json()["access_token"]
    user_r = requests.get(
        f"{DISCORD_API}/users/@me",
        headers={"Authorization": f"Bearer {token}"},
    )
    user = user_r.json()

    session["user"] = {
        "id": user["id"],
        "username": user["username"],
        "avatar": user.get("avatar"),
    }
    return redirect(url_for("dashboard"))


@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect(url_for("index"))
    return render_template("dashboard.html", user=session["user"])


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))