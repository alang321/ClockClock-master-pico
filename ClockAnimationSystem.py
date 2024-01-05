class ClockAnimationSystem:
    animations_ids = {
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
        self.clockclock = clockclock

    def new_pose(new_positions_h, new_positions_m, animation)
        
