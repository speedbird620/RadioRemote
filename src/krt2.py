#!/usr/bin/env python3

"""
KTR2 Serial Port Listener
Listens on /dev/ttyAMA0 @ 9600 baud for "S" command
Uses binary protocol from KTR2 manual
"""

import serial
import sys
import signal
import time

serialData = serial.Serial('/dev/ttyAMA0',9600, timeout=0.1) 

last_response = 0
ComEstablished = False
TimeComEstablished = 0
Step25khz = False
volume = 0
volume_x = 0
volume_hex = ''
squelch = 0
squelch_hex = ''
intercom = 0
intercom_hex = ''
ActiveFrequency = ['','']
StandbyFrequency = ['','']
x = False
y = 0

array = [''] * 30
array_pointer = 0

HexArray = [
    0x00, 0x01, 0x02, 0x03, 0x05, 0x06, 0x07, 0x08, 0x0A, 0x0B,
    0x0C, 0x0D, 0x0F, 0x10, 0x11, 0x12, 0x14, 0x15, 0x16, 0x17,
    0x19, 0x1A, 0x1B, 0x1C, 0x1E, 0x1F, 0x20, 0x21, 0x23, 0x24,
    0x25, 0x26, 0x28, 0x29, 0x2A, 0x2B, 0x2D, 0x2E, 0x2F, 0x30,
    0x32, 0x33, 0x34, 0x35, 0x37, 0x38, 0x39, 0x3A, 0x3C, 0x3D,
    0x3E, 0x3F, 0x41, 0x42, 0x43, 0x44, 0x46, 0x47, 0x48, 0x49,
    0x4B, 0x4C, 0x4D, 0x4E, 0x50, 0x51, 0x52, 0x53, 0x55, 0x56,
    0x57, 0x58, 0x5A, 0x5B, 0x5C, 0x5D, 0x5F, 0x60, 0x61, 0x62,
    0x64, 0x65, 0x66, 0x67, 0x69, 0x6A, 0x6B, 0x6C, 0x6E, 0x6F,
    0x70, 0x71, 0x73, 0x74, 0x75, 0x76, 0x78, 0x79, 0x7A, 0x7B,
    0x7D, 0x7E, 0x7F, 0x80, 0x82, 0x83, 0x84, 0x85, 0x87, 0x88,
    0x89, 0x8A, 0x8C, 0x8D, 0x8E, 0x8F, 0x91, 0x92, 0x93, 0x94,
    0x96, 0x97, 0x98, 0x99, 0x9B, 0x9C, 0x9D, 0x9E, 0xA0, 0xA1,
    0xA2, 0xA3, 0xA5, 0xA6, 0xA7, 0xA8, 0xAA, 0xAB, 0xAC, 0xAD,
    0xAF, 0xB0, 0xB1, 0xB2, 0xB4, 0xB5, 0xB6, 0xB7, 0xB9, 0xBA,
    0xBB, 0xBC, 0xBE, 0xBF, 0xC0, 0xC1, 0xC3, 0xC4, 0xC5, 0xC6
]

