from __main__ import app
from flask import Flask, redirect, url_for, render_template, request, send_file, jsonify
import matplotlib.pyplot as plt
from pathlib import Path
import gc

from scripts.utils import read_tle
from scripts.utils import read_current_pos
from scripts.satellite import satellite
from scripts.satellite import satellite_plot

satellites = []
current_pos = [0, 0]
satellites_objects = []

drawing = False
stop_processes = False


@app.route('/stop', methods=['GET', 'POST'])
def stop():
    global stop_processes, drawing
    stop_processes = True
    drawing = False
    return "STOPPED"


@app.route('/auto', methods=['GET', 'POST'])
def auto():
    global satellites, current_pos, satellites_objects, drawing, stop_processes
    data = request.json
    if not drawing:
        print("drawing maps...")
        drawing = True
        for x in range(len(satellites)):
            if not stop_processes:
                name = satellites[x]["name"]
                print(f'drawing map for "{name}"')
                current_pos = read_current_pos.read_current_pos()
                sun_resolution = float(data[x][satellites[x]["name"]]['form_sun_resolution'])
                satellite_resolution = float(data[x][satellites[x]["name"]]['form_satellite_resolution'])
                path_resolution = int(data[x][satellites[x]["name"]]['form_path_resolution'])
                before_time = int(data[x][satellites[x]["name"]]['form_before_time'])
                after_time = int(data[x][satellites[x]["name"]]['form_after_time'])
                draw_sat = False
                if data[x][satellites[x]["name"]]['form_satellite_area']:
                    draw_sat = True
                draw_sun = False
                if data[x][satellites[x]["name"]]['form_sun_area']:
                    draw_sun = True

                plt = satellite_plot.satellite_map(satellites_objects[x],
                                                   current_pos,
                                                   satellite_resolution=satellite_resolution,
                                                   sun_resolution=sun_resolution,
                                                   path_resolution=path_resolution,
                                                   before_time=before_time,
                                                   after_time=after_time,
                                                   draw_sat_area=draw_sat,
                                                   draw_sun_area=draw_sun)
                ROOT_DIR = str(Path(__file__).parent.parent.parent.as_posix())  # This is your Project Root
                plt.savefig(ROOT_DIR + "/static/dynamic_images" + f'/{name}.png')
                print(f'map for "{name}" was created and saved')
                plt.clf()
                plt.close()
                gc.collect()
            else:
                return "STOP"
        drawing = False
        return "SUCCESS"
    else:
        return "WAIT"


@app.route('/draw', methods=['GET', 'POST'])
def draw():
    global satellites, current_pos, satellites_objects, drawing
    data = request.form
    if not drawing:
        drawing = True
        for x in range(len(satellites)):
            if satellites[x]["name"] == data['sat']:
                print(f'drawing map for "{data["sat"]}"')
                current_pos = read_current_pos.read_current_pos()
                sun_resolution = float(data['form_sun_resolution'])
                satellite_resolution = float(data['form_satellite_resolution'])
                path_resolution = int(data['form_path_resolution'])
                before_time = int(data['form_before_time'])
                after_time = int(data['form_after_time'])
                draw_sat = False
                if 'form_satellite_area' in data:
                    draw_sat = True
                draw_sun = False
                if 'form_sun_area' in data:
                    draw_sun = True

                plt = satellite_plot.satellite_map(satellites_objects[x],
                                                   current_pos,
                                                   satellite_resolution=satellite_resolution,
                                                   sun_resolution=sun_resolution,
                                                   path_resolution=path_resolution,
                                                   before_time=before_time,
                                                   after_time=after_time,
                                                   draw_sat_area=draw_sat,
                                                   draw_sun_area=draw_sun)
                ROOT_DIR = str(Path(__file__).parent.parent.parent.as_posix())  # This is your Project Root
                plt.savefig(ROOT_DIR + "/static/dynamic_images" + f'/{data["sat"]}.png')
                plt.close()
                print(f'map for "{data["sat"]}" was created and saved')
                drawing = False
                return "SUCCESS"
    return 'WAIT'


@app.route('/ssm')
def satellite_static_map():
    global satellites, current_pos, satellites_objects
    satellites_tle = read_tle.read_tle()
    satellites_objects = [satellite.satellite(item) for item in satellites_tle]
    current_pos = read_current_pos.read_current_pos()
    satellites = [item.get_informations(current_pos) for item in satellites_objects]
    return render_template("satellite_static_map.html", satellites=satellites)