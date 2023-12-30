#!/usr/bin/env python3

import logging
import time
import signal
import sys
import json
import serial
import math, random
#import click
import os.path
import RPi.GPIO as GPIO
from six.moves import input
from threading import Thread, Event
import threading
#from queue import Queue
from multiprocessing import Queue

import sounddevice as sd
from vosk import Model, KaldiRecognizer
import pyttsx3

#temporay for case with no arduino - add pty
import pty

# conversation queue
q = Queue()

# speach output software
speachEngine = pyttsx3.init()

# customizations
DRINK_SIZE = 8 # size of the cup to fill in ounces
# recipes below assume:
#   bottle 0 = vodka
#   bottle 1 = gin
#   bottle 2 = tequila
#   bottle 3 = rum
#   bottle 4 = triple sec
#   bottle 5 = lime cordial
#   bottle 6 = orange juice
#   bottle 7 = cranberry
#   bottle 8 = dummy used for proportions for shots

MENU = {
  'adirondack': [
    { 'bottle' : 0, 'proportion': 0 },
    { 'bottle' : 1, 'proportion': 2 },
    { 'bottle' : 2, 'proportion': 0 },
    { 'bottle' : 3, 'proportion': 0 },
    { 'bottle' : 4, 'proportion': 0 },
    { 'bottle' : 5, 'proportion': 0 },
    { 'bottle' : 6, 'proportion': 2 },
    { 'bottle' : 7, 'proportion': 0 },
  ],
  'bermuda triangle': [
    { 'bottle' : 0, 'proportion': 0 },
    { 'bottle' : 1, 'proportion': 0 },
    { 'bottle' : 2, 'proportion': 0 },
    { 'bottle' : 3, 'proportion': 2 },
    { 'bottle' : 4, 'proportion': 0 },
    { 'bottle' : 5, 'proportion': 0 },
    { 'bottle' : 6, 'proportion': 1 },
    { 'bottle' : 7, 'proportion': 5 },
  ],
  'blood bath punch': [
    { 'bottle' : 0, 'proportion': 1 },
    { 'bottle' : 1, 'proportion': 0 },
    { 'bottle' : 2, 'proportion': 0 },
    { 'bottle' : 3, 'proportion': 0 },
    { 'bottle' : 4, 'proportion': 0 },
    { 'bottle' : 5, 'proportion': 0 },
    { 'bottle' : 6, 'proportion': 4 },
    { 'bottle' : 7, 'proportion': 8 },
  ],
  'blossom': [
    { 'bottle' : 0, 'proportion': 0 },
    { 'bottle' : 1, 'proportion': 0 },
    { 'bottle' : 2, 'proportion': 0 },
    { 'bottle' : 3, 'proportion': 1 },
    { 'bottle' : 4, 'proportion': 0 },
    { 'bottle' : 5, 'proportion': 0 },
    { 'bottle' : 6, 'proportion': 1 },
    { 'bottle' : 7, 'proportion': 0 },
  ],
  'blush lily': [
    { 'bottle' : 0, 'proportion': 6 },
    { 'bottle' : 1, 'proportion': 0 },
    { 'bottle' : 2, 'proportion': 0 },
    { 'bottle' : 3, 'proportion': 0 },
    { 'bottle' : 4, 'proportion': 1 },
    { 'bottle' : 5, 'proportion': 8 },
    { 'bottle' : 6, 'proportion': 0 },
    { 'bottle' : 7, 'proportion': 12 },
  ],
  'brass monkey': [
    { 'bottle' : 0, 'proportion': 1 },
    { 'bottle' : 1, 'proportion': 0 },
    { 'bottle' : 2, 'proportion': 0 },
    { 'bottle' : 3, 'proportion': 1 },
    { 'bottle' : 4, 'proportion': 0 },
    { 'bottle' : 5, 'proportion': 0 },
    { 'bottle' : 6, 'proportion': 4 },
    { 'bottle' : 7, 'proportion': 0 },
  ],
  'california breeze': [
    { 'bottle' : 0, 'proportion': 3 },
    { 'bottle' : 1, 'proportion': 0 },
    { 'bottle' : 2, 'proportion': 0 },
    { 'bottle' : 3, 'proportion': 0 },
    { 'bottle' : 4, 'proportion': 1 },
    { 'bottle' : 5, 'proportion': 0 },
    { 'bottle' : 6, 'proportion': 4 },
    { 'bottle' : 7, 'proportion': 4 },
  ],
  'cape cod': [
    { 'bottle' : 0, 'proportion': 2 },
    { 'bottle' : 1, 'proportion': 0 },
    { 'bottle' : 2, 'proportion': 0 },
    { 'bottle' : 3, 'proportion': 0 },
    { 'bottle' : 4, 'proportion': 0 },
    { 'bottle' : 5, 'proportion': 0 },
    { 'bottle' : 6, 'proportion': 0 },
    { 'bottle' : 7, 'proportion': 6 },
  ],
  'cape codder': [
    { 'bottle' : 0, 'proportion': 2 },
    { 'bottle' : 1, 'proportion': 0 },
    { 'bottle' : 2, 'proportion': 0 },
    { 'bottle' : 3, 'proportion': 0 },
    { 'bottle' : 4, 'proportion': 0 },
    { 'bottle' : 5, 'proportion': 0 },
    { 'bottle' : 6, 'proportion': 0 },
    { 'bottle' : 7, 'proportion': 6 },
  ],
  'citrus cranberry punch': [
    { 'bottle' : 0, 'proportion': 2 },
    { 'bottle' : 1, 'proportion': 0 },
    { 'bottle' : 2, 'proportion': 0 },
    { 'bottle' : 3, 'proportion': 0 },
    { 'bottle' : 4, 'proportion': 26 },
    { 'bottle' : 5, 'proportion': 0 },
    { 'bottle' : 6, 'proportion': 6 },
    { 'bottle' : 7, 'proportion': 8 },
  ],
  'cosmo': [
    { 'bottle' : 0, 'proportion': 2 },
    { 'bottle' : 1, 'proportion': 0 },
    { 'bottle' : 2, 'proportion': 0 },
    { 'bottle' : 3, 'proportion': 0 },
    { 'bottle' : 4, 'proportion': 2 },
    { 'bottle' : 5, 'proportion': 1 },
    { 'bottle' : 6, 'proportion': 0 },
    { 'bottle' : 7, 'proportion': 2 },
  ],
  'cosmo rita': [
    { 'bottle' : 0, 'proportion': 0 },
    { 'bottle' : 1, 'proportion': 0 },
    { 'bottle' : 2, 'proportion': 3 },
    { 'bottle' : 3, 'proportion': 0 },
    { 'bottle' : 4, 'proportion': 1 },
    { 'bottle' : 5, 'proportion': 1 },
    { 'bottle' : 6, 'proportion': 0 },
    { 'bottle' : 7, 'proportion': 2 },
  ],
  'cosmopolitan': [
    { 'bottle' : 0, 'proportion': 2 },
    { 'bottle' : 1, 'proportion': 0 },
    { 'bottle' : 2, 'proportion': 0 },
    { 'bottle' : 3, 'proportion': 0 },
    { 'bottle' : 4, 'proportion': 2 },
    { 'bottle' : 5, 'proportion': 1 },
    { 'bottle' : 6, 'proportion': 0 },
    { 'bottle' : 7, 'proportion': 2 },
  ],
  'cran aid': [
    { 'bottle' : 0, 'proportion': 0 },
    { 'bottle' : 1, 'proportion': 0 },
    { 'bottle' : 2, 'proportion': 2 },
    { 'bottle' : 3, 'proportion': 0 },
    { 'bottle' : 4, 'proportion': 0 },
    { 'bottle' : 5, 'proportion': 0 },
    { 'bottle' : 6, 'proportion': 1 },
    { 'bottle' : 7, 'proportion': 0 },
  ],
  'cranberry': [
    { 'bottle' : 0, 'proportion': 0 },
    { 'bottle' : 1, 'proportion': 0 },
    { 'bottle' : 2, 'proportion': 0 },
    { 'bottle' : 3, 'proportion': 0 },
    { 'bottle' : 4, 'proportion': 0 },
    { 'bottle' : 5, 'proportion': 0 },
    { 'bottle' : 6, 'proportion': 6 },
    { 'bottle' : 7, 'proportion': 0 },
  ],
  'cranberry iced tea': [
    { 'bottle' : 0, 'proportion': 1 },
    { 'bottle' : 1, 'proportion': 1 },
    { 'bottle' : 2, 'proportion': 1 },
    { 'bottle' : 3, 'proportion': 1 },
    { 'bottle' : 4, 'proportion': 1 },
    { 'bottle' : 5, 'proportion': 2 },
    { 'bottle' : 6, 'proportion': 0 },
    { 'bottle' : 7, 'proportion': 8 },
  ],
  'cranberry juice': [
    { 'bottle' : 0, 'proportion': 0 },
    { 'bottle' : 1, 'proportion': 0 },
    { 'bottle' : 2, 'proportion': 0 },
    { 'bottle' : 3, 'proportion': 0 },
    { 'bottle' : 4, 'proportion': 0 },
    { 'bottle' : 5, 'proportion': 0 },
    { 'bottle' : 6, 'proportion': 6 },
    { 'bottle' : 7, 'proportion': 0 },
  ],
  'cranberry kamikaze': [
    { 'bottle' : 0, 'proportion': 3 },
    { 'bottle' : 1, 'proportion': 0 },
    { 'bottle' : 2, 'proportion': 0 },
    { 'bottle' : 3, 'proportion': 0 },
    { 'bottle' : 4, 'proportion': 2 },
    { 'bottle' : 5, 'proportion': 3 },
    { 'bottle' : 6, 'proportion': 0 },
    { 'bottle' : 7, 'proportion': 2 },
  ],
  'cranberry margarita': [
    { 'bottle' : 0, 'proportion': 0 },
    { 'bottle' : 1, 'proportion': 0 },
    { 'bottle' : 2, 'proportion': 3 },
    { 'bottle' : 3, 'proportion': 0 },
    { 'bottle' : 4, 'proportion': 1 },
    { 'bottle' : 5, 'proportion': 2 },
    { 'bottle' : 6, 'proportion': 0 },
    { 'bottle' : 7, 'proportion': 4 },
  ],
  'cranberry orange crush': [
    { 'bottle' : 0, 'proportion': 2 },
    { 'bottle' : 1, 'proportion': 0 },
    { 'bottle' : 2, 'proportion': 0 },
    { 'bottle' : 3, 'proportion': 0 },
    { 'bottle' : 4, 'proportion': 0 },
    { 'bottle' : 5, 'proportion': 0 },
    { 'bottle' : 6, 'proportion': 2 },
    { 'bottle' : 7, 'proportion': 2 },
  ],
  'cranberry orange rum spritzer': [
    { 'bottle' : 0, 'proportion': 0 },
    { 'bottle' : 1, 'proportion': 0 },
    { 'bottle' : 2, 'proportion': 0 },
    { 'bottle' : 3, 'proportion': 3 },
    { 'bottle' : 4, 'proportion': 0 },
    { 'bottle' : 5, 'proportion': 0 },
    { 'bottle' : 6, 'proportion': 2 },
    { 'bottle' : 7, 'proportion': 2 },
  ],
  'cranberry shot': [
    { 'bottle' : 0, 'proportion': 0 },
    { 'bottle' : 1, 'proportion': 0 },
    { 'bottle' : 2, 'proportion': 0 },
    { 'bottle' : 3, 'proportion': 0 },
    { 'bottle' : 4, 'proportion': 0 },
    { 'bottle' : 5, 'proportion': 0 },
    { 'bottle' : 6, 'proportion': 1 },
    { 'bottle' : 7, 'proportion': 0 },
  ],
  'cranberry toad': [
    { 'bottle' : 0, 'proportion': 2 },
    { 'bottle' : 1, 'proportion': 0 },
    { 'bottle' : 2, 'proportion': 0 },
    { 'bottle' : 3, 'proportion': 0 },
    { 'bottle' : 4, 'proportion': 0 },
    { 'bottle' : 5, 'proportion': 0 },
    { 'bottle' : 6, 'proportion': 1 },
    { 'bottle' : 7, 'proportion': 5 },
  ],
  'cranberry vodka': [
    { 'bottle' : 0, 'proportion': 3 },
    { 'bottle' : 1, 'proportion': 0 },
    { 'bottle' : 2, 'proportion': 0 },
    { 'bottle' : 3, 'proportion': 0 },
    { 'bottle' : 4, 'proportion': 0 },
    { 'bottle' : 5, 'proportion': 0 },
    { 'bottle' : 6, 'proportion': 0 },
    { 'bottle' : 7, 'proportion': 8 },
  ],
  'crantinis': [
    { 'bottle' : 0, 'proportion': 4 },
    { 'bottle' : 1, 'proportion': 0 },
    { 'bottle' : 2, 'proportion': 0 },
    { 'bottle' : 3, 'proportion': 0 },
    { 'bottle' : 4, 'proportion': 2 },
    { 'bottle' : 5, 'proportion': 1 },
    { 'bottle' : 6, 'proportion': 0 },
    { 'bottle' : 7, 'proportion': 8 },
  ],
  'creamsicle delight': [
    { 'bottle' : 0, 'proportion': 3 },
    { 'bottle' : 1, 'proportion': 0 },
    { 'bottle' : 2, 'proportion': 0 },
    { 'bottle' : 3, 'proportion': 0 },
    { 'bottle' : 4, 'proportion': 0 },
    { 'bottle' : 5, 'proportion': 0 },
    { 'bottle' : 6, 'proportion': 4 },
    { 'bottle' : 7, 'proportion': 0 },
  ],
  'gimlet': [
    { 'bottle' : 0, 'proportion': 0 },
    { 'bottle' : 1, 'proportion': 2 },
    { 'bottle' : 2, 'proportion': 0 },
    { 'bottle' : 3, 'proportion': 0 },
    { 'bottle' : 4, 'proportion': 0 },
    { 'bottle' : 5, 'proportion': 1 },
    { 'bottle' : 6, 'proportion': 0 },
    { 'bottle' : 7, 'proportion': 0 },
  ],
  'cranberry gimlet': [
    { 'bottle' : 0, 'proportion': 0 },
    { 'bottle' : 1, 'proportion': 8 },
    { 'bottle' : 2, 'proportion': 0 },
    { 'bottle' : 3, 'proportion': 0 },
    { 'bottle' : 4, 'proportion': 0 },
    { 'bottle' : 5, 'proportion': 4 },
    { 'bottle' : 6, 'proportion': 0 },
    { 'bottle' : 7, 'proportion': 3 },
  ],
  'gin and cranberry': [
    { 'bottle' : 0, 'proportion': 0 },
    { 'bottle' : 1, 'proportion': 1 },
    { 'bottle' : 2, 'proportion': 0 },
    { 'bottle' : 3, 'proportion': 0 },
    { 'bottle' : 4, 'proportion': 0 },
    { 'bottle' : 5, 'proportion': 0 },
    { 'bottle' : 6, 'proportion': 0 },
    { 'bottle' : 7, 'proportion': 3 },
  ],
  'gin and orange': [
    { 'bottle' : 0, 'proportion': 0 },
    { 'bottle' : 1, 'proportion': 3 },
    { 'bottle' : 2, 'proportion': 0 },
    { 'bottle' : 3, 'proportion': 0 },
    { 'bottle' : 4, 'proportion': 0 },
    { 'bottle' : 5, 'proportion': 0 },
    { 'bottle' : 6, 'proportion': 6 },
    { 'bottle' : 7, 'proportion': 0 },
  ],
  'gin and tonic': [
    { 'bottle' : 0, 'proportion': 0 },
    { 'bottle' : 1, 'proportion': 3 },
    { 'bottle' : 2, 'proportion': 0 },
    { 'bottle' : 3, 'proportion': 0 },
    { 'bottle' : 4, 'proportion': 0 },
    { 'bottle' : 5, 'proportion': 0 },
    { 'bottle' : 6, 'proportion': 0 },
    { 'bottle' : 7, 'proportion': 0 },
  ],
  'gin daiquiri': [
    { 'bottle' : 0, 'proportion': 0 },
    { 'bottle' : 1, 'proportion': 2 },
    { 'bottle' : 2, 'proportion': 0 },
    { 'bottle' : 3, 'proportion': 1 },
    { 'bottle' : 4, 'proportion': 0 },
    { 'bottle' : 5, 'proportion': 1 },
    { 'bottle' : 6, 'proportion': 0 },
    { 'bottle' : 7, 'proportion': 0 },
  ],
  'gin screwdriver': [
    { 'bottle' : 0, 'proportion': 0 },
    { 'bottle' : 1, 'proportion': 3 },
    { 'bottle' : 2, 'proportion': 0 },
    { 'bottle' : 3, 'proportion': 0 },
    { 'bottle' : 4, 'proportion': 0 },
    { 'bottle' : 5, 'proportion': 0 },
    { 'bottle' : 6, 'proportion': 6 },
    { 'bottle' : 7, 'proportion': 0 },
  ],
  'hurricane': [
    { 'bottle' : 0, 'proportion': 0 },
    { 'bottle' : 1, 'proportion': 0 },
    { 'bottle' : 2, 'proportion': 0 },
    { 'bottle' : 3, 'proportion': 2 },
    { 'bottle' : 4, 'proportion': 0 },
    { 'bottle' : 5, 'proportion': 0 },
    { 'bottle' : 6, 'proportion': 3 },
    { 'bottle' : 7, 'proportion': 3 },
  ],
  'kamakazie': [
    { 'bottle' : 0, 'proportion': 1 },
    { 'bottle' : 1, 'proportion': 0 },
    { 'bottle' : 2, 'proportion': 0 },
    { 'bottle' : 3, 'proportion': 0 },
    { 'bottle' : 4, 'proportion': 1 },
    { 'bottle' : 5, 'proportion': 1 },
    { 'bottle' : 6, 'proportion': 0 },
    { 'bottle' : 7, 'proportion': 0 },
  ],
  'leq spreader': [
    { 'bottle' : 0, 'proportion': 1 },
    { 'bottle' : 1, 'proportion': 1 },
    { 'bottle' : 2, 'proportion': 1 },
    { 'bottle' : 3, 'proportion': 1 },
    { 'bottle' : 4, 'proportion': 0 },
    { 'bottle' : 5, 'proportion': 0 },
    { 'bottle' : 6, 'proportion': 0 },
    { 'bottle' : 7, 'proportion': 0 },
  ],
  'long beach tea': [
    { 'bottle' : 0, 'proportion': 1 },
    { 'bottle' : 1, 'proportion': 1 },
    { 'bottle' : 2, 'proportion': 1 },
    { 'bottle' : 3, 'proportion': 1 },
    { 'bottle' : 4, 'proportion': 1 },
    { 'bottle' : 5, 'proportion': 2 },
    { 'bottle' : 6, 'proportion': 0 },
    { 'bottle' : 7, 'proportion': 2 },
  ],
  'madras': [
    { 'bottle' : 0, 'proportion': 3 },
    { 'bottle' : 1, 'proportion': 0 },
    { 'bottle' : 2, 'proportion': 0 },
    { 'bottle' : 3, 'proportion': 0 },
    { 'bottle' : 4, 'proportion': 0 },
    { 'bottle' : 5, 'proportion': 0 },
    { 'bottle' : 6, 'proportion': 2 },
    { 'bottle' : 7, 'proportion': 8 },
  ],
  'margarita': [
    { 'bottle' : 0, 'proportion': 0 },
    { 'bottle' : 1, 'proportion': 0 },
    { 'bottle' : 2, 'proportion': 3 },
    { 'bottle' : 3, 'proportion': 0 },
    { 'bottle' : 4, 'proportion': 1 },
    { 'bottle' : 5, 'proportion': 2 },
    { 'bottle' : 6, 'proportion': 0 },
    { 'bottle' : 7, 'proportion': 0 },
  ],
  'metropolitan': [
    { 'bottle' : 0, 'proportion': 2 },
    { 'bottle' : 1, 'proportion': 0 },
    { 'bottle' : 2, 'proportion': 0 },
    { 'bottle' : 3, 'proportion': 0 },
    { 'bottle' : 4, 'proportion': 2 },
    { 'bottle' : 5, 'proportion': 1 },
    { 'bottle' : 6, 'proportion': 0 },
    { 'bottle' : 7, 'proportion': 1 },
  ],
  'metropolitan cranberry martini': [
    { 'bottle' : 0, 'proportion': 2 },
    { 'bottle' : 1, 'proportion': 0 },
    { 'bottle' : 2, 'proportion': 0 },
    { 'bottle' : 3, 'proportion': 0 },
    { 'bottle' : 4, 'proportion': 2 },
    { 'bottle' : 5, 'proportion': 1 },
    { 'bottle' : 6, 'proportion': 0 },
    { 'bottle' : 7, 'proportion': 1 },
  ],
  'mexian madras': [
    { 'bottle' : 0, 'proportion': 0 },
    { 'bottle' : 1, 'proportion': 0 },
    { 'bottle' : 2, 'proportion': 4 },
    { 'bottle' : 3, 'proportion': 0 },
    { 'bottle' : 4, 'proportion': 0 },
    { 'bottle' : 5, 'proportion': 1 },
    { 'bottle' : 6, 'proportion': 2 },
    { 'bottle' : 7, 'proportion': 12 },
  ],
  'mexican river': [
    { 'bottle' : 0, 'proportion': 0 },
    { 'bottle' : 1, 'proportion': 0 },
    { 'bottle' : 2, 'proportion': 2 },
    { 'bottle' : 3, 'proportion': 0 },
    { 'bottle' : 4, 'proportion': 0 },
    { 'bottle' : 5, 'proportion': 2 },
    { 'bottle' : 6, 'proportion': 1 },
    { 'bottle' : 7, 'proportion': 6 },
  ],
  'midnight sun martini': [
    { 'bottle' : 0, 'proportion': 0 },
    { 'bottle' : 1, 'proportion': 0 },
    { 'bottle' : 2, 'proportion': 0 },
    { 'bottle' : 3, 'proportion': 0 },
    { 'bottle' : 4, 'proportion': 1 },
    { 'bottle' : 5, 'proportion': 0 },
    { 'bottle' : 6, 'proportion': 0 },
    { 'bottle' : 7, 'proportion': 6 },
  ],
  'my pleasure': [
    { 'bottle' : 0, 'proportion': 0 },
    { 'bottle' : 1, 'proportion': 0 },
    { 'bottle' : 2, 'proportion': 0 },
    { 'bottle' : 3, 'proportion': 2 },
    { 'bottle' : 4, 'proportion': 0 },
    { 'bottle' : 5, 'proportion': 0 },
    { 'bottle' : 6, 'proportion': 0 },
    { 'bottle' : 7, 'proportion': 6 },
  ],
  'new england iced tea': [
    { 'bottle' : 0, 'proportion': 1 },
    { 'bottle' : 1, 'proportion': 1 },
    { 'bottle' : 2, 'proportion': 1 },
    { 'bottle' : 3, 'proportion': 1 },
    { 'bottle' : 4, 'proportion': 1 },
    { 'bottle' : 5, 'proportion': 1 },
    { 'bottle' : 6, 'proportion': 0 },
    { 'bottle' : 7, 'proportion': 2 },
  ],
  'oj': [
    { 'bottle' : 0, 'proportion': 0 },
    { 'bottle' : 1, 'proportion': 0 },
    { 'bottle' : 2, 'proportion': 0 },
    { 'bottle' : 3, 'proportion': 0 },
    { 'bottle' : 4, 'proportion': 0 },
    { 'bottle' : 5, 'proportion': 0 },
    { 'bottle' : 6, 'proportion': 6 },
    { 'bottle' : 7, 'proportion': 0 },
  ],
  'oj shot': [
    { 'bottle' : 0, 'proportion': 0 },
    { 'bottle' : 1, 'proportion': 0 },
    { 'bottle' : 2, 'proportion': 0 },
    { 'bottle' : 3, 'proportion': 0 },
    { 'bottle' : 4, 'proportion': 0 },
    { 'bottle' : 5, 'proportion': 0 },
    { 'bottle' : 6, 'proportion': 1 },
    { 'bottle' : 7, 'proportion': 0 },
  ],
  'orange blossom': [
    { 'bottle' : 0, 'proportion': 0 },
    { 'bottle' : 1, 'proportion': 2 },
    { 'bottle' : 2, 'proportion': 0 },
    { 'bottle' : 3, 'proportion': 0 },
    { 'bottle' : 4, 'proportion': 0 },
    { 'bottle' : 5, 'proportion': 0 },
    { 'bottle' : 6, 'proportion': 2 },
    { 'bottle' : 7, 'proportion': 0 },
  ],
  'orange crush': [
    { 'bottle' : 0, 'proportion': 3 },
    { 'bottle' : 1, 'proportion': 0 },
    { 'bottle' : 2, 'proportion': 0 },
    { 'bottle' : 3, 'proportion': 0 },
    { 'bottle' : 4, 'proportion': 3 },
    { 'bottle' : 5, 'proportion': 0 },
    { 'bottle' : 6, 'proportion': 2 },
    { 'bottle' : 7, 'proportion': 0 },
  ],
  'orange gin buck': [
    { 'bottle' : 0, 'proportion': 0 },
    { 'bottle' : 1, 'proportion': 3 },
    { 'bottle' : 2, 'proportion': 0 },
    { 'bottle' : 3, 'proportion': 0 },
    { 'bottle' : 4, 'proportion': 0 },
    { 'bottle' : 5, 'proportion': 0 },
    { 'bottle' : 6, 'proportion': 1 },
    { 'bottle' : 7, 'proportion': 0 },
  ],
  'orange juice': [
    { 'bottle' : 0, 'proportion': 0 },
    { 'bottle' : 1, 'proportion': 0 },
    { 'bottle' : 2, 'proportion': 0 },
    { 'bottle' : 3, 'proportion': 0 },
    { 'bottle' : 4, 'proportion': 0 },
    { 'bottle' : 5, 'proportion': 0 },
    { 'bottle' : 6, 'proportion': 6 },
    { 'bottle' : 7, 'proportion': 0 },
  ],
  'orange juice shot': [
    { 'bottle' : 0, 'proportion': 0 },
    { 'bottle' : 1, 'proportion': 0 },
    { 'bottle' : 2, 'proportion': 0 },
    { 'bottle' : 3, 'proportion': 0 },
    { 'bottle' : 4, 'proportion': 0 },
    { 'bottle' : 5, 'proportion': 0 },
    { 'bottle' : 6, 'proportion': 1 },
    { 'bottle' : 7, 'proportion': 0 },
  ],
  'orange lime gin fizz': [
    { 'bottle' : 0, 'proportion': 0 },
    { 'bottle' : 1, 'proportion': 4 },
    { 'bottle' : 2, 'proportion': 0 },
    { 'bottle' : 3, 'proportion': 0 },
    { 'bottle' : 4, 'proportion': 0 },
    { 'bottle' : 5, 'proportion': 1 },
    { 'bottle' : 6, 'proportion': 1 },
    { 'bottle' : 7, 'proportion': 0 },
  ],
  'orange margarita': [
    { 'bottle' : 0, 'proportion': 0 },
    { 'bottle' : 1, 'proportion': 0 },
    { 'bottle' : 2, 'proportion': 3 },
    { 'bottle' : 3, 'proportion': 0 },
    { 'bottle' : 4, 'proportion': 1 },
    { 'bottle' : 5, 'proportion': 2 },
    { 'bottle' : 6, 'proportion': 4 },
    { 'bottle' : 7, 'proportion': 0 },
  ],
  'orange vesper martini': [
    { 'bottle' : 0, 'proportion': 2 },
    { 'bottle' : 1, 'proportion': 6 },
    { 'bottle' : 2, 'proportion': 0 },
    { 'bottle' : 3, 'proportion': 0 },
    { 'bottle' : 4, 'proportion': 1 },
    { 'bottle' : 5, 'proportion': 0 },
    { 'bottle' : 6, 'proportion': 2 },
    { 'bottle' : 7, 'proportion': 0 },
  ],
  'phoenix sunset margarita': [
    { 'bottle' : 0, 'proportion': 0 },
    { 'bottle' : 1, 'proportion': 0 },
    { 'bottle' : 2, 'proportion': 3 },
    { 'bottle' : 3, 'proportion': 0 },
    { 'bottle' : 4, 'proportion': 0 },
    { 'bottle' : 5, 'proportion': 1 },
    { 'bottle' : 6, 'proportion': 6 },
    { 'bottle' : 7, 'proportion': 0 },
  ],
  'prickly madras': [
    { 'bottle' : 0, 'proportion': 0 },
    { 'bottle' : 1, 'proportion': 0 },
    { 'bottle' : 2, 'proportion': 2 },
    { 'bottle' : 3, 'proportion': 0 },
    { 'bottle' : 4, 'proportion': 0 },
    { 'bottle' : 5, 'proportion': 0 },
    { 'bottle' : 6, 'proportion': 3 },
    { 'bottle' : 7, 'proportion': 3 },
  ],
  'red rooster': [
    { 'bottle' : 0, 'proportion': 4 },
    { 'bottle' : 1, 'proportion': 0 },
    { 'bottle' : 2, 'proportion': 0 },
    { 'bottle' : 3, 'proportion': 0 },
    { 'bottle' : 4, 'proportion': 0 },
    { 'bottle' : 5, 'proportion': 0 },
    { 'bottle' : 6, 'proportion': 1 },
    { 'bottle' : 7, 'proportion': 8 },
  ],
  'rum screwdriver': [
    { 'bottle' : 0, 'proportion': 0 },
    { 'bottle' : 1, 'proportion': 0 },
    { 'bottle' : 2, 'proportion': 0 },
    { 'bottle' : 3, 'proportion': 2 },
    { 'bottle' : 4, 'proportion': 0 },
    { 'bottle' : 5, 'proportion': 0 },
    { 'bottle' : 6, 'proportion': 4 },
    { 'bottle' : 7, 'proportion': 0 },
  ],
  'rum shot': [
    { 'bottle' : 0, 'proportion': 0 },
    { 'bottle' : 1, 'proportion': 0 },
    { 'bottle' : 2, 'proportion': 0 },
    { 'bottle' : 3, 'proportion': 1 },
    { 'bottle' : 4, 'proportion': 0 },
    { 'bottle' : 5, 'proportion': 0 },
    { 'bottle' : 6, 'proportion': 0 },
    { 'bottle' : 7, 'proportion': 0 },
    { 'bottle' : 8, 'proportion': 7 },
  ],
  'rum sunburst': [
    { 'bottle' : 0, 'proportion': 0 },
    { 'bottle' : 1, 'proportion': 0 },
    { 'bottle' : 2, 'proportion': 0 },
    { 'bottle' : 3, 'proportion': 2 },
    { 'bottle' : 4, 'proportion': 0 },
    { 'bottle' : 5, 'proportion': 0 },
    { 'bottle' : 6, 'proportion': 5 },
    { 'bottle' : 7, 'proportion': 1 },
  ],
  'sandy margarita': [
    { 'bottle' : 0, 'proportion': 0 },
    { 'bottle' : 1, 'proportion': 0 },
    { 'bottle' : 2, 'proportion': 3 },
    { 'bottle' : 3, 'proportion': 0 },
    { 'bottle' : 4, 'proportion': 0 },
    { 'bottle' : 5, 'proportion': 6 },
    { 'bottle' : 6, 'proportion': 3 },
    { 'bottle' : 7, 'proportion': 0 },
  ],
  'screwdriver': [
    { 'bottle' : 0, 'proportion': 2 },
    { 'bottle' : 1, 'proportion': 0 },
    { 'bottle' : 2, 'proportion': 0 },
    { 'bottle' : 3, 'proportion': 0 },
    { 'bottle' : 4, 'proportion': 0 },
    { 'bottle' : 5, 'proportion': 0 },
    { 'bottle' : 6, 'proportion': 6 },
    { 'bottle' : 7, 'proportion': 0 },
  ],
  'shark': [
    { 'bottle' : 0, 'proportion': 3 },
    { 'bottle' : 1, 'proportion': 0 },
    { 'bottle' : 2, 'proportion': 3 },
    { 'bottle' : 3, 'proportion': 0 },
    { 'bottle' : 4, 'proportion': 0 },
    { 'bottle' : 5, 'proportion': 0 },
    { 'bottle' : 6, 'proportion': 0 },
    { 'bottle' : 7, 'proportion': 0 },
  ],
  'south of the border screwdriver': [
    { 'bottle' : 0, 'proportion': 0 },
    { 'bottle' : 1, 'proportion': 0 },
    { 'bottle' : 2, 'proportion': 2 },
    { 'bottle' : 3, 'proportion': 0 },
    { 'bottle' : 4, 'proportion': 0 },
    { 'bottle' : 5, 'proportion': 0 },
    { 'bottle' : 6, 'proportion': 6 },
    { 'bottle' : 7, 'proportion': 0 },
  ],
  'tequila bite': [
    { 'bottle' : 0, 'proportion': 0 },
    { 'bottle' : 1, 'proportion': 0 },
    { 'bottle' : 2, 'proportion': 2 },
    { 'bottle' : 3, 'proportion': 0 },
    { 'bottle' : 4, 'proportion': 0 },
    { 'bottle' : 5, 'proportion': 0 },
    { 'bottle' : 6, 'proportion': 0 },
    { 'bottle' : 7, 'proportion': 6 },
  ],
  'tequila oasis': [
    { 'bottle' : 0, 'proportion': 0 },
    { 'bottle' : 1, 'proportion': 0 },
    { 'bottle' : 2, 'proportion': 2 },
    { 'bottle' : 3, 'proportion': 0 },
    { 'bottle' : 4, 'proportion': 1 },
    { 'bottle' : 5, 'proportion': 0 },
    { 'bottle' : 6, 'proportion': 2 },
    { 'bottle' : 7, 'proportion': 4 },
  ],
  'tequila screwdriver': [
    { 'bottle' : 0, 'proportion': 0 },
    { 'bottle' : 1, 'proportion': 0 },
    { 'bottle' : 2, 'proportion': 2 },
    { 'bottle' : 3, 'proportion': 0 },
    { 'bottle' : 4, 'proportion': 0 },
    { 'bottle' : 5, 'proportion': 0 },
    { 'bottle' : 6, 'proportion': 4 },
    { 'bottle' : 7, 'proportion': 0 },
  ],
  'tequila shot': [
    { 'bottle' : 0, 'proportion': 0 },
    { 'bottle' : 1, 'proportion': 0 },
    { 'bottle' : 2, 'proportion': 1 },
    { 'bottle' : 3, 'proportion': 0 },
    { 'bottle' : 4, 'proportion': 0 },
    { 'bottle' : 5, 'proportion': 0 },
    { 'bottle' : 6, 'proportion': 0 },
    { 'bottle' : 7, 'proportion': 0 },
  ],
  'tequila sunburst': [
    { 'bottle' : 0, 'proportion': 0 },
    { 'bottle' : 1, 'proportion': 0 },
    { 'bottle' : 2, 'proportion': 2 },
    { 'bottle' : 3, 'proportion': 0 },
    { 'bottle' : 4, 'proportion': 0 },
    { 'bottle' : 5, 'proportion': 0 },
    { 'bottle' : 6, 'proportion': 5 },
    { 'bottle' : 7, 'proportion': 1 },
  ],
  'tequila sunrise': [
    { 'bottle' : 0, 'proportion': 0 },
    { 'bottle' : 1, 'proportion': 0 },
    { 'bottle' : 2, 'proportion': 3 },
    { 'bottle' : 3, 'proportion': 0 },
    { 'bottle' : 4, 'proportion': 0 },
    { 'bottle' : 5, 'proportion': 0 },
    { 'bottle' : 6, 'proportion': 8 },
    { 'bottle' : 7, 'proportion': 0 },
  ],
  'the gto': [
    { 'bottle' : 0, 'proportion': 0 },
    { 'bottle' : 1, 'proportion': 16 },
    { 'bottle' : 2, 'proportion': 0 },
    { 'bottle' : 3, 'proportion': 0 },
    { 'bottle' : 4, 'proportion': 0 },
    { 'bottle' : 5, 'proportion': 2 },
    { 'bottle' : 6, 'proportion': 1 },
    { 'bottle' : 7, 'proportion': 0 },
  ],
  'vodka cranberry': [
    { 'bottle' : 0, 'proportion': 3 },
    { 'bottle' : 1, 'proportion': 0 },
    { 'bottle' : 2, 'proportion': 0 },
    { 'bottle' : 3, 'proportion': 0 },
    { 'bottle' : 4, 'proportion': 0 },
    { 'bottle' : 5, 'proportion': 0 },
    { 'bottle' : 6, 'proportion': 0 },
    { 'bottle' : 7, 'proportion': 8 },
  ],
  'vodka gimlet': [
    { 'bottle' : 0, 'proportion': 2 },
    { 'bottle' : 1, 'proportion': 0 },
    { 'bottle' : 2, 'proportion': 0 },
    { 'bottle' : 3, 'proportion': 0 },
    { 'bottle' : 4, 'proportion': 0 },
    { 'bottle' : 5, 'proportion': 1 },
    { 'bottle' : 6, 'proportion': 0 },
    { 'bottle' : 7, 'proportion': 0 },
  ],
  'vodka shot': [
    { 'bottle' : 0, 'proportion': 1 },
    { 'bottle' : 1, 'proportion': 0 },
    { 'bottle' : 2, 'proportion': 0 },
    { 'bottle' : 3, 'proportion': 0 },
    { 'bottle' : 4, 'proportion': 0 },
    { 'bottle' : 5, 'proportion': 0 },
    { 'bottle' : 6, 'proportion': 0 },
    { 'bottle' : 7, 'proportion': 0 },
    { 'bottle' : 8, 'proportion': 7 },
  ],
  'vodka sunrise': [
    { 'bottle' : 0, 'proportion': 1 },
    { 'bottle' : 1, 'proportion': 0 },
    { 'bottle' : 2, 'proportion': 0 },
    { 'bottle' : 3, 'proportion': 0 },
    { 'bottle' : 4, 'proportion': 0 },
    { 'bottle' : 5, 'proportion': 0 },
    { 'bottle' : 6, 'proportion': 5 },
    { 'bottle' : 7, 'proportion': 0 },
  ],
  'vodka tonic': [
    { 'bottle' : 0, 'proportion': 3 },
    { 'bottle' : 1, 'proportion': 0 },
    { 'bottle' : 2, 'proportion': 0 },
    { 'bottle' : 3, 'proportion': 0 },
    { 'bottle' : 4, 'proportion': 0 },
    { 'bottle' : 5, 'proportion': 0 },
    { 'bottle' : 6, 'proportion': 0 },
    { 'bottle' : 7, 'proportion': 0 },
  ],
  'double dutch cosmopolitan': [
    { 'bottle' : 0, 'proportion': 0 },
    { 'bottle' : 1, 'proportion': 5 },
    { 'bottle' : 2, 'proportion': 0 },
    { 'bottle' : 3, 'proportion': 0 },
    { 'bottle' : 4, 'proportion': 3 },
    { 'bottle' : 5, 'proportion': 1 },
    { 'bottle' : 6, 'proportion': 0 },
    { 'bottle' : 7, 'proportion': 6 },
  ],
  'gin cosmopolitan': [
    { 'bottle' : 0, 'proportion': 0 },
    { 'bottle' : 1, 'proportion': 5 },
    { 'bottle' : 2, 'proportion': 0 },
    { 'bottle' : 3, 'proportion': 0 },
    { 'bottle' : 4, 'proportion': 3 },
    { 'bottle' : 5, 'proportion': 1 },
    { 'bottle' : 6, 'proportion': 0 },
    { 'bottle' : 7, 'proportion': 6 },
  ],
  'plymouth rock': [
    { 'bottle' : 0, 'proportion': 0 },
    { 'bottle' : 1, 'proportion': 3 },
    { 'bottle' : 2, 'proportion': 0 },
    { 'bottle' : 3, 'proportion': 0 },
    { 'bottle' : 4, 'proportion': 0 },
    { 'bottle' : 5, 'proportion': 0 },
    { 'bottle' : 6, 'proportion': 0 },
    { 'bottle' : 7, 'proportion': 5 },
  ]
}


