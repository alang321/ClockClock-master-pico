from struct import pack
import machine

#region clock clock

class ClockSteppers:
    def __init__(self, i2c_bus_lst: machine.I2C, i2c_address_lst: int, steps_full_rev: int):
        self.steps_full_rev = steps_full_rev
        self.i2c_bus_lst = i2c_bus_lst
        self.i2c_address_lst = i2c_address_lst
            
        # commands a specific set of steppers
        self.stepper_modules = [StepperModule(i2c_bus, i2c_address, steps_full_rev) for i2c_address, i2c_bus in zip(self.i2c_address_lst, i2c_bus_lst)]

        self.stepper_clocks = [clock for clock_list in (module.clocks for module in self.stepper_modules) for clock in clock_list]
        self.minute_steppers = [stepper for stepper_list in (module.minute_steppers for module in self.stepper_modules) for stepper in stepper_list]
        self.hour_steppers = [stepper for stepper_list in (module.hour_steppers for module in self.stepper_modules) for stepper in stepper_list]

        self.current_speed = -1 #will get set in init function of ClockCLOCK"$ module via set_mode_all
        self.current_accel = -1

    def enable_disable_driver_all(self, enable_disable: bool):
        """
        true to enable driver of module
        false to disable
        """
        for module in self.stepper_modules:
            module.enable_disable_driver(enable_disable)

    def is_running_all(self, minute=True, hour=True) -> bool: #returns True if stepper is running
        for module in self.stepper_modules:
            if module.is_running(minute, hour):
                return True
        
        return False

    def set_speed_all(self, speed: int, minute=True, hour=True):
        if hour == minute:
            self.current_speed = speed
            for module in self.stepper_modules:
                module.all_steppers.set_speed(speed)
        elif hour:
            for module in self.stepper_modules:
                module.all_hour_steppers.set_speed(speed)
        elif minute:
            for module in self.stepper_modules:
                module.all_minute_steppers.set_speed(speed)

    def set_accel_all(self, accel: int, minute=True, hour=True):
        if hour == minute:
            self.current_accel = accel
            for module in self.stepper_modules:
                module.all_steppers.set_accel(accel)
        elif hour:
            for module in self.stepper_modules:
                module.all_hour_steppers.set_accel(accel)
        elif minute:
            for module in self.stepper_modules:
                module.all_minute_steppers.set_accel(accel)

    def move_to_all(self, position: int, direction = 0, minute=True, hour=True):
        if hour == minute:
            for module in self.stepper_modules:
                module.all_steppers.move_to(position, direction)
        elif hour:
            for module in self.stepper_modules:
                module.all_hour_steppers.move_to(position, direction)
        elif minute:
            for module in self.stepper_modules:
                module.all_minute_steppers.move_to(position, direction)

    def move_to_extra_revs_all(self, position: int, direction: int, extra_revs: int, minute=True, hour=True):
        if hour == minute:
            for module in self.stepper_modules:
                module.all_steppers.move_to_extra_revs(position, direction, extra_revs)
        elif hour:
            for module in self.stepper_modules:
                module.all_hour_steppers.move_to_extra_revs(position, direction, extra_revs)
        elif minute:
            for module in self.stepper_modules:
                module.all_minute_steppers.move_to_extra_revs(position, direction, extra_revs)

    def moveTo_min_steps_all(self, position: int, direction: int, min_steps: int, minute=True, hour=True): 
        if hour == minute:
            for module in self.stepper_modules:
                module.all_steppers.move_to_min_steps(position, direction, min_steps)
        elif hour:
            for module in self.stepper_modules:
                module.all_hour_steppers.move_to_min_steps(position, direction, min_steps)
        elif minute:
            for module in self.stepper_modules:
                module.all_minute_steppers.move_to_min_steps(position, direction, min_steps)

    def move_all(self, distance: int, direction: int, minute=True, hour=True):
        if hour == minute:
            for module in self.stepper_modules:
                module.all_steppers.move(distance, direction)
        elif hour:
            for module in self.stepper_modules:
                module.all_hour_steppers.move(distance, direction)
        elif minute:
            for module in self.stepper_modules:
                module.all_minute_steppers.move(distance, direction)
        
    def stop_all(self, minute=True, hour=True):
        if hour == minute:
            for module in self.stepper_modules:
                module.all_steppers.stop()
        elif hour:
            for module in self.stepper_modules:
                module.all_hour_steppers.stop()
        elif minute:
            for module in self.stepper_modules:
                module.all_minute_steppers.stop()

#endregion

#region stepper module

