from struct import pack
import machine

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
        
    def enable_disable_driver_module(self, enable_disable: bool) -> bool:
        """
        true to enable driver of module
        false to disable
        """
        buffer = pack("<BB", self.cmd_id["enable_driver"], int(enable_disable)) #cmd_id uint8, enable uint8         
        
        try:
            self.i2c_bus.writeto(self.i2c_address, buffer)
            self.is_driver_enabled = enable_disable
                
            return True
        except:
            if __debug__:
                print("Slave not found:", self.i2c_address)
            return False
        
    def set_speed_module(self, speed: int) -> bool:
        buffer = pack("<BHb", self.cmd_id["set_speed"], speed, self.sub_stepper_id) #cmd_id uint8, speed uint16, stepper_id int8           
        
        try:
            self.i2c_bus.writeto(self.i2c_address, buffer)
                
            return True
        except:
            if __debug__:
                print("Slave not found:", self.i2c_address)
            return False
    
    def set_accel_module(self, accel: int) -> bool:
        buffer = pack("<BHb", self.cmd_id["set_accel"], accel, self.sub_stepper_id) #cmd_id uint8, accel uint16, stepper_id int8           
        
        try:
            self.i2c_bus.writeto(self.i2c_address, buffer)
                
            return True
        except:
            if __debug__:
                print("Slave not found:", self.i2c_address)
            return False
    
    def move_to_module(self, position: int, direction: int) -> bool:
        buffer = pack("<BHbb", self.cmd_id["moveTo"], position, direction, self.sub_stepper_id) #cmd_id uint8, position uint16, dir int8, stepper_id int8           
        
        try:
            self.i2c_bus.writeto(self.i2c_address, buffer)
            
            for stepper in self.steppers:
                stepper.current_target_pos = position
                
            return True
        except:
            if __debug__:
                print("Slave not found:", self.i2c_address)
            return False
    
    def move_to_extra_revs_module(self, position: int, direction: int, extra_revs: int) -> bool:
        buffer = pack("<BHbBb", self.cmd_id["moveTo_extra_revs"], position, direction, extra_revs, self.sub_stepper_id) #cmd_id uint8, position uint16, dir int8, extra_revs uint8, stepper_id int8           
        
        try:
            self.i2c_bus.writeto(self.i2c_address, buffer)
            
            for stepper in self.steppers:
                stepper.current_target_pos = position
                
            return True
        except:
            if __debug__:
                print("Slave not found:", self.i2c_address)
            return False
    
    def move_module(self, distance: int, direction: int) -> bool:
        buffer = pack("<BHbb", self.cmd_id["move"], distance, direction, self.sub_stepper_id) #cmd_id uint8, distance uint16, dir int8, stepper_id int8
        
        try:
            self.i2c_bus.writeto(self.i2c_address, buffer)
            
            for stepper in self.steppers:
                relative = (distance * direction) % self.steps_full_rev
            
                stepper.current_target_pos = (self.steps_full_rev + stepper.current_target_pos + relative) % self.steps_full_rev
                
            return True
        except:
            if __debug__:
                print("Slave not found:", self.i2c_address)
            return False
        
    def stop_module(self) -> bool:
        buffer = pack("<Bb", self.cmd_id["stop"], self.sub_stepper_id) #cmd_id uint8, stepper_id int8           
        
        try:
            self.i2c_bus.writeto(self.i2c_address, buffer)
            
            for stepper in self.steppers:
                stepper.current_target_pos = -1
                
            return True
        except:
            if __debug__:
                print("Slave not found:", self.i2c_address)
            return False
    
    def falling_pointer_module(self) -> bool:
        buffer = pack("<Bb", self.cmd_id["falling_pointer"], self.sub_stepper_id) #cmd_id uint8, stepper_id int8           
        
        try:
            self.i2c_bus.writeto(self.i2c_address, buffer)
            return True
        except:
            if __debug__:
                print("Slave not found:", self.i2c_address)
            return False
    
    def is_running_module(self) -> bool: #returns True if stepper is running
        try:
            buffer = self.i2c_bus.readfrom(self.i2c_address, 1)
            
            return (buffer[0] != 0)
        except:
            if __debug__:
                print("Slave not found:", self.i2c_address)
            return False
        

