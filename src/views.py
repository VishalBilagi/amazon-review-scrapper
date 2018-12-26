from flask import Flask, request, session, redirect, url_for, render_template, flash
from .scrape import *
app = Flask(__name__)

@app.route('/', methods=['GET','POST'])
def index():
    url = str(request.form['amazonURL'])
    print('Incoming link: ' + url)
    getReviewData(url)
    return render_template('index.html')
