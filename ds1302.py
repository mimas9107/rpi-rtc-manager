import RPi.GPIO as GPIO
import time
import calendar
from datetime import datetime, timezone
from config import config

# DS1302 Registers
REG_SECONDS = 0x80
REG_MINUTES = 0x82
REG_HOURS   = 0x84
REG_DATE    = 0x86
REG_MONTH   = 0x88
REG_DAY     = 0x8A
REG_YEAR    = 0x8C
REG_WP      = 0x8E
REG_TC      = 0x90 # Trickle Charge Register
REG_BURST   = 0xBE

class DS1302:
    def __init__(self, clk, dat, rst):
        self.clk = clk
        self.dat = dat
        self.rst = rst
        
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        GPIO.setup(self.clk, GPIO.OUT)
        GPIO.setup(self.rst, GPIO.OUT)
        
        # Power-on Safety: Ensure Trickle Charger is DISABLED to save battery
        self._disable_trickle_charge()
        
    def _write_byte(self, value):
        GPIO.setup(self.dat, GPIO.OUT)
        for i in range(8):
            GPIO.output(self.dat, (value >> i) & 1)
            GPIO.output(self.clk, 1)
            time.sleep(0.00001)
            GPIO.output(self.clk, 0)
            time.sleep(0.00001)

    def _read_byte(self):
        GPIO.setup(self.dat, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        value = 0
        for i in range(8):
            bit = GPIO.input(self.dat)
            value |= (bit << i)
            GPIO.output(self.clk, 1)
            time.sleep(0.00001)
            GPIO.output(self.clk, 0)
            time.sleep(0.00001)
        return value

    def _disable_trickle_charge(self):
        """Forces the internal trickle charger to OFF state."""
        GPIO.output(self.rst, 1)
        self._write_byte(REG_TC)
        # 0x00 to be absolutely sure.
        self._write_byte(0x00)
        GPIO.output(self.rst, 0)

    def _bcd_to_dec(self, bcd):
        return (bcd & 0x0F) + ((bcd >> 4) * 10)

    def _dec_to_bcd(self, dec):
        return ((dec // 10) << 4) | (dec % 10)

    def is_clock_halted(self):
        """Checks the CH (Clock Halt) bit in the seconds register."""
        GPIO.output(self.rst, 1)
        self._write_byte(REG_SECONDS | 0x01)
        seconds_reg = self._read_byte()
        GPIO.output(self.rst, 0)
        return (seconds_reg & 0x80) != 0

    def read_time(self):
        """Returns epoch_sec (int) in UTC"""
        if self.is_clock_halted():
            return 0
            
        GPIO.output(self.rst, 1)
        self._write_byte(REG_BURST | 0x01)
        
        sec = self._bcd_to_dec(self._read_byte() & 0x7F)
        min = self._bcd_to_dec(self._read_byte() & 0x7F)
        hour = self._bcd_to_dec(self._read_byte() & 0x3F)
        date = self._bcd_to_dec(self._read_byte() & 0x3F)
        month = self._bcd_to_dec(self._read_byte() & 0x1F)
        day = self._bcd_to_dec(self._read_byte() & 0x07)
        year = self._bcd_to_dec(self._read_byte() & 0xFF) + 2000
        
        GPIO.output(self.rst, 0)
        
        try:
            # Create a naive datetime object assuming it's UTC
            dt = datetime(year, month, date, hour, min, sec)
            # Use calendar.timegm to convert UTC tuple to timestamp (correctly ignores local timezone)
            return int(calendar.timegm(dt.timetuple()))
        except ValueError:
            return 0

    def write_time(self, epoch_sec):
        """Sets RTC time from epoch_sec (int). RTC stores UTC time."""
        # Convert epoch to UTC datetime object explicitly
        dt = datetime.fromtimestamp(epoch_sec, tz=timezone.utc)
        
        # Disable write protect
        GPIO.output(self.rst, 1)
        self._write_byte(REG_WP)
        self._write_byte(0x00)
        GPIO.output(self.rst, 0)
        
        # Burst write
        GPIO.output(self.rst, 1)
        self._write_byte(REG_BURST)
        
        self._write_byte(self._dec_to_bcd(dt.second) & 0x7F)
        self._write_byte(self._dec_to_bcd(dt.minute))
        self._write_byte(self._dec_to_bcd(dt.hour))
        self._write_byte(self._dec_to_bcd(dt.day))
        self._write_byte(self._dec_to_bcd(dt.month))
        self._write_byte(self._dec_to_bcd(dt.weekday() + 1))
        self._write_byte(self._dec_to_bcd(dt.year % 100))
        
        # Enable write protect
        self._write_byte(0x80)
        
        GPIO.output(self.rst, 0)

# Helper function to get instance
def get_rtc():
    return DS1302(clk=config['CLK'], dat=config['DAT'], rst=config['RST'])
