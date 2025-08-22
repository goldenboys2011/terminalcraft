import socket
import struct
import time
import threading
from prompt_toolkit import PromptSession
from prompt_toolkit.patch_stdout import patch_stdout
from prompt_toolkit.formatted_text import ANSI
from prompt_toolkit.shortcuts import print_formatted_text

session = PromptSession()

server = session.prompt("Server IP: ")
port = 25565
username = session.prompt("Username: ")
login_command = "/login"
has_logged_in = False

id_keepalive = 0
id_login = 1
id_handshake = 2
id_chat = 3

prev_time = time.time()

packet_ids = {
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


# Chatgpt cooked this color map
mc_color_map = {
    "§0": "\x1b[30m",
    "§1": "\x1b[34m",
    "§2": "\x1b[32m",
    "§3": "\x1b[36m",
    "§4": "\x1b[31m",
    "§5": "\x1b[35m",
    "§6": "\x1b[33m",
    "§7": "\x1b[37m",
    "§8": "\x1b[90m",
    "§9": "\x1b[94m",
    "§a": "\x1b[92m",
    "§b": "\x1b[96m",
    "§c": "\x1b[91m",
    "§d": "\x1b[95m",
    "§e": "\x1b[93m",
    "§f": "\x1b[97m",
    "§l": "\x1b[1m",
    "§n": "\x1b[4m",
    "§o": "\x1b[3m",
    "§m": "\x1b[9m",
    "§k": "",          
    "§r": "\x1b[0m",
}

def translate_colors(msg: str) -> str:
    for code, ansi in mc_color_map.items():
        msg = msg.replace(code, ansi)
    return msg + "\033[0m"

#print(translate_colors("§6Golden §e2 §f- §aWelcome to the server!"))

def send_packet(s, id, data):
    s.sendall(struct.pack(f'>b', id) + data)

def encode_string16(string):
    return struct.pack(f'>h{len(string) * 2}s', len(string), string.encode('utf-16-be'))

def handle_login(s, server, port, username):
    send_packet(s, id_handshake, encode_string16(username))

ggg = 5


def listen_for_input():
    global ggg
    with patch_stdout():
        while True:
            try:
                user_input = session.prompt("> ")
                if user_input.strip():
                    send_packet(ggg, id_chat, encode_string16(user_input))
            except EOFError:
                break

input_thread = threading.Thread(target=listen_for_input)
input_thread.daemon = True

st = False

def handle_packet(s, packet_id):
    # --- Special handlers first ---
    if packet_id == id_handshake:
        length = struct.unpack('>h', s.recv(2))[0]
        temp2 = s.recv(length * 2).decode('utf-16-be')
        print(temp2)
        if temp2 == "-":
            send_packet(
                s, id_login,
                struct.pack('>i', 14) +
                encode_string16(username) +
                struct.pack('>qb', 0, 0)
            )
        return

    if packet_id == id_chat:
        length = struct.unpack('>h', s.recv(2))[0]
        msg = s.recv(length * 2).decode('utf-16-be')
        print_formatted_text(ANSI(translate_colors(msg)))
        return

    if packet_id == 0xff:  # kick
        length = struct.unpack('>h', s.recv(2))[0]
        reason = s.recv(length * 2).decode('utf-16-be')
        print("kick:", reason)
        return "disconnect"

    # --- Fixed length packets from packet_ids dict ---
    if packet_id in packet_ids:
        s.recv(packet_ids[packet_id])
        return

    # --- Special variable-length ones (examples) ---
    if packet_id == 0x0f:
        s.recv(10)
        if struct.unpack('>h', s.recv(2))[0] >= 0:
            s.recv(3)
        return

    if packet_id == 0x14:
        s.recv(4)
        length = struct.unpack('>h', s.recv(2))[0]
        s.recv(length + 16)
        return

    if packet_id == 0x17:
        s.recv(17)
        if struct.unpack('>i', s.recv(4))[0] > 0:
            s.recv(6)
        return

    if packet_id == 0x18:
        s.recv(19)
        val = s.recv(1)
        while val != b'\x7f':
            val = s.recv(1)
        return

    if packet_id == 0x28:
        s.recv(4)
        val = s.recv(1)
        while val != b'\x7f':
            val = s.recv(1)
        return

    if packet_id == 0x33:
        s.recv(13)
        s.recv(struct.unpack('>i', s.recv(4))[0])
        return

    if packet_id == 0x34:
        s.recv(8)
        length = struct.unpack('>h', s.recv(2))[0]
        s.recv(4 * length)
        return

    if packet_id == 0x3c:
        s.recv(28)
        s.recv(struct.unpack('>i', s.recv(4))[0] * 3)
        return

    if packet_id == 0x64:
        s.recv(2)
        length = struct.unpack('>h', s.recv(2))[0]
        s.recv(length)
        s.recv(1)
        return

    if packet_id == 0x67:
        s.recv(3)
        if struct.unpack('>h', s.recv(2))[0] != -1:
            s.recv(3)
        return

    if packet_id == 0x68:
        s.recv(1)
        count = struct.unpack('>h', s.recv(2))[0]
        for _ in range(count):
            item_id = struct.unpack('>h', s.recv(2))[0]
            if item_id != -1:
                s.recv(3)
        return

    if packet_id == 0x82:
        s.recv(10)
        for _ in range(4):  # four strings
            length = struct.unpack('>h', s.recv(2))[0]
            s.recv(length)
        return

    if packet_id == 0x83:
        s.recv(4)
        s.recv(struct.unpack('>B', s.recv(1))[0])
        return

    # --- Fallback ---
    # print(f"Unknown packet id: {hex(packet_id)}")


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
                    m()
                    return

        while True:
            try:
                data = s.recv(1)
                if not data:
                    continue
                packet_id = struct.unpack('>B', data)[0]
                result = handle_packet(s, packet_id)
                if result == "disconnect":
                    return
            except socket.timeout:
                return

m()
