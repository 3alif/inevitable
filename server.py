import os
from flask import Flask
from threading import Thread
from waitress import serve

app = Flask('')

@app.route('/')
def home():
    return "Imma Alive"

def run():
  port = int(os.environ.get('PORT', 8080))
  serve(app, host='0.0.0.0', port=port)

def online():
    t = Thread(target=run)
    t.daemon = True
    t.start()