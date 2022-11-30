import machine
from struct import pack, unpack
import time
import uasyncio as asyncio

class NTPmodule:
    
    def __init__(self, i2c_bus, address):
        self.i2c = i2c_bus
        self.address = address
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
        buffer = pack("<BHH", 1, 60, 60) #cmdid, ntp_poll_timeout, ntp time validity
        
        self.i2c_write(buffer)
        
    def __read_ntp(self):
        try:
            timebuf = self.i2c.readfrom(self.address, 4)
            return unpack("<BBBB", timebuf)
        except:
            print("NTP module not found")
            return (0, 0, 0, 0)
        
    def i2c_write(self, buffer):
        try:
            self.i2c.writeto(self.address, buffer)
        except:
            print("NTP module not found", buffer)
            
    async def get_ntp_time(self, ntp_gettime_delay=50, ntp_timeout=60, ntp_validity=60):
        self.__start_ntp_poll(ntp_timeout, ntp_validity)
        
        await asyncio.sleep(ntp_gettime_delay)
        
        return self.__read_ntp()



async def test(a):
    test2 = await a.get_ntp_time()
    print(test2)


    
i2c0 = machine.I2C(0, sda=machine.Pin(16), scl=machine.Pin(17), freq=100000)
print(i2c0.scan())

a = NTPmodule(i2c0, 40)

a.stop_hotspot()

asyncio.run(test(a))







