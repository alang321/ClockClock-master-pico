import math
import random
import uasyncio as asyncio

class DigitDisplay:
    """
    A class used to display digits given a list of steppers (might be over fragemntation of code idk)

    ...

    Attributes
    ----------
    digit_display_indices : List[int]
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
    digit_display_indices = [[0, 1, 8, 9, 16, 17], [2, 3, 10, 11, 18, 19], [4, 5, 12, 13, 20, 21], [6, 7, 14, 15, 22, 23]]
    column_indices = [[0, 8, 16], [1, 9, 17], [2, 10, 18], [3, 11, 19], [4, 12, 20], [5, 13, 21], [6, 14, 22], [7, 15, 23]]
    row_indices = [[0, 1, 2, 3, 4, 5, 6, 7], [8, 9, 10, 11, 12, 13, 14, 15], [16, 17, 18, 19, 20, 21, 22, 23]]

    row_module_indices = [[0, 1], [2, 3], [4, 5]]
    
    # fractional position of the pointer, first sublist is hour hand second is minute hand, 0.0 at the 12 o clock position and 0.5 at 6 o clock
    # from top left, rows first
    digits_pointer_pos_frac =  [[[0.5, 0.5, 0.5, 0.5, 0.25, 0.75],   [0.25, 0.75, 0, 0, 0, 0]],             # 0
                               [[0.625, 0.5, 0.125, 0, 0.625, 0],    [0.625, 0.625, 0.125, 0.5, 0.625, 0]],   # 1, with angled line on top
                               #[[0.625, 0.5, 0.625, 0, 0.625, 0],    [0.625, 0.5, 0.625, 0.5, 0.625, 0]],   # 1, classic 7 segment straight line
                               [[0.25, 0.75, 0.5, 0.75, 0.25, 0.75], [0.25, 0.5, 0.25, 0, 0, 0.75]],        # 2
                               [[0.25, 0.75, 0.25, 0, 0.25, 0.75],   [0.25, 0.5, 0.25, 0.75, 0.25, 0]],     # 3
                               [[0.5, 0.5, 0, 0, 0.625, 0],          [0.5, 0.5, 0.25, 0.5, 0.625, 0]],      # 4
                               [[0.25, 0.75, 0, 0.5, 0.25, 0],       [0.5, 0.75, 0.25, 0.75, 0.25, 0.75]],  # 5
                               [[0.5, 0.75, 0, 0.75, 0, 0],          [0.25, 0.75, 0.5, 0.5, 0.25, 0.75]],   # 6
                               [[0.25, 0.5, 0.625, 0.5, 0.625, 0],   [0.25, 0.75, 0.625, 0, 0.625, 0]],     # 7
                               [[0.5, 0.5, 0, 0, 0, 0],              [0.25, 0.75, 0.25, 0.75, 0.25, 0.75]], # 8
                               [[0.5, 0.5, 0.25, 0.5, 0.25, 0],      [0.25, 0.75, 0, 0, 0.25, 0.75]]]       # 9
    
    #animations modes for position transitions
    animations = {
      "shortest path": 0,  # simply taking shortest path to new position
      "stealth": 1,  # minimal movements to minimize noise
      "extra revs": 2,  # move with extra revolutions to target
      "straight wave": 3,  # align steppers in straight line at 45 degrees and start moving delayed from left to right
      "opposing pointers": 4,  # align all pointers at bottom and start moving minute and hours opposite direction with extra rotations to target
      "focus": 5,  # move all pointer to point to center and move with extra rotation to target, maybe change speed depending on how far out
      "opposites": 6,  # simply rotate pointers in opposing directions to target
      "field lines":  7,  # visualize electric vector field of 2 point charges
      "equipotential": 8,  # visualises equipotential line directions of 2 point charges
      "speedy clock": 9,  # move minute and hour hand at different speeds to move somewhat like a clock althoug hour hand doesnt move as slow
      "random": 10,  # all clocks move to unique radnom position, once all clocks reach the move to correct one with shortest path
      "handoff": 11,   # all move pointing down, then bottom row starts opposing pointer thing, when done second row starts ("handoff") and so on
      "opposing wave": 12,  # like opposing pointers but starts from left with delay between columns
      "circle": 13 # a big circle that collapses to the center
      }
    
    def __init__(self, clockclock):
        """
        Parameters
        ----------
        clockclock
            a ClockClock24 obj, basically the "master"
        """
        self.clockclock = clockclock
        
        self.hour_steppers = self.clockclock.hour_steppers
        self.minute_steppers = self.clockclock.minute_steppers
        
        self.steps_full_rev = self.clockclock.steps_full_rev
        
        self.animation_handlers = [
            self.new_pose_shortest_path,
            self.new_pose_stealth,
            self.new_pose_extra_revs,
            self.new_pose_straight_wave,
            self.new_pose_opposing_pointers,
            self.new_pose_focus,
            self.new_pose_opposites,
            self.new_pose_field_lines,
            self.new_pose_equipotential,
            self.new_pose_speedy_clock,
            self.new_pose_random,
            self.new_pose_handoff,
            self.new_pose_opposing_wave,
            self.new_pose_circle
          ]
        
        self.animation_turns = 2 # number of rotations used in a lot of animations
        
        self.digits_pointer_pos_abs = [[[int(frac * self.steps_full_rev) for frac in hour_minute] for hour_minute in number] for number in DigitDisplay.digits_pointer_pos_frac]
    
    def display_digit(self, field, digit, direction, extra_revs = 0):
        """Display a single digit on the clock
        
        Parameters
            the field where the number should be displayed 0-3
        digit : int
            the number to display
        direction : int
            -1 ccw, 1 cw, 0 whichever is shorter
        extra_revs : int, optional
            how many extra revolutions should be made, ignored when direction is 0 (default is 0)
        """
        if extra_revs == 0 or direction == 0:
            for sub_index, clk_index in enumerate(self.digit_display_indices[field]):
                self.hour_steppers[clk_index].move_to(self.digits_pointer_pos_abs[digit][0][sub_index], direction)
                self.minute_steppers[clk_index].move_to(self.digits_pointer_pos_abs[digit][1][sub_index], direction)
        else:
            for sub_index, clk_index in enumerate(self.digit_display_indices[field]):
                self.hour_steppers[clk_index].move_to_extra_revs(self.digits_pointer_pos_abs[digit][0][sub_index], direction, extra_revs)
                self.minute_steppers[clk_index].move_to_extra_revs(self.digits_pointer_pos_abs[digit][1][sub_index], direction, extra_revs)
                
    def display_mode(self, mode_id):
        mode_id += 1
        mode_string = str(mode_id)
        digit_count = len(str(mode_string))
        
        default_pos = int(self.steps_full_rev * 0.625)
        
        new_positions_0 = [default_pos] * 24
        new_positions_1 = [default_pos] * 24
        for digit_id, field in enumerate(range(4 - digit_count, 4)):
            digit = int(mode_string[digit_id])
            for sub_index, clk_index in enumerate(self.digit_display_indices[field]):
                new_positions_0[clk_index] = self.digits_pointer_pos_abs[digit][0][sub_index]
                new_positions_1[clk_index] = self.digits_pointer_pos_abs[digit][1][sub_index]

        for clk_index in range(24):
            self.hour_steppers[clk_index].move_to(new_positions_0[clk_index], 0)
            self.minute_steppers[clk_index].move_to(new_positions_1[clk_index], 0)
                
    def display_digits(self, digits, animation_id = 0):
        """Display all 4 digits simultaneously on the clock
        
        Parameters
        ----------
        digits : List[int]
            the digits to display, should be length 4
        animation : int, optional
            index of animation to use, indices are in animations dict as static member in this class (default is 0, "shortest path")
        """
        new_positions_h = [0] * 24
        new_positions_m = [0] * 24
        
        for field, digit in enumerate(digits):
            for sub_index, clk_index in enumerate(DigitDisplay.digit_display_indices[field]):
                new_positions_h[clk_index] = self.digits_pointer_pos_abs[digit][0][sub_index]
                new_positions_m[clk_index] = self.digits_pointer_pos_abs[digit][1][sub_index]
        
        self.clockclock.async_display_task = asyncio.create_task(
            self.animation_handlers[animation_id](new_positions_h, new_positions_m))

    async def new_pose_shortest_path(self, new_positions_h, new_positions_m):
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
    
    async def new_pose_stealth(self, new_positions_0, new_positions_1):
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
        self.__new_pose_stealth(new_positions_0, new_positions_1)
                
    def __new_pose_stealth(self, new_positions_0, new_positions_1):
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
    
    async def new_pose_extra_revs(self, new_positions_h, new_positions_m, direction=0, extra_revs=2):
        """Display a series of new positions on the clock, move stepper the shortest path to its destianation
        
        Parameters
        ----------
        new_positions_h : List[int]
            the positions to display for hour steppers, should int arrays of length 24
        new_positions_m : List[int]
            the positions to display for hour steppers, should int arrays of length 24
        direction : int
            optional, if direction is 0 the value is chosen randomly
        extra_revs : int
            optional, how many etra revs to take to target pos
        """
        if direction == 0:
            direction = random.choice([-1, 1])
        
        for clk_index in range(24):
            self.hour_steppers[clk_index].move_to_extra_revs(new_positions_h[clk_index], direction, extra_revs)
            self.minute_steppers[clk_index].move_to_extra_revs(new_positions_m[clk_index], direction, extra_revs)
    
    async def new_pose_straight_wave(self, new_positions_h, new_positions_m):
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
        ms_delay = 350 # movement delay between individual columns
        extra_revs = self.animation_turns
        direction = random.choice([-1, 1])
        start_ang = random.choice([0.875, 0.625, 0.25])

        direction = random.randint(0, 1)
        if direction == 0:
            column_indices = self.column_indices
        else:
            column_indices = reversed(self.column_indices)

        start_pos_m = int(self.steps_full_rev * start_ang)
        start_pos_h = int(self.steps_full_rev * (start_ang - 0.5))
        
        for clk_index in range(24):
            self.hour_steppers[clk_index].move_to(start_pos_h, 0)
            self.minute_steppers[clk_index].move_to(start_pos_m, 0)

        self.clockclock.movement_done_event.clear()
        await self.clockclock.movement_done_event.wait()

        for col_index, col in enumerate(column_indices):
            if col_index != 0:
                await asyncio.sleep_ms(ms_delay)
            for clk_index in col:
                self.hour_steppers[clk_index].move_to_extra_revs(new_positions_h[clk_index], direction, extra_revs)
                self.minute_steppers[clk_index].move_to_extra_revs(new_positions_m[clk_index], direction, extra_revs)
    
    async def new_pose_opposing_pointers(self, new_positions_h, new_positions_m):
        """Display a series of new positions on the clock, align all pointers at bottom and start moving minute and hours
        opposite direction with extra rotations to target
        
        Parameters
        ----------
        new_positions_h : List[int]
            the positions to display for hour steppers, should int arrays of length 24
        new_positions_m : List[int]
            the positions to display for hour steppers, should int arrays of length 24
        """
        extra_revs = self.animation_turns
        start_ang = random.choice([0, 0.125, 0.25, 0.375, 0.5, 0.625, 0.75, 0.875])
        start_pos = int(self.steps_full_rev * start_ang)
        
        self.clockclock.move_to_all(start_pos, 0)
        
        self.clockclock.movement_done_event.clear()
        await self.clockclock.movement_done_event.wait()

        for clk_index in range(24):
            self.hour_steppers[clk_index].move_to_extra_revs(new_positions_h[clk_index], 1, extra_revs)
            self.minute_steppers[clk_index].move_to_extra_revs(new_positions_m[clk_index], -1, extra_revs)
    
    async def new_pose_focus(self, new_positions_h, new_positions_m):
        """Display a series of new positions on the clock, move all pointer to point to center and
        move with extra rotation to target
        
        Parameters
        ----------
        new_positions_h : List[int]
            the positions to display for hour steppers, should int arrays of length 24
        new_positions_m : List[int]
            the positions to display for hour steppers, should int arrays of length 24
        """
        extra_revs = self.animation_turns
        direction = random.choice([1, -1])
        
        # up is poitive x axis
        # left is poitive y axis
        # origin is at the center of top left clock
        #center, top left, bottom left, bottom right, top right
        points = [[-1, -3.5], [0.5, 0.5], [-2.5, 0.5], [-2.5, -7.5], [0.5, -7.5]]  #in units of clock spacing (10cm in this case)
        point = random.choice(points)
        
        for clk_index in range(24):
            # this assumes equal vertical and horizontal clock spacing, which is the case obv
            row = clk_index // 8
            col = clk_index % 8
            
            #the locations of the current stepper in units of clock spacing
            loc_x = -row
            loc_y = -col

            # the point the steppers should point too in units of clock spacing
            point_x = point[0]
            point_y = point[1]

            dist_x = point_x - loc_x # signed distance in vertical direction to point
            dist_y = point_y - loc_y # signed distance in horizontal direction to point

            theta = (-math.atan2(dist_y, dist_x) + math.pi * 2) % (math.pi * 2) 
            frac_ang = theta / (math.pi * 2)  # angle from 12 o clock position in cw dir
            
            start_pos = int(frac_ang * self.steps_full_rev)
            
            self.hour_steppers[clk_index].move_to(start_pos, 0)
            self.minute_steppers[clk_index].move_to(start_pos, 0)
        
        self.clockclock.movement_done_event.clear()
        await self.clockclock.movement_done_event.wait()

        delay_per_distance = 400 # ms
        start_delays = [0] * len(DigitDisplay.column_indices)
        col_indices = list(range(len(DigitDisplay.column_indices)))
        #calculate time delay of each column to point to scale start time    
        for col_index in col_indices:
            loc_y = -col_index
            point_y = point[1]
            distance = abs(point_y - loc_y)
            
            start_delays[col_index] = int(distance * delay_per_distance)

        parallel_sorted = sorted(zip(start_delays, DigitDisplay.column_indices))
        sorted_col = [x for y, x in parallel_sorted]
        sorted_delays = [y for y, x in parallel_sorted]
                   
        for sorted_col_index, col in enumerate(sorted_col):
            if sorted_col_index != 0:
                async_delay = sorted_delays[sorted_col_index] - sorted_delays[sorted_col_index - 1]
                if async_delay != 0:
                    await asyncio.sleep_ms(async_delay)
            for clk_index in col:
                self.hour_steppers[clk_index].move_to_extra_revs(new_positions_h[clk_index], direction, extra_revs)
                self.minute_steppers[clk_index].move_to_extra_revs(new_positions_m[clk_index], direction, extra_revs)
    
    async def new_pose_opposites(self, new_positions_h, new_positions_m):
        """Display a series of new positions on the clock, simply rotate minute and hour pointers in opposing directions to target
        
        Parameters
        ----------
        new_positions_h : List[int]
            the positions to display for hour steppers, should int arrays of length 24
        new_positions_m : List[int]
            the positions to display for hour steppers, should int arrays of length 24
        extra_revs : int
            optional parameter for extra revs
        """
        extra_revs = self.animation_turns
        
        for clk_index in range(24):
            self.hour_steppers[clk_index].move_to_extra_revs(new_positions_h[clk_index], 1, extra_revs)
            self.minute_steppers[clk_index].move_to_extra_revs(new_positions_m[clk_index], -1, extra_revs)
    
    async def new_pose_field_lines(self, new_positions_h, new_positions_m):
        """Display a series of new positions on the clock, visualises vectors of electric field with 2 point charges
        
        Parameters
        ----------
        new_positions_h : List[int]
            the positions to display for hour steppers, should int arrays of length 24
        new_positions_m : List[int]
            the positions to display for hour steppers, should int arrays of length 24
        """
        extra_revs = self.animation_turns
        direction = random.choice([-1, 1])
        
        # up is poitive x axis
        # left is poitive y axis
        # origin is at the center of top left clock
        q_magnitudes = [1, -1]
        points = random.choice([[[-1, -1.5], [-1, -5.5]], [[0.5, 0.5], [0.5, -7.5]], [[-2.5, 0.5], [-2.5, -7.5]]]) 
        point_1 = points[0]
        point_2 = points[1]
        q_locations = [point_1, point_2]
        
        for clk_index in range(24):
            # this assumes equal vertical and horizontal clock spacing, which is the case obv
            row = clk_index // 8
            col = clk_index % 8
            
            #the locations of the current stepper in units of clock spacing
            loc_x = -row
            loc_y = -col
            
            E_total = [0, 0]
            
            for q_index, q_magnitude in enumerate(q_magnitudes):
                point_x = q_locations[q_index][0]
                point_y = q_locations[q_index][1]

                dist_x = loc_x - point_x
                dist_y = loc_y - point_y
                
                # the point the steppers should point too in units of clock spacing
                distance = math.sqrt(dist_x**2 + dist_y**2)
                
                E_vector = [q_magnitude/distance**2*dist_x/distance, q_magnitude/distance**2*dist_y/distance]

                E_total = [E_vector[0] + E_total[0], E_vector[1] + E_total[1]]
            
            theta = (-math.atan2(E_total[1], E_total[0]) + math.pi * 2) % (math.pi * 2) 
            frac_ang = theta / (math.pi * 2)  # angle from 12 o clock position in cw dir
            
            start_pos_m = frac_ang * self.steps_full_rev
            start_pos_h = ((frac_ang + 0.5) * self.steps_full_rev) % self.steps_full_rev
            
            self.hour_steppers[clk_index].move_to(int(start_pos_h), 0)
            self.minute_steppers[clk_index].move_to(int(start_pos_m), 0)
            
        #wait for move to be done
        self.clockclock.movement_done_event.clear()
        await self.clockclock.movement_done_event.wait()

        for clk_index in range(24):
            self.hour_steppers[clk_index].move_to_extra_revs(new_positions_h[clk_index], direction, extra_revs)
            self.minute_steppers[clk_index].move_to_extra_revs(new_positions_m[clk_index], direction, extra_revs)
    
    async def new_pose_equipotential(self, new_positions_h, new_positions_m):
        """Display a series of new positions on the clock, visualises directions of equipotential lines with 2 point charges
        
        Parameters
        ----------
        new_positions_h : List[int]
            the positions to display for hour steppers, should int arrays of length 24
        new_positions_m : List[int]
            the positions to display for hour steppers, should int arrays of length 24
        """
        extra_revs = self.animation_turns
        direction = random.choice([-1, 1])
        
        # up is poitive x axis
        # left is poitive y axis
        # origin is at the center of top left clock
        q_magnitudes = [1, -1]
        points = random.choice([[[-1, -1.5], [-1, -5.5]], [[0.5, 0.5], [0.5, -7.5]], [[-2.5, 0.5], [-2.5, -7.5]]]) 
        point_1 = points[0]
        point_2 = points[1]
        q_locations = [point_1, point_2]
        
        for clk_index in range(24):
            # this assumes equal vertical and horizontal clock spacing, which is the case obv
            row = clk_index // 8
            col = clk_index % 8
            
            #the locations of the current stepper in units of clock spacing
            loc_x = -row
            loc_y = -col
            
            E_total = [0, 0]
            
            for q_index, q_magnitude in enumerate(q_magnitudes):
                point_x = q_locations[q_index][0]
                point_y = q_locations[q_index][1]

                dist_x = loc_x - point_x
                dist_y = loc_y - point_y
                
                # the point the steppers should point too in units of clock spacing
                distance = math.sqrt(dist_x**2 + dist_y**2)
                
                E_vector = [q_magnitude/distance**2*dist_x/distance, q_magnitude/distance**2*dist_y/distance]

                E_total = [E_vector[0] + E_total[0], E_vector[1] + E_total[1]]
                
            eq = [E_total[1], -E_total[0]]#direction of quipotential lines, normal to field lines
            
            theta = (-math.atan2(eq[1], eq[0]) + math.pi * 2) % (math.pi * 2) 
            frac_ang = theta / (math.pi * 2)  # angle from 12 o clock position in cw dir

            start_pos_m = frac_ang * self.steps_full_rev
            start_pos_h = ((frac_ang + 0.5) * self.steps_full_rev) % self.steps_full_rev
            
            self.hour_steppers[clk_index].move_to(int(start_pos_h), 0)
            self.minute_steppers[clk_index].move_to(int(start_pos_m), 0)

        #wait for move to be done
        self.clockclock.movement_done_event.clear()
        await self.clockclock.movement_done_event.wait()

        for clk_index in range(24):
            self.hour_steppers[clk_index].move_to_extra_revs(new_positions_h[clk_index], direction, extra_revs)
            self.minute_steppers[clk_index].move_to_extra_revs(new_positions_m[clk_index], direction, extra_revs)
    
    async def new_pose_speedy_clock(self, new_positions_h, new_positions_m):
        """move minute and hour hand at different speeds to move somewhat like a clock althoug hour hand doesnt move as slow
        
        Parameters
        ----------
        new_positions_h : List[int]
            the positions to display for hour steppers, should int arrays of length 24
        new_positions_m : List[int]
            the positions to display for hour steppers, should int arrays of length 24
        extra_revs : int
            optional parameter for extra revs
        """
        hour_speed = int(self.clockclock.current_speed * 0.43)
        
        for stepper in self.hour_steppers:
            stepper.set_speed(hour_speed)
            
        for clk_index in range(24):
            self.hour_steppers[clk_index].move_to_extra_revs(new_positions_h[clk_index], 1, 1)
            self.minute_steppers[clk_index].move_to_extra_revs(new_positions_m[clk_index], 1, 3)
        
        self.clockclock.movement_done_event.clear()
        try:
            await self.clockclock.movement_done_event.wait()
        finally:
            self.clockclock.set_speed_all(self.clockclock.current_speed) #always gets called, even when task is cancelled

    async def new_pose_random(self, new_positions_h, new_positions_m):
        """all clocks move to unique radnom position, once all clocks reach the move to correct one with shortest path

        Parameters
        ----------
        new_positions_h : List[int]
            the positions to display for hour steppers, should int arrays of length 24
        new_positions_m : List[int]
            the positions to display for hour steppers, should int arrays of length 24
        extra_revs : int
            optional parameter for extra revs
        """
        for clk_index in range(24):
            direction = random.choice([-1, 1])
            position = random.randrange(self.steps_full_rev)
            self.hour_steppers[clk_index].move_to(position, direction)
            direction = random.choice([-1, 1])
            position = random.randrange(self.steps_full_rev)
            self.minute_steppers[clk_index].move_to(position, direction)

        self.clockclock.movement_done_event.clear()
        await self.clockclock.movement_done_event.wait()

        for clk_index in range(24):
            self.hour_steppers[clk_index].move_to(new_positions_h[clk_index], 0)
            self.minute_steppers[clk_index].move_to(new_positions_m[clk_index], 0)

    async def new_pose_handoff(self, new_positions_h, new_positions_m):
        """all move pointing down, then bottom row starts opposing pointer thing, when done second row starts ("handoff") and so on

        Parameters
        ----------
        new_positions_h : List[int]
            the positions to display for hour steppers, should int arrays of length 24
        new_positions_m : List[int]
            the positions to display for hour steppers, should int arrays of length 24
        """
        start_pos = 0
        end_pos = int(self.steps_full_rev * 0.5)

        self.clockclock.move_to_all(start_pos, 0)

        self.clockclock.movement_done_event.clear()
        await self.clockclock.movement_done_event.wait()

        for clk_indices in self.row_indices:
            for clk_index in clk_indices:
                self.hour_steppers[clk_index].move_to(end_pos, 1)
                self.minute_steppers[clk_index].move_to(end_pos, -1)

            await asyncio.sleep(4.65)

        self.clockclock.movement_done_event.clear()
        await self.clockclock.movement_done_event.wait()

        for clk_index in range(24):
            self.hour_steppers[clk_index].move_to(new_positions_h[clk_index], 0)
            self.minute_steppers[clk_index].move_to(new_positions_m[clk_index], 0)

    async def new_pose_opposing_wave(self, new_positions_h, new_positions_m):
        """like opposing pointers but starts from left with delay between columns

        Parameters
        ----------
        new_positions_h : List[int]
            the positions to display for hour steppers, should int arrays of length 24
        new_positions_m : List[int]
            the positions to display for hour steppers, should int arrays of length 24
        """
        direction = random.randint(0, 1)
        ms_delay = 450
        extra_revs = 1

        if direction == 0:
            start_pos = int(self.steps_full_rev * 0.75)
            column_indices = self.column_indices
        else:
            start_pos = int(self.steps_full_rev * 0.25)
            column_indices = reversed(self.column_indices)

        self.clockclock.move_to_all(start_pos, 0)

        self.clockclock.movement_done_event.clear()
        await self.clockclock.movement_done_event.wait()

        for index, col in enumerate(column_indices):
            if index != 0:
                await asyncio.sleep_ms(ms_delay)
            for clk_index in col:
                self.hour_steppers[clk_index].move_to_extra_revs(new_positions_h[clk_index], 1, extra_revs)
                self.minute_steppers[clk_index].move_to_extra_revs(new_positions_m[clk_index], -1, extra_revs)

    async def new_pose_circle(self, new_positions_h, new_positions_m):
        """a big circle that collapses to the center

        Parameters
        ----------
        new_positions_h : List[int]
            the positions to display for hour steppers, should int arrays of length 24
        new_positions_m : List[int]
            the positions to display for hour steppers, should int arrays of length 24
        """
        extra_revs = self.animation_turns
        
        # this function is relatively computationally heavy and takes about 7ms to execute on a Pi Pico
        # could be implemented as precalculated list
        
        # each pointers midpoint should be tangent to circle in center of clockclock
        # can be seen as right angle triangle, as tangent are normal to radius
        
        # coordinate system: origin at center of clockclock, y+ up x+ right
        # center of clock clock
        
        point = random.choice([[0, 0], [0, 20], [40, 20]]) 
        x_cc = point[0]
        y_cc = point[1]
        
        # with abc and c the hypotenuse, with x_c center of a clock
        # a - from center or clock to center of clock pointer - 2cm
        # c - center of clockclock to center of clock sqrt((x_c - x_cc)**2 + (y_c - y_cc))
        # b - center of clockclock to center of clock pointer

        for clk_index in range(24):
            x_c = -35 + clk_index % 8 * 10  # cm
            y_c = 10 - clk_index // 8 * 10  # cm
            
            #signed distance of clock to center
            x_dist = (x_c - x_cc)
            y_dist = (y_c - y_cc)

            a = 2  # cm
            c = math.sqrt(x_dist ** 2 + y_dist ** 2)

            # angle between a and c
            alph = math.acos(a / c)
            # angle between c and horizontal
            gam = math.atan(y_dist / x_dist) * math.copysign(1, x_dist)
            # angle between c and vertical
            lam = math.pi / 2 - gam
            # angle between vertical and a
            kap = math.pi - lam - alph

            pos_1 = int(-(self.steps_full_rev * kap) / (2 * math.pi) * math.copysign(1, x_dist)) % self.steps_full_rev

            # since the angle of the pointers with respect to c should be equal
            pos_2 = int(-(self.steps_full_rev * (kap + 2 * alph)) / (2 * math.pi) * math.copysign(1, x_dist)) % self.steps_full_rev
            
            if y_dist > 0:
                self.hour_steppers[clk_index].move_to(pos_2, 0)
                self.minute_steppers[clk_index].move_to(pos_1, 0)
            else:
                self.hour_steppers[clk_index].move_to(pos_1, 0)
                self.minute_steppers[clk_index].move_to(pos_2, 0)
        
        #wait for move to be done
        self.clockclock.movement_done_event.clear()
        await self.clockclock.movement_done_event.wait()
                
        for clk_index in range(24):
            x_c = -35 + clk_index % 8 * 10  # cm
            y_c = 10 - clk_index // 8 * 10  # cm
            
            #signed distance of clock to center
            x_dist = (x_c - x_cc)
            y_dist = (y_c - y_cc)
            
            if x_dist < 0:
                if y_dist > 0:
                    self.hour_steppers[clk_index].move_to_extra_revs(new_positions_h[clk_index], -1, extra_revs)
                    self.minute_steppers[clk_index].move_to_extra_revs(new_positions_m[clk_index], 1, extra_revs)
                else:                
                    self.hour_steppers[clk_index].move_to_extra_revs(new_positions_h[clk_index], 1, extra_revs)
                    self.minute_steppers[clk_index].move_to_extra_revs(new_positions_m[clk_index], -1, extra_revs)
            else:
                if y_dist > 0:
                    self.hour_steppers[clk_index].move_to_extra_revs(new_positions_h[clk_index], 1, extra_revs)
                    self.minute_steppers[clk_index].move_to_extra_revs(new_positions_m[clk_index], -1, extra_revs)
                else:                
                    self.hour_steppers[clk_index].move_to_extra_revs(new_positions_h[clk_index], -1, extra_revs)
                    self.minute_steppers[clk_index].move_to_extra_revs(new_positions_m[clk_index], 1, extra_revs)
                

