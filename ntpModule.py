import machine
from struct import pack, unpack
import time
import uasyncio as asyncio

class NTPmodule:
    
    def __init__(self, i2c_bus, address, i2c_polling_interval=3):
        self.i2c = i2c_bus
        self.address = address
        
        #how often to check if ntp module has received new time
        self.polling_delay = i2c_polling_interval #s
        return
    
    def start_hotspot(self):
        buffer = pack("<BB", 0, 1) #start hotspot
        
        self.i2c_write(buffer)
        
    def stop_hotspot(self):
        buffer = pack("<BB", 0, 0) #stop hotspot
        
        self.i2c_write(buffer)
        
    def reset_data(self):
        buffer = pack("<B", 2) #reset saved data
        
        self.i2c_write(buffer)
        
    def __start_ntp_poll(self, ntp_timeout, ntp_validity):
        buffer = pack("<BHH", 1, ntp_timeout, ntp_validity) #cmdid, ntp_poll_timeout, ntp time validity
        
        self.i2c_write(buffer)
        
    def __read_ntp(self):
        try:
            timebuf = self.i2c.readfrom(self.address, 4)
            return unpack("<BBBB", timebuf)
        except:
            if __debug__:
                print("NTP module not found")
            return (0, 0, 0, 0)
        
    def i2c_write(self, buffer):
        try:
            self.i2c.writeto(self.address, buffer)
        except:
            if __debug__:
                print("NTP module not found", buffer)
            
    async def get_ntp_time(self, ntp_timeout=120, ntp_validity=120):
        self.__start_ntp_poll(ntp_timeout, ntp_validity)
        
        still_polling = True
        time_valid = False
        while still_polling and not time_valid:
            await asyncio.sleep(self.polling_delay)
            
            ntp_return = self.__read_ntp()
            still_polling = ((1 << 1) & ntp_return[0] != 0)
            time_valid = ((1 << 0) & ntp_return[0] != 0)
            print('polled ntp time')
        
        return time_valid, ntp_return[1], ntp_return[2], ntp_return[3]








