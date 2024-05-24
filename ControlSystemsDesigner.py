import FreeSimpleGUI as sg
from PIL import ImageGrab
import os
import math
from matplotlib.pyplot import plot as plt
username = str(os.getlogin())

# This script is a rudimentary GUI that allows you to connect different objetcts, nodes and shapes, move them and
# delete things. This could be used to create a simulink-like tool if necessary that could be used for control block
# diagrams, Piping and instrumentation or for other uses.

# This was created based on graph demo scripts from PySimpleGUI (FreeSimpleGUI)

# def Pipe(lengths,bends,diameter, rho, v):
#     Re = Reynolds(V=v, D=diameter, rho=rho, mu=1E-3)
#     fd = friction_factor(Re, eD=0.0000025 / diameter)
#     length = sum(lengths)
#     K = K_from_f(fd=fd, L=length, D=diameter)
#     for bend in bends:
#         K += bend_rounded(Di=diameter, angle=bend, fd=fd)
#
#     K += entrance_sharp()
#     K += exit_normal()
#     return dP_from_K(K, rho=rho, V=v)


import math


def calculate_distance(point1, point2):
    x1, y1 = point1
    x2, y2 = point2
    return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)


def check_lines(lines, threshold=5):
    for i in range(len(lines)):
        for j in range(i + 1, len(lines)):
            for point1 in lines[i]:
                for point2 in lines[j]:
                    distance = calculate_distance(point1, point2)
                    if distance <= threshold:
                        return True


def connect(Upstream, Downstream, upstreamloc, downstreamloc, g, allines, color):
    if Upstream == "CylTank":
        upstreamoffset = [18, 160]
    if Upstream == "RegenEngine":
        upstreamoffset = [43, 26]
    if Upstream == "Preburner":
        upstreamoffset = [17, 3]
    if Upstream == "PumpL":
        upstreamoffset = [15, 72]
    if Upstream == "PumpR":
        upstreamoffset = [5, 72]
    if Upstream == "Turbine":
        upstreamoffset = [0, 40]
    if Downstream == "Preburner":
        downstreamoffset = [33, 39]
    if Downstream == "PumpL":
        downstreamoffset = [0, 35]
    if Downstream == "PumpR":
        downstreamoffset = [20, 35]
    if Downstream == "RegenEngine":
        downstreamoffset = [12, 26]
    if Downstream == "Turbine":
        downstreamoffset = [12, 64]
    if Downstream == "Engine":
        downstreamoffset = [25, 7]
    upstreamoutlet = [upstreamoffset[0] + upstreamloc[0], upstreamoffset[1] + upstreamloc[1]]
    downstreaminlet = [downstreamoffset[0] + downstreamloc[0], downstreamoffset[1] + downstreamloc[1]]
    allines.append(
        g.DrawLine(tuple(upstreamoutlet), tuple([upstreamoutlet[0], downstreaminlet[1]]), width=3, color=color))
    allines.append(
        g.DrawLine(tuple([upstreamoutlet[0], downstreaminlet[1]]), tuple(downstreaminlet), width=3, color=color))


def addComp(Component, g, location):
    with open("PROPULSION\\P_ID\\" + Component + ".png", "rb") as image:
        f = image.read()
        data = bytearray(f)
    data = bytes(data)
    g.draw_image(data=data, location=location)


def save_element_as_file(element, filename):
    """
    Saves any element as an image file.  Element needs to have an underlyiong Widget available (almost if not all of them do)
    :param element: The element to save
    :param filename: The filename to save to. The extension of the filename determines the format (jpg, png, gif, ?)
    """
    widget = element.Widget
    box = (widget.winfo_rootx(), widget.winfo_rooty(), widget.winfo_rootx() + widget.winfo_width(),
           widget.winfo_rooty() + widget.winfo_height())
    grab = ImageGrab.grab(bbox=box)
    grab.save(filename)


# from pylab import *


