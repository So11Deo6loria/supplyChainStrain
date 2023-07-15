import serial
import time
import struct

def crc16(data):
    crc = 0
    for byte in data:
        crc ^= byte << 8
        for _ in range(8):
            if crc & 0x8000:
                crc = (crc << 1) ^ 0x1021
            else:
                crc <<= 1
    return crc & 0xFFFF

def send_file(serial_port, file_path, send_log_line):
    def send_password():
        ser.write(b'password')
    
    xmodemReady = False
    send_log_line(f"Preparing file {file_path}...")
    send_log_line(f"Restart IoT board in the next 3 seconds...")
    with open(file_path, 'rb') as file:
        with serial.Serial(serial_port, baudrate=115200, timeout=1) as ser:
            start_time = time.time()
            send_log_line(f"Attempting to write secret key...")
            send_password()
            while( ( not xmodemReady ) and ( time.time() - start_time < 3 ) ):                
                for i in range(10): 
                    response = ser.read(1)
                    print(repr(response))
                    if( response == b'*' ):
                        xmodemReady = True
                    time.sleep(0.01)

            if( xmodemReady ):
                response = None
                start_time = time.time()
                targetReady = False
                send_log_line("Waiting for XModem1K Ready...")
                while( ( not targetReady ) and ( time.time() - start_time < 15 ) ):
                    response = ser.read(1)
                    print(repr(response))
                    if( response == b'C' ):
                        targetReady = True
                    time.sleep(0.1)
                
                if( targetReady ):
                    send_log_line('Transmitting Firmware...')
                else:
                    return 'XModem1K Ready Timed Out...'    
            else:
                return 'Password Prompt Timed Out...'

            packet_number = 1
            while True:
                data = file.read(1024)
                if not data:
                    break

                header = bytearray(b'\x02')
                header.extend(struct.pack('B', packet_number))
                header.extend(struct.pack('B', 255 - packet_number))
                header.extend(data)

                if len(data) < 1024:
                    header.extend(b'\x1A' * (1024 - len(data)))

                crc16_val = crc16(header[3:])
                header.extend(struct.pack('>H', crc16_val))
                ser.write(header)

                response = ser.read(1)
                if response == b'\x06':
                    packet_number = (packet_number + 1) % 256
                else:
                    send_log_line('Error in transmission. Retransmitting packet...')
                    time.sleep(1)

            ser.write(b'\x04')
            response = ser.read(1)

            if response == b'\x06':
                return 'File transfer successful.'
            else:
                return 'File transfer failed.'
