#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup
import os

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name = "larawed",
    version = "1.0.0",
    author = "Josef Kuchař",
    author_email = "josef.kuchar267@gmail.com",
    description = "Tool for timelapsing pxls.space",
    license = "GPLv3",
    keywords = "space pxls timelapse python websocket",
    url = "https://github.com/JosefKuchar/PXLER",
    long_description = read("README.md"),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Topic :: Utilities",
        "License :: GNUv3 License"
    ],
    install_requires = [
        "colorama",
        "websocket-client",
        "numpy",
        "pillow",
        "argparse"
    ]
)
