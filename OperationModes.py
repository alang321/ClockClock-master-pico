from DigitDisplay import DigitDisplay
import random

mode_ids = {
    "night mode": 0,
    "visual": 1,  # every timechange has choreographies and stuff
    "shortest path": 2,  # move to new position with shortest path
    "stealth": 3,
    "analog": 4,  # every clock is a normal clock
    "sleep": 5,  # move all steppers to 6 o clock (default) position and disable stepper drivers
    "settings": 6,
    }

def get_mode_list(clockclock):
    return [NightDay(clockclock), Visual(clockclock), ShortestPath(clockclock), Stealth(clockclock), Analog(clockclock), Sleep(clockclock), Settings(clockclock)]

class Stealth:
    id = mode_ids["stealth"]

    def __init__(self, clockclock):
        self.clockclock = clockclock
        self.steppers = clockclock.steppers
        self.stepper_speed = self.clockclock.settings.stepper_speed_stealth
        self.stepper_accel = self.clockclock.settings.stepper_accel_stealth
        
    def start(self):
        self.clockclock.alarm_flag = True # so a new time is displayed instead of the mode number even before next minute
        
    def end(self):
        return
    
    def new_time(self, hour, minute):
        self.clockclock.cancel_tasks() # tasks cancelled since previous display could still be running if started

        # Set speed and accel every minute, the clock used to crash every 2 weeks, i suspect this was due to corrupted i2c messages.
        # The validity checking and checksum should prevent this, but they lead to missed messages (very very rarely)
        # in the case of a missed message on the mode change, one module would be stuck in the previous speed and accel
        # adding these statements makes this be the case for at most 1 minute, while adding a bit of overhead
        # but there is a lot of spare capacity on the i2c bus.
        # Usually set acceleration is relatively expensive due to a sqrt, but if the acceleration is already set
        # it is not update by the driver, so this is not a problem.
        self.clockclock.set_speed_all(self.stepper_speed)
        self.clockclock.set_accel_all(self.stepper_accel)

        digits = [hour//10, hour%10, minute//10, minute%10]
        self.clockclock.digit_display.display_digits(digits, DigitDisplay.animations["stealth"])
    
    def button_click(self, button_id):
        return

class ShortestPath:
    id = mode_ids["shortest path"]

    def __init__(self, clockclock):
        self.clockclock = clockclock
        self.steppers = clockclock.steppers
        self.stepper_speed = self.clockclock.settings.stepper_speed_default
        self.stepper_accel = self.clockclock.settings.stepper_accel_default

    def start(self):
        self.clockclock.alarm_flag = True

    def end(self):
        return
    
    def new_time(self, hour, minute):
        self.clockclock.cancel_tasks()

        # see explanation in stealth function
        self.clockclock.set_speed_all(self.stepper_speed)
        self.clockclock.set_accel_all(self.stepper_accel)
        
        digits = [hour//10, hour%10, minute//10, minute%10]
        self.clockclock.digit_display.display_digits(digits, DigitDisplay.animations["shortest path"])
        
    def button_click(self, button_id):
        return

class Visual:
    id = mode_ids["visual"]

    def __init__(self, clockclock):
        self.clockclock = clockclock
        self.steppers = clockclock.steppers
        self.stepper_speed = self.clockclock.settings.stepper_speed_default
        self.stepper_accel = self.clockclock.settings.stepper_accel_default
        self.animation_id_lst = self.clockclock.settings.visual_animation_ids
               
        self.random_shuffle(self.animation_id_lst)
        self.animation_index = 0

    def start(self):
        self.clockclock.alarm_flag = True

    def end(self):
        return
    
    def new_time(self, hour, minute):
        self.clockclock.cancel_tasks()

        # see explanation in stealth function
        self.clockclock.set_speed_all(self.stepper_speed)
        self.clockclock.set_accel_all(self.stepper_accel)
        
        digits = [hour//10, hour%10, minute//10, minute%10]
        if __debug__:
            print("animation id:", self.animation_id_lst[self.animation_index],", current queue:", self.animation_id_lst)
            
        self.clockclock.digit_display.display_digits(digits, self.animation_id_lst[self.animation_index])
        
        self.animation_index += 1
        
        if self.animation_index == len(self.animation_id_lst):
            self.animation_index = 0
            self.random_shuffle(self.animation_id_lst)
            
    def button_click(self, button_id):
        return

    def random_shuffle(seq):
        l = len(seq)
        for i in range(l):
            j = random.randrange(l)
            seq[i], seq[j] = seq[j], seq[i]

class Analog:
    id = mode_ids["analog"]

    def __init__(self, clockclock):
        self.clockclock = clockclock
        self.steppers = clockclock.steppers
        self.stepper_speed = self.clockclock.settings.stepper_speed_analog
        self.stepper_accel = self.clockclock.settings.stepper_accel_analog

    def start(self):
        self.clockclock.alarm_flag = True

    def end(self):
        return
    
    def new_time(self, hour, minute):
        self.clockclock.cancel_tasks()

        # see explanation in stealth function
        self.clockclock.set_speed_all(self.stepper_speed)
        self.clockclock.set_accel_all(self.stepper_accel)
        
        self.steppers.move_to_all(int(self.clockclock.steps_full_rev/60 * minute))
        self.steppers.move_to_all(int(self.clockclock.steps_full_rev/12 * (hour%12 + minute/60)))
        
    def button_click(self, button_id):
        return

class Sleep:
    id = mode_ids["sleep"]

    def __init__(self, clockclock):
        self.clockclock = clockclock
        self.steppers = clockclock.steppers
        self.stepper_speed = self.clockclock.settings.stepper_speed_default
        self.stepper_accel = self.clockclock.settings.stepper_accel_default

    def start(self):
        self.clockclock.alarm_flag = True

    def end(self):
        return
    
    def new_time(self, hour, minute):
        self.clockclock.cancel_tasks()

        # see explanation in stealth function
        self.clockclock.set_speed_all(self.stepper_speed)
        self.clockclock.set_accel_all(self.stepper_accel)
        
        self.steppers.move_to_all(int(0.5*self.clockclock.steps_full_rev))
        
    def button_click(self, button_id):
        return
    
class NightDay:
    id = mode_ids["night mode"]

    def __init__(self, clockclock, night_mode, day_mode):
        self.clockclock = clockclock
        self.steppers = clockclock.steppers

        self.night_mode = night_mode
        self.day_mode = day_mode
        
        #check that its not of type nightmode or daymode 
        if isinstance(self.night_mode, NightDay):
            raise Exception("night mode can not be of type NightDay")
        if isinstance(self.day_mode, NightDay):
            raise Exception("day mode can not be of type NightDay")

        self.current_mode = None

    def start(self):
        self.clockclock.alarm_flag = True
        self.current_mode = None

    def end(self):
        if self.current_mode != None:
            self.current_mode.end()

    def new_time(self, hour, minute):
        if isinstance(self.night_mode, NightDay):
            raise Exception("night mode can not be of type NightDay")
        if isinstance(self.day_mode, NightDay):
            raise Exception("day mode can not be of type NightDay")

        self.clockclock.cancel_tasks()

        hour_24, minute_24 = self.clockclock.rtc.get_hour_minute(False) 

        night_start = self.persistent.get_var("night start")
        night_end = self.persistent.get_var("night end")
        start_time_min = night_start[0] * 60 + night_start[1]
        end_time_min = night_end[0] * 60 + night_end[1]
        curr_time_min = hour_24 * 60 + minute_24

        if start_time_min < end_time_min:
            is_night = (start_time_min <= curr_time_min <= end_time_min)
        else:
            is_night = (start_time_min <= curr_time_min or curr_time_min <= end_time_min)

        if is_night:
            if not isinstance(self.current_mode, self.night_mode):
                self.end()
                self.current_mode = self.night_mode
                self.current_mode.start()
        else:
            if not isinstance(self.current_mode, self.day_mode):
                self.end()
                self.current_mode = self.day_mode
                self.current_mode.start()

        if self.current_mode != None:
            self.current_mode.new_time(hour, minute)

    def button_click(self, button_id):
        if self.current_mode != None:
            self.current_mode.button_click(button_id)

class Settings:
    id = mode_ids["settings"]
    
    def __init__(self, clockclock):
        self.clockclock = clockclock
        self.steppers = clockclock.steppers
        self.stepper_speed = self.clockclock.settings.stepper_speed_fast
        self.stepper_accel = self.clockclock.settings.stepper_accel_fast

    def start(self):
            if __debug__:
                print("starting settings mode")
            self.stop_ntp()
            
            self.clockclock.set_speed_all(self.stepper_speed)
            self.clockclock.set_accel_all(self.stepper_accel)




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

    
 
    def __settings_new_time(self, hour: int, minute: int):
        self.cancel_tasks()

        # see explanation in stealth function
        self.set_speed_all(ClockClock24.stepper_speed_default)
        self.set_accel_all(ClockClock24.stepper_accel_default)

        if self.__settings_do_display_new_time[self.__settings_current_page]:
            self.__settings_update_display()


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


#how to handle button presses?
#button event functions in ClockClock24 class
#this calss can attach to them somehow?