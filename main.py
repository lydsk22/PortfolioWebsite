import smtplib
from datetime import date
from flask import Flask, abort, render_template, redirect, url_for, flash, request, send_from_directory
from flask_bootstrap import Bootstrap5
from flask_ckeditor import CKEditor
from flask_gravatar import Gravatar
from flask_login import UserMixin, login_user, LoginManager, current_user, logout_user
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship, DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Text
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
import os

# Optional: add contact me email functionality (Day 60)
import smtplib

'''
Make sure the required packages are installed: 
Open the Terminal in PyCharm (bottom left). 

On Windows type:
python -m pip install -r requirements.txt

On MacOS type:
pip3 install -r requirements.txt

This will install the packages from the requirements.txt for this project.
'''

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('FLASK_KEY')
ckeditor = CKEditor(app)
Bootstrap5(app)


@app.route('/')
def home():
    return render_template("index.html", status="home")


@app.route("/about")
def about():
    return render_template("about.html", status="about")


@app.route("/resume", methods=["GET", "POST"])
def resume():
    return render_template("resume.html", status="resume")


@app.route('/download')
def download():
    return send_from_directory('static', path="files/LydiaKidwell_Resume_2025.pdf")

@app.route("/projects")
def projects():
    return render_template("projects.html", status="projects")


MAIL_ADDRESS = os.environ.get("MY_EMAIL")
MAIL_APP_PW = os.environ.get("MY_EMAIL_PASS")


@app.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        data = request.form
        send_email(data["name"], data["email"], data["phone"], data["message"])
        return render_template("contact.html", msg_sent=True, status="contact")
    return render_template("contact.html", msg_sent=False, status="contact")


def send_email(name, email, phone, message):
    email_message = f"Subject:New Message\n\nName: {name}\nEmail: {email}\nPhone: {phone}\nMessage:{message}"
    with smtplib.SMTP("smtp.gmail.com") as connection:
        connection.starttls()
        connection.login(MAIL_ADDRESS, MAIL_APP_PW)
        connection.sendmail(MAIL_ADDRESS, MAIL_APP_PW, email_message)


if __name__ == "__main__":
    app.run(debug=True, port=5001)
