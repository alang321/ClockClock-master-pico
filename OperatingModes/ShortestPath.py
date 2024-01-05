from ClockDigitDisplay import ClockDigitDisplay

class ShortestPath:
    allowed_as_startup_mode = True
    allowed_as_night_day_mode = True

    def __init__(self, clockclock):
        self.clockclock = clockclock
        self.steppers = clockclock.steppers
        self.stepper_speed = self.clockclock.settings.persistent.get_var("Speed Visual")
        self.stepper_accel = self.clockclock.settings.persistent.get_var("Accel Visual")

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
        self.clockclock.digit_display.display_digits(digits, ClockDigitDisplay.animations["shortest path"])
        
    def button_click(self, button_id: int, long_press=False, double_press=False):
        return