class ClockStepper:
    """
    A class representing a single stepper in a ClockClock
    Adresses slave over I2C using commands, code for slave here:
    https://github.com/alang321/clockclock-slave

    ...

    Attributes
    ----------
    cmd_id : dict
        dict for command ids that are passed as the first byte to let slave identify how to interpret following data
    module
        class ClockModule module (pcb + mcu, containing 4 coaxial steppers = 8 steppers) on which the stepper is, also contains i2c information
    sub_stepper_id : int
        stepper id which identifies specific stepper on module
    current_target_pos : int
        the target position where stepper is currently moving to or is at
    steps_per_rev : int
        number of steps a stepper needs to make one revolution
    """
    
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
    
    def __init__(self, sub_stepper_id: int, module: ClockModule, steps_per_rev: int, current_target_pos = 0):
        self.module = module
        self.sub_stepper_id = sub_stepper_id
        self.current_target_pos = current_target_pos
        self.steps_per_rev = steps_per_rev
        
    def set_speed(self, speed: int) -> bool:
        buffer = pack("<BHb", self.cmd_id["set_speed"], speed, self.sub_stepper_id) #cmd_id uint8, speed uint16, stepper_id int8           
        
        try:
            self.module.i2c_bus.writeto(self.module.i2c_address, buffer)
            
            return True
        except:
            if __debug__:
                print("Slave not found:", self.module.i2c_address)
            return False
    
    def set_accel(self, accel: int) -> bool:
        buffer = pack("<BHb", self.cmd_id["set_accel"], accel, self.sub_stepper_id) #cmd_id uint8, accel uint16, stepper_id int8           
        
        try:
            self.module.i2c_bus.writeto(self.module.i2c_address, buffer)
            
            return True
        except:
            if __debug__:
                print("Slave not found:", self.module.i2c_address)
            return False
    
    def move_to(self, position: int, direction: int) -> bool:
        buffer = pack("<BHbb", self.cmd_id["moveTo"], position, direction, self.sub_stepper_id) #cmd_id uint8, position uint16, dir int8, stepper_id int8           
        
        try:
            self.module.i2c_bus.writeto(self.module.i2c_address, buffer)
            self.current_target_pos = position
            
            return True
        except:
            if __debug__:
                print("Slave not found:", self.module.i2c_address)
            return False
    
    def move_to_extra_revs(self, position: int, direction: int, extra_revs: int) -> bool:
        buffer = pack("<BHbBb", self.cmd_id["moveTo_extra_revs"], position, direction, extra_revs, self.sub_stepper_id) #cmd_id uint8, position uint16, dir int8, extra_revs uint8, stepper_id int8           
        
        try:
            self.module.i2c_bus.writeto(self.module.i2c_address, buffer)
            self.current_target_pos = position
            
            return True
        except:
            if __debug__:
                print("Slave not found:", self.module.i2c_address)
            return False
    
    def move(self, distance: int, direction: int) -> bool:
        buffer = pack("<BHbb", self.cmd_id["move"], distance, direction, self.sub_stepper_id) #cmd_id uint8, distance uint16, dir int8, stepper_id int8           
        
        try:
            self.module.i2c_bus.writeto(self.module.i2c_address, buffer)
            
            relative = (distance * direction) % self.steps_per_rev
            
            self.current_target_pos = (self.steps_per_rev + self.current_target_pos + relative) % self.steps_per_rev
            
            return True
        except:
            if __debug__:
                print("Slave not found:", self.module.i2c_address)
            return False
        
    def stop(self) -> bool:
        buffer = pack("<Bb", self.cmd_id["stop"], self.sub_stepper_id) #cmd_id uint8, stepper_id int8     
        
        try:
            self.module.i2c_bus.writeto(self.module.i2c_address, buffer)      
            self.current_target_pos = -1
            
            return True
        except:
            if __debug__:
                print("Slave not found:", self.module.i2c_address)
            return False
    
    def falling_pointer(self) -> bool:
        buffer = pack("<Bb", self.cmd_id["falling_pointer"], self.sub_stepper_id) #cmd_id uint8, stepper_id int8   
        
        try:
            self.module.i2c_bus.writeto(self.module.i2c_address, buffer)          
            self.current_target_pos = int(0.5 * self.steps_per_rev)
            
            return True
        except:
            if __debug__:
                print("Slave not found:", self.module.i2c_address)
            return False
    
    def is_running(self) -> bool: #returns True if stepper is running
        try:
            buffer = self.module.i2c_bus.readfrom(self.module.i2c_address, 1)
            
            return ((1 << self.sub_stepper_id) & buffer[0] != 0)
        except:
            if __debug__:
                print("Slave not found:", self.module.i2c_address)
            return False
    


    

