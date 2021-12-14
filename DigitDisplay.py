from ClockStepper import ClockStepper
import math
import time

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
        dictionary that contains names of animation modes and translates to indices
    clockclock
        a ClockClock24 obj, basically the "master"
    minute_steppers : List[ClockStepper]
        list of 24 stepper objs containing minute pointers from top left row first
    hour_steppers : List[ClockStepper]
        list of 24 stepper objs containing hour pointers
    steps_full_rev : int
        number of steps a stepper needs to make one revolution

    Methods
    -------
    display_digit(field, number, direction, extra_revs = 0)
        Display a one digit on the clock
        
    display_digits(digits, animation = 0)
        Display all digits on the clock with animation
    """
    digit_display_indeces = [[0, 1, 8, 9, 16, 17], [2, 3, 10, 11, 18, 19], [4, 5, 12, 13, 20, 21], [6, 7, 14, 15, 22, 23]]
    column_indeces = [[0, 8, 16], [1, 9, 17], [2, 10, 18], [3, 11, 19], [4, 12, 20], [5, 13, 21], [6, 14, 22], [7, 15, 23]]
    row_indeces = [[0, 1, 2, 3, 4, 5, 6, 7], [8, 9, 10, 11, 12, 13, 14, 15], [16, 17, 18, 19, 20, 21, 22, 23]]
    
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
    
    #animations modes for position transitions
    animations = {
      "shortest path": 0, # simply taking shortest path to new position
      "stealth": 1, # minimal movements to minimize noise
      "extra revs": 2, # move with extra revolutions to target
      "straight wave": 3, # align steppers in straight line at 45 degrees and start moving delayed from left to right
      "opposing pointers", 4 # align all pointers at bottom and start moving minute and hours opposite direction with extra rotations to target
      "focus", 5, # move all pointer to point to center and move with extra rotation to target, maybe change speed depending on how far out
      "opposites",  6, # simply rotate pointers in opposing directions to target
      #"circles",  7, # align pointers in a circular looking thing, start rotating staggered from center inwards to center
      #"speedy clock", 8, # move minute and hour hand at different speeds to give "illsuion" of clock, right nowmthi would have to be implemented fully blocking
      }
    
    animation_handlers = [
        new_pose_shortest_path,
        new_pose_stealth,
        new_pose_extra_revs,
        new_pose_straight_wave,
        new_pose_opposing_pointers,
        new_pose_focus,
        new_pose_opposites,
      ]
    
    def __init__(self, clockclock):
        """
        Parameters
        ----------
        clockclock
            a ClockClock24 obj, basically the "master"
        """
        self.clockclock = clockclock
        
        self.hour_steppers = self.clock.hour_steppers
        self.minute_steppers = self.clock.minute_steppers
        
        self.steps_full_rev = self.clock.steps_full_rev
        
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
        """Display all 4 digits simultaneously on the clock
        
        Parameters
        ----------
        digits : List[int]
            the digits to display, should be length 4
        animation : int, optional
            index of animation to use, indeces are in animations dict as static member in this class (default is 0, "shortest path")
        """
        new_positions_h = [0] * 24
        new_positions_m = [0] * 24
        
        for field, digit in enumerate(digits):
            for sub_index, clk_index in enumerate(DigitDisplay.digit_display_indeces[field]):
                new_positions_h[clk_index] = DigitDisplay.digits_pointer_pos_abs[digit][0][sub_index]
                new_positions_m[clk_index] = DigitDisplay.digits_pointer_pos_abs[digit][1][sub_index]
                
        animation_handlers[animation](new_positions_h, new_positions_m)
    
    def new_pose_stealth(self, new_positions_0, new_positions_1):
        """Display a series of new positions on the clock, minimizes the steppers that are moving by
        checking if either of the clock pointers is already at desired position,
        can be used with slow steppers speed for very quiet, night-time operation
        
        Parameters
        ----------
        new_positions_0 : List[int]
            the positions to display, should int arrays of length 24
        new_positions_1 : List[int]
            the positions to display, should int arrays of length 24
        """
        for clk_index in range(24):
            a_pos = new_positions_0[clk_index]
            b_pos = new_positions_1[clk_index]
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
    
    def new_pose_shortest_path(self, new_positions_h, new_positions_m):
        """Display a series of new positions on the clock, move stepper the shortest path to its destianation
        
        Parameters
        ----------
        new_positions_h : List[int]
            the positions to display for hour steppers, should int arrays of length 24
        new_positions_m : List[int]
            the positions to display for hour steppers, should int arrays of length 24
        """
        for clk_index in range(24):
            self.hour_steppers[clk_index].move_to(new_positions_h[clk_index], 0)
            self.minute_steppers[clk_index].move_to(new_positions_m[clk_index], 0)
    
    def new_pose_extra_revs(self, new_positions_h, new_positions_m):
        """Display a series of new positions on the clock, move stepper the shortest path to its destianation
        
        Parameters
        ----------
        new_positions_h : List[int]
            the positions to display for hour steppers, should int arrays of length 24
        new_positions_m : List[int]
            the positions to display for hour steppers, should int arrays of length 24
        """
        extra_revs = 2
        direction = -1
        
        for clk_index in range(24):
            self.hour_steppers[clk_index].move_to(new_positions_h[clk_index], direction, extra_revs)
            self.minute_steppers[clk_index].move_to(new_positions_m[clk_index], direction, extra_revs)
    
    def new_pose_straight_wave(self, new_positions_h, new_positions_m):
        """Display a series of new positions on the clock, move all steppers to make
        minute and hour hands form a line, the start rotating staggered left to right
        with extra revolutions
        
        Parameters
        ----------
        new_positions_h : List[int]
            the positions to display for hour steppers, should int arrays of length 24
        new_positions_m : List[int]
            the positions to display for hour steppers, should int arrays of length 24
        """
        extra_revs = 2
        direction = -1
        start_pos_m = int(self.steps_full_rev * 0.875)
        start_pos_h = int(self.steps_full_rev * 0.375)
        
        for clk_index in range(24):
            self.hour_steppers[clk_index].move_to(start_pos_h, 0)
            self.minute_steppers[clk_index].move_to(start_pos_m, 0)
        
        time.sleep(0.1)
        while self.clockclock.is_running():
            time.sleep(0.2)
            
        for col in DigitDisplay.column_indeces:
            for clk_index in col:
                self.hour_steppers[clk_index].move_to_extra_revs(new_positions_h[clk_index], direction, extra_revs)
                self.minute_steppers[clk_index].move_to_extra_revs(new_positions_m[clk_index], direction, extra_revs)
            time.sleep(0.25)
    
    def new_pose_opposing_pointers(self, new_positions_h, new_positions_m):
        """Display a series of new positions on the clock, align all pointers at bottom and start moving minute and hours
        opposite direction with extra rotations to target
        
        Parameters
        ----------
        new_positions_h : List[int]
            the positions to display for hour steppers, should int arrays of length 24
        new_positions_m : List[int]
            the positions to display for hour steppers, should int arrays of length 24
        """
        extra_revs = 2
        start_pos = int(self.steps_full_rev * 0.5)
        
        self.clockclock.move_to_all(start_pos, 0)
        
        time.sleep(0.1)
        while self.clockclock.is_running():
            time.sleep(0.2)
        
        for clk_index in range(24):
            self.hour_steppers[clk_index].move_to_extra_revs(new_positions_h[clk_index], -1, extra_revs)
            self.minute_steppers[clk_index].move_to_extra_revs(new_positions_m[clk_index], 1, extra_revs)
    
    def new_pose_focus(self, new_positions_h, new_positions_m):
        """Display a series of new positions on the clock, move all pointer to point to center and
        move with extra rotation to target
        
        Parameters
        ----------
        new_positions_h : List[int]
            the positions to display for hour steppers, should int arrays of length 24
        new_positions_m : List[int]
            the positions to display for hour steppers, should int arrays of length 24
        """
        extra_revs = 2
        direction = 1
        
        for clk_index in range(24):
            # this assumes equal vertical and horizontal clock spacing
            row = clk_index // 8
            col = clk_index % 8

            # up is poitive x axis
            # left is poitive y axis
            # the point the steppers should point too in units of clock spacing
            point_x = 1  # between 4th and 5th clock
            point_y = 3.5  # on 2nd row

            dist_x = row - point_x # distance in horizontal direction to point
            dist_y = col - point_y # distance in vecrtical direction to point

            theta = (-math.atan2(dist_y, dist_x) + math.pi * 2) % (math.pi * 2) 
            frac_ang = theta / (math.pi * 2)  # angle from 12 o clock position in cw dir
            
            start_pos = int(frac_ang * self.steps_full_rev)
            
            self.hour_steppers[clk_index].move_to(start_pos, 0)
            self.minute_steppers[clk_index].move_to(start_pos, 0)
        
        time.sleep(0.1)
        while self.clockclock.is_running():
            time.sleep(0.2)
            
        for i in self.range(4):
            for clk_index in DigitDisplay.column_indices[3 - i]:
                self.hour_steppers[clk_index].move_to_extra_revs(new_positions_h[clk_index], direction, extra_revs)
                self.minute_steppers[clk_index].move_to_extra_revs(new_positions_m[clk_index], direction, extra_revs)
            for clk_index in DigitDisplay.column_indices[4 + i]:
                self.hour_steppers[clk_index].move_to_extra_revs(new_positions_h[clk_index], direction, extra_revs)
                self.minute_steppers[clk_index].move_to_extra_revs(new_positions_m[clk_index], direction, extra_revs)
            time.sleep(0.25)
    
    def new_pose_opposites(self, new_positions_h, new_positions_m):
        """Display a series of new positions on the clock, simply rotate minute and hour pointers in opposing directions to target
        
        Parameters
        ----------
        new_positions_h : List[int]
            the positions to display for hour steppers, should int arrays of length 24
        new_positions_m : List[int]
            the positions to display for hour steppers, should int arrays of length 24
        """
        extra_revs = 2
            
        for clk_index in self.range(24):
            self.hour_steppers[clk_index].move_to_extra_revs(new_positions_h[clk_index], 1, extra_revs)
            self.minute_steppers[clk_index].move_to_extra_revs(new_positions_m[clk_index], -1, extra_revs)
        
        