def main():
    sg.theme('Black')
    wirelist = []
    col = [[sg.T('Select Action', enable_events=True, font="Calibri 22 bold")],
           [sg.R('Set Objective', 1, key='-OBJECTIVE-', enable_events=True)],
           [sg.R('Select Motors', 1, key='-MOTOR-', enable_events=True)],
           [sg.R('Add Controller', 1, key='-CONTROLLER-', enable_events=True)],
           # [sg.R('Add Sensor', 1, key='-SENSOR-', enable_events=True)],
           [sg.R('Add Filter', 1, key='-HIGHPASS-', enable_events=True)],
           [sg.R('Add Summation', 1, key='-SUM-', enable_events=True)],
           [sg.R('Add Product', 1, key='-GROUND-', enable_events=True)],
           [sg.R('Connect', 1, key='-WIRE-', enable_events=True)],
           [sg.R('Rotate', 1, key='-ROTATE-', enable_events=True)],
           [sg.R('Move Item', 1, key='-MOVE-', enable_events=True)],
           [sg.R('Move All', 1, key='-MOVEALL-', enable_events=True)],
           [sg.R('Erase Item', 1, key='-ERASE-', enable_events=True)],
           [sg.R('Erase All', 1, key='-CLEAR-', enable_events=True)],
           [sg.R('Bring to front', 1, key='-FRONT-', enable_events=True)],
           [sg.R('Send to back', 1, key='-BACK-', enable_events=True)],
           [sg.R('Add Text', 1, key='-BLOCK-', enable_events=True)],
           [sg.B('Submit', key='-SAVE-'), sg.Cancel()]]
    dragfigurepng = []
    rot = []
    layout = [[sg.Graph((1100, 660), (0, 450), (450, 0),
                        key="-GRAPH-",
                        enable_events=True,
                        background_color='white',
                        drag_submits=True,
                        right_click_menu=[[], ['Erase item', ]]
                        ), sg.Col(col, key='-COL-')]]

    window = sg.Window("Electrical Systems Designer", layout, finalize=True)

    # get the graph element for ease of use later
    graph = window["-GRAPH-"]  # type: sg.Graph

    dragging = False
    start_point = end_point = prior_rect = prior_rect1 = None
    # graph.bind('<Button-3>', '+RIGHT+')

    while True:
        event, values = window.read()

        if event == sg.WIN_CLOSED:
            break  # exit

        if event in ('-MOVE-', '-MOVEALL-'):
            graph.set_cursor(cursor='fleur')  # not yet released method... coming soon!
        elif not event.startswith('-GRAPH-'):
            graph.set_cursor(cursor='left_ptr')  # not yet released method... coming soon!

        if event == "-GRAPH-":  # if there's a "Graph" event, then it's a mouse
            x, y = values["-GRAPH-"]
            if not dragging:
                start_point = (x, y)
                dragging = True
                drag_figures = graph.get_figures_at_location((x, y))
                # print(drag_figures)
                lastxy = x, y
            else:
                end_point = (x, y)


            if prior_rect:
                graph.delete_figure(prior_rect)

            if prior_rect1:
                graph.delete_figure(prior_rect1)
            delta_x, delta_y = x - lastxy[0], y - lastxy[1]
            lastxy = x, y
            if None not in (start_point, end_point):
                if values['-MOVE-']:
                    # print(drag_figures)
                    for fig in drag_figures:
                        graph.move_figure(fig, delta_x, delta_y)
                        graph.update()
                if values['-ROTATE-']:
                    from PIL import Image
                    for fig in drag_figures:

                        imagename = dragfigurepng[fig - 1]
                        graph.delete_figure(fig)

                        if not os.path.isfile(
                                "C:\\Users\\" + username + "\\AppData\\Roaming\\FreeCAD\\Mod\\SpacecraftDesigner\\Electrical\\" + str(
                                        rot[fig - 1]) + imagename):
                            with Image.open(
                                    "C:\\Users\\" + username + "\\AppData\\Roaming\\FreeCAD\\Mod\\SpacecraftDesigner\\Electrical\\" + imagename) as im:
                                newim = im.rotate(rot[fig - 1], expand=True)
                                newim.save(
                                    "C:\\Users\\" + username + "\\AppData\\Roaming\\FreeCAD\\Mod\\SpacecraftDesigner\\Electrical\\" + str(
                                        rot[fig - 1]) + imagename)

                        with open(
                                "C:\\Users\\" + username + "\\AppData\\Roaming\\FreeCAD\\Mod\\SpacecraftDesigner\\Electrical\\" + str(
                                        rot[fig - 1]) + imagename, "rb") as image:
                            f = image.read()
                            data = bytearray(f)
                        data = bytes(data)
                        graph.draw_image(data=data, location=(values["-GRAPH-"][0], values["-GRAPH-"][1]))
                        dragfigurepng.append(str(rot[fig - 1]) + imagename)
                        rot.append(rot[fig - 1] + 90)

                elif values['-SUM-']:

                    with open(
                            "C:\\Users\\" + username + "\\AppData\\Roaming\\FreeCAD\\Mod\\SpacecraftDesigner\\Electrical\\SPST-Switch.png",
                            "rb") as image:
                        f = image.read()
                        data = bytearray(f)
                    data = bytes(data)
                    graph.draw_image(data=data, location=(25, 25))
                    dragfigurepng.append("SPST-Switch.png")

                elif values['-OBJECTIVE-']:
                    print("IMPLEMENT FREECAD A2PLUS SENSOR DEFINITION")
                    sensorlist = ["Rotary encoder 1", "Accelerometer 1"]
                    # There is always a sensor added to an actuator
                    # If statements for human triggers
                    # Add 2dof tracker directly in FreeCAD i.e. something you can slap on the side of a vehicle
                    # And how about for dynamics and control for instance sensor input for ehicle rotation for CMG?
                    layout1 = [
                        [sg.Listbox(values=(sensorlist), size=(40, 3))],
                        [sg.Submit(tooltip='Submit', key="-SUBMIT-"), sg.Cancel()]]

                    window1 = sg.Window('Select Sensor', layout1, grab_anywhere=False)

                    event1, values1 = window1.read()
                    if event1 == ["-SUBMIT-"]:
                        with open(
                                "C:\\Users\\" + username + "\\AppData\\Roaming\\FreeCAD\\Mod\\SpacecraftDesigner\\ELECTRICAL\\SingleCellBattery_Michel_Bakni.png",
                                "rb") as image:
                            f = image.read()
                            data = bytearray(f)
                        data = bytes(data)
                        graph.draw_image(data=data, location=(values["-GRAPH-"][0], values["-GRAPH-"][1]))
                    elif event1 == "Cancel":
                        window1.close()
                elif values["-BLOCK-"]:
                    layout = [
                        [sg.Text('Text', size=(15, 1)), sg.InputText()],
                        [sg.Submit(), sg.Cancel()]]

                    window44 = sg.Window('Add Text', layout)
                    event11, values11 = window44.read()
                    window44.close()
                    if values11:
                        graph.draw_text(values11[0], location=(values["-GRAPH-"][0], values["-GRAPH-"][1]))
                elif values["-CONTROLLER-"]:
                    sg.SetOptions(tooltip_time=20)

                    my_tooltip = """A Proportional, Integral, Derivative controller (PID) is an algorithm that is often used to control motors and actuators \nbased on where the motor should be and where the motor is (error).
                    
                    PID Controllers have three components:

                    The Proportional (P) term produces a control signal proportional to the current error.
                    Increasing this results in a stronger response to errors.
                    
                    The Integral (I) term is based on the cumulative sum of past errors.
                    It is useful for eliminating steady-state error and drift and addressing system bias.
                    
                    The Derivative (D) term is based on how the error is changing over time.
                    It can be used to stabilize the system prevent overshoot, which is when a system responds a bit too much.
                    
                    PID controllers continuously adjust the control input based on real-time evaluations of error, integral, and derivative. 
                    They are essential for achieving stable and accurate responses in dynamic systems."""
                    # MPCTooltip =
                    layout = [
                        [sg.Text('Text', size=(15, 1)), sg.InputText("Controller Name")],
                        [sg.Button('Proporional, Integral, Derivative', tooltip=my_tooltip,key="-PID-")],
                        [sg.Button('Linear Quadraic Regulator', tooltip=my_tooltip,key="-LQR-")],
                        [sg.Button('Model Predicive Controller', tooltip=my_tooltip,key="-MPC-")],
                        [sg.Submit(), sg.Cancel()]]

                    window44 = sg.Window('Select Controller Type', layout)
                    event11, values11 = window44.read()
                    window44.close()
                    if values11:
                        print(event11)
                        if event11 == "-MPC-":
                            # print("MPC")
                            type = "MPC"
                            layout55 = [
                                [sg.Text('Prediction Horizon', size=(15, 1)), sg.InputText("1.0",size=(15, 1))],
                                [sg.Text('Control Horizon', size=(15, 1)), sg.InputText("1.0",size=(15, 1))],
                                [sg.Text('Error Weight', size=(15, 1)), sg.InputText("1.0",size=(15, 1))],
                                [sg.Submit(), sg.Cancel()]]

                            window55 = sg.Window('Select PID Controller Gains', layout55)
                            event55, values55 = window55.read()
                            window55.close()
                        elif event11 == "-PID-":
                            type = "PID"
                            layout55 = [
                                [sg.Text('Proportional Gain', size=(15, 1)), sg.InputText("1.0",size=(15, 1))],
                                [sg.Text('Integral Gain', size=(15, 1)), sg.InputText("1.0",size=(15, 1))],
                                [sg.Text('Derivative Gain', size=(15, 1)), sg.InputText("1.0",size=(15, 1))],
                                [sg.Submit(), sg.Cancel()]]

                            window55 = sg.Window('Select PID Controller Gains', layout55)
                            event55, values55 = window55.read()
                            window55.close()

                        elif event11 == "-LQR-":
                            type = "LQR"
                            layout55 = [
                                [sg.Text('Proportional Gain', size=(15, 1)), sg.InputText("1.0",size=(15, 1))],
                                [sg.Text('Integral Gain', size=(15, 1)), sg.InputText("1.0",size=(15, 1))],
                                [sg.Text('Derivative Gain', size=(15, 1)), sg.InputText("1.0",size=(15, 1))],
                                [sg.Submit(), sg.Cancel()]]

                            window55 = sg.Window('Select PID Controller Gains', layout55)
                            event55, values55 = window55.read()
                            window55.close()
                        print(event11)
                        if event11 and event11 != "Cancel":
                            graph.draw_rectangle((values["-GRAPH-"][0]-50,  values["-GRAPH-"][1]-20), (values["-GRAPH-"][0]+50,  values["-GRAPH-"][1]+20), fill_color="white")
                            graph.draw_text(type, location=(values["-GRAPH-"][0], values["-GRAPH-"][1]))

                elif values['-MOTOR-']:
                    print("IMPLEMENT FREECAD A2PLUS JOINT MOTOR DEFINITION")
                    with open(
                            "C:\\Users\\" + username + "\\AppData\\Roaming\\FreeCAD\\Mod\\SpacecraftDesigner\\ELECTRICAL\\Motor.png",
                            "rb") as image:
                        f = image.read()
                        data = bytearray(f)
                    data = bytes(data)
                    graph.draw_image(data=data, location=(values["-GRAPH-"][0], values["-GRAPH-"][1]))


                elif values['-WIRE-']:
                    prior_rect = graph.draw_line(start_point, end_point, color="blue", width=4)
                    # print(end_point)
                    # wirelist.append([start_point,end_point])
                    # print("WIRE")

                elif values['-ERASE-']:
                    for figure in drag_figures:
                        # print(figure)
                        graph.delete_figure(figure)

                elif values['-CLEAR-']:
                    graph.erase()
                elif values['-MOVEALL-']:
                    graph.move(delta_x, delta_y)
                elif values['-FRONT-']:
                    for fig in drag_figures:
                        graph.bring_figure_to_front(fig)
                elif values['-BACK-']:
                    for fig in drag_figures:
                        graph.send_figure_to_back(fig)
            # window["-INFO-"].update(value=f"mouse {values['-GRAPH-']}")
        elif event.endswith('+UP'):  # The drawing has ended because mouse up
            true_elements = [key for key, value in values.items() if value]
            # print(true_elements)
            if "-WIRE-" in true_elements:
                wirelist.append([start_point, end_point])
                # for wire in wirelist:

                print(wirelist)
                # print(start_point)
                # print(end_point)
            # print("COOL")
            # window["-INFO-"].update(value=f"grabbed rectangle from {start_point} to {end_point}")
            start_point, end_point = None, None  # enable grabbing a new rect
            dragging = False
            prior_rect = None
            prior_rect1 = None
        # elif event.endswith('+RIGHT+'):  # Righ click
        # window["-INFO-"].update(value=f"Right clicked location {values['-GRAPH-']}")
        # elif event.endswith('+MOTION+'):  # Righ click
        #     window["-INFO-"].update(value=f"mouse freely moving {values['-GRAPH-']}")
        elif event == '-SAVE-':
            # filename = sg.popup_get_file('Choose file (PNG, JPG, GIF) to save to', save_as=True)
            filename = r'test.jpg'
            save_element_as_file(window['-GRAPH-'], filename)
        elif event == 'Erase item':
            # window["-INFO-"].update(value=f"Right click erase at {values['-GRAPH-']}")
            if values['-GRAPH-'] != (None, None):
                drag_figures = graph.get_figures_at_location(values['-GRAPH-'])
                for figure in drag_figures:
                    graph.delete_figure(figure)

    window.close()


main()