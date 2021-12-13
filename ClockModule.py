from struct import pack
import machine
from ClockStepper import ClockStepper

class ClockModule: # module for 1 of the 6 pcbs in the clock
    cmd_id = {
      "enable_driver": 0,
      "set_speed": 1,
      "set_accel": 2,
      "moveTo": 3,
      "moveTo_extra_revs": 4,
      "move": 5,
      "stop": 6,
      "falling_pointer": 7
    }
    
    def __init__(self, i2c_bus: machine.I2C, i2c_address: int, steps_full_rev: int):
        self.steps_full_rev = steps_full_rev
        self.i2c_bus = i2c_bus
        self.i2c_address = i2c_address
        self.sub_stepper_id = -1 # so it addresses all steppers
        self.is_driver_enabled = True
            
        self.steppers = [ClockStepper(sub_id, self, self.steps_full_rev) for sub_id in range(8)]
        self.minute_steppers = self.steppers[:4]
        self.hour_steppers = self.steppers[4:]
        
    def enable_disable_driver_module(self, enable_disable: bool):
        """
        true to enable driver of module
        false to disable
        """
        buffer = pack("<BB", self.cmd_id["enable_driver"], int(enable_disable)) #cmd_id uint8, enable uint8         
        
        try:
            self.i2c_bus.writeto(self.i2c_address, buffer)
            self.is_driver_enabled = enable_disable
        except:
            print("Slave not found:", self.i2c_address)
        
    def set_speed_module(self, speed: int):
        buffer = pack("<BHb", self.cmd_id["set_speed"], speed, self.sub_stepper_id) #cmd_id uint8, speed uint16, stepper_id int8           
        
        try:
            self.i2c_bus.writeto(self.i2c_address, buffer)
        except:
            print("Slave not found:", self.i2c_address)
    
    def set_accel_module(self, accel: int):
        buffer = pack("<BHb", self.cmd_id["set_accel"], accel, self.sub_stepper_id) #cmd_id uint8, accel uint16, stepper_id int8           
        
        try:
            self.i2c_bus.writeto(self.i2c_address, buffer)
        except:
            print("Slave not found:", self.i2c_address)
    
    def move_to_module(self, position: int, direction: int):
        buffer = pack("<BHbb", self.cmd_id["moveTo"], position, direction, self.sub_stepper_id) #cmd_id uint8, position uint16, dir int8, stepper_id int8           
        
        try:
            self.i2c_bus.writeto(self.i2c_address, buffer)
            
            for stepper in self.steppers:
                stepper.current_target_pos = position
        except:
            print("Slave not found:", self.i2c_address)
    
    def move_to_extra_revs_module(self, position: int, direction: int, extra_revs: int):
        buffer = pack("<BHbBb", self.cmd_id["moveTo_extra_revs"], position, direction, extra_revs, self.sub_stepper_id) #cmd_id uint8, position uint16, dir int8, extra_revs uint8, stepper_id int8           
        
        try:
            self.i2c_bus.writeto(self.i2c_address, buffer)
            
            for stepper in self.steppers:
                stepper.current_target_pos = position
        except:
            print("Slave not found:", self.i2c_address)
    
    def move_module(self, distance: int, direction: int):
        buffer = pack("<BHbb", self.cmd_id["move"], distance, direction, self.sub_stepper_id) #cmd_id uint8, distance uint16, dir int8, stepper_id int8           
        
        try:
            self.i2c_bus.writeto(self.i2c_address, buffer)
            
            for stepper in self.steppers:
                relative = (distance * direction) % self.steps_per_rev
            
                self.current_target_pos = (self.steps_per_rev + self.current_target_pos + relative) % self.steps_per_rev
        except:
            print("Slave not found:", self.i2c_address)
        
    def stop_module(self):
        buffer = pack("<Bb", self.cmd_id["stop"], self.sub_stepper_id) #cmd_id uint8, stepper_id int8           
        
        try:
            self.i2c_bus.writeto(self.i2c_address, buffer)
            
            for stepper in self.steppers:
                stepper.current_target_pos = -1
        except:
            print("Slave not found:", self.i2c_address)
    
    def falling_pointer_module(self):
        buffer = pack("<Bb", self.cmd_id["falling_pointer"], self.sub_stepper_id) #cmd_id uint8, stepper_id int8           
        
        try:
            self.i2c_bus.writeto(self.i2c_address, buffer)
        except:
            print("Slave not found:", self.i2c_address)
    
    def is_running_module(self) -> bool: #returns True if stepper is running
        try:
            buffer = self.i2c_bus.readfrom(self.i2c_address, 1)
            
            return (buffer[0] != 0)
        except:
            print("Slave not found:", self.i2c_address)
            return False
    