maxWordsInName = 0

# contstants
SER_DEVICE = '/dev/ttyACM0' # ensure correct file descriptor for connected arduino
PUSH_TO_TALK = False #True
PUSH_TO_TALK_PIN = 38
PUMP_SPEED = 0.056356667 # 100 ml / min = 0.056356667 oz / sec
NUM_BOTTLES = 8
PRIME_WHICH = None


def get_pour_time(pour_prop, total_prop):
    return ((float(DRINK_SIZE) * (float(pour_prop) / float(total_prop))) / PUMP_SPEED)

# def make_drink(drink_name, msg_q):
def make_drink(drink_name):
    timeToPour = 0
    print('make_drink()')

    #for key in MENU:
    #    print(key)
        
    # check that drink exists in menu
    if not drink_name in MENU:
        print('drink "' + drink_name + '" not in menu')
        return
    speachEngine.say('Making you a '+ drink_name);
    speachEngine.runAndWait();
    # get drink recipe
    recipe = MENU[drink_name]
    print(drink_name + ' = ' + str(recipe))

    # sort drink ingredients by proportion
    sorted_recipe = sorted(recipe, key=lambda p: p['proportion'], reverse=True)
    print(sorted_recipe)

    # calculate time to pour most used ingredient
    total_proportion = 0
    for p in sorted_recipe:
        total_proportion += p['proportion']
    drink_time = get_pour_time(sorted_recipe[0]['proportion'], total_proportion)
    print('Drink will take ' + str(math.floor(drink_time)) + 's')
    pouringShot = False
    
    # for each pour
    for i, pour in enumerate(sorted_recipe):

        # for first ingredient
        if i == 0:

            if pour['bottle'] ==8:
                pouringShot = True
                print("Pouring a shot")
            else:
              # start pouring with no delay
              pour_thread = Thread(target=trigger_pour, args=([msg_q, pour['bottle'], math.floor(drink_time), 0 , True, drink_name]))
              pour_thread.name = 'pour' + str(pour['bottle'])
              pour_thread.start()
              timeToPour=(math.floor(drink_time))


        # for other ingredients
        else:
            # calculate the latest time they could start
            pour_time = get_pour_time(pour['proportion'], total_proportion)
            latest_time = drink_time - pour_time
            
            # start each other ingredient at a random time between now and latest time
            delay = random.randint(0, math.floor(latest_time))
            if pouringShot:
              delay = 0
              timeToPour = math.floor(pour_time)
              pouringShot = False
            pour_thread = Thread(target=trigger_pour, args=([msg_q, pour['bottle'], math.floor(pour_time), delay]))
            pour_thread.name = 'pour' + str(pour['bottle'])
            pour_thread.start()
    
    print('time to pour' + str(timeToPour) )
    return timeToPour      
  


