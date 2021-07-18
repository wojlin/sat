from __main__ import app
from flask import Flask, redirect, url_for, render_template, request, send_file, jsonify
import matplotlib.pyplot as plt
from pathlib import Path
import gc
import datetime

from scripts.utils import read_tle
from scripts.utils import read_current_pos
from scripts.satellite import satellite
from scripts.satellite import satellite_plot

satellites = []
current_pos = [0, 0]
satellites_objects = []


def update_sats():
    global satellites, current_pos, satellites_objects
    satellites_tle = read_tle.read_tle()
    satellites_objects = [satellite.satellite(item) for item in satellites_tle]
    current_pos = read_current_pos.read_current_pos()
    satellites = [item.get_informations(current_pos) for item in satellites_objects]

@app.route('/sfr_update', methods=['POST', 'GET'])
def satellite_flyby_radar_update():
    global satellites, current_pos, satellites_objects
    update_sats()
    data = request.json
    sats_data = []
    sats_pos = []
    for item in data[1]:
        if item[1]:
            for sat in satellites_objects:
                sats_pos.append(sat.azimut(current_pos))
                if sat.satellite_object.name == item[0]:
                    time_now = datetime.datetime.now()
                    sat_data = sat.flyby(current_pos, time_now, time_now + datetime.timedelta(hours=int(data[0]["hours"])), int(data[0]["angle"]))
                    sats_data.append(sat_data)

    sats_data = [j for sub in sats_data for j in sub]
    sats_data = sorted(sats_data, key=lambda l:datetime.datetime.strptime(l[1], '%H:%M:%S   %d-%b-%Y'))

    plt = satellite_plot.satellite_radar(sats_data, sats_pos)
    ROOT_DIR = str(Path(__file__).parent.parent.parent.as_posix())  # This is your Project Root
    plt.savefig(ROOT_DIR + "/static/dynamic_images" + f'/radar.png')
    print(f'map for "radar" was created and saved')
    plt.clf()
    plt.close()
    gc.collect()

    print(sats_data)

    print("update")
    return jsonify(sats_data)

@app.route('/sfr')
def satellite_flyby_radar():
    global satellites, current_pos, satellites_objects
    update_sats()
    return render_template("satellite_flyby_radar.html", satellites=satellites)
