import random
from ClockStepperModule import ClockStepper
from ClockStepperModule import ClockModule
from DigitDisplay import DigitDisplay
from DS3231_timekeeper import DS3231_timekeeper
import uasyncio as asyncio
import os
import json

class ClockClock24:
    #fast speed used when showing mode numbers and similar
    stepper_speed_fast = 700
    stepper_accel_fast = 450
    
    #normal speed used in most modes
    stepper_speed_default = 585
    stepper_accel_default = 200
    
    #used in stealth mode
    stepper_speed_stealth = 150
    stepper_accel_stealth = 50
    
    #used in analog mode
    stepper_speed_analog = 70
    stepper_accel_analog = 50
    
    modes = {
      "visual": 0,  # every timechange has choreographies and stuff
      "shortest path": 1,  # move to new position with shortest path
      "stealth": 2,
      "analog": 3,  # every clock is a normal clock
      "sleep": 4,  # move all steppers to 6 o clock (default) position and disable stepper drivers
      "night mode": 5,
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
                                     DigitDisplay.animations["field lines"],
                                     DigitDisplay.animations["equipotential"],
                                     DigitDisplay.animations["speedy clock"],
                                     DigitDisplay.animations["random"],
                                     DigitDisplay.animations["handoff"]]
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

        self.mode_change_handlers = [self.__visual, self.__shortest_path, self.__stealth, self.__analog, self.__sleep, self.__night_mode, self.__settings]
        self.time_change_handlers = [self.__visual_new_time,
                                     self.__shortest_path_new_time,
                                     self.__stealth_new_time,
                                     self.__analog_new_time,
                                     self.__no_new_time,
                                     self.__no_new_time,
                                     self.__settings_new_time]
        self.time_handler = None
        self.current_speed = -1
        self.current_accel = -1

        self.input_lock = False # gets turned on during a mode change being display
        
        #night mode config
        self.settings_pages = {
            "change time": 0,
            "night start": 1,
            "night end": 2,
            "day mode": 3,
            "night mode": 4
        }
        self.__settings_current_page = 0
        self.__settings_current_digit = 3
        self.__settings_display_funcs = [self.__settings_change_time_disp, self.__settings_night_start_disp, self.__settings_night_end_disp, self.__settings_mode_day_disp, self.__settings_mode_night_disp]
        self.__settings_do_display_new_time = [True, False, False, False, False]
        self.__settings_pagecount = len(self.__settings_display_funcs)
        self.__nightmode_allowed_modes = [0, 1, 2, 3, 4]
        self.__persistent_data_changed = False

        #night mode
        self.default_night_start = [21, 0]
        self.default_night_end = [8, 0]
        self.default_night_mode = 0
        self.default_day_mode = 1
        self.night_config_file = "night_config.txt"
        self.night_start = self.default_night_start
        self.night_end = self.default_night_end
        self.night_mode = self.default_night_mode
        self.day_mode = self.default_day_mode
        self.__persistent_read_storage()

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

    def display_digit(self, field: int, number: int, direction=0, extra_revs=0):
        self.cancel_tasks()
        self.digit_display.display_digit(field, number, direction, extra_revs)
    
    def display_time(self, hour: int, minute: int):
        if __debug__:
            print("New time displayed:", hour, minute)
        
        if self.night_on:
            start_time_min = self.night_start[0] * 60 + self.night_start[1]
            end_time_min = self.night_end[0] * 60 + self.night_end[1]
            curr_time_min = hour * 60 + minute
            
            is_night = False
            if start_time_min < end_time_min:
                is_night = (start_time_min <= curr_time_min <= end_time_min)
            else:
                is_night = (start_time_min <= curr_time_min or curr_time_min <= end_time_min)
            
            if is_night:
                if __debug__:
                    print("its night")
                if self.__current_mode_night != self.night_mode:
                    self.mode_change_handlers[self.day_mode](False)
                    self.__current_mode_night = self.night_mode
                    self.mode_change_handlers[self.night_mode](True)
            else:
                if __debug__:
                    print("its day")
                if self.__current_mode_night != self.day_mode:
                    self.mode_change_handlers[self.night_mode](False)
                    self.__current_mode_night = self.day_mode
                    self.mode_change_handlers[self.day_mode](True)
                   
        self.time_handler(hour, minute)
        
    def swap(self, index: int):
        minute_pos = self.minute_steppers[index].current_target_pos
        hour_pos = self.hour_steppers[index].current_target_pos
        
        if minute_pos == -1 or hour_pos == -1:
            return
        
        self.minute_steppers[index].move_to(hour_pos, 0)
        self.hour_steppers[index].move_to(minute_pos, 0)

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

        hour, minute = rtc.get_hour_minute()
        self.display_time(hour, time)

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
            self.__persistent_data_changed = False
            self.__settings_update_display()
        else:
            if self.__persistent_data_changed:
                self.__persistent_data_changed = False

                self.__persistent_write_storage()

    def __sleep(self, start):
        if start:
            self.time_handler = self.time_change_handlers[self.__current_mode]
            self.set_speed_all(ClockClock24.stepper_speed_default)
            self.set_accel_all(ClockClock24.stepper_accel_default)
        
            self.move_to_all(int(0.5*self.steps_full_rev))

#endregion