def trigger_pour(msg_q, bottle_num, pour_time, start_delay=0, last_bottle=False, drink_name=' '):

    if bottle_num > NUM_BOTTLES:
        print('Bad bottle number')
        return
    if pour_time == 0:
        return
    
    print('Pouring bottle ' + str(bottle_num) + ' for ' + str(pour_time) + 's after a ' + str(start_delay) + 's delay')

    time.sleep(start_delay) # start delay
    msg_q.put('b' + str(bottle_num) + 'r!') # start bottle pour
    time.sleep(pour_time) # wait
    msg_q.put('b' + str(bottle_num) + 'l!') # end bottle pour


def signal_handler(signal, frame):
    """ Ctrl+C handler to cleanup """

    if PUSH_TO_TALK:
        GPIO.cleanup()

    for t in threading.enumerate():
        print(t.name)
        if t.name == 'AssistantThread' or t.name == 'SerialThread':
            t.shutdown_flag.set()
            print('killing ' + str(t.name))

    print('Goodbye!')
    #sys.exit(1)


def poll(assistant_thread):
    """ Polling function for push-to-talk button """

    is_active = False
    # vals = [1, 1, 1]
    vals = [0, 0, 0]

    print('Polling for GPIO')
    
    while True:

        # get input value
        val = GPIO.input(PUSH_TO_TALK_PIN)
        # print("input = ", val)

        # shift values
        vals[2] = vals[1]
        vals[1] = vals[0]
        vals[0] = val

        # check for button press and hold
        # if (is_active == False) and (vals[2] == 1) and (vals[1] == 0) and (vals[0] == 0):
        if (is_active == False) and (vals[2] == 0) and (vals[1] == 1) and (vals[0] == 1):
            is_active = True
            assistant_thread.button_flag.set()
            print('Start talking')

        # check for button release
        # if (is_active == True) and (vals[2] == 0) and (vals[1] == 1) and (vals[0] == 1):
        if (is_active == True) and (vals[2] == 1) and (vals[1] == 0) and (vals[0] == 0):
            is_active = False

        # sleep
        time.sleep(0.1)
        
        
