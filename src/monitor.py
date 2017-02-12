import sys
import time
from networktables import NetworkTables

NetworkTables.initialize(server = "10.17.69.69")

sd = NetworkTables.getTable("CameraData")

while True:
    try:
        print sd.getNumber('x'), sd.getNumber('y'), sd.getNumber('size'), sd.getNumber('count')
    except:
        print "Key problem"