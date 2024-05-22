import FreeCAD
import FreeCADGui
import sys
import os
import math
import re
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
import csv
from scipy.optimize import curve_fit
import numpy
import warnings
from datetime import timedelta
from os.path import exists
from datetime import datetime
import zipfile

FreeCADPath = FreeCAD.__path__[1]
FreeCADPathbin = FreeCADPath.replace("lib","bin")
FreeCADPath = FreeCADPathbin + "\\Scripts\\pip"
# import FreeSimpleGUI as sg
try:
    import FreeSimpleGUI as sg
except:
    import subprocess
    print("pip installing necessary packages for Spacecraft Designer\n"
          "This may take a minute...")
    def install_requirements():
        try:
            FreeCAD.Console.PrintMessage("Installing requirements...\n")  # Use FreeCAD's console
            subprocess.check_call([FreeCADPath, "install", "FreeSimpleGUI"])
            subprocess.check_call([FreeCADPath, "install", "requests"])
            FreeCAD.Console.PrintMessage("Installation complete!\n")
        except subprocess.CalledProcessError as e:
            FreeCAD.Console.PrintError(f"Error installing requirements: {e}\n")

    install_requirements()
    import requests
    # We also need to download tcl/tk which is what is necessary for FreeSimpleGUI for this workbench GUI
    url = "https://github.com/VallesMarinerisExplorer/tcl/archive/refs/heads/main.zip"
    response = requests.get(url)
    response.raise_for_status()  # Raise an exception for HTTP errors

    filename = url.split("/")[-1]  # Extract filename from URL

    with open(filename, 'wb') as file:
        file.write(response.content)

    with zipfile.ZipFile(filename, 'r') as zip_ref:
        zip_ref.extractall(FreeCADPathbin)

    import shutil

    # Define the source and destination directories
    source_dir = FreeCADPathbin + "\\tcl-main\\tcl"
    destination_dir = FreeCADPathbin.replace("bin","lib")

    # Get the subfolders of the source parent directory
    subfolders = [f for f in os.listdir(source_dir) if os.path.isdir(os.path.join(source_dir, f))]

    # Copy each subfolder to the destination directory
    for subfolder in subfolders:
        source_subfolder = os.path.join(source_dir, subfolder)
        try:
            shutil.copytree(source_subfolder, os.path.join(destination_dir, subfolder))
        except shutil.Error as e:
            print(f"Error copying {subfolder}: {e}")
        except OSError as e:
            print(f"OS error encountered for {subfolder}: {e}")

    src_files = os.listdir(source_dir)
    for file_name in src_files:
        full_file_name = os.path.join(source_dir, file_name)
        if os.path.isfile(full_file_name):
            shutil.copy(full_file_name, destination_dir)
    shutil.rmtree(source_dir)
    os.remove(filename)
    import FreeSimpleGUI as sg


username = str(os.getlogin())

sg.ChangeLookAndFeel('Black')
App=FreeCAD
SCDesignerPath = "C:\\Users\\" + username + "\\AppData\\Roaming\\FreeCAD\\Mod\\SpacecraftDesigner"

class vehicle:
    def __init__(self):
        self.name = ""
        self.destination = ""
        self.launch_date = ""
        self.launch_vehicle = ""
        self.cost = ""
        self.mass = 0
        self.system_list = {}
        self.TargetLatitude = 0
        self.TargetLongitude = 0

new_vehicle = vehicle()
def addPowerSystem(Name,Volts,PeakAmps):
    with open(SCDesignerPath + "\\Vehicles\\" + new_vehicle.name + "PowerBudget.csv", "a") as f:
        f.write(Name + "," + Volts + "," + PeakAmps + "\n")
    f.close()

def MeridionalStress(pressure, axialradius, thickness):
    MeridStress = pressure*axialradius/(2*thickness)
    return MeridStress

def HoopStress(pressure, axialradius, thickness, merradius):
    # Hoop stress according to eqn 11-47 of Space Mission Analysis and Design Second Edition
    HoopStressReturn = (pressure*axialradius/(2*thickness))*(2-(axialradius/merradius))
    return HoopStressReturn

def Properties(Name, Selector):
    import pandas as pd
    xls_file = pd.ExcelFile('MECHANICAL\\Materials.xlsx')
    df = xls_file.parse('Sheet1')
    Name = df[df['NAME'].str.match(Name)]
    Columns = ['MATERIAL', 'NAME', 'GEOMETRY', 'DENSITY_(kg/m^3)', 'TENSILE_ULT_STRENGTH', 'TENSILE_YIELD_STRENGTH',
                  'YOUNGS_MODULUS',	'ELONGATION_PERCENT', 'COEFF_THERMAL_EXP', 'POISSONS RATIO', 'HEAT TRANSFER COEFF', 'VICKERS HARDNESS']
    Column = Columns.index(Selector)
    return Name.iloc[0,Column]

class Body():
    def __init__(self, Name):
        self.Name = Name
        if self.Name == "Mercury":
            self.orbit_rad = 0.38709893
            self.orbit_per = self.orbit_rad**1.5
            self.orbit_vel = 2*math.pi*self.orbit_rad/self.orbit_per
            self.mean_longJ2000 = 252.25084
            self.mass = 3.3e23
            self.radius = 2440
            self.soi = 111631
        if self.Name == "Venus":
            self.orbit_rad = 0.72333199
            self.orbit_per = self.orbit_rad**1.5
            self.orbit_vel = 2*math.pi*self.orbit_rad/self.orbit_per
            self.mean_longJ2000 = 181.97973
            self.mass = 4.869e24
            self.radius = 6052
            self.soi = 612171
        if self.Name == "Earth":
            self.orbit_rad = 1
            self.orbit_per = 1
            self.orbit_vel = 2*math.pi*self.orbit_rad/self.orbit_per
            self.mean_longJ2000 = 100.46435
            self.mass = 5.972e24
            self.radius = 6378
            self.soi = 918347
        if self.Name == "Mars":
            self.orbit_rad = 1.52366231
            self.orbit_per = self.orbit_rad**1.5
            self.orbit_vel = 2*math.pi*self.orbit_rad/self.orbit_per
            self.mean_longJ2000 = 355.45332
            self.mass = 6.4219e23
            self.radius = 3397
            self.soi = 573473
        if self.Name == "Jupiter":
            self.orbit_rad = 5.20336301
            self.orbit_per = self.orbit_rad**1.5
            self.orbit_vel = 2*math.pi*self.orbit_rad/self.orbit_per
            self.mean_longJ2000 = 34.40438
            self.mass = 1.9e27
            self.radius = 71492
            self.soi = 47901004
        if self.Name == "Saturn":
            self.orbit_rad = 9.53707032
            self.orbit_per = self.orbit_rad**1.5
            self.orbit_vel = 2*math.pi*self.orbit_rad/self.orbit_per
            self.mean_longJ2000 = 49.94432
            self.mass = 5.68e26
            self.radius = 60268
            self.soi = 54164329
        if self.Name == "Uranus":
            self.orbit_rad = 19.19126393
            self.orbit_per = self.orbit_rad**1.5
            self.orbit_vel = 2*math.pi*self.orbit_rad/self.orbit_per
            self.mean_longJ2000 = 313.23218
            self.mass = 8.683e25
            self.radius = 25559
            self.soi = 51419820
        if self.Name == "Neptune":
            self.orbit_rad = 30.06896348
            self.orbit_per = self.orbit_rad**1.5
            self.orbit_vel = 2*math.pi*self.orbit_rad/self.orbit_per
            self.mean_longJ2000 = 304.8803
            self.mass = 1.0247e26
            self.radius = 24766
            self.soi = 86082764



def AtlasMass(apogeealt, config, inclination):

    x = [5000, 7500, 10000, 12500, 15000, 17500, 20000, 22500, 25000, 27500, 30000, 35000, 35786, 40000, 45000,
         50000, 55000, 60000, 65000, 70000, 75000, 80000, 85000, 90000, 95000, 100000, 105000, 110000, 115000,
         120000, 125000, 130000, 135000, 140000, 145000, 150000]

    if config == 401:
        y = [7827, 7135, 6625, 6238, 5933, 5688, 5487, 5318, 5176, 5054, 4948, 4774, 4750, 4636, 4525, 4433, 4356,
             4290, 4234, 4184, 4141, 4103, 4069, 4038, 4011, 3986, 3963, 3942, 3923, 3905, 3889, 3874, 3860, 3847,
             3835, 3823]
    if config == 411:
        y = [9729, 8869, 8242, 7766, 7394, 7095, 6847, 6642, 6468, 6321, 6191, 5978, 5950, 5810, 5674, 5562, 5467,
             5387, 5318, 5258, 5205, 5158, 5117, 5079, 5046, 5015, 4987, 4962, 4939, 4917, 4897, 4879, 4862, 4846,
             4831, 4817]
    if config == 421:
        y = [11263, 10260, 9529, 8977, 8545, 8199, 7915, 7680, 7481, 7311, 7164, 6922, 6890, 6732, 6579, 6452, 6348,
             6258, 6181, 6113, 6054, 6001, 5955, 5913, 5875, 5841, 5810, 5781, 5755, 5731, 5709, 5688, 5669, 5651,
             5634, 5619]
    if config == 431:
        y = [12573, 11453, 10637, 10021, 9541, 9156, 8841, 8579, 8358, 8169, 8005, 7736, 7700, 7525, 7355, 7215,
             7097, 6997, 6912, 6837, 6771, 6713, 6662, 6615, 6573, 6536, 6501, 6470, 6441, 6414, 6389, 6367, 6348,
             6329, 6310, 6293]
    if config == 501:
        y = [6392, 5783, 5335, 5002, 4773, 4570, 4401, 4262, 4115, 4021, 3940, 3796, 3775, 3682, 3583, 3506, 3442,
             3382, 3337, 3295, 3253, 3223, 3195, 3168, 3145, 3123, 3104, 3085, 3069, 3054, 3040, 3027, 3014, 3003,
             2992, 2982]
    if config == 511:
        y = [8807, 7988, 7394, 6944, 6594, 6313, 6083, 5893, 5731, 5593, 5473, 5277, 5250, 5123, 4998, 4895, 4809,
             4735, 4672, 4617, 4569, 4526, 4488, 4454, 4423, 4395, 4370, 4347, 4326, 4306, 4288, 4271, 4255, 4241,
             4227, 4215]
    if config == 521:
        y = [10790, 9785, 9058, 8512, 8088, 7749, 7475, 7245, 7051, 6885, 6742, 6507, 6475, 6322, 6173, 6050, 5947,
             5860, 5784, 5719, 5662, 5611, 5566, 5525, 5489, 5456, 5425, 5398, 5373, 5349, 5328, 5308, 5289, 5272,
             5256, 5241]
    if config == 531:
        y = [12455, 11288, 10446, 9806, 9323, 8933, 8614, 8350, 8129, 7940, 7776, 7508, 7475, 7301, 7131, 6991,
             6875, 6775, 6690, 6616, 6551, 6493, 6442, 6396, 6354, 6317, 6283, 6252, 6223, 6197, 6172, 6150, 6129,
             6109, 6091, 6074]
    if config == 541:
        y = [13885, 12561, 11610, 10901, 10345, 9913, 9562, 9268, 9021, 8810, 8627, 8330, 8290, 8096, 7909, 7754,
             7624, 7514, 7424, 7342, 7270, 7206, 7150, 7099, 7053, 7012, 6974, 6940, 6908, 6879, 6852, 6827, 6804,
             6783, 6763, 6744]
    if config == 551:
        y = [14988, 13534, 12497, 11726, 11131, 10659, 10275, 9955, 9690, 9461, 9265, 8944, 8900, 8691, 8488, 8322,
             8181, 8064, 7962, 7873, 7796, 7727, 7666, 7611, 7562, 7517, 7481, 7444, 7410, 7379, 7350, 7323, 7298,
             7275, 7253, 7233]
    with warnings.catch_warnings():
        warnings.simplefilter('ignore', np.RankWarning)
        coeff = numpy.polyfit(x, y, 21)
        p = np.poly1d(coeff)
        masslim = p(apogeealt)
    return masslim

def AntaresMass(apogeealt, config, inclination):
    if config == 232:
        x = [1375.026864, 1681.203525, 1885.321298, 2242.527402, 2586.976144, 3001.590372, 3246.106455, 3639.458414,
             4054.072641, 4436.793467, 4819.514292, 5266.021921, 5776.316355, 6286.610789, 6796.905222, 7370.98646,
             8008.854502, 8710.509349, 9475.950999, 10305.17945, 11261.98152, 12410.14399, 13749.66688, 15152.97657,
             16556.28627, 17959.59596, 19362.90565, 20766.21534, 22169.52504, 23572.83473, 24976.14442, 26379.45412,
             27782.76381, 29186.0735, 30589.38319, 31992.69289, 33396.00258, 34799.31227, 36202.62196, 37605.93166,
             39009.24135, 40412.55104, 41815.86074, 43219.17043, 44622.48012, 46025.78981, 47429.09951, 48832.4092,
             50235.71889, 51639.02858, 53042.33828, 54445.64797, 55848.95766, 57252.26735, 58655.57705, 60058.88674,
             61462.19643, 62865.50613, 64268.81582, 65672.12551, 67075.4352, 68478.7449, 69882.05459, 71285.36428,
             72688.67397, 74091.98367, 75495.29336, 76898.60305, 78301.91274, 79705.22244, 81108.53213, 82511.84182,
             83915.15152, 85318.46121, 86721.7709, 88125.08059, 89528.39029, 90931.69998, 92335.00967, 93738.31936,
             95141.62906, 96544.93875, 97948.24844, 99287.77133]

        y = [6884.159239, 6705.16221, 6557.908497, 6389.051693, 6215.124777, 6021.688948, 5894.385027, 5735.668449,
             5572.543078, 5422.644088, 5274.949495, 5115.681818, 4945.392157, 4788.328877, 4639.532086, 4483.130125,
             4327.058824, 4172.75104, 4023.954248, 3882.085561, 3742.618093, 3596.962567, 3449.909253, 3321.853832,
             3210.030789, 3112.035327, 3026.063847, 2949.711554, 2880.573651, 2819.852536, 2764.542214, 2712.839086,
             2667.14795, 2626.266407, 2584.783666, 2549.914114, 2513.842165, 2483.181008, 2448.912656, 2421.858694,
             2389.995139, 2367.75077, 2343.702803, 2321.458435, 2304.624858, 2290.196078, 2270.356506, 2256.528926,
             2246.909739, 2237.290553, 2228.272565, 2218.653379, 2204.825798, 2194.004213, 2181.98023, 2172.962243,
             2162.140658, 2152.521471, 2140.497488, 2129.675903, 2122.461514, 2115.247124, 2108.032734, 2103.22314,
             2096.60995, 2091.199157, 2080.377573, 2073.764382, 2065.347594, 2058.734403, 2052.722411, 2047.311619,
             2041.900826, 2038.894831, 2032.28164, 2027.472047, 2023.263653, 2013.043267, 2007.632474, 1999.215686,
             1993.804894, 1988.995301, 1985.989305, 1979.376114]

    if config == 233:
        x = [609.5852138, 915.7618741, 1119.879648, 1438.813669, 1706.718246, 2140.468515, 2446.645175, 2905.910165,
             3288.630991, 3798.925424, 4245.433054, 4691.940683, 5138.448313, 5648.742747, 6159.03718, 6733.118418,
             7370.98646, 8008.854502, 8646.722545, 9348.377391, 10177.60585, 11134.40791, 12282.57038, 13622.09327,
             15025.40297, 16428.71266, 17832.02235, 19235.33204, 20638.64174, 22041.95143, 23445.26112, 24848.57081,
             26251.88051, 27655.1902, 29058.49989, 30461.80959, 31865.11928, 33268.42897, 34671.73866, 36075.04836,
             37478.35805, 38881.66774, 40284.97743, 41688.28713, 43091.59682, 44494.90651, 45898.2162, 47301.5259,
             48704.83559, 50108.14528, 51511.45498, 52914.76467, 54318.07436, 55721.38405, 57124.69375, 58528.00344,
             59931.31313, 61334.62282, 62737.93252, 64141.24221, 65544.5519, 66947.86159, 67777.09005]

        y = [6773.939394, 6607.286988, 6456.506239, 6311.016043, 6141.71836, 5960.516934, 5789.896613, 5590.178253,
             5426.171123, 5230.861557, 5054.509804, 4889.180036, 4735.423351, 4571.746881, 4413.030303, 4247.700535,
             4081.048128, 3927.622103, 3788.745098, 3647.002377, 3505.13369, 3365.666221, 3221.994652, 3078.368174,
             2951.515152, 2839.090909, 2738.089451, 2649.713175, 2566.747691, 2494.002593, 2426.668287, 2364.744774,
             2308.232053, 2255.927726, 2209.635391, 2165.747853, 2124.86631, 2091.800357, 2055.127208, 2028.674445,
             1998.013288, 1976.971317, 1956.530546, 1934.286177, 1915.047804, 1900.017825, 1878.374656, 1857.332685,
             1842.302706, 1828.475126, 1811.641549, 1794.807973, 1784.587587, 1773.164803, 1760.539621, 1744.307244,
             1728.676065, 1719.056879, 1710.038892, 1701.622103, 1693.806514, 1682.38373, 1678.475936]

    with warnings.catch_warnings():
        warnings.simplefilter('ignore', np.RankWarning)
        coeff = numpy.polyfit(x, y, 30)
        p = np.poly1d(coeff)
        masslim = p(apogeealt)
    return masslim

def Falcon9MassCirc(apogeealt, config, inclination):

    if config == "RTLS" and inclination == 28.5:
        x = [399.9794132, 481.7548257, 506.1310516, 556.9202175, 654.4280656, 721.4628421, 754.9802304, 797.6395401,
             822.0150069, 855.5323951, 948.4618062, 998.7348981, 1041.388227, 1086.073094, 1113.495868, 1149.548193,
             1196.771841, 1231.807543, 1298.915736, 1349.100459, 1431.356819, 1497.650438, 1600.867641, 1697.77789,
             1796.718181, 1896.797531, 1996.607575]

        y = [11680.50006, 11365.56956, 11286.36111, 11101.76376, 10774.17717, 10555.78611, 10446.59058, 10304.6364,
             10228.19952, 10119.004, 9835.09562, 9682.221879, 9562.106797, 9434.712013, 9347.355589, 9245.439762,
             9111.285255, 9016.129151, 8844.271282, 8699.462116, 8481.071058, 8317.277764, 8320.917615, 8322.737541,
             8322.737541, 8310.866329, 8313.554521]

    if config == "ASDS" and inclination == 28.5:
        x = [399.4351444, 430.9309628, 483.7609219, 501.0279989, 616.8361376, 656.4556164, 699.1250938, 744.8305145,
             796.6392219, 848.4419483, 894.1521538, 924.6246273, 999.5000358, 1067.842083, 1099.835319, 1151.635553,
             1193.987441, 1220.192488, 1253.709876, 1295.354912, 1323.78897, 1379.647296, 1407.577954, 1433.474084,
             1488.32038, 1508.629032, 1544.681357, 1592.919921, 1620.849084, 1672.134954, 1708.287959, 1738.14499,
             1791.243666, 1818.879192, 1862.03891, 1898.8568, 1947.339586, 1998.620971]

        y = [15520.54284, 15382.2285, 15156.55774, 15098.32013, 14645.15868, 14486.82516, 14307.74449, 14159.23857,
             13957.22685, 13777.05422, 13611.07702, 13504.0654, 13240.43619, 13012.68552, 12910.76969, 12739.6967,
             12608.66206, 12521.30564, 12412.11011, 12268.33599, 12193.71905, 12026.2859, 11937.10956, 11866.13246,
             11688.68973, 11640.4617, 11538.54587, 11403.87139, 11320.15482, 11174.56078, 11075.55683, 10992.56823,
             10844.3743, 10774.17717, 10657.70194, 10539.40678, 10439.31088, 10310.09617]

    if config == "RTLS" and inclination == 38:
        x = [404.6643957, 467.3105337, 505.3767633, 596.5181932, 643.9378393, 700.2758592, 741.3873873, 802.2933548,
             844.927532, 918.0146929, 954.5582734, 1007.546465, 1083.475905, 1103.777894, 1146.412071, 1195.745905,
             1219.499232, 1264.163608, 1301.722288, 1345.879114, 1396.735597, 1423.534223, 1499.734812, 1598.638879,
             1699.133726, 1799.846093, 1900.123418, 1996.050317]

        y = [11379.78846, 11155.35308, 11040.79752, 10714.96628, 10555.30015, 10362.95777, 10227.99855, 10036.29333,
             9900.696949, 9682.495883, 9573.39535, 9426.071401, 9209.325008, 9144.592025, 9016.98263, 8883.007175,
             8809.691617, 8693.317715, 8585.315049, 8471.479964, 8328.275957, 8264.188951, 8084.2113, 8106.902349,
             8102.356493, 8106.772467, 8111.448204, 8092.686441]

    if config == "ASDS" and inclination == 38:
        x = [397.2686711, 496.2408682, 604.3489605, 696.2154614, 753.5685808, 815.9971974, 875.3805157, 903.2957508,
             953.0356242, 1000.237749, 1048.962523, 1097.687297, 1115.959087, 1149.457369, 1198.182143, 1219.499232,
             1254.520163, 1324.562026, 1377.854747, 1402.217134, 1435.715416, 1491.292112, 1508.802577, 1548.391456,
             1595.593581, 1626.046565, 1675.278889, 1705.224323, 1761.562342, 1796.583274, 1833.126854, 1884.389377,
             1907.736664, 1954.938789, 1995.441258]

        y = [15137.52255, 14747.48814, 14313.81352, 13968.3285, 13773.76588, 13533.74471, 13337.36375, 13240.99161,
             13064.61241, 12886.9344, 12737.31081, 12577.2967, 12519.10975, 12410.00921, 12246.35841, 12191.80815,
             12082.70761, 11864.50655, 11700.85575, 11641.94146, 11537.20495, 11373.55415, 11326.27725, 11209.90335,
             11077.16437, 10991.70228, 10853.50827, 10778.95624, 10620.76047, 10529.38877, 10435.28956, 10311.64229,
             10244.36363, 10118.89802, 10009.79748]

    if config == "RTLS" and inclination == 45:
        x = [402.2547626, 444.0819221, 500.9050035, 538.4488251, 602.5044322, 702.8298818, 739.3590055, 791.8696209,
             842.8581894, 896.6371771, 952.4455606, 1000.716188, 1027.025855, 1073.448283, 1125.958898, 1165.532116,
             1202.737705, 1244.67855, 1276.134185, 1346.655687, 1398.405279, 1499.767034, 1599.31546, 1699.77055,
             1800.22564, 1899.158684, 1998.091727]

        y = [11112.98892, 10966.49631, 10797.6009, 10639.47025, 10434.57542, 10136.63531, 9985.520864, 9832.980184,
             9658.571852, 9495.114467, 9331.674203, 9182.219869, 9113.755278, 8970.724716, 8830.477368, 8721.537166,
             8606.890747, 8503.656763, 8412.860421, 8242.259346, 8106.103355, 7845.584364, 7843.112269, 7842.745597,
             7850.216941, 7850.411779, 7852.547304]

    if config == "ASDS" and inclination == 45:
        x = [400.7035877, 441.0378285, 500.3976545, 555.1913401, 606.0277039, 663.2566644, 698.9160471, 804.8070189,
             855.034564, 897.651875, 931.1369051, 979.8424034, 1002.673106, 1046.812464, 1080.297494, 1103.635545,
             1132.047086, 1184.811375, 1203.075937, 1235.546269, 1290.339955, 1322.302938, 1343.611594, 1396.883233,
             1416.669841, 1456.243059, 1497.947142, 1530.823353, 1588.661132, 1605.403647, 1647.513609, 1698.248503,
             1776.633915, 1808.705616, 1855.019326, 1898.651335, 1943.298042, 1997.787318]

        y = [14779.795, 14638.079, 14401.81933, 14191.01841, 13979.45562, 13776.68868, 13652.10488, 13264.29478,
             13089.88003, 12935.0704, 12828.26432, 12664.76413, 12599.39231, 12446.781, 12326.86203, 12257.85202,
             12174.31493, 11999.92158, 11919.94136, 11847.36592, 11665.70476, 11585.8401, 11520.45543, 11360.63624,
             11302.52367, 11193.58347, 11060.62095, 10975.66454, 10831.91073, 10785.06413, 10656.11175, 10525.4109,
             10305.70285, 10238.06739, 10104.20713, 9989.837467, 9886.403771, 9753.549115]

    if config == "RTLS" and inclination == 51.6:
        x = [403.1141961, 450.2996276, 544.6617355, 626.8513825, 660.3365939, 730.35378, 784.1327494, 823.2027206,
             946.4988645, 998.2500632, 1019.562814, 1059.141552, 1138.299027, 1217.456503, 1275.304146, 1347.362235,
             1398.614882, 1430.584008, 1500.844524, 1599.63267, 1700.175855, 1800.388131, 1900.917705, 1998.841428]

        y = [10838.94817, 10691.71297, 10364.52362, 10091.86583, 9982.802716, 9764.676485, 9588.357782, 9475.659229,
             9110.297792, 8946.703119, 8892.171561, 8783.108446, 8564.982215, 8346.855984, 8194.167622, 8012.395763,
             7883.337743, 7801.540406, 7628.323093, 7627.039421, 7627.039421, 7618.004723, 7623.403984, 7629.498976]

    if config == "ASDS" and inclination == 51.6:
        x = [405.5994905, 467.9906988, 506.0387592, 539.5166747, 609.5236465, 664.3084758, 702.3579953, 792.9087309,
             825.6351699, 895.0365829, 923.0438837, 982.4004743, 1005.229482, 1035.672136, 1087.421389, 1139.174534,
             1244.200313, 1315.74088, 1352.272855, 1399.246289, 1428.383567, 1478.922055, 1499.927053, 1544.073018,
             1596.847586, 1624.753875, 1674.227297, 1701.373354, 1746.536851, 1797.645178, 1832.293702, 1886.898079,
             1914.299103, 1966.263731, 2000.771145, 1203.985641]

        y = [14433.75371, 14181.73266, 14045.40377, 13909.07487, 13652.77655, 13440.10348, 13309.22774, 12971.13208,
             12872.97528, 12630.85516, 12545.19799, 12338.56601, 12257.41051, 12164.06503, 11993.19948, 11836.87568,
             11509.68633, 11291.5601, 11182.49699, 11056.29538, 10964.37076, 10823.17665, 10757.15084, 10637.18141,
             10502.67023, 10419.05518, 10282.72628, 10204.56438, 10091.86583, 9965.664227, 9866.468726, 9738.501338,
             9664.338419, 9539.27938, 9454.937237, 11620.68966]

    if config == "RTLS" and inclination == 60:
        x = [401.4119958, 466.8933014, 504.2482525, 538.4658912, 601.8250984, 648.1090075, 721.2044184, 754.7064817,
             827.8018925, 883.6386647, 938.9678299, 995.3122091, 1019.677346, 1101.909683, 1141.503031, 1194.294161,
             1260.283073, 1424.747748, 1498.858373, 1600.379777, 1642.511159, 1694.287076, 1735.403244, 1831.340971,
             1902.139836, 1930.32434, 2001.722482]

        y = [8446.432031, 12024.26004, 8124.154558, 8034.342912, 7870.481111, 7746.838876, 7555.169519, 7459.33484,
             7267.665483, 7127.107954, 6980.161447, 6845.992896, 6788.492089, 6611.546658, 6500.988053, 6385.986438,
             6213.484017, 5830.145302, 5670.420837, 5439.186309, 5350.971908, 5245.553762, 5159.302551, 4967.633193,
             4833.464643, 4775.963836, 4641.795286]

    if config == "ASDS" and inclination == 60:
        x = [406.2850232, 503.9486138, 597.8559125, 698.6666667, 757.7521238, 901.9125174, 1002.164904, 1056.225051,
             1096.427527, 1127.797641, 1179.573557, 1240.4864, 1283.632996, 1315.104632, 1398.098379, 1427.79339,
             1479.569306, 1542.00497, 1592.867193, 1622.714486, 1680.581686, 1798.346515, 1837.432255, 1894.211726,
             1925.755877, 1983.623077]
        y = [10855.71585, 10522.85007, 10219.37359, 9878.202131, 9711.44979, 9280.193736, 8959.147562, 8801.020342,
             8689.852115, 8609.350985, 8475.182435, 8321.846949, 8206.845334, 8130.177591, 7921.737165, 7842.673555,
             7698.921537, 7555.169519, 7421.000969, 7363.500161, 7219.748143, 6986.550425, 6884.326768, 6763.848886,
             6692.65741, 6577.655796]

    if config == "RTLS" and inclination == 70:
        x = [399.4367401, 425.3856612, 460.7282991, 481.3535394, 501.8804108, 529.1732942, 590.214924, 632.9544017,
             698.5875098, 742.8430875, 793.709774, 861.8670389, 903.0582898, 941.2163398, 994.6272627, 1054.145764,
             1096.884024, 1131.971433, 1188.41326, 1223.509789, 1300.377006, 1399.333665, 1498.229129, 1575.900339,
             1617.993128, 1680.390067, 1716.233055, 1774.190281, 1820.974881, 1841.3154, 1898.770774, 1941.989524,
             1999.951766]

        y = [9269.349891, 9183.617486, 14177.41333, 8999.400232, 14151.87895, 8855.31827, 8680.225355, 8538.876762,
             8326.381924, 8198.71984, 8055.240923, 7870.420624, 7773.764576, 7651.554481, 7499.26258, 7323.255265,
             7184.118931, 7104.389122, 6981.824081, 6885.522978, 6697.852634, 6474.241933, 6274.519202, 6101.25263,
             6027.567695, 5881.474544, 5813.078874, 5705.474603, 5596.644577, 5550.439502, 5431.887008, 5342.516666,
             5225.797888]

    if config == "ASDS" and inclination == 70:
        x = [400.899151, 492.8361803, 598.4953749, 699.0547544, 741.397745, 797.5589351, 820.747046, 861.9453283,
             900.0903246, 942.818261, 995.2038927, 1022.167562, 1074.055356, 1096.564536, 1135.096986, 1183.937517,
             1251.073674, 1293.810643, 1327.375711, 1398.598975, 1446.399662, 1497.263672, 1533.367122, 1591.12662,
             1621.858214, 1674.241841, 1703.734857, 1754.594852, 1797.942919, 1891.902386, 1952.913904, 1998.678066]

        y = [12149.25373, 11759.672, 11399.63227, 10940.01829, 10825.11356, 10658.77529, 10606.24742, 10496.81435,
             10398.32458, 10277.9482, 10142.98566, 10059.08206, 9905.87576, 9839.301516, 9730.782845, 9577.576544,
             9402.483629, 9265.69229, 9183.617486, 8964.751342, 8855.31827, 8716.703046, 8636.452127, 8492.625804,
             8417.585983, 8286.266297, 8220.606454, 8089.286768, 7996.273573, 7760.987552, 7640.611173, 7540.292608]

    if config == "RTLS" and inclination == 90:
        x = [401.6348271, 453.7177977, 502.9691165, 532.7631242, 599.6476312, 651.331114, 706.5615023, 795.7408451,
             827.6629962, 900.3083227, 999.875032, 1057.198464, 1101.281434, 1149.924712, 1203.634998, 1248.73137,
             1301.934955, 1355.13854, 1398.981818, 1479.026889, 1516.269398, 1594.402663, 1631.797183, 1695.134784,
             1745.804866, 1801.541955, 1846.131626, 1902.882117, 1955.579001, 1998.221767]

        y = [9012.973347, 8861.09762, 8728.55608, 8642.692098, 8459.119608, 8315.083815, 8151.279674, 7853.70215,
             7769.07001, 7582.277363, 7160.264618, 7004.650684, 6885.925795, 6786.245162, 6678.862447, 6567.83964,
             6472.677234, 6349.434118, 6263.080048, 6117.378251, 6032.746111, 5885.952286, 5803.420313, 5679.657184,
             5574.094515, 5472.171938, 5366.609269, 5250.126324, 5148.203747, 5080.96016]

    if config == "ASDS" and inclination == 90:
        x = [403.0477166, 465.8786172, 502.3610755, 607.7548442, 698.4542894, 757.7382843, 818.5423816, 883.4000854,
             908.9884763, 977.6464362, 1006.021682, 1049.597951, 1100.521383, 1125.603073, 1198.56799, 1233.530346,
             1283.693726, 1312.575672, 1396.941357, 1428.103457, 1479.280239, 1507.655484, 1548.191549, 1624.196671,
             1657.638924, 1699.188391, 1745.804866, 1799.768502, 1844.611524, 1898.935723, 1940.377977, 1994.594964]

        y = [12108.05971, 11886.0141, 11741.32044, 11412.22816, 11101.57427, 10881.3487, 10652.0229, 10442.04552,
             10348.98524, 10146.05011, 10076.88836, 9953.12523, 9816.621779, 9734.719708, 9505.39391, 9407.111425,
             9265.147836, 9188.705903, 8951.189898, 8861.09762, 8738.482445, 8664.53265, 8533.489337, 8315.083815,
             8205.881054, 8067.557557, 7987.475532, 7879.420725, 7769.07001, 7638.026697, 7562.158741, 7426.901359]

    if config == "RTLS" and inclination == "SSO":
        x = [403.2985471, 438.2847577, 498.1176581, 550.846695, 608.648206, 660.3641193, 702.9569973, 739.4647614,
             794.2286706, 823.132173, 882.465983, 906.0434228, 1058.934521, 1100.382871, 1138.040832, 1197.375173,
             1235.408552, 1295.393719, 1332.776272, 1391.801271, 1439.271861, 1484.911208, 1516.864772, 1590.650454,
             1608.143115, 1682.692578, 1722.250931, 1743.553073, 1799.118086, 1843.969085, 1898.739609, 1947.427721,
             1997.631003]

        y = [8946.842299, 8835.611453, 8651.494957, 8467.378461, 8275.839958, 8099.145469, 7967.931448, 7853.656807,
             7692.043439, 7608.168146, 7460.114001, 7384.184556, 6969.897626, 6839.731289, 6748.957831, 6603.198938,
             6503.46917, 6350.915502, 6257.980508, 6091.048219, 5987.942981, 5865.19865, 5805.348382, 5615.880432,
             5558.337823, 5380.358544, 5292.391774, 5251.476997, 5135.630831, 5022.354246, 4889.381221, 4785.04854,
             4650.029776]

    if config == "ASDS" and inclination == "SSO":
        x = [407.8325413, 506.5385429, 557.6444064, 603.2709971, 627.6115097, 661.0728048, 703.0545918, 731.039908,
             764.5012032, 819.2542458, 884.6659186, 904.4382444, 942.4634742, 995.1926321, 1016.997347, 1053.503155,
             1115.56643, 1199.53465, 1300.51559, 1325.788633, 1402.355961, 1450.023093, 1500.734387, 1538.762803,
             1601.550298, 1676.182593, 1699.734165, 1788.734137, 1808.003768, 1849.076346, 1899.654279, 1935.78827,
             2000.152797]

        y = [12100.61065, 11717.64834, 11535.98673, 11358.00745, 11290.49807, 11167.75374, 11027.06425, 10922.26507,
             10799.52074, 10590.85538, 10394.46445, 10320.81785, 10185.79909, 10002.20644, 9940.310429, 9817.566099,
             9623.630056, 9362.364392, 9035.218217, 8958.355784, 8729.233033, 8598.305747, 8465.856564, 8344.63413,
             8149.00415, 7951.852272, 7891.241055, 7538.613025, 7485.423815, 7362.679485, 7215.386288, 7117.190823,
             6934.882959]
    if apogeealt >= 400:
        with warnings.catch_warnings():
            warnings.simplefilter('ignore', np.RankWarning)
            coeff = numpy.polyfit(x, y, 30)
            p = np.poly1d(coeff)
            masslim = p(apogeealt)
            if masslim > y[0]:
                masslim = y[0]
            return masslim

# print(AtlasMass(5000, 541, 0))
# print(AntaresMass(5000, 233, 0))
# print(Falcon9MassCirc(1800, "ASDS", "SSO"))

# You need to add inclination information for the models!!! Currently not using it unless Falcon 9

def ParkingOrbitAlgorithm(testmass, circalt, inclination):
    if circalt <= 2000 and circalt >= 400:
        launchvehiclelist = []
        Atlasconfigs = [551, 541, 531, 431, 521, 421, 511, 411, 501, 401]
        Antaresconfigs = [232, 233]
        for i in Atlasconfigs:
            if AtlasMass(circalt, i, inclination) >= testmass:
                launchvehiclelist.append("Atlas V " + str(i))
        for i in Antaresconfigs:
            if AntaresMass(circalt, i, inclination) >= testmass:
                launchvehiclelist.append("Antares " + str(i))
        if Falcon9MassCirc(circalt, "ASDS", inclination) >= testmass:
            launchvehiclelist.append("Falcon 9 ASDS")
        if Falcon9MassCirc(circalt, "RTLS", inclination) >= testmass:
            launchvehiclelist.append("Falcon 9 RTLS")
        return launchvehiclelist
    else:
        print("Not Achievable")


# ComponentsLoc = SCDesignerPath + "\\Component_Lists.xlsx"

# masses = []
# masses.append(Falcon9MassCirc(1000, "RTLS", 28.5))
# masses.append(Falcon9MassCirc(1000, "RTLS", 38))
# masses.append(Falcon9MassCirc(1000, "RTLS", 51.6))
#
#
# masses.append(Falcon9MassCirc(1000, "RTLS", 60))
# masses.append(Falcon9MassCirc(1000, "RTLS", 70))
# masses.append(Falcon9MassCirc(1000, "RTLS", 90))
#
# inclinations = [28.5, 38, 51.6, 60, 70, 90]
#
# # import matplotlib
# from matplotlib import pyplot as plt
#
# plt.plot(inclinations, masses)
# plt.show()

def CalculateAsmMass():

    Vol = []
    inertiafiles = []
    totalMass = 0
    densarray = []
    skipheader = 1
    with open(SCDesignerPath + str(App.ActiveDocument.Label) +
              "\\" + str(App.ActiveDocument.Label) + "Inertia.csv", 'r') as f:
                    InertiaRows = csv.reader(f, delimiter=',')
                    for row in InertiaRows:
                        if skipheader == 0:
                            Vol.append(float(row[17])) # m^3
                            inertiafiles.append(row[0])
                        skipheader = 0

    for filename in os.listdir(SCDesignerPath + "\\STRUCTURAL"):
        for i in range(0, len(inertiafiles)):
            if (inertiafiles[i] + ".csv") == filename:
                with open(SCDesignerPath + "\\STRUCTURAL\\" + filename, 'r') as k:
                    matdata = csv.reader(k, delimiter=',')
                    for row in matdata:
                        densarray.append(27679.90471* float(row[15]))  # Convert from MIL-HDBK 5J lbs/in^3 to kg/m^3
                    # print(matdata)
    try:
        for i in range(0, len(Vol)):
            mass = Vol[i] * densarray[i]
            totalMass = totalMass + mass
        print(str(totalMass) + " kg") # kg
        return totalMass
    except:
        pass



class Explore():
    """My new command"""

    def GetResources(self):
        return {'Pixmap'  : SCDesignerPath + '\\EXP.jpg',
                'MenuText': "Explore",
                'ToolTip' : "Explore Opportunities"}

    def Activated(self):

        layout = [[sg.Text('Opportunities', size=(30, 1))],
            [sg.Listbox(values=('Lunar ISRU Challenge', 'Mars Sample Return Challenge', 'Asteroid Mining Challenge', 'Robotic Servicing Challenge'), size=(40, 10)), sg.Button('OK', key='-OPPORTUNITY-',)],
            [sg.Text('Create an Opportunity'), sg.Button('OK',key='-CREATE-',)],
            [sg.Text('Explore the Solar System'), sg.Button('OK',key='-EXPLORE-',)],
            [sg.Cancel()]]


        window = sg.Window('Explore Opportunities', layout, default_element_size=(80, 80), grab_anywhere=False)

        event, values = window.read()
        print(values)

        window.close()
        if event == "Cancel":
            window.close()
        elif event == "-EXPLORE-":
            print("Explore")
            window.close()
        elif event == "-OPPORTUNITY-":
            print("Opportunity")
            window.close()
        elif event == "-CREATE-":
            print("Create")
            window.close()
            print(values)
        return

class Payload():
    """My new command"""

    def GetResources(self):
        return {'Pixmap'  : 'C:\\Users\\' + username + '\\AppData\\Roaming\\FreeCAD\\Mod\\SpacecraftDesigner\\Icons\\PLD.jpg',
                'Accel' : "Shift+Y", # a default shortcut (optional)
                'MenuText': "Payload",
                'ToolTip' : "Select payload and payload characteristics"}

    def Activated(self):
        layout1 = [
            [sg.Text('Name your mission', size=(25, 1)), sg.InputText('', size=(20, 1))],
            [sg.Submit(tooltip='Click to submit'), sg.Cancel()]]

        # https://web.archive.org/web/20180925131401/https://engineer.jpl.nasa.gov/practices/2404.pdf

        window1 = sg.Window('Payload', layout1, default_element_size=(40, 1), grab_anywhere=False)
        event1, values1 = window1.read()
        # vehicle.name = values1[0]
        global new_vehicle
        new_vehicle.name = values1[0]
        import FreeCADGui as Gui
        SCDesignerPath = "C:\\Users\\" + username + "\\AppData\\Roaming\\FreeCAD\\Mod\\SpacecraftDesigner"
        App.getDocument(FreeCAD.ActiveDocument.Name).saveAs(SCDesignerPath +
                                                            "/Vehicles/" + new_vehicle.name + "Assembly.FCStd")

        window1.close()
        if event1 == "Submit":
            layout = [
                [sg.Text('Target Body', size=(25, 1)), sg.InputCombo(('Sun', 'Mercury', 'Venus', 'Earth', 'Moon', 'Mars', 'Jupiter', 'Saturn', 'Uranus', 'Neptune', 'Pluto', 'Planetary Moon', 'Asteroid', 'Comet', 'Other Spacecraft'), size=(20, 1))],
                [sg.Text('Select Scientific Payload', size=(25, 1)), sg.InputCombo(('Optical Telescope', 'Radio Telescope', 'X-ray Telescope', 'Infrared Telescope', 'Mass Spectrometer', 'Magnetometer', 'Radar Altimeter', 'Gas Chromatograph', 'X-ray Powder Diffraction', 'Fizeau Interferometer'), size=(25, 1)), sg.Button('Add', key="-INSTRUMENT-")],
                [sg.Checkbox('Human Payload', default=True, key="-HUMAN-")],
                [sg.Submit(tooltip='Click to submit'), sg.Cancel()]]
            # https://web.archive.org/web/20180925131401/https://engineer.jpl.nasa.gov/practices/2404.pdf

            window = sg.Window('Payload', layout, default_element_size=(40, 1), grab_anywhere=False)
            event, values = window.read()
            new_vehicle.destination = values[0]

            window.close()
            if event == "Quit":
                window.close()

            elif event == "-INSTRUMENT-":
                    window.close()
                    inst_type = values[1]
                    if inst_type == "Optical Telescope":
                        # https://en.wikipedia.org/wiki/List_of_space_telescopes
                        layout = [sg.Text('Telescope Type', size=(25, 1)), sg.InputCombo(('Cassegrain telescope', 'Schmidt–Cassegrain telescope'), size=(25, 1)),sg.Button('Add', key="-TELESCOPE-")],
                        window = sg.Window('Optical Telescope', layout, default_element_size=(40, 1), grab_anywhere=False)


                        event, values = window.read()
                        window.close()

                        # All this in mini SMAD starting pg 250
                        def GroundResNadir(altitude, centerwavelength, opticalaperture):
                            groundres = 1.22 * altitude * centerwavelength / opticalaperture
                            return groundres

                        # On page 252
                        # Include slant range in this as well later
                        def GroundResToAperture(groundres, wavelength, altitude):
                            Aperture = 1.22 * (altitude * wavelength) / groundres
                            return Aperture

                        def Magnification(focallength, altitude):
                            magnification = focallength / altitude
                            return magnification

                        def FocalLengthForImageDia(ImageDia, opticalaperture, wavelength):
                            focallength = ImageDia * opticalaperture / (2.44 * wavelength)
                            return focallength

                        # will give same info as above but in another way
                        def NumericalAperture(focallength, opticalaperture):
                            numericalaperture = opticalaperture / (2 * focallength)
                            fnumber = 1 / (2 * numericalaperture)
                            return numericalaperture, fnumber

                        # MiniSMAD Pg 253
                        def DepthOfFocus(wavelength, Fnumber):
                            depthofFocus1 = 2 * wavelength * (Fnumber ** 2)
                            depthofFocus2 = -2 * wavelength * (Fnumber ** 2)
                            return depthofFocus1, depthofFocus2

                        # Refer to MiniSMAD pg 253
                        def CassegrainTelescope(focallength, I2, I1):
                            effectivefocallength = focallength * (I2 / I1)
                            return effectivefocallength

                        # https://www.lumenera.com/blog/understanding-dynamic-range-and-signal-to-noise-ratio-when-comparing-cameras#:~:text=Dynamic%20range%20quantifies%20the%20working,capacity%20and%20its%20noise%20floor.
                        def DynamicRange(FullWellCapacity, readnoise):
                            dynrange = 20 * math.log10(FullWellCapacity / readnoise)
                            return dynrange

                        # https://stackoverflow.com/questions/51413068/calculate-signal-to-noise-ratio-in-python-scipy-version-1-1
                        def signaltonoise(a, axis=0, ddof=0):
                            a = np.asanyarray(a)
                            m = a.mean(axis)
                            sd = a.std(axis=axis, ddof=ddof)
                            return np.where(sd == 0, 0, m / sd)

                        '''Design Process
                        - Determine Instrument requirements such as resolution, band pass, swath width, and sensitivity
                        - Choose a preliminary diffraction-limited aperture to meet resolution, and select a compatible preliminary modulation 
                          transfer function
                        - Determine dynamic range of the target radiance and apparent temperature levels and contrasts
                        - Select detector candidates - by wavelength, specific detectivity, band pass, time constant, operating temperature,
                          size and shape
                        - Determine optical link budget which yields required Noise Equipment Temperature Difference with sufficient signal 
                          to noise
                        - Determine alternative focal plane architectures or scanning schemes to produce desired results
                        - Select system F# and compatible telescope design
                        - Complete preliminary design and analytically check for expected Modulation Transfer Function. Iterate
                        - Estimate power, weight, temperature constraints and other requirements
                        - Iterate and document'''








                    else:


                        window.close()
                    return


class Schedule():
    """My new command"""

    def GetResources(self):
        return {'Pixmap'  : 'C:\\Users\\' + username + '\\AppData\\Roaming\\FreeCAD\\Mod\\SpacecraftDesigner\\Icons\\SCH.jpg',
                'Accel' : "Shift+H", # a default shortcut (optional)
                'MenuText': "Mission Scheduler",
                'ToolTip' : "Set Mission Schedule"}

    def Activated(self):

        if not exists(SCDesignerPath + "\\Schedule.png"):
            from PIL import Image
            img = Image.new("RGB", (1, 1), (12, 9, 60))
            img.save(SCDesignerPath + "\\Schedule.png", "PNG")

        ActivitiesList = ['Solar Panel Deploy', 'Collect Sample']
        import io
        import FreeSimpleGUI as sg
        from PIL import Image
        import time
        filename = SCDesignerPath + "\\Schedule.png"
        image = Image.open(filename)
        image.thumbnail((900, 900))
        bio = io.BytesIO()
        image.save(bio, format="PNG")
        layout = [
            [sg.Image(data=bio.getvalue(), key="-IMAGE-")],
            [sg.Text('Select Event'), sg.InputCombo(ActivitiesList)],
            [sg.Text('Start Date (mm-dd-yyyy)'), sg.InputText('', size=(20, 1))],
            [sg.Text('Stop Date (mm-dd-yyyy)'), sg.InputText('', size=(20, 1))],
            [sg.Button('Add Event'), sg.Button('Remove Event'), sg.Cancel(), sg.Button("Done", key="-DONE-")]]

        window = sg.Window("Set Mission Schedule", layout)
        if not exists(SCDesignerPath + "\\schedule.csv"):
            with open(SCDesignerPath + "\\schedule.csv", "w+") as f:
                f.write("task,start,end,milestone")
        while True:
            event, values = window.read()
            print(event)
            if event == "Cancel":
                window.close()
                break
            elif event == "-DONE-":
                window.close()
                break
            elif event == "Remove Event":

                MissionEvent = values[0]

                output = []
                with open(SCDesignerPath + "\\schedule.csv",
                          'r') as f:
                    for row in csv.reader(f):
                        if row[0] != MissionEvent:
                            output.append(row)
                f.close()
                with open(SCDesignerPath + "\\schedule.csv",
                          'w+') as f:
                    header = 1
                    for row in output:
                        if header == 0:
                            f.write("\n")
                        f.write(row[0] + "," + row[1] + "," + row[2])
                        header = 0
                f.close()


            elif event == "Add Event":

                with open(SCDesignerPath + "\\schedule.csv",
                          "a") as f:
                    f.write("\n" + values[0] + ',' + values[1] + ',' + values[2])
                f.close()

            if event == "Add Event" or event == "Remove Event":
                import matplotlib.dates as mdates

                start = []
                stop = []
                task = []
                duration = []
                pasttime = []
                header = 1
                with open(SCDesignerPath + "\\schedule.csv", "r") as f:
                    for row in csv.reader(f):
                        if header == 1:
                            header = 0
                            continue
                        start.append(datetime.strptime(row[1], '%m-%d-%Y'))  # %H:%M:%S'))
                        stop.append(datetime.strptime(row[2], '%m-%d-%Y'))
                        task.append(row[0])

                for i in range(0, len(start)):
                    duration.append(stop[i] - start[i] + timedelta(days=1))
                    pasttime.append(start[i] - start[0])

                nrow = len(start)
                plt.figure(num=1, figsize=[12, 8], dpi=100)
                bar_width = 0.5
                for i in range(nrow):
                    i_rev = nrow - 1 - i
                    plt.broken_barh([(start[i_rev], duration[i_rev])], (i - bar_width / 2, bar_width), color="b")
                    plt.broken_barh([(start[0], pasttime[i_rev])], (i - bar_width / 2, bar_width), color="w")

                y_pos = np.arange(nrow)
                plt.yticks(y_pos, labels=reversed(task))

                plt.savefig(SCDesignerPath + "\\Schedule.png")

                image = Image.open(SCDesignerPath + "\\Schedule.png")
                image.thumbnail((1200, 1200))
                bio = io.BytesIO()
                image.save(bio, format="PNG")
                window["-IMAGE-"].update(data=bio.getvalue())
            else:
                window.close()
                break

class LaunchVehicle():
    """My new command"""

    def GetResources(self):
        return {'Pixmap'  : 'C:\\Users\\' + username + '\\AppData\\Roaming\\FreeCAD\\Mod\\SpacecraftDesigner\\Icons\\Launch.jpg',
                'Accel' : "Shift+W", # a default shortcut (optional)
                'MenuText': "Launch Vehicle",
                'ToolTip' : "Select a Launch Vehicle"}

    def Activated(self):
        layout = [
            [sg.Text('Select Launch Vehicle', size=(25, 1)), sg.InputCombo(('Alpha','Antares 230', 'Antares 231', 'Antares 232','Antares 233', 'Electron', 'Electron Expanded','Falcon 9', 'Falcon Heavy', 'LauncherOne', 'Starship'), size=(20, 1)), sg.Button("OK", key="-LV-")],
            [sg.Text('Select Payload Adapter', size=(25, 1)), sg.InputCombo(('609.6 mm diameter', '937 mm diameter','1194 mm diameter','1575 mm diameter','1666 mm diameter')),sg.Button("OK", key="-ADAPTER-")],
            [sg.Text('Payload Fairing Fit Check', size=(25, 1)), sg.Button("OK", key="-FIT-")],
            [sg.Text('Run In-Flight Loads Test', size=(25, 1)), sg.Button("OK")],
            [sg.Text('Run Acoustics Test', size=(25, 1)), sg.Button("OK")],
            [sg.Text('Run Vibration Test', size=(25, 1)), sg.Button("OK")],
            [sg.Cancel()]
        ]
        # https://web.archive.org/web/20180925131401/https://engineer.jpl.nasa.gov/practices/2404.pdf

        window = sg.Window('Launch Vehicle', layout, default_element_size=(40, 1), grab_anywhere=False)
        event, values = window.read()

        window.close()
        if event == "Quit":
            window.close()
        elif event == "-FIT-":
            window.close()

            import FreeCAD as App
            if App.ActiveDocument.Name == "Unnamed":

                layout = [[sg.Text('Please name your project first', size=(25, 1)), sg.Button("OK")],
                          [sg.Cancel()]]
                # https://web.archive.org/web/20180925131401/https://engineer.jpl.nasa.gov/practices/2404.pdf

                window = sg.Window('Launch Vehicle', layout, default_element_size=(40, 1), grab_anywhere=False)
                window.close()
                pass







            launchvehicle = values[0].replace(" ", "")
            launchvehicle = launchvehicle
            with open(
                    SCDesignerPath + "\\AssemblyInclude.txt",
                    'w+') as f:
                f.write("LaunchVehicles\\" + launchvehicle + "Fairing.fcstd")

            import FreeCADGui as Gui

            Gui.activateWorkbench("A2plusWorkbench")  # A2p_import_part.py was modified
            Gui.runCommand('a2p_ImportPart', 0)
            os.remove(SCDesignerPath + "\\AssemblyInclude.txt")
            fairingname = "b_" + launchvehicle + "_001_"
            Gui.Selection.addSelection('Assembly2', fairingname, 'Edge29', 0.00, 0.00, 0.00)
            Gui.activateWorkbench("SpacecraftDesigner")


class GNC():
    """My new command"""

    def GetResources(self):
        return {'Pixmap'  : 'C:\\Users\\' + username + '\\AppData\\Roaming\\FreeCAD\\Mod\\SpacecraftDesigner\\Icons\\GNC.jpg',
                'Accel' : "Shift+G", # a default shortcut (optional)
                'MenuText': "Guidance, Navigation and Control",
                'ToolTip' : "Define Spacecraft Guidance, Navigation and Control Scheme"}

    def Activated(self):
        import os
        import FreeSimpleGUI as sg

        layout = [
                  # [sg.Text('Expected Loiter Time at Mission Destination (optional, for return planning)'), sg.InputText('', size=(20, 1)), sg.Radio('Days', "RADIO1"), sg.Radio('Months', "RADIO1"), sg.Radio('Years', "RADIO1")],
                  # [sg.Text('Select Launch Vehicle', size=(25, 1)), sg.InputCombo('placeholder', 'placeholder2'), sg.Button('OK', key="-LAUNCH-")],
                  [sg.Text('Open Trajectory Designer'), sg.Button('OK', key="-TRAJ-")],
                  [sg.Text('Open Control Systems Designer'), sg.Button('OK', key="-CONTROLLER-")],
                  # [sg.Text('Select Landing Site'), sg.Button('OK', key="-LDG-")],
                  [sg.Text('Set Rocket-Powered Landing Sequence'), sg.Button('OK', key="-SEQUENCE-")],
                  [sg.Text('Add Vehicle Surface Path'), sg.Button('OK', key="-SURF-")],
                  [sg.Text('Add Robotic Arm'), sg.Button('OK', key="-ROBO-")],
                  [sg.Text('Add Spring/Damper/Actuator'), sg.InputCombo(('Linear Spring', 'Linear Damper', 'Linear Actuator', 'Rotary Spring', 'Rotary Damper', 'Rotary Actuator')), sg.Button('OK', key="-ACTUATOR-")],
                  [sg.Text('Add Sensor'), sg.InputCombo(('Angular Position Sensor', 'Angular Velocity Sensor', 'Angular Acceleration Sensor', 'Linear Position Sensor', 'Linear Velocity Sensor', 'Linear Acceleration Sensor')), sg.Button('OK')],
                  [sg.Text('Calculate Moment of Inertia'), sg.Button('OK', key='-INERTIA-',)],
                  [sg.Text('Implement Attitude Stabilization Method'), sg.InputCombo(('Spin Stabilization', '3-Axis Stabilization (Control Moment Gyros)',
                                                         '3-Axis Stabilization (Reaction Control Thrusters)', 'Magnetorquer', 'Solar Pressure Stabilization', 'Aerodynamic Stabilization', 'Yo-Yo Despin')),
                   sg.Button('OK', key='-STABILIZATION-',)],[sg.Cancel()]]


        window = sg.Window('Guidance, Navigation and Control', layout, default_element_size=(40, 1), grab_anywhere=False)

        event, values = window.read()

        if event == "Exit" or event == sg.WIN_CLOSED:
            window.close()


        if event == "-LAUNCH-":
            import matplotlib.pyplot as plt
            from scipy.optimize import curve_fit
            import numpy as np
            import numpy
            import warnings
            def AtlasMass(apogeealt, config, inclination):

                x = [5000, 7500, 10000, 12500, 15000, 17500, 20000, 22500, 25000, 27500, 30000, 35000, 35786, 40000,
                     45000, 50000, 55000, 60000, 65000, 70000, 75000, 80000, 85000, 90000, 95000, 100000, 105000,
                     110000, 115000, 120000, 125000, 130000, 135000, 140000, 145000, 150000]

                if config == 401:
                    y = [7827, 7135, 6625, 6238, 5933, 5688, 5487, 5318, 5176, 5054, 4948, 4774, 4750, 4636, 4525, 4433,
                         4356, 4290, 4234, 4184, 4141, 4103, 4069, 4038, 4011, 3986, 3963, 3942, 3923, 3905, 3889, 3874,
                         3860, 3847, 3835, 3823]
                if config == 411:
                    y = [9729, 8869, 8242, 7766, 7394, 7095, 6847, 6642, 6468, 6321, 6191, 5978, 5950, 5810, 5674, 5562,
                         5467, 5387, 5318, 5258, 5205, 5158, 5117, 5079, 5046, 5015, 4987, 4962, 4939, 4917, 4897, 4879,
                         4862, 4846, 4831, 4817]
                if config == 421:
                    y = [11263, 10260, 9529, 8977, 8545, 8199, 7915, 7680, 7481, 7311, 7164, 6922, 6890, 6732, 6579,
                         6452, 6348, 6258, 6181, 6113, 6054, 6001, 5955, 5913, 5875, 5841, 5810, 5781, 5755, 5731, 5709,
                         5688, 5669, 5651, 5634, 5619]
                if config == 431:
                    y = [12573, 11453, 10637, 10021, 9541, 9156, 8841, 8579, 8358, 8169, 8005, 7736, 7700, 7525, 7355,
                         7215, 7097, 6997, 6912, 6837, 6771, 6713, 6662, 6615, 6573, 6536, 6501, 6470, 6441, 6414, 6389,
                         6367, 6348, 6329, 6310, 6293]
                if config == 501:
                    y = [6392, 5783, 5335, 5002, 4773, 4570, 4401, 4262, 4115, 4021, 3940, 3796, 3775, 3682, 3583, 3506,
                         3442, 3382, 3337, 3295, 3253, 3223, 3195, 3168, 3145, 3123, 3104, 3085, 3069, 3054, 3040, 3027,
                         3014, 3003, 2992, 2982]
                if config == 511:
                    y = [8807, 7988, 7394, 6944, 6594, 6313, 6083, 5893, 5731, 5593, 5473, 5277, 5250, 5123, 4998, 4895,
                         4809, 4735, 4672, 4617, 4569, 4526, 4488, 4454, 4423, 4395, 4370, 4347, 4326, 4306, 4288, 4271,
                         4255, 4241, 4227, 4215]
                if config == 521:
                    y = [10790, 9785, 9058, 8512, 8088, 7749, 7475, 7245, 7051, 6885, 6742, 6507, 6475, 6322, 6173,
                         6050, 5947, 5860, 5784, 5719, 5662, 5611, 5566, 5525, 5489, 5456, 5425, 5398, 5373, 5349, 5328,
                         5308, 5289, 5272, 5256, 5241]
                if config == 531:
                    y = [12455, 11288, 10446, 9806, 9323, 8933, 8614, 8350, 8129, 7940, 7776, 7508, 7475, 7301, 7131,
                         6991, 6875, 6775, 6690, 6616, 6551, 6493, 6442, 6396, 6354, 6317, 6283, 6252, 6223, 6197, 6172,
                         6150, 6129, 6109, 6091, 6074]
                if config == 541:
                    y = [13885, 12561, 11610, 10901, 10345, 9913, 9562, 9268, 9021, 8810, 8627, 8330, 8290, 8096, 7909,
                         7754, 7624, 7514, 7424, 7342, 7270, 7206, 7150, 7099, 7053, 7012, 6974, 6940, 6908, 6879, 6852,
                         6827, 6804, 6783, 6763, 6744]
                if config == 551:
                    y = [14988, 13534, 12497, 11726, 11131, 10659, 10275, 9955, 9690, 9461, 9265, 8944, 8900, 8691,
                         8488, 8322, 8181, 8064, 7962, 7873, 7796, 7727, 7666, 7611, 7562, 7517, 7481, 7444, 7410, 7379,
                         7350, 7323, 7298, 7275, 7253, 7233]
                with warnings.catch_warnings():
                    warnings.simplefilter('ignore', np.RankWarning)
                    coeff = numpy.polyfit(x, y, 21)
                    p = np.poly1d(coeff)
                    masslim = p(apogeealt)
                return masslim

            def AntaresMass(apogeealt, config, inclination):
                if config == 232:
                    x = [1375.026864, 1681.203525, 1885.321298, 2242.527402, 2586.976144, 3001.590372, 3246.106455,
                         3639.458414,
                         4054.072641, 4436.793467, 4819.514292, 5266.021921, 5776.316355, 6286.610789, 6796.905222,
                         7370.98646,
                         8008.854502, 8710.509349, 9475.950999, 10305.17945, 11261.98152, 12410.14399, 13749.66688,
                         15152.97657,
                         16556.28627, 17959.59596, 19362.90565, 20766.21534, 22169.52504, 23572.83473, 24976.14442,
                         26379.45412,
                         27782.76381, 29186.0735, 30589.38319, 31992.69289, 33396.00258, 34799.31227, 36202.62196,
                         37605.93166,
                         39009.24135, 40412.55104, 41815.86074, 43219.17043, 44622.48012, 46025.78981, 47429.09951,
                         48832.4092,
                         50235.71889, 51639.02858, 53042.33828, 54445.64797, 55848.95766, 57252.26735, 58655.57705,
                         60058.88674,
                         61462.19643, 62865.50613, 64268.81582, 65672.12551, 67075.4352, 68478.7449, 69882.05459,
                         71285.36428,
                         72688.67397, 74091.98367, 75495.29336, 76898.60305, 78301.91274, 79705.22244, 81108.53213,
                         82511.84182,
                         83915.15152, 85318.46121, 86721.7709, 88125.08059, 89528.39029, 90931.69998, 92335.00967,
                         93738.31936,
                         95141.62906, 96544.93875, 97948.24844, 99287.77133]

                    y = [6884.159239, 6705.16221, 6557.908497, 6389.051693, 6215.124777, 6021.688948, 5894.385027,
                         5735.668449,
                         5572.543078, 5422.644088, 5274.949495, 5115.681818, 4945.392157, 4788.328877, 4639.532086,
                         4483.130125,
                         4327.058824, 4172.75104, 4023.954248, 3882.085561, 3742.618093, 3596.962567, 3449.909253,
                         3321.853832,
                         3210.030789, 3112.035327, 3026.063847, 2949.711554, 2880.573651, 2819.852536, 2764.542214,
                         2712.839086,
                         2667.14795, 2626.266407, 2584.783666, 2549.914114, 2513.842165, 2483.181008, 2448.912656,
                         2421.858694,
                         2389.995139, 2367.75077, 2343.702803, 2321.458435, 2304.624858, 2290.196078, 2270.356506,
                         2256.528926,
                         2246.909739, 2237.290553, 2228.272565, 2218.653379, 2204.825798, 2194.004213, 2181.98023,
                         2172.962243,
                         2162.140658, 2152.521471, 2140.497488, 2129.675903, 2122.461514, 2115.247124, 2108.032734,
                         2103.22314,
                         2096.60995, 2091.199157, 2080.377573, 2073.764382, 2065.347594, 2058.734403, 2052.722411,
                         2047.311619,
                         2041.900826, 2038.894831, 2032.28164, 2027.472047, 2023.263653, 2013.043267, 2007.632474,
                         1999.215686,
                         1993.804894, 1988.995301, 1985.989305, 1979.376114]

                if config == 233:
                    x = [609.5852138, 915.7618741, 1119.879648, 1438.813669, 1706.718246, 2140.468515, 2446.645175,
                         2905.910165,
                         3288.630991, 3798.925424, 4245.433054, 4691.940683, 5138.448313, 5648.742747, 6159.03718,
                         6733.118418,
                         7370.98646, 8008.854502, 8646.722545, 9348.377391, 10177.60585, 11134.40791, 12282.57038,
                         13622.09327,
                         15025.40297, 16428.71266, 17832.02235, 19235.33204, 20638.64174, 22041.95143, 23445.26112,
                         24848.57081,
                         26251.88051, 27655.1902, 29058.49989, 30461.80959, 31865.11928, 33268.42897, 34671.73866,
                         36075.04836,
                         37478.35805, 38881.66774, 40284.97743, 41688.28713, 43091.59682, 44494.90651, 45898.2162,
                         47301.5259,
                         48704.83559, 50108.14528, 51511.45498, 52914.76467, 54318.07436, 55721.38405, 57124.69375,
                         58528.00344,
                         59931.31313, 61334.62282, 62737.93252, 64141.24221, 65544.5519, 66947.86159, 67777.09005]

                    y = [6773.939394, 6607.286988, 6456.506239, 6311.016043, 6141.71836, 5960.516934, 5789.896613,
                         5590.178253,
                         5426.171123, 5230.861557, 5054.509804, 4889.180036, 4735.423351, 4571.746881, 4413.030303,
                         4247.700535,
                         4081.048128, 3927.622103, 3788.745098, 3647.002377, 3505.13369, 3365.666221, 3221.994652,
                         3078.368174,
                         2951.515152, 2839.090909, 2738.089451, 2649.713175, 2566.747691, 2494.002593, 2426.668287,
                         2364.744774,
                         2308.232053, 2255.927726, 2209.635391, 2165.747853, 2124.86631, 2091.800357, 2055.127208,
                         2028.674445,
                         1998.013288, 1976.971317, 1956.530546, 1934.286177, 1915.047804, 1900.017825, 1878.374656,
                         1857.332685,
                         1842.302706, 1828.475126, 1811.641549, 1794.807973, 1784.587587, 1773.164803, 1760.539621,
                         1744.307244,
                         1728.676065, 1719.056879, 1710.038892, 1701.622103, 1693.806514, 1682.38373, 1678.475936]

                with warnings.catch_warnings():
                    warnings.simplefilter('ignore', np.RankWarning)
                    coeff = numpy.polyfit(x, y, 30)
                    p = np.poly1d(coeff)
                    masslim = p(apogeealt)
                return masslim

            def Falcon9MassCirc(apogeealt, config, inclination):

                if config == "RTLS" and inclination == 28.5:
                    x = [399.9794132, 481.7548257, 506.1310516, 556.9202175, 654.4280656, 721.4628421, 754.9802304,
                         797.6395401,
                         822.0150069, 855.5323951, 948.4618062, 998.7348981, 1041.388227, 1086.073094, 1113.495868,
                         1149.548193,
                         1196.771841, 1231.807543, 1298.915736, 1349.100459, 1431.356819, 1497.650438, 1600.867641,
                         1697.77789,
                         1796.718181, 1896.797531, 1996.607575]

                    y = [11680.50006, 11365.56956, 11286.36111, 11101.76376, 10774.17717, 10555.78611, 10446.59058,
                         10304.6364,
                         10228.19952, 10119.004, 9835.09562, 9682.221879, 9562.106797, 9434.712013, 9347.355589,
                         9245.439762,
                         9111.285255, 9016.129151, 8844.271282, 8699.462116, 8481.071058, 8317.277764, 8320.917615,
                         8322.737541,
                         8322.737541, 8310.866329, 8313.554521]

                if config == "ASDS" and inclination == 28.5:
                    x = [399.4351444, 430.9309628, 483.7609219, 501.0279989, 616.8361376, 656.4556164, 699.1250938,
                         744.8305145,
                         796.6392219, 848.4419483, 894.1521538, 924.6246273, 999.5000358, 1067.842083, 1099.835319,
                         1151.635553,
                         1193.987441, 1220.192488, 1253.709876, 1295.354912, 1323.78897, 1379.647296, 1407.577954,
                         1433.474084,
                         1488.32038, 1508.629032, 1544.681357, 1592.919921, 1620.849084, 1672.134954, 1708.287959,
                         1738.14499,
                         1791.243666, 1818.879192, 1862.03891, 1898.8568, 1947.339586, 1998.620971]

                    y = [15520.54284, 15382.2285, 15156.55774, 15098.32013, 14645.15868, 14486.82516, 14307.74449,
                         14159.23857,
                         13957.22685, 13777.05422, 13611.07702, 13504.0654, 13240.43619, 13012.68552, 12910.76969,
                         12739.6967,
                         12608.66206, 12521.30564, 12412.11011, 12268.33599, 12193.71905, 12026.2859, 11937.10956,
                         11866.13246,
                         11688.68973, 11640.4617, 11538.54587, 11403.87139, 11320.15482, 11174.56078, 11075.55683,
                         10992.56823,
                         10844.3743, 10774.17717, 10657.70194, 10539.40678, 10439.31088, 10310.09617]

                if config == "RTLS" and inclination == 38:
                    x = [404.6643957, 467.3105337, 505.3767633, 596.5181932, 643.9378393, 700.2758592, 741.3873873,
                         802.2933548,
                         844.927532, 918.0146929, 954.5582734, 1007.546465, 1083.475905, 1103.777894, 1146.412071,
                         1195.745905,
                         1219.499232, 1264.163608, 1301.722288, 1345.879114, 1396.735597, 1423.534223, 1499.734812,
                         1598.638879,
                         1699.133726, 1799.846093, 1900.123418, 1996.050317]

                    y = [11379.78846, 11155.35308, 11040.79752, 10714.96628, 10555.30015, 10362.95777, 10227.99855,
                         10036.29333,
                         9900.696949, 9682.495883, 9573.39535, 9426.071401, 9209.325008, 9144.592025, 9016.98263,
                         8883.007175,
                         8809.691617, 8693.317715, 8585.315049, 8471.479964, 8328.275957, 8264.188951, 8084.2113,
                         8106.902349,
                         8102.356493, 8106.772467, 8111.448204, 8092.686441]

                if config == "ASDS" and inclination == 38:
                    x = [397.2686711, 496.2408682, 604.3489605, 696.2154614, 753.5685808, 815.9971974, 875.3805157,
                         903.2957508,
                         953.0356242, 1000.237749, 1048.962523, 1097.687297, 1115.959087, 1149.457369, 1198.182143,
                         1219.499232,
                         1254.520163, 1324.562026, 1377.854747, 1402.217134, 1435.715416, 1491.292112, 1508.802577,
                         1548.391456,
                         1595.593581, 1626.046565, 1675.278889, 1705.224323, 1761.562342, 1796.583274, 1833.126854,
                         1884.389377,
                         1907.736664, 1954.938789, 1995.441258]

                    y = [15137.52255, 14747.48814, 14313.81352, 13968.3285, 13773.76588, 13533.74471, 13337.36375,
                         13240.99161,
                         13064.61241, 12886.9344, 12737.31081, 12577.2967, 12519.10975, 12410.00921, 12246.35841,
                         12191.80815,
                         12082.70761, 11864.50655, 11700.85575, 11641.94146, 11537.20495, 11373.55415, 11326.27725,
                         11209.90335,
                         11077.16437, 10991.70228, 10853.50827, 10778.95624, 10620.76047, 10529.38877, 10435.28956,
                         10311.64229,
                         10244.36363, 10118.89802, 10009.79748]

                if config == "RTLS" and inclination == 45:
                    x = [402.2547626, 444.0819221, 500.9050035, 538.4488251, 602.5044322, 702.8298818, 739.3590055,
                         791.8696209,
                         842.8581894, 896.6371771, 952.4455606, 1000.716188, 1027.025855, 1073.448283, 1125.958898,
                         1165.532116,
                         1202.737705, 1244.67855, 1276.134185, 1346.655687, 1398.405279, 1499.767034, 1599.31546,
                         1699.77055,
                         1800.22564, 1899.158684, 1998.091727]

                    y = [11112.98892, 10966.49631, 10797.6009, 10639.47025, 10434.57542, 10136.63531, 9985.520864,
                         9832.980184,
                         9658.571852, 9495.114467, 9331.674203, 9182.219869, 9113.755278, 8970.724716, 8830.477368,
                         8721.537166,
                         8606.890747, 8503.656763, 8412.860421, 8242.259346, 8106.103355, 7845.584364, 7843.112269,
                         7842.745597,
                         7850.216941, 7850.411779, 7852.547304]

                if config == "ASDS" and inclination == 45:
                    x = [400.7035877, 441.0378285, 500.3976545, 555.1913401, 606.0277039, 663.2566644, 698.9160471,
                         804.8070189,
                         855.034564, 897.651875, 931.1369051, 979.8424034, 1002.673106, 1046.812464, 1080.297494,
                         1103.635545,
                         1132.047086, 1184.811375, 1203.075937, 1235.546269, 1290.339955, 1322.302938, 1343.611594,
                         1396.883233,
                         1416.669841, 1456.243059, 1497.947142, 1530.823353, 1588.661132, 1605.403647, 1647.513609,
                         1698.248503,
                         1776.633915, 1808.705616, 1855.019326, 1898.651335, 1943.298042, 1997.787318]

                    y = [14779.795, 14638.079, 14401.81933, 14191.01841, 13979.45562, 13776.68868, 13652.10488,
                         13264.29478,
                         13089.88003, 12935.0704, 12828.26432, 12664.76413, 12599.39231, 12446.781, 12326.86203,
                         12257.85202,
                         12174.31493, 11999.92158, 11919.94136, 11847.36592, 11665.70476, 11585.8401, 11520.45543,
                         11360.63624,
                         11302.52367, 11193.58347, 11060.62095, 10975.66454, 10831.91073, 10785.06413, 10656.11175,
                         10525.4109,
                         10305.70285, 10238.06739, 10104.20713, 9989.837467, 9886.403771, 9753.549115]

                if config == "RTLS" and inclination == 51.6:
                    x = [403.1141961, 450.2996276, 544.6617355, 626.8513825, 660.3365939, 730.35378, 784.1327494,
                         823.2027206,
                         946.4988645, 998.2500632, 1019.562814, 1059.141552, 1138.299027, 1217.456503, 1275.304146,
                         1347.362235,
                         1398.614882, 1430.584008, 1500.844524, 1599.63267, 1700.175855, 1800.388131, 1900.917705,
                         1998.841428]

                    y = [10838.94817, 10691.71297, 10364.52362, 10091.86583, 9982.802716, 9764.676485, 9588.357782,
                         9475.659229,
                         9110.297792, 8946.703119, 8892.171561, 8783.108446, 8564.982215, 8346.855984, 8194.167622,
                         8012.395763,
                         7883.337743, 7801.540406, 7628.323093, 7627.039421, 7627.039421, 7618.004723, 7623.403984,
                         7629.498976]

                if config == "ASDS" and inclination == 51.6:
                    x = [405.5994905, 467.9906988, 506.0387592, 539.5166747, 609.5236465, 664.3084758, 702.3579953,
                         792.9087309,
                         825.6351699, 895.0365829, 923.0438837, 982.4004743, 1005.229482, 1035.672136, 1087.421389,
                         1139.174534,
                         1244.200313, 1315.74088, 1352.272855, 1399.246289, 1428.383567, 1478.922055, 1499.927053,
                         1544.073018,
                         1596.847586, 1624.753875, 1674.227297, 1701.373354, 1746.536851, 1797.645178, 1832.293702,
                         1886.898079,
                         1914.299103, 1966.263731, 2000.771145, 1203.985641]

                    y = [14433.75371, 14181.73266, 14045.40377, 13909.07487, 13652.77655, 13440.10348, 13309.22774,
                         12971.13208,
                         12872.97528, 12630.85516, 12545.19799, 12338.56601, 12257.41051, 12164.06503, 11993.19948,
                         11836.87568,
                         11509.68633, 11291.5601, 11182.49699, 11056.29538, 10964.37076, 10823.17665, 10757.15084,
                         10637.18141,
                         10502.67023, 10419.05518, 10282.72628, 10204.56438, 10091.86583, 9965.664227, 9866.468726,
                         9738.501338,
                         9664.338419, 9539.27938, 9454.937237, 11620.68966]

                if config == "RTLS" and inclination == 60:
                    x = [401.4119958, 466.8933014, 504.2482525, 538.4658912, 601.8250984, 648.1090075, 721.2044184,
                         754.7064817,
                         827.8018925, 883.6386647, 938.9678299, 995.3122091, 1019.677346, 1101.909683, 1141.503031,
                         1194.294161,
                         1260.283073, 1424.747748, 1498.858373, 1600.379777, 1642.511159, 1694.287076, 1735.403244,
                         1831.340971,
                         1902.139836, 1930.32434, 2001.722482]

                    y = [8446.432031, 12024.26004, 8124.154558, 8034.342912, 7870.481111, 7746.838876, 7555.169519,
                         7459.33484,
                         7267.665483, 7127.107954, 6980.161447, 6845.992896, 6788.492089, 6611.546658, 6500.988053,
                         6385.986438,
                         6213.484017, 5830.145302, 5670.420837, 5439.186309, 5350.971908, 5245.553762, 5159.302551,
                         4967.633193,
                         4833.464643, 4775.963836, 4641.795286]

                if config == "ASDS" and inclination == 60:
                    x = [406.2850232, 503.9486138, 597.8559125, 698.6666667, 757.7521238, 901.9125174, 1002.164904,
                         1056.225051,
                         1096.427527, 1127.797641, 1179.573557, 1240.4864, 1283.632996, 1315.104632, 1398.098379,
                         1427.79339,
                         1479.569306, 1542.00497, 1592.867193, 1622.714486, 1680.581686, 1798.346515, 1837.432255,
                         1894.211726,
                         1925.755877, 1983.623077]
                    y = [10855.71585, 10522.85007, 10219.37359, 9878.202131, 9711.44979, 9280.193736, 8959.147562,
                         8801.020342,
                         8689.852115, 8609.350985, 8475.182435, 8321.846949, 8206.845334, 8130.177591, 7921.737165,
                         7842.673555,
                         7698.921537, 7555.169519, 7421.000969, 7363.500161, 7219.748143, 6986.550425, 6884.326768,
                         6763.848886,
                         6692.65741, 6577.655796]

                if config == "RTLS" and inclination == 70:
                    x = [399.4367401, 425.3856612, 460.7282991, 481.3535394, 501.8804108, 529.1732942, 590.214924,
                         632.9544017,
                         698.5875098, 742.8430875, 793.709774, 861.8670389, 903.0582898, 941.2163398, 994.6272627,
                         1054.145764,
                         1096.884024, 1131.971433, 1188.41326, 1223.509789, 1300.377006, 1399.333665, 1498.229129,
                         1575.900339,
                         1617.993128, 1680.390067, 1716.233055, 1774.190281, 1820.974881, 1841.3154, 1898.770774,
                         1941.989524,
                         1999.951766]

                    y = [9269.349891, 9183.617486, 14177.41333, 8999.400232, 14151.87895, 8855.31827, 8680.225355,
                         8538.876762,
                         8326.381924, 8198.71984, 8055.240923, 7870.420624, 7773.764576, 7651.554481, 7499.26258,
                         7323.255265,
                         7184.118931, 7104.389122, 6981.824081, 6885.522978, 6697.852634, 6474.241933, 6274.519202,
                         6101.25263,
                         6027.567695, 5881.474544, 5813.078874, 5705.474603, 5596.644577, 5550.439502, 5431.887008,
                         5342.516666,
                         5225.797888]

                if config == "ASDS" and inclination == 70:
                    x = [400.899151, 492.8361803, 598.4953749, 699.0547544, 741.397745, 797.5589351, 820.747046,
                         861.9453283,
                         900.0903246, 942.818261, 995.2038927, 1022.167562, 1074.055356, 1096.564536, 1135.096986,
                         1183.937517,
                         1251.073674, 1293.810643, 1327.375711, 1398.598975, 1446.399662, 1497.263672, 1533.367122,
                         1591.12662,
                         1621.858214, 1674.241841, 1703.734857, 1754.594852, 1797.942919, 1891.902386, 1952.913904,
                         1998.678066]

                    y = [12149.25373, 11759.672, 11399.63227, 10940.01829, 10825.11356, 10658.77529, 10606.24742,
                         10496.81435,
                         10398.32458, 10277.9482, 10142.98566, 10059.08206, 9905.87576, 9839.301516, 9730.782845,
                         9577.576544,
                         9402.483629, 9265.69229, 9183.617486, 8964.751342, 8855.31827, 8716.703046, 8636.452127,
                         8492.625804,
                         8417.585983, 8286.266297, 8220.606454, 8089.286768, 7996.273573, 7760.987552, 7640.611173,
                         7540.292608]

                if config == "RTLS" and inclination == 90:
                    x = [401.6348271, 453.7177977, 502.9691165, 532.7631242, 599.6476312, 651.331114, 706.5615023,
                         795.7408451,
                         827.6629962, 900.3083227, 999.875032, 1057.198464, 1101.281434, 1149.924712, 1203.634998,
                         1248.73137,
                         1301.934955, 1355.13854, 1398.981818, 1479.026889, 1516.269398, 1594.402663, 1631.797183,
                         1695.134784,
                         1745.804866, 1801.541955, 1846.131626, 1902.882117, 1955.579001, 1998.221767]

                    y = [9012.973347, 8861.09762, 8728.55608, 8642.692098, 8459.119608, 8315.083815, 8151.279674,
                         7853.70215,
                         7769.07001, 7582.277363, 7160.264618, 7004.650684, 6885.925795, 6786.245162, 6678.862447,
                         6567.83964,
                         6472.677234, 6349.434118, 6263.080048, 6117.378251, 6032.746111, 5885.952286, 5803.420313,
                         5679.657184,
                         5574.094515, 5472.171938, 5366.609269, 5250.126324, 5148.203747, 5080.96016]

                if config == "ASDS" and inclination == 90:
                    x = [403.0477166, 465.8786172, 502.3610755, 607.7548442, 698.4542894, 757.7382843, 818.5423816,
                         883.4000854,
                         908.9884763, 977.6464362, 1006.021682, 1049.597951, 1100.521383, 1125.603073, 1198.56799,
                         1233.530346,
                         1283.693726, 1312.575672, 1396.941357, 1428.103457, 1479.280239, 1507.655484, 1548.191549,
                         1624.196671,
                         1657.638924, 1699.188391, 1745.804866, 1799.768502, 1844.611524, 1898.935723, 1940.377977,
                         1994.594964]

                    y = [12108.05971, 11886.0141, 11741.32044, 11412.22816, 11101.57427, 10881.3487, 10652.0229,
                         10442.04552,
                         10348.98524, 10146.05011, 10076.88836, 9953.12523, 9816.621779, 9734.719708, 9505.39391,
                         9407.111425,
                         9265.147836, 9188.705903, 8951.189898, 8861.09762, 8738.482445, 8664.53265, 8533.489337,
                         8315.083815,
                         8205.881054, 8067.557557, 7987.475532, 7879.420725, 7769.07001, 7638.026697, 7562.158741,
                         7426.901359]

                if config == "RTLS" and inclination == "SSO":
                    x = [403.2985471, 438.2847577, 498.1176581, 550.846695, 608.648206, 660.3641193, 702.9569973,
                         739.4647614,
                         794.2286706, 823.132173, 882.465983, 906.0434228, 1058.934521, 1100.382871, 1138.040832,
                         1197.375173,
                         1235.408552, 1295.393719, 1332.776272, 1391.801271, 1439.271861, 1484.911208, 1516.864772,
                         1590.650454,
                         1608.143115, 1682.692578, 1722.250931, 1743.553073, 1799.118086, 1843.969085, 1898.739609,
                         1947.427721,
                         1997.631003]

                    y = [8946.842299, 8835.611453, 8651.494957, 8467.378461, 8275.839958, 8099.145469, 7967.931448,
                         7853.656807,
                         7692.043439, 7608.168146, 7460.114001, 7384.184556, 6969.897626, 6839.731289, 6748.957831,
                         6603.198938,
                         6503.46917, 6350.915502, 6257.980508, 6091.048219, 5987.942981, 5865.19865, 5805.348382,
                         5615.880432,
                         5558.337823, 5380.358544, 5292.391774, 5251.476997, 5135.630831, 5022.354246, 4889.381221,
                         4785.04854,
                         4650.029776]

                if config == "ASDS" and inclination == "SSO":
                    x = [407.8325413, 506.5385429, 557.6444064, 603.2709971, 627.6115097, 661.0728048, 703.0545918,
                         731.039908,
                         764.5012032, 819.2542458, 884.6659186, 904.4382444, 942.4634742, 995.1926321, 1016.997347,
                         1053.503155,
                         1115.56643, 1199.53465, 1300.51559, 1325.788633, 1402.355961, 1450.023093, 1500.734387,
                         1538.762803,
                         1601.550298, 1676.182593, 1699.734165, 1788.734137, 1808.003768, 1849.076346, 1899.654279,
                         1935.78827,
                         2000.152797]

                    y = [12100.61065, 11717.64834, 11535.98673, 11358.00745, 11290.49807, 11167.75374, 11027.06425,
                         10922.26507,
                         10799.52074, 10590.85538, 10394.46445, 10320.81785, 10185.79909, 10002.20644, 9940.310429,
                         9817.566099,
                         9623.630056, 9362.364392, 9035.218217, 8958.355784, 8729.233033, 8598.305747, 8465.856564,
                         8344.63413,
                         8149.00415, 7951.852272, 7891.241055, 7538.613025, 7485.423815, 7362.679485, 7215.386288,
                         7117.190823,
                         6934.882959]
                if apogeealt >= 400:
                    with warnings.catch_warnings():
                        warnings.simplefilter('ignore', np.RankWarning)
                        coeff = numpy.polyfit(x, y, 30)
                        p = np.poly1d(coeff)
                        masslim = p(apogeealt)
                        if masslim > y[0]:
                            masslim = y[0]
                        return masslim

            print(AtlasMass(5000, 541, 0))
            print(AntaresMass(5000, 233, 0))
            print(Falcon9MassCirc(1800, "ASDS", "SSO"))

            # You need to add inclination information for the models!!! Currently not using it unless Falcon 9

            def ParkingOrbitAlgorithm(testmass, circalt, inclination):
                if circalt <= 2000 and circalt >= 400:
                    launchvehiclelist = []
                    Atlasconfigs = [551, 541, 531, 431, 521, 421, 511, 411, 501, 401]
                    Antaresconfigs = [232, 233]
                    for i in Atlasconfigs:
                        if AtlasMass(circalt, i, inclination) >= testmass:
                            launchvehiclelist.append("Atlas V " + str(i))
                    for i in Antaresconfigs:
                        if AntaresMass(circalt, i, inclination) >= testmass:
                            launchvehiclelist.append("Antares " + str(i))
                    if Falcon9MassCirc(circalt, "ASDS", inclination) >= testmass:
                        launchvehiclelist.append("Falcon 9 ASDS")
                    if Falcon9MassCirc(circalt, "RTLS", inclination) >= testmass:
                        launchvehiclelist.append("Falcon 9 RTLS")
                    return launchvehiclelist
                else:
                    print("Not Achievable")

            testmass = 5000
            launchvehiclelist = ParkingOrbitAlgorithm(testmass, 800, 45)


        elif event == "-TRAJ-":
            # LVMinaz = 26
            # LVMaxaz = 57
            # layout1 = [[sg.Text('Launch Vehicle Azimuth (between ' + str(LVMinaz) + " and " + str(LVMaxaz) + " degrees) "), sg.InputText(''), sg.Button('OK', key="-AZI-")],
            #            [sg.Button('OK', key='-TRAJDONE-', )]]
            # window1 = sg.Window('Guidance, Navigation and Control', layout1, default_element_size=(40, 1),
            #                    grab_anywhere=False)
            #
            # event, values = window1.read()
            import FreeSimpleGUI as sg
            import numpy as np
            from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
            import FreeSimpleGUI as sg
            import matplotlib
            # matplotlib.use('TkAgg')


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
                # print(r)
                h = np.sqrt(mu * a * (1 - e ** 2))

                X = r * (np.cos(math.radians(omega_LAN)) * np.cos(math.radians(omega_AP) + nu) - np.sin(
                    math.radians(omega_LAN)) * np.sin(math.radians(omega_AP) + nu) * np.cos(math.radians(i)))
                Y = r * (np.sin(math.radians(omega_LAN)) * np.cos(math.radians(omega_AP) + nu) + np.cos(
                    math.radians(omega_LAN)) * np.sin(math.radians(omega_AP) + nu) * np.cos(math.radians(i)))
                Z = r * (np.sin(math.radians(i)) * np.sin(math.radians(omega_AP) + nu))

                p = a * (1 - e ** 2)

                V_X = (X * h * e / (r * p)) * np.sin(nu) - (h / r) * (np.cos(omega_LAN) * np.sin(omega_AP + nu) + \
                                                                      np.sin(omega_LAN) * np.cos(
                            omega_AP + nu) * np.cos(i))
                V_Y = (Y * h * e / (r * p)) * np.sin(nu) - (h / r) * (np.sin(omega_LAN) * np.sin(omega_AP + nu) - \
                                                                      np.cos(omega_LAN) * np.cos(
                            omega_AP + nu) * np.cos(i))
                V_Z = (Z * h * e / (r * p)) * np.sin(nu) + (h / r) * (np.cos(omega_AP + nu) * np.sin(i))

                return [X, Y, Z], [V_X, V_Y, V_Z]

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
            for MA in range(0, 360):
                statevecxyz, statevecvxvyvz = kep_2_cart(mu, Semimajoraxis, Eccentricity, Inclination, AOP, RAAN, MA)
                # print(statevecxyz)
                X_Orb.append(statevecxyz[0])
                Y_Orb.append(statevecxyz[1])
                Z_Orb.append(statevecxyz[2])

            elev = 10.0
            rot = 80.0 / 180 * np.pi
            ax.plot_surface(x, y, z, rstride=4, cstride=4, color='r', linewidth=0, alpha=1)
            # calculate vectors for "vertical" circle
            a = np.array([-np.sin(elev / 180 * np.pi), 0, np.cos(elev / 180 * np.pi)])
            b = np.array([0, 1, 0])
            b = b * np.cos(rot) + np.cross(a, b) * np.sin(rot) + a * np.dot(a, b) * (1 - np.cos(rot))
            ax.plot(np.sin(u), np.cos(u), 0, color='k', linestyle='dashed')
            horiz_front = np.linspace(0, np.pi, 100)
            ax.plot(np.sin(horiz_front), np.cos(horiz_front), 0, color='k')
            vert_front = np.linspace(np.pi / 2, 3 * np.pi / 2, 100)
            ax.plot(a[0] * np.sin(u) + b[0] * np.cos(u), b[1] * np.cos(u), a[2] * np.sin(u) + b[2] * np.cos(u),
                    color='k', linestyle='dashed')
            ax.plot(a[0] * np.sin(vert_front) + b[0] * np.cos(vert_front), b[1] * np.cos(vert_front),
                    a[2] * np.sin(vert_front) + b[2] * np.cos(vert_front), color='k')
            ax.scatter3D(X_Orb, Y_Orb, Z_Orb, color='y')

            ax.set_facecolor("black")
            fig.set_facecolor("black")

            plt.axis('off')
            plt.grid(b=None)
            ax.set_box_aspect([1, 1, 1])

            def draw_figure(canvas, figure):
                figure_canvas_agg = FigureCanvasTkAgg(figure, canvas)
                figure_canvas_agg.draw()
                figure_canvas_agg.get_tk_widget().pack(side='top', fill='both', expand=1)
                return figure_canvas_agg

            launchdate = "09_04_2022 00:00:00.000"
            Semimajoraxis = 3000000  # meters
            Inclination = 45
            Eccentricity = 0.3

            EngineList = ["Main Engine", "RCS"]
            # BurnList = ["Earth Departure", "TCM 1", "TCM 2", "Mars Injection Orbit", "Circularization Burn"]
            BurnList = []
            Initial = "Earth"
            Destination = "Mars"
            ReferenceFrames = [Initial + " LVLH", Initial + " Centered-Inertial",
                               Initial + "-Centered, " + Initial + " Fixed", "International Celestial Reference Frame",
                               Destination + " LVLH", Destination + " Centered-Inertial",
                               Destination + "-Centered, " + Destination + " Fixed", ]

            Header = ["Burn Name", "    Engine    ", "    Time of Ignition    ", "Reference Frame", "Delta VX",
                      "Delta VY", "Delta VZ", "Mass Decrease", "Burn Duration"]
            col1 = [[sg.Text('Initial Orbital Elements', font=("Cooper", 26))],
                    [sg.Text('Reference Frame:                                 '),
                     sg.Listbox(ReferenceFrames[0:3], size=(15, 3))],
                    [sg.Text('Semi major axis:                                   '),
                     sg.InputText(Semimajoraxis / 1000, size=(15, 3)), sg.Text(' Kilometers')],
                    [sg.Text('Inclination:                                            '),
                     sg.InputText(Inclination, size=(15, 3)), sg.Text(' Degrees')],
                    [sg.Text('Eccentricity:                                         '),
                     sg.InputText(Eccentricity, size=(15, 3))],
                    [sg.Text('Right Ascension of the Ascending Node: '), sg.InputText(RAAN, size=(20, 3)),
                     sg.Text(' Degrees')],
                    [sg.Text('Arguement of Periapsis:                        '), sg.InputText(AOP, size=(20, 3)),
                     sg.Text(' Degrees')]]
            col2 = [[sg.Text('Transit Orbital Elements', font=("Cooper", 26))],
                    [sg.Text('Reference Frame:                                 '),
                     sg.Listbox(ReferenceFrames[3:4], size=(15, 3))],
                    [sg.Text('Semi major axis:                                   '),
                     sg.InputText(Semimajoraxis / 1000, size=(15, 3)), sg.Text(' Kilometers')],
                    [sg.Text('Inclination:                                            '),
                     sg.InputText(Inclination, size=(15, 3)), sg.Text(' Degrees')],
                    [sg.Text('Eccentricity:                                         '),
                     sg.InputText(Eccentricity, size=(15, 3))],
                    [sg.Text('Right Ascension of the Ascending Node: '), sg.InputText(RAAN, size=(15, 3)),
                     sg.Text(' Degrees')],
                    [sg.Text('Arguement of Periapsis:                        '), sg.InputText(AOP, size=(15, 3)),
                     sg.Text(' Degrees')]]
            col3 = [[sg.Text('Target Orbital Elements', font=("Cooper", 26))],
                    [sg.Text('Reference Frame:                                 '),
                     sg.Listbox(ReferenceFrames[4:7], size=(15, 3))],
                    [sg.Text('Semi major axis:                                   '),
                     sg.InputText(Semimajoraxis / 1000, size=(15, 3)), sg.Text(' Kilometers')],
                    [sg.Text('Inclination:                                            '),
                     sg.InputText(Inclination, size=(15, 3)), sg.Text(' Degrees')],
                    [sg.Text('Eccentricity:                                         '),
                     sg.InputText(Eccentricity, size=(15, 3))],
                    [sg.Text('Right Ascension of the Ascending Node: '), sg.InputText(RAAN, size=(15, 3)),
                     sg.Text(' Degrees')],
                    [sg.Text('Arguement of Periapsis:                        '), sg.InputText(AOP, size=(15, 3)),
                     sg.Text(' Degrees')]]
            layout = [[sg.Text('Pork Chop Plot Mission Planner'), sg.Button('OK', key="-PORK-")],
                      [sg.Text('Select Launch Vehicle'), sg.Button('OK', key= "-LAUNCH-")],
                      [sg.Column(col1), sg.Canvas(key='-CANVAS-', size=(4, 4)), sg.Column(col2),
                       sg.Canvas(key='-CANVAS1-', size=(4, 4))],
                      [sg.Column(col3), sg.Canvas(key='-CANVAS2-', size=(4, 4))],
                      [sg.Text('Add Burn', font=("Cooper", 26))],
                      [sg.Text("Burn Name: "), sg.InputText("Name", size=(15, 3), key="-NAME-"),
                       sg.Text('Select Engine: '), sg.Listbox(EngineList, size=(20, 3), key="-ENGINE-"),
                       sg.Text("Set Time of Ignition"), sg.InputText(launchdate, size=(25, 3), key="-TIG-"),
                       sg.Text(" GMT")],
                      [sg.Text("Reference Frame"), sg.InputCombo(ReferenceFrames, key="-REF-"), sg.Text("Delta Vx"),
                       sg.InputText("0", size=(6, 3), key="-DVX-"), sg.Text("m/s    "), sg.Text("Delta Vy"),
                       sg.InputText("0", size=(6, 3), key="-DVY-"), sg.Text("m/s    "), sg.Text("Delta Vz"),
                       sg.InputText("0", size=(6, 3), key="-DVZ-"), sg.Text("m/s"),
                       sg.Button("Add Burn", key="-UPDATE-"), sg.Text('Vary Burn Parameter          '),
                       sg.Listbox(('Time of Ignition', 'Burn X dV', 'Burn Y dV', 'Burn Z dV', 'Engine Used'),
                                  size=(20, 5)), sg.Button('Run Differential Corrector', key='-CORRECTOR-', )],
                      [sg.Table(BurnList, headings=Header, auto_size_columns=True, key='Table')],
                      [sg.Submit(), sg.Cancel()]]

            window2 = sg.Window('Trajectory Planner', layout, default_element_size=(40, 1), finalize=True,
                               grab_anywhere=False)
            myTable = window2['Table']
            # myTable.bind('<Button-1>', "Click")

            draw_figure(window2['-CANVAS-'].TKCanvas, fig)
            draw_figure(window2['-CANVAS1-'].TKCanvas, fig)
            draw_figure(window2['-CANVAS2-'].TKCanvas, fig)
            while True:
                event2, values2 = window2.read()
                if event2 == "Exit" or event2 == sg.WIN_CLOSED:
                    window2.close()
                    break
                if event2 == "-LAUNCH-":
                    layout3 = [
                        [sg.Text('Select Launch Vehicle', size=(25, 1)), sg.InputCombo(('Alpha', 'Antares 230',
                                                                                        'Antares 231', 'Antares 232',
                                                                                        'Antares 233', 'Electron',
                                                                                        'Electron Expanded', 'Falcon 9',
                                                                                        'Falcon Heavy', 'LauncherOne',
                                                                                        'Starship'), size=(20, 1)),
                         sg.Button("OK", key="-LV-")],
                        [sg.Text('Select Payload Adapter', size=(25, 1)), sg.InputCombo(('609.6 mm diameter',
                                                                                         '937 mm diameter',
                                                                                         '1194 mm diameter',
                                                                                         '1575 mm diameter',
                                                                                         '1666 mm diameter')),
                         sg.Button("OK", key="-ADAPTER-")],
                        [sg.Text('Payload Fairing Fit Check', size=(25, 1)), sg.Button("OK", key="-FIT-")],
                        [sg.Text('Run In-Flight Loads Test', size=(25, 1)), sg.Button("OK")],
                        [sg.Text('Run Acoustics Test', size=(25, 1)), sg.Button("OK")],
                        [sg.Text('Run Vibration Test', size=(25, 1)), sg.Button("OK")],
                        [sg.Cancel()]
                    ]
                    # https://web.archive.org/web/20180925131401/https://engineer.jpl.nasa.gov/practices/2404.pdf

                    window3 = sg.Window('Launch Vehicle', layout3, default_element_size=(40, 1), grab_anywhere=False)
                    event3, values3 = window3.read()

                    # window3.close()
                    if event3 == "Quit":
                        window3.close()
                    elif event3 == "-FIT-":
                        window3.close()

                        import FreeCAD as App
                        if App.ActiveDocument.Name == "Unnamed":
                            layout4 = [[sg.Text('Please name your project first', size=(25, 1)), sg.Button("OK")],
                                      [sg.Cancel()]]
                            # https://web.archive.org/web/20180925131401/https://engineer.jpl.nasa.gov/practices/2404.pdf

                            window4 = sg.Window('Launch Vehicle', layout4, default_element_size=(40, 1),
                                               grab_anywhere=False)
                            window4.close()
                            pass

                        launchvehicle = values[0].replace(" ", "")
                        # launchvehicle = launchvehicle
                        with open(
                                SCDesignerPath + "\\AssemblyInclude.txt",
                                'w+') as f:
                            f.write("LaunchVehicles\\" + launchvehicle + "Fairing.fcstd")

                        import FreeCADGui as Gui

                        Gui.activateWorkbench("A2plusWorkbench")  # A2p_import_part.py was modified
                        Gui.runCommand('a2p_ImportPart', 0)
                        os.remove(
                            SCDesignerPath + "\\AssemblyInclude.txt")
                        fairingname = "b_" + launchvehicle + "_001_"
                        Gui.Selection.addSelection('Assembly2', fairingname, 'Edge29', 0.00, 0.00, 0.00)
                        Gui.activateWorkbench("SpacecraftDesigner")

                if event == "-PORK-":
                    window.close()
                    Departure = "Earth"
                    targetBody = "Jupiter"
                    with open(SCDesignerPath + "\\DepartureDest.csv", "w+") as f:
                        f.write(Departure + "," + targetBody)
                    f.close()
                    os.startfile(SCDesignerPath + "\\PorkchopPlotFreeCAD\\PorkchopPlotFreeCAD.exe")

                    import subprocess
                    import time
                    def process_exists(process_name):
                        call = 'TASKLIST', '/FI', 'imagename eq %s' % process_name
                        output = subprocess.check_output(call).decode()
                        last_line = output.strip().split('\r\n')[-1]
                        return last_line.lower().startswith(process_name.lower())

                    while process_exists("PorkchopPlotFreeCAD.exe") == True:
                        time.sleep(1)

                    import io
                    import os
                    import FreeSimpleGUI as sg
                    from PIL import Image
                    filename = SCDesignerPath + "\\PORKCHOP.png"
                    image = Image.open(filename)
                    image.thumbnail((700, 700))
                    bio = io.BytesIO()
                    image.save(bio, format="PNG")
                    layout = [
                        [sg.Image(data=bio.getvalue(), key="-IMAGE-")],
                        [sg.Button("Done")]]
                    window = sg.Window("Image Viewer", layout)
                    # while True:
                    event, values = window.read()
                    if event == "Done" or event == sg.WIN_CLOSED:
                        window.close()
                    #     if event == "Load Image":
                    #         filename = SCDesignerPath + "\\PORKCHOP.png"
                    #         if os.path.exists(filename):
                    #             image = Image.open(filename)
                    #             image.thumbnail((700, 700))
                    #             bio = io.BytesIO()
                    #             image.save(bio, format="PNG")
                    #             window["-IMAGE-"].update(data=bio.getvalue())
                    #

                if event == "-UPDATE-":
                    BurnList.append(
                        [values["-NAME-"], values["-ENGINE-"][0], values["-TIG-"], values["-REF-"], values["-DVX-"],
                         values["-DVY-"], values["-DVZ-"]])
                    window['Table'].update(BurnList)




        elif event == "-ACTUATOR-":

            if values[0] == "Rotary Actuator":
                import math
                layout1 = [[sg.Text('Select Electrical Motor Type'), sg.InputCombo(('Brushed DC Motor', 'Brushless DC Motor', 'AC Induction Motor', 'Servo Motor', 'Stepper Motor')), sg.Button('OK')]
                           ]
                window1 = sg.Window('Select Electrical Motor', layout1, default_element_size=(40, 1), grab_anywhere=False)

                event1, values1 = window1.read()
                window1.close()
                if event1 == "Exit" or event1 == sg.WIN_CLOSED:
                    pass
                if values1[0] == 'Servo Motor':
                    import FreeSimpleGUI as sg
                    import matplotlib.pyplot as plt

                    # Define GUI layout
                    layout = [
                        [sg.Text('Select Motor Type:')],
                        [sg.Radio('Brushless DC', 'motor_type', default=True, key='BLDC')],
                        [sg.Radio('Permanent Magnet Synchronous', 'motor_type', key='PMSM')],
                        [sg.Radio('AC Induction', 'motor_type', key='ACIM')],
                        [sg.Radio('Stepper', 'motor_type', key='STEPPER')],
                        [sg.Text('Number of Windings:'), sg.InputText(default_text='10', key='num_windings')],
                        [sg.Text('Wire Gauge:'), sg.InputText(default_text='18', key='wire_gauge')],
                        [sg.Text('Temperature (C):'), sg.InputText(default_text='25', key='temp')],
                        [sg.Button('Design Motor')],
                        [sg.Button('Plot Results')]
                    ]

                    # Create the window
                    window = sg.Window('Motor Design', layout)

                    # Define function to plot motor performance
                    def plot_results(torque, velocity):
                        fig, ax = plt.subplots()
                        ax.plot(torque, velocity)
                        ax.set_xlabel('Torque (Nm)')
                        ax.set_ylabel('Velocity (rad/s)')
                        plt.show()

                    # Event loop
                    while True:
                        event, values = window.read()
                        if event == sg.WIN_CLOSED:
                            break
                        if event == 'Design Motor':
                            # Get motor parameters from GUI
                            motor_type = 'BLDC' if values['BLDC'] else 'PMSM' if values['PMSM'] else 'ACIM' if values[
                                'ACIM'] else 'STEPPER'
                            num_windings = int(values['num_windings'])
                            wire_gauge = int(values['wire_gauge'])
                            temp = float(values['temp'])

                            # Design the motor
                            # TODO: Implement PYLEECAN motor design code here

                        if event == 'Plot Results':
                            # Get motor performance data
                            # TODO: Replace with actual motor performance data
                            torque = [0, 1, 2, 3, 4]
                            velocity = [0, 10, 20, 30, 40]

                            # Plot the results
                            plot_results(torque, velocity)

                    # Close the window
                    window.close()

                if values1[0] == 'Brushed DC Motor':
                    import FreeCAD as App
                    import Part
                    import math
                    import FreeSimpleGUI as sg

                    def designMotor(torque, k_t, k_e):
                        # Calculate motor dimensions
                        diameter = math.sqrt((60 * torque) / (math.pi * k_t))
                        length = k_e * diameter

                        # Create motor parts
                        shaft = Part.makeCylinder(diameter / 2, length)
                        magnet = Part.makeBox(diameter / 2, diameter / 2, length)
                        stator = Part.makeCylinder(diameter / 2 * 1.2, length * 1.1)

                        # Position motor parts
                        magnet.translate(App.Vector(0, 0, length / 2))
                        stator.translate(App.Vector(0, 0, length / 2))
                        shaft.translate(App.Vector(0, 0, -length / 2))

                        # Create motor assembly
                        motor = stator.cut(magnet)
                        motor = motor.cut(shaft)

                        return motor

                    # FreeSimpleGUI inputs
                    layout = [
                        [sg.Text("Enter motor requirements:")],
                        [sg.Text("Torque (N*m):"), sg.InputText(key="torque")],
                        [sg.Text("Torque constant (N*m/A):"), sg.InputText(key="k_t")],
                        [sg.Text("Back-EMF constant (V/(rad/s)):"), sg.InputText(key="k_e")],
                        [sg.Button("Design Motor")]
                    ]

                    # Create FreeSimpleGUI window
                    window1 = sg.Window("Motor Design", layout)

                    while True:
                        # Read values from FreeSimpleGUI window
                        event, values = window1.read()

                        # Exit when the window is closed
                        if event == sg.WIN_CLOSED:
                            break

                        # Design motor when the button is pressed
                        if event == "Design Motor":
                            try:
                                torque = float(values["torque"])
                                k_t = float(values["k_t"])
                                k_e = float(values["k_e"])

                                motor = designMotor(torque, k_t, k_e)

                                # Display motor in FreeCAD
                                Part.show(motor)
                            except ValueError:
                                sg.Popup("Invalid input. Please enter numbers.")
                            except Exception as e:
                                sg.Popup(f"An error occurred: {str(e)}")
                if values1[0] == "Brushless DC Motor":
                    layout2 = [
                        [sg.Text("Angular Acceleration:  "), sg.Image(
                            'C:\\Users\\' + username + '\\AppData\\Roaming\\FreeCAD\\Mod\\SpacecraftDesigner\\Controllers\\AngAccel.png')],
                        [sg.Text("Moment of Inertia:  "), sg.Image(
                            'C:\\Users\\' + username + '\\AppData\\Roaming\\FreeCAD\\Mod\\SpacecraftDesigner\\Controllers\\MomentOfInertia.png')],
                        [sg.Text("Torque Constant:  "), sg.Image(
                            'C:\\Users\\' + username + '\\AppData\\Roaming\\FreeCAD\\Mod\\SpacecraftDesigner\\Controllers\\TorqueConst.png')],
                        [sg.Text("Electrical Current:  "), sg.Image(
                            'C:\\Users\\' + username + '\\AppData\\Roaming\\FreeCAD\\Mod\\SpacecraftDesigner\\Controllers\\Current.png')],
                        [sg.Text("Motor Damping Coefficient:  "), sg.Image(
                            'C:\\Users\\' + username + '\\AppData\\Roaming\\FreeCAD\\Mod\\SpacecraftDesigner\\Controllers\\MotorDamping.png')],
                        [sg.Text("Angular Speed:  "), sg.Image(
                            'C:\\Users\\' + username + '\\AppData\\Roaming\\FreeCAD\\Mod\\SpacecraftDesigner\\Controllers\\AngSpeed.png')],
                        [sg.Image('C:\\Users\\' + username + '\\AppData\\Roaming\\FreeCAD\\Mod\\SpacecraftDesigner\\Controllers\\BrushlessDCEqn1.png')],
                        [[sg.Image('C:\\Users\\' + username + '\\AppData\\Roaming\\FreeCAD\\Mod\\SpacecraftDesigner\\Controllers\\BrushlessDCEqn2.png')]]]
                    window2 = sg.Window('Brushless DC Motor Designer', layout2, default_element_size=(40, 1),
                                        grab_anywhere=False)

                    event2, values2 = window2.read()
                    k_e = 1 # TBR         #https://www.youtube.com/watch?v=9eUxWdtOrik&t=186s
                    # https://pypi.org/project/gym-electric-motor/
                    torque_const = k_e

                    # Km =
                    # Kt =
                    # Kv =

                    # P = V**2/R
                    #
                    # motor_const_ = torque_const/math.sqrt(P) #https://www.faulhaber.com/fileadmin/user_upload_global/support/MC_Support/Motors/Tutorials_Motors/dff_200276_whitepaper_motorcalculation_fin.pdf
                    J = 0.01
                    b = 0.1
                    K = 0.01
                    R = 1
                    L = 0.5

                    from scipy import signal
                    from matplotlib import pyplot as plt

                    # https://ctms.engin.umich.edu/CTMS/index.php?example=MotorSpeed&section=SystemModeling
                    A = [[-b / J, K / J], [-K / L, -R / L]]
                    B = [[1.], [1.]]
                    C = [[1., 0.]]
                    D = [[0.]]

                    motor_ss = signal.StateSpace(A, B, C, D)

                    t2, y2 = signal.step(motor_ss)
                    plt.plot(t2, y2)
                    plt.show()

                    shaft_diameter = 0.2
                    motor_diameter = 2
                    shaft_length = 1
                    motor_length = 1
                    lines = [[0, 0], [0, motor_diameter / 2], [motor_length, motor_diameter / 2],
                             [motor_length, shaft_diameter / 2], [motor_length + shaft_length, shaft_diameter / 2],
                             [motor_length + shaft_length, 0], [0, 0]]
                    # with open("MotorMacro.FCmacro", "w+") as f:
                    import Part
                    import PartDesign
                    import PartDesignGui
                    import Sketcher
                    import FreeCADGui as Gui
                    App.newDocument("Unnamed")
                    App.setActiveDocument("Unnamed")
                    App.ActiveDocument=App.getDocument("Unnamed")
                    Gui.ActiveDocument=Gui.getDocument("Unnamed")
                    Gui.activateWorkbench("PartDesignWorkbench")
                    App.activeDocument().addObject('PartDesign::Body','Body')
                    import PartDesignGui
                    Gui.activeView().setActiveObject('pdbody', App.activeDocument().Body)
                    Gui.Selection.clearSelection()
                    Gui.Selection.addSelection(App.ActiveDocument.Body)
                    App.ActiveDocument.recompute()
                    App.activeDocument().Body.newObject('Sketcher::SketchObject','Sketch')
                    App.activeDocument().Sketch.Support = (App.activeDocument().XY_Plane, [''])
                    App.activeDocument().Sketch.MapMode = 'FlatFace'
                    App.ActiveDocument.recompute()
                    Gui.activeDocument().setEdit('Sketch')
                    Gui.activateWorkbench('SketcherWorkbench')
                    import PartDesignGui
                    for i in range(0, len(lines) - 1):
                        App.ActiveDocument.Sketch.addGeometry(Part.LineSegment(App.Vector(lines[i][0], lines[i][1]),App.Vector(lines[i + 1][0], lines[i + 1][1])),False)
                    App.ActiveDocument.recompute()
                    Gui.getDocument('Unnamed').resetEdit()
                    ActiveSketch = App.ActiveDocument.getObject('Sketch')
                    Gui.getDocument("Unnamed").getObject("Sketch").Visibility=True
                    Gui.SendMsgToActiveView("ViewFit")
                    App.activeDocument().Body.newObject("PartDesign::Revolution","Revolution")
                    App.activeDocument().Revolution.Profile = App.activeDocument().Sketch
                    App.activeDocument().Revolution.ReferenceAxis = (App.activeDocument().Sketch,['V_Axis'])
                    App.activeDocument().Revolution.Angle = 360.0
                    App.activeDocument().Revolution.Reversed = 1
                    Gui.activeDocument().hide("Sketch")
                    App.ActiveDocument.recompute()
                    Gui.ActiveDocument.Revolution.ShapeColor=Gui.ActiveDocument.Body.ShapeColor
                    Gui.ActiveDocument.Revolution.LineColor=Gui.ActiveDocument.Body.LineColor
                    Gui.ActiveDocument.Revolution.PointColor=Gui.ActiveDocument.Body.PointColor
                    Gui.ActiveDocument.Revolution.Transparency=Gui.ActiveDocument.Body.Transparency
                    Gui.ActiveDocument.Revolution.DisplayMode=Gui.ActiveDocument.Body.DisplayMode
                    Gui.activeDocument().setEdit('Revolution', 0)
                    Gui.Selection.clearSelection()
                    Gui.activeDocument().hide("Sketch")
                    App.ActiveDocument.Revolution.Angle = 360.000000
                    App.ActiveDocument.Revolution.ReferenceAxis = (App.ActiveDocument.X_Axis, [""])
                    App.ActiveDocument.Revolution.Midplane = 0
                    App.ActiveDocument.Revolution.Reversed = 1
                    App.ActiveDocument.recompute()
                    Gui.activeDocument().resetEdit()
                    Gui.activeDocument().activeView().viewIsometric()
                    Gui.SendMsgToActiveView("ViewFit")

            if values[0] == "Linear Actuator":
                print("Linear Actuator")
                maxlength = 4 # m
                minlength = 2 # m
                # print(new_veh)
                global new_vehicle
                new_vehicle.system_list["Linear Actuator"] = {"maxlength":maxlength,"minlength":minlength}

                # print(new_vehicle.name)

            if values[0] == "Linear Spring":
                print("Linear Spring")
            if values[0] == "Rotary Spring":
                print("Rotary Spring")
            if values[0] == "Linear Damper":
                print("Linear Damper")
            if values[0] == "Rotary Damper":
                print("Rotary Damper")


        elif event == "-SEQUENCE-":
            """
            A rocket powered landing with successive convexification
            author: Sven Niederberger
                    Atsushi Sakai
            Ref:
            - Python implementation of 'Successive Convexification for 6-DoF Mars Rocket Powered Landing with Free-Final-Time' paper
            by Michael Szmuk and Behcet Acıkmese.
            - EmbersArc/SuccessiveConvexificationFreeFinalTime: Implementation of "Successive Convexification for 6-DoF Mars Rocket Powered Landing with Free-Final-Time" https://github.com/EmbersArc/SuccessiveConvexificationFreeFinalTime
            """

            from time import time
            import numpy as np
            from scipy.integrate import odeint
            import cvxpy
            import matplotlib.pyplot as plt
            from mpl_toolkits import mplot3d

            # Trajectory points
            K = 50

            # Max solver iterations
            iterations = 30

            # Weight constants
            W_SIGMA = 1  # flight time
            W_DELTA = 1e-3  # difference in state/input
            W_DELTA_SIGMA = 1e-1  # difference in flight time
            W_NU = 1e5  # virtual control

            solver = 'ECOS'
            verbose_solver = False

            show_animation = True

            class Rocket_Model_6DoF:
                """
                A 6 degree of freedom rocket landing problem.
                """

                def __init__(self):
                    """
                    A large r_scale for a small scale problem will
                    ead to numerical problems as parameters become excessively small
                    and (it seems) precision is lost in the dynamics.
                    """
                    self.n_x = 14
                    self.n_u = 3

                    # Mass
                    self.m_wet = 3.0  # 30000 kg
                    self.m_dry = 2.2  # 22000 kg

                    # Flight time guess
                    self.t_f_guess = 10.0  # 10 s

                    # State constraints
                    self.r_I_final = np.array((0., 0., 0.))
                    self.v_I_final = np.array((-1e-1, 0., 0.))
                    self.q_B_I_final = self.euler_to_quat((0, 0, 0))
                    self.w_B_final = np.deg2rad(np.array((0., 0., 0.)))

                    self.w_B_max = np.deg2rad(60)

                    # Angles
                    max_gimbal = 20
                    max_angle = 90
                    glidelslope_angle = 20

                    self.tan_delta_max = np.tan(np.deg2rad(max_gimbal))
                    self.cos_theta_max = np.cos(np.deg2rad(max_angle))
                    self.tan_gamma_gs = np.tan(np.deg2rad(glidelslope_angle))

                    # Thrust limits
                    self.T_max = 5.0
                    self.T_min = 0.3

                    # Angular moment of inertia
                    self.J_B = 1e-2 * np.diag([1., 1., 1.])

                    # Gravity
                    self.g_I = np.array((-1, 0., 0.))

                    # Fuel consumption
                    self.alpha_m = 0.01

                    # Vector from thrust point to CoM
                    self.r_T_B = np.array([-1e-2, 0., 0.])

                    self.set_random_initial_state()

                    self.x_init = np.concatenate(
                        ((self.m_wet,), self.r_I_init, self.v_I_init, self.q_B_I_init, self.w_B_init))
                    self.x_final = np.concatenate(
                        ((self.m_dry,), self.r_I_final, self.v_I_final, self.q_B_I_final, self.w_B_final))

                    self.r_scale = np.linalg.norm(self.r_I_init)
                    self.m_scale = self.m_wet

                def set_random_initial_state(self):
                    self.r_I_init = np.array((0., 0., 0.))
                    self.r_I_init[0] = np.random.uniform(3, 4)
                    print("Here")
                    print(self.r_I_init[0])
                    print("Here")
                    self.r_I_init[1:3] = np.random.uniform(-2, 2, size=2)
                    print(self.r_I_init[1:3])
                    print("Here")
                    self.v_I_init = np.array((0., 0., 0.))
                    self.v_I_init[0] = np.random.uniform(-1, -0.5)
                    self.v_I_init[1:3] = np.random.uniform(
                        -0.5, -0.2, size=2) * self.r_I_init[1:3]

                    self.q_B_I_init = self.euler_to_quat((0,
                                                          np.random.uniform(-30, 30),
                                                          np.random.uniform(-30, 30)))
                    self.w_B_init = np.deg2rad((0,
                                                np.random.uniform(-20, 20),
                                                np.random.uniform(-20, 20)))

                def f_func(self, x, u):
                    m, rx, ry, rz, vx, vy, vz, q0, q1, q2, q3, wx, wy, wz = x[0], x[1], x[
                        2], x[3], x[4], x[5], x[6], x[7], x[8], x[9], x[10], x[11], x[12], x[13]
                    ux, uy, uz = u[0], u[1], u[2]

                    return np.matrix([
                        [-0.01 * np.sqrt(ux ** 2 + uy ** 2 + uz ** 2)],
                        [vx],
                        [vy],
                        [vz],
                        [(-1.0 * m - ux * (2 * q2 ** 2 + 2 * q3 ** 2 - 1) - 2 * uy
                          * (q0 * q3 - q1 * q2) + 2 * uz * (q0 * q2 + q1 * q3)) / m],
                        [(2 * ux * (q0 * q3 + q1 * q2) - uy * (2 * q1 ** 2
                                                               + 2 * q3 ** 2 - 1) - 2 * uz * (q0 * q1 - q2 * q3)) / m],
                        [(-2 * ux * (q0 * q2 - q1 * q3) + 2 * uy
                          * (q0 * q1 + q2 * q3) - uz * (2 * q1 ** 2 + 2 * q2 ** 2 - 1)) / m],
                        [-0.5 * q1 * wx - 0.5 * q2 * wy - 0.5 * q3 * wz],
                        [0.5 * q0 * wx + 0.5 * q2 * wz - 0.5 * q3 * wy],
                        [0.5 * q0 * wy - 0.5 * q1 * wz + 0.5 * q3 * wx],
                        [0.5 * q0 * wz + 0.5 * q1 * wy - 0.5 * q2 * wx],
                        [0],
                        [1.0 * uz],
                        [-1.0 * uy]
                    ])

                def A_func(self, x, u):
                    m, rx, ry, rz, vx, vy, vz, q0, q1, q2, q3, wx, wy, wz = x[0], x[1], x[
                        2], x[3], x[4], x[5], x[6], x[7], x[8], x[9], x[10], x[11], x[12], x[13]
                    ux, uy, uz = u[0], u[1], u[2]

                    return np.matrix([
                        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                        [0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                        [0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0],
                        [0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0],
                        [(ux * (2 * q2 ** 2 + 2 * q3 ** 2 - 1) + 2 * uy * (q0 * q3 - q1 * q2) - 2 * uz * (
                                    q0 * q2 + q1 * q3)) / m ** 2, 0, 0, 0, 0, 0, 0, 2 * (q2 * uz
                                                                                         - q3 * uy) / m,
                         2 * (q2 * uy + q3 * uz) / m, 2 * (q0 * uz + q1 * uy - 2 * q2 * ux) / m,
                         2 * (-q0 * uy + q1 * uz - 2 * q3 * ux) / m, 0, 0, 0],
                        [(-2 * ux * (q0 * q3 + q1 * q2) + uy * (2 * q1 ** 2 + 2 * q3 ** 2 - 1) + 2 * uz * (
                                    q0 * q1 - q2 * q3)) / m ** 2, 0, 0, 0, 0, 0, 0, 2 * (-q1 * uz
                                                                                         + q3 * ux) / m,
                         2 * (-q0 * uz - 2 * q1 * uy + q2 * ux) / m, 2 * (q1 * ux + q3 * uz) / m,
                         2 * (q0 * ux + q2 * uz - 2 * q3 * uy) / m, 0, 0, 0],
                        [(2 * ux * (q0 * q2 - q1 * q3) - 2 * uy * (q0 * q1 + q2 * q3) + uz * (
                                    2 * q1 ** 2 + 2 * q2 ** 2 - 1)) / m ** 2, 0, 0, 0, 0, 0, 0, 2 * (q1 * uy
                                                                                                     - q2 * ux) / m,
                         2 * (q0 * uy - 2 * q1 * uz + q3 * ux) / m, 2 * (-q0 * ux - 2 * q2 * uz + q3 * uy) / m,
                         2 * (q1 * ux + q2 * uy) / m, 0, 0, 0],
                        [0, 0, 0, 0, 0, 0, 0, 0, -0.5 * wx, -0.5 * wy,
                         - 0.5 * wz, -0.5 * q1, -0.5 * q2, -0.5 * q3],
                        [0, 0, 0, 0, 0, 0, 0, 0.5 * wx, 0, 0.5 * wz,
                         - 0.5 * wy, 0.5 * q0, -0.5 * q3, 0.5 * q2],
                        [0, 0, 0, 0, 0, 0, 0, 0.5 * wy, -0.5 * wz, 0,
                         0.5 * wx, 0.5 * q3, 0.5 * q0, -0.5 * q1],
                        [0, 0, 0, 0, 0, 0, 0, 0.5 * wz, 0.5 * wy,
                         - 0.5 * wx, 0, -0.5 * q2, 0.5 * q1, 0.5 * q0],
                        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]])

                def B_func(self, x, u):
                    m, rx, ry, rz, vx, vy, vz, q0, q1, q2, q3, wx, wy, wz = x[0], x[1], x[
                        2], x[3], x[4], x[5], x[6], x[7], x[8], x[9], x[10], x[11], x[12], x[13]
                    ux, uy, uz = u[0], u[1], u[2]

                    return np.matrix([
                        [-0.01 * ux / np.sqrt(ux ** 2 + uy ** 2 + uz ** 2),
                         -0.01 * uy / np.sqrt(ux ** 2 + uy ** 2 + uz ** 2),
                         -0.01 * uz / np.sqrt(ux ** 2 + uy ** 2 + uz ** 2)],
                        [0, 0, 0],
                        [0, 0, 0],
                        [0, 0, 0],
                        [(-2 * q2 ** 2 - 2 * q3 ** 2 + 1) / m, 2
                         * (-q0 * q3 + q1 * q2) / m, 2 * (q0 * q2 + q1 * q3) / m],
                        [2 * (q0 * q3 + q1 * q2) / m, (-2 * q1 ** 2 - 2
                                                       * q3 ** 2 + 1) / m, 2 * (-q0 * q1 + q2 * q3) / m],
                        [2 * (-q0 * q2 + q1 * q3) / m, 2 * (q0 * q1 + q2 * q3)
                         / m, (-2 * q1 ** 2 - 2 * q2 ** 2 + 1) / m],
                        [0, 0, 0],
                        [0, 0, 0],
                        [0, 0, 0],
                        [0, 0, 0],
                        [0, 0, 0],
                        [0, 0, 1.0],
                        [0, -1.0, 0]
                    ])

                def euler_to_quat(self, a):
                    a = np.deg2rad(a)

                    cy = np.cos(a[1] * 0.5)
                    sy = np.sin(a[1] * 0.5)
                    cr = np.cos(a[0] * 0.5)
                    sr = np.sin(a[0] * 0.5)
                    cp = np.cos(a[2] * 0.5)
                    sp = np.sin(a[2] * 0.5)

                    q = np.zeros(4)

                    q[0] = cy * cr * cp + sy * sr * sp
                    q[1] = cy * sr * cp - sy * cr * sp
                    q[3] = cy * cr * sp + sy * sr * cp
                    q[2] = sy * cr * cp - cy * sr * sp

                    return q

                def skew(self, v):
                    return np.matrix([
                        [0, -v[2], v[1]],
                        [v[2], 0, -v[0]],
                        [-v[1], v[0], 0]
                    ])

                def dir_cosine(self, q):
                    return np.matrix([
                        [1 - 2 * (q[2] ** 2 + q[3] ** 2), 2 * (q[1] * q[2]
                                                               + q[0] * q[3]), 2 * (q[1] * q[3] - q[0] * q[2])],
                        [2 * (q[1] * q[2] - q[0] * q[3]), 1 - 2
                         * (q[1] ** 2 + q[3] ** 2), 2 * (q[2] * q[3] + q[0] * q[1])],
                        [2 * (q[1] * q[3] + q[0] * q[2]), 2 * (q[2] * q[3]
                                                               - q[0] * q[1]), 1 - 2 * (q[1] ** 2 + q[2] ** 2)]
                    ])

                def omega(self, w):
                    return np.matrix([
                        [0, -w[0], -w[1], -w[2]],
                        [w[0], 0, w[2], -w[1]],
                        [w[1], -w[2], 0, w[0]],
                        [w[2], w[1], -w[0], 0],
                    ])

                def initialize_trajectory(self, X, U):
                    """
                    Initialize the trajectory with linear approximation.
                    """
                    K = X.shape[1]

                    for k in range(K):
                        alpha1 = (K - k) / K
                        alpha2 = k / K

                        m_k = (alpha1 * self.x_init[0] + alpha2 * self.x_final[0],)
                        r_I_k = alpha1 * self.x_init[1:4] + alpha2 * self.x_final[1:4]
                        v_I_k = alpha1 * self.x_init[4:7] + alpha2 * self.x_final[4:7]
                        q_B_I_k = np.array([1, 0, 0, 0])
                        w_B_k = alpha1 * self.x_init[11:14] + alpha2 * self.x_final[11:14]

                        X[:, k] = np.concatenate((m_k, r_I_k, v_I_k, q_B_I_k, w_B_k))
                        U[:, k] = m_k * -self.g_I

                    return X, U

                def get_constraints(self, X_v, U_v, X_last_p, U_last_p):
                    """
                    Get model specific constraints.
                    :param X_v: cvx variable for current states
                    :param U_v: cvx variable for current inputs
                    :param X_last_p: cvx parameter for last states
                    :param U_last_p: cvx parameter for last inputs
                    :return: A list of cvx constraints
                    """
                    # Boundary conditions:
                    constraints = [
                        X_v[0, 0] == self.x_init[0],
                        X_v[1:4, 0] == self.x_init[1:4],
                        X_v[4:7, 0] == self.x_init[4:7],
                        # X_v[7:11, 0] == self.x_init[7:11],  # initial orientation is free
                        X_v[11:14, 0] == self.x_init[11:14],

                        # X_[0, -1] final mass is free
                        X_v[1:, -1] == self.x_final[1:],
                        U_v[1:3, -1] == 0,
                    ]

                    constraints += [
                        # State constraints:
                        X_v[0, :] >= self.m_dry,  # minimum mass
                        cvxpy.norm(X_v[2: 4, :], axis=0) <= X_v[1, :] / \
                        self.tan_gamma_gs,  # glideslope
                        cvxpy.norm(X_v[9:11, :], axis=0) <= np.sqrt(
                            (1 - self.cos_theta_max) / 2),  # maximum angle
                        # maximum angular velocity
                        cvxpy.norm(X_v[11: 14, :], axis=0) <= self.w_B_max,

                        # Control constraints:
                        cvxpy.norm(U_v[1:3, :], axis=0) <= self.tan_delta_max * \
                        U_v[0, :],  # gimbal angle constraint
                        cvxpy.norm(U_v, axis=0) <= self.T_max,  # upper thrust constraint
                    ]

                    # linearized lower thrust constraint
                    rhs = [U_last_p[:, k] / cvxpy.norm(U_last_p[:, k]) * U_v[:, k]
                           for k in range(X_v.shape[1])]
                    constraints += [
                        self.T_min <= cvxpy.vstack(rhs)
                    ]

                    return constraints

            class Integrator:
                def __init__(self, m, K):
                    self.K = K
                    self.m = m
                    self.n_x = m.n_x
                    self.n_u = m.n_u

                    self.A_bar = np.zeros([m.n_x * m.n_x, K - 1])
                    self.B_bar = np.zeros([m.n_x * m.n_u, K - 1])
                    self.C_bar = np.zeros([m.n_x * m.n_u, K - 1])
                    self.S_bar = np.zeros([m.n_x, K - 1])
                    self.z_bar = np.zeros([m.n_x, K - 1])

                    # vector indices for flat matrices
                    x_end = m.n_x
                    A_bar_end = m.n_x * (1 + m.n_x)
                    B_bar_end = m.n_x * (1 + m.n_x + m.n_u)
                    C_bar_end = m.n_x * (1 + m.n_x + m.n_u + m.n_u)
                    S_bar_end = m.n_x * (1 + m.n_x + m.n_u + m.n_u + 1)
                    z_bar_end = m.n_x * (1 + m.n_x + m.n_u + m.n_u + 2)
                    self.x_ind = slice(0, x_end)
                    self.A_bar_ind = slice(x_end, A_bar_end)
                    self.B_bar_ind = slice(A_bar_end, B_bar_end)
                    self.C_bar_ind = slice(B_bar_end, C_bar_end)
                    self.S_bar_ind = slice(C_bar_end, S_bar_end)
                    self.z_bar_ind = slice(S_bar_end, z_bar_end)

                    self.f, self.A, self.B = m.f_func, m.A_func, m.B_func

                    # integration initial condition
                    self.V0 = np.zeros((m.n_x * (1 + m.n_x + m.n_u + m.n_u + 2),))
                    self.V0[self.A_bar_ind] = np.eye(m.n_x).reshape(-1)

                    self.dt = 1. / (K - 1)

                def calculate_discretization(self, X, U, sigma):
                    """
                    Calculate discretization for given states, inputs and total time.
                    :param X: Matrix of states for all time points
                    :param U: Matrix of inputs for all time points
                    :param sigma: Total time
                    :return: The discretization matrices
                    """
                    for k in range(self.K - 1):
                        self.V0[self.x_ind] = X[:, k]
                        V = np.array(odeint(self._ode_dVdt, self.V0, (0, self.dt),
                                            args=(U[:, k], U[:, k + 1], sigma))[1, :])

                        # using \Phi_A(\tau_{k+1},\xi) = \Phi_A(\tau_{k+1},\tau_k)\Phi_A(\xi,\tau_k)^{-1}
                        # flatten matrices in column-major (Fortran) order for CVXPY
                        Phi = V[self.A_bar_ind].reshape((self.n_x, self.n_x))
                        self.A_bar[:, k] = Phi.flatten(order='F')
                        self.B_bar[:, k] = np.matmul(Phi, V[self.B_bar_ind].reshape(
                            (self.n_x, self.n_u))).flatten(order='F')
                        self.C_bar[:, k] = np.matmul(Phi, V[self.C_bar_ind].reshape(
                            (self.n_x, self.n_u))).flatten(order='F')
                        self.S_bar[:, k] = np.matmul(Phi, V[self.S_bar_ind])
                        self.z_bar[:, k] = np.matmul(Phi, V[self.z_bar_ind])

                    return self.A_bar, self.B_bar, self.C_bar, self.S_bar, self.z_bar

                def _ode_dVdt(self, V, t, u_t0, u_t1, sigma):
                    """
                    ODE function to compute dVdt.
                    :param V: Evaluation state V = [x, Phi_A, B_bar, C_bar, S_bar, z_bar]
                    :param t: Evaluation time
                    :param u_t0: Input at start of interval
                    :param u_t1: Input at end of interval
                    :param sigma: Total time
                    :return: Derivative at current time and state dVdt
                    """
                    alpha = (self.dt - t) / self.dt
                    beta = t / self.dt
                    x = V[self.x_ind]
                    u = u_t0 + beta * (u_t1 - u_t0)

                    # using \Phi_A(\tau_{k+1},\xi) = \Phi_A(\tau_{k+1},\tau_k)\Phi_A(\xi,\tau_k)^{-1}
                    # and pre-multiplying with \Phi_A(\tau_{k+1},\tau_k) after integration
                    Phi_A_xi = np.linalg.inv(
                        V[self.A_bar_ind].reshape((self.n_x, self.n_x)))

                    A_subs = sigma * self.A(x, u)
                    B_subs = sigma * self.B(x, u)
                    f_subs = self.f(x, u)

                    dVdt = np.zeros_like(V)
                    dVdt[self.x_ind] = sigma * f_subs.transpose()
                    dVdt[self.A_bar_ind] = np.matmul(
                        A_subs, V[self.A_bar_ind].reshape((self.n_x, self.n_x))).reshape(-1)
                    dVdt[self.B_bar_ind] = np.matmul(Phi_A_xi, B_subs).reshape(-1) * alpha
                    dVdt[self.C_bar_ind] = np.matmul(Phi_A_xi, B_subs).reshape(-1) * beta
                    dVdt[self.S_bar_ind] = np.matmul(Phi_A_xi, f_subs).transpose()
                    z_t = -np.matmul(A_subs, x) - np.matmul(B_subs, u)
                    dVdt[self.z_bar_ind] = np.dot(Phi_A_xi, z_t.T).flatten()

                    return dVdt

            class SCProblem:
                """
                Defines a standard Successive Convexification problem and
                        adds the model specific constraints and objectives.
                :param m: The model object
                :param K: Number of discretization points
                """

                def __init__(self, m, K):
                    # Variables:
                    self.var = dict()
                    self.var['X'] = cvxpy.Variable((m.n_x, K))
                    self.var['U'] = cvxpy.Variable((m.n_u, K))
                    self.var['sigma'] = cvxpy.Variable(nonneg=True)
                    self.var['nu'] = cvxpy.Variable((m.n_x, K - 1))
                    self.var['delta_norm'] = cvxpy.Variable(nonneg=True)
                    self.var['sigma_norm'] = cvxpy.Variable(nonneg=True)

                    # Parameters:
                    self.par = dict()
                    self.par['A_bar'] = cvxpy.Parameter((m.n_x * m.n_x, K - 1))
                    self.par['B_bar'] = cvxpy.Parameter((m.n_x * m.n_u, K - 1))
                    self.par['C_bar'] = cvxpy.Parameter((m.n_x * m.n_u, K - 1))
                    self.par['S_bar'] = cvxpy.Parameter((m.n_x, K - 1))
                    self.par['z_bar'] = cvxpy.Parameter((m.n_x, K - 1))

                    self.par['X_last'] = cvxpy.Parameter((m.n_x, K))
                    self.par['U_last'] = cvxpy.Parameter((m.n_u, K))
                    self.par['sigma_last'] = cvxpy.Parameter(nonneg=True)

                    self.par['weight_sigma'] = cvxpy.Parameter(nonneg=True)
                    self.par['weight_delta'] = cvxpy.Parameter(nonneg=True)
                    self.par['weight_delta_sigma'] = cvxpy.Parameter(nonneg=True)
                    self.par['weight_nu'] = cvxpy.Parameter(nonneg=True)

                    # Constraints:
                    constraints = []

                    # Model:
                    constraints += m.get_constraints(
                        self.var['X'], self.var['U'], self.par['X_last'], self.par['U_last'])

                    # Dynamics:
                    # x_t+1 = A_*x_t+B_*U_t+C_*U_T+1*S_*sigma+zbar+nu
                    constraints += [
                        self.var['X'][:, k + 1] ==
                        cvxpy.reshape(self.par['A_bar'][:, k], (m.n_x, m.n_x)) *
                        self.var['X'][:, k] +
                        cvxpy.reshape(self.par['B_bar'][:, k], (m.n_x, m.n_u)) *
                        self.var['U'][:, k] +
                        cvxpy.reshape(self.par['C_bar'][:, k], (m.n_x, m.n_u)) *
                        self.var['U'][:, k + 1] +
                        self.par['S_bar'][:, k] * self.var['sigma'] +
                        self.par['z_bar'][:, k] +
                        self.var['nu'][:, k]
                        for k in range(K - 1)
                    ]

                    # Trust regions:
                    dx = cvxpy.sum(cvxpy.square(
                        self.var['X'] - self.par['X_last']), axis=0)
                    du = cvxpy.sum(cvxpy.square(
                        self.var['U'] - self.par['U_last']), axis=0)
                    ds = self.var['sigma'] - self.par['sigma_last']
                    constraints += [cvxpy.norm(dx + du, 1) <= self.var['delta_norm']]
                    constraints += [cvxpy.norm(ds, 'inf') <= self.var['sigma_norm']]

                    # Flight time positive:
                    constraints += [self.var['sigma'] >= 0.1]

                    # Objective:
                    sc_objective = cvxpy.Minimize(
                        self.par['weight_sigma'] * self.var['sigma'] +
                        self.par['weight_nu'] * cvxpy.norm(self.var['nu'], 'inf') +
                        self.par['weight_delta'] * self.var['delta_norm'] +
                        self.par['weight_delta_sigma'] * self.var['sigma_norm']
                    )

                    objective = sc_objective

                    self.prob = cvxpy.Problem(objective, constraints)

                def set_parameters(self, **kwargs):
                    """
                    All parameters have to be filled before calling solve().
                    Takes the following arguments as keywords:
                    A_bar
                    B_bar
                    C_bar
                    S_bar
                    z_bar
                    X_last
                    U_last
                    sigma_last
                    E
                    weight_sigma
                    weight_nu
                    radius_trust_region
                    """

                    for key in kwargs:
                        if key in self.par:
                            self.par[key].value = kwargs[key]
                        else:
                            print(f'Parameter \'{key}\' does not exist.')

                def get_variable(self, name):
                    if name in self.var:
                        return self.var[name].value
                    else:
                        print(f'Variable \'{name}\' does not exist.')
                        return None

                def solve(self, **kwargs):
                    error = False
                    try:
                        self.prob.solve(verbose=verbose_solver,
                                        solver=solver)
                    except cvxpy.SolverError:
                        error = True

                    stats = self.prob.solver_stats

                    info = {
                        'setup_time': stats.setup_time,
                        'solver_time': stats.solve_time,
                        'iterations': stats.num_iters,
                        'solver_error': error
                    }

                    return info

            def axis3d_equal(X, Y, Z, ax):

                max_range = np.array([X.max() - X.min(), Y.max()
                                      - Y.min(), Z.max() - Z.min()]).max()
                Xb = 0.5 * max_range * np.mgrid[-1:2:2, -1:2:2,
                                       - 1:2:2][0].flatten() + 0.5 * (X.max() + X.min())
                Yb = 0.5 * max_range * np.mgrid[-1:2:2, -1:2:2,
                                       - 1:2:2][1].flatten() + 0.5 * (Y.max() + Y.min())
                Zb = 0.5 * max_range * np.mgrid[-1:2:2, -1:2:2,
                                       - 1:2:2][2].flatten() + 0.5 * (Z.max() + Z.min())
                # Comment or uncomment following both lines to test the fake bounding box:
                for xb, yb, zb in zip(Xb, Yb, Zb):
                    ax.plot([xb], [yb], [zb], 'w')

            def plot_animation(X, U):  # pragma: no cover

                fig = plt.figure()
                ax = fig.gca(projection='3d')
                # for stopping simulation with the esc key.
                fig.canvas.mpl_connect('key_release_event',
                                       lambda event: [exit(0) if event.key == 'escape' else None])

                for k in range(K):
                    plt.cla()
                    ax.plot(X[2, :], X[3, :], X[1, :])  # trajectory
                    ax.scatter3D([0.0], [0.0], [0.0], c="r",
                                 marker="x")  # target landing point
                    axis3d_equal(X[2, :], X[3, :], X[1, :], ax)

                    rx, ry, rz = X[1:4, k]
                    # vx, vy, vz = X[4:7, k]
                    qw, qx, qy, qz = X[7:11, k]

                    CBI = np.array([
                        [1 - 2 * (qy ** 2 + qz ** 2), 2 * (qx * qy + qw * qz),
                         2 * (qx * qz - qw * qy)],
                        [2 * (qx * qy - qw * qz), 1 - 2
                         * (qx ** 2 + qz ** 2), 2 * (qy * qz + qw * qx)],
                        [2 * (qx * qz + qw * qy), 2 * (qy * qz - qw * qx),
                         1 - 2 * (qx ** 2 + qy ** 2)]
                    ])

                    Fx, Fy, Fz = np.dot(np.transpose(CBI), U[:, k])
                    dx, dy, dz = np.dot(np.transpose(CBI), np.array([1., 0., 0.]))

                    # attitude vector
                    ax.quiver(ry, rz, rx, dy, dz, dx, length=0.5, linewidth=3.0,
                              arrow_length_ratio=0.0, color='black')

                    # thrust vector
                    ax.quiver(ry, rz, rx, -Fy, -Fz, -Fx, length=0.1,
                              arrow_length_ratio=0.0, color='red')

                    ax.set_title("Rocket powered landing")
                    plt.pause(0.5)

            def main():
                print("start!!")
                m = Rocket_Model_6DoF()

                # state and input list
                X = np.empty(shape=[m.n_x, K])
                U = np.empty(shape=[m.n_u, K])

                # INITIALIZATION
                sigma = m.t_f_guess
                X, U = m.initialize_trajectory(X, U)

                integrator = Integrator(m, K)
                problem = SCProblem(m, K)

                converged = False
                w_delta = W_DELTA
                for it in range(iterations):
                    t0_it = time()
                    print('-' * 18 + f' Iteration {str(it + 1).zfill(2)} ' + '-' * 18)

                    A_bar, B_bar, C_bar, S_bar, z_bar = integrator.calculate_discretization(
                        X, U, sigma)

                    problem.set_parameters(A_bar=A_bar, B_bar=B_bar, C_bar=C_bar, S_bar=S_bar, z_bar=z_bar,
                                           X_last=X, U_last=U, sigma_last=sigma,
                                           weight_sigma=W_SIGMA, weight_nu=W_NU,
                                           weight_delta=w_delta, weight_delta_sigma=W_DELTA_SIGMA)
                    problem.solve()

                    X = problem.get_variable('X')
                    U = problem.get_variable('U')
                    sigma = problem.get_variable('sigma')

                    delta_norm = problem.get_variable('delta_norm')
                    sigma_norm = problem.get_variable('sigma_norm')
                    nu_norm = np.linalg.norm(problem.get_variable('nu'), np.inf)

                    if delta_norm < 1e-3 and sigma_norm < 1e-3 and nu_norm < 1e-7:
                        converged = True

                    w_delta *= 1.5

                    if converged:
                        print(f'Converged after {it + 1} iterations.')
                        break

                if show_animation:  # pragma: no cover
                    plot_animation(X, U)

                print("done!!")
        if event == "-PORK-":
            window.close()
            Departure = "Earth"
            targetBody = "Jupiter"
            with open(SCDesignerPath+ "\\DepartureDest.csv", "w+") as f:
                f.write(Departure + "," + targetBody)
            f.close()
            # For some reason does not like running the porkchop function as part of freecad... should investigate...
            os.startfile(SCDesignerPath + "\\PorkchopPlotFreeCAD\\PorkchopPlotFreeCAD.exe")

            import subprocess
            import time
            def process_exists(process_name):
                call = 'TASKLIST', '/FI', 'imagename eq %s' % process_name
                output = subprocess.check_output(call).decode()
                last_line = output.strip().split('\r\n')[-1]
                return last_line.lower().startswith(process_name.lower())

            while process_exists("PorkchopPlotFreeCAD.exe") == True:
                time.sleep(1)

            import io
            import os
            import FreeSimpleGUI as sg
            from PIL import Image
            filename = SCDesignerPath + "\\PORKCHOP.png"
            image = Image.open(filename)
            image.thumbnail((700, 700))
            bio = io.BytesIO()
            image.save(bio, format="PNG")
            layout = [
                [sg.Image(data=bio.getvalue(),key="-IMAGE-")],
                [sg.Button("Done")]]
            window = sg.Window("Image Viewer", layout)
            # while True:
            event, values = window.read()
            if event == "Done" or event == sg.WIN_CLOSED:
                window.close()
            #     if event == "Load Image":
            #         filename = SCDesignerPath + "\\PORKCHOP.png"
            #         if os.path.exists(filename):
            #             image = Image.open(filename)
            #             image.thumbnail((700, 700))
            #             bio = io.BytesIO()
            #             image.save(bio, format="PNG")
            #             window["-IMAGE-"].update(data=bio.getvalue())
            #

        if event == "LDG":
            pass
        if event == "-SURF-":
            pass
        if event == "-ROBO-":
            pass
        if event == "-CONTROLLER-":


            # import FreeSimpleGUIWeb as sg
            # import FreeSimpleGUIQt as sg
            import FreeSimpleGUI as sg
            import math
            import numpy as np
            from scipy.integrate import odeint

            # specify number of steps
            ns = 300
            # define time points
            t = np.linspace(0, ns / 10, ns + 1)

            SIZE_T = len(t)
            print(len(t))
            SIZE_Y = 50
            NUMBER_MARKER_FREQUENCY = 10

            def process(y, t, u, Kp, taup):
                # Kp = process gain
                # taup = process time constant
                dydt = -y / taup + Kp / taup * u
                return dydt

            def draw_axis(max_pv):
                graph.draw_line((0, 0), (SIZE_T, 0))  # axis lines
                graph.draw_line((0, -max_pv), (0, max_pv))

                for x in range(0, SIZE_T + 1, NUMBER_MARKER_FREQUENCY):
                    graph.draw_line((x, -max_pv / 30), (x, max_pv / 30))  # tick marks
                    if x != 0:
                        graph.draw_text(str(x), (x, -10))  # numeric labels
                # print(type(round(max_pv)))
                for y in range(-round(max_pv), round(max_pv * 1.25), round(max_pv / 10)):
                    graph.draw_line((1, y), (1, y))
                    if y != 0:
                        graph.draw_text(str(y), (len(t) / 70, y), color='blue')

            pv = [10]
            # Create the graph that will be put into the window
            graph = sg.Graph(canvas_size=(800, 300),
                             graph_bottom_left=(0, -(pv[0] + 5)),
                             graph_top_right=(SIZE_T + 5, pv[0] + 5),
                             background_color='white',
                             key='graph')
            # Window layout
            ControllerList = []
            Header = ['Name','Controller Type','Component', 'Equation']
            layout = [[graph],
                      [sg.Text('Add '), sg.InputCombo(('Proportional Integral', 'Proportional Derivative',
                                             'Proportional Integral Derivative', 'Linear Quadratic Regulator','Model Predictive',
                                             'Bang-bang','Reinforcement Learning')), sg.Text(" Controller to "), sg.InputCombo(('Actuator 1', 'Actuator 2')), sg.Text(' using '), sg.InputCombo(('Sensor 1', 'Sensor 2'))],
                      [sg.Text('')],
                      [sg.Text('Initial Condition'), sg.InputText('', size=(5,1))],
                      [sg.Text('Desired State (Set Point)'), sg.InputText('', size=(5,1))],
                      [sg.Text('System Equation, if Known'), sg.Text('Identify System Behavior Using SINDY Test Case'), sg.Button('OK')],
                      [sg.Text('Update System Values')],
                      [sg.Text('Tau P'), sg.InputText('1', key='_SLIDER_', size=(5, 1))],
                      [sg.Text('Tau I'), sg.InputText('1', key='_SLIDER1_', size=(5,1))],
                      [sg.Text('Tau D'), sg.InputText('1', key='_SLIDER2_',size=(5,1))],
                      [sg.Text('Show Pole Zero Map'), sg.Button('OK', key='-PZMAP-')],
                      [sg.Text('Show Bode Plot'), sg.Button('OK', key='-BODE-')],
                      [sg.Button("Save This Controller", key="-UPDATE-")],
                      [sg.Table(ControllerList, headings=Header, key='Table', auto_size_columns=True)],
                      [sg.Submit(), sg.Cancel()]]




            window = sg.Window('Control Systems Designer', layout)
            prev_t = prev_pv = prev_sp = None
            # pv = 10

            while True:
                event, values = window.read()
                print(values)
                if event == "Cancel":
                    window.close()
                    pass

                if event == '-BODE-':
                    from sympy.abc import s
                    from sympy.physics.control.lti import TransferFunction
                    from sympy.physics.control.control_plots import bode_plot
                    tf1 = TransferFunction(1 * s ** 2 + 0.1 * s + 7.5, 1 * s ** 4 + 0.12 * s ** 3 + 9 * s ** 2, s)
                    bode_plot(tf1, initial_exp=0.2, final_exp=0.7)
                if event == '-PZMAP-':
                    from sympy.abc import s
                    from sympy.physics.control.lti import TransferFunction
                    from sympy.physics.control.control_plots import pole_zero_plot
                    tf1 = TransferFunction(s ** 2 + 1, s ** 4 + 4 * s ** 3 + 6 * s ** 2 + 5 * s + 2, s)
                    pole_zero_plot(tf1)
                if event == "-UPDATE-":
                    ControllerList.append(
                        [values[0], values[0]])
                    window['Table'].update(ControllerList)

                if event is None:
                    break
                graph.erase()
                draw_axis(max(pv))

                # process model
                Kp = 3.0
                taup = 5.0

                delta_t = t[1] - t[0]

                # storage for recording values
                op = np.zeros(ns + 1)  # controller output
                pv = np.zeros(ns + 1)  # process variable
                e = np.zeros(ns + 1)  # error
                ie = np.zeros(ns + 1)  # integral of the error
                dpv = np.zeros(ns + 1)  # derivative of the pv
                P = np.zeros(ns + 1)  # proportional
                I = np.zeros(ns + 1)  # integral
                D = np.zeros(ns + 1)  # derivative
                sp = np.zeros(ns + 1)  # set point
                sp[25:] = 10

                # PID (starting point)
                Kc = 1.0 / Kp
                tauI = taup
                tauD = 0.0

                # PID (tuning)
                Kc = Kc * 2
                tauI = float(values['_SLIDER_'])  # tauI / 2
                tauD = float(values['_SLIDER2_'])

                # Upper and Lower limits on OP
                op_hi = 10.0
                op_lo = 0.0

                # loop through time steps
                for i in range(0, ns):
                    e[i] = sp[i] - pv[i]
                    if i >= 1:  # calculate starting on second cycle
                        dpv[i] = (pv[i] - pv[i - 1]) / delta_t
                        ie[i] = ie[i - 1] + e[i] * delta_t
                    P[i] = Kc * e[i]
                    I[i] = Kc / tauI * ie[i]
                    D[i] = - Kc * tauD * dpv[i]
                    op[i] = op[0] + P[i] + I[i] + D[i]
                    if op[i] > op_hi:  # check upper limit
                        op[i] = op_hi
                        ie[i] = ie[i] - e[i] * delta_t  # anti-reset windup
                    if op[i] < op_lo:  # check lower limit
                        op[i] = op_lo
                        ie[i] = ie[i] - e[i] * delta_t  # anti-reset windup
                    y = odeint(process, pv[i], [0, delta_t], args=(op[i], Kp, taup))
                    pv[i + 1] = y[-1]
                op[ns] = op[ns - 1]
                ie[ns] = ie[ns - 1]
                P[ns] = P[ns - 1]
                I[ns] = I[ns - 1]
                D[ns] = D[ns - 1]

                for t_i in range(0, len(t)):
                    if prev_t is not None:
                        graph.draw_line((prev_t, prev_sp), (t_i, sp[t_i]), width=2)
                        graph.draw_line((prev_t, prev_pv), (t_i, pv[t_i]), color='red', width=4)
                    prev_t, prev_pv, prev_sp = t_i, pv[t_i], sp[t_i]




        window.close()
        if event == "Quit":
            window.close()
        elif event == "Ok":
            window.close()
        elif event == "-STABILIZATION-":
            # What is the ground target?
            # What is the pointing accuracy requirement?
            # What is the sensor error
            # What is the unknown error
            import FreeCAD

            ShapeList = []

            for obj in FreeCAD.ActiveDocument.Objects:
                if hasattr(obj, "Shape"):
                    ShapeList.append(obj.Name)

            # This is not exactly correct I think vv, numparts

            NumParts = len(ShapeList)
            if values[4] == "Spin Stabilization":
                if NumParts == 1:
                    InertiaString = str(App.ActiveDocument.ActiveObject.Shape.MatrixOfInertia)
                    InertiaString = InertiaString[InertiaString.find("("):]
                    InertiaString = re.sub(r'[)(]', '', InertiaString)
                    values = [float(i) for i in InertiaString.split(',')]
                    values = np.array(values)
                    Imatrix = np.reshape(values, (4, 4))
                    Imatrix = np.delete(Imatrix, 3, axis=1)
                    Imatrix = np.delete(Imatrix, 3, axis=0)
                    print("Inertia Matrix: ")
                    print(Imatrix)
                    Ixx = Imatrix[0][0]
                    Iyy = Imatrix[1][1]
                    Izz = Imatrix[2][2]

                    k = (Ixx - Izz) * (Iyy - Izz) / (Ixx * Iyy)  # Howard page 555 with omega_0 removed
                    print("Stability factor k:  " + str(k))
                    if k > 0:
                        print("Stable")
                    else:
                        print("Unstable")

                if NumParts > 1:

                    import os
                    import os.path
                    import FreeCAD
                    import importOBJ
                    import FreeCAD
                    import Draft
                    import Mesh
                    import FreeCADGui as Gui

                    ShapeList = []

                    for obj in FreeCAD.ActiveDocument.Objects:
                        if hasattr(obj, "Shape"):
                            ShapeList.append(obj.Name)

                    # Gui.runCommand('a2p_Show_Hierarchy_Command',0)

                    # uniqueshapelist = []
                    # for shape in ShapeList:
                    #	shapemod = shape[2:]
                    #	modstop = shapemod.find("_")
                    #	shapemod = shapemod[:modstop]
                    #	uniqueshapelist.append(shapemod)
                    #
                    # uniqueshapelist = sorted(set(uniqueshapelist))

                    if os.path.isdir(SCDesignerPath + "\\" +
                            str(
                                    App.ActiveDocument.Label)):
                        pass
                    else:
                        os.mkdir(SCDesignerPath + "\\" + str(
                            App.ActiveDocument.Label))

                    # print(ShapeList)

                    for shape in ShapeList:
                        Draft.clone(FreeCAD.ActiveDocument.getObject(shape))
                        shapemod = shape[2:]
                        modstop = shapemod.find("_")
                        shapemod = shapemod[:modstop]
                        FreeCAD.getDocument(App.ActiveDocument.Label).getObject("Clone").Scale = (
                        0.1000, 0.1000, 0.1000)
                        ActiveDocName = str(App.ActiveDocument.Label)
                        MeshExportName = "C:/Users/" + username + "/AppData/Roaming/FreeCAD/Mod/SpacecraftDesigner/" + str(
                            App.ActiveDocument.Label) + "/" + shapemod + ".obj"
                        App.getDocument(App.ActiveDocument.Label).recompute()
                        __objs__ = []
                        __objs__.append(FreeCAD.getDocument(App.ActiveDocument.Label).getObject("Clone"))
                        Mesh.export(__objs__, MeshExportName)
                        del __objs__
                        App.getDocument(App.ActiveDocument.Label).removeObject('Clone')
                        App.getDocument(App.ActiveDocument.Label).recompute()
                        m = App.ActiveDocument.getObject(shape).Shape.MatrixOfInertia
                        v = App.ActiveDocument.getObject(
                            shape).Shape.Volume / 1000000000  # Convert volume from mm^3 to m^3
                        p = FreeCAD.ActiveDocument.getObject(shape).Placement.Base
                        ypr = str(FreeCAD.ActiveDocument.getObject(shape).Placement)
                        startloc = ypr.find("Roll=")
                        ypr = ypr[startloc + 6:-2]
                        ypr = ypr.split(",")
                        if os.path.exists(
                                SCDesignerPath + "\\" + str(
                                        App.ActiveDocument.Label) + "\\" + str(
                                        App.ActiveDocument.Label) + "Inertia.csv"):
                            with open(
                                    SCDesignerPath + "\\" + str(
                                            App.ActiveDocument.Label) + "\\" + str(
                                            App.ActiveDocument.Label) + "Inertia.csv", 'a') as f:
                                f.write("\n")
                                f.write(str(shapemod) + ",")
                                for i in range(4):
                                    for j in range(4):
                                        f.write(str(m.A[i * 4 + j]) + ",")
                                f.write(str(v) + ",")
                                for i in range(3):
                                    f.write(str(p[i]) + ",")
                                f.write(ypr[2] + ",")
                                f.write(ypr[1] + ",")
                                f.write(ypr[0] + ",")
                                f.close()
                        else:

                            with open(
                                    SCDesignerPath + "\\" + str(
                                            App.ActiveDocument.Label) + "\\" + str(
                                            App.ActiveDocument.Label) + "Inertia.csv", 'w') as f:
                                f.write(
                                    "NAME,IXX,IXY,IXZ,IX0,IYX,IYY,IYZ,IY0,IZX,IZY,IZZ,IZ0,I0X,I0Y,I0Z,I00,VOL,X,Y,Z,R,P,Y\n")
                                f.write(str(shapemod) + ",")
                                for i in range(4):
                                    for j in range(4):
                                        f.write(str(m.A[i * 4 + j]) + ",")
                                f.write(str(v) + ",")
                                for i in range(3):
                                    f.write(str(p[i]) + ",")
                                f.write(ypr[2] + ",")
                                f.write(ypr[1] + ",")
                                f.write(ypr[0] + ",")
                                f.close()
                    Gui.activateWorkbench("A2plusWorkbench")
                    Gui.runCommand('a2p_Show_Hierarchy_Command', 0)

                    mass = CalculateAsmMass()
                    # global new_vehicle
                    new_vehicle.mass = mass
                    print(mass)
                    launchvehiclelist = ParkingOrbitAlgorithm(mass, 800, 45)



        elif event == "-INERTIA-":
            InertiaString = str(App.ActiveDocument.ActiveObject.Shape.MatrixOfInertia)
            InertiaString = InertiaString[InertiaString.find("("):]
            InertiaString = re.sub(r'[)(]', '', InertiaString)
            values = [float(i) for i in InertiaString.split(',')]
            values = np.array(values)
            Imatrix = np.reshape(values, (4,4))
            Imatrix = np.delete(Imatrix,3, axis=1)
            Imatrix = np.delete(Imatrix,3, axis=0)
            print(Imatrix)
            Ixx = Imatrix[0][0]
            Iyy = Imatrix[1][1]
            Izz = Imatrix[2][2]

            k = (Ixx-Izz)*(Iyy-Izz)/(Ixx*Iyy) # Howard page 555 with omega_0 removed
            print("Stability factor k:" + str(k))
            if k > 0:
                print("Stable")
            else:
                print("Unstable")
        return

class Propulsion():

    def GetResources(self):
        return {'Pixmap'  : 'C:\\Users\\' + username + '\\AppData\\Roaming\\FreeCAD\\Mod\\SpacecraftDesigner\\Icons\\Propulsion.jpg',
                'Accel' : "Shift+P", # a default shortcut (optional)
                'MenuText': "Propulsion",
                'ToolTip' : "Define Spacecraft Propulsion System"}

    def Activated(self):
        # from openpyxl import Workbook
        # import openpyxl


        import FreeSimpleGUI as sg

        SCDesignerPath = "C:\\Users\\" + username + "\\AppData\\Roaming\\FreeCAD\\Mod\\SpacecraftDesigner"
        # file = SCDesignerPath + "\\Component_lists.xlsx"
        # wb = openpyxl.load_workbook(file)
        # ws = wb["Engines"]
        EngineList = []
        # for cell in ws['A']:
        #     EngineList.append(cell.value)

        from PIL import Image, ImageDraw
        import random
        im = Image.new('RGB', (1000, 100), (255, 255, 255))
        draw = ImageDraw.Draw(im)

        deltaVList = [1700, 400, 500, 600, 100]
        deltaVnames = ['Earth Escape', 'Circularization Burn', 'Geostationary Orbit Injection',
                       'Trajectory Correction Maneuvers', 'Planetary Injection Burn']
        totalDeltaV = sum(deltaVList)

        startloc = 0
        i = 0
        for deltaVnum in deltaVList:
            endloc = startloc + (deltaVnum * 1000 / totalDeltaV)
            draw.rectangle((startloc, 0, endloc, 100),
                           fill=(random.randrange(1, 255, 1), random.randrange(1, 255, 1), random.randrange(1, 255, 1)))
            half = int(endloc - startloc) / 2
            middle = startloc + half
            draw.text((middle, 50), deltaVnames[i], fill=(0, 0, 0))
            startloc = endloc
            i += 1
        im.save(SCDesignerPath + "\\DeltaVBreakdown.jpg", quality=95)

        import io
        import FreeSimpleGUI as sg
        from PIL import Image
        import time
        filename = SCDesignerPath + "\\DeltaVBreakdown.jpg"
        image = Image.open(filename)
        image.thumbnail((1000, 10000))
        bio = io.BytesIO()
        image.save(bio, format="PNG")


































        counter = 0
        Header = ["Stage Number","Applicable Burns", "Delta-V Req","ISP", "Propellant Mass","Structural Mass", "Num Engines","Engine Type", "Maximum Thrust"]

        StageList = []
        layout = [[sg.Text('Delta-V Breakdown')],
                  [sg.Image(data=bio.getvalue(), key="-IMAGE-")],
                  [sg.Text('')],
                  [sg.Text('Add Stage'), sg.InputCombo(['Liquid Rocket Engine', 'Solid Rocket Engine', 'Hybrid Rocket Engine','Ion Propulsion System', 'Nuclear Propulsion System', 'Hall-Effect Thruster'], key="-Engine Type-"), sg.Text("Number of Engines", size=(15, 1)), sg.InputText("", key="-Number of Engines-",size=(10, 1)), sg.Text("Select Burn"), sg.InputCombo(deltaVnames, key="-DELTAVSEL-"), sg.Button("OK", key='-STAGE-')],# .Button('Liquid Rocket Engine', key="-LIQUID-"), sg.Button('Solid Rocket Engine', key="-SOLID-"), sg.Button('Hybrid Rocket Engine'),sg.Button('Ion Propulsion System'),sg.Button('Nuclear Propulsion System'),sg.Button('Hall-Effect Thruster')],
                  [sg.Table(StageList, headings=Header, auto_size_columns=True, key='Table')],
                  [sg.Cancel()]]# [sg.Text('Select Existing Propulsion System'), sg.InputCombo(("Placeholder", "Placeholder2"), size=(30, 1)), # EngineList Here
                  #  sg.Button('Existing Prop System')]]
                  # [sg.Text('Add Turbopump'), sg.Button("OK", key="-TURBOPUMP-")],
                  # [sg.Text('Add Pressure Vessel'), sg.InputCombo(("Cylindrical", "Spherical", "Integrated Cylindrical Tank"), size=(30, 1)), sg.Text('To',size=(20,1)), sg.InputCombo(EngineList, size=(20,1)), sg.Button('OK', key="-PRESSURE-")],
                  # [sg.Text('Define Outlet Flange'), sg.Button('OK', key="-OUTLET-")],
                  # [sg.Text('Define Inlet Flange'), sg.Button('OK', key="-INLET-")],
                  # [sg.Text('Add Pipe'), sg.Button('OK', key="-PIPE-")],
                  # [sg.Text('Add O-ring'), sg.Button('OK', key="O-ring")]]
        window = sg.Window('Propulsion', layout, default_element_size=(55, 1), grab_anywhere=False, finalize=True)
        try:
            mass = CalculateAsmMass()
        except:
            print("\nPlease create your payload first before selecting a propulsion system\n")
        while True:
            event, values = window.read()

            if event == "Cancel":
                window.close()
                break
            if event == '-STAGE-':
                if values["-Engine Type-"] == "Liquid Rocket Engine":
                    layout = [
                        [sg.Text('Select Fuel'),
                         sg.InputCombo(('Liquid Hydrogen', 'Liquid Methane', 'Liquid Kerosene'))],
                        [sg.Text('Select Oxidizer'), sg.InputCombo(('Liquid Oxygen', ''))],
                        [sg.Text('Set Oxidizer/Fuel (Mixture) Ratio'), sg.InputText(size=(10, 8)),
                         sg.Checkbox('Optimize to Max Specific Impulse', default=True)],
                        [sg.Text('Set Chamber Pressure (pascals)'), sg.InputText(size=(10, 8))],
                        [sg.Text('Set Altitude (meters)'), sg.InputText(size=(10, 8))],
                        [sg.Text('Set Expansion Ratio (5<Ar<50)'), sg.InputText(size=(10, 8))],
                        [sg.Text('Set Throat Diameter', key="-THROATDIA-"), sg.InputText(size=(10, 8))],
                        [sg.Text('Set Exit Diameter', key="-EXITDIA-"), sg.InputText(size=(10, 8))],
                        [sg.Button('OK'), sg.Cancel()]]
                    window = sg.Window('Define Prop System', layout, default_element_size=(55, 1), grab_anywhere=False)

                    event, values = window.read()

                    if event == "Cancel":
                        window.close()
                        pass
                    else:
                        # window.close()
                        from pygasflow.nozzles import CD_TOP_Nozzle, CD_Conical_Nozzle, CD_Min_Length_Nozzle
                        from pygasflow.utils import Ideal_Gas, Flow_State
                        from pygasflow.solvers import De_Laval_Solver
                        import numpy as np
                        import math
                        import matplotlib.pyplot as plt
                        import matplotlib.patches as patches

                        # Initialize air as the gas to use in the nozzle
                        gas = Ideal_Gas(287, 1.4)

                        Fuel = values[0]
                        Oxidizer = values[1]
                        OFRatio = float(values[2])

                        if Fuel == "Liquid Hydrogen" and Oxidizer == "Liquid Oxygen":
                            t0 = 3552.778  # Kelvin
                            MolMass = 10
                            v_etheoretical = 4425.696  # Meters/sec
                            FuelDens = 71
                            OxDens = 1142
                        elif Fuel == 'Liquid Kerosene' and Oxidizer == "Liquid Oxygen":
                            t0 = 3672.222  # Kelvin
                            MolMass = 23.3
                            v_etheoretical = 3465.576  # Meters/sec
                            FuelDens = 810
                            OxDens = 1142
                        elif Fuel == "MMH" and Oxidizer == "N2O4":
                            t0 = 3388.889  # Kelvin
                            MolMass = 21.5
                            v_etheoretical = 3297.936  # Meters/sec
                            FuelDens = 878
                            OxDens = 1440
                        elif Fuel == "N2H4":
                            t0 = 1227.778  # Kelvin
                            MolMass = 13
                            v_etheoretical = 2325.624  # Meters/sec
                            FuelDens = 1010
                        elif Fuel == "He":
                            t0 = 288.889
                            MolMass = 4
                            v_etheoretical = 1551.432  # Meters/sec
                        elif Fuel == "N2":
                            t0 = 288.889
                            MolMass = 28
                            v_etheoretical = 667.512  # Meters/sec

                        # sqrttcdivm = math.sqrt(t0 / MolMass)

                        p0 = float(values[4])  # stagnation condition
                        h = float(values[5])  # meters
                        expratio = float(values[6])

                        Ri = 0.4
                        Ai = math.pi * (Ri ** 2)
                        Rt = 0.2
                        At = math.pi * (Rt ** 2)
                        Ae = At * expratio
                        Re = math.sqrt((Ae / math.pi))

                        # How do you optimize for altitude?

                        # for alt in range(0, 110):
                        #     h = alt*1000
                        #     # h is meters alt

                        upstream_state = Flow_State(p0=p0, t0=t0)

                        from ambiance import Atmosphere

                        sealevel = Atmosphere(h)
                        Tinf = sealevel.temperature
                        Pinf = sealevel.pressure
                        d = sealevel.density
                        a = sealevel.speed_of_sound
                        mu = sealevel.dynamic_viscosity  # Verify that mu is in fact dynamic and not kinematic viscosity
                        # Tinf, Pinf, d, a, mu = isa.calculate_at_h(h, atmosphere)

                        Pb_P0_ratio = Pinf / p0

                        # half cone angle of the divergent
                        theta_c = 40
                        # half cone angle of the convergent
                        theta_N = 15

                        # Junction radius between the convergent and divergent
                        Rbt = 0.75 * Rt
                        # Junction radius between the "combustion chamber" and convergent
                        Rbc = 1.5 * Rt
                        # Fractional Length of the TOP nozzle with respect to a same exit
                        # area ratio conical nozzle with 15 deg half-cone angle.
                        K = 0.8
                        # geometry type
                        geom = "axisymmetric"

                        geom_con = CD_Conical_Nozzle(
                            Ri,  # Inlet radius
                            Re,  # Exit (outlet) radius
                            Rt,  # Throat radius
                            Rbt,  # Junction radius ratio at the throat (between the convergent and divergent)
                            Rbc,  # Junction radius ratio between the "combustion chamber" and convergent
                            theta_c,  # Half angle [degrees] of the convergent.
                            theta_N,  # Half angle [degrees] of the conical divergent.
                            geom,  # Geometry type
                            1000  # Number of discretization points along the total length of the nozzle
                        )

                        geom_top = CD_TOP_Nozzle(
                            Ri,  # Inlet radius
                            Re,  # Exit (outlet) radius
                            Rt,  # Throat radius
                            Rbc,  # Junction radius ratio between the "combustion chamber" and convergent
                            theta_c,  # Half angle [degrees] of the convergent.
                            K,  # Fractional Length of the nozzle
                            geom,  # Geometry type
                            1000  # Number of discretization points along the total length of the nozzle
                        )

                        n = 15
                        gamma = gas.gamma

                        geom_moc = CD_Min_Length_Nozzle(
                            Ri,  # Inlet radius
                            Re,  # Exit (outlet) radius
                            Rt,  # Throat radius
                            Rbt,  # Junction radius ratio at the throat (between the convergent and divergent)
                            Rbc,  # Junction radius ratio between the "combustion chamber" and convergent
                            theta_c,  # Half angle [degrees] of the convergent.
                            n,  # number of characteristics lines
                            gamma  # Specific heat ratio
                        )

                        # Initialize the nozzle
                        nozzle_conical = De_Laval_Solver(gas, geom_con, upstream_state)
                        nozzle_top = De_Laval_Solver(gas, geom_top, upstream_state)
                        nozzle_moc = De_Laval_Solver(gas, geom_moc, upstream_state)
                        # print(nozzle_conical)
                        NozzleChars = str(nozzle_conical)
                        NozzleChars = NozzleChars.replace("\n", "")
                        # NozzleChars = NozzleChars.replace("\t", "")

                        NozzleChars = NozzleChars.split(":")

                        for item in NozzleChars:
                            if item.find("T*") > 0:
                                item = item.replace("Important Pressure Ratios", "")
                                criticalquantities = item.split("\t")
                                criticalquantities = criticalquantities[1:]

                            if item.find("r1") > 0:
                                item = item.replace("Flow Condition", "")
                                pressureratios = item.split("\t")
                                pressureratios = pressureratios[1:]

                        Tstar = float(criticalquantities[1])
                        Pstar = float(criticalquantities[3])
                        Rhostar = float(criticalquantities[5])
                        ustar = float(criticalquantities[7])

                        mdot = Rhostar * ustar * At

                        r1 = float(pressureratios[1])
                        r2 = float(pressureratios[3])
                        r3 = float(pressureratios[5])

                        # Assuming perfectly expanded ******
                        print(Pb_P0_ratio)
                        print(gamma)
                        print(MolMass)
                        print(t0)
                        U_e = math.sqrt(
                            ((1 - ((Pb_P0_ratio) ** ((gamma - 1) / gamma))) * 2 * gamma * (8314 / MolMass) * t0) / (
                                        gamma - 1))

                        mdotfuel = mdot / (1 + OFRatio)
                        mdotox = mdot - mdotfuel

                        def Plot_Nozzle(geom, L, A, M, P, rho, T, flow_condition, Asw_At_ratio, title):
                            fig, ax = plt.subplots(nrows=4, sharex=True)
                            fig.set_size_inches(8, 10)
                            radius_nozzle, radius_container = geom.get_points(False)
                            ar_nozzle, ar_container = geom.get_points(True)
                            # nozzle geometry
                            ax[0].add_patch(
                                patches.Polygon(radius_container, facecolor="0.85", hatch="///", edgecolor="0.4",
                                                linewidth=0.5))
                            ax[0].add_patch(
                                patches.Polygon(radius_nozzle, facecolor='#b7e1ff', edgecolor="0.4", linewidth=1))
                            ax[0].set_ylim(0, max(radius_container[:, 1]))
                            ax[0].set_ylabel("r [m]")
                            ax[0].set_title(title + flow_condition)

                            ax[1].add_patch(
                                patches.Polygon(ar_container, facecolor="0.85", hatch="///", edgecolor="0.4",
                                                linewidth=0.5))
                            ax[1].add_patch(
                                patches.Polygon(ar_nozzle, facecolor='#b7e1ff', edgecolor="0.4", linewidth=1))
                            ax[1].set_ylim(0, max(ar_container[:, 1]))
                            ax[1].set_ylabel("$A/A^{*}$")

                            # draw the shock wave if present in the nozzle
                            if Asw_At_ratio:
                                # get shock wave location in the divergent
                                x = geom.location_divergent_from_area_ratio(Asw_At_ratio)
                                rsw = np.sqrt((Asw_At_ratio * geom.critical_area) / np.pi)
                                ax[0].plot([x, x], [0, rsw], 'r')
                                ax[1].plot([x, x], [0, Asw_At_ratio], 'r')
                                ax[0].text(x, rsw + 0.5 * (max(radius_container[:, 1]) - max(radius_nozzle[:, -1])),
                                           "SW",
                                           color="r",
                                           ha='center',
                                           va="center",
                                           bbox=dict(boxstyle="round", fc="white", lw=0, alpha=0.85),
                                           )
                                ax[1].text(x, Asw_At_ratio + 0.5 * (max(ar_container[:, 1]) - max(ar_nozzle[:, -1])),
                                           "SW",
                                           color="r",
                                           ha='center',
                                           va="center",
                                           bbox=dict(boxstyle="round", fc="white", lw=0, alpha=0.85),
                                           )

                            # mach number
                            ax[2].plot(L, M)
                            ax[2].set_ylim(0)
                            ax[2].grid()
                            ax[2].set_ylabel("M")

                            # ratios
                            ax[3].plot(L, P, label="$P/P_{0}$")
                            ax[3].plot(L, rho, label=r"$\rho/\rho_{0}$")
                            ax[3].plot(L, T, label="$T/T_{0}$")
                            ax[3].set_xlim(min(ar_container[:, 0]), max(ar_container[:, 0]))
                            ax[3].set_ylim(0, 1)
                            ax[3].legend(loc="lower left")
                            ax[3].grid()
                            ax[3].set_xlabel("L [m]")
                            ax[3].set_ylabel("ratios")
                            with open(
                                    SCDesignerPath + "\\RocketNozzlePoints.txt",
                                    "w+") as r:
                                for q in range(0, len(radius_nozzle)):
                                    if radius_nozzle[q][1] < 0:
                                        turnaround = q - 1
                                        break
                                    r.write(str(round(radius_nozzle[q][0], 4)) + "," + str(
                                        round(radius_nozzle[q][1], 4)) + ",0\n")
                                for s in range(turnaround, 0, -1):
                                    r.write(str(round((radius_nozzle[s][0]), 4)) + "," + str(
                                        round(radius_nozzle[s][1] + 0.1, 4)) + ",0\n")
                                r.write(str(round((radius_nozzle[0][0]), 4)) + "," + str(
                                    round(radius_nozzle[0][1], 4)) + ",0\n")
                            r.close()

                            r.close()
                            plt.tight_layout()
                            plt.show()

                        # L1, A1, M1, P1, rho1, T1, flow_condition1, Asw_At_ratio1 = nozzle_conical.compute(Pb_P0_ratio)
                        L2, A2, M2, P2, rho2, T2, flow_condition2, Asw_At_ratio2 = nozzle_top.compute(Pb_P0_ratio)
                        # L3, A3, M3, P3, rho3, T3, flow_condition3, Asw_At_ratio3 = nozzle_moc.compute(Pb_P0_ratio)

                        # Plot_Nozzle(geom_con, L1, A1, M1, P1, rho1, T1, flow_condition1, Asw_At_ratio1, "Conical Nozzle: ")
                        # Plot_Nozzle(geom_moc, L3, A3, M3, P3, rho3, T3, flow_condition3, Asw_At_ratio3, "MOC Nozzle: ")

                        plot = 0
                        title = "TOP Nozzle at " + str(h) + " meters: "
                        Plot_Nozzle(geom_top, L2, A2, M2, P2, rho2, T2, flow_condition2, Asw_At_ratio2, title)

                    # PID DESIGNER

                    # def addComp(Component, g, location):
                    #     with open(SCDesignerPath + "\\PROPULSION\\P_ID\\" + Component + ".png", "rb") as image:
                    #         f = image.read()
                    #         data = bytearray(f)
                    #     data = bytes(data)
                    #     g.draw_image(data=data, location=location)
                    #
                    # def connect(Upstream, Downstream, upstreamloc, downstreamloc, g, allines, color):
                    #     if Upstream == "CylTank":
                    #         upstreamoffset = [18, 160]
                    #     if Upstream == "RegenEngine":
                    #         upstreamoffset = [43, 26]
                    #     if Upstream == "Preburner":
                    #         upstreamoffset = [17, 3]
                    #     if Upstream == "PumpL":
                    #         upstreamoffset = [15, 72]
                    #     if Upstream == "PumpR":
                    #         upstreamoffset = [5, 72]
                    #     if Upstream == "Turbine":
                    #         upstreamoffset = [0, 40]
                    #     if Downstream == "Preburner":
                    #         downstreamoffset = [33, 39]
                    #     if Downstream == "PumpL":
                    #         downstreamoffset = [0, 35]
                    #     if Downstream == "PumpR":
                    #         downstreamoffset = [20, 35]
                    #     if Downstream == "RegenEngine":
                    #         downstreamoffset = [12, 26]
                    #     if Downstream == "Turbine":
                    #         downstreamoffset = [12, 64]
                    #     if Downstream == "Engine":
                    #         downstreamoffset = [25, 7]
                    #     upstreamoutlet = [upstreamoffset[0] + upstreamloc[0], upstreamoffset[1] + upstreamloc[1]]
                    #     downstreaminlet = [downstreamoffset[0] + downstreamloc[0], downstreamoffset[1] + downstreamloc[1]]
                    #     allines.append(
                    #         g.DrawLine(tuple(upstreamoutlet), tuple([upstreamoutlet[0], downstreaminlet[1]]), width=3,
                    #                    color=color))
                    #     allines.append(
                    #         g.DrawLine(tuple([upstreamoutlet[0], downstreaminlet[1]]), tuple(downstreaminlet), width=3,
                    #                    color=color))
                    #

                    #
                    # col = [[sg.T('Place Component', enable_events=True)],
                    #        [sg.B('Piping', key='-PIPING-', size=(12, 1), enable_events=True)],
                    #        [sg.B('Valve', key='-VALVE-', button_color=('black', 'white'), size=(12, 1),
                    #              enable_events=True)],
                    #        [sg.B('Tank', key='-TANK-', size=(12, 1), enable_events=True)],
                    #        [sg.B('Pump', key='-PUMP-', button_color=('black', 'white'), size=(12, 1), enable_events=True)],
                    #        [sg.B('Turbine', key='-TURBINE-', size=(12, 1), enable_events=True)],
                    #        [sg.B('Engine', key='-ENGINE-', button_color=('black', 'white'), size=(12, 1),
                    #              enable_events=True)],
                    #        [sg.B('Sensor', key='-SENSOR-', size=(12, 1), enable_events=True)],
                    #        [sg.B('Filter', key='-FILTER-', button_color=('black', 'white'), size=(12, 1),
                    #              enable_events=True)],
                    #        [sg.B('Pres. Reg.', key='-CONTROLLER-', size=(12, 1), enable_events=True)],
                    #        [sg.B('Engine Cycle', key='-CYCLE-', size=(12, 1), enable_events=True)],
                    #        [sg.B('Add Text', key='-ADDT-', button_color=('black', 'white'), size=(12, 1),
                    #              enable_events=True)],
                    #        [sg.B('Clear Sheet', key='-CLEAR-', size=(12, 1), enable_events=True)],
                    #        [sg.B('Erase Object', key='-ERASE-', size=(12, 1), enable_events=True)],
                    #        [sg.B('Move', key='-MOVE-', button_color=('black', 'white'), size=(12, 1), enable_events=True)],
                    #
                    #        ]
                    #
                    # layout = [
                    #     [sg.Graph((1300, 660), (0, 450), (450, 0), key='-GRAPH-',
                    #               change_submits=True, drag_submits=True, background_color="white"), sg.Col(col)],
                    #     [sg.Button('Export to PDF'), sg.Button('Exit')]
                    # ]
                    #
                    # window = sg.Window('Piping and Instrumentation (P&ID) Designer', layout, finalize=True)
                    # g = window['-GRAPH-']  # type: sg.Graph
                    #
                    # xarr = []
                    # yarr = []
                    # eventarr = []
                    # allines = []
                    # dragging = False
                    # piping = 1
                    # erase = 0
                    # start_point = end_point = prior_rect = None
                    # while True:
                    #     event, values = window.read()
                    #     if event is None:
                    #         break  # exit
                    #     eventarr.append(event)
                    #     if event is None:
                    #         break  # exit
                    #     if event == "-GRAPH-":
                    #         x, y = values["-GRAPH-"]
                    #
                    #         xarr.append(x)
                    #         yarr.append(y)
                    #
                    #         if piping == 1 and erase == 0:
                    #             # piping = 1
                    #             if len(xarr) > 1:
                    #                 if abs(xarr[-2] - xarr[-1]) > abs(yarr[-2] - yarr[-1]):
                    #                     line = g.DrawLine((xarr[-2], yarr[-2]), (xarr[-1], yarr[-2]), width=2)
                    #                     yarr[-1] = yarr[-2]
                    #                 else:
                    #                     line = g.DrawLine((xarr[-2], yarr[-2]), (xarr[-2], yarr[-1]), width=2)
                    #                     xarr[-1] = xarr[-2]
                    #
                    #         if piping == 0 and erase == 0:
                    #             if not dragging:
                    #                 start_point = (x, y)
                    #                 dragging = True
                    #                 drag_figures = g.get_figures_at_location((x, y))
                    #                 lastxy = x, y
                    #             else:
                    #                 end_point = (x, y)
                    #             delta_x, delta_y = x - lastxy[0], y - lastxy[1]
                    #             lastxy = x, y
                    #             if None not in (start_point, end_point):
                    #                 for fig in drag_figures:
                    #                     # fig = drag_figures[-1]
                    #                     g.move_figure(fig, delta_x, delta_y)
                    #                     g.update()
                    #
                    #         if piping == 0 and erase == 1:
                    #             drag_figures = g.get_figures_at_location((x, y))
                    #             for figure in drag_figures:
                    #                 g.delete_figure(figure)
                    #
                    #     if event == "-MOVE-":
                    #         piping = 0
                    #     if event == "-PIPING-":
                    #         piping = 1
                    #         erase = 0
                    #     if event == "-ERASE-":
                    #         erase = 1
                    #         piping = 0
                    #     if event == "-VALVE-":
                    #         layout1 = [
                    #             [sg.Listbox(values=(
                    #                 'Angle valve', 'Check valve', 'Diaphragm valve', 'Ball valve', 'Butterfly valve',
                    #                 'Gate valve', 'Plug valve', 'Relief valve', 'Rotary valve', 'Solenoid, 2-way',
                    #                 'Solenoid, 3-way', 'Solenoid, 4-way',
                    #                 'Solenoid, 5-way'), size=(40, 20)),
                    #                 sg.Image(SCDesignerPath + '\\PROPULSION\\P_ID\\Valves\\Images\\Blank.png', size=(1, 1),
                    #                          key='-IMAGE-')],
                    #             [sg.Radio('Fail Open', "RADIO1", default=True, size=(10, 1)),
                    #              sg.Radio('Fail Closed', "RADIO1"),
                    #              sg.Button('Show Valve Image')],
                    #             [sg.Radio('Hand Operated', "RADIO2"), sg.Radio('Hydraulic', "RADIO2"),
                    #              sg.Radio('Pneumatic', "RADIO2"), sg.Radio('Electrically actuated', "RADIO2")],
                    #             [sg.Submit(tooltip='Submit'), sg.Cancel()]]
                    #
                    #         window1 = sg.Window('Select a valve type', layout1, grab_anywhere=False)
                    #         while True:
                    #             action, event1 = window1.read()
                    #             if action == "Show Valve Image":
                    #                 valvetype = event1[0][0]
                    #                 if valvetype == "Angle valve":
                    #                     window1.Element('-IMAGE-').Update(
                    #                         SCDesignerPath + '\\PROPULSION\\P_ID\\Valves\\Images\\Angle.png')
                    #                 elif valvetype == "Check valve":
                    #                     window1.Element('-IMAGE-').Update(
                    #                         SCDesignerPath + '\\PROPULSION\\P_ID\\Valves\\Images\\SwingCheck.png')
                    #                 elif valvetype == "Diaphragm valve":
                    #                     window1.Element('-IMAGE-').Update(
                    #                         SCDesignerPath + '\\PROPULSION\\P_ID\\Valves\\Images\\Diaphragm.png')
                    #                 elif valvetype == "Ball valve":
                    #                     window1.Element('-IMAGE-').Update(
                    #                         SCDesignerPath + '\\PROPULSION\\P_ID\\Valves\\Images\\TrunnionBall.png')
                    #                 elif valvetype == "Butterfly valve":
                    #                     window1.Element('-IMAGE-').Update(
                    #                         SCDesignerPath + '\\PROPULSION\\P_ID\\Valves\\Images\\Butterfly.png')
                    #                 elif valvetype == "Gate valve":
                    #                     window1.Element('-IMAGE-').Update(
                    #                         SCDesignerPath + '\\PROPULSION\\P_ID\\Valves\\Images\\Gate.png')
                    #                 elif valvetype == "Plug valve":
                    #                     window1.Element('-IMAGE-').Update(
                    #                         SCDesignerPath + '\\PROPULSION\\P_ID\\Valves\\Images\\Plug.png')
                    #                 # elif valvetype == "Solenoid 2-way"
                    #
                    #             if action == "Submit":
                    #                 valvetype = event1[0][0]
                    #                 window1.close()
                    #                 if valvetype == "Ball valve":
                    #                     with open(SCDesignerPath + "\\PROPULSION\\P_ID\\Valves\\HandOpGlobe.png",
                    #                               "rb") as image:
                    #                         f = image.read()
                    #                         data = bytearray(f)
                    #                     data = bytes(data)
                    #                     g.draw_image(data=data, location=(25, 25))
                    #             if action == "Cancel":
                    #                 window1.close()
                    #                 break
                    #
                    #     if event == "-TANK-":
                    #         layout1 = [
                    #             [sg.Listbox(values=(
                    #                 'Spherical Tank', 'Cylindrical Tank'),
                    #                 size=(40, 3))],
                    #             [sg.Submit(tooltip='Submit'), sg.Cancel()]]
                    #
                    #         window1 = sg.Window('Tank Type', layout1, grab_anywhere=False)
                    #
                    #         action, event1 = window1.read()
                    #         TankType = event1[0][0]
                    #
                    #         if action == "Submit":
                    #             window1.close()
                    #         if TankType == 'Cylindrical Tank':
                    #             with open(SCDesignerPath + "\\PROPULSION\\P_ID\\TankCylBlue.png", "rb") as image:
                    #                 f = image.read()
                    #                 data = bytearray(f)
                    #             data = bytes(data)
                    #             g.draw_image(data=data, location=(25, 25))
                    #         if TankType == 'Spherical Tank':
                    #             with open(SCDesignerPath + "\\PROPULSION\\P_ID\\TankSpRed.png", "rb") as image:
                    #                 f = image.read()
                    #                 data = bytearray(f)
                    #             data = bytes(data)
                    #             g.draw_image(data=data, location=(25, 25))
                    #
                    #     if event == "-TURBINE-":
                    #         with open(SCDesignerPath + "\\PROPULSION\\P_ID\\Turbine.png", "rb") as image:
                    #             f = image.read()
                    #             data = bytearray(f)
                    #         data = bytes(data)
                    #         g.draw_image(data=data, location=(20, 20))
                    #
                    #     if event == "-PUMP-":
                    #         with open(SCDesignerPath + "\\PROPULSION\\P_ID\\Pump.png", "rb") as image:
                    #             f = image.read()
                    #             data = bytearray(f)
                    #         data = bytes(data)
                    #         g.draw_image(data=data, location=(20, 20))
                    #     if event == "-CLEAR-":
                    #         g.erase()
                    #     if event == "-ENGINE-":
                    #         with open(SCDesignerPath + "\\PROPULSION\\P_ID\\Engine.png", "rb") as image:
                    #             f = image.read()
                    #             data = bytearray(f)
                    #         data = bytes(data)
                    #         g.draw_image(data=data, location=(200, 200))
                    #     if event == "-SENSOR-":
                    #         layout1 = [
                    #             [sg.Listbox(values=(
                    #                 'Accelerometer', 'Flow meter', 'Pressure transducer', 'Thermocouple', 'Load cell'
                    #             ), size=(40, 10)),
                    #                 sg.Image(SCDesignerPath + '\\PROPULSION\\P_ID\\Valves\\Images\\Blank.png', size=(1, 1),
                    #                          key='-IMAGE-')],
                    #             [sg.Radio('Fail Open', "RADIO1", default=True, size=(10, 1)),
                    #              sg.Radio('Fail Closed', "RADIO1"),
                    #              sg.Button('Show Sensor Image')],
                    #             [sg.Submit(tooltip='Submit'), sg.Cancel()]]
                    #
                    #         window1 = sg.Window('Select Sensor Type', layout1, grab_anywhere=False)
                    #         while True:
                    #             action, event1 = window1.read()
                    #             if action == "Show Valve Image":
                    #                 valvetype = event1[0][0]
                    #                 if valvetype == "Angle valve":
                    #                     window1.Element('-IMAGE-').Update(
                    #                         SCDesignerPath + '\\PROPULSION\\P_ID\\Valves\\Images\\Angle.png')
                    #                 # elif valvetype == "Check valve":
                    #
                    #                 elif valvetype == "Diaphragm valve":
                    #                     window1.Element('-IMAGE-').Update(
                    #                         SCDesignerPath + '\\PROPULSION\\P_ID\\Valves\Images\Diaphragm.png')
                    #                 elif valvetype == "Ball valve":
                    #                     window1.Element('-IMAGE-').Update(
                    #                         SCDesignerPath + '\\PROPULSION\\P_ID\\Valves\Images\TrunnionBall.png')
                    #                 elif valvetype == "Butterfly valve":
                    #                     window1.Element('-IMAGE-').Update(
                    #                         SCDesignerPath + '\\PROPULSION\\P_ID\\Valves\Images\Butterfly.png')
                    #                 elif valvetype == "Gate valve":
                    #                     window1.Element('-IMAGE-').Update(
                    #                         SCDesignerPath + '\\PROPULSION\\P_ID\\Valves\Images\Gate.png')
                    #                 # elif valvetype == "Rotary valve":
                    #                 #
                    #                 # elif valvetype == "Solenoid 2-way"
                    #
                    #             if action == "Submit":
                    #                 valvetype = event1[0][0]
                    #                 window1.close()
                    #                 if valvetype == "Ball valve":
                    #                     with open(SCDesignerPath + "\\PROPULSION\\P_ID\\Valves\\HandOpGlobe.png",
                    #                               "rb") as image:
                    #                         f = image.read()
                    #                         data = bytearray(f)
                    #                     data = bytes(data)
                    #                     g.draw_image(data=data, location=(25, 25))
                    #             if action == "Cancel":
                    #                 window1.close()
                    #                 break
                    #
                    #     if event == "-CYCLE-":
                    #         layout1 = [
                    #             [sg.Listbox(values=(
                    #                 'Monopropellant', 'Pressure-fed bipropellant', 'Expander cycle', 'Gas-generator cycle',
                    #                 'Combustion tap-off cycle',
                    #                 'Staged combustion', 'Full-flow staged combustion'), size=(40, 30)),
                    #                 sg.Image(SCDesignerPath + '\\PROPULSION\\P_ID\\Valves\\Images\\Blank.png', size=(1, 1),
                    #                          key='-IMAGE-')],
                    #             [sg.Button('Show Cycle')],
                    #             [sg.Submit(tooltip='Submit'), sg.Cancel()]]
                    #
                    #         window1 = sg.Window('Add Engine Cycle', layout1, grab_anywhere=False)
                    #         cycletype = ""
                    #         while True:
                    #             action, event1 = window1.read()
                    #             if action == "Show Cycle":
                    #                 cycletype = event1[0][0]
                    #                 if cycletype == "Monopropellant":
                    #                     window1.Element('-IMAGE-').Update(SCDesignerPath + '\\PROPULSION\\P_ID\\Monoprop.png')
                    #                 if cycletype == "Pressure-fed bipropellant":
                    #                     window1.Element('-IMAGE-').Update(SCDesignerPath + '\\PROPULSION\\P_ID\\Pressure.png')
                    #                 if cycletype == "Expander cycle":
                    #                     window1.Element('-IMAGE-').Update(SCDesignerPath + '\\PROPULSION\\P_ID\\Expander.png')
                    #                 if cycletype == "Gas-generator cycle":
                    #                     window1.Element('-IMAGE-').Update(SCDesignerPath + '\\PROPULSION\\P_ID\\GasGen.png')
                    #                 if cycletype == "Combustion tap-off cycle":
                    #                     window1.Element('-IMAGE-').Update(SCDesignerPath + '\\PROPULSION\\P_ID\\CombTap.png')
                    #                 if cycletype == "Staged combustion":
                    #                     window1.Element('-IMAGE-').Update(SCDesignerPath + '\\PROPULSION\\P_ID\\StagedComb.png')
                    #                 if cycletype == "Full-flow staged combustion":
                    #                     window1.Element('-IMAGE-').Update(SCDesignerPath + '\\PROPULSION\\P_ID\\FullFlow.png')
                    #             if action == "Submit":
                    #                 cycletype = event1[0][0]
                    #                 window1.close()
                    #                 break
                    #             if action == "Cancel":
                    #                 window1.close()
                    #                 break
                    #         if cycletype == "Monopropellant":
                    #             addComp("TankCylBlue", g, (400, 25))
                    #             addComp("Engine", g, (200, 220))
                    #
                    #         if cycletype == "Pressure-fed bipropellant":
                    #             addComp("TankCylBlue", g, (400, 25))
                    #             addComp("TankCylRed", g, (25, 25))
                    #             addComp("Engine", g, (200, 220))
                    #
                    #         if cycletype == "Expander cycle":
                    #             engineloc = [200, 220]
                    #             fueltankloc = [25, 25]
                    #             pumpLLoc = [170, 25]
                    #             preburnerloc = [210, 120]
                    #             turbineloc = [215, 23]
                    #             pumpRLoc = [260, 25]
                    #             oxtankloc = [400, 25]
                    #             addComp("TankCylBlue", g, tuple(oxtankloc))
                    #             addComp("TankCylRed", g, tuple(fueltankloc))
                    #             addComp("Preburner", g, tuple(preburnerloc))
                    #             addComp("RegenEngine", g, tuple(engineloc))
                    #             addComp("PumpL", g, tuple(pumpLLoc))
                    #             addComp("Turbine", g, tuple(turbineloc))
                    #             addComp("PumpR", g, tuple(pumpRLoc))
                    #
                    #             connect("CylTank", "PumpL", fueltankloc, pumpLLoc, g, allines, "red")
                    #             connect("PumpL", "RegenEngine", pumpLLoc, engineloc, g, allines, "red")
                    #             connect("RegenEngine", "Preburner", engineloc, preburnerloc, g, allines, "red")
                    #             connect("Preburner", "Turbine", preburnerloc, turbineloc, g, allines, "red")
                    #             connect("Turbine", "Engine", turbineloc, engineloc, g, allines, "red")
                    #             connect("CylTank", "PumpR", oxtankloc, pumpRLoc, g, allines, "blue")
                    #             connect("PumpR", "Engine", pumpRLoc, engineloc, g, allines, "blue")
                    #
                    #         if cycletype == "Gas-generator cycle":
                    #             engineloc = [200, 220]
                    #             fueltankloc = [25, 25]
                    #             pumpLLoc = [170, 25]
                    #             preburnerloc = [210, 120]
                    #             turbineloc = [215, 23]
                    #             pumpRLoc = [260, 25]
                    #             oxtankloc = [400, 25]
                    #             addComp("TankCylBlue", g, tuple(oxtankloc))
                    #             addComp("TankCylRed", g, tuple(fueltankloc))
                    #             addComp("Preburner", g, tuple(preburnerloc))
                    #             addComp("RegenEngine", g, tuple(engineloc))
                    #             addComp("PumpL", g, tuple(pumpLLoc))
                    #             addComp("Turbine", g, tuple(turbineloc))
                    #             addComp("PumpR", g, tuple(pumpRLoc))
                    #
                    #             connect("CylTank", "PumpL", fueltankloc, pumpLLoc, g, allines, "red")
                    #             connect("PumpL", "RegenEngine", pumpLLoc, engineloc, g, allines, "red")
                    #             connect("RegenEngine", "Preburner", engineloc, preburnerloc, g, allines, "red")
                    #             connect("Preburner", "Turbine", preburnerloc, turbineloc, g, allines, "red")
                    #             connect("Turbine", "Engine", turbineloc, engineloc, g, allines, "red")
                    #             connect("CylTank", "PumpR", oxtankloc, pumpRLoc, g, allines, "blue")
                    #             connect("PumpR", "Engine", pumpRLoc, engineloc, g, allines, "blue")
                    #
                    #         if cycletype == "Combustion tap-off cycle":
                    #             engineloc = [200, 220]
                    #             fueltankloc = [25, 25]
                    #             pumpLLoc = [170, 25]
                    #             preburnerloc = [210, 120]
                    #             turbineloc = [215, 23]
                    #             pumpRLoc = [260, 25]
                    #             oxtankloc = [400, 25]
                    #             addComp("TankCylBlue", g, tuple(oxtankloc))
                    #             addComp("TankCylRed", g, tuple(fueltankloc))
                    #             addComp("Preburner", g, tuple(preburnerloc))
                    #             addComp("RegenEngine", g, tuple(engineloc))
                    #             addComp("PumpL", g, tuple(pumpLLoc))
                    #             addComp("Turbine", g, tuple(turbineloc))
                    #             addComp("PumpR", g, tuple(pumpRLoc))
                    #
                    #             connect("CylTank", "PumpL", fueltankloc, pumpLLoc, g, allines, "red")
                    #             connect("PumpL", "RegenEngine", pumpLLoc, engineloc, g, allines, "red")
                    #             connect("RegenEngine", "Preburner", engineloc, preburnerloc, g, allines, "red")
                    #             connect("Preburner", "Turbine", preburnerloc, turbineloc, g, allines, "red")
                    #             connect("Turbine", "Engine", turbineloc, engineloc, g, allines, "red")
                    #             connect("CylTank", "PumpR", oxtankloc, pumpRLoc, g, allines, "blue")
                    #             connect("PumpR", "Engine", pumpRLoc, engineloc, g, allines, "blue")
                    #
                    #         if cycletype == "Staged combustion":
                    #             engineloc = [200, 220]
                    #             fueltankloc = [25, 25]
                    #             pumpLLoc = [170, 25]
                    #             preburnerloc = [210, 120]
                    #             turbineloc = [215, 23]
                    #             pumpRLoc = [260, 25]
                    #             oxtankloc = [400, 25]
                    #             addComp("TankCylBlue", g, tuple(oxtankloc))
                    #             addComp("TankCylRed", g, tuple(fueltankloc))
                    #             addComp("Preburner", g, tuple(preburnerloc))
                    #             addComp("RegenEngine", g, tuple(engineloc))
                    #             addComp("PumpL", g, tuple(pumpLLoc))
                    #             addComp("Turbine", g, tuple(turbineloc))
                    #             addComp("PumpR", g, tuple(pumpRLoc))
                    #
                    #             connect("CylTank", "PumpL", fueltankloc, pumpLLoc, g, allines, "red")
                    #             connect("PumpL", "RegenEngine", pumpLLoc, engineloc, g, allines, "red")
                    #             connect("RegenEngine", "Preburner", engineloc, preburnerloc, g, allines, "red")
                    #             connect("Preburner", "Turbine", preburnerloc, turbineloc, g, allines, "orange")
                    #             connect("Turbine", "Engine", turbineloc, engineloc, g, allines, "orange")
                    #             connect("CylTank", "PumpR", oxtankloc, pumpRLoc, g, allines, "blue")
                    #             connect("PumpR", "Engine", pumpRLoc, engineloc, g, allines, "blue")
                    #             connect("PumpR", "Preburner", pumpRLoc, preburnerloc, g, allines, "blue")
                    #
                    #         if cycletype == "Full-flow staged combustion":
                    #             engineloc = [200, 220]
                    #             fueltankloc = [25, 25]
                    #             pumpLLoc = [170, 25]
                    #             preburnerloc = [210, 120]
                    #             turbineloc = [215, 23]
                    #             pumpRLoc = [260, 25]
                    #             oxtankloc = [400, 25]
                    #             addComp("TankCylBlue", g, tuple(oxtankloc))
                    #             addComp("TankCylRed", g, tuple(fueltankloc))
                    #             addComp("Preburner", g, tuple(preburnerloc))
                    #             addComp("RegenEngine", g, tuple(engineloc))
                    #             addComp("PumpL", g, tuple(pumpLLoc))
                    #             addComp("Turbine", g, tuple(turbineloc))
                    #             addComp("PumpR", g, tuple(pumpRLoc))
                    #
                    #             connect("CylTank", "PumpL", fueltankloc, pumpLLoc, g, allines, "red")
                    #             connect("PumpL", "RegenEngine", pumpLLoc, engineloc, g, allines, "red")
                    #             connect("RegenEngine", "Preburner", engineloc, preburnerloc, g, allines, "red")
                    #             connect("Preburner", "Turbine", preburnerloc, turbineloc, g, allines, "red")
                    #             connect("Turbine", "Engine", turbineloc, engineloc, g, allines, "red")
                    #             connect("CylTank", "PumpR", oxtankloc, pumpRLoc, g, allines, "blue")
                    #             connect("PumpR", "Engine", pumpRLoc, engineloc, g, allines, "blue")
                    #
                    #     if event.endswith('+UP'):  # The drawing has ended because mouse up
                    #         start_point, end_point = None, None  # enable grabbing a new rect
                    #         dragging = False
                    #         prior_rect = None
                    #
                    #     if event == 'Exit':
                    #         exit()

                deltavReq = deltaVList[deltaVnames.index(values["-DELTAVSEL-"])]
                StageList.append([counter,values["-DELTAVSEL-"], deltavReq,"ISP", "Propellant Mass","Structural Mass",values["-Number of Engines-"],values["-Engine Type-"], "Maximum Thrust"])
                print(StageList)
                window['Table'].update(StageList)
                counter+=1

            if event == "-TURBOPUMP-":
                import thermochem
                from thermochem.janaf import Janafdb
                from thermochem.burcat import Elementdb
                from proptools import isentropic
                import pyromat as pm
                import cantera as ct
                import numpy as np
                import matplotlib.pyplot as plt

                def FuelData(Formula, Fuel, Temperature, Phase):
                    db = Janafdb()
                    fueloutput = db.getphasedata(formula=Formula, name=Fuel, cache=False)
                    cp = fueloutput.cp([Temperature])[0]
                    S = fueloutput.S([Temperature])[0]
                    DeltaG = fueloutput.DeltaG([Temperature])[0]
                    DeltaH = fueloutput.DeltaH([Temperature])[0]
                    gef = fueloutput.gef([Temperature])[0]
                    hef = fueloutput.hef([Temperature])[0]
                    return cp, S, DeltaG, DeltaH, gef, hef

                # Define gravitational constants
                g = 9.81

                # Define fuel and oxidizer
                FuelFormula = "H2"
                Fuel = "Hydrogen"
                Phase = "Ref"

                OxFormula = "O2"
                Oxidizer = "Oxygen"

                MixtureRatio = 2  # Oxidizer % mass/ Fuel % mass

                # Gas generator example
                TurbineEfficiency = 0.8
                mdotTurbine = 100  # kg/s

                # Define tank conditions
                P_tank = 101325 * 10  # Pascals
                P_Chamber = 101325 * 100  # Pascals
                TankTemp = 300  # Kelvins

                M = 0.01  # Pipe speed mach number

                fuel = pm.get("ig." + Formula)
                gamma = fuel.gam(T=TankTemp, p=P_tank / 100)

                ox = pm.get("ig." + OxFormula)  # Define pyromat oxidizer properties
                gammaOx = ox.gam(T=TankTemp, p=P_tank / 100)

                # ASSUMING NO DENSITY CHANGE FROM TANK TO PUMP IMPELLER and also GAS GENERATOR, PROBABLY OVERSIMPLIFICATION
                fuelDens = fuel.d(T=TankTemp)
                oxDens = ox.d(T=TankTemp)
                # gamma = H2.k(T=TankTemp)

                # Fuel and oxidizer feed line thermal properties
                T1 = TankTemp * (
                            1 / isentropic.stag_temperature_ratio(M, gamma))  # Calculate temperature of fuel at pipe speeds
                T1ox = TankTemp * (1 / isentropic.stag_temperature_ratio(M,
                                                                         gammaOx))  # Calculate temperature of fuel at pipe speeds

                C_p = FuelData(FuelFormula, Fuel, T1, Phase)[0]  # Calculate specific heat
                C_pOx = FuelData(FuelFormula, Fuel, T1, Phase)[0]  # Calculate specific heat
                # Put in spouting velocity Ue

                # Get all of the Species objects defined in the GRI 3.0 mechanism
                species = {S.name: S for S in ct.Species.listFromFile('gri30.cti')}

                # Create an IdealGas object including incomplete combustion species
                gas2 = ct.Solution(thermo='IdealGas', species=species.values())
                gas2.TP = TankTemp, P_tank
                gas2.set_equivalence_ratio(1, FuelFormula, OxFormula)
                gas2.equilibrate('HP')  # Calculate chemical equilibrium

                # Calculate the specific heat ratio of the combustion products of the gas generator
                gammaGGExhaust = gas2.cp / gas2.cv

                # Calculate the turbine inlet conditions
                T_1 = gas2.T  # Set turbine inlet temperature
                P_a = 101325  # Set turbine exit pressure.

                # Calculate turbine power generated
                TurbinePower = (mdotTurbine * TurbineEfficiency * gas2.cp * T1 * (
                            1 - ((P_a / P_tank) ** ((gammaGGExhaust - 1) / gammaGGExhaust))))

                PumpPower = TurbinePower
                Turbine_angvel = 100
                Turbine_Torque = TurbinePower / Turbine_angvel

                Turbopump_type = "Direct Drive"

                if Turbopump_type == "Direct Drive":
                    Pump_angvel = Turbine_angvel
                    Pump_Torque = Turbine_Torque
                elif Turbopump_type == "Geared, Pancake":
                    print("Pancake")
                elif Turbopump_type == "Geared, Off-set Turbine":
                    print("Off-set Turbine")
                elif Turbopump_type == "Geared, Single Geared Pump":
                    print("Geared, Single Geared Pump")

                # Define mass flow rates (for now)
                mdotFuelPump = 100  # kg/s
                mdotOxPump = 100  # kg/s

                # Calculate volumetric flow rates
                Qfuel = mdotFuelPump / fuelDens
                Qox = mdotOxPump / oxDens

                # Calculate pressure gain across pumps (not including line losses, cooling jacket, injector pressure losses, etc for now)
                FuelPumpDeltaP = P_Chamber - P_tank
                OxPumpDeltaP = P_Chamber - P_tank

                # Calculate pump head
                Hfuel = FuelPumpDeltaP / (g * fuelDens)
                Hox = OxPumpDeltaP / (g * oxDens)

                # Calculate pump specific speed and pump specific diameter for fuel and oxidizer pumps
                Fuel_n_s = (Pump_angvel * math.sqrt(Qfuel)) / (((g * Hfuel) ** 0.75))
                Fuel_d_s = (D * ((g * Hfuel) ** 0.25)) / math.sqrt(Qfuel)

                Ox_n_s = (Pump_angvel * math.sqrt(Qox)) / (((g * Hox) ** 0.75))
                Ox_d_s = (D * ((g * Hox) ** 0.25)) / math.sqrt(Qox)

                # Define fuel/ox pump radii
                Rfuel = 0.1  # meters
                Rox = 0.1  # meters

                # Calculate tip speeds
                u_tip_fuel = Pump_angvel * Rfuel  # Radians/sec
                u_tip_ox = Pump_angvel * Rox  # Radians/sec

                # Define outlet areas
                A_outlet_Ox = 0.002  # m^2
                A_outlet_Prop = 0.002  # m^2

                # Define head and flow coefficients for fuel and ox pumps
                OxPumpHeadCoeff = (Hox) / ((u_tip_ox ** 2) / g)
                OxPumpFlowCoeff = (Qox / A_outlet_Ox) / u_tip_ox

                FuelPumpHeadCoeff = (Hfuel) / ((u_tip_fuel ** 2) / g)
                FuelPumpFlowCoeff = (Qfuel / A_outlet_Fuel) / u_tip_fuel

                # Define fuel/oxidizer Z heights
                Z_OxLevel = 30  # Meters
                Z_FuelLevel = 20  # Meters

                Z_OxPumpLevel = 2.5  # Meters
                Z_FuelPumpLevel = 2.5  # Meters

                # Calculate head from tank, INCORPORATE DRAG INTO THIS EVENTUALLY
                FPA = 90  # Straight up yo
                Z_accel = 0
                lateral_accel = 0
                Zox = (Z_OxLevel - Z_OxPumpLevel) * (
                            (g + Z_accel * math.sin(math.radians(FPA))) + (lateral_accel * math.cos(math.radians(FPA))))
                Zfuel = (Z_FuelLevel - Z_FuelPumpLevel) * (
                            (g + Z_accel * math.sin(math.radians(FPA))) + (lateral_accel * math.cos(math.radians(FPA))))

                # Calculate suction head
                NPSHAvailableOx = (P_tank / oxDens) + Zox - (P_fox / oxDens) - (P_vapor_ox / oxDens)
                NPSHAvailableFuel = (P_tank / fuelDens) + Zfuel - (P_ffuel / fuelDens) - (P_vapor_fuel / fuelDens)

                ThomaOx = NPSHAvailableOx / Hox
                ThomaFuel = NPSHAvailableFuel / Hfuel

                Pump_Suction_Specific_Speed = 25  # Meters

                OxPumpFluidPower = ShaftPwrDist * Hox
                FuelPumpFluidPower = (1 - ShaftPwrDist) * Hfuel

                # OxPumpEff =
                # FuelPumpEff =

                import FreeCAD as App
                import Draft

                doc = App.newDocument()

                p1 = App.Vector(0, 0, 0)
                p2 = App.Vector(1000, 1000, 0)
                p3 = App.Vector(2000, 0, 0)
                p4 = App.Vector(1500, -2000, 0)

                bezcurve1 = Draft.make_bezcurve([p1, p2, p3, p4], closed=True)
                # bezcurve2 = Draft.make_bezcurve([p4, 1.3*p2, p1, 4.1*p3], closed=True)
                # bezcurve3 = Draft.make_bezcurve([1.7*p3, 1.5*p4, 2.1*p2, p1], closed=True)

                doc.recompute()

                #
                # # Turbine power must equal pump power
                # # From Peroxide turbopump design
                # NPSHAvailable = ((P_tank/(density*9.81)) + ((C**2)/(2*9.81))) - (P_Chamber/(density*9.81))
                #
                # # U = N*
                #
                # # Inducer volumetric flow rate
                # Qin = mdotPump/density
                # lambda_c = 1.3
                # lambda_w = 0.28 + ((U/400)**2)
                # NPSHRequired = (lambda_c *((C**2)/2*9.81)) + (lambda_w*((W**2)/2*9.81))
                # # W is fluid velocity in relative reference frame
                # # C is fluid velocity in absolute reference frame

                #
                # # Pump Impeller
                # # establish NPSHR, NPSHA, N, Cavitation limits, Optimal inlet geometry, blade number
                #
                # # inducer
                # # pick flow/head coefficient, inlet and outlet size
                #
                # # volute
                # # define volute shape based on outlet velocity requirements
                #
                # # turbine impeller
                # # define inlet/outlet diameter, efficiency, power output, pressure drop, number of blades
                #
                #
                #
                # # Define meridional profile, blade shape, inlet/outlet velocity triangles, 3D geometry
            if event == "-SOLID-":
                import matplotlib.pyplot as plt
                import math
                from numpy import array
                import matplotlib.pyplot as plt
                from scipy.integrate import odeint
                import numpy as np
                from scipy import integrate

                L_grain = 12
                D_o_grain = 2
                D_port = 0.2
                D_throat = 1
                T_f = 3500
                gamma = 1.13
                MW = 27
                BRC = 0.00000385
                BRE = 0.62
                Rho = 1800
                V_e = 2350
                Cstar = math.sqrt(8.314 * T_f / (gamma * MW)) * ((2 / (gamma + 1)) ** (-(gamma + 1) / (2 * (gamma - 1))))
                A_t = math.pi * ((D_throat) ** 2) / 4
                gravity = 9.81
                timespan = 409

                def Burn(x, t):

                    r_b = BRC * (x[1] ** BRE)
                    w = r_b * t
                    if w > D_port:
                        print("stop")
                        A_b = 0
                        p_c = 0
                        F = 0
                    else:
                        A_b = (2 * math.pi * ((D_o_grain ** 2) - ((D_port + w) ** 2))) + (
                                    2 * math.pi * (D_port + w) * L_grain)
                        p_c = (BRC * Rho * A_b * Cstar / (gravity * A_t)) ** (1 / (1 - BRE))
                        F = (p_c * A_t * V_e / Cstar)
                    # print(A_b)
                    return array([A_b, p_c, F])

                A_b1 = (2 * math.pi * ((D_o_grain ** 2) - (D_port ** 2))) + (2 * math.pi * D_port * L_grain)

                p_c1 = ((BRC * Rho * A_b1 * Cstar) / (gravity * A_t)) ** (1 / (1 - BRE))

                initial_state = array([A_b1, p_c1, 0])
                solution = odeint(Burn, initial_state, [i for i in range(0, timespan)])

                # print(solution)
                times = np.linspace(0, timespan, timespan)

                plt.plot(times, solution[:, 1])
                plt.xlabel("Time (s)")
                plt.ylabel("Chamber Pressure (Pa)")
                plt.show()

                plt.plot(times, solution[:, 2])
                plt.xlabel("Time (s)")
                plt.ylabel("Thrust (N)")
                plt.show()
            if event == "-PIPE-":
                import os
                import os.path
                import FreeCAD
                import importOBJ
                import FreeCAD
                import Draft

                ShapeList = []

                for obj in FreeCAD.ActiveDocument.Objects:
                    if hasattr(obj, "Shape"):
                        ShapeList.append(obj.Name)


                if os.path.isdir(SCDesignerPath + "\\" + str(
                        App.ActiveDocument.Label)):
                    pass
                else:
                    os.mkdir(SCDesignerPath + "\\" + str(
                        App.ActiveDocument.Label))

                roll = []
                pitch = []
                yaw = []
                x = []
                y = []
                z = []

                for shape in ShapeList:
                    p = FreeCAD.ActiveDocument.getObject(shape).Placement.Base
                    print(p)
                    ypr = str(FreeCAD.ActiveDocument.getObject(shape).Placement)
                    startloc = ypr.find("Roll=")
                    ypr = ypr[startloc + 6:-2]
                    ypr = ypr.split(",")
                    roll.append(ypr[2])
                    pitch.append(ypr[1])
                    yaw.append(ypr[0])
                    x.append(p[0])
                    y.append(p[1])
                    z.append(p[2])
                try:
                    deltaX = x[1] - x[0]
                    deltaY = y[1] - y[0]
                    deltaZ = z[1] - z[0]

                    import math
                    distance = math.sqrt((deltaX**2)+(deltaZ**2))

                    PlaneAngle = -math.degrees(math.atan2(deltaZ,deltaX))

                    OffsetRadius = 20
                    if roll[0] == roll[1] and pitch[0] == pitch[1] and yaw[0] == yaw[1]:
                        Equal = True
                    import FreeCADGui as Gui
                    Gui.runCommand('Std_OrthographicCamera', 1)
                     ### Begin command Std_Workbench
                    Gui.activateWorkbench("PartDesignWorkbench")
                     ### End command Std_Workbench
                     ### Begin command PartDesign_Body
                    App.activeDocument().addObject('PartDesign::Body', 'Body')
                    import PartDesignGui
                    Gui.activateView('Gui::View3DInventor', True)
                    Gui.activeView().setActiveObject('pdbody', App.activeDocument().Body)
                    Gui.Selection.clearSelection()
                    Gui.Selection.addSelection(App.ActiveDocument.Body)
                    App.ActiveDocument.recompute()
                     ### End command PartDesign_Body
                     # Gui.Selection.addSelection(App.ActiveDocument.Name,'Body')
                     ### Begin command PartDesign_Plane
                    App.getDocument(App.ActiveDocument.Name).getObject('Body').newObject('PartDesign::Plane',
                                                                                             'DatumPlane')
                    App.activeDocument().recompute()
                    Gui.getDocument(App.ActiveDocument.Name).setEdit(
                        App.getDocument(App.ActiveDocument.Name).getObject('Body'), 0, 'DatumPlane.')
                    import Show
                    from Show.Containers import isAContainer
                    _tv_DatumPlane = Show.TempoVis(App.ActiveDocument, tag='PartGui::TaskAttacher')
                    tvObj = App.getDocument(App.ActiveDocument.Name).getObject('DatumPlane')

                    Gui.Selection.clearSelection()
                    App.getDocument(App.ActiveDocument.Name).DatumPlane.Placement = App.Placement(App.Vector(0, 0, 0),
                                                                                                 App.Rotation(
                                                                                                     App.Vector(0, 1, 0), PlaneAngle),
                                                                                                 App.Vector(0, 0, 0))
                    App.getDocument(App.ActiveDocument.Name).getObject('DatumPlane').AttachmentOffset = App.Placement(
                        App.Vector(0.0000000000, 0.0000000000, 0.0000000000),
                        App.Rotation(0.0000000000, 0.0000000000, 0.0000000000))
                    App.getDocument(App.ActiveDocument.Name).getObject('DatumPlane').MapReversed = False
                    App.getDocument(App.ActiveDocument.Name).getObject('DatumPlane').Support = None
                    App.getDocument(App.ActiveDocument.Name).getObject('DatumPlane').MapPathParameter = 0.000000
                    App.getDocument(App.ActiveDocument.Name).getObject('DatumPlane').MapMode = 'Deactivated'
                    App.getDocument(App.ActiveDocument.Name).getObject('DatumPlane').recompute()
                    Gui.getDocument(App.ActiveDocument.Name).resetEdit()
                    _tv_DatumPlane.restore()
                    del (_tv_DatumPlane)

                    App.getDocument(App.ActiveDocument.Name).getObject('Body').newObject('Sketcher::SketchObject', 'Sketch')
                    App.getDocument(App.ActiveDocument.Name).getObject('Sketch').Support = (
                    App.getDocument(App.ActiveDocument.Name).getObject('DatumPlane'), '')
                    App.getDocument(App.ActiveDocument.Name).getObject('Sketch').MapMode = 'FlatFace'
                    App.ActiveDocument.recompute()
                    Gui.getDocument(App.ActiveDocument.Name).setEdit(
                        App.getDocument(App.ActiveDocument.Name).getObject('Body'), 0, 'Sketch.')
                    import Show
                    ActiveSketch = App.getDocument(App.ActiveDocument.Name).getObject('Sketch')
                    tv = Show.TempoVis(App.ActiveDocument, tag=ActiveSketch.ViewObject.TypeId)
                    ActiveSketch.ViewObject.TempoVis = tv
                    if ActiveSketch.ViewObject.EditingWorkbench:
                        tv.activateWorkbench(ActiveSketch.ViewObject.EditingWorkbench)
                    if ActiveSketch.ViewObject.HideDependent:
                        tv.hide(tv.get_all_dependent(App.getDocument(App.ActiveDocument.Name).getObject('Body'), 'Sketch.'))
                    if ActiveSketch.ViewObject.ShowSupport:
                        tv.show([ref[0] for ref in ActiveSketch.Support if not ref[0].isDerivedFrom("PartDesign::Plane")])
                    if ActiveSketch.ViewObject.ShowLinks:
                        tv.show([ref[0] for ref in ActiveSketch.ExternalGeometry])
                    tv.hide(ActiveSketch)
                    del (tv)
                    del (ActiveSketch)

                    import PartDesignGui
                    ActiveSketch = App.getDocument(App.ActiveDocument.Name).getObject('Sketch')
                    if ActiveSketch.ViewObject.RestoreCamera:
                        ActiveSketch.ViewObject.TempoVis.saveCamera()

                     ### End command PartDesign_NewSketch
                     # Gui.Selection.clearSelection()
                    Gui.runCommand('Sketcher_CreatePolyline', 0)
                    import Part
                    import Sketcher
                    # Offset = 25
                    App.getDocument(App.ActiveDocument.Name).getObject('Sketch').addGeometry(
                        Part.LineSegment(App.Vector(OffsetRadius, OffsetRadius, 0), App.Vector(distance-OffsetRadius, OffsetRadius, 0)), False)
                    App.getDocument(App.ActiveDocument.Name).getObject('Sketch').addConstraint(
                        Sketcher.Constraint('Horizontal', 0))
                    Gui.runCommand('Sketcher_CompCreateArc', 1)
                    # App.getDocument(App.ActiveDocument.Name).getObject('Sketch').setDatum(5, App.Units.Quantity('0.000000 mm'))
                    App.getDocument(App.ActiveDocument.Name).getObject('Sketch').addGeometry(
                        Part.ArcOfCircle(Part.Circle(App.Vector(OffsetRadius, 0, 0), App.Vector(0, 0, 1), OffsetRadius),
                                         1.806574, 3.137779), False)
                    App.getDocument(App.ActiveDocument.Name).getObject('Sketch').addConstraint(
                        Sketcher.Constraint('Coincident', 1, 2, -1, 1))
                    # App.getDocument(App.ActiveDocument.Name).getObject('Sketch').addConstraint(
                    #     Sketcher.Constraint('Coincident', 1, 1, 0, 1))
                    App.getDocument(App.ActiveDocument.Name).getObject('Sketch').addConstraint(
                        Sketcher.Constraint('Tangent', 1, 1, 0, 1))
                    # App.getDocument(App.ActiveDocument.Name).getObject('Sketch').delConstraintOnPoint(1, 1)
                    App.getDocument(App.ActiveDocument.Name).getObject('Sketch').addGeometry(
                        Part.ArcOfCircle(Part.Circle(App.Vector(distance-OffsetRadius, y[1], 0), App.Vector(0, 0, 1), OffsetRadius),
                                         0, 1.570205), False)
                    App.getDocument(App.ActiveDocument.Name).getObject('Sketch').addConstraint(
                        Sketcher.Constraint('Coincident', 2, 2, 0, 2))
                    App.getDocument(App.ActiveDocument.Name).getObject('Sketch').addConstraint(
                        Sketcher.Constraint('DistanceY', 1, 2, 2, 3, y[1]))
                    # App.getDocument(App.ActiveDocument.Name).getObject('Sketch').setDatum(4,App.Units.Quantity('8.120000 mm'))
                    Gui.getDocument(App.ActiveDocument.Name).resetEdit()
                    App.ActiveDocument.recompute()
                    ActiveSketch = App.getDocument(App.ActiveDocument.Name).getObject('Sketch')


                     # Gui.Selection.addSelection(App.ActiveDocument.Name,'Body','Sketch.')
                    App.getDocument(App.ActiveDocument.Name).recompute()

                    App.getDocument(App.ActiveDocument.Name).getObject('Body').newObject('PartDesign::Plane',
                                                                                             'DatumPlane001')
                    App.getDocument(App.ActiveDocument.Name).getObject('DatumPlane001').Support = [
                        (App.getDocument(App.ActiveDocument.Name).getObject('Sketch'), '')]
                    App.getDocument(App.ActiveDocument.Name).getObject('DatumPlane001').MapMode = 'ObjectXY'
                    App.activeDocument().recompute()
                    Gui.getDocument(App.ActiveDocument.Name).setEdit(
                        App.getDocument(App.ActiveDocument.Name).getObject('Body'), 0, 'DatumPlane001.')
                    import Show
                    from Show.Containers import isAContainer

                     ### End command PartDesign_Plane
                     # Gui.Selection.clearSelection()
                    App.getDocument(App.ActiveDocument.Name).getObject('DatumPlane001').AttachmentOffset = App.Placement(
                        App.Vector(0.0000000000, 0.0000000000, 0.0000000000),
                        App.Rotation(0.0000000000, 0.0000000000, 0.0000000000))
                    App.getDocument(App.ActiveDocument.Name).getObject('DatumPlane001').MapReversed = False
                    App.getDocument(App.ActiveDocument.Name).getObject('DatumPlane001').Support = [
                        (App.getDocument(App.ActiveDocument.Name).getObject('Sketch'), '')]
                    App.getDocument(App.ActiveDocument.Name).getObject('DatumPlane001').MapPathParameter = 0.000000
                    App.getDocument(App.ActiveDocument.Name).getObject('DatumPlane001').MapMode = 'ObjectXZ'
                    App.getDocument(App.ActiveDocument.Name).getObject('DatumPlane001').recompute()
                    Gui.getDocument(App.ActiveDocument.Name).resetEdit()



                    App.getDocument(App.ActiveDocument.Name).getObject('Body').newObject('Sketcher::SketchObject',
                                                                                             'Sketch001')
                    App.getDocument(App.ActiveDocument.Name).getObject('Sketch001').Support = (
                    App.getDocument(App.ActiveDocument.Name).getObject('DatumPlane001'), '')
                    App.getDocument(App.ActiveDocument.Name).getObject('Sketch001').MapMode = 'FlatFace'
                    App.ActiveDocument.recompute()
                    Gui.getDocument(App.ActiveDocument.Name).setEdit(
                        App.getDocument(App.ActiveDocument.Name).getObject('Body'), 0, 'Sketch001.')
                    ActiveSketch = App.getDocument(App.ActiveDocument.Name).getObject('Sketch001')
                    tv = Show.TempoVis(App.ActiveDocument, tag=ActiveSketch.ViewObject.TypeId)
                    ActiveSketch.ViewObject.TempoVis = tv
                    if ActiveSketch.ViewObject.EditingWorkbench:
                        tv.activateWorkbench(ActiveSketch.ViewObject.EditingWorkbench)
                    if ActiveSketch.ViewObject.HideDependent:
                        tv.hide(
                            tv.get_all_dependent(App.getDocument(App.ActiveDocument.Name).getObject('Body'), 'Sketch001.'))
                    if ActiveSketch.ViewObject.ShowSupport:
                        tv.show([ref[0] for ref in ActiveSketch.Support if not ref[0].isDerivedFrom("PartDesign::Plane")])
                    if ActiveSketch.ViewObject.ShowLinks:
                        tv.show([ref[0] for ref in ActiveSketch.ExternalGeometry])
                    tv.hide(ActiveSketch)
                    del (tv)
                    del (ActiveSketch)

                    import PartDesignGui
                    ActiveSketch = App.getDocument(App.ActiveDocument.Name).getObject('Sketch001')
                    if ActiveSketch.ViewObject.RestoreCamera:
                        ActiveSketch.ViewObject.TempoVis.saveCamera()
                    outerRadius = 12
                    innerRadius = 10
                     ### End command PartDesign_NewSketch
                     # Gui.Selection.clearSelection()
                    Gui.runCommand('Sketcher_CompCreateCircle', 0)
                    App.getDocument(App.ActiveDocument.Name).getObject('Sketch001').addGeometry(
                        Part.Circle(App.Vector(-0.000000, 0.000000, 0), App.Vector(0, 0, 1), outerRadius), False)
                    App.getDocument(App.ActiveDocument.Name).getObject('Sketch001').addConstraint(
                        Sketcher.Constraint('Coincident', 0, 3, -1, 1))
                    App.getDocument(App.ActiveDocument.Name).getObject('Sketch001').addGeometry(
                        Part.Circle(App.Vector(-0.000000, 0.000000, 0), App.Vector(0, 0, 1), innerRadius), False)
                    # App.getDocument(App.ActiveDocument.Name).getObject('Sketch001').addConstraint(
                    #     Sketcher.Constraint('Coincident', 1, 3, 0, 3))
                    Gui.getDocument(App.ActiveDocument.Name).resetEdit()
                    App.ActiveDocument.recompute()
                    ActiveSketch = App.getDocument(App.ActiveDocument.Name).getObject('Sketch001')

                     # Gui.Selection.addSelection(App.ActiveDocument.Name,'Body','Sketch001.')
                    App.getDocument(App.ActiveDocument.Name).recompute()
                     ### Begin command PartDesign_AdditivePipe
                    App.getDocument(App.ActiveDocument.Name).getObject('Body').newObject('PartDesign::AdditivePipe',
                                                                                             'AdditivePipe')
                    App.getDocument(App.ActiveDocument.Name).getObject('AdditivePipe').Profile = App.getDocument(
                        App.ActiveDocument.Name).getObject('Sketch001')
                    App.getDocument(App.ActiveDocument.Name).getObject('AdditivePipe').Spine = App.getDocument(
                        App.ActiveDocument.Name).getObject('Sketch')
                    App.ActiveDocument.recompute()

                    Gui.Selection.addSelection(App.ActiveDocument.Name, 'Body', 'DatumPlane001.')
                    Gui.runCommand('Std_ToggleVisibility', 0)
                    Gui.Selection.addSelection(App.ActiveDocument.Name, 'Body', 'DatumPlane.')

                    Gui.runCommand('Std_ToggleVisibility', 0)
                    Gui.SendMsgToActiveView("Save")
                    App.getDocument(App.ActiveDocument.Name).save()
                    AssemblyName = App.ActiveDocument.Name
                    App.newDocument(App.ActiveDocument.Name)
                    # App.getDocument(App.ActiveDocument.Name).moveObject(App.getDocument(AssemblyName).getObject('Body'),True)
                    # App.getDocument(App.ActiveDocument.Name).saveAs(
                    #     SCDesignerPath + "/Pipe.FCStd")

                except:
                    pass
            if event == "-PRESSURE-" and values[1] == "Spherical":
                import FreeCADGui as Gui
                import Sketcher
                import Part
                Gui.runCommand('Std_Workbench', 25)
                Gui.runCommand('Std_ViewStatusBar', 1)
                Gui.runCommand('Std_ViewStatusBar', 0)
                with open('C:/Program Files/FreeCAD 0.19/data/Mod/Start/StartPage/LoadNew.py') as file:
                    exec(file.read())
                 # App.setActiveDocument(FreeCAD.ActiveDocument.Name)
                 # App.ActiveDocument=App.getDocument(FreeCAD.ActiveDocument.Name)
                 # Gui.ActiveDocument=Gui.getDocument(FreeCAD.ActiveDocument.Name)
                Gui.runCommand('Std_OrthographicCamera', 1)
                 ### Begin command Std_Workbench
                Gui.activateWorkbench("PartDesignWorkbench")
                 ### End command Std_Workbench
                 ### Begin command PartDesign_Body
                App.activeDocument().addObject('PartDesign::Body', 'Body')
                import PartDesignGui
                Gui.activateView('Gui::View3DInventor', True)
                Gui.activeView().setActiveObject('pdbody', App.activeDocument().Body)
                Gui.Selection.clearSelection()
                Gui.Selection.addSelection(App.ActiveDocument.Body)
                App.ActiveDocument.recompute()
                 ### End command PartDesign_Body
                 # Gui.Selection.addSelection(FreeCAD.ActiveDocument.Name,'Body')
                Gui.runCommand('PartDesign_NewSketch', 0)
                 # Gui.Selection.clearSelection()
                 # Gui.Selection.addSelection(FreeCAD.ActiveDocument.Name,'Body','Origin.XZ_Plane.',-17.0328,-3.8743e-06,32.5)
                App.getDocument(FreeCAD.ActiveDocument.Name).getObject('Body').newObject('Sketcher::SketchObject', 'Sketch')
                App.getDocument(FreeCAD.ActiveDocument.Name).getObject('Sketch').Support = (
                App.getDocument(FreeCAD.ActiveDocument.Name).getObject('XZ_Plane'), [''])
                App.getDocument(FreeCAD.ActiveDocument.Name).getObject('Sketch').MapMode = 'FlatFace'
                App.ActiveDocument.recompute()
                Gui.getDocument(FreeCAD.ActiveDocument.Name).setEdit(App.getDocument(FreeCAD.ActiveDocument.Name).getObject('Body'), 0, 'Sketch.')
                import Show
                ActiveSketch = App.getDocument(FreeCAD.ActiveDocument.Name).getObject('Sketch')
                tv = Show.TempoVis(App.ActiveDocument, tag=ActiveSketch.ViewObject.TypeId)
                ActiveSketch.ViewObject.TempoVis = tv
                if ActiveSketch.ViewObject.EditingWorkbench:
                    tv.activateWorkbench(ActiveSketch.ViewObject.EditingWorkbench)
                if ActiveSketch.ViewObject.HideDependent:
                    tv.hide(tv.get_all_dependent(App.getDocument(FreeCAD.ActiveDocument.Name).getObject('Body'), 'Sketch.'))
                if ActiveSketch.ViewObject.ShowSupport:
                    tv.show([ref[0] for ref in ActiveSketch.Support if not ref[0].isDerivedFrom("PartDesign::Plane")])
                if ActiveSketch.ViewObject.ShowLinks:
                    tv.show([ref[0] for ref in ActiveSketch.ExternalGeometry])
                tv.hide(ActiveSketch)
                del (tv)
                del (ActiveSketch)

                import PartDesignGui
                ActiveSketch = App.getDocument(FreeCAD.ActiveDocument.Name).getObject('Sketch')
                if ActiveSketch.ViewObject.RestoreCamera:
                    ActiveSketch.ViewObject.TempoVis.saveCamera()

                 # Gui.Selection.clearSelection()
                Gui.runCommand('Sketcher_CompCreateArc', 0)
                App.getDocument(FreeCAD.ActiveDocument.Name).getObject('Sketch').addGeometry(
                    Part.ArcOfCircle(Part.Circle(App.Vector(0.000000, -0.000000, 0), App.Vector(0, 0, 1), 69.774403),
                                     0.032553, 3.101019), False)
                App.getDocument(FreeCAD.ActiveDocument.Name).getObject('Sketch').addConstraint(
                    Sketcher.Constraint('Coincident', 0, 3, -1, 1))
                App.getDocument(FreeCAD.ActiveDocument.Name).getObject('Sketch').addGeometry(
                    Part.ArcOfCircle(Part.Circle(App.Vector(0.000000, -0.000000, 0), App.Vector(0, 0, 1), 71.282617),
                                     0.028942, 3.101878), False)
                App.getDocument(FreeCAD.ActiveDocument.Name).getObject('Sketch').addConstraint(
                    Sketcher.Constraint('Coincident', 1, 3, 0, 3))
                Gui.runCommand('Sketcher_CreatePolyline', 0)
                App.getDocument(FreeCAD.ActiveDocument.Name).getObject('Sketch').addGeometry(
                    Part.LineSegment(App.Vector(-71.226409, 2.830220, 0), App.Vector(-74.622643, 3.018874, 0)), False)
                App.getDocument(FreeCAD.ActiveDocument.Name).getObject('Sketch').addConstraint(
                    Sketcher.Constraint('Coincident', 1, 2, 2, 1))
                App.getDocument(FreeCAD.ActiveDocument.Name).getObject('Sketch').addGeometry(
                    Part.LineSegment(App.Vector(-74.622643, 3.018874, 0), App.Vector(-74.622643, 4.339629, 0)), False)
                App.getDocument(FreeCAD.ActiveDocument.Name).getObject('Sketch').addConstraint(
                    Sketcher.Constraint('Coincident', 2, 2, 3, 1))
                App.getDocument(FreeCAD.ActiveDocument.Name).getObject('Sketch').addConstraint(Sketcher.Constraint('Vertical', 3))
                App.getDocument(FreeCAD.ActiveDocument.Name).getObject('Sketch').addGeometry(
                    Part.LineSegment(App.Vector(-74.622643, 4.339629, 0), App.Vector(-77.264145, 4.339629, 0)), False)
                App.getDocument(FreeCAD.ActiveDocument.Name).getObject('Sketch').addConstraint(
                    Sketcher.Constraint('Coincident', 3, 2, 4, 1))
                App.getDocument(FreeCAD.ActiveDocument.Name).getObject('Sketch').addConstraint(Sketcher.Constraint('Horizontal', 4))
                App.getDocument(FreeCAD.ActiveDocument.Name).getObject('Sketch').addGeometry(
                    Part.LineSegment(App.Vector(-77.264145, 4.339629, 0), App.Vector(-77.264145, 1.509440, 0)), False)
                App.getDocument(FreeCAD.ActiveDocument.Name).getObject('Sketch').addConstraint(
                    Sketcher.Constraint('Coincident', 4, 2, 5, 1))
                App.getDocument(FreeCAD.ActiveDocument.Name).getObject('Sketch').addConstraint(Sketcher.Constraint('Vertical', 5))
                App.getDocument(FreeCAD.ActiveDocument.Name).getObject('Sketch').addGeometry(
                    Part.LineSegment(App.Vector(-77.264145, 1.509440, 0), App.Vector(-69.339622, 1.320761, 0)), False)
                App.getDocument(FreeCAD.ActiveDocument.Name).getObject('Sketch').addConstraint(
                    Sketcher.Constraint('Coincident', 5, 2, 6, 1))
                App.getDocument(FreeCAD.ActiveDocument.Name).getObject('Sketch').addConstraint(Sketcher.Constraint('Horizontal', 6))
                App.getDocument(FreeCAD.ActiveDocument.Name).getObject('Sketch').addGeometry(
                    Part.LineSegment(App.Vector(-69.339622, 1.509440, 0), App.Vector(-69.339622, 3.018874, 0)), False)
                App.getDocument(FreeCAD.ActiveDocument.Name).getObject('Sketch').addConstraint(
                    Sketcher.Constraint('Coincident', 6, 2, 7, 1))
                App.getDocument(FreeCAD.ActiveDocument.Name).getObject('Sketch').addConstraint(
                    Sketcher.Constraint('Coincident', 7, 2, 0, 2))
                App.getDocument(FreeCAD.ActiveDocument.Name).getObject('Sketch').addConstraint(Sketcher.Constraint('Vertical', 7))
                App.getDocument(FreeCAD.ActiveDocument.Name).getObject('Sketch').addGeometry(
                    Part.LineSegment(App.Vector(71.252764, 2.062774, 0), App.Vector(71.254903, 1.988904, 0)), False)
                App.getDocument(FreeCAD.ActiveDocument.Name).getObject('Sketch').addConstraint(
                    Sketcher.Constraint('Tangent', 1, 1, 8, 1))
                App.getDocument(FreeCAD.ActiveDocument.Name).getObject('Sketch').addGeometry(
                    Part.LineSegment(App.Vector(71.254903, 1.988904, 0), App.Vector(74.433968, 2.264154, 0)), False)
                App.getDocument(FreeCAD.ActiveDocument.Name).getObject('Sketch').addConstraint(
                    Sketcher.Constraint('Coincident', 8, 2, 9, 1))
                App.getDocument(FreeCAD.ActiveDocument.Name).getObject('Sketch').addGeometry(
                    Part.LineSegment(App.Vector(74.433968, 2.264154, 0), App.Vector(74.433968, 4.905665, 0)), False)
                App.getDocument(FreeCAD.ActiveDocument.Name).getObject('Sketch').addConstraint(
                    Sketcher.Constraint('Coincident', 9, 2, 10, 1))
                App.getDocument(FreeCAD.ActiveDocument.Name).getObject('Sketch').addConstraint(Sketcher.Constraint('Vertical', 10))
                App.getDocument(FreeCAD.ActiveDocument.Name).getObject('Sketch').addGeometry(
                    Part.LineSegment(App.Vector(74.433968, 4.905665, 0), App.Vector(76.320755, 4.905665, 0)), False)
                App.getDocument(FreeCAD.ActiveDocument.Name).getObject('Sketch').addConstraint(
                    Sketcher.Constraint('Coincident', 10, 2, 11, 1))
                App.getDocument(FreeCAD.ActiveDocument.Name).getObject('Sketch').addConstraint(Sketcher.Constraint('Horizontal', 11))
                App.getDocument(FreeCAD.ActiveDocument.Name).getObject('Sketch').addGeometry(
                    Part.LineSegment(App.Vector(76.320755, 4.905665, 0), App.Vector(76.132080, 0.943404, 0)), False)
                App.getDocument(FreeCAD.ActiveDocument.Name).getObject('Sketch').addConstraint(
                    Sketcher.Constraint('Coincident', 11, 2, 12, 1))
                App.getDocument(FreeCAD.ActiveDocument.Name).getObject('Sketch').addGeometry(
                    Part.LineSegment(App.Vector(76.132080, 0.943404, 0), App.Vector(69.528297, 0.943404, 0)), False)
                App.getDocument(FreeCAD.ActiveDocument.Name).getObject('Sketch').addConstraint(
                    Sketcher.Constraint('Coincident', 12, 2, 13, 1))
                App.getDocument(FreeCAD.ActiveDocument.Name).getObject('Sketch').addConstraint(Sketcher.Constraint('Horizontal', 13))
                App.getDocument(FreeCAD.ActiveDocument.Name).getObject('Sketch').addGeometry(
                    Part.LineSegment(App.Vector(69.528297, 0.943404, 0), App.Vector(69.528297, 2.075475, 0)), False)
                App.getDocument(FreeCAD.ActiveDocument.Name).getObject('Sketch').addConstraint(
                    Sketcher.Constraint('Coincident', 13, 2, 14, 1))
                App.getDocument(FreeCAD.ActiveDocument.Name).getObject('Sketch').addConstraint(
                    Sketcher.Constraint('Coincident', 14, 2, 0, 1))
                App.getDocument(FreeCAD.ActiveDocument.Name).getObject('Sketch').addConstraint(Sketcher.Constraint('Vertical', 14))
                Gui.getDocument(FreeCAD.ActiveDocument.Name).resetEdit()
                App.ActiveDocument.recompute()
                ActiveSketch = App.getDocument(FreeCAD.ActiveDocument.Name).getObject('Sketch')
                tv = ActiveSketch.ViewObject.TempoVis
                if tv:
                    tv.restore()
                ActiveSketch.ViewObject.TempoVis = None
                del (tv)
                del (ActiveSketch)

                 # Gui.Selection.addSelection(FreeCAD.ActiveDocument.Name,'Body','Sketch.')
                App.getDocument(FreeCAD.ActiveDocument.Name).recompute()
                 ### Begin command PartDesign_Revolution
                App.getDocument(FreeCAD.ActiveDocument.Name).getObject('Body').newObject('PartDesign::Revolution', 'Revolution')
                App.getDocument(FreeCAD.ActiveDocument.Name).getObject('Revolution').Profile = App.getDocument(FreeCAD.ActiveDocument.Name).getObject(
                    'Sketch')
                App.getDocument(FreeCAD.ActiveDocument.Name).getObject('Revolution').ReferenceAxis = (
                App.getDocument(FreeCAD.ActiveDocument.Name).getObject('Sketch'), ['V_Axis'])
                App.getDocument(FreeCAD.ActiveDocument.Name).getObject('Revolution').Angle = 360.0
                App.getDocument(FreeCAD.ActiveDocument.Name).getObject('Sketch').Visibility = False
                App.ActiveDocument.recompute()
                App.getDocument(FreeCAD.ActiveDocument.Name).getObject('Revolution').ViewObject.ShapeColor = getattr(
                    App.getDocument(FreeCAD.ActiveDocument.Name).getObject('Body').getLinkedObject(True).ViewObject, 'ShapeColor',
                    App.getDocument(FreeCAD.ActiveDocument.Name).getObject('Revolution').ViewObject.ShapeColor)
                App.getDocument(FreeCAD.ActiveDocument.Name).getObject('Revolution').ViewObject.LineColor = getattr(
                    App.getDocument(FreeCAD.ActiveDocument.Name).getObject('Body').getLinkedObject(True).ViewObject, 'LineColor',
                    App.getDocument(FreeCAD.ActiveDocument.Name).getObject('Revolution').ViewObject.LineColor)
                App.getDocument(FreeCAD.ActiveDocument.Name).getObject('Revolution').ViewObject.PointColor = getattr(
                    App.getDocument(FreeCAD.ActiveDocument.Name).getObject('Body').getLinkedObject(True).ViewObject, 'PointColor',
                    App.getDocument(FreeCAD.ActiveDocument.Name).getObject('Revolution').ViewObject.PointColor)
                App.getDocument(FreeCAD.ActiveDocument.Name).getObject('Revolution').ViewObject.Transparency = getattr(
                    App.getDocument(FreeCAD.ActiveDocument.Name).getObject('Body').getLinkedObject(True).ViewObject, 'Transparency',
                    App.getDocument(FreeCAD.ActiveDocument.Name).getObject('Revolution').ViewObject.Transparency)
                App.getDocument(FreeCAD.ActiveDocument.Name).getObject('Revolution').ViewObject.DisplayMode = getattr(
                    App.getDocument(FreeCAD.ActiveDocument.Name).getObject('Body').getLinkedObject(True).ViewObject, 'DisplayMode',
                    App.getDocument(FreeCAD.ActiveDocument.Name).getObject('Revolution').ViewObject.DisplayMode)
                Gui.getDocument(FreeCAD.ActiveDocument.Name).setEdit(App.getDocument(FreeCAD.ActiveDocument.Name).getObject('Body'), 0, 'Revolution.')
                Gui.Selection.clearSelection()
                 ### End command PartDesign_Revolution
                 # Gui.Selection.clearSelection()
                 # Gui.Selection.addSelection(FreeCAD.ActiveDocument.Name,'Body','Origin.X_Axis.',-18.2134,0,0)
                App.getDocument(FreeCAD.ActiveDocument.Name).getObject('Sketch').Visibility = False
                App.getDocument(FreeCAD.ActiveDocument.Name).getObject('Revolution').Angle = 360.000000
                App.getDocument(FreeCAD.ActiveDocument.Name).getObject('Revolution').ReferenceAxis = (
                App.getDocument(FreeCAD.ActiveDocument.Name).getObject('X_Axis'), [''])
                App.getDocument(FreeCAD.ActiveDocument.Name).getObject('Revolution').Midplane = 0
                App.getDocument(FreeCAD.ActiveDocument.Name).getObject('Revolution').Reversed = 0
                App.getDocument(FreeCAD.ActiveDocument.Name).recompute()
                Gui.getDocument(FreeCAD.ActiveDocument.Name).resetEdit()



            if event == "-PRESSURE-" and values[1] == "Cylindrical":
                print(values)
                import FreeCADGui as Gui
                import Part
                import Sketcher
                Gui.runCommand('Std_Workbench', 23)
                Gui.runCommand('Std_ViewStatusBar', 1)
                Gui.runCommand('Std_ViewStatusBar', 0)
                with open('C:/Program Files/FreeCAD 0.19/data/Mod/Start/StartPage/LoadNew.py') as file:
                    exec(file.read())
                # App.setActiveDocument(FreeCAD.ActiveDocument.Name)
                # App.ActiveDocument=App.getDocument(FreeCAD.ActiveDocument.Name)
                # Gui.ActiveDocument=Gui.getDocument(FreeCAD.ActiveDocument.Name)
                Gui.runCommand('Std_OrthographicCamera', 1)
                ### Begin command Std_Workbench
                Gui.activateWorkbench("PartDesignWorkbench")
                ### End command Std_Workbench
                ### Begin command PartDesign_NewSketch
                import FreeCAD
                import FreeCAD as App
                App.getDocument(FreeCAD.ActiveDocument.Name).addObject('PartDesign::Body', 'Body')
                Gui.ActiveDocument.ActiveView.setActiveObject('pdbody', App.getDocument(FreeCAD.ActiveDocument.Name).getObject('Body'))
                ### End command PartDesign_NewSketch
                # Gui.Selection.addSelection(FreeCAD.ActiveDocument.Name,'Body','Origin.XZ_Plane.',-20.7326,-3.8743e-06,32.5)
                App.getDocument(FreeCAD.ActiveDocument.Name).getObject('Body').newObject('Sketcher::SketchObject', 'Sketch')
                App.getDocument(FreeCAD.ActiveDocument.Name).getObject('Sketch').Support = (
                App.getDocument(FreeCAD.ActiveDocument.Name).getObject('XZ_Plane'), [''])
                App.getDocument(FreeCAD.ActiveDocument.Name).getObject('Sketch').MapMode = 'FlatFace'
                App.ActiveDocument.recompute()
                Gui.getDocument(FreeCAD.ActiveDocument.Name).setEdit(App.getDocument(FreeCAD.ActiveDocument.Name).getObject('Body'), 0, 'Sketch.')
                import Show
                ActiveSketch = App.getDocument(FreeCAD.ActiveDocument.Name).getObject('Sketch')
                tv = Show.TempoVis(App.ActiveDocument, tag=ActiveSketch.ViewObject.TypeId)
                ActiveSketch.ViewObject.TempoVis = tv
                if ActiveSketch.ViewObject.EditingWorkbench:
                    tv.activateWorkbench(ActiveSketch.ViewObject.EditingWorkbench)
                if ActiveSketch.ViewObject.HideDependent:
                    tv.hide(tv.get_all_dependent(App.getDocument(FreeCAD.ActiveDocument.Name).getObject('Body'), 'Sketch.'))
                if ActiveSketch.ViewObject.ShowSupport:
                    tv.show([ref[0] for ref in ActiveSketch.Support if not ref[0].isDerivedFrom("PartDesign::Plane")])


                import PartDesignGui
                ActiveSketch = App.getDocument(FreeCAD.ActiveDocument.Name).getObject('Sketch')
                if ActiveSketch.ViewObject.RestoreCamera:
                    ActiveSketch.ViewObject.TempoVis.saveCamera()

                # Gui.Selection.clearSelection()
                Gui.runCommand('Sketcher_CompCreateArc', 0)
                App.getDocument(FreeCAD.ActiveDocument.Name).getObject('Sketch').addGeometry(
                    Part.ArcOfCircle(Part.Circle(App.Vector(-81.531532, -0.270265, 0), App.Vector(0, 0, 1), 36.216217),
                                     1.559169, 3.141593), False)
                App.getDocument(FreeCAD.ActiveDocument.Name).getObject('Sketch').addConstraint(Sketcher.Constraint('PointOnObject', 0, 3, -1))
                App.getDocument(FreeCAD.ActiveDocument.Name).getObject('Sketch').addConstraint(Sketcher.Constraint('PointOnObject', 0, 2, -1))
                App.getDocument(FreeCAD.ActiveDocument.Name).getObject('Sketch').addGeometry(
                    Part.ArcOfCircle(Part.Circle(App.Vector(-81.797661, -0.000000, 0), App.Vector(0, 0, 1), 34.329525),
                                     -4.715138, -3.133720), False)
                App.getDocument(FreeCAD.ActiveDocument.Name).getObject('Sketch').addConstraint(Sketcher.Constraint('Coincident', 1, 3, 0, 3))
                App.getDocument(FreeCAD.ActiveDocument.Name).getObject('Sketch').addConstraint(Sketcher.Constraint('PointOnObject', 1, 2, -1))
                Gui.runCommand('Sketcher_CreateLine', 0)
                App.getDocument(FreeCAD.ActiveDocument.Name).getObject('Sketch').addGeometry(
                    Part.LineSegment(App.Vector(-81.110443, 35.943523, 0), App.Vector(50.540543, 35.945953, 0)), False)
                App.getDocument(FreeCAD.ActiveDocument.Name).getObject('Sketch').addConstraint(Sketcher.Constraint('Coincident', 2, 1, 0, 1))
                App.getDocument(FreeCAD.ActiveDocument.Name).getObject('Sketch').addConstraint(Sketcher.Constraint('Horizontal', 2))
                App.getDocument(FreeCAD.ActiveDocument.Name).getObject('Sketch').addGeometry(
                    Part.LineSegment(App.Vector(-81.703285, 34.327274, 0), App.Vector(50.900913, 34.144150, 0)), False)
                App.getDocument(FreeCAD.ActiveDocument.Name).getObject('Sketch').addConstraint(Sketcher.Constraint('Coincident', 3, 1, 1, 1))
                App.getDocument(FreeCAD.ActiveDocument.Name).getObject('Sketch').addConstraint(Sketcher.Constraint('Horizontal', 3))
                Gui.runCommand('Sketcher_CompCreateArc', 0)
                App.getDocument(FreeCAD.ActiveDocument.Name).getObject('Sketch').addGeometry(
                    Part.ArcOfCircle(Part.Circle(App.Vector(51.801800, -0.270265, 0), App.Vector(0, 0, 1), 36.235749),
                                     -0.004566, 1.605610), False)
                App.getDocument(FreeCAD.ActiveDocument.Name).getObject('Sketch').addConstraint(Sketcher.Constraint('PointOnObject', 4, 3, -1))
                App.getDocument(FreeCAD.ActiveDocument.Name).getObject('Sketch').addConstraint(Sketcher.Constraint('Coincident', 4, 2, 2, 2))
                App.getDocument(FreeCAD.ActiveDocument.Name).getObject('Sketch').addConstraint(Sketcher.Constraint('PointOnObject', 4, 1, -1))
                App.getDocument(FreeCAD.ActiveDocument.Name).getObject('Sketch').addGeometry(
                    Part.ArcOfCircle(Part.Circle(App.Vector(52.061485, -0.000000, 0), App.Vector(0, 0, 1), 34.346891),
                                     -0.009642, 1.604592), False)
                App.getDocument(App.ActiveDocument.Name).getObject('Sketch').addConstraint(
                    Sketcher.Constraint('DistanceY', 1, 2, 1, 3, 7.798736))
                App.getDocument(App.ActiveDocument.Name).getObject('Sketch').setDatum(5, App.Units.Quantity('0.000000 mm'))
                App.getDocument(FreeCAD.ActiveDocument.Name).getObject('Sketch').addConstraint(Sketcher.Constraint('Coincident', 5, 3, 4, 3))
                App.getDocument(FreeCAD.ActiveDocument.Name).getObject('Sketch').addConstraint(Sketcher.Constraint('Coincident', 5, 2, 3, 2))
                App.getDocument(FreeCAD.ActiveDocument.Name).getObject('Sketch').addConstraint(Sketcher.Constraint('PointOnObject', 5, 1, -1))
                # Gui.Selection.addSelection(FreeCAD.ActiveDocument.Name,'Body','Sketch.Edge1',-101.055,-0.00800361,30.266,False)
                # Gui.Selection.addSelection(FreeCAD.ActiveDocument.Name,'Body','Sketch.Edge3',-69.8198,-0.00800429,35.9435,False)
                ### Begin command Sketcher_ConstrainTangent
                App.getDocument(FreeCAD.ActiveDocument.Name).getObject('Sketch').addConstraint(Sketcher.Constraint('Tangent', 2, 1, 0, 1))
                App.getDocument(FreeCAD.ActiveDocument.Name).getObject('Sketch').delConstraintOnPoint(2, 1)
                ### End command Sketcher_ConstrainTangent
                # Gui.Selection.clearSelection()
                # Gui.Selection.addSelection(FreeCAD.ActiveDocument.Name,'Body','Sketch.Edge3',46.2162,-0.00800437,36.6372,False)
                # Gui.Selection.addSelection(FreeCAD.ActiveDocument.Name,'Body','Sketch.Edge5',56.5865,-0.00800432,36.2159,False)
                ### Begin command Sketcher_ConstrainTangent
                App.getDocument(FreeCAD.ActiveDocument.Name).getObject('Sketch').addConstraint(Sketcher.Constraint('Tangent', 4, 2, 2, 2))
                App.getDocument(FreeCAD.ActiveDocument.Name).getObject('Sketch').delConstraintOnPoint(4, 2)
                ### End command Sketcher_ConstrainTangent
                # Gui.Selection.clearSelection()
                # Gui.Selection.addSelection(FreeCAD.ActiveDocument.Name,'Body','Sketch.Edge2',-99.8549,-0.0080034,28.4791,False)
                # Gui.Selection.addSelection(FreeCAD.ActiveDocument.Name,'Body','Sketch.Edge4',-71.6216,-0.00800409,34.3273,False)
                ### Begin command Sketcher_ConstrainTangent
                App.getDocument(FreeCAD.ActiveDocument.Name).getObject('Sketch').addConstraint(Sketcher.Constraint('Tangent', 3, 1, 1, 1))
                App.getDocument(FreeCAD.ActiveDocument.Name).getObject('Sketch').delConstraintOnPoint(3, 1)
                ### End command Sketcher_ConstrainTangent
                # Gui.Selection.clearSelection()
                App.getDocument(FreeCAD.ActiveDocument.Name).getObject('Sketch').movePoint(3, 0, App.Vector(0.000000, 0.540539, 0), 1)
                # Gui.Selection.addSelection(FreeCAD.ActiveDocument.Name,'Body','Sketch.Edge4',47.2973,-0.00800416,34.864,False)
                # Gui.Selection.addSelection(FreeCAD.ActiveDocument.Name,'Body','Sketch.Edge6',54.4961,-0.00800412,34.5787,False)
                ### Begin command Sketcher_ConstrainTangent
                App.getDocument(FreeCAD.ActiveDocument.Name).getObject('Sketch').addConstraint(Sketcher.Constraint('Tangent', 5, 2, 3, 2))
                App.getDocument(FreeCAD.ActiveDocument.Name).getObject('Sketch').delConstraintOnPoint(5, 2)
                ### End command Sketcher_ConstrainTangent
                # Gui.Selection.clearSelection()
                Gui.runCommand('Sketcher_CreateLine', 0)
                App.getDocument(FreeCAD.ActiveDocument.Name).getObject('Sketch').addGeometry(
                    Part.LineSegment(App.Vector(-118.311935, -0.000000, 0), App.Vector(-115.651421, -0.000000, 0)), False)
                App.getDocument(FreeCAD.ActiveDocument.Name).getObject('Sketch').addConstraint(Sketcher.Constraint('Coincident', 6, 1, 0, 2))
                App.getDocument(FreeCAD.ActiveDocument.Name).getObject('Sketch').addConstraint(Sketcher.Constraint('Coincident', 6, 2, 1, 2))
                Gui.runCommand('Sketcher_CreateLine', 0)
                App.getDocument(FreeCAD.ActiveDocument.Name).getObject('Sketch').addGeometry(
                    Part.LineSegment(App.Vector(85.264854, -0.000000, 0), App.Vector(87.925369, -0.000000, 0)), False)
                App.getDocument(FreeCAD.ActiveDocument.Name).getObject('Sketch').addConstraint(Sketcher.Constraint('Coincident', 7, 1, 5, 1))
                App.getDocument(FreeCAD.ActiveDocument.Name).getObject('Sketch').addConstraint(Sketcher.Constraint('Coincident', 7, 2, 4, 1))
                App.getDocument(FreeCAD.ActiveDocument.Name).getObject('Sketch').addConstraint(Sketcher.Constraint('Horizontal', 7))
                Gui.runCommand('Sketcher_SelectRedundantConstraints', 0)
                # Gui.Selection.addSelection(FreeCAD.ActiveDocument.Name,'Body','Sketch.Constraint19')
                # Gui.Selection.clearSelection()
                App.getDocument(FreeCAD.ActiveDocument.Name).getObject('Sketch').delConstraint(18)
                Gui.getDocument(FreeCAD.ActiveDocument.Name).resetEdit()
                App.ActiveDocument.recompute()
                ActiveSketch = App.getDocument(FreeCAD.ActiveDocument.Name).getObject('Sketch')


                # Gui.Selection.addSelection(FreeCAD.ActiveDocument.Name,'Body','Sketch.')
                App.getDocument(FreeCAD.ActiveDocument.Name).recompute()
                ### Begin command PartDesign_Revolution
                App.getDocument(FreeCAD.ActiveDocument.Name).getObject('Body').newObject('PartDesign::Revolution', 'Revolution')
                App.getDocument(FreeCAD.ActiveDocument.Name).getObject('Revolution').Profile = App.getDocument(FreeCAD.ActiveDocument.Name).getObject('Sketch')
                App.getDocument(FreeCAD.ActiveDocument.Name).getObject('Revolution').ReferenceAxis = (
                App.getDocument(FreeCAD.ActiveDocument.Name).getObject('Sketch'), ['V_Axis'])
                App.getDocument(FreeCAD.ActiveDocument.Name).getObject('Revolution').Angle = 360.0
                App.getDocument(FreeCAD.ActiveDocument.Name).getObject('Sketch').Visibility = False
                App.ActiveDocument.recompute()
                App.getDocument(FreeCAD.ActiveDocument.Name).getObject('Revolution').ViewObject.ShapeColor = getattr(
                    App.getDocument(FreeCAD.ActiveDocument.Name).getObject('Body').getLinkedObject(True).ViewObject, 'ShapeColor',
                    App.getDocument(FreeCAD.ActiveDocument.Name).getObject('Revolution').ViewObject.ShapeColor)
                App.getDocument(FreeCAD.ActiveDocument.Name).getObject('Revolution').ViewObject.LineColor = getattr(
                    App.getDocument(FreeCAD.ActiveDocument.Name).getObject('Body').getLinkedObject(True).ViewObject, 'LineColor',
                    App.getDocument(FreeCAD.ActiveDocument.Name).getObject('Revolution').ViewObject.LineColor)
                App.getDocument(FreeCAD.ActiveDocument.Name).getObject('Revolution').ViewObject.PointColor = getattr(
                    App.getDocument(FreeCAD.ActiveDocument.Name).getObject('Body').getLinkedObject(True).ViewObject, 'PointColor',
                    App.getDocument(FreeCAD.ActiveDocument.Name).getObject('Revolution').ViewObject.PointColor)
                App.getDocument(FreeCAD.ActiveDocument.Name).getObject('Revolution').ViewObject.Transparency = getattr(
                    App.getDocument(FreeCAD.ActiveDocument.Name).getObject('Body').getLinkedObject(True).ViewObject, 'Transparency',
                    App.getDocument(FreeCAD.ActiveDocument.Name).getObject('Revolution').ViewObject.Transparency)
                App.getDocument(FreeCAD.ActiveDocument.Name).getObject('Revolution').ViewObject.DisplayMode = getattr(
                    App.getDocument(FreeCAD.ActiveDocument.Name).getObject('Body').getLinkedObject(True).ViewObject, 'DisplayMode',
                    App.getDocument(FreeCAD.ActiveDocument.Name).getObject('Revolution').ViewObject.DisplayMode)
                Gui.getDocument(FreeCAD.ActiveDocument.Name).setEdit(App.getDocument(FreeCAD.ActiveDocument.Name).getObject('Body'), 0, 'Revolution.')
                Gui.Selection.clearSelection()
                ### End command PartDesign_Revolution
                # Gui.Selection.clearSelection()
                # Gui.Selection.addSelection(FreeCAD.ActiveDocument.Name,'Body','Origin.X_Axis.',11.6697,0,0)
                App.getDocument(FreeCAD.ActiveDocument.Name).getObject('Sketch').Visibility = False
                App.getDocument(FreeCAD.ActiveDocument.Name).getObject('Revolution').Angle = 360.000000
                App.getDocument(FreeCAD.ActiveDocument.Name).getObject('Revolution').ReferenceAxis = (
                App.getDocument(FreeCAD.ActiveDocument.Name).getObject('X_Axis'), [''])
                App.getDocument(FreeCAD.ActiveDocument.Name).getObject('Revolution').Midplane = 0
                App.getDocument(FreeCAD.ActiveDocument.Name).getObject('Revolution').Reversed = 0
                App.getDocument(FreeCAD.ActiveDocument.Name).recompute()
                Gui.getDocument(FreeCAD.ActiveDocument.Name).resetEdit()

            if event == "-LIQUID-":
                # Delta v depends on structural and fuel mass
                # Fuel mass depends on
                # Structural mass depends on fuel mass, fuel volume, payload mass, payload volume, engine thrust
                # Engine thrust depends on structural/fuel/payload mass i.e. a = F/m acceleration must be greater than 9.81 m/s2
                layout = [
                    [sg.Text('Select Fuel'), sg.InputCombo(('Liquid Hydrogen', 'Liquid Methane', 'Liquid Kerosene'))],
                    [sg.Text('Select Oxidizer'),sg.InputCombo(('Liquid Oxygen', ''))],
                    [sg.Text('Set Oxidizer/Fuel (Mixture) Ratio'),sg.InputText(size=(10,8)), sg.Checkbox('Optimize to Max Specific Impulse', default=True)],
                    [sg.Text('Set Chamber Pressure (pascals)'),sg.InputText(size=(10,8))],
                    [sg.Text('Set Altitude (meters)'),sg.InputText(size=(10,8))],
                    [sg.Text('Set Expansion Ratio (5<Ar<50)'),sg.InputText(size=(10,8))],
                    [sg.Text('Set Throat Diameter',key="-THROATDIA-"), sg.InputText(size=(10, 8))],
                    [sg.Text('Set Exit Diameter', key="-EXITDIA-"),sg.InputText(size=(10,8))],
                    [sg.Button('OK'), sg.Cancel()]]
                window = sg.Window('Stage Designer', layout, default_element_size=(55, 1), grab_anywhere=False)

                event, values = window.read()

                if event == "Cancel":
                    window.close()
                    pass
                else:
                    # window.close()
                    from pygasflow.nozzles import CD_TOP_Nozzle, CD_Conical_Nozzle, CD_Min_Length_Nozzle
                    from pygasflow.utils import Ideal_Gas, Flow_State
                    from pygasflow.solvers import De_Laval_Solver
                    import numpy as np
                    import math
                    import matplotlib.pyplot as plt
                    import matplotlib.patches as patches

                    # Initialize air as the gas to use in the nozzle
                    gas = Ideal_Gas(287, 1.4)

                    Fuel = values[0]
                    Oxidizer = values[1]
                    OFRatio = float(values[2])

                    if Fuel == "Liquid Hydrogen" and Oxidizer == "Liquid Oxygen":
                        t0 = 3552.778  # Kelvin
                        MolMass = 10
                        v_etheoretical = 4425.696  # Meters/sec
                        FuelDens = 71
                        OxDens = 1142
                    elif Fuel == 'Liquid Kerosene' and Oxidizer == "Liquid Oxygen":
                        t0 = 3672.222  # Kelvin
                        MolMass = 23.3
                        v_etheoretical = 3465.576  # Meters/sec
                        FuelDens = 810
                        OxDens = 1142
                    elif Fuel == "MMH" and Oxidizer == "N2O4":
                        t0 = 3388.889  # Kelvin
                        MolMass = 21.5
                        v_etheoretical = 3297.936  # Meters/sec
                        FuelDens = 878
                        OxDens = 1440
                    elif Fuel == "N2H4":
                        t0 = 1227.778  # Kelvin
                        MolMass = 13
                        v_etheoretical = 2325.624  # Meters/sec
                        FuelDens = 1010
                    elif Fuel == "He":
                        t0 = 288.889
                        MolMass = 4
                        v_etheoretical = 1551.432  # Meters/sec
                    elif Fuel == "N2":
                        t0 = 288.889
                        MolMass = 28
                        v_etheoretical = 667.512  # Meters/sec

                    # sqrttcdivm = math.sqrt(t0 / MolMass)

                    p0 = float(values[4]) # stagnation condition
                    h = float(values[5])  # meters
                    expratio = float(values[6])

                    Ri = 0.4
                    Ai = math.pi * (Ri ** 2)
                    Rt = 0.2
                    At = math.pi * (Rt ** 2)
                    Ae = At * expratio
                    Re = math.sqrt((Ae / math.pi))

                    # How do you optimize for altitude?

                    # for alt in range(0, 110):
                    #     h = alt*1000
                    #     # h is meters alt

                    upstream_state = Flow_State(p0=p0, t0=t0)

                    from ambiance import Atmosphere


                    sealevel = Atmosphere(h)
                    Tinf = sealevel.temperature
                    Pinf = sealevel.pressure
                    d = sealevel.density
                    a = sealevel.speed_of_sound
                    mu = sealevel.dynamic_viscosity  # Verify that mu is in fact dynamic and not kinematic viscosity
                    # Tinf, Pinf, d, a, mu = isa.calculate_at_h(h, atmosphere)

                    Pb_P0_ratio = Pinf / p0

                    # half cone angle of the divergent
                    theta_c = 40
                    # half cone angle of the convergent
                    theta_N = 15

                    # Junction radius between the convergent and divergent
                    Rbt = 0.75 * Rt
                    # Junction radius between the "combustion chamber" and convergent
                    Rbc = 1.5 * Rt
                    # Fractional Length of the TOP nozzle with respect to a same exit
                    # area ratio conical nozzle with 15 deg half-cone angle.
                    K = 0.8
                    # geometry type
                    geom = "axisymmetric"

                    geom_con = CD_Conical_Nozzle(
                        Ri,  # Inlet radius
                        Re,  # Exit (outlet) radius
                        Rt,  # Throat radius
                        Rbt,  # Junction radius ratio at the throat (between the convergent and divergent)
                        Rbc,  # Junction radius ratio between the "combustion chamber" and convergent
                        theta_c,  # Half angle [degrees] of the convergent.
                        theta_N,  # Half angle [degrees] of the conical divergent.
                        geom,  # Geometry type
                        1000  # Number of discretization points along the total length of the nozzle
                    )

                    geom_top = CD_TOP_Nozzle(
                        Ri,  # Inlet radius
                        Re,  # Exit (outlet) radius
                        Rt,  # Throat radius
                        Rbc,  # Junction radius ratio between the "combustion chamber" and convergent
                        theta_c,  # Half angle [degrees] of the convergent.
                        K,  # Fractional Length of the nozzle
                        geom,  # Geometry type
                        1000  # Number of discretization points along the total length of the nozzle
                    )

                    n = 15
                    gamma = gas.gamma

                    geom_moc = CD_Min_Length_Nozzle(
                        Ri,  # Inlet radius
                        Re,  # Exit (outlet) radius
                        Rt,  # Throat radius
                        Rbt,  # Junction radius ratio at the throat (between the convergent and divergent)
                        Rbc,  # Junction radius ratio between the "combustion chamber" and convergent
                        theta_c,  # Half angle [degrees] of the convergent.
                        n,  # number of characteristics lines
                        gamma  # Specific heat ratio
                    )

                    # Initialize the nozzle
                    nozzle_conical = De_Laval_Solver(gas, geom_con, upstream_state)
                    nozzle_top = De_Laval_Solver(gas, geom_top, upstream_state)
                    nozzle_moc = De_Laval_Solver(gas, geom_moc, upstream_state)
                    # print(nozzle_conical)
                    NozzleChars = str(nozzle_conical)
                    NozzleChars = NozzleChars.replace("\n", "")
                    # NozzleChars = NozzleChars.replace("\t", "")

                    NozzleChars = NozzleChars.split(":")

                    for item in NozzleChars:
                        if item.find("T*") > 0:
                            item = item.replace("Important Pressure Ratios", "")
                            criticalquantities = item.split("\t")
                            criticalquantities = criticalquantities[1:]

                        if item.find("r1") > 0:
                            item = item.replace("Flow Condition", "")
                            pressureratios = item.split("\t")
                            pressureratios = pressureratios[1:]

                    Tstar = float(criticalquantities[1])
                    Pstar = float(criticalquantities[3])
                    Rhostar = float(criticalquantities[5])
                    ustar = float(criticalquantities[7])

                    mdot = Rhostar * ustar * At

                    r1 = float(pressureratios[1])
                    r2 = float(pressureratios[3])
                    r3 = float(pressureratios[5])

                    # Assuming perfectly expanded ******
                    print(Pb_P0_ratio)
                    print(gamma)
                    print(MolMass)
                    print(t0)
                    U_e = math.sqrt(((1 - ((Pb_P0_ratio) ** ((gamma - 1) / gamma))) * 2 * gamma * (8314 / MolMass) * t0) / (gamma - 1))

                    mdotfuel = mdot / (1 + OFRatio)
                    mdotox = mdot - mdotfuel


                    def Plot_Nozzle(geom, L, A, M, P, rho, T, flow_condition, Asw_At_ratio, title):
                        fig, ax = plt.subplots(nrows=4, sharex=True)
                        fig.set_size_inches(8, 10)
                        radius_nozzle, radius_container = geom.get_points(False)
                        ar_nozzle, ar_container = geom.get_points(True)
                        # nozzle geometry
                        ax[0].add_patch(patches.Polygon(radius_container, facecolor="0.85", hatch="///", edgecolor="0.4", linewidth=0.5))
                        ax[0].add_patch(patches.Polygon(radius_nozzle, facecolor='#b7e1ff', edgecolor="0.4", linewidth=1))
                        ax[0].set_ylim(0, max(radius_container[:, 1]))
                        ax[0].set_ylabel("r [m]")
                        ax[0].set_title(title + flow_condition)

                        ax[1].add_patch(patches.Polygon(ar_container, facecolor="0.85", hatch="///", edgecolor="0.4", linewidth=0.5))
                        ax[1].add_patch(patches.Polygon(ar_nozzle, facecolor='#b7e1ff', edgecolor="0.4", linewidth=1))
                        ax[1].set_ylim(0, max(ar_container[:, 1]))
                        ax[1].set_ylabel("$A/A^{*}$")

                        # draw the shock wave if present in the nozzle
                        if Asw_At_ratio:
                            # get shock wave location in the divergent
                            x = geom.location_divergent_from_area_ratio(Asw_At_ratio)
                            rsw = np.sqrt((Asw_At_ratio * geom.critical_area) / np.pi)
                            ax[0].plot([x, x], [0, rsw], 'r')
                            ax[1].plot([x, x], [0, Asw_At_ratio], 'r')
                            ax[0].text(x, rsw + 0.5 * (max(radius_container[:, 1]) - max(radius_nozzle[:, -1])),
                                       "SW",
                                       color="r",
                                       ha='center',
                                       va="center",
                                       bbox=dict(boxstyle="round", fc="white", lw=0, alpha=0.85),
                                       )
                            ax[1].text(x, Asw_At_ratio + 0.5 * (max(ar_container[:, 1]) - max(ar_nozzle[:, -1])),
                                       "SW",
                                       color="r",
                                       ha='center',
                                       va="center",
                                       bbox=dict(boxstyle="round", fc="white", lw=0, alpha=0.85),
                                       )

                        # mach number
                        ax[2].plot(L, M)
                        ax[2].set_ylim(0)
                        ax[2].grid()
                        ax[2].set_ylabel("M")

                        # ratios
                        ax[3].plot(L, P, label="$P/P_{0}$")
                        ax[3].plot(L, rho, label=r"$\rho/\rho_{0}$")
                        ax[3].plot(L, T, label="$T/T_{0}$")
                        ax[3].set_xlim(min(ar_container[:, 0]), max(ar_container[:, 0]))
                        ax[3].set_ylim(0, 1)
                        ax[3].legend(loc="lower left")
                        ax[3].grid()
                        ax[3].set_xlabel("L [m]")
                        ax[3].set_ylabel("ratios")
                        with open(SCDesignerPath + "\\RocketNozzlePoints.txt", "w+") as r:
                            for q in range(0, len(radius_nozzle)):
                                if radius_nozzle[q][1] < 0:
                                    turnaround = q - 1
                                    break
                                r.write(str(round(radius_nozzle[q][0], 4)) + "," + str(round(radius_nozzle[q][1], 4)) + ",0\n")
                            for s in range(turnaround, 0, -1):
                                r.write(str(round((radius_nozzle[s][0]), 4)) + "," + str(round(radius_nozzle[s][1] + 0.1, 4)) + ",0\n")
                            r.write(str(round((radius_nozzle[0][0]), 4)) + "," + str(round(radius_nozzle[0][1], 4)) + ",0\n")
                        r.close()

                        r.close()
                        plt.tight_layout()
                        plt.show()



                    # L1, A1, M1, P1, rho1, T1, flow_condition1, Asw_At_ratio1 = nozzle_conical.compute(Pb_P0_ratio)
                    L2, A2, M2, P2, rho2, T2, flow_condition2, Asw_At_ratio2 = nozzle_top.compute(Pb_P0_ratio)
                    # L3, A3, M3, P3, rho3, T3, flow_condition3, Asw_At_ratio3 = nozzle_moc.compute(Pb_P0_ratio)

                    # Plot_Nozzle(geom_con, L1, A1, M1, P1, rho1, T1, flow_condition1, Asw_At_ratio1, "Conical Nozzle: ")
                    # Plot_Nozzle(geom_moc, L3, A3, M3, P3, rho3, T3, flow_condition3, Asw_At_ratio3, "MOC Nozzle: ")

                    plot = 0
                    title = "TOP Nozzle at " + str(h) + " meters: "
                    Plot_Nozzle(geom_top, L2, A2, M2, P2, rho2, T2, flow_condition2, Asw_At_ratio2, title)




                # PID DESIGNER


                # def addComp(Component, g, location):
                #     with open(SCDesignerPath + "\\PROPULSION\\P_ID\\" + Component + ".png", "rb") as image:
                #         f = image.read()
                #         data = bytearray(f)
                #     data = bytes(data)
                #     g.draw_image(data=data, location=location)
                #
                # def connect(Upstream, Downstream, upstreamloc, downstreamloc, g, allines, color):
                #     if Upstream == "CylTank":
                #         upstreamoffset = [18, 160]
                #     if Upstream == "RegenEngine":
                #         upstreamoffset = [43, 26]
                #     if Upstream == "Preburner":
                #         upstreamoffset = [17, 3]
                #     if Upstream == "PumpL":
                #         upstreamoffset = [15, 72]
                #     if Upstream == "PumpR":
                #         upstreamoffset = [5, 72]
                #     if Upstream == "Turbine":
                #         upstreamoffset = [0, 40]
                #     if Downstream == "Preburner":
                #         downstreamoffset = [33, 39]
                #     if Downstream == "PumpL":
                #         downstreamoffset = [0, 35]
                #     if Downstream == "PumpR":
                #         downstreamoffset = [20, 35]
                #     if Downstream == "RegenEngine":
                #         downstreamoffset = [12, 26]
                #     if Downstream == "Turbine":
                #         downstreamoffset = [12, 64]
                #     if Downstream == "Engine":
                #         downstreamoffset = [25, 7]
                #     upstreamoutlet = [upstreamoffset[0] + upstreamloc[0], upstreamoffset[1] + upstreamloc[1]]
                #     downstreaminlet = [downstreamoffset[0] + downstreamloc[0], downstreamoffset[1] + downstreamloc[1]]
                #     allines.append(
                #         g.DrawLine(tuple(upstreamoutlet), tuple([upstreamoutlet[0], downstreaminlet[1]]), width=3,
                #                    color=color))
                #     allines.append(
                #         g.DrawLine(tuple([upstreamoutlet[0], downstreaminlet[1]]), tuple(downstreaminlet), width=3,
                #                    color=color))
                #

                #
                # col = [[sg.T('Place Component', enable_events=True)],
                #        [sg.B('Piping', key='-PIPING-', size=(12, 1), enable_events=True)],
                #        [sg.B('Valve', key='-VALVE-', button_color=('black', 'white'), size=(12, 1),
                #              enable_events=True)],
                #        [sg.B('Tank', key='-TANK-', size=(12, 1), enable_events=True)],
                #        [sg.B('Pump', key='-PUMP-', button_color=('black', 'white'), size=(12, 1), enable_events=True)],
                #        [sg.B('Turbine', key='-TURBINE-', size=(12, 1), enable_events=True)],
                #        [sg.B('Engine', key='-ENGINE-', button_color=('black', 'white'), size=(12, 1),
                #              enable_events=True)],
                #        [sg.B('Sensor', key='-SENSOR-', size=(12, 1), enable_events=True)],
                #        [sg.B('Filter', key='-FILTER-', button_color=('black', 'white'), size=(12, 1),
                #              enable_events=True)],
                #        [sg.B('Pres. Reg.', key='-CONTROLLER-', size=(12, 1), enable_events=True)],
                #        [sg.B('Engine Cycle', key='-CYCLE-', size=(12, 1), enable_events=True)],
                #        [sg.B('Add Text', key='-ADDT-', button_color=('black', 'white'), size=(12, 1),
                #              enable_events=True)],
                #        [sg.B('Clear Sheet', key='-CLEAR-', size=(12, 1), enable_events=True)],
                #        [sg.B('Erase Object', key='-ERASE-', size=(12, 1), enable_events=True)],
                #        [sg.B('Move', key='-MOVE-', button_color=('black', 'white'), size=(12, 1), enable_events=True)],
                #
                #        ]
                #
                # layout = [
                #     [sg.Graph((1300, 660), (0, 450), (450, 0), key='-GRAPH-',
                #               change_submits=True, drag_submits=True, background_color="white"), sg.Col(col)],
                #     [sg.Button('Export to PDF'), sg.Button('Exit')]
                # ]
                #
                # window = sg.Window('Piping and Instrumentation (P&ID) Designer', layout, finalize=True)
                # g = window['-GRAPH-']  # type: sg.Graph
                #
                # xarr = []
                # yarr = []
                # eventarr = []
                # allines = []
                # dragging = False
                # piping = 1
                # erase = 0
                # start_point = end_point = prior_rect = None
                # while True:
                #     event, values = window.read()
                #     if event is None:
                #         break  # exit
                #     eventarr.append(event)
                #     if event is None:
                #         break  # exit
                #     if event == "-GRAPH-":
                #         x, y = values["-GRAPH-"]
                #
                #         xarr.append(x)
                #         yarr.append(y)
                #
                #         if piping == 1 and erase == 0:
                #             # piping = 1
                #             if len(xarr) > 1:
                #                 if abs(xarr[-2] - xarr[-1]) > abs(yarr[-2] - yarr[-1]):
                #                     line = g.DrawLine((xarr[-2], yarr[-2]), (xarr[-1], yarr[-2]), width=2)
                #                     yarr[-1] = yarr[-2]
                #                 else:
                #                     line = g.DrawLine((xarr[-2], yarr[-2]), (xarr[-2], yarr[-1]), width=2)
                #                     xarr[-1] = xarr[-2]
                #
                #         if piping == 0 and erase == 0:
                #             if not dragging:
                #                 start_point = (x, y)
                #                 dragging = True
                #                 drag_figures = g.get_figures_at_location((x, y))
                #                 lastxy = x, y
                #             else:
                #                 end_point = (x, y)
                #             delta_x, delta_y = x - lastxy[0], y - lastxy[1]
                #             lastxy = x, y
                #             if None not in (start_point, end_point):
                #                 for fig in drag_figures:
                #                     # fig = drag_figures[-1]
                #                     g.move_figure(fig, delta_x, delta_y)
                #                     g.update()
                #
                #         if piping == 0 and erase == 1:
                #             drag_figures = g.get_figures_at_location((x, y))
                #             for figure in drag_figures:
                #                 g.delete_figure(figure)
                #
                #     if event == "-MOVE-":
                #         piping = 0
                #     if event == "-PIPING-":
                #         piping = 1
                #         erase = 0
                #     if event == "-ERASE-":
                #         erase = 1
                #         piping = 0
                #     if event == "-VALVE-":
                #         layout1 = [
                #             [sg.Listbox(values=(
                #                 'Angle valve', 'Check valve', 'Diaphragm valve', 'Ball valve', 'Butterfly valve',
                #                 'Gate valve', 'Plug valve', 'Relief valve', 'Rotary valve', 'Solenoid, 2-way',
                #                 'Solenoid, 3-way', 'Solenoid, 4-way',
                #                 'Solenoid, 5-way'), size=(40, 20)),
                #                 sg.Image(SCDesignerPath + '\\PROPULSION\\P_ID\\Valves\\Images\\Blank.png', size=(1, 1),
                #                          key='-IMAGE-')],
                #             [sg.Radio('Fail Open', "RADIO1", default=True, size=(10, 1)),
                #              sg.Radio('Fail Closed', "RADIO1"),
                #              sg.Button('Show Valve Image')],
                #             [sg.Radio('Hand Operated', "RADIO2"), sg.Radio('Hydraulic', "RADIO2"),
                #              sg.Radio('Pneumatic', "RADIO2"), sg.Radio('Electrically actuated', "RADIO2")],
                #             [sg.Submit(tooltip='Submit'), sg.Cancel()]]
                #
                #         window1 = sg.Window('Select a valve type', layout1, grab_anywhere=False)
                #         while True:
                #             action, event1 = window1.read()
                #             if action == "Show Valve Image":
                #                 valvetype = event1[0][0]
                #                 if valvetype == "Angle valve":
                #                     window1.Element('-IMAGE-').Update(
                #                         SCDesignerPath + '\\PROPULSION\\P_ID\\Valves\\Images\\Angle.png')
                #                 elif valvetype == "Check valve":
                #                     window1.Element('-IMAGE-').Update(
                #                         SCDesignerPath + '\\PROPULSION\\P_ID\\Valves\\Images\\SwingCheck.png')
                #                 elif valvetype == "Diaphragm valve":
                #                     window1.Element('-IMAGE-').Update(
                #                         SCDesignerPath + '\\PROPULSION\\P_ID\\Valves\\Images\\Diaphragm.png')
                #                 elif valvetype == "Ball valve":
                #                     window1.Element('-IMAGE-').Update(
                #                         SCDesignerPath + '\\PROPULSION\\P_ID\\Valves\\Images\\TrunnionBall.png')
                #                 elif valvetype == "Butterfly valve":
                #                     window1.Element('-IMAGE-').Update(
                #                         SCDesignerPath + '\\PROPULSION\\P_ID\\Valves\\Images\\Butterfly.png')
                #                 elif valvetype == "Gate valve":
                #                     window1.Element('-IMAGE-').Update(
                #                         SCDesignerPath + '\\PROPULSION\\P_ID\\Valves\\Images\\Gate.png')
                #                 elif valvetype == "Plug valve":
                #                     window1.Element('-IMAGE-').Update(
                #                         SCDesignerPath + '\\PROPULSION\\P_ID\\Valves\\Images\\Plug.png')
                #                 # elif valvetype == "Solenoid 2-way"
                #
                #             if action == "Submit":
                #                 valvetype = event1[0][0]
                #                 window1.close()
                #                 if valvetype == "Ball valve":
                #                     with open(SCDesignerPath + "\\PROPULSION\\P_ID\\Valves\\HandOpGlobe.png",
                #                               "rb") as image:
                #                         f = image.read()
                #                         data = bytearray(f)
                #                     data = bytes(data)
                #                     g.draw_image(data=data, location=(25, 25))
                #             if action == "Cancel":
                #                 window1.close()
                #                 break
                #
                #     if event == "-TANK-":
                #         layout1 = [
                #             [sg.Listbox(values=(
                #                 'Spherical Tank', 'Cylindrical Tank'),
                #                 size=(40, 3))],
                #             [sg.Submit(tooltip='Submit'), sg.Cancel()]]
                #
                #         window1 = sg.Window('Tank Type', layout1, grab_anywhere=False)
                #
                #         action, event1 = window1.read()
                #         TankType = event1[0][0]
                #
                #         if action == "Submit":
                #             window1.close()
                #         if TankType == 'Cylindrical Tank':
                #             with open(SCDesignerPath + "\\PROPULSION\\P_ID\\TankCylBlue.png", "rb") as image:
                #                 f = image.read()
                #                 data = bytearray(f)
                #             data = bytes(data)
                #             g.draw_image(data=data, location=(25, 25))
                #         if TankType == 'Spherical Tank':
                #             with open(SCDesignerPath + "\\PROPULSION\\P_ID\\TankSpRed.png", "rb") as image:
                #                 f = image.read()
                #                 data = bytearray(f)
                #             data = bytes(data)
                #             g.draw_image(data=data, location=(25, 25))
                #
                #     if event == "-TURBINE-":
                #         with open(SCDesignerPath + "\\PROPULSION\\P_ID\\Turbine.png", "rb") as image:
                #             f = image.read()
                #             data = bytearray(f)
                #         data = bytes(data)
                #         g.draw_image(data=data, location=(20, 20))
                #
                #     if event == "-PUMP-":
                #         with open(SCDesignerPath + "\\PROPULSION\\P_ID\\Pump.png", "rb") as image:
                #             f = image.read()
                #             data = bytearray(f)
                #         data = bytes(data)
                #         g.draw_image(data=data, location=(20, 20))
                #     if event == "-CLEAR-":
                #         g.erase()
                #     if event == "-ENGINE-":
                #         with open(SCDesignerPath + "\\PROPULSION\\P_ID\\Engine.png", "rb") as image:
                #             f = image.read()
                #             data = bytearray(f)
                #         data = bytes(data)
                #         g.draw_image(data=data, location=(200, 200))
                #     if event == "-SENSOR-":
                #         layout1 = [
                #             [sg.Listbox(values=(
                #                 'Accelerometer', 'Flow meter', 'Pressure transducer', 'Thermocouple', 'Load cell'
                #             ), size=(40, 10)),
                #                 sg.Image(SCDesignerPath + '\\PROPULSION\\P_ID\\Valves\\Images\\Blank.png', size=(1, 1),
                #                          key='-IMAGE-')],
                #             [sg.Radio('Fail Open', "RADIO1", default=True, size=(10, 1)),
                #              sg.Radio('Fail Closed', "RADIO1"),
                #              sg.Button('Show Sensor Image')],
                #             [sg.Submit(tooltip='Submit'), sg.Cancel()]]
                #
                #         window1 = sg.Window('Select Sensor Type', layout1, grab_anywhere=False)
                #         while True:
                #             action, event1 = window1.read()
                #             if action == "Show Valve Image":
                #                 valvetype = event1[0][0]
                #                 if valvetype == "Angle valve":
                #                     window1.Element('-IMAGE-').Update(
                #                         SCDesignerPath + '\\PROPULSION\\P_ID\\Valves\\Images\\Angle.png')
                #                 # elif valvetype == "Check valve":
                #
                #                 elif valvetype == "Diaphragm valve":
                #                     window1.Element('-IMAGE-').Update(
                #                         SCDesignerPath + '\\PROPULSION\\P_ID\\Valves\Images\Diaphragm.png')
                #                 elif valvetype == "Ball valve":
                #                     window1.Element('-IMAGE-').Update(
                #                         SCDesignerPath + '\\PROPULSION\\P_ID\\Valves\Images\TrunnionBall.png')
                #                 elif valvetype == "Butterfly valve":
                #                     window1.Element('-IMAGE-').Update(
                #                         SCDesignerPath + '\\PROPULSION\\P_ID\\Valves\Images\Butterfly.png')
                #                 elif valvetype == "Gate valve":
                #                     window1.Element('-IMAGE-').Update(
                #                         SCDesignerPath + '\\PROPULSION\\P_ID\\Valves\Images\Gate.png')
                #                 # elif valvetype == "Rotary valve":
                #                 #
                #                 # elif valvetype == "Solenoid 2-way"
                #
                #             if action == "Submit":
                #                 valvetype = event1[0][0]
                #                 window1.close()
                #                 if valvetype == "Ball valve":
                #                     with open(SCDesignerPath + "\\PROPULSION\\P_ID\\Valves\\HandOpGlobe.png",
                #                               "rb") as image:
                #                         f = image.read()
                #                         data = bytearray(f)
                #                     data = bytes(data)
                #                     g.draw_image(data=data, location=(25, 25))
                #             if action == "Cancel":
                #                 window1.close()
                #                 break
                #
                #     if event == "-CYCLE-":
                #         layout1 = [
                #             [sg.Listbox(values=(
                #                 'Monopropellant', 'Pressure-fed bipropellant', 'Expander cycle', 'Gas-generator cycle',
                #                 'Combustion tap-off cycle',
                #                 'Staged combustion', 'Full-flow staged combustion'), size=(40, 30)),
                #                 sg.Image(SCDesignerPath + '\\PROPULSION\\P_ID\\Valves\\Images\\Blank.png', size=(1, 1),
                #                          key='-IMAGE-')],
                #             [sg.Button('Show Cycle')],
                #             [sg.Submit(tooltip='Submit'), sg.Cancel()]]
                #
                #         window1 = sg.Window('Add Engine Cycle', layout1, grab_anywhere=False)
                #         cycletype = ""
                #         while True:
                #             action, event1 = window1.read()
                #             if action == "Show Cycle":
                #                 cycletype = event1[0][0]
                #                 if cycletype == "Monopropellant":
                #                     window1.Element('-IMAGE-').Update(SCDesignerPath + '\\PROPULSION\\P_ID\\Monoprop.png')
                #                 if cycletype == "Pressure-fed bipropellant":
                #                     window1.Element('-IMAGE-').Update(SCDesignerPath + '\\PROPULSION\\P_ID\\Pressure.png')
                #                 if cycletype == "Expander cycle":
                #                     window1.Element('-IMAGE-').Update(SCDesignerPath + '\\PROPULSION\\P_ID\\Expander.png')
                #                 if cycletype == "Gas-generator cycle":
                #                     window1.Element('-IMAGE-').Update(SCDesignerPath + '\\PROPULSION\\P_ID\\GasGen.png')
                #                 if cycletype == "Combustion tap-off cycle":
                #                     window1.Element('-IMAGE-').Update(SCDesignerPath + '\\PROPULSION\\P_ID\\CombTap.png')
                #                 if cycletype == "Staged combustion":
                #                     window1.Element('-IMAGE-').Update(SCDesignerPath + '\\PROPULSION\\P_ID\\StagedComb.png')
                #                 if cycletype == "Full-flow staged combustion":
                #                     window1.Element('-IMAGE-').Update(SCDesignerPath + '\\PROPULSION\\P_ID\\FullFlow.png')
                #             if action == "Submit":
                #                 cycletype = event1[0][0]
                #                 window1.close()
                #                 break
                #             if action == "Cancel":
                #                 window1.close()
                #                 break
                #         if cycletype == "Monopropellant":
                #             addComp("TankCylBlue", g, (400, 25))
                #             addComp("Engine", g, (200, 220))
                #
                #         if cycletype == "Pressure-fed bipropellant":
                #             addComp("TankCylBlue", g, (400, 25))
                #             addComp("TankCylRed", g, (25, 25))
                #             addComp("Engine", g, (200, 220))
                #
                #         if cycletype == "Expander cycle":
                #             engineloc = [200, 220]
                #             fueltankloc = [25, 25]
                #             pumpLLoc = [170, 25]
                #             preburnerloc = [210, 120]
                #             turbineloc = [215, 23]
                #             pumpRLoc = [260, 25]
                #             oxtankloc = [400, 25]
                #             addComp("TankCylBlue", g, tuple(oxtankloc))
                #             addComp("TankCylRed", g, tuple(fueltankloc))
                #             addComp("Preburner", g, tuple(preburnerloc))
                #             addComp("RegenEngine", g, tuple(engineloc))
                #             addComp("PumpL", g, tuple(pumpLLoc))
                #             addComp("Turbine", g, tuple(turbineloc))
                #             addComp("PumpR", g, tuple(pumpRLoc))
                #
                #             connect("CylTank", "PumpL", fueltankloc, pumpLLoc, g, allines, "red")
                #             connect("PumpL", "RegenEngine", pumpLLoc, engineloc, g, allines, "red")
                #             connect("RegenEngine", "Preburner", engineloc, preburnerloc, g, allines, "red")
                #             connect("Preburner", "Turbine", preburnerloc, turbineloc, g, allines, "red")
                #             connect("Turbine", "Engine", turbineloc, engineloc, g, allines, "red")
                #             connect("CylTank", "PumpR", oxtankloc, pumpRLoc, g, allines, "blue")
                #             connect("PumpR", "Engine", pumpRLoc, engineloc, g, allines, "blue")
                #
                #         if cycletype == "Gas-generator cycle":
                #             engineloc = [200, 220]
                #             fueltankloc = [25, 25]
                #             pumpLLoc = [170, 25]
                #             preburnerloc = [210, 120]
                #             turbineloc = [215, 23]
                #             pumpRLoc = [260, 25]
                #             oxtankloc = [400, 25]
                #             addComp("TankCylBlue", g, tuple(oxtankloc))
                #             addComp("TankCylRed", g, tuple(fueltankloc))
                #             addComp("Preburner", g, tuple(preburnerloc))
                #             addComp("RegenEngine", g, tuple(engineloc))
                #             addComp("PumpL", g, tuple(pumpLLoc))
                #             addComp("Turbine", g, tuple(turbineloc))
                #             addComp("PumpR", g, tuple(pumpRLoc))
                #
                #             connect("CylTank", "PumpL", fueltankloc, pumpLLoc, g, allines, "red")
                #             connect("PumpL", "RegenEngine", pumpLLoc, engineloc, g, allines, "red")
                #             connect("RegenEngine", "Preburner", engineloc, preburnerloc, g, allines, "red")
                #             connect("Preburner", "Turbine", preburnerloc, turbineloc, g, allines, "red")
                #             connect("Turbine", "Engine", turbineloc, engineloc, g, allines, "red")
                #             connect("CylTank", "PumpR", oxtankloc, pumpRLoc, g, allines, "blue")
                #             connect("PumpR", "Engine", pumpRLoc, engineloc, g, allines, "blue")
                #
                #         if cycletype == "Combustion tap-off cycle":
                #             engineloc = [200, 220]
                #             fueltankloc = [25, 25]
                #             pumpLLoc = [170, 25]
                #             preburnerloc = [210, 120]
                #             turbineloc = [215, 23]
                #             pumpRLoc = [260, 25]
                #             oxtankloc = [400, 25]
                #             addComp("TankCylBlue", g, tuple(oxtankloc))
                #             addComp("TankCylRed", g, tuple(fueltankloc))
                #             addComp("Preburner", g, tuple(preburnerloc))
                #             addComp("RegenEngine", g, tuple(engineloc))
                #             addComp("PumpL", g, tuple(pumpLLoc))
                #             addComp("Turbine", g, tuple(turbineloc))
                #             addComp("PumpR", g, tuple(pumpRLoc))
                #
                #             connect("CylTank", "PumpL", fueltankloc, pumpLLoc, g, allines, "red")
                #             connect("PumpL", "RegenEngine", pumpLLoc, engineloc, g, allines, "red")
                #             connect("RegenEngine", "Preburner", engineloc, preburnerloc, g, allines, "red")
                #             connect("Preburner", "Turbine", preburnerloc, turbineloc, g, allines, "red")
                #             connect("Turbine", "Engine", turbineloc, engineloc, g, allines, "red")
                #             connect("CylTank", "PumpR", oxtankloc, pumpRLoc, g, allines, "blue")
                #             connect("PumpR", "Engine", pumpRLoc, engineloc, g, allines, "blue")
                #
                #         if cycletype == "Staged combustion":
                #             engineloc = [200, 220]
                #             fueltankloc = [25, 25]
                #             pumpLLoc = [170, 25]
                #             preburnerloc = [210, 120]
                #             turbineloc = [215, 23]
                #             pumpRLoc = [260, 25]
                #             oxtankloc = [400, 25]
                #             addComp("TankCylBlue", g, tuple(oxtankloc))
                #             addComp("TankCylRed", g, tuple(fueltankloc))
                #             addComp("Preburner", g, tuple(preburnerloc))
                #             addComp("RegenEngine", g, tuple(engineloc))
                #             addComp("PumpL", g, tuple(pumpLLoc))
                #             addComp("Turbine", g, tuple(turbineloc))
                #             addComp("PumpR", g, tuple(pumpRLoc))
                #
                #             connect("CylTank", "PumpL", fueltankloc, pumpLLoc, g, allines, "red")
                #             connect("PumpL", "RegenEngine", pumpLLoc, engineloc, g, allines, "red")
                #             connect("RegenEngine", "Preburner", engineloc, preburnerloc, g, allines, "red")
                #             connect("Preburner", "Turbine", preburnerloc, turbineloc, g, allines, "orange")
                #             connect("Turbine", "Engine", turbineloc, engineloc, g, allines, "orange")
                #             connect("CylTank", "PumpR", oxtankloc, pumpRLoc, g, allines, "blue")
                #             connect("PumpR", "Engine", pumpRLoc, engineloc, g, allines, "blue")
                #             connect("PumpR", "Preburner", pumpRLoc, preburnerloc, g, allines, "blue")
                #
                #         if cycletype == "Full-flow staged combustion":
                #             engineloc = [200, 220]
                #             fueltankloc = [25, 25]
                #             pumpLLoc = [170, 25]
                #             preburnerloc = [210, 120]
                #             turbineloc = [215, 23]
                #             pumpRLoc = [260, 25]
                #             oxtankloc = [400, 25]
                #             addComp("TankCylBlue", g, tuple(oxtankloc))
                #             addComp("TankCylRed", g, tuple(fueltankloc))
                #             addComp("Preburner", g, tuple(preburnerloc))
                #             addComp("RegenEngine", g, tuple(engineloc))
                #             addComp("PumpL", g, tuple(pumpLLoc))
                #             addComp("Turbine", g, tuple(turbineloc))
                #             addComp("PumpR", g, tuple(pumpRLoc))
                #
                #             connect("CylTank", "PumpL", fueltankloc, pumpLLoc, g, allines, "red")
                #             connect("PumpL", "RegenEngine", pumpLLoc, engineloc, g, allines, "red")
                #             connect("RegenEngine", "Preburner", engineloc, preburnerloc, g, allines, "red")
                #             connect("Preburner", "Turbine", preburnerloc, turbineloc, g, allines, "red")
                #             connect("Turbine", "Engine", turbineloc, engineloc, g, allines, "red")
                #             connect("CylTank", "PumpR", oxtankloc, pumpRLoc, g, allines, "blue")
                #             connect("PumpR", "Engine", pumpRLoc, engineloc, g, allines, "blue")
                #
                #     if event.endswith('+UP'):  # The drawing has ended because mouse up
                #         start_point, end_point = None, None  # enable grabbing a new rect
                #         dragging = False
                #         prior_rect = None
                #
                #     if event == 'Exit':
                #         exit()
                #
                # window.close()

            if event == "Existing Prop System":
                Engine = values[1]
                for row in ws.rows:
                    if row[0].value == Engine:
                        for cell in row:
                            print(cell.value, end=" ")

                # Could be used in the future to import step files of existing engines at least for shape and placement
                # import ImportGui
                # ImportGui.open(
                #     u"propulsion/" + Engine + ".step")

            if event == "O-ring":
                import csv
                OringList = []
                i = 0
                with open(SCDesignerPath + '\\PROPULSION\\O_rings.csv', 'r') as csvfile:
                    orings = csv.reader(csvfile, delimiter=',')
                    for row in orings:
                        if i == 0:
                            Header = row
                            i = 1
                            continue
                        OringList.append(row)

                layout = [[sg.Table(OringList,
                                    headings=Header,
                                    auto_size_columns=True,
                                    key='Table')]]

                win = sg.Window('Select O-ring',
                                layout, keep_on_top=True, finalize=True)

                myTable = win['Table']
                myTable.bind('<Button-1>', "Click")

                while True:
                    event, values = win.read()
                    # print(event, values)
                    if event in (None,):
                        win.close()
                        break
                    elif event == 'TableClick':
                        try:
                            bind_event = myTable.user_bind_event
                            col = myTable.Widget.identify_column(bind_event.x)
                            row_iid = myTable.Widget.identify_row(bind_event.y)
                            row = myTable.Widget.item(row_iid)
                            print(row['values'])

                            OringType = row['values'][0]
                            CrossSection = float(row['values'][1])
                            InnerDiameter = float(row['values'][2])
                            OuterDiameter = float(row['values'][3])
                            print(OringType)
                            print(CrossSection)
                            print(InnerDiameter)
                            print(OuterDiameter)
                        except:
                            pass





                            import Part
                            import PartDesign
                            import PartDesignGui
                            import Sketcher
                            App.newDocument(FreeCAD.ActiveDocument.Name)

                            App.setActiveDocument(FreeCAD.ActiveDocument.Name)
                            App.ActiveDocument = App.getDocument(FreeCAD.ActiveDocument.Name)
                            # Gui.ActiveDocument = Gui.getDocument(FreeCAD.ActiveDocument.Name)
                            # Gui.activateWorkbench("PartDesignWorkbench")
                            App.activeDocument().addObject('PartDesign::Body', 'Body')
                            import PartDesignGui
                            # Gui.activeView().setActiveObject('pdbody', App.activeDocument().Body)
                            # Gui.Selection.clearSelection()
                            # Gui.Selection.addSelection(App.ActiveDocument.Body)
                            App.ActiveDocument.recompute()
                            App.activeDocument().Body.newObject('Sketcher::SketchObject', 'Sketch')
                            App.activeDocument().Sketch.Support = (App.activeDocument().XY_Plane, [''])
                            App.activeDocument().Sketch.MapMode = 'FlatFace'
                            App.ActiveDocument.recompute()
                            # Gui.activeDocument().setEdit('Sketch')
                            # Gui.activateWorkbench('SketcherWorkbench')
                            import PartDesignGui

                            ActiveSketch = App.ActiveDocument.getObject('Sketch')

                            ActiveSketch = App.getDocument(FreeCAD.ActiveDocument.Name).getObject('Sketch')

                            # Gui.runCommand('Std_OrthographicCamera', 1)
                            # Gui.runCommand('Sketcher_CompCreateCircle', 0)
                            App.getDocument(FreeCAD.ActiveDocument.Name).getObject('Sketch').addGeometry(
                                Part.Circle(App.Vector(-0.047387, 4.004093, 0), App.Vector(0, 0, 1), 0.892370), False)
                            App.getDocument(FreeCAD.ActiveDocument.Name).getObject('Sketch').addConstraint(
                                Sketcher.Constraint('PointOnObject', 0, 3, -2))
                            App.ActiveDocument.recompute()
                            # Gui.runCommand('Sketcher_CreatePoint', 0)
                            App.getDocument(FreeCAD.ActiveDocument.Name).getObject('Sketch').addGeometry(
                                Part.Point(App.Vector(-0.017064, 4.853165, 0)))
                            App.getDocument(FreeCAD.ActiveDocument.Name).getObject('Sketch').addConstraint(
                                Sketcher.Constraint('PointOnObject', 1, 1, 0))
                            App.ActiveDocument.recompute()
                            # Gui.Selection.addSelection(FreeCAD.ActiveDocument.Name,'Body','Sketch.Vertex2',-0.017064,4.85317,0.012,False)
                            # Gui.Selection.addSelection(FreeCAD.ActiveDocument.Name,'Body','Sketch.V_Axis',0,4.85952,0.001,False)
                            ### Begin command Sketcher_ConstrainPointOnObject
                            App.getDocument(FreeCAD.ActiveDocument.Name).getObject('Sketch').addConstraint(
                                Sketcher.Constraint('PointOnObject', 1, 1, -2))
                            ### End command Sketcher_ConstrainPointOnObject
                            # Gui.Selection.clearSelection()
                            # Gui.Selection.addSelection(FreeCAD.ActiveDocument.Name,'Body','Sketch.Vertex2',0,4.85317,0.012,False)
                            # Gui.Selection.addSelection(FreeCAD.ActiveDocument.Name,'Body','Sketch.RootPoint',0,0,0.012,False)
                            ### Begin command Sketcher_ConstrainDistanceY
                            App.getDocument(FreeCAD.ActiveDocument.Name).getObject('Sketch').addConstraint(
                                Sketcher.Constraint('DistanceY', -1, 1, 1, 1, 4.853165))
                            App.getDocument(FreeCAD.ActiveDocument.Name).getObject('Sketch').setDatum(3, App.Units.Quantity(str((InnerDiameter/2)-(CrossSection/2)) + ' mm'))
                            App.ActiveDocument.recompute()
                            ### End command Sketcher_ConstrainDistanceY
                            # Gui.Selection.clearSelection()
                            # Gui.Selection.addSelection(FreeCAD.ActiveDocument.Name,'Body','Sketch.Vertex1',0,5.04849,0.012,False)
                            # Gui.Selection.addSelection(FreeCAD.ActiveDocument.Name,'Body','Sketch.RootPoint',0,0,0.012,False)
                            # Gui.Selection.clearSelection()
                            # Gui.Selection.addSelection(FreeCAD.ActiveDocument.Name,'Body','Sketch.Edge1',4.79595,6.27988,0.008,False)
                            ### Begin command Sketcher_CompConstrainRadDia
                            App.getDocument(FreeCAD.ActiveDocument.Name).getObject('Sketch').addConstraint(
                                Sketcher.Constraint('Radius', 0, 4.951508))
                            App.getDocument(FreeCAD.ActiveDocument.Name).getObject('Sketch').setDatum(4, App.Units.Quantity(str(CrossSection/2) + ' mm'))
                            App.ActiveDocument.recompute()
                            ### End command Sketcher_CompConstrainRadDia
                            # Gui.Selection.clearSelection()
                            # Gui.getDocument(FreeCAD.ActiveDocument.Name).resetEdit()
                            App.ActiveDocument.recompute()
                            ActiveSketch = App.getDocument(FreeCAD.ActiveDocument.Name).getObject('Sketch')

                            # Gui.Selection.addSelection(FreeCAD.ActiveDocument.Name,'Body','Sketch.')
                            App.getDocument(FreeCAD.ActiveDocument.Name).recompute()
                            ### Begin command PartDesign_Revolution
                            App.getDocument(FreeCAD.ActiveDocument.Name).getObject('Body').newObject('PartDesign::Revolution', 'Revolution')
                            App.getDocument(FreeCAD.ActiveDocument.Name).getObject('Revolution').Profile = App.getDocument(
                                FreeCAD.ActiveDocument.Name).getObject('Sketch')
                            App.getDocument(FreeCAD.ActiveDocument.Name).getObject('Revolution').ReferenceAxis = (
                            App.getDocument(FreeCAD.ActiveDocument.Name).getObject('X_Axis'), [''])
                            # App.getDocument(FreeCAD.ActiveDocument.Name).getObject('Revolution').ReferenceAxis = (
                            # App.getDocument(FreeCAD.ActiveDocument.Name).getObject('Sketch'), ['V_Axis'])
                            App.getDocument(FreeCAD.ActiveDocument.Name).getObject('Revolution').Angle = 360.0
                            App.getDocument(FreeCAD.ActiveDocument.Name).getObject('Sketch').Visibility = False
                            App.ActiveDocument.recompute()
                            App.getDocument(FreeCAD.ActiveDocument.Name).getObject('Revolution').ViewObject.ShapeColor = getattr(
                                App.getDocument(FreeCAD.ActiveDocument.Name).getObject('Body').getLinkedObject(True).ViewObject, 'ShapeColor',
                                App.getDocument(FreeCAD.ActiveDocument.Name).getObject('Revolution').ViewObject.ShapeColor)
                            App.getDocument(FreeCAD.ActiveDocument.Name).getObject('Revolution').ViewObject.LineColor = getattr(
                                App.getDocument(FreeCAD.ActiveDocument.Name).getObject('Body').getLinkedObject(True).ViewObject, 'LineColor',
                                App.getDocument(FreeCAD.ActiveDocument.Name).getObject('Revolution').ViewObject.LineColor)
                            App.getDocument(FreeCAD.ActiveDocument.Name).getObject('Revolution').ViewObject.PointColor = getattr(
                                App.getDocument(FreeCAD.ActiveDocument.Name).getObject('Body').getLinkedObject(True).ViewObject, 'PointColor',
                                App.getDocument(FreeCAD.ActiveDocument.Name).getObject('Revolution').ViewObject.PointColor)
                            App.getDocument(FreeCAD.ActiveDocument.Name).getObject('Revolution').ViewObject.Transparency = getattr(
                                App.getDocument(FreeCAD.ActiveDocument.Name).getObject('Body').getLinkedObject(True).ViewObject,
                                'Transparency', App.getDocument(FreeCAD.ActiveDocument.Name).getObject('Revolution').ViewObject.Transparency)
                            App.getDocument(FreeCAD.ActiveDocument.Name).getObject('Revolution').ViewObject.DisplayMode = getattr(
                                App.getDocument(FreeCAD.ActiveDocument.Name).getObject('Body').getLinkedObject(True).ViewObject,
                                'DisplayMode', App.getDocument(FreeCAD.ActiveDocument.Name).getObject('Revolution').ViewObject.DisplayMode)
                            App.getDocument(FreeCAD.ActiveDocument.Name).recompute()
                            # Gui.getDocument(FreeCAD.ActiveDocument.Name).setEdit(App.getDocument(FreeCAD.ActiveDocument.Name).getObject('Body'), 0,
                            #                                    'Revolution.')
                            # Gui.Selection.clearSelection()
                            ### End command PartDesign_Revolution
                            win.close()
                            window.close()

            if event == "Quit":
                window.close()
            elif event == "Ok":
                window.close()
                print(values)

            # import PropulsiveLanding2
            # import pandas as pd
            # import numpy as np
            # file_loc = "Component_Lists.xlsx"
            # df = pd.read_excel(file_loc, index_col=None, na_values=['NA'], sheet_name= "Engines", usecols = "A")
            # print(df)
            #
            # layout = [
            #     [sg.Radio('Select Engine', "RADIO1", default=True, size=(10,1)), sg.Radio('Design Engine', "RADIO1")],
            #     [sg.Text('Available Engines')],
            #     [sg.InputCombo(('Combobox 1', 'Combobox 2'), size=(20, 1)), sg.Button('OK')]
            # ]
            #
            #
            # window = sg.Window('Propulsion', layout, default_element_size=(40, 1), grab_anywhere=False)
            #
            # event, values = window.read()
            # print(values[1])
            #
            # window.close()
            # if event == "Quit":
            #     window.close()
            # elif event == "Ok":
            #     window.close()
            #     print(values)
        return

class Mechanical():
    """My new command"""

    def GetResources(self):
        return {'Pixmap'  : 'C:\\Users\\' + username + '\\AppData\\Roaming\\FreeCAD\\Mod\\SpacecraftDesigner\\Icons\\Mech.jpg',
                'Accel' : "Shift+S", # a default shortcut (optional)
                'MenuText': "Mechanical",
                'ToolTip' : "Define Spacecraft Mechanical Systems"}

    def Activated(self):
        import csv
        import FreeCAD
        import FreeCADGui as Gui
        i = 0
        MaterialList = []
        with open(SCDesignerPath + '\\STRUCTURAL\\MIL_HDBK_5J.csv', 'r') as csvfile:
            materials = csv.reader(csvfile, delimiter=',')
            for row in materials:
                if i == 0:
                    Header = row
                    print(Header)
                    i = 1
                    continue
                MaterialList.append(row)

        surfacefinishes = ["Flame Cutting", "Snagging", "Sawing", "Planing/Shaping", "Drilling", "Chemical Milling",
                           "Electrical Discharge", "Milling", "Broaching", "Reaming", "Electron Beam", "Laser",
                           "Electrochemical", "Boring_Turning", "Barrel Finishing", "Electrolytic Grinding",
                           "Roller Burnishing", "Grinding", "Horning", "Electro Polish", "Polishing", "Lapping",
                           "Super Finishing", "Sand Casting", "Hot Rolling", "Forging", "Perm Mold Casting",
                           "Investment Casting", "Extruding", "Cold Rolling_Drawing", "Die Casting"]

        layout = [[sg.Text('Add Material', size=(25, 1)), sg.InputCombo(('Bar', 'Sheet', 'Plate', 'Tubing', 'Strip', 'Forging', 'Ring', 'Extrusion', 'Rod', 'Sandwich panel', 'Composite lay-up', 'Forging', 'Casting', '3D-Printed Structure')), sg.Button('OK', key='-GEOMETRY-')],
                  [sg.Text('Set Mechanical Surface Finish', size=(25, 1)),sg.InputCombo(surfacefinishes), sg.Button('OK', key="-FINISH-")],
                  [sg.Text('Add Engineering Fabric', size=(25, 1)), sg.Button('OK', key="-FABRIC-")],
                  [sg.Text('Add Bearing', size=(25, 1)), sg.Button('OK', key="-BEARING-"),sg.Text('Add Fastener', size=(25, 1)), sg.Button('OK', key="-FASTENER-")],
                  [sg.Text('Add Hydraulic System', size=(25, 1)), sg.Button('OK', key="-HYDRAULIC-"), sg.Text('Add Pneumatic System', size=(25, 1)), sg.Button('OK', key="-PNEUMATIC-")],
                  [sg.Text('Add Belt Drive', size=(25, 1)), sg.Button('OK', key="-BELT-"),
                   sg.Text('Add Aircraft Tire', size=(25, 1)), sg.Button('OK', key="-TIRE-")],
                  [sg.Text('Add Track System', size=(25, 1)), sg.Button('OK', key="-TRACK-")],
                  [sg.Text('Add Gear', size=(25, 1)), sg.Button('OK', key="-GEAR-")],
                  [sg.Text('Add Belt Drive', size=(25, 1)), sg.Button('OK', key="-BELT-"), sg.Text('Add Chain Drive', size=(25, 1)), sg.Button('OK', key="-CHAIN-")],
                  [sg.Text('Add Shaft', size=(25, 1)), sg.Button('OK', key="-SHAFT-")],
                  [sg.Text('Add Weld', size=(25, 1)), sg.Button('OK', key="-WELD-")],
                  [sg.Text('Add Subtractive Isogrid Pattern', size=(25, 1)), sg.Button('OK', key="-REMOVE-")],
                  [sg.Text('Add Debris Shielding', size=(25, 1)), sg.Button('OK', key="-DEBRIS-")],
                  [sg.Text('Add Radiation Shielding', size=(25, 1)), sg.Button('OK', key="-RADIATION-")],
                  [sg.Text('Remove All Constraints', size=(25, 1)), sg.Button('OK', key="-REMOVE-")],
                  [sg.Text('Reset Constraints', size=(25, 1)), sg.Button('OK', key="-RESET-")],
                  [sg.Submit(tooltip='Click to submit this window'), sg.Cancel()]]



        window = sg.Window('Mechanical Systems', layout, default_element_size=(40, 1), grab_anywhere=False)

        event, values = window.read()
        # nasa.gov/sites/default/files/atoms/files/soa2018_final_doc.pdf
        window.close()    
        if event == "Cancel":
            window.close()
        elif event == "Submit":
            window.close()
        elif event == "-FABRIC-":

            layout1 = [[sg.Text("Set Extended Piston Length (m)"), sg.InputText("", key="-EXTLEN-")],
                       [sg.Text("Set Retracted Piston Length (m)"), sg.InputText("", key="-RETLEN-")],
                       [sg.Text("Set Fluid Pressure (Pa)"), sg.InputText("", key="-PRES-")],
                       [sg.Text("Piston Force (N)"), sg.Text("",key="-PISTONFORCE-")],

                       [sg.Submit(tooltip='Click to submit this window'), sg.Cancel()]]
            window1 = sg.Window('Hydraulic Piston', layout1, default_element_size=(40, 1), grab_anywhere=False)
            # event1, values1 = window1.read()

        elif event == "-HYDRAULIC-":
            layout1 = [[sg.Text("Set Extended Piston Length (m)"), sg.InputText("", key="-EXTLEN-")],
                       [sg.Text("Set Retracted Piston Length (m)"), sg.InputText("", key="-RETLEN-")],
                       [sg.Text("Set Fluid Pressure (Pa)"), sg.InputText("", key="-PRES-")],
                       [sg.Text("Set Piston Radius (m)"), sg.InputText("", key="-RAD-")],
                       [sg.Text("Piston Force (N)"), sg.Text("",key="-PISTONFORCE-")],
                       [sg.Button("Update Force", key="-FORCEUP-"), sg.Cancel()]]
            window1 = sg.Window('Hydraulic Piston', layout1, default_element_size=(40, 1), grab_anywhere=False, finalize=True)
            event1, values1 = window1.read()
            if event1 == "Cancel":
                window1.close()
            if event1 == "-FORCEUP-":
                exlen = float(values1["-EXTLEN-"])
                retlen = float(values1["-RETLEN-"])
                fluidpress = float(values1["-PRES-"])
                radius = float(values1["-RAD-"])
                Force = fluidpress*math.pi*(radius**2)
                print(Force)
                window1.Element["-PISTONFORCE-"].update(str(round(Force,2)))

        elif event == "-REMOVE-":
            Gui.activateWorkbench("A2plusWorkbench")
            for obj in FreeCAD.ActiveDocument.Objects:
                if obj.Name.find("Coincident") > -1:
                    App.getDocument('RoverAssembly4').removeObject(obj.Name)
                    App.getDocument('RoverAssembly4').recompute()
            Gui.activateWorkbench("SpacecraftDesigner")

        elif event == "-RESET-":
            # remember in a2p workbench CD_a2p line 157 commented out to work with this
            Gui.activateWorkbench("A2plusWorkbench")
            import pyautogui
            import time
            for obj in FreeCAD.ActiveDocument.Objects:
                if obj.Name.find("b_") > -1:
                    Gui.Selection.addSelection('RoverAssembly4', obj.Name)
                    Gui.runCommand('rnp_Update_A2pParts')
                    Gui.Selection.clearSelection()
            Gui.activateWorkbench("SpacecraftDesigner")

        elif event == "-GEOMETRY-":
            window.close()
            MaterialListGeometry = []
            userSel = values[0]
            for Material in MaterialList:
                if Material[4].find(userSel) > -1:
                    print(Material[1] + " " + Material[0]+ " " + Material[2])
                    MaterialListGeometry.append(Material)
            Header = ["MATERIAL","CLASSIFICATION","NAME","GRADE","GEOMETRY","CONDITION/TEMPER"]#,"THICKNESS (m)","ULTIMATE TENSILE STRENGTH (Long Grain)", "TENSILE YIELD STRENGTH (Long Grain)", "COMPRESSIVE YIELD STRENGTH (Long Grain)", "ULTIMATE SHEAR STRENGTH (Long Grain)", "BRU 2", "YOUNGS MODULUS", "SHEAR MODULUS", "POISSONS RATIO", "DENSITY", "C", "K", "alpha"]
            print(Header)

            layout = [[sg.Table(MaterialListGeometry,
                                headings=Header,
                                auto_size_columns=True,
                                key='Table')]]

            win = sg.Window('Select Material',
                            layout, keep_on_top=True, finalize=True)

            myTable = win['Table']
            myTable.bind('<Button-1>', "Click")

            while True:
                event, values = win.read()
                # print(event, values)
                if event in (None,):
                    win.close()
                    break
                elif event == 'TableClick':
                    try:
                        bind_event = myTable.user_bind_event
                        col = myTable.Widget.identify_column(bind_event.x)
                        row_iid = myTable.Widget.identify_row(bind_event.y)
                        row = myTable.Widget.item(row_iid)
                        win.close()

                        print(row)

                        Material = str(row['values'][0])
                        Classification = str(row['values'][1])
                        Name = str(row['values'][2])
                        Grade = str(row['values'][3])
                        Geometry = str(row['values'][4])
                        Condition = float(row['values'][5])
                        Thickness = float(row['values'][6])
                        UltTensStr = float(row['values'][7])
                        TensYieldStr = float(row['values'][8])
                        CompYieldStr = float(row['values'][9])
                        UltShearStr = float(row['values'][10])
                        BRU2 = float(row['values'][11])
                        YoungsM = float(row['values'][10])
                        ShearMod = float(row['values'][10])
                        PoissonsR = float(row['values'][10])
                        Density = float(row['values'][10])
                        Cval = float(row['values'][10])
                        Kval = float(row['values'][10])
                        Alpha = float(row['values'][10])
                        print(Material + " " + Name + " selected.")
                        if os.path.isdir(SCDesignerPath + "\\" +
                                         str(
                                             App.ActiveDocument.Label)):
                            pass
                        else:
                            os.mkdir(SCDesignerPath + "\\" + str(
                                App.ActiveDocument.Label))

                        with open(
                                SCDesignerPath + "\\STRUCTURAL\\" + str(
                                    App.ActiveDocument.Label) + ".csv", 'w+') as f:
                            f.write(str(Material) + ","+ str(Classification) + "," + str(Name) + "," + str(Grade) + "," + str(Geometry) + "," + str(Condition) + "," + str(Thickness) + "," + str(UltTensStr) + "," + str(TensYieldStr) + "," + str(CompYieldStr) + ","+ str(UltShearStr) + "," + str(BRU2) + "," + str(YoungsM) + "," + str(ShearMod) + "," + str(PoissonsR) + "," + str(Density) + "," + str(Cval) + "," + str(Kval) + "," + str(Alpha))
                            # f.close()

                    except:
                        pass

            import os
            import os.path
            import FreeCAD
            import importOBJ
            import FreeCAD
            import Draft
            import Mesh
            import FreeCADGui as Gui

            ShapeList = []

            for obj in FreeCAD.ActiveDocument.Objects:
                if hasattr(obj, "Shape"):
                    ShapeList.append(obj.Name)

            # Gui.runCommand('a2p_Show_Hierarchy_Command',0)

            # uniqueshapelist = []
            # for shape in ShapeList:
            #	shapemod = shape[2:]
            #	modstop = shapemod.find("_")
            #	shapemod = shapemod[:modstop]
            #	uniqueshapelist.append(shapemod)
            #
            # uniqueshapelist = sorted(set(uniqueshapelist))

            if os.path.isdir(SCDesignerPath + "\\" +
                             str(
                                 App.ActiveDocument.Label)):
                pass
            else:
                os.mkdir(SCDesignerPath + "\\" + str(
                    App.ActiveDocument.Label))
            if os.path.exists(
                    SCDesignerPath + "\\" + str(
                        App.ActiveDocument.Label) + "\\" + str(
                        App.ActiveDocument.Label) + "Inertia.csv"):
                os.remove(SCDesignerPath + "\\" + str(
                        App.ActiveDocument.Label) + "\\" + str(
                        App.ActiveDocument.Label) + "Inertia.csv")
                with open(SCDesignerPath + "\\" + str(
                        App.ActiveDocument.Label) + "\\" + str(
                        App.ActiveDocument.Label) + "Inertia.csv", "w") as my_empty_csv:
                    pass


            for shape in ShapeList:
                if shape == "Body":

                    Draft.clone(FreeCAD.ActiveDocument.getObject(shape))
                    shapemod = shape[2:]
                    modstop = shapemod.find("_")
                    shapemod = shapemod[:modstop]
                    FreeCAD.getDocument(App.ActiveDocument.Label).getObject("Clone").Scale = (
                        0.1000, 0.1000, 0.1000)
                    MeshExportName = "C:/Users/" + username + "/AppData/Roaming/FreeCAD/Mod/SpacecraftDesigner/" + str(
                        App.ActiveDocument.Label) + "/" + shapemod + ".obj"
                    App.getDocument(App.ActiveDocument.Label).recompute()
                    __objs__ = []
                    __objs__.append(FreeCAD.getDocument(App.ActiveDocument.Label).getObject("Clone"))
                    Mesh.export(__objs__, MeshExportName)
                    del __objs__
                    App.getDocument(App.ActiveDocument.Label).removeObject('Clone')
                    App.getDocument(App.ActiveDocument.Label).recompute()
                    m = App.ActiveDocument.getObject(shape).Shape.MatrixOfInertia
                    v = App.ActiveDocument.getObject(
                        shape).Shape.Volume / 1000000000  # Convert volume from mm^3 to m^3
                    p = FreeCAD.ActiveDocument.getObject(shape).Placement.Base
                    ypr = str(FreeCAD.ActiveDocument.getObject(shape).Placement)
                    startloc = ypr.find("Roll=")
                    ypr = ypr[startloc + 6:-2]
                    ypr = ypr.split(",")

                    with open(
                            SCDesignerPath + "\\" + str(
                                App.ActiveDocument.Label) + "\\" + str(
                                App.ActiveDocument.Label) + "Inertia.csv", 'a') as f:
                        f.write("\n")
                        f.write(str(shapemod) + ",")
                        for i in range(4):
                            for j in range(4):
                                f.write(str(m.A[i * 4 + j]) + ",")
                        f.write(str(v) + ",")
                        for i in range(3):
                            f.write(str(p[i]) + ",")
                        f.write(ypr[2] + ",")
                        f.write(ypr[1] + ",")
                        f.write(ypr[0] + ",")
                        f.close()





        return

class Power():
    """My new command"""

    def GetResources(self):
        return {'Pixmap'  : 'C:\\Users\\' + username + '\\AppData\\Roaming\\FreeCAD\\Mod\\SpacecraftDesigner\\Icons\\Power.jpg',
                'Accel' : "Shift+E", # a default shortcut (optional)
                'MenuText': "Power",
                'ToolTip' : "Define Spacecraft Power System"}

    def Activated(self):
        MaxPower = "|Placeholder|"
        layout = [[sg.Text('Maximum Power Draw: ' + MaxPower)],
            [sg.Text('Add Power Generation System'),  sg.Listbox(values=('Photovoltaic', 'Solar Thermal', 'Fuel Cell(s)', 'Radioisotope Thermoelectric Generator', 'Full Nuclear System'), size=(40, 8)),  sg.Button('Add Power Gen')],
            [sg.Text('Add Power Storage System'),  sg.Listbox(values=('Nickel Hydride Battery/batteries', 'Lithium Ion Battery/batteries', 'Lithium Polymer Battery/Batteries', 'Nickel-Cadmium Battery/batteries', 'Flywheel'), size=(40, 8)), sg.Text("Voltage"), sg.InputText(size=(10,8)), sg.Text("Watt Hours"), sg.InputText(size=(10,8)),  sg.Button('Add Power Stor')],
            [sg.Submit(tooltip='Click to submit this window'), sg.Cancel()]]


        window = sg.Window('Power', layout, default_element_size=(40, 10), grab_anywhere=False)

        event, values = window.read()

        window.close()

        if event == "Add Power Gen":
            window.close()
            ConsumerList = []
            import csv
            i = 0
            peakpower = 0
            with open(SCDesignerPath + "\\Vehicles\\" + new_vehicle.name + "\\PowerBudget.csv", "r") as f:
                consumers = csv.reader(f, delimiter=',')
                for row in consumers:
                    if i == 0:
                        Header = row
                        i = 1
                        continue
                    ConsumerList.append(row)
                    peakpower+=float(row[1])*float(row[2])

            if values[0][0] == "Photovoltaic":
                import FreeCADGui as Gui
                layout1 = [[sg.Text('Choose panel type'), sg.Listbox(values=(
                    'Silicon', 'High Efficiency Silicon', 'Cadmium Sulfide', 'Cadmium Telluride', 'Gallium Arsenide/Germanium', 'Gallium Indium Phosphide/Gallium Arsenide/Germanium', 'Amorphous Silicon', 'Copper Indium Gallium Selenide'), size=(40, 8)), sg.Button('Add Power Gen')]]

                window11 = sg.Window('Photovoltaics', layout1, default_element_size=(40, 10), grab_anywhere=False)
                event1, values1 = window11.read()
                window11.close()
                if values1[0] == 'Silicon':
                    efficiency = 0.13
                elif values1[0] == 'High Efficiency Silicon':
                    efficiency = 0.17
                elif values1[0] == 'Gallium Arsenide/Germanium':
                    efficiency = 0.185
                # elif values1[0] == 'Cadmium Sulfide':
                #     efficiency =
                # elif values1[0] == 'Gallium Indium Phosphide/Gallium Arsenide/Germanium':
                #     efficiency =
                elif values1[0] == 'Amorphous Silicon':
                    efficiency = 0.06
                elif values1[0] == 'Copper Indium Gallium Selenide':
                    efficiency = 0.1

                # Pload =
                # PEol = Pload + Precharge
                # PBol =

                length = 1 # Meters
                width = 0.25 # Meters
                Thickness = 0.02 # Meters
                import Part
                import PartDesign
                import PartDesignGui
                import Sketcher
                App.newDocument(FreeCAD.ActiveDocument.Name)

                App.setActiveDocument(FreeCAD.ActiveDocument.Name)
                App.ActiveDocument = App.getDocument(FreeCAD.ActiveDocument.Name)
                Gui.ActiveDocument = Gui.getDocument(FreeCAD.ActiveDocument.Name)
                Gui.activateWorkbench("PartDesignWorkbench")
                App.activeDocument().addObject('PartDesign::Body', 'Body')
                import PartDesignGui
                Gui.activeView().setActiveObject('pdbody', App.activeDocument().Body)
                Gui.Selection.clearSelection()
                Gui.Selection.addSelection(App.ActiveDocument.Body)
                App.ActiveDocument.recompute()
                App.activeDocument().Body.newObject('Sketcher::SketchObject', 'Sketch')
                App.activeDocument().Sketch.Support = (App.activeDocument().XY_Plane, [''])
                App.activeDocument().Sketch.MapMode = 'FlatFace'
                App.ActiveDocument.recompute()
                Gui.activeDocument().setEdit('Sketch')
                Gui.activateWorkbench('SketcherWorkbench')
                import PartDesignGui

                ActiveSketch = App.ActiveDocument.getObject('Sketch')

                App.ActiveDocument.Sketch.addGeometry(Part.LineSegment(App.Vector(0, 0, 0), App.Vector(length*1000, 0, 0)),
                                                      False)
                App.ActiveDocument.Sketch.addGeometry(Part.LineSegment(App.Vector(length*1000, 0, 0), App.Vector(length*1000, width*1000, 0)),
                                                      False)
                App.ActiveDocument.Sketch.addGeometry(Part.LineSegment(App.Vector(length*1000, width*1000, 0), App.Vector(0, width*1000, 0)),
                                                      False)
                App.ActiveDocument.Sketch.addGeometry(Part.LineSegment(App.Vector(0, width*1000, 0), App.Vector(0, 0, 0)),
                                                      False)
                App.ActiveDocument.recompute()

                Gui.getDocument(FreeCAD.ActiveDocument.Name).resetEdit()
                ActiveSketch = App.ActiveDocument.getObject('Sketch')

                Gui.activateWorkbench('PartDesignWorkbench')
                App.getDocument(FreeCAD.ActiveDocument.Name).recompute()
                App.activeDocument().Body.newObject("PartDesign::Pad", "Pad")
                App.activeDocument().Pad.Profile = App.activeDocument().Sketch
                App.activeDocument().Pad.Length = 10.0
                App.ActiveDocument.recompute()
                Gui.activeDocument().hide("Sketch")
                App.ActiveDocument.recompute()
                Gui.ActiveDocument.Pad.ShapeColor = Gui.ActiveDocument.Body.ShapeColor
                Gui.ActiveDocument.Pad.LineColor = Gui.ActiveDocument.Body.LineColor
                Gui.ActiveDocument.Pad.PointColor = Gui.ActiveDocument.Body.PointColor
                Gui.ActiveDocument.Pad.Transparency = Gui.ActiveDocument.Body.Transparency
                Gui.ActiveDocument.Pad.DisplayMode = Gui.ActiveDocument.Body.DisplayMode
                Gui.activeDocument().setEdit('Pad', 0)
                Gui.Selection.clearSelection()
                Gui.activeDocument().hide("Sketch")
                App.ActiveDocument.Pad.Length = Thickness*1000
                App.ActiveDocument.Pad.Type = 0
                App.ActiveDocument.Pad.UpToFace = None
                App.ActiveDocument.Pad.Reversed = 0
                App.ActiveDocument.Pad.Midplane = 0
                App.ActiveDocument.Pad.Offset = 0.000000
                App.ActiveDocument.recompute()
                Gui.activeDocument().resetEdit()
                Gui.activeDocument().activeView().viewDefaultOrientation('Trimetric', 0)
                Gui.SendMsgToActiveView("ViewFit")
                Gui.activateWorkbench("SpacecraftDesigner")
                
                
                
                
                
                
                
                
                
                
                
                
                
                
            # if values[0][0] == "Solar Thermal":
            #
            # if values[0][0] == "Fuel Cell(s)":
            #
            # if values[0][0] == "Radioisotope Thermoelectric Generator":
            #
            # if values[0][0] == 'Full Nuclear System':


        elif event == "Add Power Stor":
            batt_type = values[1][0]
            batt_voltage = values[2]
            batt_watthours = values[3]
            print(batt_watthours)

            window.close()
            # if values[0][0] == "Nickel Hydride Battery/batteries":
            #     layout1 = [[sg.Text('Choose layers'), sg.Listbox(values=(
            #         'Silicon', 'Cadmium Sulfide', 'Cadmium Telluride', 'Gallium Arsenide', 'Gallium Phosphide'), size=(40, 8)), sg.Button('Add Power Gen')]]
            #
            #     window11 = sg.Window('Photovoltaics', layout1, default_element_size=(40, 10), grab_anywhere=False)
            #     event1, values1 = window11.read()
            #     window11.close()


        return


class Thermal():
    """My new command"""
    import math
    def GetResources(self):
        return {
            'Pixmap': 'C:\\Users\\' + username + '\\AppData\\Roaming\\FreeCAD\\Mod\\SpacecraftDesigner\\Icons\\Thermal.jpg',
            'Accel': "Shift+T",  # a default shortcut (optional)
            'MenuText': "Thermal",
            'ToolTip': "Define Spacecraft Thermal Systems"}

    def Activated(self):

        import FreeSimpleGUI as sg

        def choose_celestial_body():
            # Define the list of celestial bodies
            celestial_bodies = ["Mercury", "Venus", "Earth", "Moon", "Mars", "Jupiter", "Saturn", "Uranus", "Neptune",
                                "Pluto",
                                "Charon"]

            # Define the layout of the GUI with a wider listbox
            layout = [
                [sg.Text('Select a celestial body for thermal analysis:')],
                [sg.Listbox(values=celestial_bodies, size=(40, len(celestial_bodies)), key='-CELESTIAL_BODY-',
                            enable_events=True)],
                [sg.Button('Submit'), sg.Button('Cancel')]
            ]

            # Create the window
            window = sg.Window('Celestial Body Selector', layout)

            # Event loop to process events and get user input
            while True:
                event, values = window.read()
                if event == sg.WINDOW_CLOSED or event == 'Cancel':
                    Planet = None
                    break
                if event == 'Submit':
                    selected_body = values['-CELESTIAL_BODY-']
                    if selected_body:
                        Planet = selected_body[0]
                        window.close()

                        return Planet

                    else:
                        sg.popup('Please select a celestial body.')

            # Close the window

        Planet = choose_celestial_body()

        layout = [
            [sg.Text('Add Thermal System'), sg.InputCombo(('Heat Pipe', 'Cold Plate', 'Thermoelectric Cooler', 'Louver',
                                                           'Heater', 'Evaporator', 'Radiator', 'Heat Pump',
                                                           'Heat Exchanger', 'Dewar', 'Phase Change Material')),
             sg.Button('OK', key="-SYS-")],
            [sg.Text('Add Pipe'), sg.Button('OK', key="-PIPE-")],
            [sg.Text('Add Thermal Coating'), sg.Button('OK', key="-COAT-")],
            [sg.Text('Add Thermal Protection System'), sg.InputCombo(('Reinforced Carbon-Carbon', 'AVCOAT',
                                                                      'Phenolic-impregnated carbon ablator (PICA)',
                                                                      'Silicone-impregnated reusable ceramic ablator (SIRCA)',
                                                                      'Super Light-Weight Ablator (SLA)-561V')),
             sg.Button('OK')],
            [sg.Text('Run Elmer Hot Case'), sg.Button('OK', key="-HOT-")],
            [sg.Text('Run Elmer Cold Case'), sg.Button('OK', key="-COLD-")],
            [sg.Submit(tooltip='Click to submit this window'), sg.Cancel()]]

        window = sg.Window('Thermal', layout, default_element_size=(40, 1), grab_anywhere=False)

        event, values = window.read()
        # print(values[1])

        window.close()
        if event == "-SYS-":
            # import pandas as pd
            # import FUNCTIONS
            from scipy import special

            thermalsystype = values[0]
            if thermalsystype == "Heat Pipe":
                # https://celsiainc.com/technology/heat-pipe/
                layout1 = [[sg.Text('Select Heat Pipe Material'),
                            sg.Listbox(values=(['Aluminum', '316 Stainless Steel']), size=(40, 8))],
                           [sg.Text('Select working fluid'), sg.Listbox(values=(
                           'Water', 'Ammonia', 'Acetone', 'Methanol', 'Toulene', 'Mercury', 'Nitrogen', 'Cesium',
                           'Potassium', 'Sodium', 'NaK'), size=(40, 8)), sg.Button('Add Power Gen')]]

                window11 = sg.Window('Heat Pipe Designer', layout1, default_element_size=(40, 10), grab_anywhere=False)
                event1, values1 = window11.read()

                # T_0 = (T_sat + ((V_v**2)/(2*C_p))
                # rho_0 = (rho_v*((T_0/T_sat)**(1/(gamma_v-1))))
                # Q_s = A_v*rho_v*lambda1*math.sqrt((gamma_v*R_v*T_0/(2*(gamma_v+1))))
                # deltaP_c = 2*sigma*math.cos(math.radians(theta))/r_c # Eqn 1.5 P 21
                # Q_c = (deltaP_c+deltaP_nh-deltaP_ah)*(2*(r_hv**2)*A_v*rho_v*lambda1*K_w*A_w*rho_l)/(L_eff*((C*f*Re*Mu*K_w*Aw*rho_l)+(2*mu*r**2*A_v*rho_v))))
                # k_eel = ()

        # import numpy as np
        # import numpy
        #
        # import math
        # import numpy
        # import numpy as np

        def ecef_to_lla(x, y, z, R):
            lat = math.asin(z / R)
            lon = math.atan2(y, x)
            alt = math.sqrt((x ** 2) + (y ** 2) + (z ** 2)) - R
            return lat, lon, alt

        GMAT = 1
        CADImport = 0

        # Planet = "Venus"

        RX = 6878
        RY = 0
        RZ = 0
        import math
        Rmag = math.sqrt((RX ** 2) + (RY ** 2) + (RZ ** 2))

        if Planet == "Mercury":
            Rplanet = 2440
        if Planet == "Venus":
            Rplanet = 6051.8
        if Planet == "Earth":
            Rplanet = 6378
        if Planet == "Moon":
            Rplanet = 1737.4
        if Planet == "Mars":
            Rplanet = 3397
        if Planet == "Jupiter":
            Rplanet = 71492
        if Planet == "Saturn":
            Rplanet = 60268
        if Planet == "Uranus":
            Rplanet = 25559
        if Planet == "Neptune":
            Rplanet = 24766
        if Planet == "Pluto":
            Rplanet = 1188.3
        if Planet == "Charon":
            Rplanet = 606

        if Rmag < 10 * Rplanet:
            InSpace = 0

        lat, lon, Alt = ecef_to_lla(RX, RY, RZ, Rplanet)

        # Alt = Rmag-Rplanet
        PlanetAngularRadius = math.asin(Rplanet / (Rplanet + Alt))  # Rad
        r = 149597870.700  # Distance from Sun in Kilometers
        Boltzman = 5.67037e-8
        AU = 149597870.700  # 1 AU in Kilometers
        SolarFlux = 1368 / ((r / AU) ** 2)  # W/m^2

        Mu = 398600
        SemimajAxis = 6878  # Km
        Alpha = math.degrees(math.acos(Rplanet / (Rplanet + Alt)))  # Deg
        EclipseAngle = math.radians(180 - (2 * Alpha))  # Rad
        OrbitPer = 2 * math.pi * math.sqrt((SemimajAxis ** 3) / Mu)
        T_eclipse = EclipseAngle * math.sqrt((SemimajAxis ** 3) / Mu)
        PercentEclipse = T_eclipse / OrbitPer

        # Spacecraft thermal and geometrical properties
        if CADImport == 0:
            SurfAbsorp = 0.5
            SolArrTopAbsorp = 0.805
            SolArrBotAbsorp = 0.60
            SurfEmmis = 0.95
            SolArrTopEmmis = 0.825
            SolArrBotEmmis = 0.80
            PowerDissipation = 9
            SAEfficiency = 0.22
            ArrArea = 1  # m^2

        SolarOffAngTheta = 0  # Deg

        if Planet == "Mercury" and InSpace == 0:
            emmittancesurf = 0.77  # +- 0.06
            Tsubsolar = 407 + (8 / math.sqrt(r / AU))  # Kelvin
            Tterminator = 110  # K
            Albedo = 0.12

            PlanetaryIR = 1192.4 / (
                    (r / AU) ** 2)  # Probably should look at this but was derived using three data points in STDH
            # Inverse square law to calculate IR
            MinPlanetaryIR = 6
            if phi <= 90:
                T = (Tsubsolar * ((math.cos(math.radians(phi))) ** 0.25)) + (Tterminator * ((phi / 90) ** 3))
            else:
                T = Tterminator

        if Planet == "Venus" and InSpace == 0:
            Albedo = 0.8  # +- 0.02
            # Limb brightening only for sensitive spacecraft components page 52
            if lat >= 0 and lat < 10:
                PlanetaryIR = 146.3
                T = - 47.6
            elif lat >= 10 and lat < 20:
                PlanetaryIR = 153.4
                T = - 44.9
            elif lat >= 20 and lat < 30:
                PlanetaryIR = 156.7
                T = - 43.7
            elif lat >= 30 and lat < 40:
                PlanetaryIR = 158.7
                T = - 43
            elif lat >= 40 and lat < 50:
                PlanetaryIR = 158.7
                T = -44.2
            elif lat >= 50 and lat < 60:
                PlanetaryIR = 152
                T = - 45.5
            elif lat >= 60 and lat < 70:
                PlanetaryIR = 138.5
                T = - 50.7
            elif lat >= 70 and lat < 80:
                PlanetaryIR = 143.5
                T = - 48.7
            elif lat >= 80 and lat <= 90:
                PlanetaryIR = 178.4
                T = - 36.2

        if Planet == "Earth":
            Albedo = 0.33
            PlanetaryIR = 260  # W/m^2
            MinPlanetaryIR = 215  # W/m^2
        # Pretty sure this came from webplotdigitizer of spacecraft thermal controls handbook data for longitude values for moon
        # but should probably check this b/c have not visited in a while
        if Planet == "Moon" and InSpace == 0:
            x = [0.160783784, 0.63, 1.243702703, 1.513702703, 2.236378378, 4.763189189, 7.470486486, 10.08754054,
                 14.23872973, 17.1, 20.65889189, 25.82596216, 29.25, 32.86493514, 37.08, 41.67267568, 47.26775676,
                 51.12, 55.02867568, 58.45791892, 61.92, 65.16, 68.4, 72.10720946, 77.58, 84.08262162, 90.31524324,
                 101.0076081, 106.2, 110.6958649, 115.92, 120.5452703, 126.1042541, 132.0061622, 138.8278216,
                 145.0553351, 149.67, 154.0706351, 157.5, 160.4327838, 163.71, 166.3888378, 170.0888108, 172.3463514,
                 174.6912162, 176.9472973, 178.0302162, 178.83, 179.2, 179.4, 179.6, 179.8, 180, 180.2, 180.72, 181,
                 181.8745784, 186.8560054, 192.7037676, 198.2266541, 207.2303514, 215.5533568, 223.7696757, 230.5422973,
                 238.041973, 245.1631622, 251.7589459, 257.8911081, 263.3057027, 269.8075946, 278.19, 287.6757568,
                 295.2561892, 299.3171351, 304.461, 311.94, 320.1633243, 328.14, 336.4071081, 342.3631622, 348.3192162,
                 354.0016216, 359.6898649]
            y = [-85.92707712, -49.9953668, -34.81479078, -16.81028279, -3.060473756, 20.81894918, 36.4731128,
                 49.27131587, 60.53410623, 68.87181467, 75.85372222, 84.79130418, 89.24633205, 93.67857957, 97.42162162,
                 101.8067432, 105.5326161, 107.9667954, 110.0513597, 112.0165021, 113.2718147, 115.0370656, 116.8023166,
                 117.9407717, 119.776834, 121.9165251, 123.3187436, 121.2374956, 119.4432432, 118.1059439, 116.0517375,
                 113.7106438, 110.9709039, 106.8403882, 100.2771921, 93.7120288, 87.38378378, 80.31677241, 73.55135135,
                 67.16007409, 59.70501931, 51.24149118, 37.9651654, 25.88628822, 9.581839368, -6.884681206,
                 -19.36078055, -35.14594595, -62.35907336, -79.73359073, -99.42471042, -111.007722, -113, -116, -118,
                 -119, -121.6305716, -128.6919215, -133.2874745, -137.1889559, -142.71976, -148.4191927, -152.5267202,
                 -155.9544715, -159.959831, -162.2168987, -165.3266778, -167.4534092, -169.6089763, -171.4951706,
                 -173.2895753, -175.2133006, -176.732031, -177.4362809, -178.5535782, -179.3706564, -180.162565,
                 -180.969112, -181.8134372, -182.0294265, -183.3509246, -182.7773766, -183.3061567]
            with warnings.catch_warnings():
                warnings.simplefilter('ignore', np.RankWarning)
                coeff = numpy.polyfit(x, y, 30)
                p = np.poly1d(coeff)
                EqSurfTemp = p(AnglefromSubsolarPoint)
            SurfaceEmmittance = 0.92  # STCH P 54

            if FeatureType == "Copernican crater":
                Albedo = 0.126
            elif FeatureType == "Apennine Mountains":
                Albedo = 0.123
            elif FeatureType == "Mare Serenitatis":
                Albedo = 0.093
            elif FeatureType == "Mare Tranquillitatis":
                Albedo = 0.092
            elif FeatureType == "Mare Fecunditatis":
                Albedo = 0.092
            elif FeatureType == "Langrenus Crater":
                Albedo = 0.129
            else:
                Albedo = 0.073
            PlanetaryIR = 1268 / ((r / AU) ** 2)
            MinPlanetaryIR = 5.2  # W/m^2

        if Planet == "Mars" and InSpace == 0:
            # https://arxiv.org/pdf/0903.2688
            # Implement this
            # https://www.nasa.gov/content/model-source-code
            PlanetaryIR = (123.25 * ((r / AU) ** 2)) - (919.72 * r / AU) + 1505.2
            MinPlanetaryIR = 30  # Near Polar Ice caps
            if lat > 80 and lat <= 90:
                MaxAlbedo = 0.5
                MinAlbedo = 0.3
            elif lat > 70 and lat <= 80:
                MaxAlbedo = 0.5
                MinAlbedo = 0.2
            elif lat > 60 and lat <= 70:
                MaxAlbedo = 0.5
                MinAlbedo = 0.2
            elif lat > 50 and lat <= 60:
                MaxAlbedo = 0.5
                MinAlbedo = 0.17
            elif lat > 40 and lat <= 50:
                MaxAlbedo = 0.28
                MinAlbedo = 0.17
            elif lat > 30 and lat <= 40:
                MaxAlbedo = 0.28
                MinAlbedo = 0.18
            elif lat > 20 and lat <= 30:
                MaxAlbedo = 0.28
                MinAlbedo = 0.22
            elif lat > 10 and lat <= 20:
                MaxAlbedo = 0.28
                MinAlbedo = 0.25
            elif lat > 0 and lat <= 10:
                MaxAlbedo = 0.28
                MinAlbedo = 0.25
            elif lat > -10 and lat <= 0:
                MaxAlbedo = 0.28
                MinAlbedo = 0.2
            elif lat > -20 and lat <= -10:
                MaxAlbedo = 0.25
                MinAlbedo = 0.18
            elif lat > -30 and lat <= -20:
                MaxAlbedo = 0.22
                MinAlbedo = 0.18
            elif lat > -40 and lat <= -30:
                MaxAlbedo = 0.22
                MinAlbedo = 0.18
            elif lat > -50 and lat <= -40:
                MaxAlbedo = 0.25
                MinAlbedo = 0.3
            elif lat > -60 and lat <= -50:
                MaxAlbedo = 0.25
                MinAlbedo = 0.4
            elif lat > -70 and lat <= -60:
                MaxAlbedo = 0.3
                MinAlbedo = 0.4
            elif lat > -80 and lat <= -70:
                MaxAlbedo = 0.4
                MinAlbedo = 0.4
            elif lat > -90 and lat <= -80:
                MaxAlbedo = 0.4
                MinAlbedo = 0.4
            # For Mars temp data maybe use MarsPerihelionSurfaceTemp image or NASA Mars Climate Model when it comes out
            latalbedo = 0
        if Planet == "Jupiter" and InSpace == 0:
            Albedo = 0.343
            PlanetaryIR = (-0.773 * ((r / AU) ** 2)) + 7.4558 * (r / AU) - 4.267
            latalbedo = 0
        if Planet == "Saturn" and InSpace == 0:
            Albedo = 0.342
            PlanetaryIR = 3E-14 * ((r / AU) ** 2) - (0.1847 * (r / AU)) + 6.3703
            latalbedo = 0
        if Planet == "Uranus" and InSpace == 0:
            Albedo = 0.343
            PlanetaryIR = (0.0065 * ((r / AU) ** 2)) - (0.3467 * (r / AU)) + 4.8896
            latalbedo = 0
        if Planet == "Neptune" and InSpace == 0:
            Albedo = 0.282
            PlanetaryIR = 0.52
            latalbedo = 0
        if Planet == "Pluto" and InSpace == 0:
            Albedo = 0.47
            PlanetaryIR = (0.0005 * ((r / AU) ** 2)) - 0.0687 * (r / AU) + 2.3598
            latalbedo = 0
        if Planet == "Charon" and InSpace == 0:
            Albedo = 0.47
            PlanetaryIR = (0.0005 * ((r / AU) ** 2)) - 0.0687 * (r / AU) + 2.3598
            latalbedo = 0

        KaCorrFactor = 0.664 + (0.521 * PlanetAngularRadius) - (0.203 * PlanetAngularRadius * PlanetAngularRadius)
        F = (1 - math.cos(math.radians(PlanetAngularRadius))) / 2
        A_solar = 1
        A_albedo = 1
        A_planetary = 1
        Js = SolarFlux
        if latalbedo == 0:
            Ja = Js * Albedo * ((GSE_x ** 2) / (Rmag ** 2))
        else:
            Ja = Js * Albedo
        Jp = PlanetaryIR * ((R_rad / Rmag) ** 2)

        Qin = Js * alpha * A_solar + Ja * alpha * A_albedo * Albedo * SurfAbsorp * KaCorrFactor * F + Jp * epsilon * A_planetary + PowerDissipation

        Qout = Qin

        print(Qin)

        # T =

        #
        # # Dont think these consider off angle pointing of solar arrays
        # MaxAbsorbedSA =(SolarFlux*ArrArea*SolArrTopAbsorp)+(PlanetaryIR*ArrArea*SolArrBotEmmis*(math.sin(PlanetAngularRadius)*math.sin(PlanetAngularRadius)))+(SolarFlux*Albedo*ArrArea*SolArrBotAbsorp*KaCorrFactor*math.sin(PlanetAngularRadius)*math.sin(PlanetAngularRadius))
        # # MinAbsorbedSA =(SolarFlux*ArrArea*SolArrTopAbsorp)+(MinPlanetaryIR*ArrArea*SolArrBotEmmis*(math.sin(PlanetAngularRadius)*math.sin(PlanetAngularRadius)))+(SolarFlux*Albedo*ArrArea*SolArrBotAbsorp*KaCorrFactor*math.sin(PlanetAngularRadius)*math.sin(PlanetAngularRadius))
        #
        # TmaxArr =(((SolarFlux*SolArrTopAbsorp)+(PlanetaryIR*SolArrBotEmmis*math.sin(PlanetAngularRadius)*math.sin(PlanetAngularRadius))+(SolarFlux*Albedo*SolArrBotAbsorp*KaCorrFactor*math.sin(PlanetAngularRadius)*math.sin(PlanetAngularRadius))-(SAEfficiency*SolarFlux))/(Boltzman*(SolArrTopEmmis+SolArrTopAbsorp)))**0.25
        # # TminArr =(((SolarFlux*SolArrTopAbsorp)+(MinPlanetaryIR*SolArrBotEmmis*math.sin(PlanetAngularRadius)*math.sin(PlanetAngularRadius))+(SolarFlux*Albedo*SolArrBotAbsorp*KaCorrFactor*math.sin(PlanetAngularRadius)*math.sin(PlanetAngularRadius))-(SAEfficiency*SolarFlux))/(Boltzman*(SolArrTopEmmis+SolArrTopAbsorp)))**0.25
        #
        # MaxEmittedArrRad = Boltzman * ArrArea * (TmaxArr ** 4) * (SolArrTopEmmis + SolArrBotEmmis)
        # # MinEmittedArrRad = Boltzman * ArrArea * (TminArr ** 4) * (SolArrTopEmmis + SolArrBotEmmis)
        #
        # MaxArrHeatGen = MaxAbsorbedSA-MaxEmittedArrRad
        # MaxSpcHeatGen = (CrossSectArea * SolarFlux * SCSurfAbsorp) + (SCSurfArea * ShadowFactorF * PlanetaryIR * SCSurfEmmis) + (SCSurfArea * ShadowFactorF * SolarFlux * Albedo * SCSurfAbsorp * KaCorrFactor) + MaxPowerDiss
        # TmaxSC =(((CrossSectArea*SolarFlux*SCSurfAbsorp)+(SCSurfArea*ShadowFactorF*PlanetaryIR*SCSurfEmmis)+(SCSurfArea*ShadowFactorF*SolarFlux*Albedo*SCSurfAbsorp*KaCorrFactor)+(MaxPowerDiss))/(SCSurfArea*Boltzman*SCSurfEmmis))**0.25 # Good
        #
        # print(TmaxSC)
        #
        # # TminSC =(((CrossSectArea*SolarFlux*SCSurfAbsorp)+(SCSurfArea*ShadowFactorF*MinPlanetaryIR*SCSurfEmmis)+(SCSurfArea*ShadowFactorF*SolarFlux*Albedo*SCSurfAbsorp*KaCorrFactor)+(MinPowerDiss))/(SCSurfArea*Boltzman*SCSurfEmmis))**0.25
        # # TminSC1 = ((CrossSectArea*ShadowFactorF**SCSurfEmmis*PlanetaryIR)+MaxPowerDiss)/CrossSectArea*Boltzman*SCSurfEmmis
        # RadAreaReq =MaxArrHeatGen/((-SolarFlux*SCSurfAbsorp*math.cos(math.degrees(SolarOffAngTheta)))+(Boltzman*SCSurfEmmis*(TmaxSC**4)))
        # ReqEclipsePower =RadAreaReq*Boltzman*SCSurfEmmis*((273.15+5)**4)
        #
        # # Apparently these numbers are wrong so fix that
        #
        # # print(RadAreaReq)
        # # print(ReqEclipsePower)

        def FreeMolecHeatingRate(Density, Vel):
            Q_FMH = (0.5) * Density * (Vel ** 3)
            return Q_FMH

        def EclipseFraction(BetaAngle, OrbitalAlt, EarthRadius, BetaAngleEclipseBegin):
            EclipseFraction = (1 / 180) * (math.acos(math.sqrt((OrbitalAlt ** 2) + (2 * EarthRadius * OrbitalAlt))))

        # http://what-when-how.com/energy-engineering/heat-exchangers-and-heat-pipes-energy-engineering/

        """
        Thermal design flow


        List components
        List component locations
        List component location constraints
        List component geometry points
        List max/min temp ranges
        List component absorbance and emmitance
        List component thermal conductivity
        Pressurized or unpressurized
        Try:
            Thermal paint of s/c region
            Surface finish of s/c region
            Select another component with higher temp margins
            Thermally isolate mechanically
            Insulate
            Thermal filler to improve coupling and heat transfer
            Thermal doublers like heat fins
            Move component outwards or inwards
            Transfer heat outwards using conduction path
        Else:
            Heat pipe
            Heat pump
            Radiator
            Heat plate
            Heat exchanger
            Evaporator
            Heater
            Radioisotope heater unit
            Louvers
            Thermoelectric cooler
            Sun shield
            Fans (pressurized)
        Else 2:
            Adjust spacecraft attitude
            Adjust spacecraft orbit


        """

        def HeatTsfrCoef(P, name1, name2, Mac1, Mac2, method):
            # Refer to spacecraft thermal controls handbook page 251/252
            he = 0
            if Mac1 == "Flame Cutting":
                Ra1 = (50 + 8) / 2
            elif Mac1 == "Snagging":
                Ra1 = (50 + 4) / 2
            elif Mac1 == "Sawing":
                Ra1 = (50 + 1.1) / 2
            elif Mac1 == "Planing/Shaping":
                Ra1 = (25 + 0.4) / 2
            elif Mac1 == "Drilling":
                Ra1 = (12.5 + 0.9) / 2
            elif Mac1 == "Chemical Milling":
                Ra1 = (12.5 + 0.9) / 2
            elif Mac1 == "Electrical Discharge":
                Ra1 = (12.5 + 0.9) / 2
            elif Mac1 == "Milling":
                Ra1 = (25 + 0.3) / 2
            elif Mac1 == "Broaching":
                Ra1 = (6.3 + 0.4) / 2
            elif Mac1 == "Reaming":
                Ra1 = (6.3 + 0.4) / 2
            elif Mac1 == "Electron Beam":
                Ra1 = (6.3 + 0.2) / 2
            elif Mac1 == "Laser":
                Ra1 = (6.3 + 0.2) / 2
            elif Mac1 == "Electrochemical":
                Ra1 = (12.5 + 0.05) / 2
            elif Mac1 == "Boring_Turning":
                Ra1 = (20 + 0.035) / 2
            elif Mac1 == "Barrel Finishing":
                Ra1 = (2.8 + 0.05) / 2
            elif Mac1 == "Electrolytic Grinding":
                Ra1 = (0.7 + 0.075) / 2
            elif Mac1 == "Roller Burnishing":
                Ra1 = (0.7 + 0.075) / 2
            elif Mac1 == "Grinding":
                Ra1 = (5.2 + 0.02) / 2
            elif Mac1 == "Horning":
                Ra1 = (1.2 + 0.025) / 2
            elif Mac1 == "Electro Polish":
                Ra1 = (1.2 + 0.012) / 2
            elif Mac1 == "Polishing":
                Ra1 = (0.7 + 0.025) / 2
            elif Mac1 == "Lapping":
                Ra1 = (0.7 + 0.025) / 2
            elif Mac1 == "Super Finishing":
                Ra1 = (0.7 + 0.025) / 2
            elif Mac1 == "Sand Casting":
                Ra1 = (40 + 5.2) / 2
            elif Mac1 == "Hot Rolling":
                Ra1 = (40 + 5.2) / 2
            elif Mac1 == "Forging":
                Ra1 = (20 + 1) / 2
            elif Mac1 == "Perm Mold Casting":
                Ra1 = (4.2 + 0.4) / 2
            elif Mac1 == "Investment Casting":
                Ra1 = (4.2 + 0.25) / 2
            elif Mac1 == "Extruding":
                Ra1 = (9.4 + 0.2) / 2
            elif Mac1 == "Cold Rolling_Drawing":
                Ra1 = (4.2 + 0.1) / 2
            elif Mac1 == "Die Casting":
                Ra1 = (1.8 + 0.175) / 2

            if Mac2 == "Flame Cutting":
                Ra2 = (50 + 8) / 2
            elif Mac2 == "Snagging":
                Ra2 = (50 + 4) / 2
            elif Mac2 == "Sawing":
                Ra2 = (50 + 1.1) / 2
            elif Mac2 == "Planing/Shaping":
                Ra2 = (25 + 0.4) / 2
            elif Mac2 == "Drilling":
                Ra2 = (12.5 + 0.9) / 2
            elif Mac2 == "Chemical Milling":
                Ra2 = (12.5 + 0.9) / 2
            elif Mac2 == "Electrical Discharge":
                Ra2 = (12.5 + 0.9) / 2
            elif Mac2 == "Milling":
                Ra2 = (25 + 0.3) / 2
            elif Mac2 == "Broaching":
                Ra2 = (6.3 + 0.4) / 2
            elif Mac2 == "Reaming":
                Ra2 = (6.3 + 0.4) / 2
            elif Mac2 == "Electron Beam":
                Ra2 = (6.3 + 0.2) / 2
            elif Mac2 == "Laser":
                Ra2 = (6.3 + 0.2) / 2
            elif Mac2 == "Electrochemical":
                Ra2 = (12.5 + 0.05) / 2
            elif Mac2 == "Boring_Turning":
                Ra2 = (20 + 0.035) / 2
            elif Mac2 == "Barrel Finishing":
                Ra2 = (2.8 + 0.05) / 2
            elif Mac2 == "Electrolytic Grinding":
                Ra2 = (0.7 + 0.075) / 2
            elif Mac2 == "Roller Burnishing":
                Ra2 = (0.7 + 0.075) / 2
            elif Mac2 == "Grinding":
                Ra2 = (5.2 + 0.02) / 2
            elif Mac2 == "Horning":
                Ra2 = (1.2 + 0.025) / 2
            elif Mac2 == "Electro Polish":
                Ra2 = (1.2 + 0.012) / 2
            elif Mac2 == "Polishing":
                Ra2 = (0.7 + 0.025) / 2
            elif Mac2 == "Lapping":
                Ra2 = (0.7 + 0.025) / 2
            elif Mac2 == "Super Finishing":
                Ra2 = (0.7 + 0.025) / 2
            elif Mac2 == "Sand Casting":
                Ra2 = (40 + 5.2) / 2
            elif Mac2 == "Hot Rolling":
                Ra2 = (40 + 5.2) / 2
            elif Mac2 == "Forging":
                Ra2 = (20 + 1) / 2
            elif Mac2 == "Perm Mold Casting":
                Ra2 = (4.2 + 0.4) / 2
            elif Mac2 == "Investment Casting":
                Ra2 = (4.2 + 0.25) / 2
            elif Mac2 == "Extruding":
                Ra2 = (9.4 + 0.2) / 2
            elif Mac2 == "Cold Rolling_Drawing":
                Ra2 = (4.2 + 0.1) / 2
            elif Mac2 == "Die Casting":
                Ra2 = (1.8 + 0.175) / 2

            Hc1 = Properties(name1, "VICKERS HARDNESS")
            Hc2 = Properties(name2, "VICKERS HARDNESS")
            if Hc2 <= Hc1:
                H_c = Hc2
            else:
                H_c = Hc1

            # Vickers Hardness Test is used from http://asm.matweb.com/search/SpecificMaterial.asp?bassnum=MA6061T6 for materials
            ka = Properties(name1, "HEAT TRANSFER COEFF")
            kb = Properties(name2, "HEAT TRANSFER COEFF")

            # Ar_Ae = 0.5*math.erf(lambda1/(math.sqrt(2)))
            sigma1 = Ra1
            sigma2 = Ra2
            m1 = 0.076 * ((sigma1 * 1000000) ** 0.52)
            m2 = 0.076 * ((sigma2 * 1000000) ** 0.52)
            m = math.sqrt((m1 ** 2) + (m2 ** 2))
            sigma = math.sqrt((sigma1 ** 2) + sigma2 ** 2)
            ks = (2 * ka * kb) / (ka + kb)
            E1 = Properties(name1, "YOUNGS_MODULUS")
            E2 = Properties(name2, "YOUNGS_MODULUS")
            pratio1 = Properties(name1, "POISSONS RATIO")
            pratio2 = Properties(name2, "POISSONS RATIO")
            Eprime = 1 / (((1 - pratio1 ** 2) / E1) + ((1 - pratio2 ** 2) / E2))
            gamma = H_c / (Eprime * m)
            if method == "Mikic":

                if gamma > 1.665:  # Consider elastic
                    he = 1.55 * (ks * m / sigma) * ((1.4142135623 * P / Eprime * m) ** 0.94)
                elif gamma <= 1.665:  # Consider plastic
                    he = 1.13 * (ks * m / sigma) * ((P / H_c) ** 0.94)

            # if method == "McKinzie":
            #     he = k*P/(I*delta)

            if method == "Yovanovich Plastic":
                lambda1 = math.sqrt(2) * special.erfcinv((2 * P) / H_c)
                he = (ks * m * math.exp((-(lambda1 ** 2) / 2))) / ((2 * math.sqrt(2 * math.pi)) * sigma * (
                        (1 - math.sqrt(0.5 * math.erfc(lambda1 / 1.4142135623))) ** 1.5))

            if method == "Yovanovich Elastic":
                lambda1 = math.sqrt(2) * special.erfcinv((5.65685425 * P) / (Eprime * m))
                he = (ks * m * math.exp((-lambda1 ** 2) / 2)) / (
                        4 * 1.77245385 * sigma * ((1 - math.sqrt(0.25 * math.erfc(lambda1 / 1.41421356))) ** 1.5))
            return he

        def HeatTsfrFromGraph8_9(pressure, material):
            pressure = pressure / 1000  # Convert Pa to KPa

            if material == "Aluminum (2024-T3) 1.2-1.6 Vacuum":
                datasheet = "Mat1"
            if material == "Aluminum (2024-T3) 0.2-0.5 Vacuum":
                datasheet = "Mat2"
            if material == "Aluminum (2024-T3) 0.2-0.5 (wavy) Vacuum":
                datasheet = "Mat3"
            if material == "Aluminum (75S-T6) 3 Air":
                datasheet = "Mat4"
            if material == "Aluminum (75S-T6) 1.6 Air":
                datasheet = "Mat5"
            if material == "Aluminum (75S-T6) 0.3 Air":
                datasheet = "Mat6"
            if material == "Aluminum (2024-T3) 0.2 (wavy) Lead foil 8 mil":
                datasheet = "Mat7"
            if material == "Aluminum (75S-T6) 3 Brass foil 1 mil":
                datasheet = "Mat8"
            if material == "Stainless 304 1.1-1.5 Vacuum":
                datasheet = "Mat9"
            if material == "Stainless 304 0.3-0.4 Vacuum":
                datasheet = "Mat10"
            if material == "Stainless 416 2.5 Air":
                datasheet = "Mat11"
            if material == "Stainless 416 2.5 Brass foil 1 mil":
                datasheet = "Mat12"
            if material == "Magnesium (AZ-31B) 1.3-1.5 (oxidized) Vacuum":
                datasheet = "Mat13"
            if material == "Magnesium (AZ-31B) 0.2-0.4 (oxidized) Vacuum":
                datasheet = "Mat14"
            if material == "Copper (OFHC) 0.2 Vacuum":
                datasheet = "Mat15"
            if material == "Stainless/Aluminum 0.8/1.6 Air":
                datasheet = "Mat16"
            if material == "Iron/Aluminum Air":
                datasheet = "Mat17"
            if material == "Tungsten/Graphite Air":
                datasheet = "Mat18"

            df = pd.read_excel(r"THERMAL\\ThermalTestProperties1.xlsx",
                               sheet_name=datasheet)
            df.columns = ["X", "Y"]
            x = df["X"].to_numpy()
            y = df["Y"].to_numpy()
            lowest_p = x[0]
            if pressure < x[0]:
                print("Pressure Too Low For Given Dataset!")
            elif pressure > x[-1]:
                print("Pressure Too High For Given Dataset!")
            else:
                with warnings.catch_warnings():
                    warnings.simplefilter('ignore', np.RankWarning)
                    coeff = numpy.polyfit(x, y, 30)
                    p = np.poly1d(coeff)
                    heattsfr = p(pressure)
                return heattsfr

        def bolts(t1, t2, kh, An, Torque):
            if t1 < t2:
                t_t = t1
            else:
                t_t = t2
            heattsfr = (1 / t_t) * 54.7 * kh * ((An / ((t_t ** 3) * (Torque ** 0.5))) ** -0.764)
            return heattsfr

        def insulation():
            pass

        def thermalIsolator():
            pass

        # def louver(Qdot, absorb_ext, emis_ext, S, theta, albedo, IR):
        #     Fe =
        #
        #     A = Qdot/(Fe*((sigma*(T**4))-((absorb_ext/emis_ext)*(S*(math.sin(math.radians(theta))+albedo))+IR))
        #     return A

        def heater():
            pass

        def heatpipe():
            pass

        def radiator():
            # Eqn 6.5
            thetastar = Ts / Tdelta
            xi = sigma * (L ** 2) * (T ** 3) * B * (emis1 + emis2) / (k * t)
            efficiency = (1 - 1.125 * xi + 1.6 * (xi ** 2)) * (1 - (thetastar ** 4))

            pass

        def heatsink():
            if material == "Beryllium":
                pass

        def PCM():

            pass

        def fluidloop():
            pass

        def sunshield():
            pass

        def RHU():
            pass

        def MMRTG():
            pass

        def variableEmittance():
            # https: // thermal.gsfc.nasa.gov / Technology / VaryE.html
            pass

        def dewar():
            pass

        def thermoeleccooler():
            pass

        print(HeatTsfrFromGraph8_9(1000000, "Tungsten/Graphite Air"))
        # print(HeatTsfrCoef(100000000, "6061-T6", "6061-T6", "Chemical Milling", "Chemical Milling", "Yovanovich Elastic"))

        # def GasGap(Pr, gamma, ]):
        #     +
        #     M = (((2-TAC1)/TAC1) + ((2- TAC2)/TAC2))*(2*gamma/(gamma+1))*(Lambda1/Pr)
        #     Mstar = M/R_p
        #     f = 1 + (0.304/((R_p/sigma)*(1+(M/R_p))))-(2.29/(((R_p/sigma)*(1+(M/R_p)))**2))
        #     h_g = k_g/(R_p*(f + Mstar))

















        if event == "Quit":
            window.close()
        elif event == "-HOT-":
            import FemGui
            import ObjectsFem
            ObjectsFem.makeAnalysis(FreeCAD.ActiveDocument, 'Analysis')
            FemGui.setActiveAnalysis(FreeCAD.ActiveDocument.ActiveObject)
            ObjectsFem.makeSolverElmer(FreeCAD.ActiveDocument)
            FemGui.getActiveAnalysis().addObject(FreeCAD.ActiveDocument.ActiveObject)

             ### Begin command FEM_ConstraintHeatflux
            App.activeDocument().addObject("Fem::ConstraintHeatflux", "ConstraintHeatflux")
            App.activeDocument().ConstraintHeatflux.AmbientTemp = 300.0
            App.activeDocument().ConstraintHeatflux.FilmCoef = 10.0
            App.activeDocument().ConstraintHeatflux.Scale = 1
            App.activeDocument().Analysis.addObject(App.activeDocument().ConstraintHeatflux)
            for amesh in App.activeDocument().Objects:
                if "" == amesh.Name:
                    amesh.ViewObject.Visibility = True
                elif "Mesh" in amesh.TypeId:
                    aparttoshow = amesh.Name.replace("_Mesh", "")
                    for apart in App.activeDocument().Objects:
                        if aparttoshow == apart.Name:
                            apart.ViewObject.Visibility = True
                amesh.ViewObject.Visibility = False

            App.ActiveDocument.recompute()
            Gui.activeDocument().setEdit('ConstraintHeatflux')
             ### End command FEM_ConstraintHeatflux
             # Gui.Selection.clearSelection()
            App.ActiveDocument.ConstraintHeatflux.ConstraintType = "DFlux"
             # Gui.Selection.addSelection(App.ActiveDocument.Name,'Body','Pad.Face6',13.9455,-16.7959,10)
            App.ActiveDocument.ConstraintHeatflux.AmbientTemp = 300.000000
            App.ActiveDocument.ConstraintHeatflux.FilmCoef = 10.000000
            App.ActiveDocument.ConstraintHeatflux.Scale = 7
            App.ActiveDocument.ConstraintHeatflux.References = [(App.ActiveDocument.Pad, "Face6")]
            App.ActiveDocument.recompute()
            Gui.activeDocument().resetEdit()

            
            
            
            
        elif event == "-COLD-":
            import FemGui
            import ObjectsFem
            ObjectsFem.makeAnalysis(FreeCAD.ActiveDocument, 'Analysis')
            FemGui.setActiveAnalysis(FreeCAD.ActiveDocument.ActiveObject)
            ObjectsFem.makeSolverElmer(FreeCAD.ActiveDocument)
            FemGui.getActiveAnalysis().addObject(FreeCAD.ActiveDocument.ActiveObject)
        elif event == "-SYS-":
            if values[0] == "Heat Pipe":
                pass
            if values[0] == "Heat Pump":
                Q = 50 # m^3/s
                dP = 1000 # Pa
                efficiency = 0.78
                P = Q*dP/efficiency



                addPowerSystem()

            elif values[0] == "Radiator":
                pass
            elif values[0] == "Evaporator":
                pass
            elif values[0] == "Phase Change Material":
                Q = m*C*()
            elif values[0] == "Cold Plate":
                pass
            elif values[0] == "Louver":
                pass
            elif values[0] == "Heater":
                awg = "40"
                l = 40 # m
                rho = 1.724e-8
                V = 200 # volts

                # Atot = spacing*height
                # https://www.eplan.help/es-ES/Infoportal/Content/harness/2.8/EPLAN_Help.htm#htm/LIB_AWG_to_mm.htm
                with open(SCDesignerPath + "\\POWER\\AWG_WIRE_AREAS.csv", "r") as f:
                    gauges = csv.reader(f, delimiter=',')
                    for row in gauges:
                        if awg == row[0]:
                            A = float(row[1])/1000000

                R = (rho*l/A)
                P = V*V/R # = I**2*R
                I = V/R
                addPowerSystem("Heater",V,I)
        elif event == "-COAT-":
            window.close()

            i = 0
            MaterialList = []
            with open(SCDesignerPath + '\\THERMAL\\Surface Finish.csv', 'r') as csvfile:
                materials = csv.reader(csvfile, delimiter=',')
                for row in materials:
                    if i == 0:
                        Header = row
                        print(Header)
                        i = 1
                        continue
                    MaterialList.append(row)

            MaterialListGeometry = []
            userSel = values[0]
            for Material in MaterialList:
                if Material[4].find(userSel) > -1:
                    print(Material[1] + " " + Material[0] + " " + Material[2])
                    MaterialListGeometry.append(Material)
            Header = ["COMPONENT", "TYPE", "ABSORPTANCE", "EMITTANCE", "COST", "REF"]
            print(Header)

            layout = [[sg.Table(MaterialListGeometry,
                                headings=Header,
                                auto_size_columns=True,
                                key='Table')]]

            win = sg.Window('Select Surface Coating',
                            layout, keep_on_top=True, finalize=True)

            myTable = win['Table']
            myTable.bind('<Button-1>', "Click")

            while True:
                event, values = win.read()
                # print(event, values)
                if event in (None,):
                    win.close()
                    break
                elif event == 'TableClick':
                    try:
                        bind_event = myTable.user_bind_event
                        col = myTable.Widget.identify_column(bind_event.x)
                        row_iid = myTable.Widget.identify_row(bind_event.y)
                        row = myTable.Widget.item(row_iid)
                        win.close()

                        print(row)

                        # Material = str(row['values'][0])
                        # Classification = str(row['values'][1])
                        # Name = str(row['values'][2])
                        # Grade = str(row['values'][3])
                        # Geometry = str(row['values'][4])
                        # Condition = float(row['values'][5])
                        # Thickness = float(row['values'][6])
                        # UltTensStr = float(row['values'][7])
                        # TensYieldStr = float(row['values'][8])
                        # CompYieldStr = float(row['values'][9])
                        # UltShearStr = float(row['values'][10])
                        # BRU2 = float(row['values'][11])
                        # YoungsM = float(row['values'][10])
                        # ShearMod = float(row['values'][10])
                        # PoissonsR = float(row['values'][10])
                        # Density = float(row['values'][10])
                        # Cval = float(row['values'][10])
                        # Kval = float(row['values'][10])
                        # Alpha = float(row['values'][10])
                        # print(Material + " " + Name + " selected.")
                        if os.path.isdir(SCDesignerPath + "\\" +
                                         str(
                                             App.ActiveDocument.Label)):
                            pass
                        else:
                            os.mkdir(SCDesignerPath + "\\" + str(
                                App.ActiveDocument.Label))

                        with open(
                                SCDesignerPath + "\\THERMAL\\" + str(
                                    App.ActiveDocument.Label) + ".csv", 'w+') as f:
                            f.write(str(Material) + "," + str(Classification) + "," + str(Name) + "," + str(
                                Grade) + "," + str(Geometry) + "," + str(Condition) + "," + str(Thickness) + "," + str(
                                UltTensStr) + "," + str(TensYieldStr) + "," + str(CompYieldStr) + "," + str(
                                UltShearStr) + "," + str(BRU2) + "," + str(YoungsM) + "," + str(ShearMod) + "," + str(
                                PoissonsR) + "," + str(Density) + "," + str(Cval) + "," + str(Kval) + "," + str(Alpha))
                            # f.close()

                    except:
                        pass
        return
        
class Aero():
    """My new command"""

    def GetResources(self):
        return {'Pixmap'  : 'C:\\Users\\' + username + '\\AppData\\Roaming\\FreeCAD\\Mod\\SpacecraftDesigner\\Icons\\Aero.jpg',
                'Accel' : "Shift+A", # a default shortcut (optional)
                'MenuText': "Aero",
                'ToolTip' : "Define Spacecraft Aerodynamic Characteristics"}

    def Activated(self):     

        layout = [
            [sg.Text('Open Fuselage Designer'), sg.Button('OK',key="-FUSELAGE-")],
            [sg.Text('Add Aero Surface'), sg.InputCombo(('Wing', 'Horizontal Stabilizer', 'Vertical Stabilizer', 'Control Surface')), sg.Button('OK', key="-SURF-")],
            [sg.Text('Conduct Entry Analysis'), sg.Button('OK', key="-ENTRY-")],
            [sg.Text('Parachute Designer'), sg.Button('OK')],
            [sg.Text('Run Vortex Lattice Method Computational Fluid Dynamics (CFD) (Peter Sharpe)'), sg.Button('OK', key="-VLM-")],
            [sg.Text('Run DATCOM'), sg.Button('OK')],
            [sg.Text('Run OpenFOAM Computational Fluid Dynamics (CFD)'), sg.Button('OK')],
            [sg.Submit(tooltip='Click to submit this window'), sg.Cancel()]]


        window = sg.Window('Aerodynamics', layout, default_element_size=(40, 1), grab_anywhere=False)      

        event, values = window.read()

        window.close()    
        if event == "Cancel":
            window.close()
        elif event == "Submit":
            window.close()
            print(values)
        elif event == "-VLM-":
            import aerosandbox as asb
            import aerosandbox.numpy as np

            wing_airfoil = asb.Airfoil("sd7037")
            tail_airfoil = asb.Airfoil("naca0010")

            ### Define the 3D geometry you want to analyze/optimize.
            # Here, all distances are in meters and all angles are in degrees.
            airplane = asb.Airplane(
                name="Peter's Glider",
                xyz_ref=[0, 0, 0],  # CG location
                wings=[
                    asb.Wing(
                        name="Main Wing",
                        symmetric=True,  # Should this wing be mirrored across the XZ plane?
                        xsecs=[  # The wing's cross ("X") sections
                            asb.WingXSec(  # Root
                                xyz_le=[0, 0, 0],
                                # Coordinates of the XSec's leading edge, relative to the wing's leading edge.
                                chord=0.18,
                                twist=2,  # degrees
                                airfoil=wing_airfoil,  # Airfoils are blended between a given XSec and the next one.
                            ),
                            asb.WingXSec(  # Mid
                                xyz_le=[0.01, 0.5, 0],
                                chord=0.16,
                                twist=0,
                                airfoil=wing_airfoil,
                            ),
                            asb.WingXSec(  # Tip
                                xyz_le=[0.08, 1, 0.1],
                                chord=0.08,
                                twist=-2,
                                airfoil=wing_airfoil,
                            ),
                        ]
                    ),
                    asb.Wing(
                        name="Horizontal Stabilizer",
                        symmetric=True,
                        xsecs=[
                            asb.WingXSec(  # root
                                xyz_le=[0, 0, 0],
                                chord=0.1,
                                twist=-10,
                                airfoil=tail_airfoil,
                            ),
                            asb.WingXSec(  # tip
                                xyz_le=[0.02, 0.17, 0],
                                chord=0.08,
                                twist=-10,
                                airfoil=tail_airfoil
                            )
                        ]
                    ).translate([0.6, 0, 0.06]),
                    asb.Wing(
                        name="Vertical Stabilizer",
                        symmetric=False,
                        xsecs=[
                            asb.WingXSec(
                                xyz_le=[0, 0, 0],
                                chord=0.1,
                                twist=0,
                                airfoil=tail_airfoil,
                            ),
                            asb.WingXSec(
                                xyz_le=[0.04, 0, 0.15],
                                chord=0.06,
                                twist=0,
                                airfoil=tail_airfoil
                            )
                        ]
                    ).translate([0.6, 0, 0.07])
                ],
                fuselages=[
                    asb.Fuselage(
                        name="Fuselage",
                        xsecs=[
                            asb.FuselageXSec(
                                xyz_c=[0.8 * xi - 0.1, 0, 0.1 * xi - 0.03],
                                radius=0.6 * asb.Airfoil("dae51").local_thickness(x_over_c=xi)
                            )
                            for xi in np.cosspace(0, 1, 30)
                        ]
                    )
                ]
            )

            vlm = asb.VortexLatticeMethod(
                airplane=airplane,
                op_point=asb.OperatingPoint(
                    velocity=25,  # m/s
                    alpha=5,  # degree
                )
            )

            aero = vlm.run()  # Returns a dictionary
            for k, v in aero.items():
                print(f"{k.rjust(4)} : {v}")


        elif event == "-ENTRY-":
            # import FundAeroSuite
            import math
            import airfoils
            '''
            Aero flow

            Determine target body atmospheric conditions, pressure temp, density as function of altitude
            Determine Orbital velocity at entry interface
            Determine cross range requirements
            Determine winged or capsule
            Determine vehicle mass
            Determine static stability
            Determine re-entry angle of attack range
            Determine drag coefficient range
            Determine ballistic coefficient range
            Determine maximum stagnation temperature 
            Determine heating rate
            Determine total heat that must be absorped
            Determine ablative or reusable tiles
            Determine TPS material



            '''
            import warnings
            from scipy.optimize import curve_fit
            import numpy as np
            import numpy
            import math

            altitude = 250

            if new_vehicle.destination == "Mars":
                x = [0, 7.88367763, 14.35631833, 22.0682227, 29.84041557, 39.47652801, 49.67533314, 56.74806773,
                     65.67690671, 73.58977276, 84.84362669, 99.26262705, 108.5438336, 118.0190503, 125.4630058,
                     131.4611536, 133.951353, 136.5410182, 139.0027988, 143.3636672, 148.2872283, 154.7845705,
                     161.3786255, 169.0365215, 178.0982184, 185.8645499, 192.458605, 200.371471, 208.3952452,
                     219.8898739, 232.9021426, 239.2324354, 246.96946, 254.7064846, 262.4435092, 270.1805337,
                     277.9175583, 285.6545829, 293.3916075]
                y = [207.5328181, 207.5328181, 195.6986873, 183.8645565, 173.8510612, 161.4707398, 150.7896782,
                     144.7208931, 140.1693044, 137.4383511, 136.5280334, 137.4383511, 145.3846154, 156.099865,
                     163.8375659, 177.6946251, 197.5193228, 218.0014722, 237.5733039, 260.1491841, 279.6299841,
                     299.9300699, 314.9503128, 326.7844436, 334.9773034, 340.4392099, 343.1701632, 345.3846154,
                     345.3846154, 346.8114342, 347.7217519, 348.6320697, 348.6320697, 348.6320697, 348.6320697,
                     348.6320697, 348.6320697, 348.6320697, 348.6320697]
                Rspec = 188.92
                gamma = 1.2941
            if new_vehicle.destination == "Venus":
                x = [0, 1.193328451, 3.353666484, 5.756043267, 7.033777203, 9.80328032, 13.24098102, 16.114733,
                     18.92261422, 21.79190039, 24.85656597, 27.69514967, 29.49479941, 30.68350669, 32.37253271,
                     34.61690926, 37.46691123, 40.17989388, 42.84263611, 46.4599463, 48.90163068, 51.46891611,
                     53.30939014, 55.39018084, 58.11572359, 62.51176029, 66.93907875, 70.77630927, 74.66567608,
                     78.82615156, 84.17533432, 86.84992571, 89.80626367, 94.27934621, 97.25111441, 101.3434178,
                     104.3833581, 107.7733541, 110.6240713, 113.8930163, 119.8365527, 126.9687964, 136.5410182,
                     144.7000623, 151.5461568, 158.9080529, 167.0403021, 177.6175851, 182.4942551, 189.3759287,
                     197.4407799, 204.7675077, 212.5045323, 220.2415569, 227.9785815, 235.715606, 243.1712843,
                     248.2169391]
                y = [737, 727.6837198, 708.3376273, 689.6370997, 673.6155073, 655.4091523, 630.2843823, 608.2026745,
                     587.3376137, 563.4670593, 539.5387069, 517.404981, 502.3076923, 487.6923077, 472.435284,
                     456.0495645, 433.1615753, 414.4025273, 396.2286836, 375.9416023, 355.3684211, 335.8876212,
                     313.4331166, 295.1509017, 270.344743, 250.8639431, 236.9230769, 225.2840142, 213.8461538,
                     198.4615385, 181.5384615, 173.8461538, 169.2994725, 164.6153846, 169.2307692, 169.2994725,
                     166.1538462, 161.1066127, 156.9230769, 153.8461538, 156.9230769, 163.0769231, 171.120108,
                     181.1336032, 197.9239085, 212.0844068, 219.3669488, 223.9185376, 226.6494909, 226.9230769,
                     227.5598086, 228.4701264, 228.4701264, 228.4701264, 228.4701264, 228.4701264, 228.4701264,
                     227.6923077]
                Rspec = 188.92
                gamma = 1.2857
            if new_vehicle.destination == "Neptune":
                x = [0, 6.691863238, 12.74862491, 19.66505597, 23.82663738, 29.27772288, 33.65527489, 38.77316214,
                     44.04840617, 49.10846954, 53.42661778, 58.61812779, 63.39096763, 66.90779698, 71.69390788,
                     76.43254315, 81.91293557, 86.60204137, 90.11887073, 94.9334196, 99.61430999, 103.6586637,
                     109.9303428, 116.3778632, 122.8253837, 128.700195, 134.4731036, 139.5303232, 143.9078752,
                     148.3655275, 153.1099926, 158.0974759, 163.5033766, 167.8407995, 172.7340267, 177.4888559,
                     182.2597998, 187.3592024, 191.9310806, 199.3164222, 207.3928066, 211.4494835, 216.5488861,
                     220.5932398, 227.2752156, 230.792045, 234.6605572, 238.5290695, 244.5323257, 250.9626254,
                     258.5749969, 265.6086556, 272.5250866, 277.5658754, 281.7860706, 286.0062658, 290.2264611,
                     295.9706157]
                y = [67.69, 62.79229542, 58.24070666, 53.6891179, 51.86848239, 50.04784689, 50, 50.04784689,
                     50.04784689, 50.76923077, 51.26160389, 53.84615385, 54.9028749, 57.33038891, 60, 63.70261318,
                     71.89547295, 79.17801497, 88.46153846, 95.56373451, 101.9359588, 106.4875475, 111.3425756,
                     115.5907251, 118.3216783, 119.2319961, 120.1423138, 120.1423138, 121.5384615, 123.0769231,
                     128.0529996, 130.1558091, 133.7970801, 137.4383511, 139.2307692, 140.7692308, 142.9002576,
                     143.8105754, 145.6312109, 148.3621642, 151.0931174, 152.0034352, 152.9137529, 153.8240707,
                     154.7343884, 155.6447062, 155.6447062, 155.6447062, 156.6961109, 156.9782849, 157.4653417,
                     157.4653417, 158.6790987, 158.3756594, 158.3756594, 158.3756594, 158.3756594, 159.2859772]
                Rspec = 3614.91
                gamma = 1.3846
            if new_vehicle.destination == "Titan":
                x = [0, 3.253185645, 11.96136701, 20.83733242, 30.68350669, 38.41010401, 44.35364042, 50.29717682,
                     55.64635958, 61.98423588, 68.72213967, 73.94145569, 81.67848027, 89.06903555, 96.44916357,
                     104.6849586, 113.4090968, 123.1419932, 135.884101, 145.9881129, 156.2352626, 163.2689213,
                     172.7340267, 182.6466511, 187.8867268, 194.7251114, 201.8573551, 207.8008915, 214.9331352,
                     224.4427935, 234.5468053, 243.3189722, 249.6369419, 256.5739115, 261.3884603, 267.931564,
                     274.049046, 282.9994241, 291.9848757]
                y = [90, 87.37087474, 80, 73.71610845, 70, 69.23076923, 69.23076923, 70.76923077, 71.53846154,
                     80.08833272, 98.46153846, 113.7700896, 124.6939026, 134.0792541, 139.2589866, 143.1824316,
                     147.1696724, 150.6698565, 155.3846154, 160, 161.1066127, 162.9272482, 164.6153846, 166.5685192,
                     166.5685192, 169.2307692, 170, 170.7692308, 171.5384615, 172.3076923, 173.8461538, 174.902466,
                     175.6716967, 175.6716967, 175.6716967, 175.6716967, 177.4923322, 177.4923322, 177.4923322]
                Rspec = 290
                gamma = 1.3846
            with warnings.catch_warnings():
                warnings.simplefilter('ignore', np.RankWarning)
                coeff = numpy.polyfit(x, y, 21)
                p = np.poly1d(coeff)
            # https://pds-atmospheres.nmsu.edu/education_and_outreach/encyclopedia/gas_constant.htm

            temp = p(altitude)
            a = math.sqrt(gamma * Rspec * temp)


            import isacalc as isa
            from airfoils import Airfoil
            crossrange = 100

            # Should be able to change geometry dynamically
            winged = 1
            if winged == 1:
                sweepangle = 45
                # Must be controlable for subsonic and supersonic regimes

                airfoil = "2412"

                rootchord = 4  # meters
                tipchord = 1  # meters

            def bluntedconedrag(Halfangle, trailingrad, conerad):
                C_d = (1 - (math.sin(math.radians(Halfangle))) ** 4) * ((trailingrad / conerad) ** 2) + (
                            2 * (math.sin(math.radians(Halfangle)) ** 2)) * (1 - (trailingrad / conerad) ** 2) * (
                                  math.cos(math.radians(Halfangle)) ** 2)
                return C_d

            def amax(Vre, gamma, Rho_0, BC, Beta=0.000139):

                accelmax = (Vre ** 2) * Beta * math.sin(math.radians(gamma)) / 2 * math.e
                altmax = (1 / Beta) * math.log(Rho_0 / (BC * Beta * math.sin(math.radians(gamma))))
                return accelmax, altmax

            def heatingrate(Rho, vel, noseradius):
                # FAA   Returning from Space:  Re-entry  (4.1.7-8)
                q_dot = 1.83 * (10 ** -4) * (vel ** 3) * math.sqrt(Rho / noseradius)
                return q_dot

            print(amax(5000, 45, 1, 1))
            print(bluntedconedrag(15, 0.304, 1))

        elif event == "-FUSELAGE-":


            import FreeCAD as App
            import Draft
            import numpy as np
            import math
            import FreeCADGui as Gui
            doc = App.newDocument()
            fuselagetuple = []
            X_scaling = 1
            Y_scaling = 5
            Z_scaling = 5

            fuselagepoints = np.array([])
            for j in range(0,50):
                x = j*X_scaling
                points = []
                for i in range(0, 13):
                    angle = i*30
                    z = Z_scaling*math.cos(math.radians(angle))
                    y = Y_scaling*math.sin(math.radians(angle))
                    fuselagepoints = np.append(fuselagepoints, [x,y,z])
                    points.append(App.Vector(x,y,z))

                fuselagetuple.append((Draft.make_bspline(points),"Edge1"))

            fuselagepoints = fuselagepoints.reshape(j+1,i+1,3)

            print(fuselagepoints[8])
            doc.recompute()

            surf = doc.addObject("Surface::Sections", "Surface")
            surf.NSections = fuselagetuple
            doc.recompute()
            Gui.SendMsgToActiveView("ViewFit")
            layout1 = [
                [sg.Text('Add fuselage station at X= '), sg.InputText('', size=(5,1)), sg.Button('+', key="-PLUS-")],
                [sg.Text('Delete fuselage station at X= '), sg.InputText('', size=(5,1)), sg.Button('-', key="-MINUS-")],
                [sg.Text('Edit fuselage station number'), sg.InputText(''), sg.Button('OK', key="-STATION-")],
                [sg.Submit("Submit")]]

            window = sg.Window('Fuselage Designer', layout1, default_element_size=(30, 50), grab_anywhere=False)
            while True:
                event, values = window.read()
                print(values)
                if event == "Submit":
                    window.close()
                    break
                elif event == "-PLUS-":
                    xval = values[0]
                    print("Plus")
                elif event == "-MINUS-":
                    yval = values[1]
                    print("Minus")
                elif event == "-STATION-":
                    stationnum = values[2]
                    print(stationnum)
                    if len(stationnum) == 1:
                        textinp = 'BSpline00' + str(stationnum)
                    elif len(stationnum) == 2:
                        textinp = 'BSpline0' + str(stationnum)
                    elif len(stationnum) == 3:
                        textinp = 'BSpline' + str(stationnum)
                    print(tuple(map(tuple, fuselagepoints[int(stationnum)])))
                    FreeCAD.getDocument(App.ActiveDocument.Name).getObject(textinp).Points = [tuple(map(tuple, fuselagepoints[int(stationnum)]))]



                        # (40.00, 0.00, 5.00),
                        #                                                              (40.00, 5.50, 4.33),
                        #                                                              (40.00, 4.33, 2.50),
                        #                                                              (40.00, 5.00, 0.00),
                        #                                                              (40.00, 4.33, -2.50),
                        #                                                              (40.00, 2.50, -4.33),
                        #                                                              (40.00, 0.00, -5.00),
                        #                                                              (40.00, -2.50, -4.33),
                        #                                                              (40.00, -4.33, -2.50),
                        #                                                              (40.00, -5.00, -0.00),
                        #                                                              (40.00, -4.33, 2.50),
                        #                                                              (40.00, -2.50, 4.33),
                        #                                                              (40.00, -0.00, 5.00), ]

                    App.getDocument('Unnamed1').getObject('Surface').ViewObject.doubleClicked()
                    Gui.ActiveDocument.resetEdit()
                    App.ActiveDocument.recompute()

        elif event == "-SURF-" and values[0] == "Wing":
            import csv
            airfoil_list = os.listdir(SCDesignerPath + "\\AERO\\Airfoil_database")
            layout1 = [
                [sg.Text('Select Airfoil'),sg.InputCombo(airfoil_list)],
                [sg.Text('Semi Span (meters)'), sg.InputText('')],
                [sg.Submit("Submit")]]

            window1 = sg.Window('Wing Designer', layout1, default_element_size=(40, 1), grab_anywhere=False)

            event1, values1 = window1.read()
            airfoil = values1[0]
            semispan = values1[1]
            print(values1)
            window1.close()

            header = 1
            with open(
                    SCDesignerPath+ "\\AERO\\Airfoil_database\\" + airfoil) as file_in:
                lines = [[]]
                for line in file_in:
                    if header == 1:
                        header = 0
                        continue
                    line = line.replace("\n", "")
                    line = line.replace("     ", "")
                    if line.find("   -") > -1:
                        data = line.split("   ")
                    else:
                        data = line.split("    ")
                    line = [float(i) for i in data]
                    lines.append(line)
                lines = lines[1:]

            import Part
            import PartDesign
            import PartDesignGui
            import Sketcher
            import FreeCAD as App
            import FreeCADGui as Gui
            App.newDocument(FreeCAD.ActiveDocument.Name)
            App.setActiveDocument(FreeCAD.ActiveDocument.Name)
            App.ActiveDocument=App.getDocument(FreeCAD.ActiveDocument.Name)
            Gui.ActiveDocument=Gui.getDocument(FreeCAD.ActiveDocument.Name)
            Gui.activateWorkbench("PartDesignWorkbench")
            App.activeDocument().addObject('PartDesign::Body','Body')
            import PartDesignGui
            Gui.activeView().setActiveObject('pdbody', App.activeDocument().Body)
            Gui.Selection.clearSelection()
            Gui.Selection.addSelection(App.ActiveDocument.Body)
            App.ActiveDocument.recompute()
            App.activeDocument().Body.newObject('Sketcher::SketchObject','Sketch')
            App.activeDocument().Sketch.Support = (App.activeDocument().XY_Plane, [''])
            App.activeDocument().Sketch.MapMode = 'FlatFace'
            App.ActiveDocument.recompute()
            Gui.activeDocument().setEdit('Sketch')
            Gui.activateWorkbench('SketcherWorkbench')
            import PartDesignGui
            chord = 5*1000
            for i in range(0, len(lines) - 1):
                App.ActiveDocument.Sketch.addGeometry(Part.LineSegment(App.Vector(chord*lines[i][0],chord*lines[i][1]),App.Vector(chord*lines[i + 1][0],chord*lines[i + 1][1])),False)
            App.ActiveDocument.Sketch.addGeometry(
                Part.LineSegment(App.Vector(chord*lines[0][0], chord*lines[0][1]), App.Vector(chord*lines[-1][0], chord*lines[-1][1])),
                False)
            Gui.getDocument(FreeCAD.ActiveDocument.Name).resetEdit()
            App.ActiveDocument.recompute()
            Gui.SendMsgToActiveView("ViewFit")



            App.getDocument(FreeCAD.ActiveDocument.Name).getObject('Body').newObject('PartDesign::Plane', 'DatumPlane')
            App.getDocument(FreeCAD.ActiveDocument.Name).getObject('DatumPlane').Support = [
                (App.getDocument(FreeCAD.ActiveDocument.Name).getObject('Sketch'), '')]
            App.getDocument(FreeCAD.ActiveDocument.Name).getObject('DatumPlane').MapMode = 'ObjectXY'
            App.activeDocument().recompute()
            Gui.getDocument(FreeCAD.ActiveDocument.Name).setEdit(App.getDocument(FreeCAD.ActiveDocument.Name).getObject('Body'), 0, 'DatumPlane.')


            App.getDocument(FreeCAD.ActiveDocument.Name).getObject('DatumPlane').AttachmentOffset = App.Placement(
                App.Vector(0.0000000000, 0.0000000000, float(semispan)*1000),
                App.Rotation(0.0000000000, 0.0000000000, 0.0000000000))
            App.getDocument(FreeCAD.ActiveDocument.Name).getObject('DatumPlane').MapReversed = False
            App.getDocument(FreeCAD.ActiveDocument.Name).getObject('DatumPlane').Support = [
                (App.getDocument(FreeCAD.ActiveDocument.Name).getObject('Sketch'), '')]
            App.getDocument(FreeCAD.ActiveDocument.Name).getObject('DatumPlane').MapPathParameter = 0.000000
            App.getDocument(FreeCAD.ActiveDocument.Name).getObject('DatumPlane').MapMode = 'ObjectXY'
            App.getDocument(FreeCAD.ActiveDocument.Name).getObject('DatumPlane').recompute()
            Gui.getDocument(FreeCAD.ActiveDocument.Name).resetEdit()

            App.getDocument(FreeCAD.ActiveDocument.Name).getObject('Body').newObject('Sketcher::SketchObject', 'Sketch001')
            App.getDocument(FreeCAD.ActiveDocument.Name).getObject('Sketch001').Support = (
            App.getDocument(FreeCAD.ActiveDocument.Name).getObject('DatumPlane'), '')
            App.getDocument(FreeCAD.ActiveDocument.Name).getObject('Sketch001').MapMode = 'FlatFace'
            App.ActiveDocument.recompute()
            Gui.getDocument(FreeCAD.ActiveDocument.Name).setEdit(App.getDocument(FreeCAD.ActiveDocument.Name).getObject('Body'), 0, 'Sketch001.')
            ActiveSketch = App.getDocument(FreeCAD.ActiveDocument.Name).getObject('Sketch001')

            del (ActiveSketch)

            import PartDesignGui
            ActiveSketch = App.getDocument(FreeCAD.ActiveDocument.Name).getObject('Sketch001')
            if ActiveSketch.ViewObject.RestoreCamera:
                ActiveSketch.ViewObject.TempoVis.saveCamera()

             ### End command PartDesign_NewSketch
             # Gui.Selection.clearSelection()
             # Gui.Selection.addSelection(FreeCAD.ActiveDocument.Name,'Body','DatumPlane.')
            Gui.runCommand('Std_ToggleVisibility', 0)
            Gui.runCommand('Sketcher_CarbonCopy', 0)
             # Gui.Selection.clearSelection()
             # Gui.Selection.addSelection(FreeCAD.ActiveDocument.Name,'Body','Sketch.')
            App.getDocument(FreeCAD.ActiveDocument.Name).getObject('Sketch001').carbonCopy("Sketch", False)
             # Gui.Selection.clearSelection()
            Gui.getDocument(FreeCAD.ActiveDocument.Name).resetEdit()
            App.ActiveDocument.recompute()





            App.getDocument(FreeCAD.ActiveDocument.Name).getObject('Body').newObject('PartDesign::AdditiveLoft', 'AdditiveLoft')
            App.getDocument(FreeCAD.ActiveDocument.Name).getObject('AdditiveLoft').Profile = App.getDocument(FreeCAD.ActiveDocument.Name).getObject(
                'Sketch')
            Gui.Selection.addSelection(FreeCAD.ActiveDocument.Name, 'Body', 'Sketch001.Edge28', 2160.22, -135.908, 6000)
            App.ActiveDocument.recompute()
            App.getDocument(FreeCAD.ActiveDocument.Name).getObject('Sketch').Visibility = False
            App.ActiveDocument.recompute()
            App.getDocument(FreeCAD.ActiveDocument.Name).getObject('AdditiveLoft').ViewObject.ShapeColor = getattr(
                App.getDocument(FreeCAD.ActiveDocument.Name).getObject('Body').getLinkedObject(True).ViewObject, 'ShapeColor',
                App.getDocument(FreeCAD.ActiveDocument.Name).getObject('AdditiveLoft').ViewObject.ShapeColor)
            App.getDocument(FreeCAD.ActiveDocument.Name).getObject('AdditiveLoft').ViewObject.LineColor = getattr(
                App.getDocument(FreeCAD.ActiveDocument.Name).getObject('Body').getLinkedObject(True).ViewObject, 'LineColor',
                App.getDocument(FreeCAD.ActiveDocument.Name).getObject('AdditiveLoft').ViewObject.LineColor)
            App.getDocument(FreeCAD.ActiveDocument.Name).getObject('AdditiveLoft').ViewObject.PointColor = getattr(
                App.getDocument(FreeCAD.ActiveDocument.Name).getObject('Body').getLinkedObject(True).ViewObject, 'PointColor',
                App.getDocument(FreeCAD.ActiveDocument.Name).getObject('AdditiveLoft').ViewObject.PointColor)
            App.getDocument(FreeCAD.ActiveDocument.Name).getObject('AdditiveLoft').ViewObject.Transparency = getattr(
                App.getDocument(FreeCAD.ActiveDocument.Name).getObject('Body').getLinkedObject(True).ViewObject, 'Transparency',
                App.getDocument(FreeCAD.ActiveDocument.Name).getObject('AdditiveLoft').ViewObject.Transparency)
            App.getDocument(FreeCAD.ActiveDocument.Name).getObject('AdditiveLoft').ViewObject.DisplayMode = getattr(
                App.getDocument(FreeCAD.ActiveDocument.Name).getObject('Body').getLinkedObject(True).ViewObject, 'DisplayMode',
                App.getDocument(FreeCAD.ActiveDocument.Name).getObject('AdditiveLoft').ViewObject.DisplayMode)
            Gui.getDocument(FreeCAD.ActiveDocument.Name).setEdit(App.getDocument(FreeCAD.ActiveDocument.Name).getObject('Body'), 0, 'AdditiveLoft.')
            App.getDocument(FreeCAD.ActiveDocument.Name).getObject('AdditiveLoft').Profile = App.getDocument(
                FreeCAD.ActiveDocument.Name).getObject('Sketch001')
            # Gui.Selection.clearSelection()
             ### End command PartDesign_AdditiveLoft
             # Gui.Selection.clearSelection()
            # Gui.Selection.addSelection(FreeCAD.ActiveDocument.Name,'Body','Sketch001.Edge28',2160.22,-135.908,6000)
             # Gui.Selection.clearSelection()
            # App.getDocument(FreeCAD.ActiveDocument.Name).getObject('Sketch001').Visibility = False
            # App.getDocument(FreeCAD.ActiveDocument.Name).getObject('Sketch').Visibility = False
            # App.getDocument(FreeCAD.ActiveDocument.Name).recompute()
            # Gui.getDocument(FreeCAD.ActiveDocument.Name).resetEdit()

        elif event == "-ENTRY-":

            import airfoils
            '''
            Aero flow

            Determine target body atmospheric conditions, pressure temp, density as function of altitude
            Determine Orbital velocity at entry interface
            Determine cross range requirements
            Determine winged or capsule
            Determine vehicle mass
            Determine static stability
            Determine re-entry angle of attack range
            Determine drag coefficient range
            Determine ballistic coefficient range
            Determine maximum stagnation temperature 
            Determine heating rate
            Determine total heat that must be absorped
            Determine ablative or reusable tiles
            Determine TPS material



            '''
            import isacalc as isa
            crossrange = 100

            # Should be able to change geometry dynamically
            winged = 1
            if winged == 1:
                sweepangle = 45
                # Must be controlable for subsonic and supersonic regimes

                airfoil = "2412"

                rootchord = 4  # meters
                tipchord = 1  # meters

            def bluntedconedrag(Halfangle, trailingrad, conerad):
                C_d = (1 - (math.sin(math.radians(Halfangle))) ** 4) * ((trailingrad / conerad) ** 2) + (
                            2 * (math.sin(math.radians(Halfangle)) ** 2)) * (1 - (trailingrad / conerad) ** 2) * (
                                  math.cos(math.radians(Halfangle)) ** 2)
                return C_d

            def amax(Vre, gamma, Rho_0, BC, Beta=0.000139):

                accelmax = (Vre ** 2) * Beta * math.sin(math.radians(gamma)) / 2 * math.e
                altmax = (1 / Beta) * math.log(Rho_0 / (BC * Beta * math.sin(math.radians(gamma))))
                return accelmax, altmax

            def heatingrate(Rho, vel, noseradius):
                # FAA   Returning from Space:  Re-entry  (4.1.7-8)
                q_dot = 1.83 * (10 ** -4) * (vel ** 3) * math.sqrt(Rho / noseradius)
                return q_dot

            print(amax(5000, 45, 1, 1))
            print(bluntedconedrag(15, 0.304, 1))













            # Dave Akins slide 6 of Launch Entry Vehicle Design

            # Reference density (at sea level I think)
            rho_0 = 1.19

            # Reentry Altitude
            reentryalt = 500

            # Gravitational parameter of the Earth
            Mu = 398600

            # Reentry radius
            r_0 = 6378 + reentryalt

            # For circular case only
            reentryvelocity = math.sqrt(Mu / r_0)  # km/s

            print(reentryvelocity)

            # Spacecraft mass
            mass = 2000  # kg

            # Spacecraft coefficient of drag
            C_d = 2

            # Spacecraft area
            Area = 100  # Square meters

            # Lift to drag ratio
            LDratio = 1

            # Ballistic coefficient
            beta = mass / (C_d * Area)

            # Entry flight path angle
            gamma_e = 0

            # velocity =
            # rho_inf = rho_0*math.e**(-altitude/reentryalt)
            # Lift = 0.5*rho_inf*(velocity**2)*C_l*Area
            # Drag = 0.5*rho_inf*(velocity**2)*C_d*Area
            # flightpathangle =
            #
            # altitude =
            #
            # dvdt = ((velocity**2)*math.sin(math.radians(flightpathangle))/(altitude+ 6378))-(gravity*math.sin(math.radians(flightpathangle)))-(Drag/mass)
            # dfpadt = (Lift/(mass*velocity))+((velocity/(altitude+6378))*math.cos(math.radians(flightpathangle)))-((gravity/velocity)*math.cos(math.radians(flightpathangle)))

            # COMMIT TO USING ALTITUDE FUNCTION OR ISA
            # velocity ratio compared to entry ~ circular velocity
            # Assuming that the start height is h_s
            for altitude in range(reentryalt, 0, -1):
                # Calculates the current velocity vs entry velocity. Refer to slide 9
                vdivve = 1 / (math.sqrt(
                    1 + (((1 / (2 * beta)) * (rho_0 * r_0 * (LDratio) * (math.exp(-(altitude / reentryalt))))))))
                velocity = vdivve * reentryvelocity

                # Deceleration in gs, slide 15
                numgs = -1 / (((2 * beta / (rho_0 * r_0)) * math.exp(altitude / reentryalt)) + LDratio)
                print(numgs)

            # Limiting deceleration, slide 17
            nlimit = -1 / LDratio

            # Time for entry, slide 19
            # deltat = 0.5*math.sqrt(r_0/gravity)*LDratio*(math.log((1+((velocity/reentryvelocity)**2))/(1-((velocity/reentryvelocity)**2))))

            # Distance along flight path, Slide 22
            # deltas = 0.5*r_0*LDratio*math.log((1-((velocity/reentryvelocity)**2)))

            # Pretty sure wrong code for bank angle
            PsiOpt = 1 / math.atan(math.sqrt(1 + (0.106 * (LDratio ** 2))))  # Optimal bank angle
            Ymax = (r_0 / 5.2) * (LDratio ** 2) * (1 / (math.sqrt(1 + (0.106 * (LDratio ** 2)))))  # Maximum crossrange
            print(PsiOpt)
            print(Ymax)

            # The next 4 equations are o slide 43
            # Height at which maximum deceleration occurs
            h_maxgs = h_s * math.log((-rho_0 * h_s / (2 * beta * math.sin(math.radians(gamma_e)))) * (math.sqrt(
                4 + ((LDratio ** 2) * (1 / (math.sin(math.radians(gamma_e))) ** 2)) - (
                            LDratio * (1 / math.tan(math.radians(gamma_e)))))))

            # Flight path angle where maximum deceleration occurs
            gamma_m = math.acos((math.cos(math.radians(gamma_e))) - ((LDratio * math.sin(math.radians(gamma_e))) / (
                        (math.sqrt(4 + ((LDratio ** 2) * (1 / (math.sin(math.radians(gamma_e)) ** 2))))) - (
                            LDratio * (1 / math.tan(math.radians(gamma_e)))))))

            # Velocity where maximum deceleration occurs
            v_m = reentryvelocity * math.exp((gamma_e - gamma_m) / LDratio)

            # Maximum gs
            n_max = (rho_0 * (reentryvelocity ** 2) / (2 * beta)) * math.sqrt(1 + ((LDratio ** 2) * v_m ** 2))

            '''
            # Heating Analysis

            def Heating(Velocity, Altitude, gamma):    # Meters/sec, meters
                import isacalc
                import isacalc as isa
                atmosphere = isa.get_atmosphere()
                Tinf, Pinf, d, a, mu = isa.calculate_at_h(Altitude, atmosphere)
                MachNum = Velocity/a
                # From slide # 3 from Entry Aerothermodynamics Dave Akins
                Twall = Tinf + (Tinf*((gamma-1)/2)*(MachNum**2))
                return Twall

            print(Heating(1000, 100000, 1.4))

            # https://www.slideserve.com/salena/reynolds-analogy
            # For 0.6 < Pr < 60
            Pr = 0.71  # Prandtl number for air

            # Reynolds number a location x behind the shock for a flat plate
            Re = Rho_behindshock*v_behindshock*x/Mu

            # Skin Friction Coefficient
            C_f = 0.664/math.sqrt(Re)

            # Stanton number
            StantonNum = C_f/(2*(Pr**(2/3)))

            # Chapman Equation (Earth)

            # Sutton Graves Equation
            if targetbody == "Earth":
                k = 0.00017415  # Earth
                m = 0.5
                n = 3
            if targetbody == "Mars":
                k = 0.00019027 # Mars
                m = 0.5
                n = 3.04

            # Chapman Method Pg 19
            HWC = 1 - (h_w / h_inf)
            q_c0 = (C / (math.sqrt(Re))) * (Rho_inf ** m) * (Velocity ** n) * HWC

            # Sutton Graves
            q_s = k*math.sqrt(Rho/Re)*(Velocity**3)

            # Mass diffusivity
            D =

            # Schmidt and Lewis number for Fay and Riddell approach
            Sc = Mu/(Rho*D)

            # https://www.tec-science.com/mechanics/gases-and-liquids/lewis-number/
            Le = Sc/Pr

            # Fay & Riddell slide 16
            dudx = (1/R)*math.sqrt((2*(p_e-p_inf)/rho_e))
            qdot_w = 0.763*((rho_e*Mu_e)**0.4)*((rho_wall*Mu_wall)**0.1)*(hoe-hw)*(1+((Le**0.52)-1)*(h_d/hoe))*(dudx**0.5)/(Pr_w**0.6)

            # PUT IN COMPRESSIBLE AERO CALCS HERE
            # Function of pressure vs x value from compressible aero calcs
            dPdSBBdivdPdSHemi =




            dUdsBBdivdUdSHemi = f*dPdSBBdivdPdSHemi
            r_BdivR_eff = dUdsBBdivdUdSHemi

            #Find effecive radius around rounded corner, can use Zoby and Sullivan tables, Rc/Rb



            '''




        return


        
class Comms():
    """My new command"""

    def GetResources(self):
        return {'Pixmap'  : 'C:\\Users\\' + username + '\\AppData\\Roaming\\FreeCAD\\Mod\\SpacecraftDesigner\\Icons\\Comm.jpg',
                'Accel' : "Shift+C", # a default shortcut (optional)
                'MenuText': "Comms",
                'ToolTip' : "Define Spacecraft Communications System"}

    def Activated(self):
        c = 299792458 # speed of light, meters/second

        layout = [[sg.Text('Add Antenna by Geometry'), sg.InputCombo(('Isotropic', 'Parabolic', 'Cassegrain', 'Helix', 'Broadside Array', 'Waveguide', 'Horn', 'Multiple Beam Phased Array', 'Hopping Beam Phased Array', 'Microstrip/Patch', 'Monopole', 'Dipole'), size=(30, 1)), sg.Button('OK',key="-GEOMETRY-")],
        [sg.Text('Add Antenna by Frequency'), sg.InputCombo(('L-Band', 'S-Band', 'C-Band','X-Band', 'Ku-Band', 'K-Band','Ka-Band', 'V-Band', 'W-Band'), size=(30, 1)), sg.Button('OK')],
        [sg.Text('Add Antenna by Existing Infrastructure'), sg.InputCombo(('Space Network (SN)', 'Deep Space Network (DSN)', 'Satellite Control Network', 'Tracking and Data Relay Satellite System (TDRSS)', 'Near Earth Network', 'European Data Relay System (EDRS)'), size=(30, 1)), sg.Button('OK', key="-EXISTS-")],
        [sg.Text('Add Antenna'), sg.InputCombo(('hybrid coupler', 'Wilkinson divider', 'Waveguide', 'Circulator', 'Directional Coupler'), size=(30, 1)), sg.Button('OK')],
        [sg.Text('Comm System Data Rate')],
        [sg.Submit(tooltip='Click to submit this window'), sg.Cancel()]]

        # https://www.intechopen.com/books/advanced-radio-frequency-antennas-for-modern-communication-and-medical-systems
        # https://descanso.jpl.nasa.gov/monograph/series8/Descanso8_00_thru_acronyms.pdf
        # antenna-theory.com/antennas/patches/antenna.php#introduction

        window = sg.Window('Communications', layout, default_element_size=(40, 1), grab_anywhere=False)      

        event, values = window.read()

        # https://pysdr.org/content/link_budgets.html

        def ReceiverPower21_3(Ptrans, Gtrans, Greceive, d, lambda1):
            Pr = Ptrans * Gtrans * Greceive / ((4 * math.pi / lambda1) ** 2)
            # Radar range equation EP394 slide 43
            return Pr

        def ReceiverPower21_2(Ptrans, Atrans, Areceive, d, lambda1):
            Pr = Ptrans * Atrans * Areceive / ((d ** 2) * (lambda1 ** 2))
            return Pr

        def ReceiverPower21_1(Ptrans, Gtrans, Areceive, d):
            # Slide 41
            Pr = Ptrans * Gtrans * Areceive / (4 * math.pi * (d ** 2))
            return Pr

        def SNR21_4(Ptrans, Gtrans, Greceive, d, lambda1, k, Ts, B):
            SNR = Ptrans * Gtrans * Greceive / (((4 * math.pi / lambda1) ** 2) * k * Ts * B)
            return SNR

        def BitEnergyToNoiseRatio21_5(Ptrans, Gtrans, Greceive, d, lambda1, k, Ts, R, Beta):
            BEtoNR = (Ptrans * Gtrans * Greceive * (math.sin(math.radians(Beta)) ** 2)) / (
                        ((4 * math.pi * d / lambda1) ** 2) * k * Ts * R)
            return BEtoNR

        def P_Noise(T, B):
            # https://pysdr.org/content/link_budgets.html
            k = 1.38e-23
            return k * T * B

        def Comm_link(Pt, Gt, Lpt, Ls, Lpol, Latm, Lpr, Gr, Tsys, R):
            # Slide 49
            Eb_No = Pt + Gt + Lpt + Lpol + Latm + Lpr + Gr - 10 * math.log(k * Tsys, 10) - 10 * math.log(R, 10)
            return Eb_No

        def Gain(eta, d, lambda1):
            # Slide 42
            return eta * ((math.pi * d / lambda1) ** 2)

        def Pointing_loss(Theta_e, Theta3db):
            # Theta e is off axis pointing
            return -12 * ((Theta_e / Theta3db) ** 2)

        def SkyNoise(Frequency, Elevation):
            # Slide 34
            pass

        def RainAttenuation(Frequency, Elevation):
            # Slide 35
            pass

        window.close()
        if event == "Cancel":
            window.close()
        elif event == "Submit":
            window.close()
            print(values)
        elif event == "-EXISTS-":
            groundstation = values[2]
            if groundstation == "Deep Space Network (DSN)":
                uplink_frequency_bands = 2025000000 #["2025000000 - 2120000000", "7145000000 - 7190000000"]
                uplink_max_rate = 2000 # bps
                downlink_frequency_bands = 2300000000 #["2200000000 - 2300000000"]
                downlink_max_rate = 6600000

            PtransGS = 0
            GtransGS = 0
            GreceiveGS = 0

            PtransSC = 0
            GtransSC = 0
            GreceiveSC = 0

            k = 1.380649e-23
            Bup = 10
            Bdown = 10
            GL = 10
            # Refer to slide 33, this is not done
            Ta = 1
            TL = 1
            T1 = 1
            Ts = Ta + (TL*((1/GL)-1)) + (T1/GL)
            uplink_lambda = c/uplink_frequency_bands
            downlink_lambda = c/downlink_frequency_bands
            Uplink_SNR = PtransGS * GtransGS * GreceiveSC / (((4 * math.pi / uplink_lambda) ** 2) * k * Ts * Bup)
            Downlink_SNR = PtransSC * GtransSC * GreceiveGS / (((4 * math.pi / downlink_lambda) ** 2) * k * Ts * Bdown)
            layout5 = [[sg.Frame(layout=[[sg.Text('Uplink Frequency'), sg.Text(uplink_frequency_bands)],
                       [sg.Text('Uplink Data Rate'), sg.Text(uplink_max_rate)],
                       [sg.Text('Ground Station Transmitter Power'), sg.Text('Power')],
                       [sg.Text('Spacecraft Receiver Power'), sg.Text('Power')],
                       [sg.Text('Uplink Signal to Noise Ratio'), sg.Text(Uplink_SNR)]], title='Uplink')],


                       [sg.Frame(layout=[[sg.Text('Downlink Frequency'), sg.Text(downlink_frequency_bands)],
                                         [sg.Text('Downlink Data Rate'), sg.Text(downlink_max_rate)],
                                         [sg.Text('Ground Station Receiver Power'), sg.Text('Power')],
                                         [sg.Text('Spacecraft Transmitter Power'), sg.Text('Power')],
                                         [sg.Text('Downlink Signal to Noise Ratio'), sg.Text(Downlink_SNR)]], title='Downlink')]]

            window5 = sg.Window('Link Budget Tool', layout5, default_element_size=(40, 1), grab_anywhere=False)

            event5, values5 = window5.read()


            # uplink_frequency =




        elif event == "-GEOMETRY-":
            if values[0] == "Microstrip/Patch":
                """ Functions dealing with rectangular patch antenna."""
                # from sph2cart1 import sph2cart1
                # from cart2sph1 import cart2sph1
                from math import cos, sin, sqrt
                from mpl_toolkits.mplot3d import Axes3D

                def sph2cart1(r, theta, phi):
                    return [
                        r * math.sin(theta) * math.cos(phi),
                        r * math.sin(theta) * math.sin(phi),
                        r * math.cos(theta)]

                def cart2sph1(x, y, z):
                    rng = math.sqrt((x ** 2) + (y ** 2) + (z ** 2))
                    lon = math.atan2(y, x)
                    lat = math.atan2((math.sqrt((x ** 2) + (y ** 2))), z)
                    return [rng, lat, lon]

                def PatchFunction(thetaInDeg, phiInDeg, Freq, W, L, h, Er):
                    """
                    Taken from Design_patchr
                    Calculates total E-field pattern for patch as a function of theta and phi
                    Patch is assumed to be resonating in the (TMx 010) mode.
                    E-field is parallel to x-axis
                    W......Width of patch (m)
                    L......Length of patch (m)
                    h......Substrate thickness (m)
                    Er.....Dielectric constant of substrate
                    Refrence C.A. Balanis 2nd Edition Page 745
                    """
                    lamba = 3e8 / Freq

                    theta_in = math.radians(thetaInDeg)
                    phi_in = math.radians(phiInDeg)

                    ko = 2 * math.pi / lamba

                    xff, yff, zff = sph2cart1(999, theta_in,
                                              phi_in)  # Rotate coords 90 deg about x-axis to match array_utils coord system with coord system used in the model.
                    xffd = zff
                    yffd = xff
                    zffd = yff
                    r, thp, php = cart2sph1(xffd, yffd, zffd)
                    phi = php
                    theta = thp

                    if theta == 0:
                        theta = 1e-9  # Trap potential division by zero warning

                    if phi == 0:
                        phi = 1e-9

                    Ereff = ((Er + 1) / 2) + ((Er - 1) / 2) * (1 + 12 * (
                                h / W)) ** -0.5  # Calculate effictive dielectric constant for microstrip line of width W on dielectric material of constant Er

                    F1 = (Ereff + 0.3) * (
                                W / h + 0.264)  # Calculate increase length dL of patch length L due to fringing fields at each end, giving total effective length Leff = L + 2*dL
                    F2 = (Ereff - 0.258) * (W / h + 0.8)
                    dL = h * 0.412 * (F1 / F2)

                    Leff = L + 2 * dL

                    Weff = W  # Calculate effective width Weff for patch, uses standard Er value.
                    heff = h * sqrt(Er)

                    # Patch pattern function of theta and phi, note the theta and phi for the function are defined differently to theta_in and phi_in

                    Numtr2 = sin(ko * heff * cos(phi) / 2)
                    Demtr2 = (ko * heff * cos(phi)) / 2
                    Fphi = (Numtr2 / Demtr2) * cos((ko * Leff / 2) * sin(phi))

                    Numtr1 = sin((ko * heff / 2) * sin(theta))
                    Demtr1 = ((ko * heff / 2) * sin(theta))
                    Numtr1a = sin((ko * Weff / 2) * cos(theta))
                    Demtr1a = ((ko * Weff / 2) * cos(theta))
                    Ftheta = ((Numtr1 * Numtr1a) / (Demtr1 * Demtr1a)) * sin(theta)

                    # Due to groundplane, function is only valid for theta values :   0 < theta < 90   for all phi
                    # Modify pattern for theta values close to 90 to give smooth roll-off, standard model truncates H-plane at theta=90.
                    # PatEdgeSF has value=1 except at theta close to 90 where it drops (proportional to 1/x^2) to 0

                    rolloff_factor = 0.5  # 1=sharp, 0=softer
                    theta_in_deg = theta_in * 180 / math.pi  # theta_in in Deg
                    F1 = 1 / (((rolloff_factor * (abs(theta_in_deg) - 90)) ** 2) + 0.001)  # intermediate calc
                    PatEdgeSF = 1 / (F1 + 1)  # Pattern scaling factor

                    UNF = 1.0006  # Unity normalisation factor for element pattern

                    if theta_in <= math.pi / 2:
                        Etot = Ftheta * Fphi * PatEdgeSF * UNF  # Total pattern by pattern multiplication
                    else:
                        Etot = 0

                    return Etot

                def GetPatchFields(PhiStart, PhiStop, ThetaStart, ThetaStop, Freq, W, L, h, Er):
                    """"
                    Calculates the E-field for range of thetaStart-thetaStop and phiStart-phiStop
                    Returning a numpy array of form - fields[phiDeg][thetaDeg] = eField
                    W......Width of patch (m)
                    L......Length of patch (m)
                    h......Substrate thickness (m)
                    Er.....Dielectric constant of substrate
                    """
                    fields = np.ones((PhiStop, ThetaStop))  # Create initial array to hold e-fields for each position

                    for phiDeg in range(PhiStart, PhiStop):
                        for thetaDeg in range(ThetaStart, ThetaStop):  # Iterate over all Phi/Theta combinations
                            eField = PatchFunction(thetaDeg, phiDeg, Freq, W, L, h,
                                                   Er)  # Calculate the field for current Phi, Theta
                            fields[phiDeg][thetaDeg] = eField  # Update array with e-field

                    return fields

                def PatchEHPlanePlot(Freq, W, L, h, Er, isLog=True):
                    """
                    Plot 2D plots showing E-field for E-plane (phi = 0°) and the H-plane (phi = 90°).
                    """

                    fields = GetPatchFields(0, 360, 0, 90, Freq, W, L, h, Er)  # Calculate the field at each phi, theta

                    Xtheta = np.linspace(0, 90, 90)  # Theta range array used for plotting

                    if isLog:  # Can plot the log scale or normal
                        plt.plot(Xtheta, 20 * np.log10(abs(fields[90, :])),
                                 label="H-plane (Phi=90°)")  # Log = 20 * log10(E-field)
                        plt.plot(Xtheta, 20 * np.log10(abs(fields[0, :])), label="E-plane (Phi=0°)")
                        plt.ylabel('E-Field (dB)')
                    else:
                        plt.plot(Xtheta, fields[90, :], label="H-plane (Phi=90°)")
                        plt.plot(Xtheta, fields[0, :], label="E-plane (Phi=0°)")
                        plt.ylabel('E-Field')

                    plt.xlabel('Theta (degs)')  # Plot formatting
                    plt.title(
                        "Patch: \nW=" + str(W) + " \nL=" + str(L) + "\nEr=" + str(Er) + " h=" + str(h) + " \n@" + str(
                            Freq) + "Hz")
                    plt.ylim(-40)
                    plt.xlim((0, 90))

                    start, end = plt.xlim()
                    plt.xticks(np.arange(start, end, 5))
                    plt.grid(b=True, which='major')
                    plt.legend()
                    plt.show()  # Show plot

                    return fields  # Return the calculated fields

                def SurfacePlot(Fields, Freq, W, L, h, Er):
                    """Plots 3D surface plot over given theta/phi range in Fields by calculating cartesian coordinate equivalent of spherical form."""

                    print("Processing SurfacePlot...")

                    fig = plt.figure()
                    ax = fig.add_subplot(111, projection='3d')

                    phiSize = Fields.shape[0]  # Finds the phi & theta range
                    thetaSize = Fields.shape[1]

                    X = np.ones((phiSize, thetaSize))  # Prepare arrays to hold the cartesian coordinate data.
                    Y = np.ones((phiSize, thetaSize))
                    Z = np.ones((phiSize, thetaSize))

                    for phi in range(phiSize):  # Iterate over all phi/theta range
                        for theta in range(thetaSize):
                            e = Fields[phi][theta]

                            xe, ye, ze = sph2cart1(e, math.radians(theta),
                                                   math.radians(phi))  # Calculate cartesian coordinates

                            X[phi, theta] = xe  # Store cartesian coordinates
                            Y[phi, theta] = ye
                            Z[phi, theta] = ze

                    ax.plot_surface(X, Y, Z, color='b')  # Plot surface
                    plt.ylabel('Y')
                    plt.xlabel('X')  # Plot formatting
                    plt.title(
                        "Patch: \nW=" + str(W) + " \nL=" + str(L) + "\nEr=" + str(Er) + " h=" + str(h) + " \n@" + str(
                            Freq) + "Hz")
                    plt.show()

                def DesignPatch(Er, h, Freq):
                    """
                    Returns the patch_config parameters for standard lambda/2 rectangular microstrip patch. Patch length L and width W are calculated and returned together with supplied parameters Er and h.
                    Returned values are in the same format as the global patchr_config variable, so can be assigned directly. The patchr_config variable is of the following form [Er,W,L,h].
                    Usage: patchr_config=design_patchr(Er,h,Freq)
                    Er.....Relative dielectric constant
                    h......Substrate thickness (m)
                    Freq...Frequency (Hz)
                    e.g. patchr_config=design_patchr(3.43,0.7e-3,2e9)
                    """
                    Eo = 8.854185e-12

                    lambd = 3e8 / Freq
                    lambdag = lambd / sqrt(Er)

                    W = (3e8 / (2 * Freq)) * sqrt(2 / (Er + 1))

                    Ereff = ((Er + 1) / 2) + ((Er - 1) / 2) * (1 + 12 * (
                                h / W)) ** -0.5  # Calculate effictive dielectric constant for microstrip line of width W on dielectric material of constant Er

                    F1 = (Ereff + 0.3) * (
                                W / h + 0.264)  # Calculate increase length dL of patch length L due to fringing fields at each end, giving actual length L = Lambda/2 - 2*dL
                    F2 = (Ereff - 0.258) * (W / h + 0.8)
                    dL = h * 0.412 * (F1 / F2)

                    lambdag = lambd / sqrt(Ereff)
                    L = (lambdag / 2) - 2 * dL

                    print('Rectangular Microstrip Patch Design')
                    print("Frequency: " + str(Freq))
                    print("Dielec Const, Er : " + str(Er))
                    print("Patch Width,  W: " + str(W) + "m")
                    print("Patch Length,  L: " + str(L) + "m")
                    print("Patch Height,  h: " + str(h) + "m")

                    return W, L, h, Er

                """Some example patches with various thickness & Er."""
                print("Patch.py")

                freq = 14e9
                Er = 3.66  # RO4350B

                h = 0.101e-3
                W, L, h, Er = DesignPatch(Er, h, freq)
                fields = PatchEHPlanePlot(freq, W, L, h, Er)
                SurfacePlot(fields, freq, W, L, h, Er)

                h = 1.524e-3
                W, L, h, Er = DesignPatch(Er, h, freq)  # RO4350B
                fields = PatchEHPlanePlot(freq, W, L, h, Er)
                SurfacePlot(fields, freq, W, L, h, Er)

                fields = PatchEHPlanePlot(freq, 10.7e-3, 10.47e-3, 3e-3, 2.5)  # Random
                SurfacePlot(fields, freq, W, L, h, Er)
        return
        
class LifeSupport():
    """My new command"""

    def GetResources(self):
        return {'Pixmap'  : 'C:\\Users\\' + username + '\\AppData\\Roaming\\FreeCAD\\Mod\\SpacecraftDesigner\\Icons\\LifeSupport.jpg',
                'Accel' : "Shift+L", # a default shortcut (optional)
                'MenuText': "LifeSupport",
                'ToolTip' : "Define Spacecraft Life Support and Crew Systems"}

    def Activated(self):
        layout = [[sg.Text('Num Crew'), sg.InputText(''), sg.Button("OK", key="-CREW-")],
                  [sg.Text("Add Potable Water Tank"), sg.Button("OK", key="-WATER-")],
                  [sg.Text("Select Food"), sg.Button("OK", key="-FOOD-")],
                  [sg.Text("Add Workout Equipment"), sg.Button("OK", key="-WORK-")],
                  [sg.Text("Add Breathable Oxygen Tank"), sg.Button("OK", key="-OXYGEN-")],
                  [sg.Text("Add Carbon Dioxide Scrubber System"), sg.Button("OK", key="-CO2-")],
                  [sg.Text("Add Launch Escape System"),sg.Button("OK",key="-LES-")],
                  [sg.Text("Add Ejection Seat"), sg.Button("OK", key="-EJECT-")],
                  [sg.Text('Define Airlock'),sg.Button("OK",key="-AIRLOCK-",tooltip='An airlock is an airtight compartment with doors that can be used to transfer people and equipment from a pressurized spacecraft to the vacuum of space and vise-versa')],
                  [sg.Text('Define Temperature and Humidity Control System'), sg.Button("OK", key="-THC-", tooltip="The Temperature and Humidity Control System regulates the spacecraft internal temperature and humidity")],
                  [sg.Text('Define Waste Management System'), sg.Button("OK", key="-WMS-", tooltip="The Waste Management System collects solid and liquid human waste and either stores it in a safe location or recycles urine into drinking water. With proper precautions, human waste could be used to grow plants")],
                  [sg.Text('Define Atmosphere Revitalization System'),sg.Button("OK",key="-ARS-",tooltip='An atmospheric revitalization system ')],
        [sg.Submit(tooltip='Click to submit this window'), sg.Cancel()]]

        window = sg.Window('Life Support and Crew Systems', layout, default_element_size=(40, 1), grab_anywhere=False)

        event, values = window.read()

        window.close()    
        if event == "Cancel":
            window.close()
        elif event == "Submit":
            window.close()
        if event == "-WATER-":

            layout1 = [[sg.Text('Volume'), sg.InputText(''), sg.Text(' Liters'), sg.Button('Update', key="-VOLUME-")],
                      [sg.Text('Diameter'), sg.InputText(''), sg.Text(' Meters'), sg.Button('Update', key="-DIAMETER-")],
                      [sg.Text('Length'), sg.InputText(''), sg.Text(' Meters'), sg.Button('Update', key="-LENGTH-")],
                      [sg.Text('Add Tank'), sg.Submit()]]
            window1 = sg.Window('Potable Water System', layout1, default_element_size=(40, 1),
                               grab_anywhere=False)

            event1, values1 = window1.read()
            if event1 == "-VOLUME-":
                window1['-VOLUME-'].update(float(values1[0]))



        elif event == "-FOOD-":
            if event == "-FOOD-":
                TripHeader = ['      Food      ','Total Mass (Kg)','Calories','Protein','   Fat   ','Sat Fat','Fiber','Carbs']
                FoodList = []
                TripFoods = []
                i = 0
                with open(SCDesignerPath + '\\CREW_SYSTEMS\\nutrients_csvfile.csv', 'r') as csvfile:
                    Foods = csv.reader(csvfile, delimiter=',')
                    for row in Foods:
                        if i == 0:
                            Header = row
                            i = 1
                            continue
                        FoodList.append(row)
                totalfoodmass = 0
                layout = [[sg.Text('Quantity: '),sg.InputText('',key='-QUANTITY-',size=(5,1)), sg.Table(FoodList,
                                    headings=Header,
                                    auto_size_columns=True,
                                    key='Table')],
                          [sg.Text('Tot Mass: '),sg.Text(totalfoodmass,key='-TOTFOODMASS-'),sg.Text(' kgs'),sg.Table(TripFoods,
                                    headings=TripHeader,
                                    auto_size_columns=True,
                                    key='-TRIPFOODS-')]]

                win = sg.Window('Select Food',
                                layout, keep_on_top=True, finalize=True)

                myTable = win['Table']
                myTable.bind('<Button-1>', "Click")

                while True:
                    event, values = win.read()
                    # print(event, values)
                    if event in (None,):
                        win.close()
                        break
                    elif event == 'TableClick':
                        try:
                            bind_event = myTable.user_bind_event
                            col = myTable.Widget.identify_column(bind_event.x)
                            row_iid = myTable.Widget.identify_row(bind_event.y)
                            row = myTable.Widget.item(row_iid)
                            data = row['values']
                            quantity = int(values['-QUANTITY-'])
                            TripFoods.append([data[0],quantity*int(data[2])/1000,quantity*int(data[3]),quantity*int(data[4]),quantity*int(data[5])]) # convert to kgs

                            win.Element('-TRIPFOODS-').update(TripFoods)

                            for food in TripFoods:
                               totalfoodmass+=float(food[1])

                            win.Element('-TOTFOODMASS-').update(totalfoodmass)
                            # FoodType = row['values'][0]
                            # Nutritionval1 = float(row['values'][1])
                            # Nutritionval2 = float(row['values'][2])
                            # Nutritionval3 = float(row['values'][3])

                        except:
                            pass


        elif event == "-CREW-":

            def HabitableVol(duration, NumCrew, comfort):
                # Spacecraft Habitability
                # ENAE 697 - Space Human Factors and Life Support
                # University of Maryland
                # David L. Akin

                if comfort == "tolerable":
                    A = 5
                if comfort == "performance":
                    A = 10
                if comfort == "optimum":
                    A = 20
                # Returns required habitable volume in cubic meters
                Volume = NumCrew * A * (1 - math.exp(-(duration / 20)))
                return Volume

            duration = 180
            NumCrew = int(values[0])
            print(HabitableVol(duration, NumCrew, "tolerable"))
        return
        
class TestEngineering():
    """My new command"""

    def GetResources(self):
        return {'Pixmap'  : 'C:\\Users\\' + username + '\\AppData\\Roaming\\FreeCAD\\Mod\\SpacecraftDesigner\\Icons\\TestEgr.jpg',
                'Accel' : "Shift+R", # a default shortcut (optional)
                'MenuText': "TestEngineering",
                'ToolTip' : "TestEngineering"}

    def Activated(self):

        layout = [
            [sg.Text('Finite Element Analysis', size=(25, 1)), sg.InputCombo((
                                                                             'Static Analysis (Axial/Lateral w/ Launch Conditions)',
                                                                             'Vibration Analysis w/ Launch Conditions',
                                                                             'Pyrotechnic Shock Analysis',
                                                                             'Propulsion System Thrust Analysis',
                                                                             'Surface Landing Analysis',
                                                                             'Surface Mobility Analysis',
                                                                             'Docking Analysis',
                                                                             'Control Torque Effects on Appendages Analysis',
                                                                             'Robotic Arm Structural Analysis',
                                                                             'Pressure Vessel Analysis',
                                                                             'Aerodynamic Loads Analysis')),
             sg.Button('OK')],
            [sg.Submit(tooltip='Click to submit this window'), sg.Cancel()]    
        ]      


        window = sg.Window('Test Engineering', layout, default_element_size=(40, 1), grab_anywhere=False)      

        event, values = window.read()
        print(values[1])

        window.close()    
        if event == "Cancel":
            window.close()
        elif event == "Submit":
            window.close()
            print(values)
        return
        
class Manufacturing():
    """My new command"""

    def GetResources(self):
        return {'Pixmap'  : 'C:\\Users\\' + username + '\\AppData\\Roaming\\FreeCAD\\Mod\\SpacecraftDesigner\\Icons\\MFG.jpg',
                'Accel' : "Shift+F", # a default shortcut (optional)
                'MenuText': "Manufacturing",
                'ToolTip' : "Manufacturing"}

    def Activated(self):

        # ------ Column Definition ------ #      
        column1 = [[sg.Text('Column 1', background_color='#F7F3EC', justification='center', size=(10, 1))],      
                    [sg.Spin(values=('Spin Box 1', '2', '3'), initial_value='Spin Box 1')],      
                    [sg.Spin(values=('Spin Box 1', '2', '3'), initial_value='Spin Box 2')],      
                    [sg.Spin(values=('Spin Box 1', '2', '3'), initial_value='Spin Box 3')]]      

        layout = [      
            
            [sg.Text('Here is some text.... and a place to enter text')],      
            [sg.InputText('This is my text')],      
            [sg.Frame(layout=[      
            [sg.Checkbox('Checkbox', size=(10,1)),  sg.Checkbox('My second checkbox!', default=True)],      
            [sg.Radio('My first Radio!     ', "RADIO1", default=True, size=(10,1)), sg.Radio('My second Radio!', "RADIO1")]], title='Options',title_color='red', relief=sg.RELIEF_SUNKEN, tooltip='Use these to set flags')],      
            [sg.Multiline(default_text='This is the default Text should you decide not to type anything', size=(35, 3)),      
                sg.Multiline(default_text='A second multi-line', size=(35, 3))],      
            [sg.InputCombo(('Combobox 1', 'Combobox 2'), size=(20, 1)),      
                sg.Slider(range=(1, 100), orientation='h', size=(34, 20), default_value=85)],      
            [sg.InputOptionMenu(('Menu Option 1', 'Menu Option 2', 'Menu Option 3'))],      
            [sg.Listbox(values=('Listbox 1', 'Listbox 2', 'Listbox 3'), size=(30, 3)),      
                sg.Frame('Labelled Group',[[      
                sg.Slider(range=(1, 100), orientation='v', size=(5, 20), default_value=25),      
                sg.Slider(range=(1, 100), orientation='v', size=(5, 20), default_value=75),      
                sg.Slider(range=(1, 100), orientation='v', size=(5, 20), default_value=10),      
                sg.Column(column1, background_color='#F7F3EC')]])],      
            [sg.Text('_'  * 80)],      
            [sg.Text('Choose A Folder', size=(35, 1))],      
            [sg.Text('Your Folder', size=(15, 1), auto_size_text=False, justification='right'),      
                sg.InputText('Default Folder'), sg.FolderBrowse()],      
            [sg.Submit(tooltip='Click to submit this window'), sg.Cancel()]    
        ]      


        window = sg.Window('Manufacturing', layout, default_element_size=(40, 1), grab_anywhere=False)      

        event, values = window.read()
        print(values[1])

        window.close()    
        if event == "Cancel":
            window.close()
        elif event == "Submit":
            window.close()
            print(values)
        return



class Run():
    """My new command"""

    def GetResources(self):
        return {'Pixmap': 'C:\\Users\\' + username + '\\AppData\\Roaming\\FreeCAD\\Mod\\SpacecraftDesigner\\FLY.jpg',
                'Accel': "Shift+L",  # a default shortcut (optional)
                'MenuText': "Fly Mission",
                'ToolTip': "Fly Mission"}

    def Activated(self):
        SpaceportList = []
        i = 0
        with open('C:\\Users\\' + username + '\\AppData\\Roaming\\FreeCAD\\Mod\\SpacecraftDesigner\\Spaceports.csv', 'r') as csvfile:
            spamreader = csv.reader(csvfile, delimiter=',')
            for row in spamreader:
                if i == 0:
                    Header = row
                    i = 1
                    continue
                SpaceportList.append(row)

        layout = [

            [sg.Text('Select existing launch site')],
            [sg.InputCombo(('Kennedy Space Center', 'Starbase', 'Mid Atlantic Regional Spaceport', 'Guiana Space Centre', 'Mojave Air and Spaceport', 'Baikonour Cosmodrome','Pacific Spaceport Complex', 'Mojave Air and Space Port', 'Spaceport America', 'Starbase'))], #'Taiyuan Satellite Launch Center', 'Xichang Satellite Launch Center', 'Wenchang Satellite Launch Center', 'Vikram Sarabhai Space Centre', 'Satish Dhawan Space Centre', 'Uchinoura Space Center', 'Taiki Aerospace Research Field', 'Tanegashima Space Center', 'Andøya Space Center', 'Esrange'))],
            [sg.Radio('Launch right now with no calculations', "RADIO1"),
             sg.Radio('Pick a launch date and remind me', "RADIO1")],[sg.Submit(tooltip='Click to submit'), sg.Cancel()]]


        window = sg.Window('Fly Mission', layout, default_element_size=(40, 1), grab_anywhere=False)
        event, values = window.read()
        if event == "Cancel":
            window.close()
        elif event == "Submit":
            window.close()
            for spaceport in SpaceportList:
                # print(spaceport[0] + "\n\n")
                # print(values[0])
                if spaceport[0] == values[0]:
                    launch_lat = spaceport[1]
                    launch_lon = spaceport[2]
                    with open(SCDesignerPath + "\\LaunchLatLon.txt", "w+") as f:
                        f.write(launch_lat + "\n")
                        f.write(launch_lon)
                    f.close()

            import os.path
            import importOBJ
            import Draft
            import Mesh
            # import  pybullet as p
            ShapeList = []

            for obj in FreeCAD.ActiveDocument.Objects:
                if hasattr(obj, "Shape"):
                    ShapeList.append(obj.Name)

            # Gui.runCommand('a2p_Show_Hierarchy_Command',0)

            # uniqueshapelist = []
            # for shape in ShapeList:
            #	shapemod = shape[2:]
            #	modstop = shapemod.find("_")
            #	shapemod = shapemod[:modstop]
            #	uniqueshapelist.append(shapemod)
            #
            # uniqueshapelist = sorted(set(uniqueshapelist))

            if os.path.isdir(SCDesignerPath + "\\" + str(
                    App.ActiveDocument.Label)):
                pass
            else:
                os.mkdir(SCDesignerPath + "\\" + str(
                    App.ActiveDocument.Label))

            print(ShapeList)

            for shape in ShapeList:
                Draft.clone(FreeCAD.ActiveDocument.getObject(shape))
                shapemod = shape[2:]
                modstop = shapemod.find("_")
                shapemod = shapemod[:modstop]
                FreeCAD.getDocument(App.ActiveDocument.Label).getObject("Clone").Scale = (0.1000, 0.1000, 0.1000)
                ActiveDocName = str(App.ActiveDocument.Label)
                MeshExportName = SCDesignerPath + "/" + str(
                    App.ActiveDocument.Label) + "/" + shapemod + ".obj"
                App.getDocument(App.ActiveDocument.Label).recompute()
                __objs__ = []
                __objs__.append(FreeCAD.getDocument(App.ActiveDocument.Label).getObject("Clone"))
                Mesh.export(__objs__, MeshExportName)
                del __objs__
                App.getDocument(App.ActiveDocument.Label).removeObject('Clone')
                App.getDocument(App.ActiveDocument.Label).recompute()
                m = App.ActiveDocument.getObject(shape).Shape.MatrixOfInertia
                v = App.ActiveDocument.getObject(shape).Shape.Volume / 1000000000  # Convert volume from mm^3 to m^3
                p = FreeCAD.ActiveDocument.getObject(shape).Placement.Base
                ypr = str(FreeCAD.ActiveDocument.getObject(shape).Placement)
                startloc = ypr.find("Roll=")
                ypr = ypr[startloc + 6:-2]
                ypr = ypr.split(",")
                if os.path.exists(SCDesignerPath + "\\" + str(
                        App.ActiveDocument.Label) + "\\" + str(App.ActiveDocument.Label) + "Inertia.csv"):
                    with open(SCDesignerPath + "\\" + str(
                            App.ActiveDocument.Label) + "\\" + str(App.ActiveDocument.Label) + "Inertia.csv", 'a') as f:
                        f.write("\n")
                        f.write(str(shapemod) + ",")
                        for i in range(4):
                            for j in range(4):
                                f.write(str(m.A[i * 4 + j]) + ",")
                        f.write(str(v) + ",")
                        for i in range(3):
                            f.write(str(p[i]) + ",")
                        f.write(ypr[2] + ",")
                        f.write(ypr[1] + ",")
                        f.write(ypr[0] + ",")
                        f.close()
                else:

                    with open(SCDesignerPath + "\\" + str(
                            App.ActiveDocument.Label) + "\\" + str(App.ActiveDocument.Label) + "Inertia.csv", 'w') as f:
                        f.write(
                            "NAME,IXX,IXY,IXZ,IX0,IYX,IYY,IYZ,IY0,IZX,IZY,IZZ,IZ0,I0X,I0Y,I0Z,I00,VOL,X,Y,Z,R,P,Y\n")
                        f.write(str(shapemod) + ",")
                        for i in range(4):
                            for j in range(4):
                                f.write(str(m.A[i * 4 + j]) + ",")
                        f.write(str(v) + ",")
                        for i in range(3):
                            f.write(str(p[i]) + ",")
                        f.write(ypr[2] + ",")
                        f.write(ypr[1] + ",")
                        f.write(ypr[0] + ",")
                        f.close()
            Gui.activateWorkbench("A2plusWorkbench")
            Gui.runCommand('a2p_Show_Hierarchy_Command', 0)
            Gui.activateWorkbench("SpacecraftDesigner")







        return


FreeCADGui.addCommand('Explore',Explore())
FreeCADGui.addCommand('Payload',Payload())
# FreeCADGui.addCommand('Launch Vehicle',LaunchVehicle())
FreeCADGui.addCommand('Schedule',Schedule())
FreeCADGui.addCommand('Propulsion',Propulsion())
FreeCADGui.addCommand('Mechanical',Mechanical())
FreeCADGui.addCommand('Thermal',Thermal())
FreeCADGui.addCommand('Power',Power())
FreeCADGui.addCommand('Aero',Aero())
FreeCADGui.addCommand('GNC',GNC())
FreeCADGui.addCommand('Comms',Comms())
FreeCADGui.addCommand('LifeSupport',LifeSupport())
FreeCADGui.addCommand('TestEngineering',TestEngineering())
FreeCADGui.addCommand('Manufacturing',Manufacturing())
FreeCADGui.addCommand('Run',Run())