def callback(indata, frames, time, status):
    """This is called (from a separate thread) for each audio block."""
    if status:
        print(status, file=sys.stderr)
    q.put(bytes(indata))
    # print('callback called')
    
    
#
def setup_audio():
#
    global device_info
    global samplerate
    global model
    global dump_fn
    global sd
    device_info = sd.query_devices(None, "input")
    samplerate = int(device_info["default_samplerate"])
    model = Model(lang="en-us")
    dump_fn = None
    print('Audio set up.')
    return 0


def int_or_string(text):
    """Helper function for argument parsing."""
    try:
        return int(text)
    except ValueError:
        return text
    
def parseDrinkName(commandString):
    parsedCommandList = commandString.split(' ')
    wordsInCommand = len(parsedCommandList)
    wordsToSearch = min(maxWordsInName,wordsInCommand)
    print('words to search for name match= ' + str(wordsToSearch) )
    index=wordsInCommand-1
    drinkFound = ''
    found = False
    while wordsToSearch > 0:
        firstIndex = wordsInCommand - wordsToSearch
        while not found and firstIndex >=0:
            drinkName = ''
            index = 0
            offset = 0
            # build up a drink name from strings in command
            while index < wordsToSearch:
                drinkName =  drinkName + parsedCommandList[firstIndex+offset]
                index = index + 1
                offset = offset + 1
                if index < wordsToSearch:
                    # we need to add another word to form the drink so add a space delimiter
                    drinkName = drinkName + ' '
            print('> Search MENU for: ' + drinkName)
            if drinkName in MENU:
                print(drinkName + 'found in menu !!!!!!')
                found = True
                drinkFound = drinkName
            else:
                drinkFound = ''
            firstIndex = firstIndex - 1
            # time.sleep(1)
        wordsToSearch = wordsToSearch - 1        
        # if not drinkName in MENU:
    return drinkFound  




