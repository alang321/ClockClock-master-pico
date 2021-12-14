import machine
import time
from ClockClock24 import ClockClock24
from DS3231_timekeeper import DS3231_timekeeper

#interrupt
def new_minute_handler():
    print("Interrupt received")
    
    hour, minute = rtc.get_hour_minute()
    
    clockclock.display_time(hour, minute)

i2c1 = machine.I2C(1,sda=machine.Pin(14), scl=machine.Pin(3), freq=100000)
i2c0 = machine.I2C(0,sda=machine.Pin(16), scl=machine.Pin(17), freq=100000)

# slave addresses
slave_adr = [13, 12, # the adress of the slave with which this clock has to be adressed
             15, 14, 
             17, 16]

slave_bus = [i2c1, i2c0, # the bus the clock is on
             i2c1, i2c0, 
             i2c1, i2c0]

time.sleep(6) #wait so clock modules have time to setup

clockclock = ClockClock24(slave_adr, slave_bus, ClockClock24.modes["visual"], 4320)

rtc = DS3231_timekeeper(new_minute_handler, 13, i2c1)

button = machine.Pin(26, machine.Pin.IN, machine.Pin.PULL_UP)

is_pressed = False

while True:
    if button.value() == 0 and not is_pressed:
        is_pressed = True
        print("Change Mode")
        curr_mode = clockclock.get_mode()
        clockclock.set_mode((curr_mode + 1) % len(ClockClock24.modes))
        time.sleep(0.2)
    else:
        is_pressed = False
    continue
