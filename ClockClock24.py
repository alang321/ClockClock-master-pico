import random
from ClockStepperModule import ClockStepper
from ClockStepperModule import ClockModule
from DigitDisplay import DigitDisplay
from DS3231_timekeeper import DS3231_timekeeper
import uasyncio as asyncio
import os
import json

#fast speed used when showing mode numbers and similar
stepper_speed_fast = 700
stepper_accel_fast = 450

#normal speed used in most modes
stepper_speed_default = 585
stepper_accel_default = 210

#used in stealth mode
stepper_speed_stealth = 125
stepper_accel_stealth = 60

#used in analog mode
stepper_speed_analog = 30
stepper_accel_analog = 20

modes = {
  "night mode": 0,
  "visual": 1,  # every timechange has choreographies and stuff
  "shortest path": 2,  # move to new position with shortest path
  "stealth": 3,
  "analog": 4,  # every clock is a normal clock
  "sleep": 5,  # move all steppers to 6 o clock (default) position and disable stepper drivers
  "settings": 6,
  }

def __init__(self, slave_adr_list, i2c_bus_list, clk_i2c_bus, clk_interrupt_pin, steps_full_rev=4320):
    # persistent data

    
    self.alarm_flag = False
    self.rtc = DS3231_timekeeper(self.new_minute_handler, clk_interrupt_pin, clk_i2c_bus)

    self.steps_full_rev = steps_full_rev
    
    self.visual_animation_ids = [DigitDisplay.animations["extra revs"], #these get shuffled randomly when ever at end of list
                                 DigitDisplay.animations["straight wave"],
                                 DigitDisplay.animations["opposing pointers"],
                                 DigitDisplay.animations["focus"],
                                 DigitDisplay.animations["opposites"],
                                 DigitDisplay.animations["equipotential"],
                                 DigitDisplay.animations["speedy clock"],
                                 DigitDisplay.animations["random"],
                                 DigitDisplay.animations["opposing wave"],
                                 DigitDisplay.animations["circle"],
                                 DigitDisplay.animations["smaller bigger"],
                                 DigitDisplay.animations["small circles"],
                                 #DigitDisplay.animations["uhrenspiel"]
                                 ]
    self.random_shuffle(self.visual_animation_ids)
    self.animation_index = 0

    #asyncio
    self.async_display_task = None  # currently running asynchronous tasks that have to be cancelled
    self.async_mode_change_task = None
    self.async_setting_page_task = None
    self.movement_done_event = asyncio.Event()
    
    self.digit_display = DigitDisplay(self, [0, self.persistent.get_var("one style"), 0, 0, 0, 0, 0, 0, self.persistent.get_var("eight style"), 0])

    self.mode_change_handlers = [self.__night_mode, self.__visual, self.__shortest_path, self.__stealth, self.__analog, self.__sleep, self.__settings]
    self.time_change_handlers = [self.__night_mode_new_time,
                                 self.__visual_new_time,
                                 self.__shortest_path_new_time,
                                 self.__stealth_new_time,
                                 self.__analog_new_time,
                                 self.__no_new_time,
                                 self.__settings_new_time]
    self.time_handler = None
    self.current_speed = -1
    self.current_accel = -1

    #settings
    self.input_lock = False # gets turned on during a mode change being display, so settings button cant be pressed when effect is not yet visible
    self.input_lock_2 = False # gets turned on during a page change being displayed, so settings button cant be pressed when effect not visible, but page can still be changed
    
    self.settings_pages = {
        "change time": 0,
        "24/12": 1,
        "default mode": 2,
        "night end": 3,
        "night start": 4,
        "day mode": 5,
        "night mode": 6,
        "one style": 7,
        "eight style": 8,
        "reset": 9
    }
    self.__settings_current_page = 0
    self.__settings_current_digit = 3
    self.__settings_display_funcs = [self.__settings_change_time_disp,
                                     self.__settings_time_format_disp,
                                     self.__settings_mode_default_disp,
                                     self.__settings_night_end_disp,
                                     self.__settings_night_start_disp,
                                     self.__settings_mode_day_disp,
                                     self.__settings_mode_night_disp,
                                     self.__settings_one_style_disp,
                                     self.__settings_eight_style_disp,
                                     self.__settings_reset]
    
    self.__settings_display_funcs = [self.__settings_change_time_disp,
                                     self.__settings_time_format,
                                     self.__settings_mode_default_disp,
                                     self.__settings_night_end_disp,
                                     self.__settings_night_start_disp,
                                     self.__settings_mode_day_disp,
                                     self.__settings_mode_night_disp,
                                     self.__settings_one_style_disp,
                                     self.__settings_eight_style_disp,
                                     self.__settings_reset_disp]
    
    self.__settings_do_display_new_time = [True, False, False, False, False, False, False, False, False, False]
    self.__settings_pagecount = len(self.__settings_display_funcs)
    self.__persistent_data_changed = False
    
    # night mode
    self.__current_mode_night = -1
    self.night_on = False
    
    self.__current_mode = None
    self.set_mode(self.persistent.get_var("default mode"))

