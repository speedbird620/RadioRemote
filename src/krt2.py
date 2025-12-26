#!/usr/bin/env python3

"""
KTR2 Serial Port Listener
Listens on /dev/ttyAMA0 @ 9600 baud for "S" command
Uses binary protocol from KTR2 manual
"""

import select
import serial
import sys
import signal
import time

serialData = serial.Serial('/dev/ttyAMA0',9600, timeout=0.1) 

question_radio2pi = 0

reply_pi2radio = 0
question_pi2radio = 0

ComEstablished = False
ComEstablished_old = False
DuplexComEstablished = False
TimeComEstablished = 0
Step25khz = False
menu = 10
volume = 0
volume_sp = 0
squelch = 0
squelch_sp = 0
intercom = 0
mhz = 118
stby_mhz = 118
mhz_sp = 118
khz = 0.0
channel = 0
stby_channel = 0
channel_sp = 0
tmp_pointer = 0
intercom_sp = 0
ActiveFrequency = ['','']
StandbyFrequency = ['','']
switch_active_standby = False

x = False
y = 0

array = [''] * 30
array_pointer = 0

#   .n00   .n05   .n10   .n15   .n25   .n30   .n35   .n40   .n50   .n55   .n60  .n65    .n75   .n80   .n85   .n90             
HexArray = [
    0x00,  0x01,  0x02,  0x03,  0x05,  0x06,  0x07,  0x08,  0x0A,  0x0B,  0x0C,  0x0D,  0x0F,  0x10,  0x11,  0x12, #.0nn
    0x14,  0x15,  0x16,  0x17,  0x19,  0x1A,  0x1B,  0x1C,  0x1E,  0x1F,  0x20,  0x21,  0x23,  0x24,  0x25,  0x26, #.1nn
    0x28,  0x29,  0x2A,  0x2B,  0x2D,  0x2E,  0x2F,  0x30,  0x32,  0x33,  0x34,  0x35,  0x37,  0x38,  0x39,  0x3A, #.2nn
    0x3C,  0x3D,  0x3E,  0x3F,  0x41,  0x42,  0x43,  0x44,  0x46,  0x47,  0x48,  0x49,  0x4B,  0x4C,  0x4D,  0x4E, #.3nn
    0x50,  0x51,  0x52,  0x53,  0x55,  0x56,  0x57,  0x58,  0x5A,  0x5B,  0x5C,  0x5D,  0x5F,  0x60,  0x61,  0x62, #.4nn
    0x64,  0x65,  0x66,  0x67,  0x69,  0x6A,  0x6B,  0x6C,  0x6E,  0x6F,  0x70,  0x71,  0x73,  0x74,  0x75,  0x76, #.5nn
    0x78,  0x79,  0x7A,  0x7B,  0x7D,  0x7E,  0x7F,  0x80,  0x82,  0x83,  0x84,  0x85,  0x87,  0x88,  0x89,  0x8A, #.6nn
    0x8C,  0x8D,  0x8E,  0x8F,  0x91,  0x92,  0x93,  0x94,  0x96,  0x97,  0x98,  0x99,  0x9B,  0x9C,  0x9D,  0x9E, #.7nn
    0xA0,  0xA1,  0xA2,  0xA3,  0xA5,  0xA6,  0xA7,  0xA8,  0xAA,  0xAB,  0xAC,  0xAD,  0xAF,  0xB0,  0xB1,  0xB2, #.8nn
    0xB4,  0xB5,  0xB6,  0xB7,  0xB9,  0xBA,  0xBB,  0xBC,  0xBE,  0xBF,  0xC0,  0xC1,  0xC3,  0xC4,  0xC5,  0xC6] #.9nn


