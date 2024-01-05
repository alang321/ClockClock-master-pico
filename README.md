# ClockClock-master-pico

Video of clock in action:
https://photos.google.com/share/AF1QipM3veQpQ0XkVU6mXYjfI77cDL8gVcDZlROT0_qATZYPRnyIRZsuLHRsqtRsNTrixQ?key=c0U2SFBVdGpubVNTWW43WENBeFczdWVBSk5FbmZB

This runs on a RPi Pico but should work with a lot of microcontrollers. All it uses is some i2c buses. Some general settings can be adjusted in ClockSettings.py such as pins etc.

Works with 6 modules controlled over an I2C bus. Module code can be found at https://github.com/alang321/clockclock-stepper-module

Optionally another RPi Pico W can be used as an NTP module https://github.com/alang321/clockclock-network-module
(This is really weird I know, but the NTP function was made after the clock was done and i didnt wanna rebuild the main PCB and desoldering is a pain without the right equipment, but it would make much more sense to use a PicoW as the main controller in the first place and then rewrite NTPModule.py)