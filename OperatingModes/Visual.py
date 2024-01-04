import random

class Visual:
    allowed_as_startup_mode = True
    allowed_as_night_day_mode = True

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