DecArray = [
    "0.000", "0.005", "0.010", "0.015", "0.025", "0.030", "0.035", "0.040", "0.050", "0.055", "0.060", "0.065", "0.075", "0.080", "0.085", "0.090", 
    "0.100", "0.105", "0.110", "0.115", "0.125", "0.130", "0.135", "0.140", "0.150", "0.155", "0.160", "0.165", "0.175", "0.180", "0.185", "0.190", 
    "0.200", "0.205", "0.210", "0.215", "0.225", "0.230", "0.235", "0.240", "0.250", "0.255", "0.260", "0.265", "0.275", "0.280", "0.285", "0.290", 
    "0.300", "0.305", "0.310", "0.315", "0.325", "0.330", "0.335", "0.340", "0.350", "0.355", "0.360", "0.365", "0.375", "0.380", "0.385", "0.390", 
    "0.400", "0.405", "0.410", "0.415", "0.425", "0.430", "0.435", "0.440", "0.450", "0.455", "0.460", "0.465", "0.475", "0.480", "0.485", "0.490",
    "0.500", "0.505", "0.510", "0.515", "0.525", "0.530", "0.535", "0.540", "0.550", "0.555", "0.560", "0.565", "0.575", "0.580", "0.585", "0.590", 
    "0.600", "0.605", "0.610", "0.615", "0.625", "0.630", "0.635", "0.640", "0.650", "0.655", "0.660", "0.665", "0.675", "0.680", "0.685", "0.690", 
    "0.700", "0.705", "0.710", "0.715", "0.725", "0.730", "0.735", "0.740", "0.750", "0.755", "0.760", "0.765", "0.775", "0.780", "0.785", "0.790", 
    "0.800", "0.805", "0.810", "0.815", "0.825", "0.830", "0.835", "0.840", "0.850", "0.855", "0.860", "0.865", "0.875", "0.880", "0.885", "0.890", 
    "0.900", "0.905", "0.910", "0.915", "0.925", "0.930", "0.935", "0.940", "0.950", "0.955", "0.960", "0.965", "0.975", "0.980", "0.985", "0.990"]

MsgArray = ['42',"Low battery",
            '44',"Cancel low battery",
            '4A',"RX",
            '56',"Cancel RX",
            '4B',"TX",
            '59',"Cancel RX, TX or DUAL-RX",
            '4C',"TX timeout",
            '4F',"DUAL mode on",
            '6F',"DUAL mode off",
            '4D',"DUAL-RX active",
            '6D',"DUAL-RX stby",
            '61',"ADC error",
            '62',"Antenna impedance mismatch – high VSWR",
            '63',"FPAA error, startup blocked",
            '64',"Frequency synthesizer error",
            '65',"PLL error",
            '66',"Key inputs blocked",
            '67',"I2C bus error",
            '68',"Antenna switch error or damaged D10 diode",
            '46',"Clear all errors",
            '38',"8.33 kHz step",
            '36',"25 kHz step",
            ]


