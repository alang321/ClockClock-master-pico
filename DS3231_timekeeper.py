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
    
    def set_hour_minute(self, hour, minute):
        #second 1 so alarm is not triggered, since this is inconsistent somehow
        self.set_datetime(urtc.datetime_tuple(year=2000, month=1, day=21, weekday=5, hour=hour, minute=minute, second=1, millisecond=0)) 
    
    def set_datetime(self, datetime):
        self.rtc.datetime(datetime)
        
    def alarm_handler(self, pin):
        self.rtc.alarm(False)
        if self.enable_minute_alarm:
            self.new_minute_handler()

    def add_to_hour_minute(self, hour = 0, minute = 0):
        """
        pass positive or negative minutes or hour to add or subtract to current time, used for timesetting buttons
        sets seconds equal to 0
        minutes_affect_hours determines wether minute rollover at 60 increases/decreases the hours
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
                if minutes_affect_hours:
                    combined_hour = combined_hour - 1
                
        if combined_hour >= 0:
            combined_hour = combined_hour % 24
        else:
            combined_hour = combined_hour % -24
            if combined_hour < 0:
                combined_hour = combined_hour + 24
        
        self.set_hour_minute(combined_hour, combined_minute)

    def increment_digit(self, digit_index):
        """
        increment digit by 1
        digit_index from 0 to 3 to increment
        """
        hour, minute = self.get_hour_minute()
        
        digits = [hour//10, hour%10, minute//10, minute%10]
        
        if digit_index == 0:
            digits[0] += 1
            digits[0] = digits[0] % 3
            if digits[0] == 2:
                digits[1] = min(digits[1], 3)    
        elif digit_index == 1:
            digits[1] += 1
            
            if digits[0] == 2:
                digits[1] = digits[1] % 4 
            else:
                digits[1] = digits[1] % 10 
        elif digit_index == 2:
            digits[2] += 1
            digits[2] = digits[2] % 6   
        elif digit_index == 3:
            digits[3] += 1
            digits[3] = digits[3] % 10    
        
        hour = digits[0] * 10 + digits[1]
        minute = digits[2] * 10 + digits[3]
        
        self.set_hour_minute(hour, minute)
    
    def decrement_digit(self, digit_index):
        """
        decrement digit by 1
        digit_index from 0 to 3 to increment
        """
        hour, minute = self.get_hour_minute()
        
        digits = [hour//10, hour%10, minute//10, minute%10]
        
        if digit_index == 0:
            digits[0] -= 1
            if digits[0] == -1:
                digits[0] = 2
            if digits[0] == 2:
                digits[1] = min(digits[1], 3)    
        elif digit_index == 1:
            digits[1] -= 1
            if digits[0] == 2:
                if digits[1] == -1:
                    digits[1] = 3
            else:
                if digits[1] == -1:
                    digits[1] = 9
        elif digit_index == 2:
            digits[2] -= 1
            if digits[2] == -1:
                digits[2] = 5  
        elif digit_index == 3:
            digits[3] -= 1
            digits[3] = digits[3] % 10 
            if digits[3] == -1:
                digits[3] = 9
        
        hour = digits[0] * 10 + digits[1]
        minute = digits[2] * 10 + digits[3]
        
        self.set_hour_minute(hour, minute)
        