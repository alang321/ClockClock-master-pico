import time
from ClockClock24 import ClockClock24
import uasyncio as asyncio
from lib.OneButton import OneButton
from ClockSettings import ClockSettings

# button handlers
def btn_mode(pin):
    global clockclock
    clockclock.button_handler(ClockClock24.button_id["next_mode"])
        
def btn_plus(pin):
    global clockclock
    clockclock.button_handler(ClockClock24.button_id["plus"])
        
def btn_minus(pin):
    global clockclock
    clockclock.button_handler(ClockClock24.button_id["minus"])
    
def btn_next(pin):
    global clockclock
    clockclock.button_handler(ClockClock24.button_id["next_digit"])
            
def btn_next_long(pin):
    global clockclock
    clockclock.button_handler(ClockClock24.button_id["next_page"])

#main loop
async def main_loop():
    button_mode = OneButton(19, True, enable_long_press=False, enable_double_click=False)
    button_plus = OneButton(21, True, enable_long_press=False, enable_double_click=False)
    button_minus = OneButton(18, True, enable_long_press=False, enable_double_click=False)
    button_next_digit = OneButton(20, True, enable_long_press=True, enable_double_click=False)
    buttons = [button_mode, button_plus, button_minus, button_next_digit]

    button_mode.attachClick(btn_mode)
    button_plus.attachClick(btn_plus)
    button_minus.attachClick(btn_minus)
    button_next_digit.attachClick(btn_next)
    button_next_digit.attachLongPressStop(btn_next_long)

    while True:
        await clockclock.run()

        for button in buttons:
            button.tick()



time.sleep(6) #wait so clock modules have time to setup

clockclock_settings = ClockSettings()

clockclock = ClockClock24(clockclock_settings)

asyncio.run(main_loop())
