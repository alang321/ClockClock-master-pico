from DigitDisplay import DigitDisplay

class Stealth:
    allowed_as_startup_mode = True
    allowed_as_night_day_mode = True

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
    
    def button_click(self, button_id: int, long_press=False, double_press=False):
        return