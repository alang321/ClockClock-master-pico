import machine
import time
import random
import ucollections
from ClockStepperModule import ClockStepper
from ClockStepperModule import ClockModule
from DigitDisplay import DigitDisplay
import uasyncio as asyncio

class ClockClock24:
    #fast speed used when showing mode numbers and similar
    stepper_speed_fast = 700
    stepper_accel_fast = 450
    
    #normal speed used in most modes
    stepper_speed_default = 585
    stepper_accel_default = 200
    
    #used in stealth mode
    stepper_speed_stealth = 150
    stepper_accel_stealth = 50
    
    #used in analog mode
    stepper_speed_analog = 70
    stepper_accel_analog = 50
    
    modes = {
      "stealth": 0,
      "visual": 1, #every timechange has choreographies and stuff
      "shortest path": 2, #move to new poosition with shortest path
      "analog": 3, # every clock is a normal clock
      "change time": 4, # mode geared towards changing time, fast and minimal movements to display time
      "sleep": 5 # move all steppers to 6 o clock (default) position and disable stepper drivers
      }
    
    def __init__(self, slave_adr_list, i2c_bus_list, mode, steps_full_rev = 4320):
        self.steps_full_rev = steps_full_rev
        
        self.visual_animation_ids = [DigitDisplay.animations["extra revs"], #these get shuffled randomly when ever at end of list
                                     DigitDisplay.animations["straight wave"],
                                     DigitDisplay.animations["opposing pointers"],
                                     DigitDisplay.animations["focus"],
                                     DigitDisplay.animations["opposites"],
                                     DigitDisplay.animations["field lines"],
                                     DigitDisplay.animations["equipotential"],
                                     DigitDisplay.animations["speedy clock"]]
        self.random_shuffle(self.visual_animation_ids)
        self.animation_index = 0

        #asyncio
        self.async_display_task = None  # currently running asynchronous task that has to be cancelled
        self.async_mode_change_task = None  # currently running asynchronous task that has to be cancelled

        self.movement_done_event = asyncio.Event()
        
        self.clock_modules = [ClockModule(i2c_bus_list[module_index], slave_adr_list[module_index], steps_full_rev) for module_index in range(len(slave_adr_list))]
        
        self.minute_steppers = [stepper for stepper_list in (module.minute_steppers for module in self.clock_modules) for stepper in stepper_list]
        self.hour_steppers = [stepper for stepper_list in (module.hour_steppers for module in self.clock_modules) for stepper in stepper_list]
        
        self.digit_display = DigitDisplay(self)

        self.mode_change_handlers = [self.__stealth, self.__visual, self.__shortest_path, self.__analog, self.__change_time, self.__sleep]
        self.time_change_handlers = [self.__stealth_new_time,
                                     self.__visual_new_time,
                                     self.__shortest_path_new_time,
                                     self.__analog_new_time,
                                     self.__change_time_new_time,
                                     self.__no_new_time]
        self.time_handler = None
        self.__current_mode = -1
        self.current_speed = -1
        self.current_accel = -1
        self.set_mode(mode)

    def cancel_tasks(self):
        self.async_display_task.cancel()
        self.async_mode_change_task.cancel()

    async def run(self):
        if not self.is_running():
            self.movement_done_event.set()
        await asyncio.sleep(0)
        
    def display_digit(self, field: int, number: int, direction=0, extra_revs=0):
        self.cancel_tasks()
        self.digit_display.display_digit(field, number, direction, extra_revs)
    
    def display_time(self, hour: int, minute: int):
        self.time_handler(hour, minute)
        
    def swap(self, index: int):
        minute_pos = self.minute_steppers[index].current_target_pos
        hour_pos = self.hour_steppers[index].current_target_pos
        
        if minute_pos == -1 or hour_pos == -1:
            return
        
        self.minute_steppers[index].move_to(hour_pos, 0)
        self.hour_steppers[index].move_to(minute_pos, 0)

    def set_mode(self, mode: int):
        self.async_mode_change_task = asyncio.create_task(self.__set_mode(mode))
        
    async def __set_mode(self, mode: int):
        if __debug__:
            print("New mode:", mode)
        
        self.cancel_tasks()
        self.__current_mode = mode
        self.time_handler = self.__no_new_time # an empty time handler so a new time doesnt interrupt the displaying of the current mode
        
        self.enable_disable_driver(True)
        self.set_speed_all(ClockClock24.stepper_speed_fast)
        self.set_accel_all(ClockClock24.stepper_accel_fast)
        self.digit_display.display_digits([0, 0, 0, self.__current_mode], DigitDisplay.animations["stealth"])

        await self.movement_done_event.wait()
        self.movement_done_event.clear()

        self.mode_change_handlers[self.__current_mode]() # specific initialisation of new mode after display of mode digit is done
        
    def get_mode(self):
        return self.__current_mode
    
    def __stealth(self):
        self.time_handler = self.time_change_handlers[self.__current_mode]
        self.set_speed_all(ClockClock24.stepper_speed_stealth)
        self.set_accel_all(ClockClock24.stepper_accel_stealth)
    
    def __shortest_path(self):
        self.time_handler = self.time_change_handlers[self.__current_mode]
        self.set_speed_all(ClockClock24.stepper_speed_default)
        self.set_accel_all(ClockClock24.stepper_accel_default)
    
    def __visual(self):
        self.time_handler = self.time_change_handlers[self.__current_mode]
        self.set_speed_all(ClockClock24.stepper_speed_default)
        self.set_accel_all(ClockClock24.stepper_accel_default)
    
    def __analog(self):
        self.time_handler = self.time_change_handlers[self.__current_mode]
        self.set_speed_all(ClockClock24.stepper_speed_analog)
        self.set_accel_all(ClockClock24.stepper_accel_analog)
    
    def __change_time(self):
        self.time_handler = self.time_change_handlers[self.__current_mode]
        self.set_speed_all(ClockClock24.stepper_speed_fast)
        self.set_accel_all(ClockClock24.stepper_accel_fast)
        
    def __sleep(self):
        self.time_handler = self.time_change_handlers[self.__current_mode]
        self.set_speed_all(ClockClock24.stepper_speed_default)
        self.set_accel_all(ClockClock24.stepper_accel_default)
        
        self.move_to_all(int(0.5*self.steps_full_rev))
    
    def __stealth_new_time(self, hour: int, minute: int):
        self.cancel_tasks()
        digits = [hour//10, hour%10, minute//10, minute%10]
        self.digit_display.display_digits(digits, DigitDisplay.animations["stealth"])
        
    def __shortest_path_new_time(self, hour: int, minute: int):
        self.cancel_tasks()
        digits = [hour//10, hour%10, minute//10, minute%10]
        self.digit_display.display_digits(digits, DigitDisplay.animations["shortest path"])
        
    def __visual_new_time(self, hour: int, minute: int):
        self.cancel_tasks()
        digits = [hour//10, hour%10, minute//10, minute%10]
        
        if __debug__:
            print("animation id:", self.visual_animation_ids[self.animation_index])
            
        self.digit_display.display_digits(digits, self.visual_animation_ids[self.animation_index])
        
        self.animation_index += 1
        
        if self.animation_index == len(self.visual_animation_ids):
            self.animation_index = 0
            self.random_shuffle(self.visual_animation_ids)     
    
    def __analog_new_time(self, hour: int, minute: int):
        self.cancel_tasks()
        for stepper in self.minute_steppers:
            stepper.move_to(int(self.steps_full_rev/60 * minute), 0)
            
        for stepper in self.hour_steppers:
            stepper.move_to(int(self.steps_full_rev/12 * (hour%12 + minute/60)), 0)
    
    def __change_time_new_time(self, hour: int, minute: int):
        self.cancel_tasks()
        digits = [hour//10, hour%10, minute//10, minute%10]
        self.digit_display.display_digits(digits, DigitDisplay.animations["stealth"])
        
    def __no_new_time(self, hour: int, minute: int):
        return
        
    #commands
    def enable_disable_driver(self, enable_disable: bool):
        """
        true to enable driver of module
        false to disable
        """
        for module in self.clock_modules:
            module.enable_disable_driver_module(enable_disable)
    
    def set_speed_all(self, speed: int):
        self.current_speed = speed
        for module in self.clock_modules:
            module.set_speed_module(speed)
    
    def set_accel_all(self, accel: int):
        self.current_accel = accel
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
    
    @staticmethod
    def random_shuffle(seq):
        l = len(seq)
        for i in range(l):
            j = random.randrange(l)
            seq[i], seq[j] = seq[j], seq[i]
    