DecArray = [
    0.000, 0.005, 0.010, 0.015, 0.025, 0.030, 0.035, 0.040, 0.050, 0.055,
    0.060, 0.065, 0.075, 0.080, 0.085, 0.090, 0.100, 0.105, 0.110, 0.115,
    0.125, 0.130, 0.135, 0.140, 0.150, 0.155, 0.160, 0.165, 0.175, 0.180,
    0.185, 0.190, 0.200, 0.205, 0.210, 0.215, 0.225, 0.230, 0.235, 0.240,
    0.250, 0.255, 0.260, 0.265, 0.275, 0.280, 0.285, 0.290, 0.300, 0.305,
    0.310, 0.315, 0.325, 0.330, 0.335, 0.340, 0.350, 0.355, 0.360, 0.365,
    0.375, 0.380, 0.385, 0.390, 0.400, 0.405, 0.410, 0.415, 0.425, 0.430,
    0.435, 0.440, 0.450, 0.455, 0.460, 0.465, 0.475, 0.480, 0.485, 0.490,
    0.500, 0.505, 0.510, 0.515, 0.525, 0.530, 0.535, 0.540, 0.550, 0.555,
    0.560, 0.565, 0.575, 0.580, 0.585, 0.590, 0.600, 0.605, 0.610, 0.615,
    0.625, 0.630, 0.635, 0.640, 0.650, 0.655, 0.660, 0.665, 0.675, 0.680,
    0.685, 0.690, 0.700, 0.705, 0.710, 0.715, 0.725, 0.730, 0.735, 0.740,
    0.750, 0.755, 0.760, 0.765, 0.775, 0.780, 0.785, 0.790, 0.800, 0.805,
    0.810, 0.815, 0.825, 0.830, 0.835, 0.840, 0.850, 0.855, 0.860, 0.865,
    0.875, 0.880, 0.885, 0.890, 0.900, 0.905, 0.910, 0.915, 0.925, 0.930,
    0.935, 0.940, 0.950, 0.955, 0.960, 0.965, 0.975, 0.980, 0.985, 0.990
]