#region  new time handlers

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
            print("animation id:", self.visual_animation_ids[self.animation_index])
            
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
        if self.__settings_do_display_new_time[self.__settings_current_page]  == self.settings_pages["change time"]:
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
                    print("settings next digit:", self.__settigns_current_digit)

                distance = int(self.steps_full_rev * 0.075)
                for clk_index in self.digit_display.digit_display_indices[self.__settings_current_digit]:
                    self.hour_steppers[clk_index].wiggle(distance, 1)
                    self.minute_steppers[clk_index].wiggle(distance, 1)

    def settings_incr_decr(self, direction):
        if not self.input_lock:
            if __debug__:
                print("settings incr", direction)
                
            self.__persistent_data_changed = True

            if self.__settings_current_page == 0:
                time_change_val = [[10, 0], [1, 0], [0, 10], [0, 1]]
                rtc.add_to_hour_minute(time_change_val[current_field][0] * direction, time_change_val[current_field][1] * direction)
                time = self.__settings_incr_decr_time(self.night_start[0], self.night_start[1],
                                                      time_change_val[self.__settings_current_digit][0] * direction,
                                                      time_change_val[self.__settings_current_digit][1] * direction)

                self.rtc.set_hour_minute(time[0], time[1])

                if __debug__:
                    print("changed time:", hour, minute)
            elif self.__settings_current_page == 1:
                time_change_val = [[10, 0], [1, 0], [0, 10], [0, 1]]
                self.night_start = self.__settings_incr_decr_time(self.night_start[0], self.night_start[1], time_change_val[self.__settings_current_digit][0] * direction, time_change_val[self.__settings_current_digit][1] * direction)
                
                if __debug__:
                    print("new start time:", self.night_start)
            elif self.__settings_current_page == 2:
                time_change_val = [[10, 0], [1, 0], [0, 10], [0, 1]]
                self.night_end = self.__settings_incr_decr_time(self.night_end[0], self.night_end[1], time_change_val[self.__settings_current_digit][0] * direction, time_change_val[self.__settings_current_digit][1] * direction)
                
                if __debug__:
                    print("new end time:", self.night_end)
            elif self.__settings_current_page == 3:
                index = self.__nightmode_allowed_modes.index(self.day_mode)
                self.day_mode = self.__nightmode_allowed_modes[(index + direction) % len(self.__nightmode_allowed_modes)]
                
                if __debug__:
                    print("new day mode:", self.day_mode)
            else:
                index = self.__nightmode_allowed_modes.index(self.night_mode)
                self.night_mode = self.__nightmode_allowed_modes[(index + direction) % len(self.__nightmode_allowed_modes)]
                
                if __debug__:
                    print("new night mode:", self.night_mode)

            self.__settings_update_display()

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

    def __settings_update_display(self):
        self.__settings_display_funcs[self.__settings_current_page]()

    def __settings_change_time_disp(self):
        hour, minute = self.rtc.get_hour_minute()
        self.__settings_display_time(hour, minute)

    def __settings_night_start_disp(self):
        self.__settings_display_time(self.night_end[0], self.night_end[1])

    def __settings_night_end_disp(self):
        self.__settings_display_time(self.night_end[0], self.night_end[1])

    def __settings_mode_day_disp(self):
        self.digit_display.display_mode(self.day_mode)

    def __settings_mode_night_disp(self):
        self.digit_display.display_mode(self.night_mode)

    def __settings_display_time(self, hour, minute):
        self.cancel_display_tasks()
        digits = [hour // 10, hour % 10, minute // 10, minute % 10]
        self.digit_display.display_digits(digits, DigitDisplay.animations["shortest path"])

    def __persistent_read_storage(self):
        try:
            f = open(self.night_config_file, "r")
            string = f.readline()
            self.night_start, self.night_end, self.night_mode, self.day_mode = json.loads(string)
            f.close()

            if not 0 <= self.night_start[0] <= 23:
                raise ValueError("Bad stored data")
            if not 0 <= self.night_start[1] <= 59:
                raise ValueError("Bad stored data")
            if not 0 <= self.night_end[0] <= 23:
                raise ValueError("Bad stored data")
            if not 0 <= self.night_end[1] <= 59:
                raise ValueError("Bad stored data")
            if self.night_mode not in self.__nightmode_allowed_modes:
                raise ValueError("Bad stored data")
            if self.day_mode not in self.__nightmode_allowed_modes:
                raise ValueError("Bad stored data")
        except Exception as e:
            if __debug__:
                print(str(e))
            self.night_start = self.default_night_start
            self.night_end = self.default_night_end
            self.night_mode = self.default_night_mode
            self.day_mode = self.default_day_mode

            self.__persistent_write_storage()

    def __persistent_write_storage(self):
        data_str = json.dumps((self.night_start, self.night_end, self.night_mode, self.day_mode), separators=None)
        f = open(self.night_config_file, "w")
        f.write(data_str)
        f.close()
        return

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
    
    def move_all(self, distance: int, direction: int):
        for module in self.clock_modules:
            module.move_module(distance, direction)
        
    def stop_all(self):
        for module in self.clock_modules:
            module.stop_module()

    def falling_pointer(self): 
        for module in self.clock_modules:
            module.falling_pointer_module()

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
    
