import skyfield
from skyfield.api import load, wgs84, EarthSatellite, N, Star, W, load, wgs84
from skyfield import api, almanac

import astropy.coordinates as coord
from astropy.time import Time
import astropy.units as u

from timezonefinder import TimezoneFinder

import numpy as np
import math
from scipy.spatial import ConvexHull, convex_hull_plot_2d

import datetime
import pprint
import pytz
import time


class satellite:
    # in order to create satellite class you must deliver "tle" to it
    def __init__(self, tle):
        ts = load.timescale()
        tle_split = tle.splitlines()
        self.tle = tle
        self.satellite_object = EarthSatellite(tle_split[1], tle_split[2], name=tle_split[0], ts=ts)

    # returns informations about satellite in dict
    # input: [longitude, latitude] of device
    # output: {'name','epoch','lon','lat','alt','azimut','elevation','distance','above'}
    def get_informations(self, current_position):
        ts = load.timescale()
        dt = datetime.datetime.now()
        t = ts.utc(dt.year, dt.month, dt.day, dt.hour, dt.minute)
        days = t - self.satellite_object.epoch

        satellite_name = f'{self.satellite_object.name}'
        if days > 0:
            satellite_epoch = '{:.3f} days away from epoch'.format(days)
        else:
            satellite_epoch = 'WARNING: {:.3f} days after epoch!'.format(days)

        geo = self.get_geo_position()
        satellite_lon = f'lon: {round(geo[0], 2)}°'  # longitude(degress)
        satellite_lat = f'lat: {round(geo[1], 2)}°'  # latitude(degress)
        satellite_alt = f'alt: {round(geo[2], 0)}km'  # altitude(km)

        direction = self.azimut(current_position)
        satellite_az = f'azimut: {round(direction[0], 2)}°'  # azimut
        satellite_elev = f'elevation: {round(direction[1], 2)}°'  # elevation
        satellite_dis = f'distance: {round(direction[2], 2)}km'  # distance
        if direction[3]:  # above horizon
            satellite_above = "satellite above horizon"
        else:
            satellite_above = "satellite below horizon"

        return {"name": satellite_name,
                "epoch": satellite_epoch,
                "lon": satellite_lon,
                "lat": satellite_lat,
                "alt": satellite_alt,
                "azimut": satellite_az,
                "elevation": satellite_elev,
                "distance": satellite_dis,
                "above": satellite_above,
                }

    # returns informations about satellite position in float
    # input: nothing
    # output: [longitude, latitude, altitude]
    def get_geo_position(self):
        ts = load.timescale()
        t = ts.now()
        tle_split = self.tle.splitlines()
        self.satellite_object = EarthSatellite(tle_split[1], tle_split[2], name=tle_split[0], ts=ts)
        geocentric = self.satellite_object.at(t)
        subpoint = wgs84.subpoint(geocentric)
        #                    longitude(degress)                  latitude(degress)                   altitude(km)
        position = [float(subpoint.longitude.degrees), float(subpoint.latitude.degrees), int(subpoint.elevation.km)]
        return position

    # returns informations about satellite pass near device location with given angle
    # input: ([longitude, latitude], time to start simulation, time to end simulation, minimum angle to trigger)
    # output: *[name, rise, culminate, set below]
    def flyby(self, current_position, time_start, time_end, minimum_angle):
        ts = load.timescale()
        #                             lat y               lon x
        geo_coords = wgs84.latlon(current_position[1], current_position[0])
        tf = TimezoneFinder()
        #                                lon x                    lat y
        timezone = tf.timezone_at(lng=current_position[0], lat=current_position[1])
        tz = pytz.timezone(timezone)
        time_offset = datetime.datetime.now(tz).utcoffset().seconds / 3600

        time_start_converted = ts.utc(time_start.year, time_start.month, time_start.day, time_start.hour, time_start.minute)
        time_end_converted = ts.utc(time_end.year, time_end.month, time_end.day, time_start.hour, time_start.minute)

        t, events = self.satellite_object.find_events(geo_coords, time_start_converted, time_end_converted,
                                                      altitude_degrees=minimum_angle)
        flyby_list = []
        row = []
        for ti, event in zip(t, events):
            name = (f'rise above {minimum_angle}°', 'culminate', f'set below {minimum_angle}°')[event]
            #                                  need to add timezone
            corrected_ti = ti.utc_strftime(f'{int(ti.utc.hour + time_offset)}:%M:%S   %d-%b-%Y')
            event_element = [self.satellite_object.name,corrected_ti, name]
            row.append(event_element)
            if event == 2:
                flyby_list.append([row[0][0], row[0][1], row[1][1], row[2][1], self.trajectory_flyby(row[0][1], row[2][1], 50, current_position)])
                row = []

        # returned time is in LOCAL TIME not utc
        return flyby_list

    # returns informations about satellite trajectory at flyby event based on given parameters
    # input: (time in seconds to plot line before satellite, time in seconds to plot after satellite, number of verticies in line   higher = more acurrate, [longitude, latitude] of device)
    # output: [azimut, elevation]
    def trajectory_flyby(self, time_before, time_after, resolution, current_position):
        time_before = datetime.datetime.strptime(time_before, '%H:%M:%S   %d-%b-%Y')
        time_before = abs(time_before - datetime.datetime.now())
        time_after = datetime.datetime.strptime(time_after, '%H:%M:%S   %d-%b-%Y')
        time_after = abs(time_after - datetime.datetime.now())

        print(f'{time_before}  {time_after}')
        print(f'{time_before.total_seconds()}  {time_after.total_seconds()}')

        trajectory_list = []
        ts = load.timescale()
        tf = TimezoneFinder()
        #                               lon x                        lat y
        timezone = tf.timezone_at(lng=current_position[0], lat=current_position[1])
        tz = pytz.timezone(timezone)
        time_offset = datetime.datetime.now(tz).utcoffset().seconds / 3600
        for x in range(resolution):
            part = int((time_after.total_seconds() - time_before.total_seconds()) / resolution)
            dt = datetime.datetime.now()
            #                                     need to subtract time zone
            t = ts.utc(dt.year, dt.month, dt.day, dt.hour - time_offset, dt.minute,
                       dt.second + time_before.total_seconds() + (x * part))
            geo_coords = wgs84.latlon(current_position[1], current_position[0])
            difference = self.satellite_object - geo_coords
            topocentric = difference.at(t)
            alt, az, distance = topocentric.altaz()
            #    aziumut(degrees)  elevation(degrees)
            point_in_time = [az.degrees, alt.degrees]
            trajectory_list.append(point_in_time)
        return trajectory_list

    # returns informations about satellite direction and elevation from device pov
    # input: [longitude, latitude] of device
    # output: [azimut, elevation, distance, above horizon bool]
    def azimut(self, current_position):
        ts = load.timescale()
        t = ts.now()
        #                         lat y                     lon x
        geo_coords = wgs84.latlon(current_position[1], current_position[0])
        difference = self.satellite_object - geo_coords
        topocentric = difference.at(t)
        alt, az, distance = topocentric.altaz()
        above_horizon = False
        if alt.degrees > 0:
            above_horizon = True
        #  aziumut(degrees) elevation(degrees) distance(km)  is above horizon
        return [az.degrees, alt.degrees, int(distance.km), above_horizon]

    # returns informations about satellite trajectory based on given parameters
    # input: (time in seconds to plot line before satellite, time in seconds to plot after satellite, number of verticies in line   higher = more acurrate, [longitude, latitude] of device)
    # output: [longitude, latitude, azimut, elevation]
    def trajectory(self, time_before, time_after, resolution, current_position):
        trajectory_list = []
        ts = load.timescale()
        tf = TimezoneFinder()
        #                               lon x                        lat y
        timezone = tf.timezone_at(lng=current_position[0], lat=current_position[1])
        tz = pytz.timezone(timezone)
        time_offset = datetime.datetime.now(tz).utcoffset().seconds / 3600
        for x in range(resolution):
            part = int((time_after + time_before) / resolution)
            dt = datetime.datetime.now()
            #                                     need to subtract time zone
            t = ts.utc(dt.year, dt.month, dt.day, dt.hour - time_offset, dt.minute,
                       dt.second - time_before + (x * part))
            geocentric = self.satellite_object.at(t)
            subpoint = wgs84.subpoint(geocentric)

            geo_coords = wgs84.latlon(current_position[1], current_position[0])
            difference = self.satellite_object - geo_coords
            topocentric = difference.at(t)
            alt, az, distance = topocentric.altaz()
            #                     longitude(degress)                latitude(degress)       aziumut(degrees)  elevation(degrees)
            point_in_time = [float(subpoint.longitude.degrees), float(subpoint.latitude.degrees), az.degrees,
                             alt.degrees]
            trajectory_list.append(point_in_time)
        return trajectory_list

    # WIP NEED MORE WORK WIP #
    # returns points where is night on earth
    # input: resolution in float (minimum:0.1 optimal:0.2 ultra:1)
    # output: [*[x,y]]
    @staticmethod
    def sun_visible_zone(resolution):
        zone = []
        for y in range(int(180 * resolution)):
            for x in range(int(360 * resolution)):
                loc = coord.EarthLocation(lon=(x / resolution - 180) * u.deg,
                                          lat=(y / resolution - 90) * u.deg)
                now = Time.now()
                altaz = coord.AltAz(location=loc, obstime=now)
                sun = coord.get_sun(now)
                if sun.transform_to(altaz).alt < 0:
                    zone.append([x / resolution - 180, y / resolution - 90])
        return zone

    # returns polygon of area visible from satellite
    # input: resolution in float (minimum:0.1 optimal:0.2 ultra:1)
    # output: [*[x,y]]
    def satellite_visible_zone(self, resolution):
        zone = []
        ts = load.timescale()
        t = ts.now()
        for y in range(int(180 * resolution)):
            for x in range(int(360 * resolution)):
                #                              lat y            lon x
                geo_coords = wgs84.latlon(y / resolution - 90, x / resolution - 180)
                difference = self.satellite_object - geo_coords
                topocentric = difference.at(t)
                alt, az, distance = topocentric.altaz()
                if alt.degrees > 0:
                    zone.append([x / resolution - 180, y / resolution - 90])
        points = np.array(zone)
        hull = ConvexHull(points)
        converted = [
            [points[hull.vertices[x], 0], points[hull.vertices[x], 1]]
            for x in range(len(hull.vertices))
        ]
        converted.append([points[hull.vertices[0], 0], points[hull.vertices[0], 1]])
        return converted


