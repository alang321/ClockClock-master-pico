class NightDay:
    allowed_as_startup_mode = True
    allowed_as_night_day_mode = False

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
            self.current_mode = None

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

    def button_click(self, button_id: int, long_press=False, double_press=False):
        if self.current_mode != None:
            self.current_mode.button_click(button_id)