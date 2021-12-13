from ClockStepper import ClockStepper

class DigitDisplay:
    """
    A class used to display digits given a list of steppers (might be over fragemntation of code idk)

    ...

    Attributes
    ----------
    digit_display_indeces : List[int]
        the clk_ind (0-23) of for each digit, starts at top lef tof digit, row first
    digits_pointer_pos_frac : List[float]
        frational position of each stepper ofr each digit
    digits_pointer_pos_abs : List[int]
        position in steps of each stepper for each digit
    animations : dict
        dictionary that contains names of animation modes and transltes to indices
    minute_steppers : List[ClockStepper]
        list of 24 stepper objs containing minute pointers from top left row first
    hour_steppers : List[ClockStepper]
        list of 24 stepper objs containing hour pointers

    Methods
    -------
    display_digit(field, number, direction, extra_revs = 0)
        Display a one digit on the clock
        
    display_digits(digits, animation = 0)
        Display all digits on the clock with animation
    """
    digit_display_indeces = [[0, 1, 8, 9, 16, 17], [2, 3, 10, 11, 18, 19], [4, 5, 12, 13, 20, 21], [6, 7, 14, 15, 22, 23]]
    
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
    
    animations = {
      "shortest path": 0
      }
    
    def __init__(self, minute_steppers, hour_steppers, steps_full_rev = 4320):
        """
        Parameters
        ----------
        minute_steppers : List[ClockStepper]
            list of 24 stepper objs containing minute pointers from top left row forst
        hour_steppers : List[ClockStepper]
            list of 24 stepper objs containing hour pointers
        steps_full_rev : int
            number of steps a stepper needs to make one revolution
        """
        self.hour_steppers = hour_steppers
        self.minute_steppers = minute_steppers
        
        self.digits_pointer_pos_abs = [[[int(frac * steps_full_rev) for frac in hour_minute] for hour_minute in number] for number in DigitDisplay.digits_pointer_pos_frac]
        
    def display_digit(self, field, digit, direction, extra_revs = 0):
        """Display a single digit on the clock
        
        Parameters
        ----------
        field : int
            the field where the number should be displayed 0-4
        digit : int
            the number to display
        direction : int
            -1 ccw, 1 cw, 0 whichever is shorter
        extra_revs : int, optional
            how many extra revolutions should be made, ignored when direction is 0 (default is 0)
        """
        if extra_revs == 0 or direction == 0:
            for sub_index, clk_index in enumerate(self.digit_display_indeces[field]):
                self.hour_steppers[clk_index].move_to(self.digits_pointer_pos_abs[digit][0][sub_index], direction)
                self.minute_steppers[clk_index].move_to(self.digits_pointer_pos_abs[digit][1][sub_index], direction)
        else:
            for sub_index, clk_index in enumerate(self.digit_display_indeces[field]):
                self.hour_steppers[clk_index].move_to_extra_revs(self.digits_pointer_pos_abs[digit][0][sub_index], direction, extra_revs)
                self.minute_steppers[clk_index].move_to_extra_revs(self.digits_pointer_pos_abs[digit][1][sub_index], direction, extra_revs)
                
    def display_digits(self, digits, animation = 0):
        """Display a time on the clock
        
        Parameters
        ----------
        digits : List[int]
            the digits to display, should be length 4
        animation : int, optional
            index of animation to use, indeces are in animations dict as static member in this class (default is 0, "shortest path")
        """
        for field, digit in enumerate(digits):
            for sub_index, clk_index in enumerate(self.digit_display_indeces[field]):
                self.hour_steppers[clk_index].move_to(self.digits_pointer_pos_abs[digit][0][sub_index], 0)
                self.minute_steppers[clk_index].move_to(self.digits_pointer_pos_abs[digit][1][sub_index], 0)
        return
    
    def display_digits_stealth(self, digits):
        """Display a time on the clock, minimizes the steppers that are moving by
        checking if either of the clock pointers is already at desired position
        
        Parameters
        ----------
        digits : List[int]
            the digits to display, should be length 4
        """
        for field, digit in enumerate(digits):
            for sub_index, clk_index in enumerate(self.digit_display_indeces[field]):
                a_pos = self.digits_pointer_pos_abs[digit][0][sub_index]
                b_pos = self.digits_pointer_pos_abs[digit][1][sub_index]
                m = self.minute_steppers[clk_index]
                h = self.hour_steppers[clk_index]
                m_pos = m.current_target_pos
                h_pos = h.current_target_pos
                
                #if both steppers are equal to either a or b dont do anything
                if (m_pos == a_pos and h_pos == b_pos) or (m_pos == b_pos and h_pos == a_pos):
                    continue
                #if one is equal move the other, minute priority because hour is usually quieter
                elif m_pos == a_pos:
                    h.move_to(b_pos, 0)
                elif m_pos == b_pos:
                    h.move_to(a_pos, 0)
                elif h_pos == a_pos:
                    m.move_to(b_pos, 0)
                elif h_pos == b_pos:
                    m.move_to(a_pos, 0)
                #if neither one is equal move both
                else:
                    m.move_to(a_pos, 0)
                    h.move_to(b_pos, 0)
            