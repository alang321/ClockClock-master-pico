import math
import random
import uasyncio as asyncio

#a weird class that pretty much just prvoides the correct pointer positions for each digit
#takes into account the current settings such as one style and eight style
class ClockDigitPointerPositions:
    # fractional position of the pointer, first sublist is hour hand second is minute hand, 0.0 at the 12 o clock position and 0.5 at 6 o clock
    # from top left, rows first
    digits_pointer_pos =  [[[[0.5, 0.5, 0.5, 0.5, 0.25, 0.75],    [0.25, 0.75, 0, 0, 0, 0]]],                 # 0
                            [[[None, 0.5, 0.125, 0, None, 0],    [None, None, 0.125, 0.5, None, 0]],      # 1 - with angled line at top
                                    [[None, 0.5, None, 0, None, 0],    [None, 0.5, None, 0.5, None, 0]]],   # 1 - classic seven segment diplay straight line
                            [[[0.25, 0.75, 0.5, 0.75, 0.25, 0.75], [0.25, 0.5, 0.25, 0, 0, 0.75]]],            # 2
                            [[[0.25, 0.75, 0.25, 0, 0.25, 0.75],   [0.25, 0.5, 0.25, 0.75, 0.25, 0]]],         # 3
                            [[[0.5, 0.5, 0, 0, None, 0],          [0.5, 0.5, 0.25, 0.5, None, 0]]],          # 4
                            [[[0.25, 0.75, 0, 0.5, 0.25, 0],       [0.5, 0.75, 0.25, 0.75, 0.25, 0.75]]],      # 5
                            [[[0.5, 0.75, 0, 0.75, 0, 0],          [0.25, 0.75, 0.5, 0.5, 0.25, 0.75]]],       # 6
                            [[[0.25, 0.5, None, 0.5, None, 0],   [0.25, 0.75, None, 0, None, 0]]],         # 7
                            [[[0.5, 0.5, 0, 0, 0, 0],              [0.25, 0.75, 0.25, 0.75, 0.25, 0.75]],      # 8 - upper circle
                                    [[0.25, 0.75, 0.5, 0.5, 0, 0],        [0.5, 0.5, 0.25, 0.75, 0.25, 0.75]],    # 8 - lower circle
                                    [[0.5, 0.5, 0.25, 0, 0, 0],           [0.25, 0.75, 0.5, 0.75, 0.25, 0.75]]],  # 8 - mirrored s
                            [[[0.5, 0.5, 0.25, 0.5, 0.25, 0],      [0.25, 0.75, 0, 0, 0.25, 0.75]]]]           # 9  

    def __init__(self, clockclock):
        self.clockclock = clockclock
        self.steps_full_rev = self.clockclock.settings.steps_full_rev

        #excuse this horribleness
        #just converts the fractional pointer positions to absolute positions in steps
        #while keeping None values for digits that have a configurable zero position there
        self.digits_pointer_pos_abs = self.digits_pointer_pos_abs = [[[[None if frac is None else int(frac * self.steps_full_rev) for frac in hour_minute] for hour_minute in digit_option] for digit_option in number] for number in self.digits_pointer_pos]

        self.persistent_idx_eight_style = self.clockclock.settings.persistent.get_index("eight style")
        self.persistent_idx_one_style = self.clockclock.settings.persistent.get_index("one style")
        self.persistent_idx_idle_pos = self.clockclock.settings.persistent.get_index("Idle Pointer Pos")

        self.default_positions_lst = [int(x * 0.25 * self.steps_full_rev) for x in range(8)]
        self.number_style_options = [0] * 10

    def get_digit(self, digit):
        default_pos_abs = self.default_positions_lst[self.clockclock.settings.persistent.get_var_by_index(self.persistent_idx_idle_pos)]

        self.number_style_options[1] = self.clockclock.settings.persistent.get_var_by_index(self.persistent_idx_one_style)
        self.number_style_options[8] = self.clockclock.settings.persistent.get_var_by_index(self.persistent_idx_eight_style)

        tmp = self.digits_pointer_pos_abs[digit][self.number_style_options[digit]]
        return [default_pos_abs if pos is None else pos for pos in tmp]

    