async def run(self):
    if not self.movement_done_event.is_set():
        if not self.is_running():
            self.movement_done_event.set()

    if self.alarm_flag:
        self.alarm_flag = False
        hour, minute = self.rtc.get_hour_minute(bool(self.persistent.get_var("twelve hour")))
        self.display_time(hour, minute)

    await asyncio.sleep(0)

def new_minute_handler(self):
    if __debug__:
        print("Interrupt received")
    self.alarm_flag = True

def display_time(self, hour: int, minute: int):
    if __debug__:
        print("New time displayed:", hour, minute)
        print('Twelve hour format:', bool(self.persistent.get_var("twelve hour")))

    self.time_handler(hour, minute)

def cancel_tasks(self):
    if self.async_display_task != None:
        self.async_display_task.cancel()
    if self.async_mode_change_task != None:
        self.async_mode_change_task.cancel()
    if self.async_setting_page_task != None: 
        self.async_setting_page_task.cancel()

def cancel_display_tasks(self):
    if self.async_display_task != None:
        self.async_display_task.cancel()
        
#region mode change

def set_mode(self, mode: int):
    self.cancel_tasks()
    self.async_mode_change_task = asyncio.create_task(self.__set_mode(mode))

async def __set_mode(self, mode: int):
    if __debug__:
        print("New mode:", mode)

    self.input_lock = True
    if self.__current_mode != None:
        self.mode_change_handlers[self.__current_mode](False) #"destructor" of the old mode
    self.__current_mode = mode
    self.time_handler = self.__no_new_time # an empty time handler so a new time doesnt interrupt the displaying of the current mode
    
    self.enable_disable_driver(True)
    self.set_speed_all(ClockClock24.stepper_speed_fast)
    self.set_accel_all(ClockClock24.stepper_accel_fast)
    self.digit_display.display_mode(mode)
    
    self.movement_done_event.clear()
    await self.movement_done_event.wait()
    
    await asyncio.sleep(2) #so digit is visible for a few seconds
    
    self.input_lock = False
    self.mode_change_handlers[self.__current_mode](True) # specific initialisation of new mode after display of mode digit is done

def get_mode(self):
    return self.__current_mode

def __stealth(self, start):
    if start:
        self.set_speed_all(ClockClock24.stepper_speed_stealth)
        self.set_accel_all(ClockClock24.stepper_accel_stealth)
        self.time_handler = self.time_change_handlers[ClockClock24.modes["stealth"]]
        self.alarm_flag = True # so a new time is displayed instead of the mode number even before next minute

def __shortest_path(self, start):
    if start:
        self.set_speed_all(ClockClock24.stepper_speed_default)
        self.set_accel_all(ClockClock24.stepper_accel_default)
        self.time_handler = self.time_change_handlers[ClockClock24.modes["shortest path"]]
        self.alarm_flag = True # so a new time is displayed instead of the mode number even before next minute

def __visual(self, start):
    if start:
        self.set_speed_all(ClockClock24.stepper_speed_default)
        self.set_accel_all(ClockClock24.stepper_accel_default)
        self.time_handler = self.time_change_handlers[ClockClock24.modes["visual"]]
        self.alarm_flag = True # so a new time is displayed instead of the mode number even before next minute

def __analog(self, start):
    if start:
        self.set_speed_all(ClockClock24.stepper_speed_analog)
        self.set_accel_all(ClockClock24.stepper_accel_analog)
        self.time_handler = self.time_change_handlers[ClockClock24.modes["analog"]]
        self.alarm_flag = True # so a new time is displayed instead of the mode number even before next minute

def __night_mode(self, start):
    if start:
        self.time_handler = self.time_change_handlers[ClockClock24.modes["night mode"]]
        self.__current_mode_night = -1
        self.alarm_flag = True # so a new time is displayed instead of the mode number even before next minute

