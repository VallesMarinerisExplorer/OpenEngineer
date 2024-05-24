from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import FreeSimpleGUI as sg
import matplotlib
import pandas as pd
# matplotlib.use('TkAgg')
import warnings
import datetime
from jdcal import gcal2jd,jd2gcal
import os
username = str(os.getlogin())
# This script acts as a basic GUI for a trajectory planner. Probably can make it a lot more user friendly,
# in more than one way maybe using better visualizations/combine with pybullet but just trying to get my thoughts down
# and see what makes sense to aggregate mission planning and orbit design functions. Not everything works!

# Sometimes you need to run this 2 or 3 times before it renders correctly

# GUI Based on examples from PySimpleGUI (FreeSimpleGUI)
warnings.filterwarnings("ignore")

sg.ChangeLookAndFeel('Black')

def plot_orbit(mu, transfer_sma, transfer_ecc, transfer_inc, transfer_AOP, transfer_RAAN,deplocs="",arrlocs="", dep_pos="", arr_pos=""):
    # fig1 = plt.figure()
    fig1.clear()
    ax1 = fig1.add_subplot(111, projection='3d')
    ax1.view_init(elev=90, azim=0)

    X_Orb = []
    Y_Orb = []
    Z_Orb = []

    # MA is mean anomaly, i.e. 0 degrees to 360 degrees i.e. full rotation around the planet/target body
    for MA in range(0, 360):
        statevecxyz, statevecvxvyvz = kep_2_cart(mu, transfer_sma, transfer_ecc, transfer_inc, transfer_AOP,
                                                 transfer_RAAN, MA)

        X_Orb.append(statevecxyz[0])
        Y_Orb.append(statevecxyz[1])
        Z_Orb.append(statevecxyz[2])

    ax1.grid()

    maxar = [max(X_Orb), max(Y_Orb),max(Z_Orb)]
    maximum = max(maxar)
    # print(maximum)
    xrng = np.array([-maximum*1.2, maximum*1.2])
    yrng = xrng
    zrng = xrng

    ax1.set_xlim(xrng)
    ax1.set_ylim(yrng)
    ax1.set_zlim(zrng)

    ax1.plot([0], [0], [0], marker='o', markersize=18.0, color='yellow')

    ax1.plot(X_Orb, Y_Orb, Z_Orb, color='w', linewidth=4, label="Transfer Orbit")
    if deplocs != "":
        ax1.plot(deplocs[:,0], deplocs[:,1], deplocs[:,2], color='b', linewidth=4, label=Initial + " Orbit")
    if arrlocs != "":
        ax1.plot(arrlocs[:,0], arrlocs[:,1], arrlocs[:,2], color='r', linewidth=4, label=Destination + " Orbit")
    if dep_pos != "":
        ax1.plot(dep_pos[0], dep_pos[1], dep_pos[2], marker='o', markersize=8.0, color='w')
        ax1.plot(arr_pos[0], arr_pos[1], arr_pos[2], marker='o', markersize=8.0, color='w')

    ax1.set_facecolor("black")
    fig1.set_facecolor("black")

    plt.axis('off')
    plt.grid(b=None)
    ax1.legend()
    fig1.canvas.draw()


def kep_2_cart(mu, a,e,i,omega_AP,omega_LAN, MA):
    import math
    from scipy import optimize
    # n = np.sqrt(mu/(a**3))
    # T = 2*math.pi*math.sqrt((a**3)/132712440018000000000)
    def f(x):
        EA_rad = x - (e * math.sin(x)) - math.radians(MA)
        return EA_rad
    EA = math.degrees(optimize.newton(f, 1))

    nu = 2*np.arctan(np.sqrt((1+e)/(1-e)) * np.tan(math.radians(EA)/2))
    r = a*(1 - e*np.cos(math.radians(EA)))

    h = np.sqrt(mu*a * (1 - e**2))

    X = r*(np.cos(math.radians(omega_LAN))*np.cos(math.radians(omega_AP)+nu) - np.sin(math.radians(omega_LAN))*np.sin(math.radians(omega_AP)+nu)*np.cos(math.radians(i)))
    Y = r*(np.sin(math.radians(omega_LAN))*np.cos(math.radians(omega_AP)+nu) + np.cos(math.radians(omega_LAN))*np.sin(math.radians(omega_AP)+nu)*np.cos(math.radians(i)))
    Z = r*(np.sin(math.radians(i))*np.sin(math.radians(omega_AP)+nu))

    p = a*(1-e**2)

    V_X = (X*h*e/(r*p))*np.sin(nu) - (h/r)*(np.cos(omega_LAN)*np.sin(omega_AP+nu) + \
    np.sin(omega_LAN)*np.cos(omega_AP+nu)*np.cos(i))
    V_Y = (Y*h*e/(r*p))*np.sin(nu) - (h/r)*(np.sin(omega_LAN)*np.sin(omega_AP+nu) - \
    np.cos(omega_LAN)*np.cos(omega_AP+nu)*np.cos(i))
    V_Z = (Z*h*e/(r*p))*np.sin(nu) + (h/r)*(np.cos(omega_AP+nu)*np.sin(i))

    return [X,Y,Z],[V_X,V_Y,V_Z]

import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')


u = np.linspace(0, 2 * np.pi, 100)
v = np.linspace(0, np.pi, 100)

x = 1 * np.outer(np.cos(u), np.sin(v))
y = 1 * np.outer(np.sin(u), np.sin(v))
z = 1 * np.outer(np.ones(np.size(u)), np.cos(v))

# Orbital Parameters
Semimajoraxis = 10
Inclination = 75
Eccentricity = 0.9
RAAN = 20
AOP = 20

X_Orb = []
Y_Orb = []
Z_Orb = []
mu = 398600
for MA in range(0,360):
    statevecxyz,statevecvxvyvz = kep_2_cart(mu,Semimajoraxis,Eccentricity,Inclination,AOP,RAAN,MA)
    # print(statevecxyz)
    X_Orb.append(statevecxyz[0])
    Y_Orb.append(statevecxyz[1])
    Z_Orb.append(statevecxyz[2])

ax.plot_surface(x, y, z,  rstride=4, cstride=4, color='r', linewidth=0, alpha=1)
ax.scatter3D(X_Orb,Y_Orb,Z_Orb, color='b')

ax.set_facecolor("black")
fig.set_facecolor("black")

plt.axis('off')
plt.grid(b=None)
ax.set_box_aspect([1,1,1])

launchrange=60

def draw_figure(canvas, figure):
    figure_canvas_agg = FigureCanvasTkAgg(figure, canvas)
    figure_canvas_agg.draw()
    figure_canvas_agg.get_tk_widget().pack(side='top', fill='both', expand=1)
    return figure_canvas_agg

# launchdate = "09_04_2022 00:00:00.000"
launchdate = "2005-09-23"
Semimajoraxis = 3000000 # meters
Inclination = 45
Eccentricity = 0.3

