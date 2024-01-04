class Analog:
    allowed_as_startup_mode = True
    allowed_as_night_day_mode = True

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
        
    def button_click(self, button_id: int, long_press=False, double_press=False):
        return