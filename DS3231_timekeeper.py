import machine
import urtc
import utime

class DS3231_timekeeper:
    def __init__(self, new_minute_handler, alarm_pin: int, i2c_bus: machine.I2C, second = 0, cest_compensation = True):
        """
        Always provide set time in UTC+1 if cest compensation is turned on
        """
        self.alarm_pin = alarm_pin
        self.second = second
        self.cest_compensation = cest_compensation
        self.new_minute_handler = new_minute_handler
        
        self.rtc = urtc.DS3231(i2c_bus)

        #setup interrupt
        alarm_flag = False
        alarmtime = urtc.datetime_tuple(year=2000, month=1, day=None, weekday=None, hour=None, minute=None, second=second, millisecond=0)
        self.rtc.interrupt()
        alarm_pin = machine.Pin(13, machine.Pin.IN, machine.Pin.PULL_UP)
        alarm_pin.irq(trigger=machine.Pin.IRQ_FALLING, handler=self.alarm_handler)
        self.rtc.alarm(False)
        self.rtc.alarm_time(alarmtime)
 
    #todo: summer time compensation    
    def get_datetime(self):
        if self.cest_compensation:
            return DS3231_timekeeper.convert_utc1_to_cest(self.rtc.datetime())
        else:
            return self.rtc.datetime()
 
    def get_hour_minute(self):
        current_time = self.get_datetime()
        
        hour = current_time.hour
        minute = current_time.minute
        
        return hour, minute
    
    def set_datetime(self, datetime):
        self.rtc.datetime(datetime)
        
    def alarm_handler(self, pin):
        self.rtc.alarm(False)
        self.new_minute_handler()
    
    @staticmethod
    def convert_utc1_to_cest(datetime):
        """
        function to convert UTC+1 to CET/CEST
        """
        # starts last sunday in march, its cest if these are given
        # month = march - 3 - 31 days
        # weekday = 7
        # day > (31 - 7)
        
        # ends last sunday in october, its cest if these are given
        # month = october - 10 - 31 days
        # weekday = 7
        # day < (31 - 7)
        
        if 3 < datetime.month < 10:
            cest = True
        elif datetime.month == 3 and datetime.day > 24:
            cest = False
            # the difference of the current weekday to 7 has to be less than the difference of the current day to 31,
            # this means the last sunday already happened
            if (31 - datetime.day) < (7 - datetime.weekday): 
                cest = True
            elif datetime.weekday == 7: # its switchday
                if datetime.hour >= 2:
                    cest = True
        elif datetime.month == 10:
            cest = True
            if datetime.day > 24:
                if (31 - datetime.day) < (7 - datetime.weekday): # see before
                    cest = False
                elif datetime.weekday == 7: # its switchday
                    if datetime.hour >= 2:
                        cest = False
        else:
            cest = False
            
        if cest:
            return urtc.datetime_tuple(datetime.year, datetime.month, datetime.day, datetime.weekday, datetime.hour+1, datetime.minute, datetime.second, datetime.millisecond)
        else:
            return datetime
        
                