while True:
    now = time.time() #/1000
    
    data = serialData.read(1)   # Reading one byte from serial port
    #if data != b'': 
    #    print(f"Raw response: {data.hex()}")

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
    elif data.hex() == '06' and array_pointer == 0:
        print(f"Radio replied OK")

        # Confirming that setpoints has been accepted by the radio
        if volume_sp != volume:
            volume = volume_sp

        if mhz_sp != stby_mhz:
            stby_mhz = mhz_sp
            StandbyFrequency[0] = stby_mhz

        if channel_sp != stby_channel:
            stby_channel = channel_sp
            StandbyFrequency[1] = stby_channel

        if switch_active_standby:
            temp_mhz = ActiveFrequency[0]
            temp_khz = ActiveFrequency[1]
            ActiveFrequency[0] = StandbyFrequency[0]
            ActiveFrequency[1] = StandbyFrequency[1]
            StandbyFrequency[0] = temp_mhz
            StandbyFrequency[1] = temp_khz
            switch_active_standby = False
            print("Switched active and standby frequencies")
            print("Active frequency: " + str(ActiveFrequency[0]) + str(ActiveFrequency[1]))
            print("Standby frequency: " + str(StandbyFrequency[0]) + str(StandbyFrequency[1]))

    # Radio replies with NAK in response from an earlier message from us
    elif data.hex() == '15' and array_pointer == 0:
        print(f"Bugger, radio replied Not OK")

        # Reverting setpoints
        if volume_sp != volume:
            volume_sp = volume

        if mhz_sp != stby_mhz:
            mhz_sp = stby_mhz

        if channel_sp != khz:
            channel_sp = khz  

        if switch_active_standby:
            switch_active_standby = False

    # Radio replies with SOH since we earelier sent 'S' to chack duplex communication
    elif data.hex() == '01' and array_pointer == 0:
        DuplexComEstablished = True             # Nice, we have duplex communication
        #print(f"Radio replied with SOH at start of message: " + str(now)) 
        reply_pi2radio = now

    # Something else received, store in array
    elif data.hex() != '':
        array[array_pointer] = data.hex()       # Write to buffer array
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
    if now - question_radio2pi > 32 and ComEstablished:
        #print("Radio not sending 'S'-question, communication timed out: " + str(now)) 
        ComEstablished = False                  # Communication lost

    # It has been a while since last reply from radio
    if now - reply_pi2radio > 6 and ComEstablished:
        #print("No reply from radio, communication timed out: " + str(now)) 
        ComEstablished = False                  # Communication lost

    # Something is wrong, Throw the array to the floor.
    if array[0] != '01' and array[0] != '02' and array[0] != '06' and array[0] != '15' and array[0] != '':
        array = [''] * 30                       # Resetting array
        array_pointer = 0                       # Resetting array pointer   


    # Test code for an Raspberry PI 5 in Visual Studio Code
    # A character is sent to the Rpi5 via keyboard. Note character needs Enter to be sent
    if select.select([sys.stdin], [], [], 0)[0]:
        char = sys.stdin.readline().strip() # Reading the character from keyboard

        # User wants to quit
        if char == 'q':
            print("So long and thanks for all the fish.")
            serialData.close()                  # Closing the serial connection
            sys.exit(0)                         # Bye

        # User wants to increase volume
        if char == '+':
            print("Up arrow pressed")
            volume_sp += 1                      # Increase volume setpoint
            checksum = squelch + intercom       # Calculate checksum
            serialData.write(bytes([0x02, 0x41, volume_sp, squelch, intercom, checksum]))  # Send volume command
            char = ''                           # Clear char variable
            time.sleep(0.15)                     # Short delay to allow processing

        # User wants to increase volume
        if char == '-':
            print("Down arrow pressed")
            volume_sp -= 1                      # Decrease volume setpoint
            checksum = squelch + intercom       # Calculate checksum
            serialData.write(bytes([0x02, 0x41, volume_sp, squelch, intercom, checksum]))  # Send volume command
            char = ''                           # Clear char variable
            time.sleep(0.15)                     # Short delay to allow processing

        # User wants to switch active and standby frequencies
        if char == '5':
            print("Switch is pressed")
            serialData.write(bytes([0x02, 0x43]))  # Send volume command
            switch_active_standby = True
            char = ''                           # Clear char variable
            time.sleep(0.15)                     # Short delay to allow processing

        # User wants to enter frequency menu
        if char == '4' and menu == 10:
            mhz_sp = stby_mhz                        # Set MHz setpoint to current MHz
            print("MHz SP = " + str(mhz_sp))    # Showing current MHz setpoint
            char = ''                           # Clear char variable
            menu = 20                           # Entering the menu
            
        # User wants to increase mHz setpoint
        elif char == '8' and menu == 20:
            mhz_sp += 1                         # Notching up setpoint

            if mhz_sp > 136:                    # End of airband. 
                mhz_sp = 118                    # Continuing from bottom.

            print("Meny: " + str(menu))         # Showing current menu
            print("MHz SP = " + str(mhz_sp))    # Showing current MHz setpoint
            char = ''                           # Clear char variable
        
        # User wants to decrease mHz setpoint
        elif char == '2' and menu == 20:
            mhz_sp -= 1                         # Notching down setpoint
            if mhz_sp < 118:                    # End of airband
                mhz_sp = 136                    # Continuing from top

            print("Meny: " + str(menu))         # Showing current menu
            print("MHz SP = " + str(mhz_sp))    # Showing current MHz setpoint
            char = ''                           # Clear char variable

        # User wants to enter nXX kHz menu
        elif char == '4' and menu == 20:
            tmp_pointer = stby_channel               # Set kHz setpoint to current kHz
            print("Meny: " + str(menu))         # Showing current menu
            print("kHz SP = " + str(DecArray[tmp_pointer])[:3] + 'xx')    # Showing current kHz setpoint
            menu = 30
            char = ''                           # Clear char variable

        # User wants to increase kHz setpoint
        elif char == '8' and menu == 30:
            print("Meny: " + str(menu))         # Showing current menu
            tmp_pointer += 16                   # Notching up setpoint
            if tmp_pointer >= len(DecArray):    # End of array
                tmp_pointer = len(DecArray) - tmp_pointer      # Continuing from start
            print("kHz SP = " + str(DecArray[tmp_pointer])[:3] + 'xx')    # Showing current kHz setpoint
            char = ''                           # Clear char variable
        
        # User wants to decrease kHz setpoint
        elif char == '2' and menu == 30:
            print("Meny: " + str(menu))         # Showing current menu
            tmp_pointer -= 16                    # Notching down setpoint
            if tmp_pointer < 0:                 # End of array
                tmp_pointer = len(DecArray) + tmp_pointer - 1  # Continuing from start
            print("kHz SP = " + str(DecArray[tmp_pointer])[:3] + 'xx')    # Showing current kHz setpoint
            char = ''                           # Clear char variable

        # User wants to enter Xnn kHz menu
        elif char == '4' and menu == 30:
            menu = 40
            print("Meny: " + str(menu))         # Showing current menu
            print("kHz SP = " + str(DecArray[tmp_pointer]))    # Showing current kHz setpoint
            char = ''                           # Clear char variable

        # User wants to increase kHz setpoint
        elif char == '8' and menu == 40:
            print("Meny: " + str(menu))         # Showing current menu
            tmp_pointer += 1                    # Notching up setpoint
            if tmp_pointer >= len(DecArray):    # End of array
                tmp_pointer = 0                 # Continuing from start
            print("kHz SP = " + str(DecArray[tmp_pointer]))    # Showing current kHz setpoint
            char = ''                           # Clear char variable
        
        # User wants to decrease kHz setpoint
        elif char == '2' and menu == 40:
            print("Meny: " + str(menu))         # Showing current menu
            tmp_pointer -= 1                    # Notching down setpoint
            if tmp_pointer < 0:                 # End of array
                tmp_pointer = len(DecArray)-1   # Continuing from end
            print("kHz SP = " + str(DecArray[tmp_pointer]))    # Showing current kHz setpoint
            char = ''                           # Clear char variable

        # User wants to set frequency
        elif char == '4' and menu == 40:
            print("Meny: " + str(menu))             # Showing current menu
            channel_sp = (HexArray[tmp_pointer])    # Setting channel setpoint
            checksum = int(mhz_sp) ^ channel_sp     # Calculate checksum4
            print("Sending to radio: " + str(mhz_sp) + str(DecArray[tmp_pointer])[1:])  # Showing frequency being sent
            serialData.write(bytes([0x02, 0x52, int(mhz_sp), channel_sp, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20, checksum]))  # Send volume command
            menu = 10                           # Exiting menu
            char = ''                           # Clear char variable
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




    """if TimeComEstablished + 5 < now and TimeComEstablished > 0 and not x and ComEstablished:

        #volume = 12
        #squelch = 4
        #intercom = 6
        #volume = volume - 1
        checksum = squelch + intercom
        serialData.write(bytes([0x02, 0x41, volume, squelch, intercom, checksum]))  # Send volume command
        print("Sent volume command")

        # 123.375: '02', '55', '7b', '4b', '20', '20', '20', '20', '20', '20', '20', '20', '30',
        # 123.000: '02', '52', '7b', '00', '20', '20', '20', '20', '20', '20', '20', '20', '7b',

        x = True"""

    """if TimeComEstablished + 1 < now and TimeComEstablished > 0 and ComEstablished:

        y = y + 1
        mHz_x = 123
        channel_x = HexArray[y]
        checksum = mHz_x ^ channel_x

        #                        '02', '52', '7b',  '00', '20', '20', '20', '20', '20', '20', '20', '20', '7b',
        serialData.write(bytes([0x02, 0x52, mHz_x, channel_x, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20, checksum]))  # Send volume command
        #serialData.write(bytes([0x02, 0x52, mHz_x, channel_x, 0x48, 0x45, 0x4a, 0x45, 0x4c, 0x49, 0x41, 0x53, checksum]))  # Hej Elias
        print("Sent standby frequency command")
        time.sleep(0.1)

        TimeComEstablished = time.time() 

        x = False"""


    # Active Frequency Message
    if array[0] == '02' and array[1] == '55' and array[12] != '':
        print("Channel active frequency received:")
        #print(f"Array contents: {array}")

        # Parse 0x02 0x55 message (frequency and name)
        try:
            mhz = int(array[2], 16)
            
            # Find array[3] hex value in HexArray to get channel index
            channel = HexArray.index(int(array[3], 16))
            khz = DecArray[channel]
                        
        except Exception as e:
            print(f"Error parsing message: {e}")

        ActiveFrequency = [str(mhz), str(khz)[1:]]

        print("Active frequency: " + str(ActiveFrequency[0]) +  str(ActiveFrequency[1]))
        print("Standby frequency: " + str(StandbyFrequency[0]) + str(StandbyFrequency[1]))

        print(f"Active array: {array}")

        array = [''] * 30
        array_pointer = 0
        
    # Standby Frequency Message
    if array[0] == '02' and array[1] == '52' and array[12] != '':
        print("Standby frequency received:")
        #print(f"Array contents: {array}")

        # Parse 0x02 0x52 message (frequency and name)
        try:
            stby_mhz = int(array[2], 16)
            
            # Find array[3] hex value in HexArray to get channel index
            stby_channel = HexArray.index(int(array[3], 16))
            stby_khz = DecArray[stby_channel]
                        
        except Exception as e:
            print(f"Error parsing message: {e}")

        StandbyFrequency = [str(stby_mhz), str(stby_khz)[1:]]

        mhz_sp = stby_mhz                        # Set MHz setpoint to current MHz
        channel_sp = stby_channel                # Set kHz setpoint to current kHz

        print("Active frequency: " + str(ActiveFrequency[0]) + str(ActiveFrequency[1]))
        print("Standby frequency: " + str(StandbyFrequency[0]) + str(StandbyFrequency[1]))

        print(f"Standby array: {array}")

        array = [''] * 30
        array_pointer = 0

    # Volume Message
    elif array[0] == '02' and array[1] == '41' and array[4] != '':
        print("Volume received:")
        #print(f"Array contents: {array}")
        volume_hex = array[2]
        volume = int(array[2], 16)
        volume_sp = volume
        
        squelch_hex = array[3]
        squelch = int(array[3], 16)
        squelch_sp = squelch

        intercom_hex = array[4]
        intercom = int(array[4], 16)
        intercom_sp = intercom

        print(f"Volume Level: {volume} Squelch Level: {squelch} Intercom Level: {intercom}")

        array = [''] * 30
        array_pointer = 0

    # Active and Standby Switch Message
    elif array[0] == '02' and array[1] == '43':
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
    elif array[0] == '02' and array[1] == '32'  and array[2] != '':
        print("PTT settings received:")
        #print(f"Array contents: {array}")
        shift_array(3)
        #array = [''] * 30
        #array_pointer = 0

    # Intercom Volume Message
    elif array[0] == '02' and array[1] == '33'  and array[2] != '':
        print("Intercom volume received:")
        #print(f"Array contents: {array}")

        array = [''] * 30
        array_pointer = 0

    # External Volume Message
    elif array[0] == '02' and array[1] == '34'  and array[2] != '':
        print("External volume received:")
        #print(f"Array contents: {array}")

        array = [''] * 30
        array_pointer = 0

    # Side Tone Settings Message
    elif array[0] == '02' and array[1] == '31'  and array[2] != '':
        print("Side tone settings received:")
        #print(f"Array contents: {array}")

        array = [''] * 30
        array_pointer = 0

    # Mic Gain Pilot Settings Message
    elif array[0] == '02' and array[1] == '49'  and array[2] != '':
        print("Mic gain pilot settings received:")
        #print(f"Array contents: {array}")

        array = [''] * 30
        array_pointer = 0


    # Mic Gain Copilot Settings Message
    elif array[0] == '02' and array[1] == '4A'  and array[2] != '':
        print("Mic gain copilot settings received:")
        #print(f"Array contents: {array}")

        array = [''] * 30
        array_pointer = 0

    # 
    elif array[0] == '02':
        for i in range(0, len(MsgArray), 2):  # Search every second element (0, 2, 4, 6, etc)
            if MsgArray[i] == array[2]:    # If hex code matches
                print(MsgArray[i + 1])  # Return the description (odd index)
                array = [''] * 30
                array_pointer = 0   





    # Flank triggering
    ComEstablished_old = ComEstablished