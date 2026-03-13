import RPi.GPIO as GPIO
import time
from datetime import datetime
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

    def _bcd_to_dec(self, bcd):
        return (bcd & 0x0F) + ((bcd >> 4) * 10)

    def _dec_to_bcd(self, dec):
        return ((dec // 10) << 4) | (dec % 10)

    def read_time(self):
        """Returns epoch_sec (int)"""
        GPIO.output(self.rst, 1)
        # Burst read
        self._write_byte(REG_BURST | 0x01) # Read mode
        
        sec = self._bcd_to_dec(self._read_byte() & 0x7F)
        min = self._bcd_to_dec(self._read_byte() & 0x7F)
        hour = self._bcd_to_dec(self._read_byte() & 0x3F)
        date = self._bcd_to_dec(self._read_byte() & 0x3F)
        month = self._bcd_to_dec(self._read_byte() & 0x1F)
        day = self._bcd_to_dec(self._read_byte() & 0x07) # Day of week (1-7)
        year = self._bcd_to_dec(self._read_byte() & 0xFF) + 2000
        
        GPIO.output(self.rst, 0)
        
        try:
            dt = datetime(year, month, date, hour, min, sec)
            return int(dt.timestamp())
        except ValueError:
            return 0

    def write_time(self, epoch_sec):
        """Sets RTC time from epoch_sec (int)"""
        dt = datetime.fromtimestamp(epoch_sec)
        
        # Disable write protect
        GPIO.output(self.rst, 1)
        self._write_byte(REG_WP)
        self._write_byte(0x00)
        GPIO.output(self.rst, 0)
        
        # Burst write
        GPIO.output(self.rst, 1)
        self._write_byte(REG_BURST) # Write mode
        
        self._write_byte(self._dec_to_bcd(dt.second))
        self._write_byte(self._dec_to_bcd(dt.minute))
        self._write_byte(self._dec_to_bcd(dt.hour))
        self._write_byte(self._dec_to_bcd(dt.day))
        self._write_byte(self._dec_to_bcd(dt.month))
        self._write_byte(self._dec_to_bcd(dt.weekday() + 1)) # DS1302 uses 1-7
        self._write_byte(self._dec_to_bcd(dt.year % 100))
        
        # Enable write protect
        self._write_byte(0x80)
        
        GPIO.output(self.rst, 0)

# Helper function to get instance
def get_rtc():
    return DS1302(clk=config['CLK'], dat=config['DAT'], rst=config['RST'])
