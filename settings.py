from PersistentStorage import PersistentStorage

nightmode_allowed_modes = [ClockClock24.modes["visual"],
                           ClockClock24.modes["shortest path"],
                           ClockClock24.modes["stealth"],
                           ClockClock24.modes["analog"],
                           ClockClock24.modes["sleep"]]

defaultmode_allowed_modes = [ClockClock24.modes["night mode"],
                             ClockClock24.modes["visual"],
                             ClockClock24.modes["shortest path"],
                             ClockClock24.modes["stealth"],
                             ClockClock24.modes["analog"],
                             ClockClock24.modes["sleep"]]

var_lst = [PersistentStorage.persistent_var("night start", [21, 0], lambda a : (0 <= a[0] <= 23 and 0 <= a[1] <= 59)), 
           PersistentStorage.persistent_var("night end", [9, 30], lambda a : (0 <= a[0] <= 23 and 0 <= a[1] <= 59)),
           PersistentStorage.persistent_var("night mode", ClockClock24.modes["stealth"], lambda a : True if a in nightmode_allowed_modes else False),
           PersistentStorage.persistent_var("day mode", ClockClock24.modes["visual"], lambda a : True if a in nightmode_allowed_modes else False),
           PersistentStorage.persistent_var("one style", 0, lambda a : True if a in [0, 1] else False),
           PersistentStorage.persistent_var("eight style", 0, lambda a : True if a in [0, 1, 2] else False),
           PersistentStorage.persistent_var("default mode", ClockClock24.modes["night mode"], lambda a : True if a in defaultmode_allowed_modes else False),
           PersistentStorage.persistent_var("twelve hour", 0, lambda a : True if a in [0, 1] else False)] # 0 for 24 hour format, 1 for twelve hour formaty

persistent = PersistentStorage("settings", var_lst)


def settings_next_page(self):
    if not self.input_lock:
        self.cancel_tasks()
        self.async_setting_page_task = asyncio.create_task(self.__settings_set_page((self.__settings_current_page + 1) % self.__settings_pagecount))

async def __settings_set_page(self, pagenum):
    self.__settings_current_page = pagenum
    if __debug__:
        print("settings set page:", self.__settings_current_page)

    #page number animation
    self.input_lock_2 = True
    self.time_handler = self.__no_new_time # an empty time handler so a new time doesnt interrupt the displaying of the current mode
    self.digit_display.display_mode(self.__settings_current_page, True)
    self.movement_done_event.clear() # wait until movement is completed
    await self.movement_done_event.wait()
    await asyncio.sleep(1) #so digit is visible for a bit
    self.time_handler = self.time_change_handlers[self.__current_mode]
    self.input_lock_2 = False
    
    self.__settings_current_digit = 3
    self.__settings_update_display()

def settings_next_digit(self):
    if not self.input_lock and not self.input_lock_2:
        if self.__settings_current_page == 0 or self.__settings_current_page == 1 or self.__settings_current_page == 2:
            self.__settings_current_digit = (self.__settings_current_digit - 1) % 4
            if __debug__:
                print("settings next digit:", self.__settings_current_digit)

            distance = int(self.steps_full_rev * 0.045)
            for clk_index in self.digit_display.digit_display_indices[self.__settings_current_digit]:
                self.hour_steppers[clk_index].wiggle(distance, 1)
                self.minute_steppers[clk_index].wiggle(distance, 1)

def settings_incr_decr(self, direction):
    if not self.input_lock and not self.input_lock_2:
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
                print("new night mode:", night_mode),
        elif self.__settings_current_page == 5: # set mode at startup
            index = self.__defaultmode_allowed_modes.index(self.persistent.get_var("default mode"))
            default_mode = self.__defaultmode_allowed_modes[(index + direction) % len(self.__defaultmode_allowed_modes)]
            
            self.persistent.set_var("default mode", default_mode)
            
            if __debug__:
                print("new default mode:", default_mode)
        elif self.__settings_current_page == 6: # set one display mode
            new_style = (self.persistent.get_var("one style") + direction) % 2
            
            self.persistent.set_var("one style", new_style)
            
            self.digit_display.number_style_options[1] = new_style
            
            if __debug__:
                print("new one style:", new_style)
        elif self.__settings_current_page == 7: # set eight display mode
            new_style = (self.persistent.get_var("eight style") + direction) % 3
            
            self.persistent.set_var("eight style", new_style)
            
            self.digit_display.number_style_options[8] = new_style
            
            if __debug__:
                print("new eight style:", new_style)
        
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



class SettingsPage:
    
  def __init__(self, clockclock, persistent_storage input_locked=True):
    self.firstname = fname
    self.lastname = lname
    
    self.__input_locked = input_locked
    
  def page_constructor(self):
      
  def page_destructor(self):

  def button_up(self):
    print(self.firstname, self.lastname)

  def button_down(self):
    print(self.firstname, self.lastname)

  def next_digit(self):
    print(self.firstname, self.lastname)
    
  def new_time(self):
      return
    
  def lock_input(self, lock):
    self.__input_locked = locke