class AssistantThread(Thread):

    def __init__(self, msg_queue):
        Thread.__init__(self)
        self.shutdown_flag = Event()
        self.button_flag = Event()
        self.msg_queue = msg_queue

    def run(self):

 
#     # Keep the microphone open for follow on requests
        follow_on = False
        
        print('Assistant Thread running')

        while not self.shutdown_flag.is_set():

            # conversation ux lights off
            self.msg_queue.put('xo!')

            # get manual input start
            if not follow_on:

                if PUSH_TO_TALK:
                    while not self.button_flag.is_set():
                        print("read button")
                        time.sleep(0.1)
                        self.button_flag.clear()
                else :
                    print('Press Enter to send a new request.')
                    x = input("Enter command")
                    print("input=" + x)
   
                # conversation ux lights hotword
                self.msg_queue.put('xh!')

            else:

                # listening ux lights hotword
                self.msg_queue.put('xl!')

#      conversation_stream.start_recording()
            logging.info('Recording audio request.')
            with sd.RawInputStream(samplerate=samplerate, blocksize = 8000, device = None,
                    dtype="int16", channels=1, callback=callback):
                
                
                rec = KaldiRecognizer(model, samplerate)
                Drink_Found = False
                while not self.shutdown_flag.is_set() and not Drink_Found:
                    data = q.get()
                    if rec.AcceptWaveform(data):
                        #print(rec.Result())
                        plaintext = json.loads(rec.Result())
                        speakString = plaintext["text"]
                        print('speakstring='+speakString)
                        speakStringSize =len(speakString)
                        if speakStringSize > 0:
                            drinkFound = parseDrinkName(speakString)
                            print('returned drink ' + drinkFound)
                            #print(' # words=' + str(len(A)) )
                            if drinkFound == '':
                                print('drink "' + speakString + '" not in menu')
                                speachEngine.say('I don\'t understand "' + speakString + '" try again please.')
                                speachEngine.runAndWait();
                            else:                            
                                # speachEngine.say('do you want a '+ speakString);
                                speachEngine.runAndWait();
                                # Making drink ux lights 
                                self.msg_queue.put('xl!')
                                pourTime=0;
                                pourTime = make_drink(drinkFound);
                                Drink_Found = True
                        #if speakString.find("gin and tonic")>=0:
                        #if speakString.find("gin")>=0 and speakString.find("tonic")>=0:
                            #speakString="gin and tonic"
                            #Drink_Found = True
                        # soundstream.stop_stream()
            if Drink_Found:
                time.sleep(pourTime)
                speachEngine.say('Youre '+ drinkFound + ' is done.  Enjoy!')
                speachEngine.runAndWait();
            # Start the state machine for conversing
            print("call from gen_converse_request>>>>>>>>>>>")
            # conversation ux lights off
            self.msg_queue.put('xo!')

            print("return from gen_converse_request<<<<<<<<<<<<<<")
            print("stop_recording !")
 #       conversation_stream.stop_recording()
            print("start_playback")
 #       conversation_stream.start_playback()

      # This generator yields ConverseResponse proto messages received from the gRPC Google Assistant API.
 #     for resp in assistant.Assist(iter_assist_requests(), common_settings.DEFAULT_GRPC_DEADLINE):

 #       assistant_helpers.log_assist_response_without_audio(resp)
            print('return from response_with_no_audio')
                #make_drink('cherry bomb', self.msg_queue)
            # make_drink(speakString, self.msg_queue)
        ## DHN if resp.error.code != code_pb2.OK:
        ## DHN    logging.error('server error: %s', resp.error.message)
        ## DHN    break

