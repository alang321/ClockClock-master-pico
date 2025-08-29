import math
import random
import uasyncio as asyncio
import json

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
    digits_pointer_pos_frac =  [[[[0.5, 0.5, 0.5, 0.5, 0.25, 0.75],    [0.25, 0.75, 0, 0, 0, 0]]],                 # 0
                                [[[0.625, 0.5, 0.125, 0, 0.625, 0],    [0.625, 0.625, 0.125, 0.5, 0.625, 0]],      # 1 - with angled line at top
                                     [[0.625, 0.5, 0.625, 0, 0.625, 0],    [0.625, 0.5, 0.625, 0.5, 0.625, 0]]],   # 1 - classic seven segment diplay straight line
                                [[[0.25, 0.75, 0.5, 0.75, 0.25, 0.75], [0.25, 0.5, 0.25, 0, 0, 0.75]]],            # 2
                                [[[0.25, 0.75, 0.25, 0, 0.25, 0.75],   [0.25, 0.5, 0.25, 0.75, 0.25, 0]]],         # 3
                                [[[0.5, 0.5, 0, 0, 0.625, 0],          [0.5, 0.5, 0.25, 0.5, 0.625, 0]]],          # 4
                                [[[0.25, 0.75, 0, 0.5, 0.25, 0],       [0.5, 0.75, 0.25, 0.75, 0.25, 0.75]]],      # 5
                                [[[0.5, 0.75, 0, 0.75, 0, 0],          [0.25, 0.75, 0.5, 0.5, 0.25, 0.75]]],       # 6
                                [[[0.25, 0.5, 0.625, 0.5, 0.625, 0],   [0.25, 0.75, 0.625, 0, 0.625, 0]]],         # 7
                                [[[0.5, 0.5, 0, 0, 0, 0],              [0.25, 0.75, 0.25, 0.75, 0.25, 0.75]],      # 8 - upper circle
                                     [[0.25, 0.75, 0.5, 0.5, 0, 0],        [0.5, 0.5, 0.25, 0.75, 0.25, 0.75]],    # 8 - lower circle
                                     [[0.5, 0.5, 0.25, 0, 0, 0],           [0.25, 0.75, 0.5, 0.75, 0.25, 0.75]]],  # 8 - mirrored s
                                [[[0.5, 0.5, 0.25, 0.5, 0.25, 0],      [0.25, 0.75, 0, 0, 0.25, 0.75]]]]           # 9  
    
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
      "circle": 13,# a big circle that collapses to the center
      "smaller bigger": 14, # idk
      "small circles": 15, # small circles made of 4 clocks each
      "uhrenspiel": 16, # dangling pointers
      "hamiltonian": 17, # show a hamiltonian path
      "game of life": 18, # cellular automaton
      "collision": 19, # bouncing pointers
      "checkerboard": 20, # checkerboard pattern    
      "shutter louvre": 21,
      "pickup": 22
      }
    
    def __init__(self, clockclock, number_style_options):
        """
        Parameters
        ----------
        clockclock
            a ClockClock24 obj, basically the "master"
        """
        self.clockclock = clockclock
        
        self.number_style_options = number_style_options
        
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
            self.new_pose_circle,
            self.new_pose_smaller_bigger,
            self.new_pose_small_circles,
            self.new_pose_uhrenspiel,
            self.new_pose_hamiltonian,
            self.new_pose_game_of_life,
            self.new_pose_collision,
            self.new_pose_checkerboard,
            self.new_pose_shutter_louver,
            self.new_pose_pickup
          ]
        
        # try to load hamiltonian paths json
        try:
            with open("hamiltonian_paths.json", 'r') as f:
                self.hamiltonian_paths = json.load(f)
            print(f"Loaded {len(self.hamiltonian_paths)} Hamiltonian paths.")
            self.animation_handlers.append(self.new_pose_hamiltonian)
        except FileNotFoundError:
            print("Warning: hamiltonian_paths.json not found. Hamiltonian animation will not work.")
            self.hamiltonian_paths = [[0, 1, 2, 3, 4, 5, 6, 7, 15, 14, 13, 12, 11, 10, 9, 8, 16, 17, 18, 19, 20, 21, 22, 23]]
        
        self.digits_pointer_pos_abs = [[[[int(frac * self.steps_full_rev) for frac in hour_minute] for hour_minute in digit_option] for digit_option in number] for number in DigitDisplay.digits_pointer_pos_frac]
        
    def __get_digit_pos_abs(self, digit):
        return self.digits_pointer_pos_abs[digit][self.number_style_options[digit]]
        
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
                self.hour_steppers[clk_index].move_to(self.__get_digit_pos_abs(digit)[0][sub_index], direction)
                self.minute_steppers[clk_index].move_to(self.__get_digit_pos_abs(digit)[1][sub_index], direction)
        else:
            for sub_index, clk_index in enumerate(self.digit_display_indices[field]):
                self.hour_steppers[clk_index].move_to_extra_revs(self.__get_digit_pos_abs(digit)[0][sub_index], direction, extra_revs)
                self.minute_steppers[clk_index].move_to_extra_revs(self.__get_digit_pos_abs(digit)[1][sub_index], direction, extra_revs)
                
    def display_mode(self, mode_id, left_align=False):
        mode_id += 1
        mode_string = str(mode_id)
        digit_count = len(str(mode_string))
        
        default_pos = int(self.steps_full_rev * 0.625)
        
        new_positions_0 = [default_pos] * 24
        new_positions_1 = [default_pos] * 24
        
        if left_align:
            field_ids = range(0, digit_count)
        else:
            field_ids = range(4 - digit_count, 4)
            
        for digit_id, field in enumerate(field_ids):
            digit = int(mode_string[digit_id])
                
            for sub_index, clk_index in enumerate(self.digit_display_indices[field]):
                new_positions_0[clk_index] = self.__get_digit_pos_abs(digit)[0][sub_index]
                new_positions_1[clk_index] = self.__get_digit_pos_abs(digit)[1][sub_index]
                
        self.__new_pose_stealth(new_positions_0, new_positions_1)
                
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
                new_positions_h[clk_index] = self.__get_digit_pos_abs(digit)[0][sub_index]
                new_positions_m[clk_index] = self.__get_digit_pos_abs(digit)[1][sub_index]
        
        self.clockclock.async_display_task = asyncio.create_task(
            self.animation_handlers[animation_id](new_positions_h, new_positions_m))

    async def new_pose_shortest_path(self, new_positions_h, new_positions_m):
        """Display a series of new positions on the clock, move stepper the shortest path to its destination
        
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
            if (m_pos == a_pos and h_pos == b_pos):
                h.move_to(b_pos, 0)
                m.move_to(a_pos, 0)
            elif (m_pos == b_pos and h_pos == a_pos):
                h.move_to(a_pos, 0)
                m.move_to(b_pos, 0)
            elif m_pos == a_pos: #if one is equal move the other, minute priority because hour is usually quieter for some reason
                h.move_to(b_pos, 0)
                m.move_to(a_pos, 0)
            elif m_pos == b_pos:
                h.move_to(a_pos, 0)
                m.move_to(b_pos, 0)
            elif h_pos == a_pos:
                m.move_to(b_pos, 0)
                h.move_to(a_pos, 0)
            elif h_pos == b_pos:
                m.move_to(a_pos, 0)
                h.move_to(b_pos, 0)
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
        ms_delay = 400 # movement delay between individual columns
        extra_revs = 1
        direction = random.choice([-1, 1])
        start_ang = random.choice([0.875, 0.625, 0.75])

        wave_direction = random.randint(0, 1)
        if wave_direction == 0:
            column_indices = self.column_indices
        else:
            column_indices = reversed(self.column_indices)

        start_pos_m = int(self.steps_full_rev * start_ang)
        start_pos_h = int(self.steps_full_rev * (start_ang - 0.5))
        
        self.clockclock.move_to_hour(start_pos_h, 0)
        self.clockclock.move_to_minute(start_pos_m, 0)

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
        extra_revs = 1
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
        extra_revs = 1
        direction = random.choice([1, -1])
        
        # up is poitive x axis
        # left is poitive y axis
        # origin is at the center of top left clock
        #center, top left, bottom left, bottom right, top right
        #points = [[-1, -3.5], [-1, -3.5], [0.5, -3.5], [-2.5, -3.5]] 
        #point = random.choice(points)
        point = [-1, -3.5]
        
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
        extra_revs = 2
        
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
        extra_revs = 1
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
        extra_revs = 1
        ms_delay = 400
        ms_delay_start = 300
        direction = random.choice([-1, 1])
        
        # up is poitive x axis
        # left is poitive y axis
        # origin is at the center of top left clock
        q_magnitudes = [1, -1]
        point_1 = random.choice([[-1, -1.5], [0.5, 0.5], [-2.5, 0.5]])
        point_2 = random.choice([[-1, -5.5], [0.5, -7.5], [-2.5, -7.5]])
        q_locations = [point_1, point_2]
        
        
        
        for col_index, col in enumerate(self.column_indices):
            if col_index != 0:
                await asyncio.sleep_ms(ms_delay_start)
                
            for clk_index in col:
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
        
        for index, col in enumerate(self.column_indices):
            if index != 0:
                await asyncio.sleep_ms(ms_delay)
            for clk_index in col:
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
        ms_delay = 400
        oldspeed = self.clockclock.current_speed
        hour_speed = int(self.clockclock.current_speed * 0.38)
        
        self.clockclock.set_speed_hour(hour_speed)
            
        for col_index, col in enumerate(self.column_indices):
            if col_index != 0:
                try:
                    await asyncio.sleep_ms(ms_delay)
                except asyncio.CancelledError:
                    self.clockclock.set_speed_hour(oldspeed) # gets called only when task is cancelled
                    raise
                
            for clk_index in col:
                self.hour_steppers[clk_index].move_to_extra_revs(new_positions_h[clk_index], 1, 1)
                self.minute_steppers[clk_index].move_to_extra_revs(new_positions_m[clk_index], 1, 3)
        
        self.clockclock.movement_done_event.clear()
        try:
            await self.clockclock.movement_done_event.wait()
        finally:
            self.clockclock.set_speed_hour(oldspeed) #always gets called, even when task is cancelled

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
        ms_delay = 300
        
        for col_index, col in enumerate(self.column_indices):
            if col_index != 0:
                await asyncio.sleep_ms(ms_delay)
            for clk_index in col:
                direction = random.choice([-1, 1])
                position = random.randrange(self.steps_full_rev)
                self.hour_steppers[clk_index].move_to(position, direction)
                direction = random.choice([-1, 1])
                position = random.randrange(self.steps_full_rev)
                self.minute_steppers[clk_index].move_to(position, direction)

        self.clockclock.movement_done_event.clear()
        await self.clockclock.movement_done_event.wait()
        
        ms_delay = 400
        
        for col_index, col in enumerate(self.column_indices):
            if col_index != 0:
                await asyncio.sleep_ms(ms_delay)
            for clk_index in col:
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
        extra_revs = 1
        
        # this function is relatively computationally heavy and takes about 7ms to execute on a Pi Pico
        # could be implemented as precalculated list
        
        # each pointers midpoint should be tangent to circle in center of clockclock
        # can be seen as right angle triangle, as tangent are normal to radius
        
        # coordinate system: origin at center of clockclock, y+ up x+ right
        # center of clock clock
        
        point = random.choice([[0, 0], [0, 0], [0, 20], [9, -20]]) 
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
                    
                        
    async def new_pose_smaller_bigger(self, new_positions_h, new_positions_m):
        """idk how to describe
        
        Parameters
        ----------
        new_positions_h : List[int]
            the positions to display for hour steppers, should int arrays of length 24
        new_positions_m : List[int]
            the positions to display for hour steppers, should int arrays of length 24
        """
        extra_revs = 1
        
        for index, clk_lst in enumerate(self.column_indices):
            if (index % 2) == 0:
                h_pos = int(0.125 * self.steps_full_rev)
                m_pos = int(0.375 * self.steps_full_rev)
            else:
                h_pos = int(0.625 * self.steps_full_rev)
                m_pos = int(0.875 * self.steps_full_rev)
            
            for clk_index in clk_lst:    
                self.hour_steppers[clk_index].move_to(h_pos, 0)
                self.minute_steppers[clk_index].move_to(m_pos, 0)
        
        self.clockclock.movement_done_event.clear()
        await self.clockclock.movement_done_event.wait()
        
        
        direction = 1
        for clk_index in range(24):
            self.hour_steppers[clk_index].move_to_extra_revs(new_positions_h[clk_index], direction, extra_revs)
            self.minute_steppers[clk_index].move_to_extra_revs(new_positions_m[clk_index], direction, extra_revs)
                    
    async def new_pose_small_circles(self, new_positions_h, new_positions_m):
        """small circles made of 4 clocks each
        
        Parameters
        ----------
        new_positions_h : List[int]
            the positions to display for hour steppers, should int arrays of length 24
        new_positions_m : List[int]
            the positions to display for hour steppers, should int arrays of length 24
        """
        extra_revs = 1
        
        # top and botom row
        for row in range(2):
            for col in range(8):
                clk_index = row * 16 + col
                
                pos = int((0.25 * (col % 2) + 0.375) * self.steps_full_rev)
                
                self.hour_steppers[clk_index].move_to(pos, 0)
                self.minute_steppers[clk_index].move_to(pos, 0)
        
        # middle row
        for col in range(8):
            clk_index = 8 + col
                
            pos = int((0.75 * (col % 2) + 0.125) * self.steps_full_rev)
                
            self.hour_steppers[clk_index].move_to(pos, 0)
            self.minute_steppers[clk_index].move_to(pos, 0)
        
        self.clockclock.movement_done_event.clear()
        await self.clockclock.movement_done_event.wait()

        for clk_index in range(24):
            self.hour_steppers[clk_index].move_to_extra_revs(new_positions_h[clk_index], 1, extra_revs)
            self.minute_steppers[clk_index].move_to_extra_revs(new_positions_m[clk_index], -1, extra_revs)
            
    async def new_pose_uhrenspiel(self, new_positions_h, new_positions_m):
        """uhrenspiel, dangling pointers
        
        Parameters
        ----------
        new_positions_h : List[int]
            the positions to display for hour steppers, should int arrays of length 24
        new_positions_m : List[int]
            the positions to display for hour steppers, should int arrays of length 24
        """
        oldspeed = self.clockclock.current_speed
        oldaccel = self.clockclock.current_accel
        
        # these values are generated with a scipy script
        # simulating a damped pendulum and taking peak accel and speed values for each period
        startpos_h = 864
        targetpos_h = [2628, 1959, 2248, 2160]
        startpos_m = int(self.steps_full_rev - 864)
        targetpos_m = [int(self.steps_full_rev/2) + (int(self.steps_full_rev/2) - i) for i in targetpos_h]
        speed = [int(i * 0.9) for i in [1000, 511, 224, 99]]
        accel = [int(i * 0.9) for i in [1422, 1072, 490, 217]]
        
        self.clockclock.move_to_hour(startpos_h, 0)
        self.clockclock.move_to_minute(startpos_m, 0)
        
        self.clockclock.movement_done_event.clear()
        await self.clockclock.movement_done_event.wait()
        self.clockclock.set_accel_all(750)
        
        for i in range(len(speed)):
            self.clockclock.set_speed_all(speed[i])
            #self.clockclock.set_accel_all(accel[i])
            
            self.clockclock.move_to_hour(targetpos_h[i], 0)
            self.clockclock.move_to_minute(targetpos_m[i], 0)
            
            self.clockclock.movement_done_event.clear()
            try:
                await self.clockclock.movement_done_event.wait()
            except asyncio.CancelledError:
                self.clockclock.set_speed_all(oldspeed) # only gets called when task is cancelled
                self.clockclock.set_accel_all(oldaccel)
                raise
    
        self.clockclock.set_speed_all(oldspeed)
        self.clockclock.set_accel_all(oldaccel)
        
        await asyncio.sleep_ms(1000)
            
        for clk_index in range(24):
            self.hour_steppers[clk_index].move_to(new_positions_h[clk_index], 0)
            self.minute_steppers[clk_index].move_to(new_positions_m[clk_index], 0)

    async def new_pose_collision(self, new_positions_h, new_positions_m):
        """EAch row or column comes with a wave from alternating directions."""
        extra_revs = 1
        ms_delay = 400
        
        wave_direction = random.choice([1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0])
        first_direction = random.choice([0, 1])

        if wave_direction == 0:
            indices = self.row_indices
            start_ang = 0.75
        else:
            indices = self.column_indices
            start_ang = 0.0

        if first_direction == 1:
            start_ang += 0.5

        # move to start position
        for index, lst in enumerate(indices):
            for clk_index in lst:
                start_pos = int(self.steps_full_rev * (start_ang + (index % 2) * 0.5))

                self.hour_steppers[clk_index].move_to(start_pos, 0)
                self.minute_steppers[clk_index].move_to(start_pos, 0)

        indices_final = []  
        for index, lst in enumerate(indices):
            if (index % 2) == first_direction:
                indices_final.append(lst)
            else:
                # reversed list
                indices_final.append(list(reversed(lst)))

        # wait for move to be done
        self.clockclock.movement_done_event.clear()
        await self.clockclock.movement_done_event.wait()

        for index in range(len(indices[0])):
            if index != 0:
                await asyncio.sleep_ms(ms_delay)

            for lst_t in indices_final:
                clk_index = lst_t[index]
                self.hour_steppers[clk_index].move_to_extra_revs(new_positions_h[clk_index], 1, extra_revs)
                self.minute_steppers[clk_index].move_to_extra_revs(new_positions_m[clk_index], -1, extra_revs)

    async def new_pose_checkerboard(self, new_positions_h, new_positions_m):
        """Animation: Moves clocks in a checkerboard pattern."""
        extra_revs = 1

        for clk_idx in range(24):
            if 7 < clk_idx < 16:
                offset = 1
            else:
                offset = 0
                
            if ((clk_idx + offset) % 2) == 0:
                start_ang_h = 0.0
                start_ang_m = 0.5
            else:
                start_ang_h = 0.25
                start_ang_m = 0.75

            start_pos_h = int(self.steps_full_rev * start_ang_h)
            start_pos_m = int(self.steps_full_rev * start_ang_m)

            self.hour_steppers[clk_idx].move_to(start_pos_h, 0)
            self.minute_steppers[clk_idx].move_to(start_pos_m, 0)

        # wait for move to be done
        self.clockclock.movement_done_event.clear()
        await self.clockclock.movement_done_event.wait()

        for clk_idx in range(24):
            if 7 < clk_idx < 16:
                offset = 1
            else:
                offset = 0

            self.hour_steppers[clk_idx].move_to_extra_revs(new_positions_h[clk_idx], 1, extra_revs)
            self.minute_steppers[clk_idx].move_to_extra_revs(new_positions_m[clk_idx], 1, extra_revs)

    async def new_pose_hamiltonian(self, new_positions_h, new_positions_m):
        """Animation: Draws a random continuous Hamiltonian path."""
        path = random.choice(self.hamiltonian_paths)
        
        direction_to_frac = {-8: 0.0, 8: 0.5, -1: 0.75, 1: 0.25}

        for i, clk_index in enumerate(path):
            in_dir = path[i-1] - clk_index if i > 0 else path[i+1] - clk_index
            out_dir = path[i+1] - clk_index if i < len(path) - 1 else path[i-1] - clk_index

            pos_h_frac = direction_to_frac.get(in_dir, 0.0)
            pos_m_frac = direction_to_frac.get(out_dir, 0.5)

            self.hour_steppers[clk_index].move_to(int(pos_h_frac * self.steps_full_rev), 0)
            self.minute_steppers[clk_index].move_to(int(pos_m_frac * self.steps_full_rev), 0)

            await asyncio.sleep(0.2)

        self.clockclock.movement_done_event.clear()
        await self.clockclock.movement_done_event.wait()

        await asyncio.sleep(0.7)

        for i, clk_index in enumerate(path):
            self.hour_steppers[clk_index].move_to(new_positions_h[clk_index], 0)
            self.minute_steppers[clk_index].move_to(new_positions_m[clk_index], 0)

            await asyncio.sleep(0.2)

    async def new_pose_game_of_life(self, new_positions_h, new_positions_m):
        """Animation: Runs Conway's Game of Life."""
        num_generations = 6
        alive_frac = (0.0, 0.0) # Pointing up/down
        dead_frac = (0.25, 0.75) # Horizontal

        # Correct dimensions: 3 rows, 8 columns
        grid = [[random.choice([True, False]) for _ in range(8)] for _ in range(3)]

        for _ in range(num_generations):
            # Display current grid
            # Corrected loop: iterate through 3 rows and 8 columns
            for r in range(3):
                for c in range(8):
                    clk_index = r * 8 + c
                    h_frac, m_frac = alive_frac if grid[r][c] else dead_frac
                    self.hour_steppers[clk_index].move_to(int(h_frac * self.steps_full_rev), 0)
                    self.minute_steppers[clk_index].move_to(int(m_frac * self.steps_full_rev), 0)
            
            self.clockclock.movement_done_event.clear()
            await self.clockclock.movement_done_event.wait()

            # Calculate next state
            new_grid = [[False] * 8 for _ in range(3)]
            # Corrected loop: iterate through 3 rows and 8 columns
            for r in range(3):
                for c in range(8):
                    live_neighbors = 0
                    for dr in [-1, 0, 1]:
                        for dc in [-1, 0, 1]:
                            if dr == 0 and dc == 0: continue
                            nr, nc = r + dr, c + dc
                            # Boundary check must use the correct dimensions
                            if 0 <= nr < 3 and 0 <= nc < 8 and grid[nr][nc]:
                                live_neighbors += 1
                    
                    if grid[r][c] and live_neighbors in [2, 3]: new_grid[r][c] = True
                    elif not grid[r][c] and live_neighbors == 3: new_grid[r][c] = True

            # check if stable
            if new_grid == grid:
                await asyncio.sleep(0.5)
                break
            grid = new_grid

        # Move to final positions
        for clk_index in range(24): # range(len(self.clocks)) is 24
            self.hour_steppers[clk_index].move_to(new_positions_h[clk_index], 0)
            self.minute_steppers[clk_index].move_to(new_positions_m[clk_index], 0)

    async def new_pose_shutter_louver(self, new_positions_h, new_positions_m):
        # clock must move at least a bit, if both stay in the same place both do a full rotation in a random direction
        # minute pointer moves, picks up hour, drops off hours, stops
        # hour and minute assignment is non strict

        # minute moves to hour, drops off hour, stops
        # maximum 1.5 rotations by minute pointer

        # calculate the distances between the minute and hour pointer in the chosen direction
        delays_ms = [0] * 24

        steps_h = [0] * 24
        steps_m = [0] * 24

        directions = [0] * 24

        speed = self.clockclock.current_speed

        final_pos_m = [0] * 24
        final_pos_h = [0] * 24

        for clk_idx in range(24):
            pos_h = self.hour_steppers[clk_idx].current_target_pos % self.steps_full_rev
            pos_m = self.minute_steppers[clk_idx].current_target_pos % self.steps_full_rev

            distance_cw = (pos_h - pos_m) % self.steps_full_rev
            distance_ccw = (pos_m - pos_h) % self.steps_full_rev

            if distance_cw < distance_ccw:
                directions[clk_idx] = 1
            elif distance_cw == distance_ccw:
                directions[clk_idx] = random.choice([-1, 1])
            else:
                directions[clk_idx] = -1

            if directions[clk_idx] == 1:
                distance = distance_cw
            else:
                distance = distance_ccw

            # calculate both distances from from pickup to dropoff
            if directions[clk_idx] == 1:
                distance_pickup_to_dropoff_1 = (new_positions_h[clk_idx] - pos_h) % self.steps_full_rev
                distance_pickup_to_dropoff_2 = (new_positions_m[clk_idx] - pos_h) % self.steps_full_rev
            else:
                distance_pickup_to_dropoff_1 = (pos_h - new_positions_h[clk_idx]) % self.steps_full_rev
                distance_pickup_to_dropoff_2 = (pos_h - new_positions_m[clk_idx]) % self.steps_full_rev

            # hour pointer is dropped off at first non-zero dropoff point, minute pointer at the other one
            if distance_pickup_to_dropoff_1 == 0 and distance_pickup_to_dropoff_2 == 0:
                steps_h[clk_idx] = self.steps_full_rev
                steps_m[clk_idx] = self.steps_full_rev + distance
                final_pos_h[clk_idx] = new_positions_h[clk_idx]
                final_pos_m[clk_idx] = new_positions_m[clk_idx]
            elif distance_pickup_to_dropoff_1 == 0:
                steps_h[clk_idx] = distance_pickup_to_dropoff_2
                steps_m[clk_idx] = self.steps_full_rev + distance
                final_pos_h[clk_idx] = new_positions_m[clk_idx]
                final_pos_m[clk_idx] = new_positions_h[clk_idx]
            elif distance_pickup_to_dropoff_2 == 0:
                steps_h[clk_idx] = distance_pickup_to_dropoff_1
                steps_m[clk_idx] = self.steps_full_rev + distance
                final_pos_h[clk_idx] = new_positions_h[clk_idx]
                final_pos_m[clk_idx] = new_positions_m[clk_idx]
            elif distance_pickup_to_dropoff_1 < distance_pickup_to_dropoff_2:
                steps_h[clk_idx] = distance_pickup_to_dropoff_1
                steps_m[clk_idx] = distance_pickup_to_dropoff_2 + distance
                final_pos_h[clk_idx] = new_positions_h[clk_idx]
                final_pos_m[clk_idx] = new_positions_m[clk_idx]
            else:
                steps_h[clk_idx] = distance_pickup_to_dropoff_2
                steps_m[clk_idx] = distance_pickup_to_dropoff_1 + distance
                final_pos_h[clk_idx] = new_positions_m[clk_idx]
                final_pos_m[clk_idx] = new_positions_h[clk_idx]

            delays_ms[clk_idx] = int(distance / speed * 1000) if speed > 0 else 0

        # create list of incremental hour pointer movement delays with corresponding indices
        # sort list by delay and create corresponding list of clk_indices
        delay_idx_pairs = sorted((delay, idx) for idx, delay in enumerate(delays_ms))
        sorted_delays, sorted_indices = zip(*delay_idx_pairs)

        for clk_idx in range(24):
            self.minute_steppers[clk_idx].move_to_min_steps(final_pos_m[clk_idx], directions[clk_idx], steps_m[clk_idx] - 10)

        prev_delay = 0
        for sorted_idx in range(24):
            clk_idx = sorted_indices[sorted_idx]
            delay_ms = sorted_delays[sorted_idx]

            delay = delay_ms - prev_delay

            if delay > 0:
                await asyncio.sleep_ms(delay)

            self.hour_steppers[clk_idx].move_to_min_steps(final_pos_h[clk_idx], directions[clk_idx], steps_h[clk_idx] - 10)
            prev_delay = delay_ms

    
    async def new_pose_pickup(self, new_positions_h, new_positions_m): 
        # pointers start moving from one of randomly chosen 4 positions (3,6,9,12) into random direction 
        # any pointers at the chosen position start moving immediately in chosen direction, 
        # any pointers in other position start moving with a delay so they are in phase 
        # they then do one full rotation when arriving at initial position 
        # then they move the less than 1*full_rotation in the same direction to their target 
        # i think max amount of rotation will be 2.875 rotations

        speed = self.clockclock.current_speed

        # pick random quadrant (3, 6, 9, 12)
        start_pos = random.choice([self.steps_full_rev // 4 * k for k in (0, 2)])
        direction = random.choice([-1, 1]) # 1 is clockwise, -1 is counterclockwise

        delays_ms = [0] * 48
        min_steps = [0] * 48

        current_pos = [0] * 48
        target_pos = [0] * 48

        for clk_idx in range(24):
            current_pos[clk_idx] = self.hour_steppers[clk_idx].current_target_pos % self.steps_full_rev
            current_pos[clk_idx + 24] = self.minute_steppers[clk_idx].current_target_pos % self.steps_full_rev

            target_pos[clk_idx] = new_positions_h[clk_idx]
            target_pos[clk_idx + 24] = new_positions_m[clk_idx]

        for ptr_idx in range(48):
            pos = current_pos[ptr_idx]

            # distance from start_pos to current_pos
            if direction == 1:
                dist_start_to_pos = (pos - start_pos) % self.steps_full_rev
            else:
                dist_start_to_pos = (start_pos - pos) % self.steps_full_rev

            # delay so all pointers line up at start_pos together
            delays_ms[ptr_idx] = int(dist_start_to_pos / speed * 1000)

            # after delay: move (steps_full_rev - dist_start_to_pos) + 1 full rev + final leg (-10 is just so i dont make some off by 1 error that forces a full rotation, i dont think its needed but it doesnt hurt)
            min_steps[ptr_idx] = (self.steps_full_rev - dist_start_to_pos) + self.steps_full_rev - 10

        # phase 1: wait for delays and start both pointers together
        delay_idx_pairs = sorted((delay, idx) for idx, delay in enumerate(delays_ms))
        sorted_delays, sorted_indices = zip(*delay_idx_pairs)

        prev_delay = 0
        for sorted_idx in range(48):
            ptr_idx = sorted_indices[sorted_idx]
            delay_ms = sorted_delays[sorted_idx]

            delta = delay_ms - prev_delay
            if delta > 0:
                await asyncio.sleep_ms(delta)

            # launch both hour and minute pointer moves, min steps means at least this many steps will be done when moving to target
            if ptr_idx < 24:
                self.hour_steppers[ptr_idx].move_to_min_steps(target_pos[ptr_idx], direction, min_steps[ptr_idx])
            else:
                self.minute_steppers[ptr_idx - 24].move_to_min_steps(target_pos[ptr_idx], direction, min_steps[ptr_idx])

            prev_delay = delay_ms

