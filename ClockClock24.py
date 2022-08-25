import random
from ClockStepperModule import ClockStepper
from ClockStepperModule import ClockModule
from DigitDisplay import DigitDisplay
from DS3231_timekeeper import DS3231_timekeeper
from PersistentStorage import PersistentStorage
import uasyncio as asyncio
import os
import json

class ClockClock24:
    #fast speed used when showing mode numbers and similar
    stepper_speed_fast = 700
    stepper_accel_fast = 450
    
    #normal speed used in most modes
    stepper_speed_default = 585
    stepper_accel_default = 210
    
    #used in stealth mode
    stepper_speed_stealth = 135
    stepper_accel_stealth = 45
    
    #used in analog mode
    stepper_speed_analog = 70
    stepper_accel_analog = 50
    
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
                                     DigitDisplay.animations["small circles"]]
        self.random_shuffle(self.visual_animation_ids)
        self.animation_index = 0

        #asyncio
        self.async_display_task = None  # currently running asynchronous task that has to be cancelled
        self.async_mode_change_task = None  # currently running asynchronous task that has to be cancelled
        self.movement_done_event = asyncio.Event()
        
        self.clock_modules = [ClockModule(i2c_bus_list[module_index], slave_adr_list[module_index], steps_full_rev) for module_index in range(len(slave_adr_list))]
        
        self.minute_steppers = [stepper for stepper_list in (module.minute_steppers for module in self.clock_modules) for stepper in stepper_list]
        self.hour_steppers = [stepper for stepper_list in (module.hour_steppers for module in self.clock_modules) for stepper in stepper_list]
        
        self.digit_display = DigitDisplay(self)

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

        self.input_lock = False # gets turned on during a mode change being display
        
        #settings
        self.settings_pages = {
            "change time": 0,
            "night start": 1,
            "night end": 2,
            "day mode": 3,
            "night mode": 4,
            "one style": 5
        }
        self.__settings_current_page = 0
        self.__settings_current_digit = 3
        self.__settings_display_funcs = [self.__settings_change_time_disp, self.__settings_night_start_disp, self.__settings_night_end_disp, self.__settings_mode_day_disp, self.__settings_mode_night_disp, self.__settings_one_style_disp]
        self.__settings_do_display_new_time = [True, False, False, False, False, False]
        self.__settings_pagecount = len(self.__settings_display_funcs)
        self.__nightmode_allowed_modes = [ClockClock24.modes["visual"],
                                          ClockClock24.modes["shortest path"],
                                          ClockClock24.modes["stealth"],
                                          ClockClock24.modes["analog"],
                                          ClockClock24.modes["sleep"]]
        self.__persistent_data_changed = False
        
        # settings
        var_lst = [PersistentStorage.persistent_var("night start", [21, 0], lambda a : (0 <= a[0] <= 23 and 0 <= a[1] <= 59)), # todo fix
                   PersistentStorage.persistent_var("night end", [8, 0], lambda a : (0 <= a[0] <= 23 and 0 <= a[1] <= 59)),
                   PersistentStorage.persistent_var("night mode", ClockClock24.modes["stealth"], lambda a : True if a in self.__nightmode_allowed_modes else False),
                   PersistentStorage.persistent_var("day mode", ClockClock24.modes["visual"], lambda a : True if a in self.__nightmode_allowed_modes else False),
                   PersistentStorage.persistent_var("one style", 0, lambda a : True if a in [0, 1] else False)]
        
        self.persistent = PersistentStorage("settings", var_lst)
        
        # night mode
        self.__current_mode_night = -1
        self.night_on = False

        self.__current_mode = 0
        self.mode_change_handlers[self.__current_mode](True)  #start with mode

        hour, minute = self.rtc.get_hour_minute()
        self.display_time(hour, minute)

    async def run(self):
        if not self.movement_done_event.is_set():
            if not self.is_running():
                self.movement_done_event.set()

        if self.alarm_flag:
            self.alarm_flag = False
            hour, minute = self.rtc.get_hour_minute()
            self.display_time(hour, minute)

        await asyncio.sleep(0)

    def new_minute_handler(self):
        if __debug__:
            print("Interrupt received")
        self.alarm_flag = True

    def display_time(self, hour: int, minute: int):
        if __debug__:
            print("New time displayed:", hour, minute)

        self.time_handler(hour, minute)

    def cancel_tasks(self):
        if self.async_display_task != None:
            self.async_display_task.cancel()
        if self.async_mode_change_task != None:
            self.async_mode_change_task.cancel()
            
    def cancel_display_tasks(self):
        if self.async_display_task != None:
            self.async_display_task.cancel()
            
    def cancel_mode_tasks(self):
        if self.async_mode_change_task != None:
            self.async_mode_change_task.cancel()

