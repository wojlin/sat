import matplotlib.pyplot as plt
from matplotlib.ticker import EngFormatter, StrMethodFormatter
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
from matplotlib import gridspec, ticker
import math
import numpy as np
from scipy.spatial import ConvexHull, convex_hull_plot_2d
import time
import os
from pathlib import Path


def satellite_map(satellite,
                  current_position,
                  satellite_resolution=0.1,
                  sun_resolution=0.1,
                  path_resolution=100,
                  before_time=0,
                  after_time=3600,
                  draw_sat_area=False,
                  draw_sun_area=False):
    satellite_info = satellite.get_informations(current_position)
    pos = satellite.get_geo_position()
    current_direction = satellite.azimut(current_position)
    trajectory = satellite.trajectory(before_time, after_time, path_resolution, current_position)

    if draw_sat_area:
        satellite_zone = satellite.satellite_visible_zone(satellite_resolution)
    if draw_sun_area:
        sun_zone = satellite.sun_visible_zone(sun_resolution)

    ROOT_DIR = str(Path(__file__).parent.parent.parent.as_posix())  # This is your Project Root
    img = plt.imread(ROOT_DIR + "/static/images/earth2.jpg")
    fig = plt.figure()
    gs = gridspec.GridSpec(ncols=2, nrows=2, width_ratios=[5, 1],
                           height_ratios=[1, 1])
    # fig, (ax1, ax2) = plt.subplots(1, 2, gridspec_kw={'width_ratios': [4, 1]})
    ax1 = plt.subplot(gs[0:, 0])
    ax2 = plt.subplot(gs[0, 1:], projection='polar')
    ax3 = plt.subplot(gs[1:, 1:])
    fig.tight_layout()
    fig.canvas.set_window_title(satellite_info['name'])
    plt.tight_layout()
    fig.tight_layout()
    plt.subplots_adjust(left=0.05, bottom=0, right=0.95, top=0.99, wspace=0.1, hspace=0.05)
    plt.gcf().set_size_inches(10, 5)
    ax1.margins(0)
    plt.xlim([-180, 180])  # limiting degrees of lon to -180,180
    plt.ylim([-90, 90])  # limiting degrees of lat to -90,90
    ax1.imshow(img, extent=[-180, 180, -90, 90])  # resizing background image to fit box
    ax1.set_xticks([-180, -150, -120, -90, -60, -30, 0, 30, 60, 90, 120, 150, 180])  # visible lon ticks
    ax1.set_yticks([-90, -75, -60, -45, -30, -15, 0, 15, 30, 45, 60, 75, 90])  # visible lat ticks
    ax1.yaxis.set_major_formatter(StrMethodFormatter(u"{x:.0f}°"))
    ax1.xaxis.set_major_formatter(StrMethodFormatter(u"{x:.0f}°"))
    ax1.grid(alpha=0.7)
    # lat
    #
    #
    #
    #
    #
    # # # # # # # # # # # # # # # # # #  lon

    # device             lon (x)             lat(y)
    ax1.plot(current_position[0], current_position[1], marker=".", markersize=20, c='r')

    # sat              lon (x)             lat(y)
    path = ROOT_DIR + '/static/images/satellite.png'
    ab = AnnotationBbox(OffsetImage(plt.imread(path), 0.15),
                        (pos[0], pos[1],), frameon=False)
    ax1.add_artist(ab)

    ax1.plot()

    x_trajectory = [trajectory[item][0] for item in range(len(trajectory))]
    y_trajectory = [trajectory[item][1] for item in range(len(trajectory))]

    x_lines_list = []
    y_lines_list = []

    last_cut = 0
    count = sum(
        x_trajectory[x] < 0 and x_trajectory[x + 1] > 0
        for x in range(len(trajectory) - 1)
    )

    opacity_level = 1 / (count + 1)

    last_cut = 0
    for x in range(len(trajectory) - 1):
        if x_trajectory[x] < 0 and x_trajectory[x + 1] > 0:
            x_copy = x_trajectory
            y_copy = y_trajectory

            x_lines_list.append(x_copy[last_cut:x + 1])
            y_lines_list.append(y_copy[last_cut:x + 1])
            last_cut = x + 1

    x_lines_list.append(x_trajectory[last_cut + 1:])
    y_lines_list.append(y_trajectory[last_cut + 1:])

    if x_lines_list:
        width = 0.0000002
        for item in range(len(x_lines_list)):
            if len(x_lines_list[item]) > 2:
                if x_lines_list[item][0] != 180 and item != 0:
                    x_lines_list[item].insert(0, 180)
                    y_lines_list[item].insert(0, y_lines_list[item][0])

                if x_lines_list[item][-1] != -180 and item != len(x_lines_list) - 1:
                    x_lines_list[item].append(-180)
                    y_lines_list[item].append(y_lines_list[item][-1])

            ax1.plot(x_lines_list[item], y_lines_list[item], c='r', alpha=1 - (item * opacity_level))

            for inside_item in range(len(x_lines_list[item]) - 1):
                u = -(x_lines_list[item][inside_item] - x_lines_list[item][inside_item + 1])
                v = -(y_lines_list[item][inside_item] - y_lines_list[item][inside_item + 1])
                length = np.sqrt(u ** 2 + v ** 2)
                hal = hl = 1. / width * length
                ax1.quiver(x_lines_list[item][inside_item], y_lines_list[item][inside_item], u, v, angles='xy',
                           scale_units='xy', scale=1,
                           headwidth=hl,
                           headaxislength=hal,
                           headlength=hl,
                           width=width,
                           color="r",
                           alpha=1 - (item * opacity_level)
                           )
    else:
        ax1.plot(x_trajectory, y_trajectory, c='r')

        width = 0.0000013
        for inside_item in range(len(x_trajectory) - 1):
            u = -(x_trajectory[inside_item] - x_trajectory[inside_item + 1])
            v = -(y_trajectory[inside_item] - y_trajectory[inside_item + 1])
            length = np.sqrt(u ** 2 + v ** 2)
            hal = hl = 1. / width * length
            ax1.quiver(x_trajectory[inside_item], y_trajectory[inside_item], u, v, angles='xy', scale_units='xy',
                       scale=1,
                       headwidth=hl,
                       headaxislength=hal,
                       headlength=hl,
                       width=width,
                       color="r")

    if draw_sun_area:
        x_sun_zone = [sun_zone[item][0] for item in range(len(sun_zone))]
        y_sun_zone = [sun_zone[item][1] for item in range(len(sun_zone))]
        for x in range(len(x_sun_zone)):
            ax1.plot(x_sun_zone[x], y_sun_zone[x], marker=".", markersize=3 / sun_resolution, c='black', alpha=0.2)

    if draw_sat_area:
        x_zone = [satellite_zone[item][0] for item in range(len(satellite_zone))]
        y_zone = [satellite_zone[item][1] for item in range(len(satellite_zone))]
        ax1.plot(x_zone, y_zone, c='b')
        xs, ys = zip(*satellite_zone)
        ax1.fill(xs, ys, color='b', alpha=0.3)

    ######################################################
    ######################################################
    ######################################################

    ax2.set_thetamin(0)
    ax2.set_thetamax(360)
    ax2.set_theta_zero_location("N")

    ax2.set_theta_direction(-1)

    ax2.set_xticklabels(['N', 'NW', 'W', 'SW', 'S', 'SE', 'E', 'NE'])

    ax2.tick_params(axis='both', which='major', labelsize=10)
    ax2.tick_params(axis='both', which='minor', labelsize=8)

    ax2.set_rlim(90, 0, 1)
    ax2.set_yticks(np.arange(0, 91, 15))
    ax2.set_yticklabels(ax2.get_yticks()[::-1])
    ax2.invert_yaxis()

    if current_direction[1] < 0:
        actual_elev = 90
    else:
        actual_elev = 90 - current_direction[1]

    ax2.plot(math.radians(current_direction[0]), actual_elev, marker=".", markersize=10, c='r')
    path = ROOT_DIR + '/static/images/satellite.png'
    ab = AnnotationBbox(OffsetImage(plt.imread(path), 0.10),
                        (math.radians(current_direction[0]), actual_elev), frameon=False)
    ax2.add_artist(ab)

    x_direction = [trajectory[item][2] for item in range(len(trajectory))]
    y_direction = [trajectory[item][3] for item in range(len(trajectory))]

    x_lines_list = []
    y_lines_list = []

    for item in range(len(x_direction)):
        x_direction[item] = math.radians(x_direction[item])

    for item in reversed(range(len(y_direction))):
        if y_direction[item] < 0:
            pass
            # y_direction.pop(item)
            # x_direction.pop(item)
            # y_direction[item] = 90

        else:
            y_direction[item] = 90 - y_direction[item]

    last_cut = 0
    for x in range(len(x_direction) - 1):
        if x_direction[x] < 0:
            x_copy = x_direction
            y_copy = y_direction

            x_lines_list.append(x_copy[last_cut:x + 1])
            y_lines_list.append(y_copy[last_cut:x + 1])
            last_cut = x + 1

    x_lines_list.append(x_direction[last_cut + 1:])
    y_lines_list.append(y_direction[last_cut + 1:])

    count = len(x_lines_list)

    opacity_level = 1 / (count + 1)

    if x_lines_list:
        width = 0.0000008
        for item in range(len(x_lines_list)):
            if len(x_lines_list[item]) > 2:
                if y_lines_list[item][0] != 90:
                    y_lines_list[item].insert(0, 90)
                    x_lines_list[item].insert(0, x_lines_list[item][0])

                if x_lines_list[item][-1] != 0 and item != len(x_lines_list) - 1:
                    y_lines_list[item].append(90)
                    x_lines_list[item].append(x_lines_list[item][-1])

            ax2.plot(x_lines_list[item], y_lines_list[item], c='r', alpha=1 - (item * opacity_level))

            for inside_item in range(len(x_lines_list[item]) - 1):
                u = -(x_lines_list[item][inside_item] - x_lines_list[item][inside_item + 1])
                v = -(y_lines_list[item][inside_item] - y_lines_list[item][inside_item + 1])
                length = np.sqrt(u ** 2 + v ** 2)
                hal = hl = 1. / width * length
                ax2.quiver(x_lines_list[item][inside_item], y_lines_list[item][inside_item], u, v, angles='xy',
                           scale_units='xy', scale=1,
                           headwidth=hl,
                           headaxislength=hal,
                           headlength=hl,
                           width=width,
                           color="r",
                           alpha=1 - (item * opacity_level)
                           )
    else:
        ax2.plot(x_direction, y_direction, c='r')

        width = 0.0000008
        for inside_item in range(len(x_direction) - 1):
            u = -(x_direction[inside_item] - x_direction[inside_item + 1])
            v = -(y_direction[inside_item] - y_direction[inside_item + 1])
            length = np.sqrt(u ** 2 + v ** 2)
            hal = hl = 1. / width * length
            ax2.quiver(x_direction[inside_item], y_direction[inside_item], u, v, angles='xy', scale_units='xy',
                       scale=1,
                       headwidth=hl,
                       headaxislength=hal,

                       headlength=hl,
                       width=width,
                       color="r")

    ax3.axis('off')
    constant_x = -230
    constant_y = 90
    font = "monospace"
    font_size = 9
    ax3.text(constant_x, constant_y, satellite_info['name'], fontsize=font_size, family=font)
    ax3.text(constant_x, constant_y - 15, satellite_info['lon'], fontsize=font_size, family=font)
    ax3.text(constant_x, constant_y - 30, satellite_info['lat'], fontsize=font_size, family=font)
    ax3.text(constant_x, constant_y - 45, satellite_info['alt'], fontsize=font_size, family=font)
    ax3.text(constant_x, constant_y - 60, satellite_info['azimut'], fontsize=font_size, family=font)
    ax3.text(constant_x, constant_y - 75, satellite_info['elevation'], fontsize=font_size, family=font)
    ax3.text(constant_x, constant_y - 90, satellite_info['distance'], fontsize=font_size, family=font)
    ax3.text(constant_x, constant_y - 105, satellite_info['above'], fontsize=font_size, family=font)
    ax3.text(constant_x, constant_y - 120, satellite_info['epoch'], fontsize=font_size, family=font)
    return plt


