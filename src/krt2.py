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
Step25khz = False
ActiveFrequency = ["",""]
StandbyFrequency = ["",""]

array = [''] * 30
array_pointer = 0


while True:
    now = time.time() #/1000
    data = serialData.read(1)
    #print(f"Raw response ({len(data)} bytes): {data.hex()}")

    if data == b'S':
        serialData.write(b'x')
        print("Sent 'x' in response to 'S'")
        time.sleep(0.1)
        last_response = time.time() #/1000

    elif data.hex() == '01' and array_pointer == 0:
        print(f"Radio replied with SOH at start of message")

    elif data.hex() != '':
        array[array_pointer] = data.hex()
        print(f"Array contents: {array}")
        array_pointer += 1
        if array_pointer >= len(array):
            array_pointer = 0

    if now - last_response > 1 and last_response != 0:
        serialData.write(b'S')
        print("Sent 'S' to radio")
        last_response = now

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

        array = [''] * 30
        array_pointer = 0
        
    elif array[0] == '02' and array[1] == '52'  and array[12] != '':
        print("Channel standby frequency received:")

        # Parse 0x02 0x55 message (frequency and name)
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

        #print(f"Array contents: {array}")
        array = [''] * 30
        array_pointer = 0

    elif array[0] == '02' and array[1] == '41' and array[5] != '':
        print("Volume received:")
        #print(f"Array contents: {array}")
        volume = int(array[2], 16)
        squelch = int(array[3], 16)
        intercom = int(array[4], 16)
        print(f"Volume Level: {volume} Squelch Level: {squelch} Intercom Level: {intercom}")
        array = [''] * 30
        array_pointer = 0

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

    elif array[0] == '02' and array[1] == '32'  and array[2] != '':
        print("PTT settings received:")
        #print(f"Array contents: {array}")
        array = [''] * 30
        array_pointer = 0

    elif array[0] == '02' and array[1] == '33'  and array[2] != '':
        print("Intercom volume received:")
        #print(f"Array contents: {array}")
        array = [''] * 30
        array_pointer = 0

    elif array[0] == '02' and array[1] == '34'  and array[2] != '':
        print("External volume received:")
        #print(f"Array contents: {array}")
        array = [''] * 30
        array_pointer = 0

    elif array[0] == '02' and array[1] == '31'  and array[2] != '':
        print("Side tone settings received:")
        #print(f"Array contents: {array}")
        array = [''] * 30
        array_pointer = 0

    elif array[0] == '02' and array[1] == '38':
        print("8.33 kHz step detected")
        Step25khz = False
        #print(f"Array contents: {array}")
        array = [''] * 30
        array_pointer = 0

    elif array[0] == '02' and array[1] == '36':
        print("25 kHz step detected")
        Step25khz = True
        #print(f"Array contents: {array}")
        array = [''] * 30
        array_pointer = 0

    elif array[0] == '02' and array[1] == '49'  and array[2] != '':
        print("Mic gain pilot settings received:")
        #print(f"Array contents: {array}")
        array = [''] * 30
        array_pointer = 0

    elif array[0] == '02' and array[1] == '4A'  and array[2] != '':
        print("Mic gain copilot settings received:")
        #print(f"Array contents: {array}")
        array = [''] * 30
        array_pointer = 0

    elif array[0] == '02' and array[1] == '57':
        print("Call Next User-Defined Memory Channel to Standby Field received")
        #print(f"Array contents: {array}")
        array = [''] * 30
        array_pointer = 0

    elif array[0] == '02' and array[1] == '77':
        print("Call Previous User-Defined Memory Channel to Standby Field received")
        #print(f"Array contents: {array}")
        array = [''] * 30
        array_pointer = 0

    elif array[0] == '02' and array[1] == '4F':
        print("Activate DUAL Mode received")
        #print(f"Array contents: {array}")
        array = [''] * 30
        array_pointer = 0

    elif array[0] == '02' and array[1] == '6F':
        print("Deactivate DUAL Mode received")
        #print(f"Array contents: {array}")
        array = [''] * 30
        array_pointer = 0
