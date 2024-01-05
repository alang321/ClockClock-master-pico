from ClockDigitDisplay import ClockDigitDisplay
import uasyncio as asyncio

class Settings:
    allowed_as_startup_mode = True
    allowed_as_night_day_mode = False
    
    def __init__(self, clockclock):
        self.clockclock = clockclock
        self.steppers = clockclock.steppers
        self.stepper_speed = self.clockclock.settings.stepper_speed_fast
        self.stepper_accel = self.clockclock.settings.stepper_accel_fast

        self.displaying_page_change = False # turned on during settings page change

        self.__persistent_data_changed_flag = False # flag set to true when persistent data is changed

        self.async_setting_page_change_task = None
        
        self.__reset_settings_flag = False

        self.__is_started = False

        self.settings_pages = []
        self.__current_page_idx = 0 
        self.__current_page = None

    def start(self):
        if __debug__:
            print("starting settings mode")
        self.clockclock.stop_ntp()
        
        self.clockclock.set_speed_all(self.stepper_speed)
        self.clockclock.set_accel_all(self.stepper_accel)

        self.__persistent_data_changed_flag = False
        self.input_lock = False

        self.__is_started = True

        self.settings_set_page(0)

    def end(self):
        if self.__is_started:
            self.__is_started = False

            self.cancel_setting_page_task()
            
            if self.clockclock.ntp_module != None:
                self.clockclock.ntp_module.stop_hotspot()
                self.clockclock.start_ntp()
                
            if self.__persistent_data_changed_flag:
                self.__persistent_data_changed_flag = False

                self.clockclock.settings.persistent.write_flash()

    def new_time(self, hour, minute):
        if not self.dont_display_time:
            if self.__current_page != None:
                self.__current_page.new_time(hour, minute)
        
    def button_click(self, button_id: int, long_press=False, double_press=False):
        if button_id == self.clockclock.button_id["next_page"]:
            self.change_page(1)
        elif button_id == self.clockclock.button_id["prev_page"]:
            self.change_page(-1)
        else:
            if not self.displaying_page_change:
                if self.__current_page != None:
                    self.__current_page.button_handler(button_id, long_press, double_press)
    
#region setting page management
    
    def cancel_setting_page_task(self):
        if self.async_setting_page_change_task != None: 
            self.async_setting_page_change_task.cancel()

    def __cancel_tasks(self):
        self.cancel_setting_page_task()
        self.__cancel_tasks()

    def change_page(self, direction):
        self.set_page((self.__current_page + direction) % len(self.settings_pages))
  
    def set_page(self, idx):
        self.__cancel_tasks()
        self.async_setting_page_change_task = asyncio.create_task(self.__set_page(idx))

    async def __set_page(self, idx):
        self.__current_page_idx = idx
        if __debug__:
            print("settings set page:", self.__current_page)

        #page number animation
        self.displaying_page_change = True

        if self.__current_page != None:
            self.__current_page.end()

        self.clockclock.digit_display.display_mode(self.__current_page, True)
        self.clockclock.movement_done_event.clear() # wait until movement is completed
        await self.clockclock.movement_done_event.wait()
        await asyncio.sleep(.8) #so digit is visible for a bit

        self.displaying_page_change = True

        self.__current_page = self.settings_pages[self.__current_page_idx]
        self.__current_page.start()  

#endregion
                
    def reset_settings(self):
        self.__persistent_data_changed_flag = False
        self.clockclock.reset_persistent_settings()

class SettingsPageNumberStyle:
    def __init__(self, clockclock):
        self.clockclock = clockclock
        self.steppers = clockclock.steppers
        self.stepper_speed = self.clockclock.settings.stepper_speed_fast
        self.stepper_accel = self.clockclock.settings.stepper_accel_fast
     
    def start(self):
        return
     
    def end(self):
        return
     
    def update_display():
        return
    
    def new_time(self, hour, minute):
         return
     
    def button_handler(self, button_id: int, long_press=False, double_press=False):
        return


class SettingsPageTimeSetting:
      

class SettingsPageTimeRTC:
        

class SettingsPageOperationMode:
        
class SettingsPageEnableDisable:
        
class SettingsPageReset:



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



#region settings



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
        self.digit_display.display_digits(digits, ClockDigitDisplay.animations["shortest path"])
        
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

    
    
#endregion


#how to handle button presses?
#button event functions in ClockClock24 class
#this calss can attach to them somehow?