#         if resp.event_type == END_OF_UTTERANCE:
#           self.msg_queue.put('xt!') # conversation ux lights thinking
#           logging.info('End of audio request detected')
#           print("stop_recording")
#           conversation_stream.stop_recording()
# 
#         if resp.speech_results:
#           logging.info('Transcript of user request: "%s".', resp.speech_results)
#           logging.info('Playing assistant response.')
#           self.msg_queue.put('xr!') # conversation ux lights responding
# 
#         if len(resp.audio_out.audio_data) > 0:
#           logging.info('Transcript of user request 1: "%s".', len(resp.audio_out.audio_data))
#           print("stop_recording")
#           conversation_stream.stop_recording()
#           ##DHN          logging.info('Transcript of user request: "%s".', resp)
#           print('writing audio data')
#           conversation_stream.write(resp.audio_out.audio_data)
# 
#         if resp.dialog_state_out.conversation_state:
#           conversation_state_bytes = resp.dialog_state_out.conversation_state
# 
#         if resp.dialog_state_out.volume_percentage != volume_percentage:
#           volume_percentage = resp.dialog_state_out.volume_percentage
#           logging.info('Volume should be set to %s%%' % volume_percentage)
# 
#         # check for follow on
#         if resp.dialog_state_out.microphone_mode == DIALOG_FOLLOW_ON:
#           follow_on = True
#           print('Expecting follow-on query from user.')
#           logging.info('Expecting follow-on query from user.')
#         elif resp.dialog_state_out.microphone_mode == CLOSE_MICROPHONE:
#           follow_on = False
#           conversation_state_bytes = None
#           print('Not expecting follow-on query from user.')
#           logging.info('Not expecting follow-on query from user.')
# 
#    conversation_stream.close()