def satellite_radar(sats_data, stats_pos):

    trajectory = sats_data[3]

    ROOT_DIR = str(Path(__file__).parent.parent.parent.as_posix())  # This is your Project Root
    fig = plt.figure()
    ax1 = plt.subplot(projection='polar')
    fig.tight_layout()
    fig.canvas.set_window_title("radar")
    plt.tight_layout()
    fig.tight_layout()
    plt.subplots_adjust(left=0.05, bottom=0.05, right=0.95, top=0.95, wspace=0.1, hspace=0.05)
    plt.gcf().set_size_inches(10, 5)


    ax1.set_thetamin(0)
    ax1.set_thetamax(360)
    ax1.set_theta_zero_location("N")

    ax1.set_theta_direction(-1)

    ax1.set_xticklabels(['N', 'NW', 'W', 'SW', 'S', 'SE', 'E', 'NE'])

    ax1.tick_params(axis='both', which='major', labelsize=10)
    ax1.tick_params(axis='both', which='minor', labelsize=8)

    ax1.set_rlim(90, 0, 1)
    ax1.set_yticks(np.arange(0, 91, 15))
    ax1.set_yticklabels(ax1.get_yticks()[::-1])
    ax1.invert_yaxis()

    plt.show()

    if current_direction[1] < 0:
        actual_elev = 90
    else:
        actual_elev = 90 - current_direction[1]

    ax1.plot(math.radians(current_direction[0]), actual_elev, marker=".", markersize=10, c='r')
    path = ROOT_DIR + '/static/images/satellite.png'
    ab = AnnotationBbox(OffsetImage(plt.imread(path), 0.10),
                        (math.radians(current_direction[0]), actual_elev), frameon=False)
    ax1.add_artist(ab)

    x_direction = [trajectory[item][2] for item in range(len(trajectory))]
    y_direction = [trajectory[item][3] for item in range(len(trajectory))]

    x_lines_list = []
    y_lines_list = []



    for item in range(len(x_direction)):
        x_direction[item] = math.radians(x_direction[item])

    for item in reversed(range(len(y_direction))):
        if y_direction[item] < 0:
            pass
            # y_direction.pop(item)
            # x_direction.pop(item)
            # y_direction[item] = 90

        else:
            y_direction[item] = 90 - y_direction[item]

    last_cut = 0
    for x in range(len(x_direction) - 1):
        if x_direction[x] < 0:
            x_copy = x_direction
            y_copy = y_direction

            x_lines_list.append(x_copy[last_cut:x + 1])
            y_lines_list.append(y_copy[last_cut:x + 1])
            last_cut = x + 1

    x_lines_list.append(x_direction[last_cut + 1:])
    y_lines_list.append(y_direction[last_cut + 1:])

    count = len(x_lines_list)

    opacity_level = 1 / (count + 1)

    if x_lines_list:
        width = 0.0000008
        for item in range(len(x_lines_list)):
            if len(x_lines_list[item]) > 2:
                if y_lines_list[item][0] != 90:
                    y_lines_list[item].insert(0, 90)
                    x_lines_list[item].insert(0, x_lines_list[item][0])

                if x_lines_list[item][-1] != 0 and item != len(x_lines_list) - 1:
                    y_lines_list[item].append(90)
                    x_lines_list[item].append(x_lines_list[item][-1])

            ax1.plot(x_lines_list[item], y_lines_list[item], c='r', alpha=1 - (item * opacity_level))

            for inside_item in range(len(x_lines_list[item]) - 1):
                u = -(x_lines_list[item][inside_item] - x_lines_list[item][inside_item + 1])
                v = -(y_lines_list[item][inside_item] - y_lines_list[item][inside_item + 1])
                length = np.sqrt(u ** 2 + v ** 2)
                hal = hl = 1. / width * length
                ax1.quiver(x_lines_list[item][inside_item], y_lines_list[item][inside_item], u, v, angles='xy',
                           scale_units='xy', scale=1,
                           headwidth=hl,
                           headaxislength=hal,
                           headlength=hl,
                           width=width,
                           color="r",
                           alpha=1 - (item * opacity_level)
                           )
    else:
        ax1.plot(x_direction, y_direction, c='r')

        width = 0.0000008
        for inside_item in range(len(x_direction) - 1):
            u = -(x_direction[inside_item] - x_direction[inside_item + 1])
            v = -(y_direction[inside_item] - y_direction[inside_item + 1])
            length = np.sqrt(u ** 2 + v ** 2)
            hal = hl = 1. / width * length
            ax1.quiver(x_direction[inside_item], y_direction[inside_item], u, v, angles='xy', scale_units='xy',
                       scale=1,
                       headwidth=hl,
                       headaxislength=hal,

                       headlength=hl,
                       width=width,
                       color="r")
    return plt
