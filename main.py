import machine
import time
from struct import pack
import random
import utime
import urtc
import machine
from ClockStepper import ClockStepper
from DigitDisplay import DigitDisplay

#interrupt
def handle_alarm(pin):
    global alarm_flag
    alarm_flag = True

steps_full_rev = 4320
stepper_speed = 700
stepper_accel = 300

sda1 = machine.Pin(14)
scl1 = machine.Pin(3)
i2c1 = machine.I2C(1,sda=sda1, scl=scl1, freq=100000)

sda0 = machine.Pin(16)
scl0 = machine.Pin(17)
i2c0 = machine.I2C(0,sda=sda0, scl=scl0, freq=100000)

# slave addresses
slave_adr = [13, 13, 13, 13, 12, 12, 12, 12, # the adress of the slave with which this clock has to be adressed
             15, 15, 15, 15, 14, 14, 14, 14, 
             17, 17, 17, 17, 16, 16, 16, 16]

slave_bus = [i2c1, i2c1, i2c1, i2c1, i2c0, i2c0, i2c0, i2c0, # the bus the clock is on
             i2c1, i2c1, i2c1, i2c1, i2c0, i2c0, i2c0, i2c0, 
             i2c1, i2c1, i2c1, i2c1, i2c0, i2c0, i2c0, i2c0]

sub_id = [0, 1, 2, 3, 0, 1, 2, 3, # the id (subid) the clock has at the slave 0-3
          0, 1, 2, 3, 0, 1, 2, 3, 
          0, 1, 2, 3, 0, 1, 2, 3]

minute_steppers = [ClockStepper(sub_id[clk_index], slave_bus[clk_index], slave_adr[clk_index]) for clk_index in range(len(slave_adr))]
hour_steppers = [ClockStepper((sub_id[clk_index] + 4), slave_bus[clk_index], slave_adr[clk_index]) for clk_index in range(len(slave_adr))]

# digit display units, contains the clock indexes making making up a double digit display, 1 sublist is 1 number, from left to right
digit_display_indeces = [[0, 1, 8, 9, 16, 17], [2, 3, 10, 11, 18, 19], [4, 5, 12, 13, 20, 21], [6, 7, 14, 15, 22, 23]]

digit_displays = [DigitDisplay([minute_steppers[i] for i in clk_index_list], [hour_steppers[i] for i in clk_index_list]) for clk_index_list in digit_display_indeces]

time.sleep(10)

rtc = urtc.DS3231(i2c1)

#setup interrupt
alarm_flag = False
alarmtime = urtc.datetime_tuple(year=2000, month=1, day=None, weekday=None, hour=None, minute=None, second=0, millisecond=0)
rtc.interrupt()
alarm_pin = machine.Pin(13, machine.Pin.IN, machine.Pin.PULL_UP)
alarm_pin.irq(trigger=machine.Pin.IRQ_FALLING, handler=handle_alarm)
rtc.alarm(False)
rtc.alarm_time(alarmtime)

while True:
    if alarm_flag:
        rtc.alarm(False)
        alarm_flag = False
        
        current_time = rtc.datetime()
        
        hour0 = current_time.hour//10
        hour1 = current_time.hour%10
        minute0 = current_time.minute//10
        minute1 = current_time.minute%10
        
        digit_displays[0].display_digit(hour0)
        digit_displays[0].display_digit(hour1)
        digit_displays[0].display_digit(minute0)
        digit_displays[0].display_digit(minute1)
