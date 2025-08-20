import sys
import socket
import struct
import time
import threading

server = "2beta2t.net"
port = 25565
username = "YawningCheese01"
login_command = "/login"
has_logged_in = False

id_keepalive = 0
id_login = 1
id_handshake = 2
id_chat = 3

prev_time = time.time()

def send_packet(s, id, data):
    s.sendall(struct.pack(f'>b', id) + data)

def encode_string16(string):
    return struct.pack(f'>h{len(string) * 2}s', len(string), string.encode('utf-16-be'))

def handle_login(s, server, port, username):
    send_packet(s, id_handshake, encode_string16(username))

ggg = 5

def listen_for_input():
    send_packet(ggg, id_chat, encode_string16(input()))
    listen_for_input()

input_thread = threading.Thread(target=listen_for_input)
input_thread.daemon = True

st = False

def m():
    global prev_time
    global has_logged_in
    global ggg
    global input_thread
    global st

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        ggg = s
        if not st:
            st = True
            input_thread.start()

        s.settimeout(10.0)
        try:
            s.connect((server, port))
            print("Connected to server. Sending login...")
            handle_login(s, server, port, username)
        except:
            print("Connection failed. Trying again...")
            while True:
                if time.time() - prev_time > 1:
                    prev_time = time.time()
                    #m()
                    return

        while True:
            if time.time() - prev_time > 0.5:
                if not has_logged_in:
                    #send_packet(s, id_chat, encode_string16(login_command))
                    has_logged_in = True
                send_packet(s, id_keepalive, b'')
                prev_time = time.time()

            try:
                data = s.recv(1)
                if data == b'':
                    #m()
                    #return
                    continue
                
                packet_id = struct.unpack('>B', data)[0]


                if packet_id == 0:
                    pass
                if packet_id == 1:
                    s.recv(15)
                if packet_id == id_handshake:
                    length = struct.unpack('>h', s.recv(2))[0]
                    temp2 = s.recv(length * 2).decode('utf-16-be')
                    print(temp2)
                    if temp2 == "-":
                        send_packet(s, id_login, struct.pack('>i', 14) + encode_string16(username) + struct.pack('>qb', 0, 0))
                if packet_id == id_chat:
                    length = struct.unpack('>h', s.recv(2))[0]
                    print(s.recv(length * 2).decode('utf-16-be'))
                if packet_id == 4:
                    s.recv(8)
                if packet_id == 5:
                    s.recv(10)
                if packet_id == 6:
                    s.recv(12)
                if packet_id == 7:
                    s.recv(9)
                if packet_id == 8:
                    s.recv(2)
                if packet_id == 9:
                    s.recv(1)
                if packet_id == 0x0d:
                    s.recv(41)
                if packet_id == 0x0e:
                    s.recv(11)
                if packet_id == 0x0f:
                    s.recv(10)
                    if struct.unpack('>h', s.recv(2))[0] >= 0:
                        s.recv(3)
                if packet_id == 0x10:
                    s.recv(2)
                if packet_id == 0x11:
                    s.recv(14)
                if packet_id == 0x12:
                    s.recv(5)
                if packet_id == 0x13:
                    s.recv(5)
                if packet_id == 0x14:
                    s.recv(4)
                    length = struct.unpack('>h', s.recv(2))[0]
                    s.recv(length + 16)
                if packet_id == 0x15:
                    s.recv(24)
                if packet_id == 0x16:
                    s.recv(8)
                if packet_id == 0x17:
                    s.recv(17)
                    if struct.unpack('>i', s.recv(4))[0] > 0:
                        s.recv(6)
                if packet_id == 0x18:
                    s.recv(19)
                    val = s.recv(1)
                    while val != b'\x7f':
                        val = s.recv(1)
                if packet_id == 0x19:
                    s.recv(4)
                    s.recv(struct.unpack('>h', s.recv(2))[0] + 16)
                if packet_id == 0x1b:
                    s.recv(18)
                if packet_id == 0x1c:
                    s.recv(10)
                if packet_id == 0x1d:
                    s.recv(4)
                if packet_id == 0x1e:
                    s.recv(4)
                if packet_id == 0x1f:
                    s.recv(7)
                if packet_id == 0x20:
                    s.recv(6)
                if packet_id == 0x21:
                    s.recv(9)
                if packet_id == 0x22:
                    s.recv(18)
                if packet_id == 0x26:
                    s.recv(5)
                if packet_id == 0x27:
                    s.recv(8)
                if packet_id == 0x28:
                    s.recv(4)
                    val = s.recv(1)
                    while val != b'\x7f':
                        val = s.recv(1)
                if packet_id == 0x32:
                    s.recv(9)
                if packet_id == 0x33:
                    s.recv(13)
                    s.recv(struct.unpack('>i', s.recv(4))[0])
                if packet_id == 0x34:
                    s.recv(8)
                    length = struct.unpack('>h', s.recv(2))[0]
                    s.recv(4 * length)
                if packet_id == 0x35:
                    s.recv(11)
                if packet_id == 0x36:
                    s.recv(12)
                if packet_id == 0x3c:
                    s.recv(28)
                    s.recv(struct.unpack('>i', s.recv(4))[0] * 3)
                if packet_id == 0x3d:
                    s.recv(17)
                if packet_id == 0x46:
                    s.recv(1)
                if packet_id == 0x47:
                    s.recv(17)
                if packet_id == 0x64:
                    s.recv(2)
                    length = struct.unpack('>h', s.recv(2))[0]
                    s.recv(length)
                    s.recv(1)
                if packet_id == 0x65:
                    s.recv(1)
                if packet_id == 0x67:
                    s.recv(3)
                    if struct.unpack('>h', s.recv(2))[0] != -1:
                        s.recv(3)
                if packet_id == 0x68:
                    s.recv(1)
                    count = struct.unpack('>h', s.recv(2))[0]
 
                    for slot in range(count):
                        item_id = struct.unpack('>h', s.recv(2))[0]
                        if item_id != -1:
                            s.recv(3)

                if packet_id == 0x69:
                    s.recv(5)
                if packet_id == 0x6a:
                    s.recv(4)
                if packet_id == 0x82:
                    s.recv(10)
                    length = struct.unpack('>h', s.recv(2))[0]
                    s.recv(length)
                    length = struct.unpack('>h', s.recv(2))[0]
                    s.recv(length)
                    length = struct.unpack('>h', s.recv(2))[0]
                    s.recv(length)
                    length = struct.unpack('>h', s.recv(2))[0]
                    s.recv(length)
                if packet_id == 0x83:
                    s.recv(4)
                    s.recv(struct.unpack('>B', s.recv(1))[0])
                if packet_id == 0xc8:
                    s.recv(5)
                if packet_id == 0xff:
                    print("kick")
                    length = struct.unpack('>h', s.recv(2))[0]
                    print(s.recv(length * 2).decode('utf-16-be'))

                    #m()
                    return

            except socket.timeout:
                #m()
                return

m()
