import machine
import time
import random
from ClockStepper import ClockStepper
from DigitDisplay import DigitDisplay
from ClockModule import ClockModule

class ClockClock24:
    stepper_speed_default = 600
    stepper_accel_default = 250
    
    stepper_speed_stealth = 150
    stepper_accel_stealth = 70
    
    stepper_speed_analog = 70
    stepper_accel_analog = 50
    
    modes = {
      "sleep": 0,
      "stealth": 1,
      "shortest path": 3, #move to new poosition with shortest path
      "visual": 2, #every timechange has choreographies and stuff
      "analog": 4 # every clock is a normal clock
      }
    
    def __init__(self, slave_adr_list: List[int], i2c_bus_list: List[machine.I2C], mode, steps_full_rev = 4320):
        self.steps_full_rev = steps_full_rev
        
        self.clock_modules = [ClockModule(i2c_bus_list[module_index], slave_adr_list[module_index], steps_full_rev) for module_index in range(len(slave_adr_list))]
        
        self.minute_steppers = [stepper for stepper_list in (module.minute_steppers for module in self.clock_modules) for stepper in stepper_list]
        self.hour_steppers = [stepper for stepper_list in (module.hour_steppers for module in self.clock_modules) for stepper in stepper_list]
        
        self.digit_display = DigitDisplay(self)

        self.mode_change_handlers = [self.__sleep, self.__stealth, self.__shortest_path, self.__visual, self.__analog]
        self.time_change_handlers = [self.__sleep_new_time, self.__stealth_new_time, self.__shortest_path_new_time, self.__visual_new_time, self.__analog_new_time]
        self.time_handler = None
        self.__current_mode = -1
        self.set_mode(mode)
        
    def set_mode(self, mode: int):
        if self.__current_mode != -1:
            self.mode_change_handlers[self.__current_mode](False) # "destructor" of old mode
            
        self.__current_mode = mode
        self.time_handler = self.time_change_handlers[self.__current_mode]
        self.mode_change_handlers[self.__current_mode](True) # specific initialisation of new mode
        
    def get_mode(self):
        return self.__current_mode
    
    def display_digit(self, field: int, number: int, direction = 0, extra_revs = 0):
        self.digit_display.display_digit(field, number, direction, extra_revs)
    
    def display_time(self, hour: int, minute: int):
        self.time_handler(hour, minute)
        
    def __sleep(self, start: bool):
        if start:
            self.set_speed_all(ClockClock24.stepper_speed_default)
            self.set_accel_all(ClockClock24.stepper_speed_default)
            
            self.move_to_all(int(0.5*self.steps_full_rev))
            
            time.sleep(0.2) # just to be sure all slaves had time to start moving, probably not needed but doesnt hurt
            
            while self.is_running():
                time.sleep(0.2)
                
            self.enable_disable_driver(False)
        else:
            self.enable_disable_driver(True)
    
    def __stealth(self, start: bool):
        if start:
            self.set_speed_all(ClockClock24.stepper_speed_stealth)
            self.set_accel_all(ClockClock24.stepper_speed_stealth)
    
    def __shortest_path(self, start: bool):
        if start:
            self.set_speed_all(ClockClock24.stepper_speed_default)
            self.set_accel_all(ClockClock24.stepper_speed_default)
    
    def __visual(self, start: bool):
        if start:
            self.set_speed_all(ClockClock24.stepper_speed_default)
            self.set_accel_all(ClockClock24.stepper_speed_default)
    
    def __analog(self, start: bool):
        if start:
            self.set_speed_all(ClockClock24.stepper_speed_analog)
            self.set_accel_all(ClockClock24.stepper_speed_analog)
        
    def __sleep_new_time(self, hour: int, minute: int):
        return
    
    def __stealth_new_time(self, hour: int, minute: int):
        """New time handler for stealth display option (minimized movements)
        gets called by display_time if this is the selected mode
        
        Parameters
        ----------
        hour : int
            hour to display
        minute : int
            to display
        """
        digits = [hour//10, hour%10, minute//10, minute%10]
        self.digit_display.display_digits(digits, DigitDisplay.animations["stealth"])
        
    def __shortest_path_new_time(self, hour: int, minute: int):
        """New time handler for visual display option (choreography transitions)
        gets called by display_time if this is the selected mode
        
        Parameters
        ----------
        hour : int
            hour to display
        minute : int
            to display
        """
        digits = [hour//10, hour%10, minute//10, minute%10]
        self.digit_display.display_digits(digits, DigitDisplay.animations["shortest path"])
        
    def __visual_new_time(self, hour: int, minute: int):
        """New time handler for visual display option (choreography transitions)
        gets called by display_time if this is the selected mode
        
        Parameters
        ----------
        hour : int
            hour to display
        minute : int
            to display
        """
        digits = [hour//10, hour%10, minute//10, minute%10]
        animation_indeces = [DigitDisplay.animations["extra revs"],
                             DigitDisplay.animations["straight wave"],
                             DigitDisplay.animations["opposing pointers"],
                             DigitDisplay.animations["focus"],
                             DigitDisplay.animations["opposites"]]
        
        self.digit_display.display_digits(digits, random.choice(animation_indeces))
    
    def __analog_new_time(self, hour: int, minute: int):
        """New time handler for analog display option (each clock is an analog clock)
        gets called by display_time if this is the selected mode    
        
        Parameters
        ----------
        hour : int
            hour to display
        minute : int
            to display
        """
        for stepper in self.minute_steppers:
            stepper.move_to(int(self.steps_full_rev/60 * minute), 0)
            
        for stepper in self.hour_steppers:
            stepper.move_to(int(self.steps_full_rev/12 * (hour%12 + minute/60)), 0)
        
    #commands
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
    
    def move_to_all(self, position: int, direction = 0):
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
    
