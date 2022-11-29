import machine
from struct import pack, unpack
import time

i2c0 = machine.I2C(0, sda=machine.Pin(16), scl=machine.Pin(17), freq=100000)


#buffer = pack("<BB", 0, 1) #start hotspot
buffer = pack("<BB", 0, 0) #stop hotspot
#buffer = pack("<BH", 1, 60) #poll ntp with 60 second timeout
#buffer = pack("<B", 2) #reset saved wifi data


buffer = pack("<BH", 1, 20)

i2c0.writeto(40, buffer)

time.sleep(50)

timebuf = i2c0.readfrom(40, 4)
valid, hour, minute, seconnd = unpack("<BBBB", timebuf)
print(bool(valid), hour, minute, seconnd)