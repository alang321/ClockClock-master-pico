import machine
import time
import random
from ClockClock24 import ClockClock24
from DS3231_timekeeper import DS3231_timekeeper

#interrupt
def new_minute_handler():
    print("Interrupt received")
    
    hour, minute = rtc.get_hour_minute()
    
    clockclock.display_digit(0, hour//10)
    clockclock.display_digit(1, hour%10)
    clockclock.display_digit(2, minute//10)
    clockclock.display_digit(3, minute%10)

stepper_speed = 700
stepper_accel = 300

i2c1 = machine.I2C(1,sda=machine.Pin(14), scl=machine.Pin(3), freq=100000)
i2c0 = machine.I2C(0,sda=machine.Pin(16), scl=machine.Pin(17), freq=100000)

# slave addresses
slave_adr = [13, 12, # the adress of the slave with which this clock has to be adressed
             15, 14, 
             17, 16]

slave_bus = [i2c1, i2c0, # the bus the clock is on
             i2c1, i2c0, 
             i2c1, i2c0]

clockclock = ClockClock24(slave_adr, slave_bus, 4320)

time.sleep(10) #wait so clock modules have time to setup

rtc = DS3231_timekeeper(new_minute_handler, 13, i2c1)

while True:
    continue
