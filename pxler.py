#!/usr/bin/env python3

import urllib.request
import time
import json
import argparse
import os
import websocket
import _thread
import numpy
import colorama
from PIL import Image

PATH = ""
READY = False

# Init colors
colorama.init()

# Print logo
print(colorama.Fore.YELLOW + " _____ __ __ __    _____ _____")
print(colorama.Fore.YELLOW + "|  _  |  |  |  |  |   __| __  |")
print(colorama.Fore.YELLOW + "|   __|-   -|  |__|   __|    -|")
print(colorama.Fore.YELLOW + "|__|  |__|__|_____|_____|__|__|")
print(colorama.Style.RESET_ALL + "https://github.com/JosefKuchar/PXLER\n")
print("Exit with double CTRL-C\n")

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
    argparser.error("This path does not exists")

def log(string):
    """ Custom logging function """
    print(colorama.Fore.CYAN + "[" + colorama.Style.RESET_ALL + time.strftime("%d.%m.%Y - %H:%M:%S") + colorama.Fore.CYAN + "] " + colorama.Style.RESET_ALL + string)

def place_pixel(x, y, color):
    """ Transform color value to RGB """
    world[x][y] = color_palette[color]

def use_boarddata(array, width, height):
    """ Transform 1D array to 2D and replace color values with RGB """
    counter = 0
    for x in range(0, width):
        for y in range(0, height):
            place_pixel(x, y, array[counter])
            counter += 1

def create_palette(array):
    """ Transform hex string to rgb values """
    palette = []
    for color in array:
        hexcolor = color.lstrip('#')
        palette.append(tuple(int(hexcolor[i:i+2], 16) for i in (0, 2, 4)))
    return palette


def on_message(websoc, message):
    """ Websocket message handler """
    msg = json.loads(message)

    if msg["type"] == "pixel":

        for pixel in msg["pixels"]:
            place_pixel(pixel["y"], pixel["x"], pixel["color"])

            if args.veryverbose:
                log("Updated pixel at " + str(pixel["y"]) + ":" + str(pixel["x"]) + " with color " + str(pixel["color"]))
def on_error(websoc, error):
    """ Websocket error handler """
    log(error)

def on_open(websoc):
    """ Websocket connection open handler """
    if args.verbose or args.veryverbose:
        log("Connected !")
    global READY
    READY = True

def run():
    """ Screenshot thread """
    while True:
        if READY:
            if args.verbose or args.veryverbose:
                log("Taking screenshot ...")
            img = Image.fromarray(world, "RGB")
            img.save(PATH + "/" + time.strftime("%Y%m%d-%H%M%S") + ".png")
        time.sleep(int(args.framerate))

def on_close(websoc):
    """ Websocket connection close handler """
    if args.verbose or args.veryverbose:
        log("Connection closed!")

if args.veryverbose:
    websocket.enableTrace(True)

_thread.start_new_thread(run, ())

while True:
    if args.verbose or args.veryverbose:
        log("Downloading info file ...")
    try:
        info = json.loads(urllib.request.urlopen("http://pxls.space/info").read().decode("utf-8"))
    except:
        if args.verbose or args.veryverbose:
            log("Download failed, retrying ...")
        READY = False
        continue

    if args.verbose or args.veryverbose:
        log("Downloading initial board data ...")
    try:
        boarddata = numpy.fromstring(urllib.request.urlopen("http://pxls.space/boarddata").read(), dtype=numpy.uint8)
    except:
        if args.verbose or args.veryverbose:
            log("Download failed, retrying ...")
        READY = False
        continue

    if args.verbose or args.veryverbose:
        log("Spawning world ...")
    world = numpy.zeros((int(info["width"]), int(info["height"]), 3), dtype=numpy.uint8)
    color_palette = create_palette(info["palette"])
    if args.verbose or args.veryverbose:
        log("Feeding world with initial data ...")
    use_boarddata(boarddata, int(info["width"]), int(info["height"]))
    if args.verbose or args.veryverbose:
        log("Connecting to the server ...")

    try:
        ws = websocket.WebSocketApp("ws://pxls.space/ws", on_message=on_message, on_error=on_error, on_close=on_close)
    except:
        if args.verbose or args.veryverbose:
            log("Connection failed, retrying ...")
        READY = False
        continue
    ws.on_open = on_open
    ws.run_forever()

    READY = False

    if args.verbose or args.veryverbose:
        log("Reconnecting in 5 seconds ...")

    time.sleep(5)
