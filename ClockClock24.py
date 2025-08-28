import random
from ClockStepperModule import ClockStepper
from ClockStepperModule import ClockModule
from DigitDisplay import DigitDisplay
from DS3231_timekeeper import DS3231_timekeeper
from PersistentStorage import PersistentStorage
import uasyncio as asyncio
import os
import json
from machine import Timer

class ClockClock24:
    #be carefull that these dont exceed the maxximum speed set in the driver, if so the commands will be ignored
    #fast speed used when showing mode numbers and similar
    stepper_speed_fast = 700
    stepper_accel_fast = 450
    
    #normal speed used in most modes
    stepper_speed_default = 585
    stepper_accel_default = 210
    
    #used in stealth mode
    stepper_speed_stealth = 105
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
    
    def __init__(self, slave_adr_list, i2c_bus_list, clk_i2c_bus, clk_interrupt_pin, ntp_module=None, steps_full_rev=4320, ntp_poll_freq_m=60):
        # persistent data
        self.__nightmode_allowed_modes = [ClockClock24.modes["visual"],
                                          ClockClock24.modes["shortest path"],
                                          ClockClock24.modes["stealth"],
                                          ClockClock24.modes["analog"],
                                          ClockClock24.modes["sleep"]]
        
        self.__defaultmode_allowed_modes = [ClockClock24.modes["night mode"],
                                            ClockClock24.modes["visual"],
                                            ClockClock24.modes["shortest path"],
                                            ClockClock24.modes["stealth"],
                                            ClockClock24.modes["analog"],
                                            ClockClock24.modes["sleep"]]
        
        var_lst = [PersistentStorage.persistent_var("night start", [21, 0], lambda a : (0 <= a[0] <= 23 and 0 <= a[1] <= 59)), # todo fix
                   PersistentStorage.persistent_var("night end", [9, 30], lambda a : (0 <= a[0] <= 23 and 0 <= a[1] <= 59)),
                   PersistentStorage.persistent_var("night mode", ClockClock24.modes["stealth"], lambda a : True if a in self.__nightmode_allowed_modes else False),
                   PersistentStorage.persistent_var("day mode", ClockClock24.modes["visual"], lambda a : True if a in self.__nightmode_allowed_modes else False),
                   PersistentStorage.persistent_var("one style", 0, lambda a : True if a in [0, 1] else False),
                   PersistentStorage.persistent_var("eight style", 0, lambda a : True if a in [0, 1, 2] else False),
                   PersistentStorage.persistent_var("default mode", ClockClock24.modes["night mode"], lambda a : True if a in self.__defaultmode_allowed_modes else False),
                   PersistentStorage.persistent_var("12 hour format", 0, lambda a : True if a in [0, 1] else False),
                   PersistentStorage.persistent_var("NTP enabled", 0, lambda a : True if a in [0, 1] else False)] # 0 for 24 hour format, 1 for twelve hour formaty
        
        self.persistent = PersistentStorage("settings", var_lst)
        
        self.alarm_flag = False
        self.rtc = DS3231_timekeeper(self.new_minute_handler, clk_interrupt_pin, clk_i2c_bus)

        self.steps_full_rev = steps_full_rev
        
        self.visual_animation_ids = [DigitDisplay.animations["extra revs"], #these get shuffled randomly when ever end of list is reached
                                     DigitDisplay.animations["straight wave"],
                                     DigitDisplay.animations["opposing pointers"],
                                     DigitDisplay.animations["focus"],
                                     DigitDisplay.animations["opposites"],
                                     #DigitDisplay.animations["equipotential"],
                                     DigitDisplay.animations["speedy clock"],
                                     DigitDisplay.animations["random"],
                                     DigitDisplay.animations["opposing wave"],
                                     DigitDisplay.animations["circle"],
                                     DigitDisplay.animations["smaller bigger"],
                                     DigitDisplay.animations["small circles"],
                                     DigitDisplay.animations["hamiltonian"],
                                     #DigitDisplay.animations["game of life"],
                                     #DigitDisplay.animations["uhrenspiel"],
                                     DigitDisplay.animations["collision"],
                                     DigitDisplay.animations["checkerboard"]
                                     ]
        self.random_shuffle(self.visual_animation_ids)
        self.animation_index = 0
        
        self.ntp_module = ntp_module
        self.ntp_poll_freq_m = ntp_poll_freq_m #how often ntp is polled, should be more than the timeout
        self.ntp_timeout_s = 180 #for how long the ntp mopdule tries to retrieve the ntp
        self.ntp_validity_s = self.ntp_timeout_s #for how long the ntp stays valid in the ntp module after receving a ntp time
        self.async_ntp_task = None
        self.ntp_timer = Timer()
        self.timer_running = False #wether or not timer is aalready running
        
        self.start_ntp()

        #asyncio
        self.async_display_task = None  # currently running asynchronous tasks that have to be cancelled
        self.async_mode_change_task = None
        self.async_setting_page_task = None
        self.movement_done_event = asyncio.Event()
        
        self.clock_modules = [ClockModule(i2c_bus_list[module_index], slave_adr_list[module_index], steps_full_rev) for module_index in range(len(slave_adr_list))]
        
        self.minute_steppers = [stepper for stepper_list in (module.minute_steppers for module in self.clock_modules) for stepper in stepper_list]
        self.hour_steppers = [stepper for stepper_list in (module.hour_steppers for module in self.clock_modules) for stepper in stepper_list]
        
        self.digit_display = DigitDisplay(self, [0, self.persistent.get_var("one style"), 0, 0, 0, 0, 0, 0, self.persistent.get_var("eight style"), 0])

        self.mode_change_handlers = [self.__night_mode, self.__visual, self.__shortest_path, self.__stealth, self.__analog, self.__sleep, self.__settings]
        self.time_change_handlers = [self.__night_mode_new_time,
                                     self.__visual_new_time,
                                     self.__shortest_path_new_time,
                                     self.__stealth_new_time,
                                     self.__analog_new_time,
                                     self.__sleep_new_time,
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
            "ntp": 2,
            "default mode": 3,
            "night end": 4,
            "night start": 5,
            "day mode": 6,
            "night mode": 7,
            "one style": 8,
            "eight style": 9,
            "reset": 10
        }
        
        self.__settings_current_page = 0
        self.__settings_current_digit = 3
        self.__settings_display_funcs = [self.__settings_time_disp,
                                         self.__settings_time_format_disp,
                                         self.__settings_ntp_disp,
                                         self.__settings_mode_default_disp,
                                         self.__settings_night_end_disp,
                                         self.__settings_night_start_disp,
                                         self.__settings_mode_day_disp,
                                         self.__settings_mode_night_disp,
                                         self.__settings_one_style_disp,
                                         self.__settings_eight_style_disp,
                                         self.__settings_reset_disp]
        
        self.__settings_modify_val_funcs   = [self.__settings_time_mod,
                                             self.__settings_time_format_mod,
                                             self.__settings_ntp_mod,
                                             self.__settings_mode_default_mod,
                                             self.__settings_night_end_mod,
                                             self.__settings_night_start_mod,
                                             self.__settings_mode_day_mod,
                                             self.__settings_mode_night_mod,
                                             self.__settings_one_style_mod,
                                             self.__settings_eight_style_mod,
                                             self.__settings_reset_mod]
        
        self.__settings_do_display_new_time = [True, False, False, False, False, False, False, False, False, False, False]
        self.__settings_pagecount = len(self.__settings_display_funcs)
        self.__persistent_data_changed = False
        
        self.__reset_settings = False
        
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
            self.send_heartbeat() # send heartbeat to all modules, so they know that the clock is still running at least once per minute

            self.alarm_flag = False
            hour, minute = self.rtc.get_hour_minute(bool(self.persistent.get_var("12 hour format")))
            self.display_time(hour, minute)

        await asyncio.sleep(0)

    def new_minute_handler(self):
        if __debug__:
            print("Interrupt received")
        self.alarm_flag = True

    def display_time(self, hour: int, minute: int):
        if __debug__:
            print("New time displayed:", hour, minute)
            print('Twelve hour format:', bool(self.persistent.get_var("12 hour format")))

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
        
        await asyncio.sleep(1.2) #so digit is visible for a few seconds
        
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
            self.stop_ntp()
                
            self.set_speed_all(ClockClock24.stepper_speed_fast)
            self.set_accel_all(ClockClock24.stepper_accel_fast)
            self.time_handler = self.time_change_handlers[ClockClock24.modes["settings"]]
            
            self.__persistent_data_changed = False
            self.async_setting_page_task = asyncio.create_task(self.__settings_set_page(0))
        else:
            if __debug__:
                print("ending settings mode")
                
            if self.ntp_module != None:
                self.ntp_module.stop_hotspot()
            self.start_ntp()
                
            if self.__reset_settings:
                self.reset_settings()
                
            if self.__persistent_data_changed:
                self.__persistent_data_changed = False

                self.persistent.write_flash()

    def __sleep(self, start):
        if start:
            self.set_speed_all(ClockClock24.stepper_speed_default)
            self.set_accel_all(ClockClock24.stepper_accel_default)
            self.time_handler = self.time_change_handlers[self.__current_mode]

            self.alarm_flag = True # so a new time is displayed instead of the mode number even before next minute

