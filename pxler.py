import websocket
import _thread
import time
import urllib.request
import json
import numpy
import colorama
import argparse
import os
from time import gmtime, strftime
from PIL import Image

PATH = ""
FRAMERATE = 0

# Init colors
colorama.init()

# Print logo
print(colorama.Fore.YELLOW + " _____ __ __ __    _____ _____")
print(colorama.Fore.YELLOW + "|  _  |  |  |  |  |   __| __  |")
print(colorama.Fore.YELLOW + "|   __|-   -|  |__|   __|    -|")
print(colorama.Fore.YELLOW + "|__|  |__|__|_____|_____|__|__|")

# Reset colors back
print(colorama.Style.RESET_ALL)
print("Exit with double CTRL-C")

# Setup argument parser
argparser = argparse.ArgumentParser(description="- Tool for timelapsing pxls.space")

# Add arguments
argparser.add_argument("path", type=str, nargs=1, help="Screenshot folder, must exist")
argparser.add_argument("--frame-rate", dest="framerate", action="store", type=int, default=5, help="Frame rate in seconds")
argparser.add_argument("-v", dest="verbose", action="store_const", const=True, default=False, help="Verbose mode")
argparser.add_argument("-vv", dest="veryverbose", action="store_const", const=True, default=False, help="Very verbose mode")
args = argparser.parse_args()

# Check if path exists
if os.path.exists(os.path.abspath(args.path[0])):
    PATH = os.path.abspath(args.path[0])
else:
    argparser.error("This path does not exists");

# Framerate
FRAMERATE = args.framerate


def place_pixel(x, y, color):
    world[x][y] = color_palette[color]

def use_boarddata(array, width, height):
    counter = 0
    for x in range(0, width):
        for y in range(0, height):
            place_pixel(x, y, array[counter])
            counter += 1

def create_palette(array):
    palette = []
    for color in array:
        hexcolor = color.lstrip('#')
        palette.append(tuple(int(hexcolor[i:i+2], 16) for i in (0, 2 ,4)))
    return palette

def on_message(ws, message):
    msg = json.loads(message)

    if msg["type"] == "pixel":
        place_pixel(int(msg["y"]), int(msg["x"]), int(msg["color"]))

        if args.veryverbose:
            print ("Updated pixel at " + str(msg["y"]) + ":" + str(msg["x"]) + " with color " + str(msg["color"]))

def on_error(ws, error):
    print(error)

def on_open(ws):
    if args.verbose or args.veryverbose:
        print("Connected !")
    def run(*arguments):
        while True:
            if args.verbose or args.veryverbose:
                print("Taking screenshot ...")
            img = Image.fromarray(world, "RGB")
            img.save(PATH + "/" + strftime("%Y-%m-%d-%H-%M-%S", gmtime()) + ".png")
            time.sleep(FRAMERATE)       
    _thread.start_new_thread(run, ())    

def on_close(ws):
    if args.verbose or args.veryverbose:
        print("Connection closed!")

if args.veryverbose:
    websocket.enableTrace(True)

while True:
    if args.verbose or args.veryverbose:
        print("Downloading info file ...")
    try:
        info = json.loads(urllib.request.urlopen("http://pxls.space/info").read().decode("utf-8"))
    except:
        if args.verbose or args.veryverbose:
            print("Download failed, retrying ...")
        continue

    if args.verbose or args.veryverbose:
        print("Downloading initial board data ...")
    try:
        boarddata = numpy.fromstring(urllib.request.urlopen("http://pxls.space/boarddata").read(), dtype=numpy.uint8)
    except:
        if args.verbose or args.veryverbose:
            print("Download failed, retrying ...")
        continue
    
    if args.verbose or args.veryverbose:
        print("Spawning world ...")
    world = numpy.zeros((int(info["width"]), int(info["height"]), 3), dtype=numpy.uint8)
    color_palette = create_palette(info["palette"])
    if args.verbose or args.veryverbose:
        print("Feeding world with initial data ...")
    use_boarddata(boarddata, int(info["width"]), int(info["height"]))
    if args.verbose or args.veryverbose:
        print("Connecting to the server ...")
    
    try:
        ws = websocket.WebSocketApp("ws://pxls.space/ws",
                                    on_message = on_message,
                                    on_error = on_error,
                                    on_close = on_close)
    except:
        if args.verbose or args.veryverbose:
            print("Connection failed, retrying ...")
        continue
    ws.on_open = on_open
    ws.run_forever()

    if args.verbose or args.veryverbose:
        print("Reconnecting in 5 seconds ...")

    time.sleep(5)