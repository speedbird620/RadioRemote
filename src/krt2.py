#!/usr/bin/env python3
#
# Rev B: vectorized letters and buttons.
# rev C: - Implemented a splash screen at boot
#        - Implemented short and long press
#        - Long press at vol-buttons changes squelch setting
#        - Long press at mid freq-button changes switch frequency
#        - Remove primary frequency when changing the secondary frequency
#
# To do (notes to myself):
#    - Consider a hardware watchdog
#    - Bug: pick up the correct frequency when chaneging frequency for the second time 

rev_string = "Rev c"

from machine import Pin
import machine
import time
from machine import UART, I2C, Pin

# UART Serial communication on Pico
# UART0: GPIO0=TX, GPIO1=RX
# UART1: GPIO4=TX, GPIO5=RX (alternative)
try:
    serialData = UART(0, baudrate=9600, timeout_char=100, tx=Pin(0), rx=Pin(1))
    print("✓ UART0 initialized (9600 baud)")
except Exception as e:
    print(f"Error initializing UART: {e}")
    serialData = None

# I2C for OLED Display (SSD1306) on Pico
# I2C0: GPIO8=SDA, GPIO9=SCL
# I2C1: GPIO14=SDA, GPIO15=SCL (alternative)
I2C_DISPLAY_ADDRESS = 0x3c
OLED_AVAILABLE = False
display = None

# ----------------------o0 Font Caching Functions 0o----------------------
# Font data is cached during initialization (see _patch_ssd1306py_fonts)
# This loads font 24 characters into RAM at startup for fast rendering

# Initialize OLED with ssd1306py for large font support
try:
    import os
    import sys
    
    # Patch ssd1306py font modules with CACHED font data for speed
    def _patch_ssd1306py_fonts():
        """Patch ssd1306py to use cached hex font data - MUCH FASTER"""
        font_path = None
        for test_path in ['/ssd1306py', 'ssd1306py']:
            try:
                os.stat(test_path + '/ascii16.txt')
                font_path = test_path
                break
            except:
                pass
        
        if not font_path:
            return False
        
        try:
            from ssd1306py import ascii16, ascii24, ascii32
            
            # Pre-load ALL font data into RAM for characters we use (0-9, ., n)
            # This eliminates file I/O during rendering
            _cache_24 = {}
            chars_to_cache = "0123456789.n "
            
            print("Loading font 24 into RAM for fast rendering...")
            with open(font_path + '/ascii24.txt', 'r') as f:
                for char in chars_to_cache:
                    f.seek(ord(char) * 242)
                    get_line1 = f.read(120)
                    get_line2 = f.read(120)
                    data = []
                    for line_data in [get_line1, get_line2]:
                        for v in line_data.split(','):
                            v = v.strip()
                            if not v:
                                continue
                            try:
                                if v.startswith('0x') or v.startswith('0X'):
                                    data.append(int(v, 16))
                                else:
                                    data.append(int(v))
                            except:
                                pass
                    _cache_24[char] = data
            
            print(f"✓ Cached {len(_cache_24)} characters in RAM")
            
            # Replace the slow file-reading function with fast cache lookup
            def make_cached_get_ch_24():
                def _get_ch(ch):
                    # Return cached data if available, otherwise fall back to empty
                    return _cache_24.get(ch, [0] * 48)
                return _get_ch
            
            # Keep the original file-based functions for other sizes (not used)
            def make_get_ch_16():
                _file = None
                def _get_ch(ch):
                    nonlocal _file
                    if _file is None:
                        _file = open(font_path + '/ascii16.txt', 'r')
                    _file.seek(ord(ch) * 81)
                    get_line = _file.read(80)
                    data = []
                    for v in get_line.split(','):
                        v = v.strip()
                        if not v:
                            continue
                        try:
                            if v.startswith('0x') or v.startswith('0X'):
                                data.append(int(v, 16))
                            else:
                                data.append(int(v))
                        except:
                            pass
                    return data
                return _get_ch
            
            ascii16._get_ch = make_get_ch_16()
            ascii24._get_ch = make_cached_get_ch_24()  # Use CACHED version
            # ascii32 not needed
            return True
        except Exception as e:
            print(f"Warning: Could not patch ssd1306py: {e}")
            import sys
            sys.print_exception(e)
            return False
    
    # Patch the fonts
    _patch_ssd1306py_fonts()
    
    # Now import and initialize
    from ssd1306py import ops as lcd
    i2c = I2C(0, freq=400000, scl=Pin(9), sda=Pin(8))
    devices = i2c.scan()
    
    if I2C_DISPLAY_ADDRESS in devices:
        print(f"✓ OLED display found at 0x{I2C_DISPLAY_ADDRESS:02x}")
        lcd.init_i2c(9, 8, 128, 64)
        lcd.clear()
        display = lcd  # Use ssd1306py ops as display object
        OLED_AVAILABLE = True
    else:
        print(f"Warning: No device at 0x{I2C_DISPLAY_ADDRESS:02x}, found: {[hex(d) for d in devices]}")
        OLED_AVAILABLE = False
except ImportError:
    print("Warning: ssd1306py module not available")
    OLED_AVAILABLE = False
except Exception as e:
    print(f"Error initializing OLED: {e}")
    OLED_AVAILABLE = False

question_radio2pi = 0

reply_pi2radio = 0
question_pi2radio = 0

short_press_ms = 220
vol_plus_pressed_time = 0
vol_minus_pressed_time = 0
freq_enter_time = 0
ComEstablished = False
ComEstablished_old = False
DuplexComEstablished = False
TimeComEstablished = 0
Step25khz = False
menu = 0
menu_old = -1
vol_plus_old = False
vol_minus_old = False
volume = -1
volume_old = 0
volume_sp = 0
squelch = -1
squelch_old = 0
squelch_sp = 0
intercom = -1
intercom_old = 0
mhz = -1
stby_mhz = -1
stby_mhz_sp = 118
stby_mhz_sp_old = 118
khz = 0.0
channel = 0
stby_channel = 0
stby_channel_sp = 0
stby_channel_sp_old = 0
tmp_pointer = 0
tmp_pointer_old = 0
intercom_sp = 0
ActiveFrequency = ['','']
ActiveFrequency0_old = ''
ActiveFrequency1_old = ''
StandbyFrequency0_old = ''
StandbyFrequency1_old = ''
ActiveFrequency_old = ['','']
StandbyFrequency = ['','']
StandbyFrequency_old = ['','']  
switch_active_standby = False