class StepperModule: # module for 1 of the 6 pcbs in the clock    
    stepper_selector = {"minute":-3,
                        "hour": -2,
                        "all": -1}
    
    def __init__(self, i2c_bus: machine.I2C, i2c_address: int, steps_full_rev: int):
        self.steps_full_rev = steps_full_rev
        self.i2c_bus = i2c_bus
        self.i2c_address = i2c_address
        self.is_driver_enabled = True

        self.clocks = [StepperClock(self, sub_clock_idx, self.steps_full_rev) for sub_clock_idx in range(3)]

        self.minute_steppers = [clock.stepper_m for clock in self.clocks]
        self.hour_steppers = [clock.stepper_h for clock in self.clocks]
        
        # commands a specific set of steppers
        self.all_steppers = Stepper(self.stepper_selector["all"], self, self.steps_full_rev) 
        self.all_hour_steppers = Stepper(self.stepper_selector["hour"], self, self.steps_full_rev)
        self.all_minute_steppers = Stepper(self.stepper_selector["minute"], self, self.steps_full_rev)
        
    def enable_disable_driver(self, enable_disable: bool):
        buffer = pack("<BB", CommandIDs.enable_driver, int(enable_disable)) #cmd_id uint8, enable uint8         
        
        self.i2c_write(buffer)
            
        self.is_driver_enabled = enable_disable
    
    def is_running(self, minute=True, hour=True) -> bool: #returns True if stepper is running
        buffer = self.i2c_read(1)
        
        # 8 bits, first 4 bits are minute, second 4 bits are hour
        if hour == minute:
            return (buffer[0] != 0)
        elif hour:
            return (buffer[0] & 0b00001111 != 0)
        elif minute:
            return (buffer[0] & 0b11110000 != 0)
    
    def i2c_write(self, buffer):
        checksum = self.calculate_Checksum(buffer)
        buffer += pack("<B", checksum)

        if __debug__:
            try:
                self.i2c_bus.writeto(self.i2c_address, buffer)
            except:
                print("Slave not found:", self.i2c_address, " Data:", buffer)
        else:
            self.i2c_bus.writeto(self.i2c_address, buffer)
    
    def i2c_read(self, byte_count):
        if __debug__:
            try:
                return self.i2c_bus.readfrom(self.i2c_address, byte_count)
            except:
                print("Slave not found:", self.i2c_address, "Tried to read ", byte_count, "byte(s)")
                return (0,)
        else:
            return self.i2c_bus.readfrom(self.i2c_address, byte_count)
        
    def calculate_Checksum(self, buffer):
        checksum = sum(buffer[i] for i in range(len(buffer))) % 256

        return checksum

#endregion
    
#region Single Stepper Clock
    
class StepperClock:
    def __init__(self, module: StepperModule, sub_clock_idx: int, steps_full_rev: int):
        self.steps_full_rev = steps_full_rev
        self.module = module
        self.sub_clock_idx = sub_clock_idx
            
        self.stepper_m = Stepper(0 + sub_clock_idx, self.module, self.steps_full_rev)
        self.stepper_h = Stepper(4 + sub_clock_idx, self.module, self.steps_full_rev)
    
    def moveTo_minimize_movement(self, pos1: int, pos2: int):
        buffer = pack("<Bhhb", CommandIDs.moveTo_minimize_movement, pos1, pos2, self.sub_clock_idx) #cmd_id uint8, pos1 int16, pos2 int16, sub_clock_idx int8

        self.module.i2c_write(buffer)

    def is_running(self) -> bool: #returns True if a stepper inside the clock is running
        buffer = self.module.i2c_read(1)

        sub_id_1 = self.stepper_m.sub_stepper_id
        sub_id_2 = self.stepper_h.sub_stepper_id

        return ((1 << sub_id_1) & buffer[0] != 0) or ((1 << sub_id_2) & buffer[0] != 0)

#endregion
        
#region clock stepper

class Stepper:
    def __init__(self, sub_stepper_id: int, module: StepperModule, steps_per_rev: int):
        self.module = module
        self.sub_stepper_id = sub_stepper_id
        self.steps_per_rev = steps_per_rev
        
    def set_speed(self, speed: int):
        buffer = pack("<BHb", CommandIDs.set_speed, speed, self.sub_stepper_id) #cmd_id uint8, speed uint16, stepper_id int8           
        
        self.module.i2c_write(buffer)
    
    def set_accel(self, accel: int):
        buffer = pack("<BHb", CommandIDs.set_accel, accel, self.sub_stepper_id) #cmd_id uint8, accel uint16, stepper_id int8           

        self.module.i2c_write(buffer)
    
    def move_to(self, position: int, direction: int):
        buffer = pack("<Bhbb", CommandIDs.moveTo_extra_revs, position, direction, self.sub_stepper_id) #cmd_id uint8, position int16, dir int8, stepper_id int8           
        
        self.module.i2c_write(buffer)
    
    def move_to_extra_revs(self, position: int, direction: int, extra_revs: int):
        buffer = pack("<BhbBb", CommandIDs.moveTo_extra_revs, position, direction, extra_revs, self.sub_stepper_id) #cmd_id uint8, position int16, dir int8, extra_revs uint8, stepper_id int8           
        
        self.module.i2c_write(buffer)
    
    def move_to_min_steps(self, position: int, direction: int, min_steps: int):
        buffer = pack("<BhbHb", CommandIDs.moveTo_min_steps, position, direction, min_steps, self.sub_stepper_id) #cmd_id uint8, position int16, dir int8, min_steps uint16, stepper_id int8           
        
        self.module.i2c_write(buffer)
    
    def move(self, distance: int, direction: int):
        buffer = pack("<BHbb", CommandIDs.move, distance, direction, self.sub_stepper_id) #cmd_id uint8, distance uint16, dir int8, stepper_id int8           
        
        self.module.i2c_write(buffer)
        
    def stop(self):
        buffer = pack("<Bb", CommandIDs.stop, self.sub_stepper_id) #cmd_id uint8, stepper_id int8     
        
        self.module.i2c_write(buffer)

    def wiggle(self, distance: int, direction: int):
        buffer = pack("<BHbb", CommandIDs.wiggle, distance, direction, self.sub_stepper_id) #cmd_id uint8, distance uint16, dir int8, stepper_id int8

        self.module.i2c_write(buffer)
    
    def is_running(self) -> bool: #returns True if stepper is running
        buffer = self.module.i2c_read(1)
            
        return ((1 << self.sub_stepper_id) & buffer[0] != 0)
  
#endregion
    
class CommandIDs:
    enable_driver = 0
    set_speed = 1
    set_accel = 2
    moveTo = 3
    moveTo_extra_revs = 4
    move = 5
    stop = 6
    wiggle = 7
    moveTo_min_steps = 8
    moveTo_minimize_movement = 9
