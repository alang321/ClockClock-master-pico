from ClockStepper import ClockStepper

class DigitDisplay:
    # fractional position of the pointer, first sublist is hour hand second is minute hand, 0.0 at the 12 o clock position and 0.5 at 6 o clock
    # from top left, rows first
    digits_pointer_pos_frac =  [[[0.5, 0.5, 0.5, 0.5, 0.25, 0.75],   [0.25, 0.75, 0, 0, 0, 0]],             # 0
                               [[0.625, 0.625, 0.125, 0, 0.625, 0],  [0.625, 0.5, 0.125, 0.5, 0.625, 0]],   # 1
                               [[0.25, 0.75, 0.5, 0.75, 0.25, 0.75], [0.25, 0.5, 0.25, 0, 0, 0.75]],        # 2
                               [[0.25, 0.75, 0.25, 0, 0.25, 0.75],   [0.25, 0.5, 0.25, 0.75, 0.25, 0]],     # 3
                               [[0.5, 0.5, 0, 0, 0.625, 0],          [0.5, 0.5, 0.25, 0.5, 0.625, 0]],      # 4
                               [[0.25, 0.75, 0, 0.5, 0.25, 0],       [0.5, 0.75, 0.25, 0.75, 0.25, 0.75]],  # 5
                               [[0.5, 0.75, 0, 0.75, 0, 0],          [0.25, 0.75, 0.5, 0.5, 0.25, 0.75]],   # 6
                               [[0.25, 0.5, 0.625, 0.5, 0.625, 0],   [0.25, 0.75, 0.625, 0, 0.625, 0]],     # 7
                               [[0.5, 0.5, 0, 0, 0, 0],              [0.25, 0.75, 0.25, 0.75, 0.25, 0.75]], # 8
                               [[0.5, 0.5, 0.25, 0.5, 0.25, 0],      [0.25, 0.75, 0, 0, 0.25, 0.75]]];      # 9
    
    digits_pointer_pos_abs = []
        
    def __init__(self, stepper_list_minute, stepper_list_hour, steps_full_rev = 4320):
        self.stepper_list_hour = stepper_list_hour
        self.stepper_list_minute = stepper_list_minute
        
        if not DigitDisplay.digits_pointer_pos_abs:
            DigitDisplay.digits_pointer_pos_abs = [[[int(frac * steps_full_rev) for frac in hour_minute] for hour_minute in number] for number in DigitDisplay.digits_pointer_pos_frac]  

    def display(self, number: int):
        for clk_index in range(len(self.stepper_list_hour)):
            self.stepper_list_hour[clk_index].move_to(DigitDisplay.digits_pointer_pos_abs[number][0][clk_index], 0)
            self.stepper_list_minute[clk_index].move_to(DigitDisplay.digits_pointer_pos_abs[number][1][clk_index], 0)
    