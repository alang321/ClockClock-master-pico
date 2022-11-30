import machine
import time
from ClockClock24 import ClockClock24
import uasyncio as asyncio
from OneButton import OneButton
from ntpModule import NTPmodule

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

i2c1 = machine.I2C(1, sda=machine.Pin(14), scl=machine.Pin(3), freq=100000)
i2c0 = machine.I2C(0, sda=machine.Pin(16), scl=machine.Pin(17), freq=100000)

# module addresses  (pcb containing 4 steppers and a mcu, stm32f103 in this case)
module_i2c_adr = [12, 13, # the adress of the module starting top left row first
                  14, 15, 
                  16, 17]

module_i2c_bus = [i2c1, i2c0, # the bus on which the module is
                  i2c1, i2c0, 
                  i2c1, i2c0]

time.sleep(6) #wait so clock modules have time to setup

clk_interrupt_pin = 13

ntp = NTPmodule(i2c0, 40)

clockclock = ClockClock24(module_i2c_adr, module_i2c_bus, i2c1, clk_interrupt_pin, ntp, 4320)

asyncio.run(main_loop())