EngineList = ["Main Engine", "RCS"]
# BurnList = ["Earth Departure", "TCM 1", "TCM 2", "Mars Injection Orbit", "Circularization Burn"]
BurnList = []
Initial = "Earth"
Destination = "Mars"

ReferenceFrames = [Initial+ " LVLH", Initial + " Centered-Inertial", Initial + "-Centered, " + Initial + " Fixed", "International Celestial Reference Frame", Destination+ " LVLH", Destination + " Centered-Inertial", Destination + "-Centered, " + Destination + " Fixed",]

Header = ["Burn Name", "    Engine    ", "    Time of Ignition    ", "Reference Frame","Delta VX","Delta VY","Delta VZ", "Mass Decrease","Burn Duration"]
col3 = [[sg.Text("Spacecraft Orbit Around", font=("Cooper", 26)),sg.Text(Initial,key="-INITNAME-", font=("Cooper", 26))],
          [sg.Button("Change Departure Body", size=(33,1), key="-DEPBOD-"),sg.Button('Edit in Separate Window', key="-EARTH-", size=(30,1))],
          [sg.Text('Reference Frame:                                 '), sg.Listbox(ReferenceFrames[0:3], size=(28,3)) ],
          [sg.Text('Semi major axis:                                   '), sg.InputText(Semimajoraxis/1000, size=(20,3)), sg.Text(' Kilometers')],
          [sg.Text('Inclination:                                            '), sg.InputText(Inclination, size=(20,3)), sg.Text(' Degrees')],
          [sg.Text('Eccentricity:                                         '), sg.InputText(Eccentricity, size=(20,3))],
          [sg.Text('Right Ascension of the Ascending Node: '), sg.InputText(RAAN, size=(20,3)), sg.Text(' Degrees')],
          [sg.Text('Arguement of Periapsis:                        '), sg.InputText(AOP, size=(20,3)), sg.Text(' Degrees')]]
col1 = [
          [sg.Text('Transfer Orbit', font=("Cooper", 26))],
          [sg.Button('Edit in Separate Window', key="-TRANSIT-")],
          # [sg.Text('Reference Frame:                                 '), sg.Listbox(ReferenceFrames[3:4], size=(28,3)) ],
          [sg.Text('Earliest Launch Date:                             '), sg.InputText(launchdate, key="-LAUNCHDATE-")],
          [sg.Text('Launch Window Search Length (days):   '), sg.InputText(launchrange, key="-LAUNCHRNG-")],
          [sg.Text('Semi major axis:                                   '), sg.InputText(Semimajoraxis/1000, size=(20,3)), sg.Text(' Kilometers')],
          [sg.Text('Inclination:                                            '), sg.InputText(Inclination, size=(20,3)), sg.Text(' Degrees')],
          [sg.Text('Eccentricity:                                         '), sg.InputText(Eccentricity, size=(20,3))],
          [sg.Text('Right Ascension of the Ascending Node: '), sg.InputText(RAAN, size=(20,3)), sg.Text(' Degrees')],
          [sg.Text('Arguement of Periapsis:                        '), sg.InputText(AOP, size=(20,3)), sg.Text(' Degrees')]]
col2 = [[sg.Text("Spacecraft Orbit Around", font=("Cooper", 26)),sg.Text(Destination,key="-DESTNAME-", font=("Cooper", 26))],
          [sg.Button("Change Target Body", size=(33,1),key="-ARRBOD-"),sg.Button('Edit in Separate Window', key="-DESTINATION-", size=(30,1)), ],
          [sg.Text('Reference Frame:                                 '), sg.Listbox(ReferenceFrames[4:7], size=(28,3)) ],
          [sg.Text('Semi major axis:                                   '), sg.InputText(Semimajoraxis/1000, size=(20,3)), sg.Text(' Kilometers')],
          [sg.Text('Inclination:                                            '), sg.InputText(Inclination, size=(20,3)), sg.Text(' Degrees')],
          [sg.Text('Eccentricity:                                         '), sg.InputText(Eccentricity, size=(20,3))],
          [sg.Text('Right Ascension of the Ascending Node: '), sg.InputText(RAAN, size=(20,3)), sg.Text(' Degrees')],
          [sg.Text('Arguement of Periapsis:                        '), sg.InputText(AOP, size=(20,3)), sg.Text(' Degrees')]]
launchcolumn = [[sg.Text('Launch Vehicle Parameters', font=("Cooper", 26))],
          [sg.Button('Edit in Separate Window', key="-SEPARATE3-")],
          [sg.Text('Payload Mass'), sg.Text(Inclination, size=(20, 1)), sg.Text(' Kilograms')],
          [sg.Text('Launch Vehicle'), sg.Text("Launch Vehicle", size=(28,1)),sg.Button("Select Vehicle", size=(21,1), key="-SELVEH-")],
          [sg.Text('Launch Site'), sg.Text("Launch Site", size=(28,1))],
          [sg.Text('Launch Date'), sg.Text("   ", size=(28,1))],
          [sg.Text('Launch Azimuth'), sg.Text(Eccentricity, size=(20,1)), sg.Text(' Degrees')],
          [sg.Text('Parking Orbit Apoapsis'), sg.InputText(RAAN, size=(20,1)), sg.Text(' Kilometers')],
          [sg.Text('Parking Orbit Periapsis'), sg.InputText(AOP, size=(20,3)), sg.Text(' Kilometers')]]

layout = [[sg.Column(col1), sg.Canvas(key='-CANVAS-', size=(200,200)),sg.Column(col2), sg.Canvas(key='-CANVAS1-', size=(250,250))],
          [sg.Column(col3), sg.Canvas(key='-CANVAS2-', size=(250,250)),sg.Column(launchcolumn),sg.Canvas(key='-CANVAS5-', size=(200,200))],
          [sg.Button('Add Burn', key="-BURN-")],
          [sg.Submit(),sg.Cancel()]]


window = sg.Window('Trajectory Planner', layout, default_element_size=(40, 1), finalize=True, grab_anywhere=False)

draw_figure(window['-CANVAS-'].TKCanvas, fig)
draw_figure(window['-CANVAS1-'].TKCanvas, fig)
draw_figure(window['-CANVAS2-'].TKCanvas, fig)

from poliastro.plotting.porkchop import porkchop
from poliastro.bodies import Mercury, Venus, Earth, Mars, Jupiter, Saturn, Uranus, Neptune, Pluto
from poliastro.util import time_range

