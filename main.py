import machine
import time
from ClockClock24 import ClockClock24
from DS3231_timekeeper import DS3231_timekeeper
import uasyncio as asyncio
from OneButton import OneButton

#interrupt
def new_minute_handler():
    if __debug__:
        print("Interrupt received")
    global alarm_flag
    alarm_flag = True

#button handlers
def cycle_mode(pin):
    global current_field
    curr_mode = clockclock.get_mode()
    asyncio.create_task(clockclock.set_mode((curr_mode + 1) % len(ClockClock24.modes)))
    
    current_field = 3
        
def increment_digit(pin):
    # check if mode is time change
    if not clockclock.input_lock:
        if clockclock.get_mode() == ClockClock24.modes["change time"]:
            time_change_val = [[10, 0], [1, 0], [0, 10], [0, 1]]
            rtc.add_to_hour_minute(time_change_val[current_field][0], time_change_val[current_field][1])
            hour, minute = rtc.get_hour_minute()
            clockclock.display_time(hour, minute)

            if __debug__:
                print("New time:", hour, minute)
        elif clockclock.get_mode() == ClockClock24.modes["night mode config"]:
             clockclock.nightconf_incr_decr(1)
        
def decrement_digit(pin):
    if not clockclock.input_lock:
        if clockclock.get_mode() == ClockClock24.modes["change time"]:
            time_change_val = [[-10, 0], [-1, 0], [0, -10], [0, -1]]
            rtc.add_to_hour_minute(time_change_val[current_field][0], time_change_val[current_field][1])
            hour, minute = rtc.get_hour_minute()
            clockclock.display_time(hour, minute)

            if __debug__:
                print("New time:", hour, minute)
        elif clockclock.get_mode() == ClockClock24.modes["night mode config"]:
             clockclock.nightconf_incr_decr(-1)
    
def cycle_field(pin):
    global current_field
    if not clockclock.input_lock:
        if clockclock.get_mode() == ClockClock24.modes["change time"]:
            current_field -= 1
            current_field = current_field % 4

            if __debug__:
                print("Changed Field:", current_field)

            for clk_index in clockclock.digit_display.digit_display_indices[current_field]:
                clockclock.hour_steppers[clk_index].move(clockclock.steps_full_rev, 1)
                clockclock.minute_steppers[clk_index].move(clockclock.steps_full_rev, -1)
        elif clockclock.get_mode() == ClockClock24.modes["night mode config"]:
            clockclock.nightconf_next_digit()
            
def cycle_page(pin):
    if not clockclock.input_lock:
        if clockclock.get_mode() == ClockClock24.modes["night mode config"]:
            clockclock.nightconf_next_page()

#main loop
async def main_loop():
    global alarm_flag
    
    button_mode = OneButton(19, True)
    button_plus = OneButton(21, True)
    button_minus = OneButton(18, True)
    button_next_digit = OneButton(20, True)
    buttons = [button_mode, button_plus, button_minus, button_next_digit]

    button_mode.attachClick(cycle_mode)
    button_plus.attachClick(increment_digit)
    button_minus.attachClick(decrement_digit)
    button_next_digit.attachClick(cycle_field)
    button_next_digit.attachLongPressStop(cycle_page)

    while True:
        if alarm_flag:
            alarm_flag = False
            hour, minute = rtc.get_hour_minute()
            clockclock.display_time(hour, minute)
        
        await clockclock.run()

        for button in buttons:
            button.tick()
        
        await asyncio.sleep_ms(10)

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

alarm_flag = False
current_field = 3 # right most digit

rtc = DS3231_timekeeper(new_minute_handler, 13, i2c1)

asyncio.run(main_loop())