x = False
y = 0
array = [''] * 30
array_pointer = 0

vol_plus = Pin(2, Pin.IN, Pin.PULL_UP)
vol_plus_old = vol_plus()

vol_minus = Pin(3, Pin.IN, Pin.PULL_UP)
vol_minus_old = vol_minus()

freq_plus = Pin(4, Pin.IN, Pin.PULL_UP)
freq_plus_old = freq_plus()

freq_enter = Pin(5, Pin.IN, Pin.PULL_UP)
freq_enter_old = freq_enter()

freq_minus = Pin(6, Pin.IN, Pin.PULL_UP)
freq_minus_old = freq_minus()

#   .n00   .n05   .n10   .n15   .n25   .n30   .n35   .n40   .n50   .n55   .n60  .n65    .n75   .n80   .n85   .n90             
HexArray = [
    0x00,  0x01,  0x02,  0x03,  0x05,  0x06,  0x07,  0x08,  0x0a,  0x0b,  0x0c,  0x0d,  0x0f,  0x10,  0x11,  0x12, #.0nn
    0x14,  0x15,  0x16,  0x17,  0x19,  0x1a,  0x1b,  0x1c,  0x1e,  0x1f,  0x20,  0x21,  0x23,  0x24,  0x25,  0x26, #.1nn
    0x28,  0x29,  0x2a,  0x2b,  0x2d,  0x2e,  0x2f,  0x30,  0x32,  0x33,  0x34,  0x35,  0x37,  0x38,  0x39,  0x3a, #.2nn
    0x3c,  0x3d,  0x3e,  0x3f,  0x41,  0x42,  0x43,  0x44,  0x46,  0x47,  0x48,  0x49,  0x4b,  0x4c,  0x4d,  0x4e, #.3nn
    0x50,  0x51,  0x52,  0x53,  0x55,  0x56,  0x57,  0x58,  0x5a,  0x5b,  0x5c,  0x5d,  0x5f,  0x60,  0x61,  0x62, #.4nn
    0x64,  0x65,  0x66,  0x67,  0x69,  0x6a,  0x6b,  0x6c,  0x6e,  0x6f,  0x70,  0x71,  0x73,  0x74,  0x75,  0x76, #.5nn
    0x78,  0x79,  0x7a,  0x7b,  0x7d,  0x7e,  0x7f,  0x80,  0x82,  0x83,  0x84,  0x85,  0x87,  0x88,  0x89,  0x8a, #.6nn
    0x8c,  0x8d,  0x8e,  0x8f,  0x91,  0x92,  0x93,  0x94,  0x96,  0x97,  0x98,  0x99,  0x9b,  0x9c,  0x9d,  0x9e, #.7nn
    0xa0,  0xa1,  0xa2,  0xa3,  0xa5,  0xa6,  0xa7,  0xa8,  0xaa,  0xab,  0xac,  0xad,  0xaf,  0xb0,  0xb1,  0xb2, #.8nn
    0xb4,  0xb5,  0xb6,  0xb7,  0xb9,  0xba,  0xbb,  0xbc,  0xbe,  0xbf,  0xc0,  0xc1,  0xc3,  0xc4,  0xc5,  0xc6] #.9nn

#    nn0      nn1      nn2      nn3      nn4      nn5      nn6      nn7      nn8      nn9      
DecArray = [
    "0.000", "0.005", "0.010", "0.015", "0.025", "0.030", "0.035", "0.040", "0.050", "0.055", #00n
    "0.060", "0.065", "0.075", "0.080", "0.085", "0.090", "0.100", "0.105", "0.110", "0.115", #01n
    "0.125", "0.130", "0.135", "0.140", "0.150", "0.155", "0.160", "0.165", "0.175", "0.180", #02n
    "0.185", "0.190", "0.200", "0.205", "0.210", "0.215", "0.225", "0.230", "0.235", "0.240", #03n
    "0.250", "0.255", "0.260", "0.265", "0.275", "0.280", "0.285", "0.290", "0.300", "0.305", #04n
    "0.310", "0.315", "0.325", "0.330", "0.335", "0.340", "0.350", "0.355", "0.360", "0.365", #05n
    "0.375", "0.380", "0.385", "0.390", "0.400", "0.405", "0.410", "0.415", "0.425", "0.430", #06n
    "0.435", "0.440", "0.450", "0.455", "0.460", "0.465", "0.475", "0.480", "0.485", "0.490", #07n
    "0.500", "0.505", "0.510", "0.515", "0.525", "0.530", "0.535", "0.540", "0.550", "0.555", #08n
    "0.560", "0.565", "0.575", "0.580", "0.585", "0.590", "0.600", "0.605", "0.610", "0.615", #09n
    "0.625", "0.630", "0.635", "0.640", "0.650", "0.655", "0.660", "0.665", "0.675", "0.680", #10n
    "0.685", "0.690", "0.700", "0.705", "0.710", "0.715", "0.725", "0.730", "0.735", "0.740", #11n
    "0.750", "0.755", "0.760", "0.765", "0.775", "0.780", "0.785", "0.790", "0.800", "0.805", #12n
    "0.810", "0.815", "0.825", "0.830", "0.835", "0.840", "0.850", "0.855", "0.860", "0.865", #13n
    "0.875", "0.880", "0.885", "0.890", "0.900", "0.905", "0.910", "0.915", "0.925", "0.930", #14n
    "0.935", "0.940", "0.950", "0.955", "0.960", "0.965", "0.975", "0.980", "0.985", "0.990"] #15n