#region mode change

    async def set_mode(self, mode: int):
        self.cancel_tasks()
        self.async_mode_change_task = asyncio.create_task(self.__set_mode(mode))

    async def __set_mode(self, mode: int):
        if __debug__:
            print("New mode:", mode)

        self.input_lock = True
        self.mode_change_handlers[self.__current_mode](False) #"destructor" of the old mode
        self.__current_mode = mode
        self.time_handler = self.__no_new_time # an empty time handler so a new time doesnt interrupt the displaying of the current mode
        
        self.enable_disable_driver(True)
        self.set_speed_all(ClockClock24.stepper_speed_fast)
        self.set_accel_all(ClockClock24.stepper_accel_fast)
        self.digit_display.display_mode(mode)
        
        self.movement_done_event.clear()
        await self.movement_done_event.wait()
        
        await asyncio.sleep(2) #so digit is displayed for atleast a few seconds
        
        self.mode_change_handlers[self.__current_mode](True) # specific initialisation of new mode after display of mode digit is done
        self.input_lock = False

        hour, minute = self.rtc.get_hour_minute()
        self.display_time(hour, minute)

    def get_mode(self):
        return self.__current_mode
    
    def __stealth(self, start):
        if start:
            self.time_handler = self.time_change_handlers[ClockClock24.modes["stealth"]]
            self.set_speed_all(ClockClock24.stepper_speed_stealth)
            self.set_accel_all(ClockClock24.stepper_accel_stealth)
    
    def __shortest_path(self, start):
        if start:
            self.time_handler = self.time_change_handlers[ClockClock24.modes["shortest path"]]
            self.set_speed_all(ClockClock24.stepper_speed_default)
            self.set_accel_all(ClockClock24.stepper_accel_default)
    
    def __visual(self, start):
        if start:
            self.time_handler = self.time_change_handlers[ClockClock24.modes["visual"]]
            self.set_speed_all(ClockClock24.stepper_speed_default)
            self.set_accel_all(ClockClock24.stepper_accel_default)
    
    def __analog(self, start):
        if start:
            self.time_handler = self.time_change_handlers[ClockClock24.modes["analog"]]
            self.set_speed_all(ClockClock24.stepper_speed_analog)
            self.set_accel_all(ClockClock24.stepper_accel_analog)
    
    def __night_mode(self, start):
        if start:
            self.time_handler = self.time_change_handlers[ClockClock24.modes["night mode"]]
            self.night_on = True
            self.__current_mode_night = -1
        else:
            self.night_on = False
    
    def __settings(self, start):
        if start:
            self.time_handler = self.time_change_handlers[ClockClock24.modes["settings"]]
            self.set_speed_all(ClockClock24.stepper_speed_fast)
            self.set_accel_all(ClockClock24.stepper_accel_fast)
            self.__settings_current_page = 0
            self.__settings_current_digit = 3
            self.__persistent_data_changed = False
            self.__settings_update_display()
        else:
            if self.__persistent_data_changed:
                self.__persistent_data_changed = False

                self.persistent.write_flash()

    def __sleep(self, start):
        if start:
            self.time_handler = self.time_change_handlers[self.__current_mode]
            self.set_speed_all(ClockClock24.stepper_speed_default)
            self.set_accel_all(ClockClock24.stepper_accel_default)
        
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
        self.cancel_display_tasks()
        digits = [hour//10, hour%10, minute//10, minute%10]
        self.digit_display.display_digits(digits, DigitDisplay.animations["stealth"])
        
    def __shortest_path_new_time(self, hour: int, minute: int):
        self.cancel_display_tasks()
        digits = [hour//10, hour%10, minute//10, minute%10]
        self.digit_display.display_digits(digits, DigitDisplay.animations["shortest path"])
        
    def __visual_new_time(self, hour: int, minute: int):
        self.cancel_display_tasks()
        digits = [hour//10, hour%10, minute//10, minute%10]
        
        if __debug__:
            print("animation id:", self.visual_animation_ids[self.animation_index],", current queue:", self.visual_animation_ids)
            
        self.digit_display.display_digits(digits, self.visual_animation_ids[self.animation_index])
        
        self.animation_index += 1
        
        if self.animation_index == len(self.visual_animation_ids):
            self.animation_index = 0
            self.random_shuffle(self.visual_animation_ids)     
    
    def __analog_new_time(self, hour: int, minute: int):
        self.cancel_display_tasks()
        for stepper in self.minute_steppers:
            stepper.move_to(int(self.steps_full_rev/60 * minute), 0)
            
        for stepper in self.hour_steppers:
            stepper.move_to(int(self.steps_full_rev/12 * (hour%12 + minute/60)), 0)
    
    def __settings_new_time(self, hour: int, minute: int):
        if self.__settings_do_display_new_time[self.__settings_current_page]:
            self.__settings_update_display()
        
    def __no_new_time(self, hour: int, minute: int):
        if __debug__:
            print("New time not displayed")
        return

#endregion

#region settings

    def settings_next_page(self):
        if not self.input_lock:
            self.__settings_current_page = (self.__settings_current_page + 1) % self.__settings_pagecount
            if __debug__:
                print("settings next page:", self.__settings_current_page)

            self.__settings_current_digit = 3
            self.__settings_display_funcs[self.__settings_current_page]()
            self.__settings_update_display()

    def settings_next_digit(self):
        if not self.input_lock:
            if self.__settings_current_page == 0 or self.__settings_current_page == 1 or self.__settings_current_page == 2:
                self.__settings_current_digit = (self.__settings_current_digit - 1) % 4
                if __debug__:
                    print("settings next digit:", self.__settings_current_digit)

                distance = int(self.steps_full_rev * 0.045)
                for clk_index in self.digit_display.digit_display_indices[self.__settings_current_digit]:
                    self.hour_steppers[clk_index].wiggle(distance, 1)
                    self.minute_steppers[clk_index].wiggle(distance, 1)

    def settings_incr_decr(self, direction):
        if not self.input_lock:
            if __debug__:
                print("settings time increment direction ", direction)
                
            self.__persistent_data_changed = True

            if self.__settings_current_page == 0: # change time page
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
            elif self.__settings_current_page == 1: # change night start time page
                time_change_val = [[10, 0], [1, 0], [0, 10], [0, 1]]
                night_start = self.persistent.get_var("night start")
                night_start_new = self.__settings_incr_decr_time(night_start[0], night_start[1],
                                                             time_change_val[self.__settings_current_digit][0] * direction,
                                                             time_change_val[self.__settings_current_digit][1] * direction)
                
                self.persistent.set_var("night start", night_start_new)
                
                if __debug__:
                    print("new start time:", night_start_new)
            elif self.__settings_current_page == 2: # change night end time page
                time_change_val = [[10, 0], [1, 0], [0, 10], [0, 1]]
                night_end = self.persistent.get_var("night end")
                night_end_new = self.__settings_incr_decr_time(night_end[0], night_end[1],
                                                                time_change_val[self.__settings_current_digit][0] * direction,
                                                                time_change_val[self.__settings_current_digit][1] * direction)
                
                self.persistent.set_var("night end", night_end_new)
                
                if __debug__:
                    print("new end time:", night_end_new)
            elif self.__settings_current_page == 3: # set mode during day
                index = self.__nightmode_allowed_modes.index(self.persistent.get_var("day mode"))
                day_mode = self.__nightmode_allowed_modes[(index + direction) % len(self.__nightmode_allowed_modes)]
                
                self.persistent.set_var("day mode", day_mode)
                
                if __debug__:
                    print("new day mode:", day_mode)
            elif self.__settings_current_page == 4: # set mode during night
                index = self.__nightmode_allowed_modes.index(self.persistent.get_var("night mode"))
                night_mode = self.__nightmode_allowed_modes[(index + direction) % len(self.__nightmode_allowed_modes)]
                
                self.persistent.set_var("night mode", night_mode)
                
                if __debug__:
                    print("new night mode:", night_mode)
            elif self.__settings_current_page == 5: # set one display mode
                new_style = (self.persistent.get_var("one style") + 1) % 2
                
                self.persistent.set_var("one style", new_style)
                
                if __debug__:
                    print("new one style:", new_style)
            
            self.__settings_update_display()

    def __settings_update_display(self):
        self.__settings_display_funcs[self.__settings_current_page]()

    def __settings_change_time_disp(self):
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
        
    def __settings_one_style_disp(self):
        self.digit_display.display_mode(0)

    def __settings_display_time(self, hour, minute):
        self.cancel_display_tasks()
        digits = [hour // 10, hour % 10, minute // 10, minute % 10]
        self.digit_display.display_digits(digits, DigitDisplay.animations["shortest path"])

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

#endregion

#region commands

    def enable_disable_driver(self, enable_disable: bool):
        """
        true to enable driver of module
        false to disable
        """
        for module in self.clock_modules:
            module.enable_disable_driver_module(enable_disable)
    
    def set_speed_all(self, speed: int):
        self.current_speed = speed
        for module in self.clock_modules:
            module.set_speed_module(speed)
    
    def set_accel_all(self, accel: int):
        self.current_accel = accel
        for module in self.clock_modules:
            module.set_accel_module(accel)
    
    def move_to_all(self, position: int, direction = 0):
        for module in self.clock_modules:
            module.move_to_module(position, direction)
    
    def move_to_extra_revs_all(self, position: int, direction: int, extra_revs: int):
        for module in self.clock_modules:
            module.move_to_extra_revs_module(position, direction, extra_revs)

    def moveTo_min_steps_all(self): 
        for module in self.clock_modules:
            module.move_to_min_steps_module()
    
    def move_all(self, distance: int, direction: int):
        for module in self.clock_modules:
            module.move_module(distance, direction)
        
    def stop_all(self):
        for module in self.clock_modules:
            module.stop_module()

    def is_running(self) -> bool: #returns True if stepper is running
        for module in self.clock_modules:
            if module.is_running_module():
                return True
        
        return False

#endregion
    
    @staticmethod
    def random_shuffle(seq):
        l = len(seq)
        for i in range(l):
            j = random.randrange(l)
            seq[i], seq[j] = seq[j], seq[i]
    