class ClockDigitDisplay:
    digit_field_indices = [[0, 1, 8, 9, 16, 17], [2, 3, 10, 11, 18, 19], [4, 5, 12, 13, 20, 21], [6, 7, 14, 15, 22, 23]]
    centered_digit_field_indices = [[1, 2, 9, 10, 17, 18], [3, 4, 11, 12, 19, 20], [5, 6, 13, 14, 21, 22]]
    column_indices = [[0, 8, 16], [1, 9, 17], [2, 10, 18], [3, 11, 19], [4, 12, 20], [5, 13, 21], [6, 14, 22], [7, 15, 23]]
    row_indices = [[0, 1, 2, 3, 4, 5, 6, 7], [8, 9, 10, 11, 12, 13, 14, 15], [16, 17, 18, 19, 20, 21, 22, 23]]
    
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
      }
    
    def __init__(self, clockclock):
        """
        Parameters
        ----------
        clockclock
            a ClockClock24 obj, basically the "master"
        """
        self.clockclock = clockclock
        
        self.hour_steppers = self.clockclock.steppers.hour_steppers
        self.minute_steppers = self.clockclock.steppers.minute_steppers
        self.stepper_clocks = self.clockclock.steppers.stepper_clocks
        
        self.steps_full_rev = self.clockclock.settings.steps_full_rev
        
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
            self.new_pose_uhrenspiel
          ]
        
        self.digit_pointer_positions = ClockDigitPointerPositions(self.clockclock)
        
    def display_mode(self, mode_id):
        mode_id += 1 # so modes are displayed from 1 not from 0
        mode_id %= 10000
        mode_string = str(mode_id)
        digit_count = len(str(mode_string))

        default_pos_left = int(self.steps_full_rev * 0.75)
        default_pos_right = int(self.steps_full_rev * 0.25)
        new_positions_0 = [default_pos_left] * 24
        new_positions_1 = [default_pos_left] * 24

        #turn all clocks on the right side to the right
        for col in self.column_indices[4:]:
            for clk_index in col:
                new_positions_0[clk_index] = default_pos_right
                new_positions_1[clk_index] = default_pos_right

        #make the digits always centered
        if digit_count == 1:
            field_array = self.centered_digit_field_indices
            field_indeces = [1]
        elif digit_count == 2:
            field_array = self.digit_field_indices
            field_indeces = [1, 2]
        elif digit_count == 3:
            field_array = self.centered_digit_field_indices
            field_indeces = [0, 1, 2]
        elif digit_count == 4:
            field_array = self.digit_field_indices
            field_indeces = [0, 1, 2, 3]
            
        for digit_id, field_idx in enumerate(field_indeces):
            digit = int(mode_string[digit_id])
            
            digit_pointer_positions = self.digit_pointer_positions.get_digit(digit)
            for sub_index, clk_index in enumerate(field_array[field_idx]):
                new_positions_0[clk_index] = digit_pointer_positions[0][sub_index]
                new_positions_1[clk_index] = digit_pointer_positions[1][sub_index]
                
        self.__new_pose_stealth(new_positions_0, new_positions_1)
                 
    def display_number(self, number, left_align=False):
        number %= 10000
        mode_string = str(number)
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
                
            digit_pointer_positions = self.digit_pointer_positions.get_digit(digit)
            for sub_index, clk_index in enumerate(self.digit_field_indices[field]):
                new_positions_0[clk_index] = digit_pointer_positions[0][sub_index]
                new_positions_1[clk_index] = digit_pointer_positions[1][sub_index]
                
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
            digit_pointer_positions = self.digit_pointer_positions.get_digit(digit)
            for sub_index, clk_index in enumerate(ClockDigitDisplay.digit_field_indices[field]):
                new_positions_h[clk_index] = digit_pointer_positions[0][sub_index]
                new_positions_m[clk_index] = digit_pointer_positions[1][sub_index]
        
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
            self.stepper_clocks[clk_index].moveTo_minimize_movement(new_positions_0[clk_index], new_positions_1[clk_index])
    
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
        
        self.clockclock.steppers.move_to_all(start_pos_h, 0, minute=False)
        self.clockclock.steppers.move_to_all(start_pos_m, 0, hour=False)

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
        
        self.clockclock.steppers.move_to_all(start_pos, 0)
        
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
        start_delays = [0] * len(ClockDigitDisplay.column_indices)
        col_indices = list(range(len(ClockDigitDisplay.column_indices)))
        #calculate time delay of each column to point to scale start time    
        for col_index in col_indices:
            loc_y = -col_index
            point_y = point[1]
            distance = abs(point_y - loc_y)
            
            start_delays[col_index] = int(distance * delay_per_distance)

        parallel_sorted = sorted(zip(start_delays, ClockDigitDisplay.column_indices))
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
        
        self.clockclock.steppers.move_to_all(startpos_h, 0, minute=False)
        self.clockclock.steppers.move_to_all(startpos_m, 0, hour=False)
        
        self.clockclock.movement_done_event.clear()
        await self.clockclock.movement_done_event.wait()
        self.clockclock.steppers.set_accel_all(750)
        
        for i in range(len(speed)):
            self.clockclock.steppers.set_speed_all(speed[i])
            #self.clockclock.set_accel_all(accel[i])
            
            self.clockclock.steppers.move_to_all(targetpos_h[i], 0, minute=False)
            self.clockclock.steppers.move_to_all(targetpos_m[i], 0, hour=False)
            
            self.clockclock.movement_done_event.clear()
            try:
                await self.clockclock.movement_done_event.wait()
            except asyncio.CancelledError:
                self.clockclock.steppers.set_speed_all(oldspeed) # only gets called when task is cancelled
                self.clockclock.steppers.set_accel_all(oldaccel)
                raise
    
        self.clockclock.steppers.set_speed_all(oldspeed)
        self.clockclock.steppers.set_accel_all(oldaccel)
        
        await asyncio.sleep_ms(1000)
            
        for clk_index in range(24):
            self.hour_steppers[clk_index].move_to(new_positions_h[clk_index], 0)
            self.minute_steppers[clk_index].move_to(new_positions_m[clk_index], 0)
        