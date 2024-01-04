from DigitDisplay import DigitDisplay

class ShortestPath:
    allowed_as_startup_mode = True
    allowed_as_night_day_mode = True

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