def __settings(self, start):
    if start:
        if __debug__:
            print("starting settings mode")
        self.set_speed_all(ClockClock24.stepper_speed_fast)
        self.set_accel_all(ClockClock24.stepper_accel_fast)
        self.time_handler = self.time_change_handlers[ClockClock24.modes["settings"]]
        
        self.__persistent_data_changed = False
        self.async_setting_page_task = asyncio.create_task(self.__settings_set_page(0))
    else:
        if __debug__:
            print("ending settings mode")
        if self.__persistent_data_changed:
            self.__persistent_data_changed = False

            self.persistent.write_flash()

def __sleep(self, start):
    if start:
        self.set_speed_all(ClockClock24.stepper_speed_default)
        self.set_accel_all(ClockClock24.stepper_accel_default)
        self.time_handler = self.time_change_handlers[self.__current_mode]
    
        self.move_to_all(int(0.5*self.steps_full_rev))

#endregion

#region  new time handlers

def __night_mode_new_time(self, hour: int, minute: int):
    night_start = self.persistent.get_var("night start")
    night_end = self.persistent.get_var("night end")
    night_mode = self.persistent.get_var("night mode")
    day_mode = self.persistent.get_var("day mode")
    
    start_time_min = night_start[0] * 60 + night_start[1]
    end_time_min = night_end[0] * 60 + night_end[1]
    curr_time_min = hour * 60 + minute

    if start_time_min < end_time_min:
        is_night = (start_time_min <= curr_time_min <= end_time_min)
    else:
        is_night = (start_time_min <= curr_time_min or curr_time_min <= end_time_min)

    if is_night:
        if __debug__:
            print("its night")
        if self.__current_mode_night != night_mode:
            self.mode_change_handlers[day_mode](False)
            self.__current_mode_night = night_mode
            self.mode_change_handlers[night_mode](True)
            self.time_handler = self.time_change_handlers[ClockClock24.modes["night mode"]]

        self.time_change_handlers[night_mode](hour, minute)
    else:
        if __debug__:
            print("its day")
        if self.__current_mode_night != day_mode:
            self.mode_change_handlers[night_mode](False)
            self.__current_mode_night = day_mode
            self.mode_change_handlers[day_mode](True)
            self.time_handler = self.time_change_handlers[ClockClock24.modes["night mode"]]

        self.time_change_handlers[day_mode](hour, minute)

def __stealth_new_time(self, hour: int, minute: int):
    self.cancel_tasks() # tasks cancelled since previous display could still be running if started
    digits = [hour//10, hour%10, minute//10, minute%10]
    self.digit_display.display_digits(digits, DigitDisplay.animations["stealth"])
    
def __shortest_path_new_time(self, hour: int, minute: int):
    self.cancel_tasks()
    digits = [hour//10, hour%10, minute//10, minute%10]
    self.digit_display.display_digits(digits, DigitDisplay.animations["shortest path"])
    
def __visual_new_time(self, hour: int, minute: int):
    self.cancel_tasks()
    digits = [hour//10, hour%10, minute//10, minute%10]
    
    if __debug__:
        print("animation id:", self.visual_animation_ids[self.animation_index],", current queue:", self.visual_animation_ids)
        
    self.digit_display.display_digits(digits, self.visual_animation_ids[self.animation_index])
    
    self.animation_index += 1
    
    if self.animation_index == len(self.visual_animation_ids):
        self.animation_index = 0
        self.random_shuffle(self.visual_animation_ids)     

def __analog_new_time(self, hour: int, minute: int):
    self.cancel_tasks()
    for stepper in self.minute_steppers:
        stepper.move_to(int(self.steps_full_rev/60 * minute), 0)
        
    for stepper in self.hour_steppers:
        stepper.move_to(int(self.steps_full_rev/12 * (hour%12 + minute/60)), 0)

def __settings_new_time(self, hour: int, minute: int):
    self.cancel_tasks()
    if self.__settings_do_display_new_time[self.__settings_current_page]:
        self.__settings_update_display()
    
def __no_new_time(self, hour: int, minute: int):
    # here tasks are not cancelled since this could be called during set mode
    if __debug__:
        print("New time not displayed")
    return

#endregion


def random_shuffle(seq):
    l = len(seq)
    for i in range(l):
        j = random.randrange(l)
        seq[i], seq[j] = seq[j], seq[i]