#endregion

#region  new time handlers

    def __night_mode_new_time(self, hour: int, minute: int):
        night_start = self.persistent.get_var("night start")
        night_end = self.persistent.get_var("night end")
        night_mode = self.persistent.get_var("night mode")
        day_mode = self.persistent.get_var("day mode")
        
        #ugly but im lazy, so day/night determination works
        hour_24, minute_24 = self.rtc.get_hour_minute(False) 
        
        start_time_min = night_start[0] * 60 + night_start[1]
        end_time_min = night_end[0] * 60 + night_end[1]
        curr_time_min = hour_24 * 60 + minute_24

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

        # Set speed and accel every minute, the clock used to crash every 2 weeks, i suspect this was due to corrupted i2c messages.
        # The validity checking and checksum should prevent this, but they lead to missed messages (very very rarely)
        # in the case of a missed message on the mode change, one module would be stuck in the previous speed and accel
        # adding these statements makes this be the case for at most 1 minute, while adding a bit of overhead
        # but there is a lot of spare capacity on the i2c bus.
        # Usually set acceleration is relatively expensive due to a sqrt, but if the acceleration is already set
        # it is not update by the driver, so this is not a problem.
        self.set_speed_all(ClockClock24.stepper_speed_stealth)
        self.set_accel_all(ClockClock24.stepper_accel_stealth)

        digits = [hour//10, hour%10, minute//10, minute%10]
        self.digit_display.display_digits(digits, DigitDisplay.animations["stealth"])
        
    def __shortest_path_new_time(self, hour: int, minute: int):
        self.cancel_tasks()

        # see explanation in stealth function
        self.set_speed_all(ClockClock24.stepper_speed_default)
        self.set_accel_all(ClockClock24.stepper_accel_default)
        
        digits = [hour//10, hour%10, minute//10, minute%10]
        self.digit_display.display_digits(digits, DigitDisplay.animations["shortest path"])
        
    def __visual_new_time(self, hour: int, minute: int):
        self.cancel_tasks()

        # see explanation in stealth function
        self.set_speed_all(ClockClock24.stepper_speed_default)
        self.set_accel_all(ClockClock24.stepper_accel_default)
        
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

        # see explanation in stealth function
        self.set_speed_all(ClockClock24.stepper_speed_analog)
        self.set_accel_all(ClockClock24.stepper_accel_analog)
        
        for stepper in self.minute_steppers:
            stepper.move_to(int(self.steps_full_rev/60 * minute), 0)
            
        for stepper in self.hour_steppers:
            stepper.move_to(int(self.steps_full_rev/12 * (hour%12 + minute/60)), 0)
    
    def __settings_new_time(self, hour: int, minute: int):
        self.cancel_tasks()

        # see explanation in stealth function
        self.set_speed_all(ClockClock24.stepper_speed_default)
        self.set_accel_all(ClockClock24.stepper_accel_default)

        if self.__settings_do_display_new_time[self.__settings_current_page]:
            self.__settings_update_display()

    def __sleep_new_time(self, hour: int, minute: int):
        self.cancel_tasks()

        self.set_speed_all(ClockClock24.stepper_speed_default)
        self.set_accel_all(ClockClock24.stepper_accel_default)
    
        self.move_to_all(int(0.5*self.steps_full_rev))
        return

    def __no_new_time(self, hour: int, minute: int):
        # here tasks are not cancelled since this could be called during set mode
        if __debug__:
            print("New time not displayed")

        return

#endregion
    
#region ntp
    
    def stop_ntp(self):
        if self.ntp_module != None:
            self.__stop_ntp_timer()
            
        if self.async_ntp_task != None:
            self.async_ntp_task.cancel()
    
    def start_ntp(self):
        if self.ntp_module != None:
            if self.persistent.get_var("NTP enabled"):
                if not self.timer_running:
                    self.__start_ntp_timer()
                    self.__ntp_callback()
            else:
                if self.timer_running:
                    self.__stop_ntp_timer()
    
    def __start_ntp_timer(self):
        self.timer_running = True
        if __debug__:
            print("Starting NTP Timer")
        self.ntp_timer.init(period=int(self.ntp_poll_freq_m*60*1000), mode=Timer.PERIODIC, callback=self.__ntp_callback)
        
    def __stop_ntp_timer(self):
        self.timer_running = False
        if __debug__:
            print("Stopping NTP Timer")
        self.ntp_timer.deinit()
        
    def __ntp_callback(self, t=0):
        if __debug__:
            print("Polling NTP Time")
        if self.async_ntp_task != None:
            self.async_ntp_task.cancel()
            
        self.async_ntp_task = asyncio.create_task(self.__ntp_get_time())

    async def __ntp_get_time(self):
        time_valid, hour, minute, second = await self.ntp_module.get_ntp_time(self.ntp_timeout_s, self.ntp_validity_s)
        
        if __debug__:
            print("Got NTP Time:", time_valid, hour, minute, second)
        
        if time_valid:
            rtc_hour, rtc_minute = self.rtc.get_hour_minute()
            self.rtc.set_hour_min_sec(hour, minute, second)
            
            if(rtc_hour != hour or rtc_minute != minute): #so time animations are definitely displayed
                if __debug__:
                    print("Forced Display of new time since new ntp time differed")
                self.alarm_flag = True
        
    
#endregion

#region settings

    def settings_change_page(self, direction):
        if not self.input_lock:
            self.cancel_tasks()
            self.async_setting_page_task = asyncio.create_task(self.__settings_set_page((self.__settings_current_page + direction) % self.__settings_pagecount))

    async def __settings_set_page(self, pagenum):
        self.__settings_current_page = pagenum
        if __debug__:
            print("settings set page:", self.__settings_current_page)
            
        if self.__reset_settings:
            self.reset_settings()
        
        
        if self.ntp_module != None:
            if self.__settings_current_page == self.settings_pages["ntp"]:
                self.ntp_module.start_hotspot()
            else:
                self.ntp_module.stop_hotspot()

        #page number animation
        self.input_lock_2 = True
        self.time_handler = self.__no_new_time # an empty time handler so a new time doesnt interrupt the displaying of the current mode
        self.digit_display.display_mode(self.__settings_current_page, True)
        self.movement_done_event.clear() # wait until movement is completed
        await self.movement_done_event.wait()
        await asyncio.sleep(.8) #so digit is visible for a bit
        self.time_handler = self.time_change_handlers[self.__current_mode]
        self.input_lock_2 = False
        
        self.__settings_current_digit = 3
        self.__settings_update_display()

    def settings_next_digit(self):
        if not self.input_lock and not self.input_lock_2:
            if (self.__settings_current_page == self.settings_pages["change time"]
                    or self.__settings_current_page == self.settings_pages["night end"]
                    or self.__settings_current_page == self.settings_pages["night start"]):
                self.__settings_current_digit = (self.__settings_current_digit - 1) % 4
                if __debug__:
                    print("settings next digit:", self.__settings_current_digit)

                distance = int(self.steps_full_rev * 0.025)
                for clk_index in self.digit_display.digit_display_indices[self.__settings_current_digit]:
                    self.hour_steppers[clk_index].wiggle(distance, 1)
                    self.minute_steppers[clk_index].wiggle(distance, 1)
                    
    
    def settings_incr_decr(self, direction):
        if not self.input_lock and not self.input_lock_2:
            if __debug__:
                print("settings time increment direction ", direction)
                
            self.__persistent_data_changed = True
            
            self.__settings_modify_val_funcs[self.__settings_current_page](direction)
            
            self.__settings_update_display()
            
#region per page up down buttons
                    
    def __settings_time_mod(self, direction):
        time_change_val = [[10, 0], [1, 0], [0, 10], [0, 1]]
        curr_hour, curr_min = self.rtc.get_hour_minute()
        time = self.__settings_incr_decr_time(curr_hour, curr_min,
                                              time_change_val[self.__settings_current_digit][0] * direction,
                                              time_change_val[self.__settings_current_digit][1] * direction)

        if __debug__:
            print("incrementing by: hour:", time_change_val[self.__settings_current_digit][0] * direction, "minutes:", time_change_val[self.__settings_current_digit][1] * direction)
            print("old time:", self.rtc.get_hour_minute())
            
        self.rtc.set_hour_minute(time[0], time[1])
        
        if __debug__:
            print("new time:", self.rtc.get_hour_minute())
        
    def __settings_time_format_mod(self, direction):
        new_time_format = (self.persistent.get_var("12 hour format") + direction) % 2
         
        self.persistent.set_var("12 hour format", new_time_format)
        
        if __debug__:
            print("new:  12 hour format = ", bool(new_time_format))
            
    def __settings_ntp_mod(self, direction):
        new_ntp_enabled = (self.persistent.get_var("NTP enabled") + direction) % 2
         
        self.persistent.set_var("NTP enabled", new_ntp_enabled)
        
        if __debug__:
            print("ntp enabled = ", bool(new_ntp_enabled))
        
    def __settings_mode_default_mod(self, direction):
        index = self.__defaultmode_allowed_modes.index(self.persistent.get_var("default mode"))
        default_mode = self.__defaultmode_allowed_modes[(index + direction) % len(self.__defaultmode_allowed_modes)]
        
        self.persistent.set_var("default mode", default_mode)
        
        if __debug__:
            print("new default mode:", default_mode)
        
    def __settings_night_end_mod(self, direction):
        time_change_val = [[10, 0], [1, 0], [0, 10], [0, 1]]
        night_end = self.persistent.get_var("night end")
        night_end_new = self.__settings_incr_decr_time(night_end[0], night_end[1],
                                                        time_change_val[self.__settings_current_digit][0] * direction,
                                                        time_change_val[self.__settings_current_digit][1] * direction)
        
        self.persistent.set_var("night end", night_end_new)
        
        if __debug__:
            print("new day start time:", night_end_new)
        
    def __settings_night_start_mod(self, direction):
        time_change_val = [[10, 0], [1, 0], [0, 10], [0, 1]]
        night_start = self.persistent.get_var("night start")
        night_start_new = self.__settings_incr_decr_time(night_start[0], night_start[1],
                                                     time_change_val[self.__settings_current_digit][0] * direction,
                                                     time_change_val[self.__settings_current_digit][1] * direction)
        
        self.persistent.set_var("night start", night_start_new)
        
        if __debug__:
            print("new night start time:", night_start_new)
        
    def __settings_mode_day_mod(self, direction):
        index = self.__nightmode_allowed_modes.index(self.persistent.get_var("day mode"))
        day_mode = self.__nightmode_allowed_modes[(index + direction) % len(self.__nightmode_allowed_modes)]
        
        self.persistent.set_var("day mode", day_mode)
        
        if __debug__:
            print("new day mode:", day_mode)
        
    def __settings_mode_night_mod(self, direction):
        index = self.__nightmode_allowed_modes.index(self.persistent.get_var("night mode"))
        night_mode = self.__nightmode_allowed_modes[(index + direction) % len(self.__nightmode_allowed_modes)]
        
        self.persistent.set_var("night mode", night_mode)
        
        if __debug__:
            print("new night mode:", night_mode)
        
    def __settings_one_style_mod(self, direction):
        new_style = (self.persistent.get_var("one style") + direction) % 2
                
        self.persistent.set_var("one style", new_style)
        
        self.digit_display.number_style_options[1] = new_style
        
        if __debug__:
            print("new one style:", new_style)
        
    def __settings_eight_style_mod(self, direction):
        new_style = (self.persistent.get_var("eight style") + direction) % 3
                
        self.persistent.set_var("eight style", new_style)
        
        self.digit_display.number_style_options[8] = new_style
        
        if __debug__:
            print("new eight style:", new_style)
        
    def __settings_reset_mod(self, direction):
        if self.__reset_settings:
            if __debug__:
                print("no reset")
            self.__reset_settings = False
        else:
            if __debug__:
                print("reset")
            self.__reset_settings = True
        
#endregion
            
#region settings display

    def __settings_update_display(self):
        # see explanation in stealth function
        self.set_speed_all(ClockClock24.stepper_speed_default)
        self.set_accel_all(ClockClock24.stepper_accel_default)

        self.__settings_display_funcs[self.__settings_current_page]()

    def __settings_time_disp(self):
        hour, minute = self.rtc.get_hour_minute()
        self.__settings_display_time(hour, minute)

    def __settings_night_start_disp(self):
        night_start = self.persistent.get_var("night start")
        self.__settings_display_time(night_start[0], night_start[1])

    def __settings_night_end_disp(self):
        night_end = self.persistent.get_var("night end")
        self.__settings_display_time(night_end[0], night_end[1])

    def __settings_mode_day_disp(self):
        self.digit_display.display_mode(self.persistent.get_var("day mode"))

    def __settings_mode_night_disp(self):
        self.digit_display.display_mode(self.persistent.get_var("night mode"))
        
    def __settings_mode_default_disp(self):
        self.digit_display.display_mode(self.persistent.get_var("default mode"))
        
    def __settings_one_style_disp(self):
        self.digit_display.display_mode(0)
        
    def __settings_eight_style_disp(self):
        self.digit_display.display_mode(7)

    def __settings_display_time(self, hour, minute):
        self.cancel_display_tasks()
        digits = [hour // 10, hour % 10, minute // 10, minute % 10]
        self.digit_display.display_digits(digits, DigitDisplay.animations["shortest path"])
        
    def __settings_time_format_disp(self):
        if bool(self.persistent.get_var("12 hour format")):
            self.digit_display.display_mode(11)
        else:
            self.digit_display.display_mode(23)
        
    def __settings_ntp_disp(self):
        if bool(self.persistent.get_var("NTP enabled")):
            self.digit_display.display_mode(0)
        else:
            self.digit_display.display_mode(-1)
        
    def __settings_reset_disp(self):
        if self.__reset_settings:
            self.move_to_hour(int(self.steps_full_rev * 0.125))
            self.move_to_minute(int(self.steps_full_rev * 0.625))
        else:
            self.move_to_hour(int(self.steps_full_rev * 0.25))
            self.move_to_minute(int(self.steps_full_rev * 0.75))

    def __settings_incr_decr_time(self, hour, minute, h_incr, m_incr):
        # combine times
        combined_hour = hour + h_incr
        combined_minute = minute + m_incr

        if combined_minute >= 0:
            combined_minute = combined_minute % 60
        else:
            # (combined_minute + (-combined_minute%60))//60 -> "floor" towards zero for negative numbers
            combined_minute = combined_minute % -60
            if combined_minute < 0:
                combined_minute = combined_minute + 60

        if combined_hour >= 24:
            combined_hour = 0
        elif combined_hour < 0:
            combined_hour = 23

        return [combined_hour, combined_minute]

    def reset_settings(self): 
        if __debug__:
            print("resetting all settings and time")   
        self.__persistent_data_changed = False
        self.__reset_settings = False
        self.rtc.set_hour_minute(0, 0)
        self.persistent.reset_flash()
        
        if self.ntp_module != None:
            self.ntp_module.reset_data()
        
        self.start_ntp()

        self.digit_display.number_style_options[1] = self.persistent.get_var("one style")
        self.digit_display.number_style_options[8] = self.persistent.get_var("eight style")
        self.alarm_flag = True
    
#endregion
        
#endregion

#region commands

    def enable_disable_driver(self, enable_disable: bool):
        """
        true to enable driver of module
        false to disable
        """
        for module in self.clock_modules:
            module.enable_disable_driver_module(enable_disable)

    def is_running(self) -> bool: #returns True if stepper is running
        for module in self.clock_modules:
            if module.is_running_module():
                return True
        
        return False

    def send_heartbeat(self):
        """
        sends a heartbeat to all modules, so they can reset their watchdogs
        """
        for module in self.clock_modules:
            module.is_running_module()  # this will send a heartbeat to all modules
    
    def set_speed_all(self, speed: int):
        self.current_speed = speed
        for module in self.clock_modules:
            module.all_steppers.set_speed(speed)
    
    def set_accel_all(self, accel: int):
        self.current_accel = accel
        for module in self.clock_modules:
            module.all_steppers.set_accel(accel)
    
    def move_to_all(self, position: int, direction = 0):
        for module in self.clock_modules:
            for stepper in module.steppers:
                stepper.current_target_pos = position
                
            module.all_steppers.move_to(position, direction)
    
    def move_to_extra_revs_all(self, position: int, direction: int, extra_revs: int):
        for module in self.clock_modules:
            for stepper in module.steppers:
                stepper.current_target_pos = position
                
            module.all_steppers.move_to_extra_revs(position, direction, extra_revs)

    def moveTo_min_steps_all(self, position: int, direction: int, min_steps: int): 
        for module in self.clock_modules:
            for stepper in module.steppers:
                stepper.current_target_pos = position
                
            module.all_steppers.move_to_min_steps(position, direction, min_steps)
    
    def move_all(self, distance: int, direction: int):
        for module in self.clock_modules:
            for stepper in module.steppers:
                stepper.current_target_pos = (distance * direction) % module.steps_full_rev
                
            module.all_steppers.move(distance, direction)
        
    def stop_all(self):
        for module in self.clock_modules:
            for stepper in module.steppers:
                stepper.current_target_pos = -1
                
            module.all_steppers.stop()
    
    # control hour steppers
    def set_speed_hour(self, speed: int):
        for module in self.clock_modules:
            module.all_hour_steppers.set_speed(speed)
    
    def set_accel_hour(self, accel: int):
        for module in self.clock_modules:
            module.all_hour_steppers.set_accel(accel)
    
    def move_to_hour(self, position: int, direction = 0):
        for module in self.clock_modules:
            for stepper in module.hour_steppers:
                stepper.current_target_pos = position
                
            module.all_hour_steppers.move_to(position, direction)
    
    def move_to_extra_revs_hour(self, position: int, direction: int, extra_revs: int):
        for module in self.clock_modules:
            for stepper in module.hour_steppers:
                stepper.current_target_pos = position
                
            module.all_hour_steppers.move_to_extra_revs(position, direction, extra_revs)

    def moveTo_min_steps_hour(self, position: int, direction: int, min_steps: int): 
        for module in self.clock_modules:
            for stepper in module.hour_steppers:
                stepper.current_target_pos = position
                
            module.all_hour_steppers.move_to_min_steps(position, direction, min_steps)
    
    def move_hour(self, distance: int, direction: int):
        for module in self.clock_modules:
            for stepper in module.hour_steppers:
                stepper.current_target_pos = (distance * direction) % module.steps_full_rev
                
            module.all_hour_steppers.move(distance, direction)
        
    def stop_hour(self):
        for module in self.clock_modules:
            for stepper in module.hour_steppers:
                stepper.current_target_pos = -1
                
            module.all_hour_steppers.stop()
    
    # control minute steppers
    def set_speed_minute(self, speed: int):
        for module in self.clock_modules:
            module.all_minute_steppers.set_speed(speed)
    
    def set_accel_minute(self, accel: int):
        for module in self.clock_modules:
            module.all_minute_steppers.set_accel(accel)
    
    def move_to_minute(self, position: int, direction = 0):
        for module in self.clock_modules:
            for stepper in module.minute_steppers:
                stepper.current_target_pos = position
                
            module.all_minute_steppers.move_to(position, direction)
    
    def move_to_extra_revs_minute(self, position: int, direction: int, extra_revs: int):
        for module in self.clock_modules:
            for stepper in module.minute_steppers:
                stepper.current_target_pos = position
                
            module.all_minute_steppers.move_to_extra_revs(position, direction, extra_revs)

    def moveTo_min_steps_minute(self, position: int, direction: int, min_steps: int): 
        for module in self.clock_modules:
            for stepper in module.minute_steppers:
                stepper.current_target_pos = position
                
            module.all_minute_steppers.move_to_min_steps(position, direction, min_steps)
    
    def move_minute(self, distance: int, direction: int):
        for module in self.clock_modules:
            for stepper in module.minute_steppers:
                stepper.current_target_pos = (distance * direction) % module.steps_full_rev
                
            module.all_minute_steppers.move(distance, direction)
        
    def stop_minute(self):
        for module in self.clock_modules:
            for stepper in module.minute_steppers:
                stepper.current_target_pos = -1
                
            module.all_minute_steppers.stop()

#endregion
    
    @staticmethod
    def random_shuffle(seq):
        l = len(seq)
        for i in range(l):
            j = random.randrange(l)
            seq[i], seq[j] = seq[j], seq[i]
    