while True:
    now = time.time() #/1000
    data = serialData.read(1)
    #print(f"Raw response ({len(data)} bytes): {data.hex()}")

    # Respond to 'S' command from radio
    if data == b'S':
        serialData.write(b'x')
        print("Sent 'x' in response to 'S'")
        time.sleep(0.1)
        ComEstablished = True
        TimeComEstablished = time.time() 
        last_response = time.time() 
        array = [''] * 30
        array_pointer = 0

    # Radio replies with SOH at start of message
    elif data.hex() == '01' and array_pointer == 0:

        print(f"Radio replied with SOH at start of message")

    # Radio replies with SOH at start of message
    elif data.hex() == '06' and array_pointer == 0:
        print(f"Radio replied OK")

    # Radio replies with SOH at start of message
    elif data.hex() == '15' and array_pointer == 0:
        print(f"Radio replied Not OK")

    # Something else received, store in array
    elif data.hex() != '':
        array[array_pointer] = data.hex()
        print(f"Array contents: {array}")
        array_pointer += 1
        if array_pointer >= len(array):
            array_pointer = 0

    if TimeComEstablished + 5 < now and TimeComEstablished > 0 and not x and ComEstablished:

        #volume = 12
        #squelch = 4
        #intercom = 6
        #volume = volume - 1
        checksum = squelch + intercom
        serialData.write(bytes([0x02, 0x41, volume, squelch, intercom, checksum]))  # Send volume command
        print("Sent volume command")

        # 123.375: '02', '55', '7b', '4b', '20', '20', '20', '20', '20', '20', '20', '20', '30',
        # 123.000: '02', '52', '7b', '00', '20', '20', '20', '20', '20', '20', '20', '20', '7b',

        x = True

    if TimeComEstablished + 1 < now and TimeComEstablished > 0 and ComEstablished:

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

        x = False

    if now - last_response > 1 and last_response != 0:
        serialData.write(b'S')
        print("Sent 'S' to radio")
        last_response = now


    # Active Frequency Message
    if array[0] == '02' and array[1] == '55' and array[12] != '':
        print("Channel active frequency received:")
        print(f"Array contents: {array}")

        # Parse 0x02 0x55 message (frequency and name)
        try:
            mhz = str(int(array[2], 16))
            khz = str(round((int(array[3], 16) * 0.005), 3))

            if len(khz) == 3:
                khz = khz + '0'
            if len(khz) == 4:
                khz = khz + '0'
                        
        except Exception as e:
            print(f"Error parsing message: {e}")

        ActiveFrequency = [mhz, khz[1:]]

        print("Active frequency: " + ActiveFrequency[0] +  ActiveFrequency[1])
        print("Standby frequency: " + StandbyFrequency[0] + StandbyFrequency[1])

        print(f"Active array: {array}")
        array = [''] * 30
        array_pointer = 0
        
    # Standby Frequency Message
    elif array[0] == '02' and array[1] == '52'  and array[12] != '':
        print("Channel standby frequency received:")

        # Parse 0x02 0x52 message (frequency and name)
        try:
            mhz = str(int(array[2], 16))
            khz = str(round((int(array[3], 16) * 0.005), 3))

            if len(khz) == 3:
                khz = khz + '0'
            if len(khz) == 4:
                khz = khz + '0'
            
            print("Active frequency: " + ActiveFrequency[0] + ActiveFrequency[1])
            print("Standby frequency: " + StandbyFrequency[0] + StandbyFrequency[1])
            
        except Exception as e:
            print(f"Error parsing message: {e}")

        StandbyFrequency = [mhz, khz[1:]]

        print("Active frequency: " + ActiveFrequency[0] + ActiveFrequency[1])
        print("Standby frequency: " + StandbyFrequency[0] + StandbyFrequency[1])

        print(f"Stby array: {array}")
        array = [''] * 30
        array_pointer = 0

    # Volume Message
    elif array[0] == '02' and array[1] == '41' and array[5] != '':
        print("Volume received:")
        #print(f"Array contents: {array}")
        volume_hex = array[2]
        volume = int(array[2], 16)
        squelch_hex = array[3]
        squelch = int(array[3], 16)
        intercom_hex = array[4]
        intercom = int(array[4], 16)
        print(f"Volume Level: {volume} Squelch Level: {squelch} Intercom Level: {intercom}")
        array = [''] * 30
        array_pointer = 0

    # Active and Standby Switch Message
    elif array[0] == '02' and array[1] == '43'  and array[2] != '':
        print("Active and standby switched:")

        temp_mhz = ActiveFrequency[0]
        temp_khz = ActiveFrequency[1]

        ActiveFrequency[0] = StandbyFrequency[0]
        ActiveFrequency[1] = StandbyFrequency[1]

        StandbyFrequency[0] = temp_mhz
        StandbyFrequency[1] = temp_khz

        print("Active frequency: " + ActiveFrequency[0] + ActiveFrequency[1])
        print("Standby frequency: " + StandbyFrequency[0] + StandbyFrequency[1])

        #print(f"Array contents: {array}")
        array = [''] * 30
        array_pointer = 0

    # PTT Settings Message
    elif array[0] == '02' and array[1] == '32'  and array[2] != '':
        print("PTT settings received:")
        #print(f"Array contents: {array}")
        array = [''] * 30
        array_pointer = 0

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

    # 8.33 kHz Step Message
    elif array[0] == '02' and array[1] == '38':
        print("8.33 kHz step detected")
        Step25khz = False
        #print(f"Array contents: {array}")
        array = [''] * 30
        array_pointer = 0

    # 25 kHz Step Message
    elif array[0] == '02' and array[1] == '36':
        print("25 kHz step detected")
        Step25khz = True
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

    # Call Next User-Defined Memory Channel to Standby Field Message
    elif array[0] == '02' and array[1] == '57':
        print("Call Next User-Defined Memory Channel to Standby Field received")
        #print(f"Array contents: {array}")
        array = [''] * 30
        array_pointer = 0

    # Call Previous User-Defined Memory Channel to Standby Field Message
    elif array[0] == '02' and array[1] == '77':
        print("Call Previous User-Defined Memory Channel to Standby Field received")
        #print(f"Array contents: {array}")
        array = [''] * 30
        array_pointer = 0

    # Activate DUAL Mode Message
    elif array[0] == '02' and array[1] == '4F':
        print("Activate DUAL Mode received")
        #print(f"Array contents: {array}")
        array = [''] * 30
        array_pointer = 0

    # Deactivate DUAL Mode Message
    elif array[0] == '02' and array[1] == '6F':
        print("Deactivate DUAL Mode received")
        #print(f"Array contents: {array}")
        array = [''] * 30
        array_pointer = 0
