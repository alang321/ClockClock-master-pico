import machine
from ClockStepper import ClockStepper
from DigitDisplay import DigitDisplay
from ClockModule import ClockModule

class ClockClock24:
    digit_display_indeces = [[0, 1, 8, 9, 16, 17], [2, 3, 10, 11, 18, 19], [4, 5, 12, 13, 20, 21], [6, 7, 14, 15, 22, 23]]
    
    def __init__(self, slave_adr_list: List[int], i2c_bus_list: List[machine.I2C], steps_full_rev = 4320):
        self.steps_full_rev = steps_full_rev
        
        self.clock_modules = [ClockModule(i2c_bus_list[module_index], slave_adr_list[module_index]) for module_index in range(len(slave_adr_list))]
        
        self.minute_steppers = [ClockStepper(clk_id%4, self.clock_modules[clk_id//4], self.steps_full_rev) for clk_id in range(24)]
        self.hour_steppers = [ClockStepper((clk_id%4 + 4), self.clock_modules[clk_id//4], self.steps_full_rev) for clk_id in range(24)]
        
        self.digit_displays = [DigitDisplay([self.minute_steppers[i] for i in clk_index_list], [self.hour_steppers[i] for i in clk_index_list], steps_full_rev) for clk_index_list in ClockClock24.digit_display_indeces]
        
    def display_digit(self, index: int, number: int):
        self.digit_displays[index].display(number)
        
    def enable_disable_driver(self, enable_disable: bool):
        """
        true to enable driver of module
        false to disable
        """
        for module in self.clock_modules:
            module.enable_disable_driver_module(enable_disable)
    
    def set_speed_all(self, speed: int):
        for module in self.clock_modules:
            module.set_speed_module(speed)
    
    def set_accel_all(self, accel: int):
        for module in self.clock_modules:
            module.set_accel_module(accel)
    
    def move_to_all(self, position: int, direction: int):
        for module in self.clock_modules:
            module.move_to_module(position, direction)
    
    def move_to_extra_revs_all(self, position: int, direction: int, extra_revs: int):
        for module in self.clock_modules:
            module.move_to_extra_revs_module(position, direction, extra_revs)
    
    def move_all(self, distance: int, direction: int):
        for module in self.clock_modules:
            module.move_module(distance, direction)
        
    def stop_all(self):
        for module in self.clock_modules:
            module.stop_module()
    
    def falling_pointer(self):
        for module in self.clock_modules:
            module.falling_pointer_module()

    def is_running(self) -> bool: #returns True if stepper is running
        for module in self.clock_modules:
            if module.is_running_module():
                return True
        
        return False
