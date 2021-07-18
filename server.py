from flask import Flask, redirect, url_for, render_template, request, send_from_directory, jsonify
import scripts.satellite.satellite
import sys
import os

app = Flask(__name__)

from scripts.pages.ssm import satellite_static_map
from scripts.pages.sfr import satellite_flyby_radar

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),'images/favicon.ico', mimetype='image/vnd.microsoft.icon')

@app.route("/")
def index():
    return render_template("index.html")


if __name__ == "__main__":
    app.run()