ByteArray = bytearray([0x42,
            0x44,
            0x4a,
            0x56,
            0x4b,
            0x59,
            0x4c,
            0x4f,
            0x6f,
            0x4d,
            0x6d,
            0x61,
            0x62,
            0x63,
            0x64,
            0x65,
            0x66,
            0x67,
            0x68,
            0x46,
            0x38,
            0x36])

MsgArray = ["Low battery",
           "Cancel low battery",
           "Tranciever RX",
           "Cancel reciever RX",
           "Tranciever TX",
           "Cancel RX, TX or DUAL-RX",
           "TX timeout (stuck mic)",
           "DUAL mode on",
           "DUAL mode off",
           "DUAL-RX active",
           "DUAL-RX stby",
           "ADC error",
           "Antenna impedance mismatch – high VSWR",
           "FPAA error, startup blocked",
           "Frequency synthesizer error",
           "PLL error",
           "Key inputs blocked",
           "I2C bus error",
           "Antenna switch error or damaged D10 diode",
           "Clear all errors",
           "8.33 kHz step",
           "25 kHz step"]

# ----------------------o0 Display Helper Functions 0o----------------------
# Vector/line-drawn font for fast rendering - draws using simple lines instead of bitmaps

# 7-segment style digit definitions (much faster than bitmap fonts)
# Each digit defined as list of line segments: (x1, y1, x2, y2)
# Coordinates are relative to character position, scaled for size
DIGIT_SEGMENTS = {
    '0': [(1,0,11,0), (11,0,11,20), (11,20,1,20), (1,20,1,0)],  # Rectangle
    '1': [(6,0,6,20)],  # Vertical line
    '2': [(1,0,11,0), (11,0,11,10), (11,10,1,10), (1,10,1,20), (1,20,11,20)],  # 2
    '3': [(1,0,11,0), (11,0,11,20), (11,20,1,20), (1,10,11,10)],  # 3
    '4': [(1,0,1,10), (1,10,11,10), (11,0,11,20)],  # 4
    '5': [(11,0,1,0), (1,0,1,10), (1,10,11,10), (11,10,11,20), (11,20,1,20)],  # 5
    '6': [(11,0,1,0), (1,0,1,20), (1,20,11,20), (11,20,11,10), (11,10,1,10)],  # 6
    '7': [(1,0,11,0), (11,0,11,20)],  # 7
    '8': [(1,0,11,0), (11,0,11,20), (11,20,1,20), (1,20,1,0), (1,10,11,10)],  # 8
    '9': [(11,20,11,0), (11,0,1,0), (1,0,1,10), (1,10,11,10)],  # 9
    '.': [(0,18,2,20), (2,20,0,20)],  # Period at bottom
    'n': [(0,10,0,20), (0,10,6,10), (6,10,6,20)],  # Small n
    ' ': []  # Space - no lines
}

def draw_line_pixels(display, x1, y1, x2, y2):
    """
    Draw a line using Bresenham's algorithm with pixel()
    """
    dx = abs(x2 - x1)
    dy = abs(y2 - y1)
    sx = 1 if x1 < x2 else -1
    sy = 1 if y1 < y2 else -1
    err = dx - dy
    
    while True:
        display.pixel(int(x1), int(y1))  # ssd1306py pixel() only takes x, y
        if x1 == x2 and y1 == y2:
            break
        e2 = 2 * err
        if e2 > -dy:
            err -= dy
            x1 += sx
        if e2 < dx:
            err += dx
            y1 += sy

def draw_vector_text(display, text, x, y, char_width=14, char_height=24):
    """
    Draw text using vector/line-drawn characters - VERY FAST
    Much faster than bitmap fonts because it draws simple lines using pixel()
    """
    if not hasattr(display, 'pixel'):
        # Fallback to regular text if pixel drawing not available
        display.text(text, x, y, 8)
        return
    
    offset_x = 0
    for char in text:
        if char in DIGIT_SEGMENTS:
            segments = DIGIT_SEGMENTS[char]
            for seg in segments:
                x1, y1, x2, y2 = seg
                # Scale and position the segment
                sx1 = x + offset_x + x1
                sy1 = y + y1
                sx2 = x + offset_x + x2
                sy2 = y + y2
                # Draw the line segment using pixel-by-pixel drawing
                draw_line_pixels(display, sx1, sy1, sx2, sy2)
        offset_x += char_width
    
    return offset_x


boot_tics = time.ticks_ms()

