import machine
import urtc

class DS3231_timekeeper:
    def __init__(self, new_minute_handler, alarm_pin: int, i2c_bus: machine.I2C, second=0, enable_minute_alarm=True):
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

    def set_datetime(self, datetime):
        self.rtc.datetime(datetime)
 
    def get_hour_minute(self, twelve=False):
        current_time = self.get_datetime()

        hour = current_time.hour
        minute = current_time.minute

        if twelve:
            if hour == 0:
                hour += 12
            elif 13 <= hour <= 24:
                hour -= 12

        return hour, minute
    
    def set_hour_minute(self, hour, minute):
        #second 1 so alarm is not triggered, since this is inconsistent somehow
        self.set_datetime(urtc.datetime_tuple(year=2000, month=1, day=21, weekday=5, hour=hour, minute=minute, second=1, millisecond=0))
        
    def set_hour_min_sec(self, hour, minute, second):
        #second 1 so alarm is not triggered, since this is inconsistent somehow
        if second == 0: #since this is inconsistent for some reason
            second = 1
        self.set_datetime(urtc.datetime_tuple(year=2000, month=1, day=21, weekday=5, hour=hour, minute=minute, second=second, millisecond=0)) 

    def alarm_handler(self, pin):
        self.rtc.alarm(False)
        if self.enable_minute_alarm:
            self.new_minute_handler()
