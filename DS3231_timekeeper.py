import machine
import urtc
import utime

class DS3231_timekeeper:
    def __init__(self, new_minute_handler, alarm_pin: int, i2c_bus: machine.I2C, second = 0, enable_minute_alarm = True):
        self.alarm_pin = alarm_pin
        self.second = second
        self.new_minute_handler = new_minute_handler
        
        self.rtc = urtc.DS3231(i2c_bus)
        
        self.enable_minute_alarm = enable_minute_alarm

        #setup interrupt
        alarm_flag = False
        alarmtime = urtc.datetime_tuple(year=2000, month=1, day=None, weekday=None, hour=None, minute=None, second=second, millisecond=0)
        self.rtc.interrupt()
        alarm_pin = machine.Pin(13, machine.Pin.IN, machine.Pin.PULL_UP)
        alarm_pin.irq(trigger=machine.Pin.IRQ_FALLING, handler=self.alarm_handler)
        self.rtc.alarm(False)
        self.rtc.alarm_time(alarmtime)
 
    def get_datetime(self):
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
        if self.enable_minute_alarm:
            self.new_minute_handler()

    def increment_hour_minute(hour = 0, minute = 0):
        """
        pass positive or negative minutes or hour to add or subtract to current time, used for timesetting buttons
        sets seconds equal to 0
        """
        datetime = self.get_datetime()
        
        # combine times
        combined_hour = datetime.hour + hour
        combined_minute = datetime.minute + minute
        
        if combined_minute >= 0:
            combined_hour = combined_hour + combined_minute//60
            combined_minute = combined_minute % 60
        else:
            # (combined_minute + (-combined_minute%60))//60 -> "floor" towards zero for negative numbers
            combined_hour = combined_hour + (combined_minute + (-combined_minute%60))//60
            combined_minute = combined_minute % -60
            if combined_minute < 0:
                combined_minute = combined_minute + 60
                combined_hour = combined_hour - 1
                
        if combined_hour >= 0:
            combined_hour = combined_hour % 24
        else:
            combined_hour = combined_hour % -24
            if combined_hour < 0:
                combined_hour = combined_hour + 24
        
        self.set_datetime(urtc.datetime_tuple(year=2000, month=1, day=21, weekday=5, hour=combined_hour, minute=combined_minute, second=0, millisecond=0))
        