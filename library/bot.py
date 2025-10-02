import socket
import struct
import time
import select
from datetime import datetime, timezone
from prompt_toolkit import ANSI, PromptSession, print_formatted_text
import socks

session = PromptSession()

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

def send_packet(s, id, data):
    s.sendall(struct.pack(f'>b', id) + data)

# Color translation
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

def handle_handshake(s, username):
    unknown = decode_string16(s)
    if unknown == "-":
        send_packet(s, 1, struct.pack('>i', 14) + 
                    encode_string16(username) + 
                    struct.pack('>qb', 0, 0))

def handle_chat(s, bot_prefix, enable_bot, bot_commands, enable_logs):
    message = decode_string16(s)

    if enable_logs:
        with open("log.txt", "a") as file:
            file.write(datetime.now(timezone.utc).strftime("%d/%m/%y %H:%M:%S ") + message + "\n")

    print_formatted_text(ANSI(translate_colors(message)))

    # To save compute power
    if bot_commands == {}: return

    if bot_prefix in message and message.startswith("<") and enable_bot: # bot command parse
        i = 0
        sender = ""
        for char in message:
            sender += char
            if char == ">":
                break
            i += 1
        if i < 18:
            remove_name = message[(i + 4):]
            if not message[i + 2:].startswith(bot_prefix):
                return
            args = remove_name.split()

            if len(args) == 0:
                help(s)
                return

            command = args[0]
            args.pop(0)

            if command in bot_commands:
                bot_commands[command](s, args, sender)
            else:
                help(s)


def handle_kick(s, queue):
    print("kick")
    print(decode_string16(s))
    queue.clear()
    #raise Exception

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
    4: 8,
    5: 10,
    6: 12,
    7: 9,
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

def handle_packet(s, packet_id, username, bot_prefix, enable_bot, bot_commands, enable_logs, queue):
    if packet_id == 0:
        return
    if packet_id in packet_funcs: # handle important functions
        # Send more data to functions to be able to have multiple "bots"

        if packet_id == 2 : packet_funcs[packet_id](s, username) # handle handshake
        elif packet_id == 3: packet_funcs[packet_id](s, bot_prefix, enable_bot, bot_commands, enable_logs) # handle chat
        else: packet_funcs[packet_id](s, queue) # handle kick
        return

    match packet_id: # unimportant variable length packets
        case 0x01:
            s.recv(4)
            decode_string16(s)
            s.recv(9)
        case 0x08:
            health = parse_short(s)
            if health <= 0:
                send_packet(s, 9, b'1')
        case 0x0f:
            if parse_short(s) >= 0:
                s.recv(3)
        case 0x14:
            s.recv(4)
            decode_string16(s)
            s.recv(16)
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
            length = parse_short(s)
            s.recv(length)
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
            else:
                print("bad packet id: " + str(packet_id))
                #raise Exception

# Impotable Claas           
class Bot():
    def __init__(self, username, ip, botCommands = {}, port = 25565, bot_prefix = "y!", enable_bot = True, enable_logs = True, disconectMessage = "Disconcted, trying again", auto_login = False, auto_login_command = "", proxy = "", proxy_port = ""):
        # Bot variables
        self.username = username
        self.ip = ip
        self.port = port
        self.botCommands = botCommands
        self.queue = []
        self.time_message = time.time()
        self.bot_prefix = bot_prefix
        self.enable_bot = enable_bot
        self.enable_logs = enable_logs
        self.disconectMessage = disconectMessage
        self.initialised = False
        self.auto_login = auto_login
        self.auto_login_command = auto_login_command
        self.s = None
        self.proxy = proxy
        self.proxy_port = proxy_port

        self.init()

    def setCommands(self, commands):
        self.botCommands = commands
        
    def send_message(self, message):
        self.queue.append(message)

    def handle_tick(self, s):
        if not self.s:
            return  # no active connection
        send_packet(s, 0, b'') # keep alive packet

        if time.time() > self.time_message and len(self.queue) > 0:
            send_packet(s, 3, encode_string16(self.queue[0]))
            self.queue.pop(0)
            self.time_message = time.time() + 1.3

    def init(self):
        try:
            self.start_time = time.time()
            self.prev_time = time.time()
            self.has_logged_in = False

            # Create a SOCKS socket if proxy is set
            if self.proxy !="" and self.proxy_port !="":
                self.s = socks.socksocket()  # wrap a socket
                self.s.set_proxy(socks.SOCKS5, self.proxy, int(self.proxy_port))
            else:
                self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

            # Connect to server
            self.s.connect((self.ip, self.port))
            print("Connected to server. Sending login...")
            send_packet(self.s, 2, encode_string16(self.username))  # handshake
            self.initialised = True

        except Exception as e:
            print(self.disconectMessage)
            print("Error:", e)  # Optional: show the real exception
            time.sleep(2)
            self.queue.clear()
            self.initialised = False

    # Main Loops | Needs to be called each tick (e.x While True loop)
    def onTick(self):
        if not self.initialised: self.init()
        try:
            if self.auto_login and time.time() - self.start_time > 1 and not self.has_logged_in:
                self.send_message(self.auto_login_command)
                self.has_logged_in = True

            if time.time() - self.prev_time > 0.05: # main tick loop
                self.handle_tick(self.s)
                self.prev_time = time.time()

            if select.select([self.s], [], [], 0)[0]: # packet handling
                data = self.s.recv(1)
                if data == b'':
                    return
                
                packet_id = struct.unpack('>B', data)[0]
                
                # Pass aditional bot data to handle packet
                handle_packet(self.s, packet_id, self.username, self.bot_prefix, self.enable_bot, self.botCommands, self.enable_logs, self.queue)
        except Exception:
            print(self.disconectMessage)
            time.sleep(2)
            self.initialised = False