class SerialThread(Thread):

    def __init__(self, msg_queue):
        Thread.__init__(self)
        self.shutdown_flag = Event()
        self.msg_queue = msg_queue;
# add back   self.serial = serial.Serial(SER_DEVICE, 9600)
# temporary code for no arduino
        master,slave = pty.openpty()
        s_name = os.ttyname(slave)
        self.serial = serial.Serial(s_name)
        print('Serial thread running')
    
    def run(self):

        while not self.shutdown_flag.is_set():
            time.sleep(0.1)

            if not self.msg_queue.empty():
                cmd = self.msg_queue.get()
                self.serial.write(str.encode(cmd))
                print('Serial sending ' + cmd)
                
        for i in range(8):
            cmd = 'b' + str(i) + 'l!'
            self.serial.write(str.encode(cmd))
            print('Serial shutting down command ' + cmd)
            time.sleep(0.1)


if __name__ == '__main__':

  # set log level (DEBUG, INFO, ERROR)
  ## DHN logging.basicConfig(level=logging.INFO)
    logging.basicConfig(level=logging.DEBUG)

  # handle SIGINT gracefully
    signal.signal(signal.SIGINT, signal_handler)


    for key in MENU:
        AA = key.split(' ')
        if len(AA) > maxWordsInName:
            maxWordsInName = len(AA)
            
    print('max words in drink name = '+ str(maxWordsInName))        
    #    print(key)

  # setup assistant
    ret_val = setup_audio()
#  if ret_val == 0:
    print('Mixalater is running')
    # create message queue for communicating between threads
    msg_q = Queue()

    # start serial thread - talks to arduino
    serial_thread = SerialThread(msg_q)
    serial_thread.name = 'SerialThread'
    serial_thread.start()
    
    # start assistant thread
    assistant_thread = AssistantThread(msg_q)
    assistant_thread.name = 'AssistantThread'
    assistant_thread.start()

    # # wait for main to finish until assistant thread is done
    assistant_thread.join()
    time.sleep(0.5)

    if PUSH_TO_TALK:

        # setup push to talk and start thread
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(PUSH_TO_TALK_PIN, GPIO.IN,pull_up_down=GPIO.PUD_DOWN)
        poll_thread = Thread(target=poll, args=([assistant_thread]))
        poll_thread.start()
