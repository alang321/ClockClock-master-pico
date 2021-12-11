from struct import pack
import machine

class ClockModule: # module for 1 of the 6 pcbs in the clock
    cmd_id = {
      "set_speed": 0,
      "set_accel": 1,
      "moveTo": 2,
      "move": 3,
      "stop": 4,
      "falling_pointer": 5
    }
    
    def __init__(self, i2c_bus: machine.I2C, i2c_address: int):
        self.i2c_bus = i2c_bus
        self.i2c_address = i2c_address
        self.sub_stepper_id = -1 # so it addresses all steppers
        
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
            self.current_target_pos = position;
        except:
            print("Slave not found:", self.i2c_address)
    
    def move_module(self, distance: int, direction: int):
        buffer = pack("<BHbb", self.cmd_id["move"], distance, direction, self.sub_stepper_id) #cmd_id uint8, distance uint16, dir int8, stepper_id int8           
        
        try:
            self.i2c_bus.writeto(self.i2c_address, buffer)
            
            relative = (distance * direction) % self.steps_per_rev
            
            self.current_target_pos = (self.steps_per_rev + self.current_target_pos + relative) % self.steps_per_rev
        except:
            print("Slave not found:", self.i2c_address)
        
    def stop_module(self):
        buffer = pack("<Bb", self.cmd_id["stop"], self.sub_stepper_id) #cmd_id uint8, stepper_id int8           
        
        try:
            self.i2c_bus.writeto(self.i2c_address, buffer)
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
    
