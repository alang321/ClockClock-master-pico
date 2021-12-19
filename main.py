import machine
import time
from ClockClock24 import ClockClock24
from DS3231_timekeeper import DS3231_timekeeper

#interrupt
def new_minute_handler():
    print("Interrupt received")
    global alarm_flag
    alarm_flag = True

#button handlers
def cycle_mode():
    curr_mode = clockclock.get_mode()
    clockclock.set_mode((curr_mode + 1) % len(ClockClock24.modes))
    print("Change Mode:", clockclock.get_mode())
    
def increment_digit():
    # check if mode is time change
    if clockclock.get_mode() == ClockClock24.modes["change time"]:
        time_change_val = [[10, 0], [1, 0], [0, 10], [0, 1]]
        rtc.add_to_hour_minute(time_change_val[current_field][0], time_change_val[current_field][1])
        hour, minute = rtc.get_hour_minute()
        clockclock.display_time(hour, minute)
        print("new time", hour, minute)
        
def decrement_digit():
    if clockclock.get_mode() == ClockClock24.modes["change time"]:
        time_change_val = [[-10, 0], [-1, 0], [0, -10], [0, -1]]
        rtc.add_to_hour_minute(time_change_val[current_field][0], time_change_val[current_field][1])
        hour, minute = rtc.get_hour_minute()
        clockclock.display_time(hour, minute)
        print("new time", hour, minute)
    
def cycle_field():
    if clockclock.get_mode() == ClockClock24.modes["change time"]:
        global current_field
        current_field -= 1
        current_field = current_field % 4
        print("Change Field:",current_field)
        
        hour, minute = rtc.get_hour_minute()
        digits = [hour//10, hour%10, minute//10, minute%10]
        clockclock.digit_display.display_digit(current_field, digits[current_field], 1, 1)
    

i2c1 = machine.I2C(1,sda=machine.Pin(14), scl=machine.Pin(3), freq=100000)
i2c0 = machine.I2C(0,sda=machine.Pin(16), scl=machine.Pin(17), freq=100000)

# module addresses  (pcb containing 4 steppers and a mcu, stm32f103 in this case)
module_i2c_adr = [13, 12, # the adress of the module starting top left row first
                  15, 14, 
                  17, 16]

module_i2c_bus = [i2c1, i2c0, # the bus on which the module is
                  i2c1, i2c0, 
                  i2c1, i2c0]

time.sleep(6) #wait so clock modules have time to setup

clockclock = ClockClock24(module_i2c_adr, module_i2c_bus, ClockClock24.modes["stealth"], 4320)

button_mode = machine.Pin(19, machine.Pin.IN, machine.Pin.PULL_UP)
button_plus = machine.Pin(21, machine.Pin.IN, machine.Pin.PULL_UP)
button_minus = machine.Pin(18, machine.Pin.IN, machine.Pin.PULL_UP)
button_next_digit = machine.Pin(20, machine.Pin.IN, machine.Pin.PULL_UP)

buttons = [button_mode, button_plus, button_minus, button_next_digit]
is_pressed = [False for i in buttons]
button_down_handler = [cycle_mode, increment_digit, decrement_digit, cycle_field]

alarm_flag = False
current_field = 3 # right most digit

rtc = DS3231_timekeeper(new_minute_handler, 13, i2c1)

while True:
    if alarm_flag:
        alarm_flag = False
        hour, minute = rtc.get_hour_minute()
        clockclock.display_time(hour, minute)
        
    clockclock.run()
    
    do_debounce = False
    for but_index, button in enumerate(buttons):
        if button.value() == 0 and not is_pressed[but_index]:
            is_pressed[but_index] = True
            button_down_handler[but_index]()
            do_debounce = True
        elif button.value() == 1 and is_pressed[but_index]:
            do_debounce = True
            is_pressed[but_index] = False
            
    if do_debounce:
        time.sleep(0.01)#debounce    
        
    #set time buttons
    #clear     
