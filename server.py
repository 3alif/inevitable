import os
from flask import Flask, render_template
from threading import Thread
from waitress import serve

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/tos')
def tos():
    return render_template('tos.html')

@app.route('/privacy')
def privacy():
    return render_template('privacy.html')

def run():
  port = int(os.environ.get('PORT', 8080))
  serve(app, host='0.0.0.0', port=port)

def online():
    t = Thread(target=run)
    t.daemon = True
    t.start()