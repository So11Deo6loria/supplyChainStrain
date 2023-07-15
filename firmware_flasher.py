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
    send_log_line(f"Restart IoT board in the next 3 seconds...")
    time.sleep(3)
    send_log_line(f"Preparing file {file_path}...")
    with open(file_path, 'rb') as file:
        with serial.Serial(serial_port, baudrate=115200, timeout=1) as ser:
            send_log_line(f"Writing secret key...")
            ser.write(b'password')  # Start XModem-1K transfer with NAK

            response = None
            while response != b'C':
                response = ser.read(1)
                time.sleep(0.25)

            send_log_line('Transmitting Firmware...')

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
                send_log_line('File transfer successful.')
                return 'File transfer successful.'
            else:
                send_log_line('File transfer failed.')
                return 'File transfer failed.'