##########################################
#              SCRIPT TEST               #
##########################################
if __name__ == "__main__":
    tle = "NOAA 18 [B] \n1 28654U 05018A   21161.43383936  .00000070  00000-0  62101-4 0  9990 \n2 28654  98.9940 226.2702 0013244 304.1597  55.8318 14.12612725827547"
    #                     lon x                 lat y
    current_position = [18.562670074241918, 54.408011976695924]

    start_time = time.time()
    noaa18 = satellite(tle)
    print("$$$$$$$$$$$$$$$$$")
    # returns satellite informations
    satellite_info = noaa18.get_informations(current_position)
    print(satellite_info['name'])
    print(satellite_info['epoch'])
    print(satellite_info['lon'])
    print(satellite_info['lat'])
    print(satellite_info['alt'])
    print(satellite_info['azimut'])
    print(satellite_info['elevation'])
    print(satellite_info['distance'])
    print(satellite_info['above'])

    print("$$$$$$$$$$$$$$$$$")
    # returns satellite lon lat and altitude
    #  lon x  lat y
    print(noaa18.get_geo_position())
    print("$$$$$$$$$$$$$$$$$")
    #  returns a aziumut and elevation of as talite from device position pov
    #  (current device lat lon)
    print(noaa18.azimut(current_position))
    print("$$$$$$$$$$$$$$$$$")
    #  returns a list of flyby near given position
    #  (current device position, timestamp from script will start counting, timestamp from script will stop counting, minmum angle to trigger)
    pprint.pprint(noaa18.flyby(current_position, datetime.datetime.now(), datetime.datetime.now() + datetime.timedelta(days=3),45))
    print("$$$$$$$$$$$$$$$$$")
    #  returns a list of points that satellite will pass in given time (line)
    # [lon x, lat y, aziumut, elevation]
    #  (time before satellite, time after satellite, resolution-points on track)
    # pprint.pprint(noaa18.trajectory(0, 4 * 60 * 60, 100, current_position))
    # print("$$$$$$$$$$$$$$$$$")

    #####################################################
    #  using all that gathered data to plot it on map   #
    #####################################################
    import satellite_plot
    from pathlib import Path
    from PIL import Image

    satellite_resolution = 0.2
    sun_resolution = 0.1
    map = satellite_plot.satellite_map(noaa18, current_position)

    ROOT_DIR = str(Path(__file__).parent.parent.parent.as_posix())  # This is your Project Root
    map.savefig(ROOT_DIR+"/static/dynamic_images"+"/map.png")
    end_time = time.time()
    print(f'time elapsed: {round((end_time - start_time), 2)} seconds')

    im = Image.open(ROOT_DIR+"/static/dynamic_images"+"/map.png")
    im.show()
