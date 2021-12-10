from struct import pack
import machine

class ClockStepper:
    cmd_id = {
      "set_speed": 0,
      "set_accel": 1,
      "moveTo": 2,
      "move": 3,
      "stop": 4,
      "falling_pointer": 5
    }
    
    def __init__(self, sub_stepper_id: int, i2c_bus: machine.I2C, i2c_address: int, current_target_pos = 0):
        self.i2c_bus = i2c_bus
        self.i2c_address = i2c_address
        self.sub_stepper_id = sub_stepper_id
        self.current_target_pos = current_target_pos
        
    def set_speed(self, speed: int):
        buffer = pack("BHB", self.cmd_id["set_speed"], speed, self.sub_stepper_id) #cmd_id uint8, speed uint16, stepper_id uint8           
        
        try:
            self.i2c_bus.writeto(self.i2c_address, buffer)
        except:
            print("Slave not found:", self.i2c_address)
    
    def set_accel(self, accel: int):
        buffer = pack("BHB", self.cmd_id["set_accel"], accel, self.sub_stepper_id) #cmd_id uint8, accel uint16, stepper_id uint8           
        
        try:
            self.i2c_bus.writeto(self.i2c_address, buffer)
        except:
            print("Slave not found:", self.i2c_address)
    
    def move_to(self, position: int, direction: int):
        buffer = pack("BHbB", self.cmd_id["moveTo"], position, direction, self.sub_stepper_id) #cmd_id uint8, position uint16, dir int8, stepper_id uint8           
        
        try:
            self.i2c_bus.writeto(self.i2c_address, buffer)
            self.current_target_pos = position;
        except:
            print("Slave not found:", self.i2c_address)
    
    def move(self, distance: int, direction: int):
        buffer = pack("BHbB", self.cmd_id["move"], distance, direction, self.sub_stepper_id) #cmd_id uint8, distance uint16, dir int8, stepper_id uint8           
        
        try:
            self.i2c_bus.writeto(self.i2c_address, buffer)
            self.current_target_pos = -1; # todo: fix
        except:
            print("Slave not found:", self.i2c_address)
    
    def stop(self):
        buffer = pack("BB", self.cmd_id["stop"], self.sub_stepper_id) #cmd_id uint8, stepper_id uint8           
        
        try:
            self.i2c_bus.writeto(self.i2c_address, buffer)
        except:
            print("Slave not found:", self.i2c_address)
    
    def falling_pointer(self):
        buffer = pack("BB", self.cmd_id["falling_pointer"], self.sub_stepper_id) #cmd_id uint8, stepper_id uint8           
        
        try:
            self.i2c_bus.writeto(self.i2c_address, buffer)
        except:
            print("Slave not found:", self.i2c_address)
    
    def is_running(self) -> bool: #returns True if stepper is running
        try:
            buffer = self.i2c_bus.readfrom(self.i2c_address, 1)
            
            return ((1 << self.sub_stepper_id) & buffer != 0)
        except:
            print("Slave not found:", self.i2c_address)
            return False
    
