import machine
import time
from ClockClock24 import ClockClock24
import uasyncio as asyncio
from lib.OneButton import OneButton
from ClockSettings import ClockSettings

# button handlers
def cycle_mode(pin):
    curr_mode = clockclock.get_mode()
    clockclock.set_mode((curr_mode + 1) % len(ClockClock24.modes))
        
def increment_digit(pin):
    if not clockclock.input_lock:
        if clockclock.get_mode() == ClockClock24.modes["settings"]:
             clockclock.settings_incr_decr(1)
        
def decrement_digit(pin):
    if not clockclock.input_lock:
        if clockclock.get_mode() == ClockClock24.modes["settings"]:
             clockclock.settings_incr_decr(-1)
    
def cycle_field(pin):
    if not clockclock.input_lock:
        if clockclock.get_mode() == ClockClock24.modes["settings"]:
            clockclock.settings_next_digit()
            
def cycle_page(pin):
    if not clockclock.input_lock:
        if clockclock.get_mode() == ClockClock24.modes["settings"]:
            clockclock.settings_change_page(1)

#main loop
async def main_loop():
    global alarm_flag
    
    button_mode = OneButton(19, True)
    button_plus = OneButton(21, True)
    button_minus = OneButton(18, True)
    button_next_digit = OneButton(20, True)
    buttons = [button_mode, button_plus, button_minus, button_next_digit]

    button_mode.attachClick(cycle_mode)
    button_mode.attachLongPressStop(cycle_mode)
    button_plus.attachClick(increment_digit)
    button_plus.attachLongPressStop(increment_digit)
    button_minus.attachClick(decrement_digit)
    button_minus.attachLongPressStop(decrement_digit)
    button_next_digit.attachClick(cycle_field)
    button_next_digit.attachLongPressStop(cycle_page)

    while True:
        await clockclock.run()

        for button in buttons:
            button.tick()



time.sleep(6) #wait so clock modules have time to setup

clockclock_settings = ClockSettings()

clockclock = ClockClock24(clockclock_settings)

asyncio.run(main_loop())