while True:
    now = time.time()
    
    # ----------------------o0 Start of bitbanging 0o----------------------

    # Read from UART if data available
    data = ''

    try:
        if serialData and serialData.any():
            data = serialData.read(1)
    except:
        print("serialData.any() fail")
        data = b''
    
    if data != '':
        print(f"Raw response: {data}")

    if array[0] != '':
        print(f"ArrAy: {array}")

    # The radio is sending 'S' to check if we are there    
    if data == b'S':    
        serialData.write(b'x')      # We are indeed, responding with an 'x'
        #print("Sent 'x' in response to 'S': " + str(now)) 

        ComEstablished = True               # Set the flag
        TimeComEstablished = time.time()    # Noteing the time communication was established
        question_radio2pi = time.time()     # Noteing the time of last question

        # Resetting the timeout timers for com check
        if ComEstablished and not ComEstablished_old:
            print("ComEstablished changed to True: " + str(now))
            question_pi2radio = now      
            reply_pi2radio = now

        array = [''] * 30                   # Resetting array
        array_pointer = 0                   # Resetting array pointer   

    # Radio replies with ACK in response from an earlier message from us
    elif data == b'\x06' and array_pointer == 0:
        print(f"Radio replied OK")

        # Confirming that setpoints has been accepted by the radio
        if volume_sp != volume:
            volume = volume_sp

        if squelch_sp != squelch:
            squelch = squelch_sp

        if stby_mhz_sp != stby_mhz:

            print("A : " + str(stby_mhz_sp))
            print("B : " + str(stby_mhz))

            print("C : " + str(StandbyFrequency[0]))

            stby_mhz = stby_mhz_sp
            print("D : " + str(stby_mhz))

            StandbyFrequency[0] = stby_mhz

            print("E : " + str(StandbyFrequency[0]))


        if stby_channel_sp != stby_channel:
            
            print("F : " + str(stby_channel_sp))
            print("G : " + str(stby_channel))

            stby_channel = stby_channel_sp

            print("H : " + str(stby_channel))

            StandbyFrequency[1] = DecArray[tmp_pointer][1:]

            print("I : " + str(StandbyFrequency[1]))

        if switch_active_standby:

            print("K : " + str(ActiveFrequency[0]))
            print("L : " + str(ActiveFrequency[1]))
            temp_mhz = ActiveFrequency[0]
            temp_khz = ActiveFrequency[1]

            print("M : " + str(temp_mhz))
            print("N : " + str(temp_khz))

            print("O : " + str(StandbyFrequency[0]))
            print("P : " + str(StandbyFrequency[1]))
            ActiveFrequency[0] = StandbyFrequency[0]
            ActiveFrequency[1] = StandbyFrequency[1]
            
            
            StandbyFrequency[0] = temp_mhz
            StandbyFrequency[1] = temp_khz

            print("Q : " + str(ActiveFrequency[0]))
            print("R : " + str(ActiveFrequency[1]))

            switch_active_standby = False
            print("Switched active and standby frequencies")
            print("Active frequency: " + str(ActiveFrequency[0]) + str(ActiveFrequency[1]))
            print("Standby frequency: " + str(StandbyFrequency[0]) + str(StandbyFrequency[1]))

    # Radio replies with NAK in response from an earlier message from us
    elif data == b'\x15' and array_pointer == 0:
        print(f"*doh*, radio replied Not OK")

        # Reverting setpoints
        if volume_sp != volume:
            volume_sp = volume

        if squelch_sp != squelch:
            squelch_sp = squelch

        if stby_mhz_sp != stby_mhz:
            stby_mhz_sp = stby_mhz_sp

        if stby_channel_sp != stby_channel:
            stby_channel_sp = stby_channel

        if switch_active_standby:
            switch_active_standby = False

    # Radio replies with SOH since we earelier sent 'S' to chack duplex communication
    elif data == b'\x01' and array_pointer == 0:
        DuplexComEstablished = True             # Nice, we have duplex communication
        print(f"Radio replied with SOH at start of message: " + str(now)) 
        reply_pi2radio = now

    # Something else received, store in array
    elif data != '':
        array[array_pointer] = data       # Write to buffer array
        #print(f"Array contents: {array}")       # Print the content of the array
        array_pointer += 1                      # Nothing up the array pointer

        # *doh* ... something messed up, the array pointer is out of bounds
        if array_pointer >= len(array):
            print("Array pointer out " + str(array_pointer) + "of bounds, resetting array and pointer")
            print(f"Active array: {array}")
            array = [''] * 30                   # Resetting array
            array_pointer = 0                   # Resetting array pointer   

    # Sending a 'S' to the radio to check if communication is duplex 
    if now - question_pi2radio > 4 and ComEstablished:
        serialData.write(b'S')                  # Sending an 'S' to radio           
        #print("Sent 'S' to radio: " + str(now)) 
        question_pi2radio = now                 # Noteing the time of last question

    # It has been a while since last 'S'-question
    if now - question_radio2pi > 45 and ComEstablished:
        print("Radio not sending 'S'-question, communication timed out: " + str(now)) 
        ComEstablished = False                  # Communication lost

    # It has been a while since last reply from radio
    if now - reply_pi2radio > 6 and ComEstablished:
        print("No reply from radio, communication timed out: " + str(now)) 
        ComEstablished = False                  # Communication lost

    # Something is wrong, Throw the array to the floor.
    if array[0] != b'\x01' and array[0] != b'\x02' and array[0] != b'\x06' and array[0] != b'\x15' and array[0] != '':
        array = [''] * 30                       # Resetting array
        array_pointer = 0                       # Resetting array pointer   


    # ----------------------o0 User input handling 0o----------------------
    # Note: On Pico, use GPIO buttons instead of stdin keyboard input
    # This is placeholder for hardware buttons integration

    # Example button pins (adjust to your setup):
    # button_plus = Pin(20, Pin.IN, Pin.PULL_UP)
    # button_minus = Pin(21, Pin.IN, Pin.PULL_UP)
    # button_enter = Pin(22, Pin.IN, Pin.PULL_UP)

    # For now, keyboard input via UART is simplified:

    # User wants to quit
    #if char == 'q':
    #    print("So long and thanks for all the fish.")
    #    serialData.deinit()
    #    break

    char = ''
    
    # Leave splash screen
    if menu == 0 and ComEstablished:
        menu = 1

    # Show normal screen
    if menu == 1 and volume != -1:
        menu = 10

    # Someone is pressing volume plus
    if not vol_plus() and vol_plus_old and vol_minus:
        vol_plus_pressed_time = time.ticks_ms()
        print("vol_plus_pressed_time = " + str(vol_plus_pressed_time))

    if vol_plus() and not vol_plus_old:
        print("tics = " + str(time.ticks_ms()))
        print("time = " + str(vol_plus_pressed_time))
        print("vol_minus time = " + str(time.ticks_ms() - vol_plus_pressed_time))
        
        # User wants to increase volume
        if time.ticks_diff(time.ticks_ms(), vol_plus_pressed_time) < short_press_ms:  # Short press
            print("Up arrow pressed")
            volume_sp += 1                      # Increase volume setpoint
            if volume_sp > 20:                  # Max volume reached
                volume_sp = 20                  
            checksum = squelch + intercom       # Calculate checksum
            serialData.write(bytes([0x02, 0x41, volume_sp, squelch, intercom, checksum]))  # Send volume command
            time.sleep(0.15)                     # Short delay to allow processing

        else:  # User wants to increase squelch
            #if time.ticks_diff(time.ticks_ms(), vol_plus_pressed_time) >= short_press_ms:  # Long press
            print("Up arrow pressed")
            squelch_sp += 1                      # Increase volume setpoint
            if squelch_sp > 20:                  # Max volume reached
                squelch_sp = 20                  
            checksum = squelch + intercom       # Calculate checksum
            serialData.write(bytes([0x02, 0x41, volume_sp, squelch, intercom, checksum]))  # Send volume command
            time.sleep(0.15)                     # Short delay to allow processing

    # Someone is pressing volume minus
    if not vol_minus() and vol_minus_old and vol_plus():
        vol_minus_pressed_time = time.ticks_ms()
        print("vol_minus_pressed_time = " + str(vol_minus_pressed_time))

    if vol_minus() and not vol_minus_old:
        # User wants to increase volume
        
        print("tics = " + str(time.ticks_ms()))
        print("time = " + str(vol_minus_pressed_time))
        print("vol_minus time = " + str(time.ticks_ms() - vol_minus_pressed_time))

        if time.ticks_diff(time.ticks_ms(), vol_minus_pressed_time) < short_press_ms:  # Short press
            print("Short down arrow pressed")
            volume_sp -= 1                      # Decrease volume setpoint
            if volume_sp < 1:                   # Min volume reached
                volume_sp = 1
            checksum = squelch + intercom       # Calculate checksum
            serialData.write(bytes([0x02, 0x41, volume_sp, squelch, intercom, checksum]))  # Send volume command
            time.sleep(0.15)                    # Short delay to allow processing

        else: # User wants to increase squelch
            #if time.ticks_diff(time.ticks_ms(), vol_minus_pressed_time) >= short_press_ms:  # Long press
            print("Long down arrow pressed")
            squelch_sp -= 1                      # Decrease volume setpoint
            if squelch_sp < 1:                   # Min volume reached
                squelch_sp = 1
            checksum = squelch + intercom       # Calculate checksum
            serialData.write(bytes([0x02, 0x41, volume_sp, squelch, intercom, checksum]))  # Send volume command
            time.sleep(0.15)                    # Short delay to allow processing


    # freq_plus = Pin(4, Pin.IN, Pin.PULL_UP)
    # freq_enter = Pin(5, Pin.IN, Pin.PULL_UP)
    # freq_minus = Pin(6, Pin.IN, Pin.PULL_UP)

    # Someone is pressing enter frequency menu
    if not freq_enter() and freq_enter_old:
        freq_enter_time = time.ticks_ms()

    if freq_enter() and not freq_enter_old and menu == 10 and stby_mhz >= 0:
 
        # User wants to change frequency
        if time.ticks_diff(time.ticks_ms(), freq_enter_time) < short_press_ms:  # Short press
            # Enter requency menu
            stby_mhz_sp = stby_mhz                   # Set MHz setpoint to current MHz
            print("MHz SP = " + str(stby_mhz_sp))    # Showing current MHz setpoint
            
            tmp_pointer = stby_channel_sp            # Set channel setpoint to current channel
            print("Channel sp: " + str(stby_channel_sp) + ", " + DecArray[stby_channel_sp])
            
            menu = 20                           # Entering the menu

        else: # User wants to switch main and standby frequencies
            #if time.ticks_diff(time.ticks_ms(), freq_enter_time) >= short_press_ms:  # Long press
            serialData.write(bytes([0x02, 0x43]))  # Send volume command
            switch_active_standby = True
            time.sleep(0.15)                     # Short delay to allow processing

        
    # User wants to increase mHz setpoint
    elif not freq_plus() and freq_plus_old and menu == 20:
        stby_mhz_sp += 1                         # Notching up setpoint

        if stby_mhz_sp > 136:                    # End of airband. 
            stby_mhz_sp = 118                    # Continuing from bottom.

        print("Meny: " + str(menu))         # Showing current menu
        print("MHz SP = " + str(stby_mhz_sp))    # Showing current MHz setpoint
        char = ''                           # Clear char variable
    
    # User wants to decrease mHz setpoint
    elif not freq_minus() and freq_minus_old and menu == 20:
        stby_mhz_sp -= 1                         # Notching down setpoint
        if stby_mhz_sp < 118:                    # End of airband
            stby_mhz_sp = 136                    # Continuing from top

        print("Meny: " + str(menu))         # Showing current menu
        print("MHz SP = " + str(stby_mhz_sp))    # Showing current MHz setpoint

    # User wants to enter nXX kHz menu
    elif not freq_enter() and freq_enter_old and menu == 20:
        print("A: " + str(stby_channel_sp))
        tmp_pointer = stby_channel_sp          # Set kHz setpoint to current kHz
        print("Meny: " + str(menu))         # Showing current menu
        print("kHz SP = " + str(DecArray[tmp_pointer])[:3] + 'xx')    # Showing current kHz setpoint
        menu = 30

    # User wants to increase kHz setpoint
    elif not freq_plus() and freq_plus_old and menu == 30:
        print("Meny: " + str(menu))         # Showing current menu
        tmp_pointer += 16                   # Notching up setpoint
        if tmp_pointer >= len(DecArray):    # End of array
            tmp_pointer = len(DecArray) - tmp_pointer      # Continuing from start
        print("kHz SP = " + str(DecArray[tmp_pointer])[:3] + 'xx')    # Showing current kHz setpoint
    
    # User wants to decrease kHz setpoint
    elif not freq_minus() and freq_minus_old and menu == 30:
        print("Meny: " + str(menu))         # Showing current menu
        tmp_pointer -= 16                    # Notching down setpoint
        if tmp_pointer < 0:                 # End of array
            tmp_pointer = len(DecArray) + tmp_pointer - 1  # Continuing from start
        print("kHz SP = " + str(DecArray[tmp_pointer])[:3] + 'xx')    # Showing current kHz setpoint

    # User wants to enter Xnn kHz menu
    elif not freq_enter() and freq_enter_old and menu == 30:
        menu = 40
        print("Meny: " + str(menu))         # Showing current menu
        print("kHz SP = " + str(DecArray[tmp_pointer]))    # Showing current kHz setpoint

    # User wants to increase kHz setpoint
    elif not freq_plus() and freq_plus_old and menu == 40:
        print("Meny: " + str(menu))         # Showing current menu
        tmp_pointer += 1                    # Notching up setpoint
        if tmp_pointer >= len(DecArray):    # End of array
            tmp_pointer = 0                 # Continuing from start
        print("kHz SP = " + str(DecArray[tmp_pointer]))    # Showing current kHz setpoint
    
    # User wants to decrease kHz setpoint
    elif not freq_minus() and freq_minus_old and menu == 40:
        print("Meny: " + str(menu))         # Showing current menu
        tmp_pointer -= 1                    # Notching down setpoint
        if tmp_pointer < 0:                 # End of array
            tmp_pointer = len(DecArray)-1   # Continuing from end
        print("kHz SP = " + str(DecArray[tmp_pointer]))    # Showing current kHz setpoint

    # User wants to set frequency
    elif not freq_enter() and freq_enter_old and menu == 40:
        print("Meny: " + str(menu))             # Showing current menu
        stby_channel_sp = (HexArray[tmp_pointer])    # Setting channel setpoint
        checksum = int(stby_mhz_sp) ^ stby_channel_sp     # Calculate checksum4
        khz_sp = str(DecArray[tmp_pointer])[1:]            # Setting kHz setpoint
        print("Channel SP: " + str(stby_channel_sp) + ", tmp_pointer: " + str(tmp_pointer))
        print("Sending to radio: " + str(stby_mhz_sp) + str(DecArray[tmp_pointer])[1:])  # Showing frequency being sent

        serialData.write(bytes([0x02, 0x52, int(stby_mhz_sp), stby_channel_sp, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20, checksum]))  # Send volume command
        menu = 10                           # Exiting menu
        time.sleep(0.15)                     # Short delay to allow processing

    elif char == 'A' and menu == 10:     # Replace with actual condition to activate dual mode
        serialData.write(bytes([0x02, 0x4F]))  # Send command

    elif char == 'a' and menu == 10:     # Replace with actual condition to deactivate dual mode
        serialData.write(bytes([0x02, 0x6F]))  # Send command

    elif char == 'B' and menu == 10:     # Call next User-Defined Memory Channel to Standby Field Message
        serialData.write(bytes([0x02, 0x57]))  # Send command

    elif char == 'b' and menu == 10:     # Call previous User-Defined Memory Channel to Standby Field Message
        serialData.write(bytes([0x02, 0x77]))  # Send command

    elif char == 'C' and menu == 10:     # Set Channel Spacing to 8.33kHz 
        serialData.write(bytes([0x02, 0x38]))  # Send command

    elif char == 'c' and menu == 10:     # Set Channel Spacing to 25kHz 
        serialData.write(bytes([0x02, 0x36]))  # Send command
    
    elif char == 'D' and menu == 10:     # Configure PPT buttons
        #serialData.write(bytes([0x02, 0x32, 0x00]))  # Pilot only
        #serialData.write(bytes([0x02, 0x32, 0x01]))  # Co-pilot only
        serialData.write(bytes([0x02, 0x32, 0x02]))  # Both
    
    elif char == 'E' and menu == 10:     # Set intercom volume
        #serialData.write(bytes([0x02, 0x33, 0x01]))  # Intercom volume = 1
        serialData.write(bytes([0x02, 0x33, 0x04]))  # Intercom volume = 4
        #serialData.write(bytes([0x02, 0x33, 0x09]))  # Intercom volume = 9
        
    elif char == 'F' and menu == 10:     # Set external input volume
        #serialData.write(bytes([0x02, 0x34, 0x01]))  # External input volume = 1
        serialData.write(bytes([0x02, 0x34, 0x04]))  # External input volume = 4
        #serialData.write(bytes([0x02, 0x34, 0x09]))  # External input volume = 9

    elif char == 'G' and menu == 10:     # Set side tone level
        #serialData.write(bytes([0x02, 0x31, 0x01]))  # Side tone level = 1
        serialData.write(bytes([0x02, 0x31, 0x04]))  # Side tone level = 4
        #serialData.write(bytes([0x02, 0x31, 0x09]))  # Side tone level = 9

    elif char == 'H' and menu == 10:     # Set external input volume
        #serialData.write(bytes([0x02, 0x34, 0x01]))  # External input volume = 1
        serialData.write(bytes([0x02, 0x34, 0x04]))  # External input volume = 4
        #serialData.write(bytes([0x02, 0x34, 0x09]))  # External input volume = 9

    elif char == 'I' and menu == 10:     # Set Pilot- and Copilot-Side Microphone Gain
        #serialData.write(bytes([0x02, 0x49, 0x01]))  # Pilot- and Copilot-Side Microphone Gain = 1
        serialData.write(bytes([0x02, 0x49, 0x04]))  # Pilot- and Copilot-Side = 4
        #serialData.write(bytes([0x02, 0x49, 0x09]))  # Pilot- and Copilot-Side = 9

    elif char == 'J' and menu == 10:     # Set Copilot-Side Microphone Gain
        #serialData.write(bytes([0x02, 0x4A, 0x01]))  # Copilot-Side Microphone Gain = 1
        serialData.write(bytes([0x02, 0x4A, 0x04]))  # Copilot-Side Microphone Gain = 4
        #serialData.write(bytes([0x02, 0x4A, 0x09]))  # Copilot-Side Microphone Gain = 9

    # ----------------------o0 Handling of incoming medssages =o----------------------

    # Active Frequency Message
    if array[0] == b'\x02' and array[1] == b'\x55' and array[12] != '':
        print("Active frequency received:")
        #print(f"Array contents: {array}")

        try:
            mhz = ord(array[2])                        # Assigning MHz value
            channel = HexArray.index(int(hex(ord(array[3])), 16))     # Finding out the decimals
            khz = DecArray[channel]                         # Assigning a readable kHz value
        except:
            print(f"Error parsing message: {e}")        # Failing gracefully    

        ActiveFrequency = [str(mhz), str(khz)[1:]]          # Storing active frequency

        print("Active frequency: " + str(ActiveFrequency[0]) +  str(ActiveFrequency[1]))    # Showing them is someone is interested
        print("Standby frequency: " + str(StandbyFrequency[0]) + str(StandbyFrequency[1]))

        #print(f"Active array: {array}")

        array = [''] * 30               # Resetting the leftovers
        array_pointer = 0               # Resetting array pointer       
        
    # Standby Frequency Message
    if array[0] == b'\x02' and array[1] == b'\x52' and array[12] != '':
        print("Standby frequency received:")
        #print(f"Array contents: {array}")

        try:
            stby_mhz = ord(array[2])                        # Assigning MHz value
            stby_channel = HexArray.index(int(hex(ord(array[3])), 16))     # Finding out the decimals
            stby_khz = DecArray[stby_channel]                   # Assigning a readable kHz value
        except Exception as e:
            print(f"Error parsing message: {e}")        # Failing gracefully    

        StandbyFrequency = [str(stby_mhz), str(stby_khz)[1:]]   # Storing standby frequency

        stby_mhz_sp = stby_mhz                        # Set MHz setpoint to current MHz
        stby_channel_sp = stby_channel                # Set kHz setpoint to current kHz

        print("Active frequency: " + str(ActiveFrequency[0]) + str(ActiveFrequency[1]))    # Showing them is someone is interested
        print("Standby frequency: " + str(StandbyFrequency[0]) + str(StandbyFrequency[1]))

        #print(f"Standby array: {array}")

        array = [''] * 30        # Resetting the leftovers
        array_pointer = 0        # Resetting array pointer

    # Volume Message
    elif array[0] == b'\x02' and array[1] == b'\x41' and array[4] != '':
        print("Volume received:")
        #print(f"Array contents: {array}")
        volume_hex = array[2]

        #volume = int(array[2], 16)
        volume = int(array[2].hex(), 16)

        volume_sp = volume
        
        squelch_hex = array[3]
        
        #squelch = int(array[3], 16)
        squelch = int(array[3].hex(), 16)
        
        squelch_sp = squelch

        intercom_hex = array[4]
        #intercom = int(array[4], 16)
        intercom = int(array[4].hex(), 16)
        intercom_sp = intercom

        print(f"Volume Level: {volume} Squelch Level: {squelch} Intercom Level: {intercom}")

        array = [''] * 30
        array_pointer = 0

    # Active and Standby Switch Message
    elif array[0] == b'\x02' and array[1] == b'\x43':
        print("Active and standby switched:")

        temp_mhz = ActiveFrequency[0]
        temp_khz = ActiveFrequency[1]

        ActiveFrequency[0] = StandbyFrequency[0]
        ActiveFrequency[1] = StandbyFrequency[1]

        StandbyFrequency[0] = temp_mhz
        StandbyFrequency[1] = temp_khz

        print("Active frequency: " + str(ActiveFrequency[0]) + str(ActiveFrequency[1]))
        print("Standby frequency: " + str(StandbyFrequency[0]) + str(StandbyFrequency[1]))

        #print(f"Array contents: {array}")

        array = [''] * 30
        array_pointer = 0

    # PTT Settings Message
    elif array[0] == b'\x02' and array[1] == b'\x32'  and array[2] != '':
        print("PTT settings received:")
        #print(f"Array contents: {array}")
        array = [''] * 30
        array_pointer = 0

    # Intercom Volume Message
    elif array[0] == b'\x02' and array[1] == b'\x33'  and array[2] != '':
        print("Intercom volume received:")
        #print(f"Array contents: {array}")

        array = [''] * 30
        array_pointer = 0

    # External Volume Message
    elif array[0] == b'\x02' and array[1] == b'\x34'  and array[2] != '':
        print("External volume received:")
        #print(f"Array contents: {array}")

        array = [''] * 30
        array_pointer = 0

    # Side Tone Settings Message
    elif array[0] == b'\x02' and array[1] == b'\x31'  and array[2] != '':
        print("Side tone settings received:")
        #print(f"Array contents: {array}")

        array = [''] * 30
        array_pointer = 0

    # Mic Gain Pilot Settings Message
    elif array[0] == b'\x02' and array[1] == b'\x49'  and array[2] != '':
        print("Mic gain pilot settings received:")
        #print(f"Array contents: {array}")

        array = [''] * 30
        array_pointer = 0


    # Mic Gain Copilot Settings Message
    elif array[0] == b'\x02' and array[1] == b'\x4A'  and array[2] != '':
        print("Mic gain copilot settings received:")
        #print(f"Array contents: {array}")

        array = [''] * 30
        array_pointer = 0

    elif array[0] == b'\x02' and array[1] != b'':
        # Convert the byte to ASCII character
        byte_char = array[1].decode() if isinstance(array[1], bytes) else array[1]
        
        for i in range(0, len(ByteArray)):
            msg_char = chr(ByteArray[i])
            
            if msg_char == byte_char:
                print(MsgArray[i])
                array = [''] * 30
                array_pointer = 0


                """elif array[0] == b'\x02' and array[1] != b'':
                    for i in range(0, len(ByteArray)):
                        if ByteArray[i] == array[1][0]:  # Compare the first byte value directly
                            print(MsgArray[i])
                            array = [''] * 30
                            array_pointer = 0

                # 
                elif array[0] == b'\x02' and array[1] != b'':
                    for i in range(0, len(ByteArray), 1):
                        #if ByteArray[i] == array[1]:  # Now comparing strings
                        print("x: " + chr(ByteArray[i]))
                        print("y: " + array[1].decode())
                       
                        if chr(ByteArray[i]) == array[1].decode():  # Now comparing strings
                            print(MsgArray[i])
                            array = [''] * 30
                            array_pointer = 0

                # Mic Gain Copilot Settings Message
                elif array[0] == b'\x02' and array[1] == b'\x38':
                    print("08.33 kHz")
                    #print(f"Array contents: {array}")

                    array = [''] * 30
                    array_pointer = 0"""

    # ----------------------o0 Display handling 0o----------------------
    # Using SSD1306 OLED display with I2C on GPIO8(SDA)/GPIO9(SCL)
    # OPTIMIZED: Using vector/line-drawn font for fast rendering
    
    if OLED_AVAILABLE and display is not None:
        
        if menu == 0 and (menu_old != menu):
            # Display update for menu 10 - Main frequency display
            display.clear()
            
            display.text(f"Radio remote", 0, 0, 8)
            display.text(rev_string, 0, 16, 8)
            display.text(f"Awaiting radio", 0, 26, 8)
            display.text(f"PLS STBY", 0, 46, 8)
            
            print("menu = Boot")
                
            display.show()

        if menu == 1 and (menu_old != menu):
            # Display update for menu 10 - Main frequency display
            display.clear()
            
            display.text("     DISCO!", 0, 24, 8)
                
            display.show()

        if menu == 10 and (menu_old != menu or volume_old != volume or squelch_old != squelch or ActiveFrequency0_old != ActiveFrequency[0] or ActiveFrequency1_old != ActiveFrequency[1] or StandbyFrequency0_old != StandbyFrequency[0] or StandbyFrequency1_old != StandbyFrequency[1]):
            # Display update for menu 10 - Main frequency display
            display.clear()
            
            display.text(f"V:{volume:2d} S:{squelch:2d} M:{menu}", 0, 0, 8)

            freq_str = f"{ActiveFrequency[0]}{ActiveFrequency[1]}"
            draw_vector_text(display, freq_str, 0, 16)  # Fast vector font - line 2
            print("freq_str: "+ freq_str)
            
            stby_freq_str = f"{StandbyFrequency[0]}{StandbyFrequency[1]}"
            draw_vector_text(display, stby_freq_str, 0, 43)  # Fast vector font - line 3

            print("menu = " + str(menu) + ", stby_freq_str: "+ stby_freq_str)
                
            display.show()
            
        elif menu == 20 and (menu_old != menu or volume_old != volume or squelch_old != squelch or ActiveFrequency0_old != ActiveFrequency[0] or ActiveFrequency1_old != ActiveFrequency[1] or StandbyFrequency0_old != StandbyFrequency[0] or stby_mhz_sp_old != stby_mhz_sp):
            # Display update for menu 20 - MHz selection
            display.clear()
            
            display.text(f"V:{volume:2d} S:{squelch:2d} M:{menu}", 0, 0, 8)

            #freq_str = f"{ActiveFrequency[0]}{ActiveFrequency[1]}"
            #draw_vector_text(display, freq_str, 0, 16)  # Fast vector font - line 2
            #print("freq_str: "+ freq_str)
            
            stby_freq_str = str(stby_mhz_sp) + ".nnn"
            draw_vector_text(display, stby_freq_str, 0, 43)  # Fast vector font - line 3
            
            print("menu = " + str(menu) + ", stby_freq_str: "+ stby_freq_str)

            display.show()
            
        elif menu == 30 and (menu_old != menu or volume_old != volume or squelch_old != squelch or ActiveFrequency0_old != ActiveFrequency[0] or ActiveFrequency1_old != ActiveFrequency[1] or StandbyFrequency0_old != StandbyFrequency[0] or tmp_pointer_old != tmp_pointer):
            # Display update for menu 30 - kHz coarse selection (x10)
            display.clear()

            display.text(f"V:{volume:2d} S:{squelch:2d} M:{menu}", 0, 0, 8)

            #freq_str = f"{ActiveFrequency[0]}{ActiveFrequency[1]}"
            #draw_vector_text(display, freq_str, 0, 16)  # Fast vector font - line 2
            #print("freq_str: "+ freq_str)
            
            stby_freq_str = str(stby_mhz_sp) + DecArray[tmp_pointer][1:3] + "nn"
            draw_vector_text(display, stby_freq_str, 0, 43)  # Fast vector font - line 3

            print("menu = " + str(menu) + ", stby_freq_str: "+ stby_freq_str)
           
            display.show()
            
        elif menu == 40 and (menu_old != menu or volume_old != volume or squelch_old != squelch or ActiveFrequency0_old != ActiveFrequency[0] or ActiveFrequency1_old != ActiveFrequency[1] or StandbyFrequency0_old != StandbyFrequency[0] or tmp_pointer_old != tmp_pointer):
            # Display update for menu 40 - kHz fine selection (x1)
            display.clear()

            display.text(f"V:{volume:2d} S:{squelch:2d} M:{menu}", 0, 0, 8)

            #freq_str = f"{ActiveFrequency[0]}{ActiveFrequency[1]}"
            #draw_vector_text(display, freq_str, 0, 16)  # Fast vector font - line 2
            #print("freq_str: "+ freq_str)
            
            stby_freq_str = str(stby_mhz_sp) + DecArray[tmp_pointer][1:]
            draw_vector_text(display, stby_freq_str, 0, 43)  # Fast vector font - line 3
            
            print("menu = " + str(menu) + ", stby_freq_str: "+ stby_freq_str)

            display.show()


    # Flank triggering
    vol_plus_old = vol_plus()
    vol_minus_old = vol_minus()
    freq_plus_old = freq_plus()
    freq_enter_old = freq_enter()
    freq_minus_old = freq_minus()
    menu_old = menu
    volume_old = volume
    squelch_old = squelch
    intercom_old = intercom 
    stby_mhz_sp_old = stby_mhz_sp
    stby_channel_sp_old = stby_channel_sp
    tmp_pointer_old = tmp_pointer
    ActiveFrequency0_old = ActiveFrequency[0]
    ActiveFrequency1_old = ActiveFrequency[1]
    StandbyFrequency0_old = StandbyFrequency[0]
    StandbyFrequency1_old = StandbyFrequency[1]
    ComEstablished_old = ComEstablished
    
    # Small delay to prevent CPU spinning
    time.sleep(0.01)





