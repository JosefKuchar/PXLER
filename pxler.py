#!/usr/bin/env python3

import urllib.request
import time
import json
import argparse
import os
import sys
import websocket
import _thread
import numpy
import colorama
import signal
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
argparser.add_argument("--server", dest="server", action="store", default="pxls.space", help="Alternative server")
argparser.add_argument("--format", dest="format", action="store", default="png", help="Image format - png or jpg")
argparser.add_argument("--quality", dest="quality", action="store", type=int, default=100, help="JPEG image quality - 0 - 100")
argparser.add_argument("-v", dest="verbose", action="store_const", const=True, default=False, help="Verbose mode")
argparser.add_argument("-vv", dest="veryverbose", action="store_const", const=True, default=False, help="Very verbose mode")

args = argparser.parse_args()

# Check if path exists
if os.path.exists(os.path.abspath(args.path[0])):
    PATH = os.path.abspath(args.path[0])
else:
    argparser.error("This path does not exists")

# Check if format is valid
if args.format != "png" and args.format != "jpg":
    argparser.error("This format is not valid")

# Check quality range
if args.quality < 0 or args.quality > 100:
    argparser.error("This quality is not valid")

# Quality only on jpeg check
if args.format == "png" and args.quality != 100:
    argparser.error("You cannot use quality option with png")

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
            img.save(PATH + "/" + time.strftime("%Y%m%d-%H%M%S") + "." + args.format, quality=args.quality)
        time.sleep(args.framerate)

def on_close(websoc):
    """ Websocket connection close handler """
    if args.verbose or args.veryverbose:
        log("Connection closed!")

def exit_handler(signal, frame):
    """ Ctrl-C handler """
    log("Exiting")
    sys.exit(0)

signal.signal(signal.SIGINT, exit_handler)

if args.veryverbose:
    websocket.enableTrace(True)

_thread.start_new_thread(run, ())

while True:
    # Download info file with width, height and palette
    if args.verbose or args.veryverbose:
        log("Downloading info file ...")

    while True:
        try:
            request = urllib.request.Request("http://" + args.server + "/info")
            request.add_header("Cookie", "pxls-agegate=1")
            info = json.loads(urllib.request.urlopen(request).read().decode("utf-8"))
        except:
            if args.verbose or args.veryverbose:
                log("Download failed, retrying ...")
            time.sleep(5)
            continue
        break


    # Download complete board data
    if args.verbose or args.veryverbose:
        log("Downloading initial board data ...")

    while True:
        try:
            request = urllib.request.Request("http://" + args.server + "/boarddata")
            request.add_header("Cookie", "pxls-agegate=1")
            boarddata = numpy.fromstring(urllib.request.urlopen(request).read(), dtype=numpy.uint8)
        except:
            if args.verbose or args.veryverbose:
                log("Download failed, retrying ...")
            time.sleep(5)
            continue
        break


    # Initialize empty array
    if args.verbose or args.veryverbose:
        log("Spawning world ...")
    world = numpy.zeros((int(info["width"]), int(info["height"]), 3), dtype=numpy.uint8)


    # Create palette from info
    color_palette = create_palette(info["palette"])


    # Use complete world data
    if args.verbose or args.veryverbose:
        log("Feeding world with initial data ...")
    use_boarddata(boarddata, int(info["width"]), int(info["height"]))


    # Establish connection to main websocket server
    if args.verbose or args.veryverbose:
        log("Connecting to the server ...")

    try:
        ws = websocket.WebSocketApp("ws://" + args.server + "/ws", on_message=on_message, on_error=on_error, on_close=on_close, cookie="pxls-agegate=1")
    except:
        if args.verbose or args.veryverbose:
            log("Connection failed, retrying ...")
        time.sleep(5)
        continue
    ws.on_open = on_open
    ws.run_forever()

    READY = False



    # Retry connection on disconnect
    if args.verbose or args.veryverbose:
        log("Reconnecting in 5 seconds ...")

    time.sleep(5)
