
from lib.PersistentStorage import PersistentStorage
from ClockDigitDisplay import ClockDigitDisplay
import machine
from OperatingModes.NightDay import NightDay
from OperatingModes.Visual import Visual
from OperatingModes.Stealth import Stealth
import OperatingModes.ClockModes as ClockModes

class ClockSettings:
    def __init__(self, filename="settings"):
        self.__nightmode_allowed_modes = []
        self.__startup_allowed_modes = []

        for idx, mode in enumerate(ClockModes.get_mode_list()):
            if mode.allowed_as_night_day_mode:
                self.__nightmode_allowed_modes.append(idx)
            if mode.allowed_as_startup_mode:
                self.__startup_allowed_modes.append(idx)
        
        default_startup_mode = NightDay
        default_day_mode = Visual
        default_night_mode = Stealth
        
        default_startup_mode_idx = ClockModes.get_mode_idx(default_startup_mode)
        default_day_mode_idx = ClockModes.get_mode_idx(default_day_mode)
        default_night_mode_idx = ClockModes.get_mode_idx(default_night_mode)

        if not default_startup_mode.allowed_as_startup_mode:
            raise Exception("default startup mode is not allowed as startup mode")
        if not default_day_mode.allowed_as_night_day_mode:
            raise Exception("default day mode is not allowed as day mode")
        if not default_night_mode.allowed_as_night_day_mode:
            raise Exception("default night mode is not allowed as night mode")
        
        var_lst = [PersistentStorage.persistent_var("night start", [21, 0], lambda a : (0 <= a[0] <= 23 and 0 <= a[1] <= 59)), # todo fix
                   PersistentStorage.persistent_var("night end", [9, 30], lambda a : (0 <= a[0] <= 23 and 0 <= a[1] <= 59)),
                   PersistentStorage.persistent_var("night mode", default_night_mode_idx, lambda a : True if a in self.__nightmode_allowed_modes else False),
                   PersistentStorage.persistent_var("day mode", default_day_mode_idx, lambda a : True if a in self.__nightmode_allowed_modes else False),
                   PersistentStorage.persistent_var("one style", 0, lambda a : True if a in [0, 1] else False),
                   PersistentStorage.persistent_var("eight style", 0, lambda a : True if a in [0, 1, 2] else False),
                   PersistentStorage.persistent_var("default mode", default_startup_mode_idx, lambda a : True if a in self.__startup_allowed_modes else False),
                   PersistentStorage.persistent_var("12 hour format", 0, lambda a : True if a in [0, 1] else False),
                   PersistentStorage.persistent_var("NTP enabled", 0, lambda a : True if a in [0, 1] else False),
                   PersistentStorage.persistent_var("Idle Pointer Pos", 5, lambda a : True if (a >= 0 and a <= 7) else False),
                   PersistentStorage.persistent_var("Speed Stealth", 105, lambda a : True if (a >= 5 and a <= 999) else False),
                   PersistentStorage.persistent_var("Accel Stealth", 60, lambda a : True if (a >= 5 and a <= 999) else False),
                   PersistentStorage.persistent_var("Speed Visual", 585, lambda a : True if (a >= 5 and a <= 999) else False),
                   PersistentStorage.persistent_var("Accel Visual", 210, lambda a : True if (a >= 5 and a <= 999) else False),
                   PersistentStorage.persistent_var("Visual Animation Ids", 210, lambda a : True if (a >= 5 and a <= 999) else False)] # 0 for 24 hour format, 1 for twelve hour formaty
        
        self.persistent = PersistentStorage(filename, var_lst)

        # how many steps per revolution the steppers have
        self.steps_per_rev = 4320

        # pin that the RTC interrupt is connected to
        self.ds3231_interrupt_pin = 13
        self.ds3231_bus = i2c1

        i2c1 = machine.I2C(1, sda=machine.Pin(14), scl=machine.Pin(3), freq=100000)
        i2c0 = machine.I2C(0, sda=machine.Pin(16), scl=machine.Pin(17), freq=100000)

        self.module_i2c_bus = [i2c1, i2c0, # the bus on which the module is
                        i2c1, i2c0, 
                        i2c1, i2c0]
        # module addresses  (pcb containing 4 steppers and a mcu, stm32f103 in this case)
        self.module_i2c_adr = [12, 13, # the adress of the module starting top left row first
                        14, 15, 
                        16, 17]

        self.ntp_module_present = True
        self.ntp_module_bus = i2c0
        self.ntp_module_adr = 40
        self.ntp_poll_freq = 180 # minutes
        self.ntp_timeout_s = 180 # s, for how long the ntp mopdule tries to retrieve the ntp
        self.ntp_validity_s = self.ntp_timeout_s #s, for how long the ntp stays valid in the ntp module after receving a ntp time

        #used during settings mode
        self.stepper_speed_fast = 700
        self.stepper_accel_fast = 450

        #used during mode change etc
        self.stepper_speed_default = 585
        self.stepper_accel_default = 210

        #used in analog mode
        self.stepper_speed_analog = 30
        self.stepper_accel_analog = 20

        #which animations to use in the viusal mode
        self.visual_animation_ids = [ClockDigitDisplay.animations["extra revs"], #these get shuffled randomly when ever end of list is reached
                                    ClockDigitDisplay.animations["straight wave"],
                                    ClockDigitDisplay.animations["opposing pointers"],
                                    ClockDigitDisplay.animations["focus"],
                                    ClockDigitDisplay.animations["opposites"],
                                    #DigitDisplay.animations["equipotential"],
                                    ClockDigitDisplay.animations["speedy clock"],
                                    ClockDigitDisplay.animations["random"],
                                    ClockDigitDisplay.animations["opposing wave"],
                                    ClockDigitDisplay.animations["circle"],
                                    ClockDigitDisplay.animations["smaller bigger"],
                                    ClockDigitDisplay.animations["small circles"],
                                    #DigitDisplay.animations["uhrenspiel"]
                                    ]
