import sys
import socket
import struct
import time
import select

server = "2beta2t.net"
port = 25565
username = "YawningCheese01"

def send_packet(s, id, data):
    s.sendall(struct.pack(f'>b', id) + data)

def encode_string16(string):
    return struct.pack(f'>h{len(string) * 2}s', len(string), string.encode('utf-16-be'))

packet_lengths = {
    1: 15,
    4: 8,
    5: 10,
    6: 12,
    7: 9,
    8: 2,
    9: 1,
    0x0d: 41,
    0x0e: 11,
    0x10: 2,
    0x11: 14,
    0x12: 5,
    0x13: 5,
    0x15: 24,
    0x16: 8,
    0x1b: 18,
    0x1c: 10,
    0x1d: 4,
    0x1e: 4,
    0x1f: 7,
    0x20: 6,
    0x21: 9,
    0x22: 18,
    0x26: 5,
    0x27: 8,
    0x32: 9,
    0x35: 11,
    0x36: 12,
    0x3d: 17,
    0x46: 1,
    0x47: 17,
    0x65: 1,
    0x69: 5,
    0x6a: 4,
    0xc8: 5
}

def m():
    prev_time = time.time()

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((server, port))
        print("Connected to server. Sending login...")
        send_packet(s, 2, encode_string16(username))

        while True:
            if time.time() - prev_time > 0.5:
                send_packet(s, 0, b'')
                prev_time = time.time()

            if select.select([sys.stdin], [], [], 0) != ([],[],[]):
                send_packet(s, 3, encode_string16(sys.stdin.readline()))

            if select.select([s], [], [], 0) != ([],[],[]):
                data = s.recv(1)
                if data == b'':
                    continue
                
                packet_id = struct.unpack('>B', data)[0]

                if packet_id == 2:
                    length = struct.unpack('>h', s.recv(2))[0]
                    temp2 = s.recv(length * 2).decode('utf-16-be')
                    print(temp2)
                    if temp2 == "-":
                        send_packet(s, 1, struct.pack('>i', 14) + encode_string16(username) + struct.pack('>qb', 0, 0))
                elif packet_id == 3:
                    length = struct.unpack('>h', s.recv(2))[0]
                    print(s.recv(length * 2).decode('utf-16-be'))
                elif packet_id == 0x0f:
                    s.recv(10)
                    if struct.unpack('>h', s.recv(2))[0] >= 0:
                        s.recv(3)
                elif packet_id == 0x14:
                    s.recv(4)
                    length = struct.unpack('>h', s.recv(2))[0]
                    s.recv(length + 16)
                elif packet_id == 0x17:
                    s.recv(17)
                    if struct.unpack('>i', s.recv(4))[0] > 0:
                        s.recv(6)
                elif packet_id == 0x18:
                    s.recv(19)
                    val = s.recv(1)
                    while val != b'\x7f':
                        val = s.recv(1)
                elif packet_id == 0x19:
                    s.recv(4)
                    s.recv(struct.unpack('>h', s.recv(2))[0] + 16)
                elif packet_id == 0x28:
                    s.recv(4)
                    val = s.recv(1)
                    while val != b'\x7f':
                        val = s.recv(1)
                elif packet_id == 0x33:
                    s.recv(13)
                    s.recv(struct.unpack('>i', s.recv(4))[0])
                elif packet_id == 0x34:
                    s.recv(8)
                    length = struct.unpack('>h', s.recv(2))[0]
                    s.recv(4 * length)
                elif packet_id == 0x3c:
                    s.recv(28)
                    s.recv(struct.unpack('>i', s.recv(4))[0] * 3)
                elif packet_id == 0x64:
                    s.recv(2)
                    length = struct.unpack('>h', s.recv(2))[0]
                    s.recv(length)
                    s.recv(1)
                elif packet_id == 0x67:
                    s.recv(3)
                    if struct.unpack('>h', s.recv(2))[0] != -1:
                        s.recv(3)
                elif packet_id == 0x68:
                    s.recv(1)
                    count = struct.unpack('>h', s.recv(2))[0]
                    for slot in range(count):
                        item_id = struct.unpack('>h', s.recv(2))[0]
                        if item_id != -1:
                            s.recv(3)
                elif packet_id == 0x82:
                    s.recv(10)
                    for i in range(4):
                        length = struct.unpack('>h', s.recv(2))[0]
                        s.recv(length)
                elif packet_id == 0x83:
                    s.recv(4)
                    s.recv(struct.unpack('>B', s.recv(1))[0])
                elif packet_id == 0xff:
                    print("kick")
                    length = struct.unpack('>h', s.recv(2))[0]
                    print(s.recv(length * 2).decode('utf-16-be'))
                    return
                elif packet_id in packet_lengths:
                    s.recv(packet_lengths[packet_id])
            
m()
