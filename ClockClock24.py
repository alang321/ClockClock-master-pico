from StepperControl import Stepper, StepperModule, ClockSteppers
from DigitDisplay import DigitDisplay
from DS3231_timekeeper import DS3231_timekeeper
import uasyncio as asyncio
from machine import Timer
from ClockSettings import ClockSettings
from NTPModule import NTPModule
import OperationModes

class ClockClock24:
    #be carefull that these dont exceed the maxximum speed set in the driver, if so the commands will be ignored
    #fast speed used when showing mode numbers and similar


    
    def __init__(self):
        # persistent data and config values
        self.settings = ClockSettings()
        
        #timekeeping, rtc and ntp module
        self.alarm_flag = False
        self.rtc = DS3231_timekeeper(self.new_minute_handler, ClockConfig.ds3231_interrupt_pin, ClockConfig.ds3231_bus, ClockConfig.second)
        self.ntp_module = None
        if self.settings.ntp_module_present:
            self.ntp_module = NTPModule(self.settings.ntp_module_bus, self.settings.ntp_module_adr, self.settings.ntp_poll_freq)               
        self.async_ntp_task = None
        self.ntp_timer = Timer()
        self.timer_running = False #wether or not timer is aalready running
        self.start_ntp()

        #asyncio and tasks
        self.async_display_task = None  # currently running asynchronous tasks that have to be cancelled
        self.async_mode_change_task = None
        self.async_setting_page_task = None
        self.movement_done_event = asyncio.Event()
        
        #stepper control
        self.steppers = ClockSteppers(self.settings.module_i2c_bus, self.settings.module_i2c_adr, self.settings.steps_per_rev)
        self.digit_display = DigitDisplay(self)

        #list of operation mode objects
        self.modes = OperationModes.get_mode_list(self)
        self.current_mode_idx = self.settings.persistent.get_var("default mode")

        self.input_lock = False
        self.dont_display_time = False
        
        self.__current_mode = None
        self.set_mode(self.current_mode_idx)

    async def run(self):
        if not self.movement_done_event.is_set():
            if not self.steppers.is_running():
                self.movement_done_event.set()

        if self.alarm_flag:
            self.alarm_flag = False
            hour, minute = self.rtc.get_hour_minute(bool(self.settings.persistent.get_var("12 hour format")))
            self.display_time(hour, minute)

        await asyncio.sleep(0)

    def new_minute_handler(self):
        if __debug__:
            print("Interrupt received")
        self.alarm_flag = True

    def display_time(self, hour: int, minute: int):
        if __debug__:
            print("New time displayed:", hour, minute)
            print('Twelve hour format:', bool(self.settings.persistent.get_var("12 hour format")))

        if not self.dont_display_time:
            if self.__current_mode != None:
                self.__current_mode.new_time(hour, minute)

    def cancel_tasks(self):
        if self.async_display_task != None:
            self.async_display_task.cancel()
        if self.async_mode_change_task != None:
            self.async_mode_change_task.cancel()
        if self.async_setting_page_task != None: 
            self.async_setting_page_task.cancel()

    def cancel_display_tasks(self):
        if self.async_display_task != None:
            self.async_display_task.cancel()
            
#region mode change

    def set_mode(self, mode_id: int):
        self.cancel_tasks()
        self.async_mode_change_task = asyncio.create_task(self.__set_mode(mode_id))

    async def __set_mode(self, mode_id: int):
        if __debug__:
            print("New mode:", mode_id)

        mode = self.modes[mode_id]

        self.input_lock = True
        self.dont_display_time = True
        if self.__current_mode != None:
            self.__current_mode.end(False) #"destructor" of the old mode
        self.__current_mode = mode
        self.current_mode_idx = mode_id
        
        self.steppers.enable_disable_driver_all(True)
        self.steppers.set_speed_all(ClockClock24.stepper_speed_fast)
        self.steppers.set_accel_all(ClockClock24.stepper_accel_fast)
        self.digit_display.display_mode(mode.id)
        
        self.movement_done_event.clear()
        await self.movement_done_event.wait()
        
        await asyncio.sleep(1.2) #so digit is visible for a bit
        
        self.input_lock = False
        self.dont_display_time = False
        self.__current_mode = mode
        self.__current_mode.start() # specific initialisation of new mode after display of mode digit is done

    def get_mode_id(self):
        return self.current_mode_idx
    
    
#endregion

    
#region ntp
    
    def stop_ntp(self):
        if self.ntp_module != None:
            self.__stop_ntp_timer()
            
        if self.async_ntp_task != None:
            self.async_ntp_task.cancel()
    
    def start_ntp(self):
        if self.ntp_module != None:
            if self.persistent.get_var("NTP enabled"):
                if not self.timer_running:
                    self.__start_ntp_timer()
                    self.__ntp_callback()
            else:
                if self.timer_running:
                    self.__stop_ntp_timer()
    
    def __start_ntp_timer(self):
        self.timer_running = True
        if __debug__:
            print("Starting NTP Timer")
        self.ntp_timer.init(period=int(self.ntp_poll_freq_m*60*1000), mode=Timer.PERIODIC, callback=self.__ntp_callback)
        
    def __stop_ntp_timer(self):
        self.timer_running = False
        if __debug__:
            print("Stopping NTP Timer")
        self.ntp_timer.deinit()
        
    def __ntp_callback(self, t=0):
        if __debug__:
            print("Polling NTP Time")
        if self.async_ntp_task != None:
            self.async_ntp_task.cancel()
            
        self.async_ntp_task = asyncio.create_task(self.__ntp_get_time())

    async def __ntp_get_time(self):
        time_valid, hour, minute, second = await self.ntp_module.get_ntp_time(self.ntp_timeout_s, self.ntp_validity_s)
        
        if __debug__:
            print("Got NTP Time:", time_valid, hour, minute, second)
        
        if time_valid:
            rtc_hour, rtc_minute = self.rtc.get_hour_minute()
            self.rtc.set_hour_min_sec(hour, minute, second)
            
            if(rtc_hour != hour or rtc_minute != minute): #so time animations are definitely displayed
                if __debug__:
                    print("Forced Display of new time since new ntp time differed")
                self.alarm_flag = True
          
#endregion
    
