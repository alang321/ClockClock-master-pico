
from lib.PersistentStorage import PersistentStorage
from DigitDisplay import DigitDisplay
import machine
import OperationModes

class ClockSettings:
    def __init__(self, filename="settings"):
        
        self.__nightmode_allowed_modes = [OperationModes.Visual.id,
                                          OperationModes.ShortestPath.id,
                                          OperationModes.Stealth.id,
                                          OperationModes.Analog.id,
                                          OperationModes.Sleep.id]
        
        self.__defaultmode_allowed_modes = [OperationModes.NightDay.id,
                                            OperationModes.Visual.id,
                                            OperationModes.ShortestPath.id,
                                            OperationModes.Stealth.id,
                                            OperationModes.Analog.id,
                                            OperationModes.Sleep.id]
        
        var_lst = [PersistentStorage.persistent_var("night start", [21, 0], lambda a : (0 <= a[0] <= 23 and 0 <= a[1] <= 59)), # todo fix
                   PersistentStorage.persistent_var("night end", [9, 30], lambda a : (0 <= a[0] <= 23 and 0 <= a[1] <= 59)),
                   PersistentStorage.persistent_var("night mode", OperationModes.Stealth.id, lambda a : True if a in self.__nightmode_allowed_modes else False),
                   PersistentStorage.persistent_var("day mode", OperationModes.Visual.id, lambda a : True if a in self.__nightmode_allowed_modes else False),
                   PersistentStorage.persistent_var("one style", 0, lambda a : True if a in [0, 1] else False),
                   PersistentStorage.persistent_var("eight style", 0, lambda a : True if a in [0, 1, 2] else False),
                   PersistentStorage.persistent_var("default mode", OperationModes.NightDay.id, lambda a : True if a in self.__defaultmode_allowed_modes else False),
                   PersistentStorage.persistent_var("12 hour format", 0, lambda a : True if a in [0, 1] else False),
                   PersistentStorage.persistent_var("NTP enabled", 0, lambda a : True if a in [0, 1] else False)] # 0 for 24 hour format, 1 for twelve hour formaty
        
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

        self.stepper_speed_fast = 700
        self.stepper_accel_fast = 450

        #normal speed used in most modes
        self.stepper_speed_default = 585
        self.stepper_accel_default = 210

        #used in stealth mode
        self.stepper_speed_stealth = 105
        self.stepper_accel_stealth = 60

        #used in analog mode
        self.stepper_speed_analog = 30
        self.stepper_accel_analog = 20

        #which animations to use in the viusal mode
        self.visual_animation_ids = [DigitDisplay.animations["extra revs"], #these get shuffled randomly when ever end of list is reached
                                DigitDisplay.animations["straight wave"],
                                DigitDisplay.animations["opposing pointers"],
                                DigitDisplay.animations["focus"],
                                DigitDisplay.animations["opposites"],
                                #DigitDisplay.animations["equipotential"],
                                DigitDisplay.animations["speedy clock"],
                                DigitDisplay.animations["random"],
                                DigitDisplay.animations["opposing wave"],
                                DigitDisplay.animations["circle"],
                                DigitDisplay.animations["smaller bigger"],
                                DigitDisplay.animations["small circles"],
                                #DigitDisplay.animations["uhrenspiel"]
                                ]
    

        