while True:
    event, values = window.read()
    launchdatestart = values["-LAUNCHDATE-"]
    launchrange = values["-LAUNCHRNG-"]

    planetIDs = [199, 299, 399, 499, 599, 699, 799, 899, 999]
    # moonIDsVis = [301, 401, 402, 501, 502, 503, 504, 505, 506, 507, 508, 509, 510, 511, 512, 513, 514, 515, 516,
    #               517,
    #               518, 519, 520, 521, 522, 523, 524, 525, 526, 527, 528, 529, 530, 531, 532, 533, 534, 535, 536,
    #               537,
    #               538, 539, 540, 541, 542, 543, 544, 545, 546, 547, 548, 549, 550, 551, 552, 553, 554, 555, 556,
    #               557,
    #               558, 559, 560, 561, 562, 563, 564, 565, 566, 567, 568, 569, 570, 571, 572, 601, 602, 603, 604, 605,
    #               606, 607,
    #               608, 609, 610, 611, 612, 615, 616, 617, 618, 701, 702, 703, 704, 705, 801, 803, 804, 805, 806,
    #               807, 808, 901, 902, 903, 904]

    choices = ["Mercury", "Venus", "Earth", "Mars", "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto"]


    moons = ["Moon", "Phobos", "Deimos",
             "Io",
             "Europa",
             "Ganymede",
             "Callisto",
             "Amalthea",
             "Himalia",
             "Elara",
             "Pasiphae",
             "Sinope",
             "Lysithea",
             "Carme",
             "Ananke",
             "Leda",
             "Thebe",
             "Adrastea",
             "Metis",
             "Callirrhoe",
             "Themisto",
             "Megaclite",
             "Taygete",
             "Chaldene",
             "Harpalyke",
             "Kalyke",
             "Iocaste",
             "Erinome",
             "Isonoe",
             "Praxidike",
             "Autonoe",
             "Thyone",
             "Hermippe",
             "Aitne",
             "Eurydome",
             "Euanthe",
             "Euporie",
             "Orthosie",
             "Sponde",
             "Kale",
             "Pasithee",
             "Hegemone",
             "Mneme",
             "Aoede",
             "Thelxinoe",
             "Arche",
             "Kallichore",
             "Helike",
             "Carpo",
             "Eukelade",
             "Cyllene",
             "Kore",
             "Herse",
             "2010J1",
             "2010J2",
             "Dia",
             "2016J1",
             "2003J18",
             "2011J2",
             "Eirene",
             "Philophrosyne",
             "2017J1",
             "Eupheme",
             "2003J19",
             "Valetudo",
             "2017J2",
             "2017J3",
             "Pandia",
             "2017J5",
             "2017J6",
             "2017J7",
             "2017J8",
             "2017J9",
             "Ersa",
             "2011J1",
             "Mimas",
             "Enceladus",
             "Tethys",
             "Dione",
             "Rhea",
             "Titan",
             "Hyperion",
             "Iapetus",
             "Phoebe",
             "Janus",
             "Epimetheus",
             "Helene",
             "Atlas",
             "Prometheus",
             "Pandora",
             "Pan",
             "Ariel",
             "Umbriel",
             "Titania",
             "Oberon",
             "Miranda",
             "Triton",
             "Naiad",
             "Thalassa",
             "Despina",
             "Galatea",
             "Larissa",
             "Proteus",
             "Charon",
             "Nix",
             "Hydra",
             "Kerberos"]
    planets = ["Mercury", "Venus", "Earth", "Mars", "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto"]
    planetIDs = [199,299,399,499,599,699,799,899,999]
    moonIDs = [301, 401, 402, 501, 502, 503, 504, 505, 506, 507, 508, 509, 510, 511, 512, 513, 514, 515, 516,
               517,
               518, 519, 520, 521, 522, 523, 524, 525, 526, 527, 528, 529, 530, 531, 532, 533, 534, 535, 536,
               537,
               538, 539, 540, 541, 542, 543, 544, 545, 546, 547, 548, 549, 550, 551, 552, 553, 554, 555, 556,
               557,
               558, 559, 560, 561, 562, 563, 564, 565, 566, 567, 568, 569, 570, 571, 572, 601, 602, 603, 604, 605,
               606,
               607,
               608, 609, 610, 611, 612, 615, 616, 617, 618, 701, 702, 703, 704, 705, 801, 803, 804, 805, 806,
               807, 808, 901, 902, 903, 904]
    if Destination in moons or Destination in planets:
        if Destination in moons:
            ID = moonIDs[moons.index(Destination)]
        else:
            ID = planetIDs[planets.index(Destination)]
        if ID == 301:
            target= Earth
        elif ID > 400:
            target = Mars
        elif ID > 500:
            target = Jupiter
        elif ID > 600:
            target = Saturn
        elif ID > 700:
            target = Uranus
        elif ID > 800:
            target = Neptune
        elif ID > 900:
            target = Pluto
    else:
        # Need to send pos/vel info for asteroids
        pass
    choices = choices + moons
    if event == "Exit" or event == sg.WIN_CLOSED:
        window.close()
        break

    if event == "-ARRBOD-":
        import csv
        with open('C:\\Users\\' + username + '\\AppData\\Roaming\\FreeCAD\\Mod\\SpacecraftDesigner\\ORBITAL\\Planets\\SmallBodyDatabase.csv') as f:
            smallbodies = csv.reader(f, delimiter=',')
            for row in smallbodies:
                if row[1] != "":
                    choices.append(row[1])
                else:
                    choices.append(row[0])

        layout1 = [
            [sg.Text('Select Target Body:')],
            [sg.Input(size=(20, 1), enable_events=True, key='-IN-')],
            [sg.pin(sg.Col(
                [[sg.Listbox(values=[], size=(25, 6), enable_events=True, key='-BOX-',
                             select_mode=sg.LISTBOX_SELECT_MODE_SINGLE, no_scrollbar=True)]],
                key='-BOX-CONTAINER-', pad=(0, 0), visible=False))],
            [sg.Submit(tooltip='Submit'), sg.Cancel()]
        ]

        window2 = sg.Window('Select Target Body', layout1, return_keyboard_events=True, finalize=True,
                            font=('Helvetica', 16))

        list_element: sg.Listbox = window2.Element(
            '-BOX-')  # store listbox element for easier access and to get to docstrings
        prediction_list, input_text, sel_item = [], "", 0

        while True:  # Event Loop
            event2, values = window2.read()
            if event2 == sg.WINDOW_CLOSED:
                break
            # pressing down arrow will trigger event -IN- then aftewards event Down:40
            elif event2.startswith('Escape'):
                window2['-IN-'].update('')
                window2['-BOX-CONTAINER-'].update(visible=False)
            elif event2.startswith('Down') and len(prediction_list):
                sel_item = (sel_item + 1) % len(prediction_list)
                list_element.update(set_to_index=sel_item, scroll_to_index=sel_item)
            elif event2.startswith('Up') and len(prediction_list):
                sel_item = (sel_item + (len(prediction_list) - 1)) % len(prediction_list)
                list_element.update(set_to_index=sel_item, scroll_to_index=sel_item)
            elif event2 == '\r':
                if len(values['-BOX-']) > 0:
                    window2['-IN-'].update(value=values['-BOX-'])
                    window2['-BOX-CONTAINER-'].update(visible=False)
            elif event2 == '-IN-':
                text = values['-IN-'].lower()
                if text == input_text:
                    continue
                else:
                    input_text = text
                prediction_list = []
                if text:
                    prediction_list = [item for item in choices if item.lower().startswith(text)]

                list_element.update(values=prediction_list)
                sel_item = 0

                list_element.update(set_to_index=sel_item)

                if len(prediction_list) > 0:
                    window2['-BOX-CONTAINER-'].update(visible=True)
                else:
                    window2['-BOX-CONTAINER-'].update(visible=False)
            elif event2 == '-BOX-':
                window2['-IN-'].update(value=values['-BOX-'])
                window2['-BOX-CONTAINER-'].update(visible=False)
            elif event2 == "Submit":
                Destination = values["-BOX-"][0]
                target = Destination
                window.Element('-DESTNAME-').update(Destination)
                # window.close()
                window2.close()
                window2.close()
            elif event2 == "Cancel":
                window2.close()
        window2.close()

    if event == "-SELVEH-":
        choices = ["Falcon 9", "Antares", "Vulcan"]
        layout1 = [
            [sg.Text('Select Launch Vehicle:')],
            [sg.Input(size=(20, 1), enable_events=True, key='-IN-')],
            [sg.pin(sg.Col(
                [[sg.Listbox(values=[], size=(25, 6), enable_events=True, key='-BOX-',
                             select_mode=sg.LISTBOX_SELECT_MODE_SINGLE, no_scrollbar=True)]],
                key='-BOX-CONTAINER-', pad=(0, 0), visible=False))],
            [sg.Submit(tooltip='Submit'), sg.Cancel()]

        ]

        window2 = sg.Window('Launch Vehicle Selector', layout1, return_keyboard_events=True, finalize=True,
                            font=('Helvetica', 16))

        list_element: sg.Listbox = window2.Element(
            '-BOX-')  # store listbox element for easier access and to get to docstrings
        prediction_list, input_text, sel_item = [], "", 0

        while True:  # Event Loop
            event2, values = window2.read()
            if event2 == sg.WINDOW_CLOSED:
                break
            # pressing down arrow will trigger event -IN- then aftewards event Down:40

            elif event2.startswith('Escape'):
                window2['-IN-'].update('')
                window2['-BOX-CONTAINER-'].update(visible=False)
            elif event2.startswith('Down') and len(prediction_list):
                sel_item = (sel_item + 1) % len(prediction_list)
                list_element.update(set_to_index=sel_item, scroll_to_index=sel_item)
            elif event2.startswith('Up') and len(prediction_list):
                sel_item = (sel_item + (len(prediction_list) - 1)) % len(prediction_list)
                list_element.update(set_to_index=sel_item, scroll_to_index=sel_item)
            elif event2 == '\r':
                if len(values['-BOX-']) > 0:
                    window2['-IN-'].update(value=values['-BOX-'])
                    window2['-BOX-CONTAINER-'].update(visible=False)
            elif event2 == '-IN-':
                text = values['-IN-'].lower()
                if text == input_text:
                    continue
                else:
                    input_text = text
                prediction_list = []
                if text:
                    prediction_list = [item for item in choices if item.lower().startswith(text)]

                list_element.update(values=prediction_list)
                sel_item = 0

                list_element.update(set_to_index=sel_item)
                # print(prediction_list[sel_item])
                if len(prediction_list) > 0:
                    window2['-BOX-CONTAINER-'].update(visible=True)
                else:
                    window2['-BOX-CONTAINER-'].update(visible=False)
            elif event2 == '-BOX-':
                window2['-IN-'].update(value=values['-BOX-'])
                window2['-BOX-CONTAINER-'].update(visible=False)
            elif event2 == "Submit":
                LaunchVehicle = values["-BOX-"][0]
                # window2.Element('-INITNAME-').update(Initial)
                print(Initial)
                window2.close()
            elif event2 == "Cancel":
                window2.close()
        window2.close()
    if event == "-DEPBOD-":

        import csv
        with open('C:\\Users\\' + username + '\\AppData\\Roaming\\FreeCAD\\Mod\\SpacecraftDesigner\\ORBITAL\\Planets\\SmallBodyDatabase.csv') as f:
            smallbodies = csv.reader(f, delimiter=',')
            for row in smallbodies:
                if row[1] != "":
                    choices.append(row[1])
                else:
                    choices.append(row[0])
        layout1 = [
            [sg.Text('Select Departure Body:')],
            [sg.Input(size=(20, 1), enable_events=True, key='-IN-')],
            [sg.pin(sg.Col(
                [[sg.Listbox(values=[], size=(25, 6), enable_events=True, key='-BOX-',
                             select_mode=sg.LISTBOX_SELECT_MODE_SINGLE, no_scrollbar=True)]],
                key='-BOX-CONTAINER-', pad=(0, 0), visible=False))],
            [sg.Submit(tooltip='Submit', key="-INITDEST-"), sg.Cancel()]

        ]

        window2 = sg.Window('AutoComplete', layout1, return_keyboard_events=True, finalize=True,
                            font=('Helvetica', 16))

        list_element: sg.Listbox = window2.Element(
            '-BOX-')  # store listbox element for easier access and to get to docstrings
        prediction_list, input_text, sel_item = [], "", 0

        while True:  # Event Loop
            event2, values = window2.read()
            if event2 == sg.WINDOW_CLOSED:
                break
            # pressing down arrow will trigger event -IN- then aftewards event Down:40

            elif event2.startswith('Escape'):
                window2['-IN-'].update('')
                window2['-BOX-CONTAINER-'].update(visible=False)
            elif event2.startswith('Down') and len(prediction_list):
                sel_item = (sel_item + 1) % len(prediction_list)
                list_element.update(set_to_index=sel_item, scroll_to_index=sel_item)
            elif event2.startswith('Up') and len(prediction_list):
                sel_item = (sel_item + (len(prediction_list) - 1)) % len(prediction_list)
                list_element.update(set_to_index=sel_item, scroll_to_index=sel_item)
            elif event2 == '\r':
                if len(values['-BOX-']) > 0:
                    window2['-IN-'].update(value=values['-BOX-'])
                    window2['-BOX-CONTAINER-'].update(visible=False)
            elif event2 == '-IN-':
                text = values['-IN-'].lower()
                if text == input_text:
                    continue
                else:
                    input_text = text
                prediction_list = []
                if text:
                    prediction_list = [item for item in choices if item.lower().startswith(text)]

                list_element.update(values=prediction_list)
                sel_item = 0

                list_element.update(set_to_index=sel_item)
                # print(prediction_list[sel_item])
                if len(prediction_list) > 0:
                    window2['-BOX-CONTAINER-'].update(visible=True)
                else:
                    window2['-BOX-CONTAINER-'].update(visible=False)
            elif event2 == '-BOX-':
                window2['-IN-'].update(value=values['-BOX-'])
                window2['-BOX-CONTAINER-'].update(visible=False)
            elif event2 == "Submit":
                Initial = values["-BOX-"][0]
                window.Element('-INITNAME-').update(Initial)
                # window.close()
                window2.close()
            elif event2 == "Cancel":
                window2.close()
        window2.close()


    if event == "-EARTH-":
        sepcol1 = [[sg.Text(Initial + ' Orbit', font=("Cooper", 26))],
                [sg.Text('Reference Frame:                                 '),
                 sg.Listbox(ReferenceFrames[0:3], size=(28, 3))],
                [sg.Text('Semi major axis:                                   '),
                 sg.InputText(Semimajoraxis / 1000, size=(20, 3)), sg.Text(' Kilometers')],
                [sg.Text('Inclination:                                            '),
                 sg.InputText(Inclination, size=(20, 3)), sg.Text(' Degrees')],
                [sg.Text('Eccentricity:                                         '),
                 sg.InputText(Eccentricity, size=(20, 3))],
                [sg.Text('Right Ascension of the Ascending Node: '), sg.InputText(RAAN, size=(20, 3)),
                 sg.Text(' Degrees')],
                [sg.Text('Arguement of Periapsis:                        '), sg.InputText(AOP, size=(20, 3)),
                 sg.Text(' Degrees')],
               [sg.Button('Update', key="-SEP1UPDATE-")]]


        w, h = figsize = (7, 7)  # figure size
        fig1 = matplotlib.figure.Figure(figsize)
        dpi = fig1.get_dpi()
        size = (w * dpi, h * dpi)
        ax1 = fig1.add_subplot(111, projection='3d')
        ax1.set_facecolor("black")
        fig1.set_facecolor("black")
        ax1.plot_surface(x, y, z, rstride=4, cstride=4, color='r', linewidth=0, alpha=1)
        ax1.scatter3D(X_Orb, Y_Orb, Z_Orb, color='b')



        # plt.axis('off')
        # plt.grid(visible=None)
        ax1.set_box_aspect([1, 1, 1])

        separatelayout1 = [[sg.Column(sepcol1), sg.Canvas(key='-CANVAS4-', size=size)]]
        sep1window = sg.Window('Earth Orbit', separatelayout1, finalize=True, grab_anywhere=False)
        OrbitalData = draw_figure(sep1window['-CANVAS4-'].TKCanvas, fig1)
        while True:
            sep1event, sep1values = sep1window.read()
            if sep1event == "Exit" or sep1event == sg.WIN_CLOSED:
                sep1window.close()
                break
            if sep1event == "-SEP1UPDATE-":
                refFrame = sep1values[0]
                Semimajoraxis = float(sep1values[1])
                Inclination = float(sep1values[2])
                Eccentricity = float(sep1values[3])
                RAAN = float(sep1values[4])
                AOP = float(sep1values[5])
                X_Orb = []
                Y_Orb = []
                Z_Orb = []
                mu = 398600

                for MA in range(0, 360):
                    statevecxyz, statevecvxvyvz = kep_2_cart(mu, Semimajoraxis, Eccentricity, Inclination, AOP, RAAN,
                                                             MA)
                    # print(statevecxyz)
                    X_Orb.append(statevecxyz[0])
                    Y_Orb.append(statevecxyz[1])
                    Z_Orb.append(statevecxyz[2])

                ax1.cla()
                # plt.axis('off')
                # plt.grid(visible=None)
                # ax1.set_box_aspect([1, 1, 1])
                ax1.set_facecolor("black")
                fig1.set_facecolor("black")
                ax1.plot_surface(x, y, z, rstride=4, cstride=4, color='r', linewidth=0, alpha=1)
                ax1.scatter3D(X_Orb, Y_Orb, Z_Orb, color='b')
                OrbitalData.draw()

    if event == "-TRANSIT-":
        import math
        import datetime
        from datetime import datetime as datet
        import csv
        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
        import FreeSimpleGUI as sg
        import matplotlib
        from matplotlib import pyplot as plt
        import os
        import warnings

        warnings.filterwarnings("ignore")

        from astroquery.jplhorizons import Horizons


        def kep_2_cart(mu, a, e, i, omega_AP, omega_LAN, MA):
            import math
            from scipy import optimize
            # n = np.sqrt(mu/(a**3))
            # T = 2*math.pi*math.sqrt((a**3)/132712440018000000000)
            def f(x):
                EA_rad = x - (e * math.sin(x)) - math.radians(MA)
                return EA_rad

            EA = math.degrees(optimize.newton(f, 1))

            nu = 2 * np.arctan(np.sqrt((1 + e) / (1 - e)) * np.tan(math.radians(EA) / 2))
            r = a * (1 - e * np.cos(math.radians(EA)))
            h = np.sqrt(mu * a * (1 - e ** 2))
            X = r * (np.cos(math.radians(omega_LAN)) * np.cos(math.radians(omega_AP) + nu) - np.sin(
                math.radians(omega_LAN)) * np.sin(math.radians(omega_AP) + nu) * np.cos(math.radians(i)))
            Y = r * (np.sin(math.radians(omega_LAN)) * np.cos(math.radians(omega_AP) + nu) + np.cos(
                math.radians(omega_LAN)) * np.sin(math.radians(omega_AP) + nu) * np.cos(math.radians(i)))
            Z = r * (np.sin(math.radians(i)) * np.sin(math.radians(omega_AP) + nu))

            p = a * (1 - e ** 2)

            V_X = (X * h * e / (r * p)) * np.sin(nu) - (h / r) * (np.cos(omega_LAN) * np.sin(omega_AP + nu) + \
                                                                  np.sin(omega_LAN) * np.cos(omega_AP + nu) * np.cos(i))
            V_Y = (Y * h * e / (r * p)) * np.sin(nu) - (h / r) * (np.sin(omega_LAN) * np.sin(omega_AP + nu) - \
                                                                  np.cos(omega_LAN) * np.cos(omega_AP + nu) * np.cos(i))
            V_Z = (Z * h * e / (r * p)) * np.sin(nu) + (h / r) * (np.cos(omega_AP + nu) * np.sin(i))

            return [X, Y, Z], [V_X, V_Y, V_Z]


        sg.theme("black")


        def draw_figure(canvas, figure):
            figure_canvas_agg = FigureCanvasTkAgg(figure, canvas)
            figure_canvas_agg.draw()
            figure_canvas_agg.get_tk_widget().pack(side='top', fill='both', expand=1)
            return figure_canvas_agg


        def delete_fig_agg(fig_agg):
            fig_agg.get_tk_widget().forget()
            plt.close('all')


        import numpy as np

        CentralBody = "Sun"
        if CentralBody == "Earth":
            mu = 398600000000000
        # Re = 6378000
        else:
            mu = 1.32712440018e20
        t = 0


        def cart_2_kep(r_vec, v_vec):
            # 1
            h_bar = np.cross(r_vec, v_vec)
            h = np.linalg.norm(h_bar)
            # 2
            r = np.linalg.norm(r_vec)
            v = np.linalg.norm(v_vec)
            # 3
            E = 0.5 * (v ** 2) - mu / r

            # 4
            a = -mu / (2 * E)

            # 5
            e = np.sqrt(1 - (h ** 2) / (a * mu))
            # 6
            i = np.arccos(h_bar[2] / h)
            # 7
            omega_LAN = np.arctan2(h_bar[0], -h_bar[1])
            # 8
            # beware of division by zero here
            lat = np.arctan2(np.divide(r_vec[2], (np.sin(i))), \
                             (r_vec[0] * np.cos(omega_LAN) + r_vec[1] * np.sin(omega_LAN)))
            # 9
            p = a * (1 - e ** 2)
            nu = np.arctan2(np.sqrt(p / mu) * np.dot(r_vec, v_vec), p - r)
            # 10
            omega_AP = math.degrees(lat - nu)
            # 11
            EA = 2 * np.arctan(np.sqrt((1 - e) / (1 + e)) * np.tan(nu / 2))
            # 12
            n = np.sqrt(mu / (a ** 3))
            T = t - (1 / n) * (EA - e * np.sin(EA))
            omega_LAN = math.degrees(omega_LAN)
            i = math.degrees(i)

            return a, e, i, omega_AP, omega_LAN, T, EA


        class Body():
            def __init__(self, Name):
                self.Name = Name
                if self.Name == "Mercury":
                    self.orbit_rad = 0.38709893
                    self.orbit_per = self.orbit_rad ** 1.5
                    self.orbit_vel = 2 * math.pi * self.orbit_rad / self.orbit_per
                    self.mean_longJ2000 = 252.25084
                    self.mass = 3.3e23
                    self.radius = 2440
                    self.soi = 111631
                if self.Name == "Venus":
                    self.orbit_rad = 0.72333199
                    self.orbit_per = self.orbit_rad ** 1.5
                    self.orbit_vel = 2 * math.pi * self.orbit_rad / self.orbit_per
                    self.mean_longJ2000 = 181.97973
                    self.mass = 4.869e24
                    self.radius = 6052
                    self.soi = 612171
                if self.Name == "Earth":
                    self.orbit_rad = 1
                    self.orbit_per = 1
                    self.orbit_vel = 2 * math.pi * self.orbit_rad / self.orbit_per
                    self.mean_longJ2000 = 100.46435
                    self.mass = 5.972e24
                    self.radius = 6378
                    self.soi = 918347
                if self.Name == "Mars":
                    self.orbit_rad = 1.52366231
                    self.orbit_per = self.orbit_rad ** 1.5
                    self.orbit_vel = 2 * math.pi * self.orbit_rad / self.orbit_per
                    self.mean_longJ2000 = 355.45332
                    self.mass = 6.4219e23
                    self.radius = 3397
                    self.soi = 573473
                if self.Name == "Jupiter":
                    self.orbit_rad = 5.20336301
                    self.orbit_per = self.orbit_rad ** 1.5
                    self.orbit_vel = 2 * math.pi * self.orbit_rad / self.orbit_per
                    self.mean_longJ2000 = 34.40438
                    self.mass = 1.9e27
                    self.radius = 71492
                    self.soi = 47901004
                if self.Name == "Saturn":
                    self.orbit_rad = 9.53707032
                    self.orbit_per = self.orbit_rad ** 1.5
                    self.orbit_vel = 2 * math.pi * self.orbit_rad / self.orbit_per
                    self.mean_longJ2000 = 49.94432
                    self.mass = 5.68e26
                    self.radius = 60268
                    self.soi = 54164329
                if self.Name == "Uranus":
                    self.orbit_rad = 19.19126393
                    self.orbit_per = self.orbit_rad ** 1.5
                    self.orbit_vel = 2 * math.pi * self.orbit_rad / self.orbit_per
                    self.mean_longJ2000 = 313.23218
                    self.mass = 8.683e25
                    self.radius = 25559
                    self.soi = 51419820
                if self.Name == "Neptune":
                    self.orbit_rad = 30.06896348
                    self.orbit_per = self.orbit_rad ** 1.5
                    self.orbit_vel = 2 * math.pi * self.orbit_rad / self.orbit_per
                    self.mean_longJ2000 = 304.8803
                    self.mass = 1.0247e26
                    self.radius = 24766
                    self.soi = 86082764

        # launch_span = time_range("2026-01-30", end="2028-11-15")
        # arrival_span = time_range("2028-11-16", end="2030-12-21")
        # span = 60
        dt = datetime.datetime.strptime(launchdatestart[:10], '%Y-%m-%d')
        # print(gcal2jd(dt.year, dt.month, dt.day))
        launch_date_end = jd2gcal(2400000.5, gcal2jd(dt.year, dt.month, dt.day)[0]+ gcal2jd(dt.year, dt.month, dt.day)[1] + int(launchrange)-2400000.5)
        launch_date_end = str(launch_date_end[0]) + "-" + str(launch_date_end[1]) + "-" + str(launch_date_end[2])
        arrival_date_start = jd2gcal(2400000.5, gcal2jd(dt.year, dt.month, dt.day)[0]+ gcal2jd(dt.year, dt.month, dt.day)[1] + int(launchrange)+1-2400000.5)
        arrival_date_end = jd2gcal(2400000.5,
                                     gcal2jd(dt.year, dt.month, dt.day)[0] + gcal2jd(dt.year, dt.month, dt.day)[
                                         1] + (2*int(launchrange)) + 1 - 2400000.5)
        dt = datetime.datetime.strptime(launch_date_end, '%Y-%m-%d')

        launch_span = time_range(launchdatestart[:10], end=str(dt.year) + "-" +str(dt.month).zfill(2) + "-" +str(dt.day).zfill(2))
        arrival_span = time_range(str(arrival_date_start[0]) + "-" +str(arrival_date_start[1]).zfill(2) + "-" +str(arrival_date_start[2]).zfill(2), end=str(arrival_date_end[0]) + "-" +str(arrival_date_end[1]).zfill(2) + "-" +str(arrival_date_end[2]).zfill(2))

        c3_launch, c3_arrival, tof, dv_launch, dv_arrival, c3_levels, vhp_levels, dep_dv, arr_dv, vv_dep, vv_arr, rr_dep, rr_arr = porkchop(
            Earth, target, launch_span, arrival_span, tfl=True)
        # print(dep_dv)
        # print(dep_dv)
        deplocs = []

        for position in rr_dep[0]:
            deplocs.append((position.value[0] * 149597870700,position.value[1] * 149597870700,position.value[2] * 149597870700))

        deplocs = np.array(deplocs)

        arrlocs = []
        for matrix in rr_arr:
            arrlocs.append((matrix[0].value[0] * 149597870700,matrix[0].value[1] * 149597870700,matrix[0].value[2] * 149597870700))
        arrlocs = np.array(arrlocs)
        from matplotlib import pyplot as plt
        import numpy as np

        fig = plt.figure(figsize=(30, 30))
        ax = fig.add_subplot(1, 1, 1)
        ax.set_title("Trajectories from " + Initial + " to " + Destination, fontsize=16)
        c = ax.contourf(
            [D.to_datetime() for D in launch_span],
            [A.to_datetime() for A in arrival_span],
            c3_launch,
            c3_levels,
        )

        line = ax.contour(
            [D.to_datetime() for D in launch_span],
            [A.to_datetime() for A in arrival_span],
            c3_launch,
            c3_levels,
            colors="black",
            linestyles="solid",
        )

        cbar = fig.colorbar(c)
        cbar.set_label("Energy (km2 / s2)")
        ax.clabel(line, inline=1, fmt="%1.1f", colors="k", fontsize=10)

        time_levels = np.linspace(100, 500, 5)

        # ax.grid()
        fig.autofmt_xdate()

        ax.set_xlabel("Launch date", fontsize=10, fontweight="bold")
        ax.set_ylabel("Arrival date", fontsize=10, fontweight="bold")


        def plot_figure(dept, arr):
            fig.clear()
            ax = fig.add_subplot(1, 1, 1)
            ax.set_title("Trajectories from " + Initial + " to " + Destination, fontsize=16)
            line = ax.contour(
                [D.to_datetime() for D in launch_span],
                [A.to_datetime() for A in arrival_span],
                c3_launch,
                c3_levels,
                colors="black",
                linestyles="solid",
            )
            c = ax.contourf(
                [D.to_datetime() for D in launch_span],
                [A.to_datetime() for A in arrival_span],
                c3_launch,
                c3_levels,
            )

            cbar = fig.colorbar(c)
            cbar.set_label("km2 / s2")
            ax.clabel(line, inline=1, fmt="%1.1f", colors="k", fontsize=10)

            fig.autofmt_xdate()

            ax.set_xlabel("Launch date", fontsize=10, fontweight="bold")
            ax.set_ylabel("Arrival date", fontsize=10, fontweight="bold")

            ax.plot(launch_span[dept].to_datetime(), arrival_span[arr].to_datetime(), '+', mew=3, ms=20, c="r")
            c3 = str(c3_launch[dept][arr])
            c3 = float(c3.replace("km2 / s2", ""))

            dV = math.sqrt(c3 + (11.186 ** 2))
            departure_dv = dep_dv[0][dept].value

            arrival_dv = dv_arrival[0][arr]*1000

            vv_departure = vv_dep[0][dept].value * 1.495978707e11 / 86400  # Departure Planet Velocity
            # print(vv_arr[0][arr].value)
            vv_arrival = vv_arr[0][arr].value * 1.495978707e11 / 86400  # Arrival Planet Velocity
            rr_departure = rr_dep[0][dept].value * 1.495978707e11

            rr_arrival = rr_arr[dept][arr].value * 1.495978707e11

            departure_vel_tot = vv_departure + departure_dv

            arrival_vel_tot = vv_arrival + arrival_dv
            transfer_sma, transfer_ecc, transfer_inc, transfer_AOP, transfer_RAAN, T, EA = cart_2_kep(rr_departure,
                                                                                                      departure_vel_tot)
            fig.canvas.draw()
            return str(launch_span[dept].to_datetime()), str(arrival_span[
                                                                 arr].to_datetime()), departure_dv, arrival_dv, transfer_sma, transfer_ecc, transfer_inc, transfer_AOP, transfer_RAAN, rr_departure, rr_arrival



        col1 = [[sg.Text("   "),
                 sg.ReadFormButton('', button_color=sg.TRANSPARENT_BUTTON, image_filename="Up.png", image_size=(50, 50),
                                   image_subsample=2, border_width=0, key="-UP-")],
                [sg.ReadFormButton('', button_color=sg.TRANSPARENT_BUTTON, image_filename="Left.png",
                                   image_size=(50, 50), image_subsample=2, border_width=0, key="-LEFT-"),
                 sg.ReadFormButton('', button_color=sg.TRANSPARENT_BUTTON, image_filename="Right.png",
                                   image_size=(50, 50), image_subsample=2, border_width=0, key="-RIGHT-")],
                [sg.Text("   "), sg.ReadFormButton('', button_color=sg.TRANSPARENT_BUTTON, image_filename="Down.png",
                                                   image_size=(50, 50), image_subsample=2, border_width=0,
                                                   key="-DOWN-")]]

        col2 = [[sg.Text("Departure Burn Vector:", font=('Arial', 10, 'bold'), size=(21, 1)),
                 sg.Text("", key='_DEPDV_', size=(21, 1)),
                 sg.Text("m/s    Arrival Burn Vector:", font=('Arial', 10, 'bold'), size=(23, 1)),
                 sg.Text("", key='_ARRDV_', size=(23, 1)), sg.Text("m/s", font=('Arial', 10, 'bold'))],
                [sg.Text("Departure Burn Magnitude:", font=('Arial', 10, 'bold'), size=(21, 1)),
                 sg.Text("", key='_DEPMAG_', size=(21, 1)),
                 sg.Text("m/s    Arrival Burn Magnitude:       ", font=('Arial', 10, 'bold'), size=(23, 1)),
                 sg.Text("", key='_ARRMAG_', size=(23, 1)), sg.Text("m/s", font=('Arial', 10, 'bold'))],
                [sg.Text("Launch Date:", font=('Arial', 10, 'bold'), size=(21, 1)),
                 sg.Text("", key='_LAUNCH_', size=(21, 1)),
                 sg.Text("          Arrival Date:", font=('Arial', 10, 'bold'), size=(23, 1)),
                 sg.Text("", key='_ARRIVAL_', size=(23, 1))],
                [sg.Button("Add Departure Burn", size=(51, 1)),sg.Button("Add Arrival Burn", size=(51, 1))],
                [sg.Text("Semimajor Axis:", font=('Arial', 10, 'bold'), size=(21, 1)),
                 sg.Text("", key='_SMA_', size=(21, 1)),
                 sg.Text("km     Eccentricity: ", font=('Arial', 10, 'bold'), size=(23, 1)),
                 sg.Text("", key='_ECC_', size=(23, 1))],
                [sg.Text("Argument of Periapsis:", font=('Arial', 10, 'bold'), size=(21, 1)),
                 sg.Text("", key='_AOP_', size=(21, 1)),
                 sg.Text("Deg    RAAN: ", font=('Arial', 10, 'bold'), size=(23, 1)),
                 sg.Text("", key='_RAAN_', size=(23, 1)), sg.Text("Deg", font=('Arial', 10, 'bold'))],
                [sg.Text("Inclination:", font=('Arial', 10, 'bold'), size=(21, 1)),
                 sg.Text("", key='_INC_', size=(21, 1)),
                 sg.Text("Deg    Total Transit Delta V:", font=('Arial', 10, 'bold'), size=(23, 1)),
                 sg.Text("", key='_TOTDV_', size=(23, 1)), sg.Text("m/s", font=('Arial', 10, 'bold')),
                 sg.Text("", size=(65, 1)), sg.Submit()]]

        separatelayout1 = [[sg.Canvas(key='-CANVAS4-', size=(900, 500)), sg.Canvas(key='-CANVAS-', size=(500, 500))],
                           [sg.Column(col1), sg.Column(col2)]]
        sep1window = sg.Window('Transfer Orbit Designer', separatelayout1, finalize=True, grab_anywhere=False)
        OrbitalData = draw_figure(sep1window['-CANVAS4-'].TKCanvas, fig)

        fig1 = plt.figure()
        draw_figure(sep1window['-CANVAS-'].TKCanvas, fig1)
        # fig_agg = None
        dept = 1
        arr = 1

        ax1 = fig1.add_subplot(111, projection='3d')
        ax1.set_facecolor("black")
        fig1.set_facecolor("black")

        plt.axis('off')
        plt.grid(b=None)

        while True:
            sep1event, sep1values = sep1window.read()
            if sep1event == "Exit" or sep1event == sg.WIN_CLOSED:
                sep1window.close()
                break
            if sep1event == "-UP-":
                if arr < 50:
                    arr += 1
            if sep1event == "-LEFT-":
                if dept > 0:
                    dept -= 1
            if sep1event == "-RIGHT-":
                if dept < 50:
                    dept += 1
            if sep1event == "-DOWN-":
                if arr > 0:
                    arr -= 1
            if sep1event == "Submit":
                print("yoooooooooo")
            # print(arr)
            launch_date, arrival_date, departure_dV, arrival_dV, transfer_sma, transfer_ecc, transfer_inc, transfer_AOP, transfer_RAAN, dep_pos, arr_pos = plot_figure(
                dept, arr)

            plot_orbit(mu, transfer_sma, transfer_ecc, transfer_inc, transfer_AOP, transfer_RAAN, deplocs, arrlocs, dep_pos, arr_pos)

            sep1window.Element('_SMA_').update(round(transfer_sma / 1000, 2))
            # sep1window.Element('__').update(launch_date)
            sep1window.Element('_ECC_').update(round(transfer_ecc, 4))
            sep1window.Element('_INC_').update(round(transfer_inc, 2))
            sep1window.Element('_RAAN_').update(round(transfer_RAAN, 2))
            sep1window.Element('_AOP_').update(round(transfer_AOP, 2))
            sep1window.Element('_DEPDV_').update(departure_dV.round(2))
            sep1window.Element('_ARRDV_').update(arrival_dV.round(2))
            sep1window.Element('_DEPMAG_').update(round(np.linalg.norm(departure_dV), 2))
            sep1window.Element('_ARRMAG_').update(round(np.linalg.norm(arrival_dV), 2))
            sep1window.Element('_TOTDV_').update(round(np.linalg.norm(arrival_dV) + np.linalg.norm(departure_dV), 2))
            sep1window.Element('_LAUNCH_').update(launch_date)
            # sep1window.Element('_LAUNCHRNG_').update(launchrange)
            sep1window.Element('_ARRIVAL_').update(arrival_date)
    if event == "-DESTINATION-":
        sepcol1 = [[sg.Text(Destination + ' Orbital Elements', font=("Cooper", 26))],
                   [sg.Text('Reference Frame:                                 '),
                    sg.Listbox(ReferenceFrames[0:3], size=(28, 3))],
                   [sg.Text('Semi major axis:                                   '),
                    sg.InputText(Semimajoraxis / 1000, size=(20, 3)), sg.Text(' Kilometers')],
                   [sg.Text('Inclination:                                            '),
                    sg.InputText(Inclination, size=(20, 3)), sg.Text(' Degrees')],
                   [sg.Text('Eccentricity:                                         '),
                    sg.InputText(Eccentricity, size=(20, 3))],
                   [sg.Text('Right Ascension of the Ascending Node: '), sg.InputText(RAAN, size=(20, 3)),
                    sg.Text(' Degrees')],
                   [sg.Text('Arguement of Periapsis:                        '), sg.InputText(AOP, size=(20, 3)),
                    sg.Text(' Degrees')],
                   [sg.Checkbox('Landing Site', default=False), sg.Text('',key="-LDGSITENAME-"), sg.Button('Change',key="-LDGSITE-")],
                   [sg.Button('Update', key="-DEST-")]]

        w, h = figsize = (7, 7)  # figure size


        fig1 = matplotlib.figure.Figure(figsize)
        dpi = fig1.get_dpi()
        size = (w * dpi, h * dpi)
        ax1 = fig1.add_subplot(111, projection='3d')
        ax1.set_facecolor("black")
        fig1.set_facecolor("black")

        plt.axis('off')

        separatelayout1 = [[sg.Column(sepcol1), sg.Canvas(key='-CANVAS4-', size=size)]]
        sep1window = sg.Window('Initial Orbital Elements', separatelayout1, finalize=True, grab_anywhere=False)
        OrbitalData = draw_figure(sep1window['-CANVAS4-'].TKCanvas, fig1)
        while True:
            sep1event, sep1values = sep1window.read()
            if sep1event == "Exit" or sep1event == sg.WIN_CLOSED:
                sep1window.close()
                break

            elif event == "Submit":
                window.close()




            if sep1event == "-DEST-":


                refFrame = sep1values[0]
                Semimajoraxis = float(sep1values[1])
                Inclination = float(sep1values[2])
                Eccentricity = float(sep1values[3])
                RAAN = float(sep1values[4])
                AOP = float(sep1values[5])

                plot_orbit(mu, Semimajoraxis, Eccentricity, Inclination, AOP, RAAN)
                OrbitalData.draw()



    if event == "-BURN-":
        layout1 = [[sg.Text("Burn Name: "), sg.InputText("Name", size=(15, 3), key="-NAME-"), sg.Text('Select Engine: '),
         sg.Listbox(EngineList, size=(20, 3), key="-ENGINE-"), sg.Text("Set Time of Ignition"),
         sg.InputText(launchdate, size=(25, 3), key="-TIG-"), sg.Text(" GMT")],
        [sg.Text("Reference Frame"), sg.InputCombo(ReferenceFrames, key="-REF-"), sg.Text("Delta Vx"),
         sg.InputText("0", size=(6, 3), key="-DVX-"), sg.Text("m/s    "), sg.Text("Delta Vy"),
         sg.InputText("0", size=(6, 3), key="-DVY-"), sg.Text("m/s    "), sg.Text("Delta Vz"),
         sg.InputText("0", size=(6, 3), key="-DVZ-"), sg.Text("m/s")],
                   [sg.Text("")],
         [sg.Button("Visualize Burn", key="-VISUALIZE-"), sg.Button("Add Burn", key="-UPDATE-")],
                   [sg.Text("")],
         [sg.Text('Vary Burn Parameter          '),
         sg.Listbox(('Time of Ignition', 'Burn X dV', 'Burn Y dV', 'Burn Z dV', 'Engine Used'), size=(20, 5)),
         sg.Button('Run Differential Corrector', key='-CORRECTOR-', )],
        [sg.Table(BurnList, headings=Header, auto_size_columns=True, key='Table')],
                   [sg.Submit()]]
        window1 = sg.Window('Burn Planner', layout1, default_element_size=(40, 1), finalize=True, grab_anywhere=False)
        while True:

            event1, values1 = window1.read()
            if event1 == "Exit" or event1 == sg.WIN_CLOSED:
                window1.close()
                break
            elif event1 == "Submit":
                window1.close()
                break
            elif event1 == "-UPDATE-":
                BurnList.append([values["-NAME-"], values["-ENGINE-"][0], values["-TIG-"], values["-REF-"], values["-DVX-"], values["-DVY-"], values["-DVZ-"]])
                window['Table'].update(BurnList)
