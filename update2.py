import sys
import socket
import struct
import time
import select

# MODIFY THESE CONSTANTS FOR USAGE

server = "2beta2t.net"
port = 25565
username = "YawningCheese01"

# refer to https://minecraft.wiki/w/Minecraft_Wiki:Projects/wiki.vg_merge/Protocol?oldid=2769758 
# for protocol and packet info

def send_packet(s, id, data):
    s.sendall(struct.pack(f'>b', id) + data)

def parse(s, format):
    return struct.unpack('>' + format, s.recv(struct.calcsize('>' + format)))

def parse_unsigned_byte(s): return parse(s, 'B')[0]
def parse_short(s): return parse(s, 'h')[0]
def parse_int(s): return parse(s, 'i')[0]

def encode_string16(string):
    return struct.pack(f'>h{len(string) * 2}s', len(string), string.encode('utf-16-be'))

def decode_string16(s):
    length = parse_short(s)
    return s.recv(length * 2).decode('utf-16-be')

def send_message(s, message):
    send_packet(s, 3, encode_string16(message))

# important packet functions, see packet_funcs for how to register

def handle_handshake(s):
    unknown = decode_string16(s)
    if unknown == "-":
        send_packet(s, 1, struct.pack('>i', 14) + 
                    encode_string16(username) + 
                    struct.pack('>qb', 0, 0))

def handle_chat(s):
    print(decode_string16(s))

def handle_kick(s):
    print("kick")
    print(decode_string16(s))

# map for important packets
# the key is the packet id, and the value is the function to call
# when adding a new function, 
# remove it from the unimportant variable lengths section or 
# the fixed_packet_lengths section if it is there

packet_funcs = {
    2: handle_handshake,
    3: handle_chat,
    0xff: handle_kick
}

# for unimportant fixed length packets
# unimportant variable length packets are handled later

fixed_packet_lengths = {
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

def handle_tick(s):
    send_packet(s, 0, b'') # keep alive packet

def handle_input(s):
    send_message(s, sys.stdin.readline())

def handle_packet(s, packet_id):
    if packet_id in packet_funcs: # handle important functions
        packet_funcs[packet_id](s)
        return

    match packet_id: # unimportant variable length packets
        case 0x0f:
            if parse_short(s) >= 0:
                s.recv(3)
        case 0x14:
            s.recv(4)
            length = parse_short(s)
            s.recv(length + 16)
        case 0x17:
            s.recv(17)
            if parse_int(s) > 0:
                s.recv(6)
        case 0x18:
            s.recv(19)
            val = s.recv(1)
            while val != b'\x7f':
                val = s.recv(1)
        case 0x19:
            s.recv(4)
            s.recv(parse_short(s) + 16)
        case 0x28:
            s.recv(4)
            val = s.recv(1)
            while val != b'\x7f':
                val = s.recv(1)
        case 0x33:
            s.recv(13)
            s.recv(parse_int(s))
        case 0x34:
            s.recv(8)
            length = parse_short(s)
            s.recv(4 * length)
        case 0x3c:
            s.recv(28)
            s.recv(parse_int(s) * 3)
        case 0x64:
            s.recv(2)
            decode_string16(s)
            s.recv(1)
        case 0x67:
            s.recv(3)
            if parse_short(s) != -1:
                s.recv(3)
        case 0x68:
            s.recv(1)
            count = parse_short(s)
            for slot in range(count):
                item_id = parse_short(s)
                if item_id != -1:
                    s.recv(3)
        case 0x82:
            s.recv(10)
            for i in range(4):
                decode_string16(s)
        case 0x83:
            s.recv(4)
            s.recv(parse_unsigned_byte(s))
        case _: # unimportant packets with fixed lengths
            if packet_id in fixed_packet_lengths:
                s.recv(fixed_packet_lengths[packet_id])

def m():
    prev_time = time.time()

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((server, port))
        print("Connected to server. Sending login...")
        send_packet(s, 2, encode_string16(username)) # send handshake

        while True:
            if time.time() - prev_time > 0.05: # main tick loop
                handle_tick(s)
                prev_time = time.time()

            if select.select([sys.stdin], [], [], 0)[0]: # user input handling
                handle_input(s)

            if select.select([s], [], [], 0)[0]: # packet handling
                data = s.recv(1)
                if data == b'':
                    continue
                
                packet_id = struct.unpack('>B', data)[0]

                handle_packet(s, packet_id)
            
m()
