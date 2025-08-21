import asyncio
import struct

SERVER = input("server ip:")
PORT = 25565
try:
    PORT = int(input("server port: (press enter for 25565):"))
except ValueError as e:
    pass
USERNAME = input("username:")

LOGIN_COMMAND = "/login"
KEEPALIVE_INTERVAL = 0.5

ID_KEEPALIVE = 0
ID_LOGIN = 1
ID_HANDSHAKE = 2
ID_CHAT = 3

has_logged_in = False

def encode_string16(string):
    return struct.pack(f'>h{len(string) * 2}s', len(string), string.encode('utf-16-be'))

async def read_packet(reader):
    try:
        packet_id_data = await reader.readexactly(1)
        packet_id = struct.unpack('>B', packet_id_data)[0]
        return packet_id
    except asyncio.IncompleteReadError:
        return None
    except ConnectionResetError:
        print("Connection reset by server.")
        return None

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

async def handle_handshake(reader, writer):
    length_data = await reader.readexactly(2)
    length = struct.unpack('>h', length_data)[0]
    temp2 = (await reader.readexactly(length * 2)).decode('utf-16-be')
    if temp2 == "-":
        send_packet(writer, ID_LOGIN, struct.pack('>i', 14) + encode_string16(USERNAME) + struct.pack('>qb', 0, 0))

async def handle_chat(reader, writer):
    length_data = await reader.readexactly(2)
    length = struct.unpack('>h', length_data)[0]
    print((await reader.readexactly(length * 2)).decode('utf-16-be'))

packet_funcs = {
    ID_HANDSHAKE: handle_handshake,
    ID_CHAT: handle_chat
}

async def handle_packet(packet_id, reader, writer):
    global has_logged_in
    if packet_id is None:
        return
    
    if packet_id in packet_funcs:
        await packet_funcs[packet_id](reader, writer)

    elif packet_id == 0x0f:
        await reader.readexactly(10)
        if struct.unpack('>h', await reader.readexactly(2))[0] >= 0:
            await reader.readexactly(3)
    elif packet_id == 0x14:
        await reader.readexactly(4)
        length = struct.unpack('>h', await reader.readexactly(2))[0]
        await reader.readexactly(length + 16)
    elif packet_id == 0x17:
        await reader.readexactly(17)
        if struct.unpack('>i', await reader.readexactly(4))[0] > 0:
            await reader.readexactly(6)
    elif packet_id == 0x18:
        await reader.readexactly(19)
        val = await reader.read(1)
        while val != b'\x7f':
            val = await reader.read(1)
    elif packet_id == 0x19:
        await reader.readexactly(4)
        length_data = await reader.readexactly(2)
        length = struct.unpack('>h', length_data)[0]
        await reader.readexactly(length + 16)
    elif packet_id == 0x28:
        await reader.readexactly(4)
        val = await reader.read(1)
        while val != b'\x7f':
            val = await reader.read(1)
    elif packet_id == 0x33:
        await reader.readexactly(13)
        length_data = await reader.readexactly(4)
        length = struct.unpack('>i', length_data)[0]
        await reader.readexactly(length)
    elif packet_id == 0x34:
        await reader.readexactly(8)
        length = struct.unpack('>h', await reader.readexactly(2))[0]
        await reader.readexactly(4 * length)
    elif packet_id == 0x3c:
        await reader.readexactly(28)
        length = struct.unpack('>i', await reader.readexactly(4))[0]
        await reader.readexactly(length * 3)
    elif packet_id == 0x64:
        await reader.readexactly(2)
        length = struct.unpack('>h', await reader.readexactly(2))[0]
        await reader.readexactly(length)
        await reader.readexactly(1)
    elif packet_id == 0x67:
        await reader.readexactly(3)
        if struct.unpack('>h', await reader.readexactly(2))[0] != -1:
            await reader.readexactly(3)
    elif packet_id == 0x68:
        await reader.readexactly(1)
        count = struct.unpack('>h', await reader.readexactly(2))[0]

        for _ in range(count):
            item_id = struct.unpack('>h', await reader.readexactly(2))[0]
            if item_id != -1:
                await reader.readexactly(3)
    elif packet_id == 0x82:
        await reader.readexactly(10)
        length = struct.unpack('>h', await reader.readexactly(2))[0]
        await reader.readexactly(length)
        length = struct.unpack('>h', await reader.readexactly(2))[0]
        await reader.readexactly(length)
        length = struct.unpack('>h', await reader.readexactly(2))[0]
        await reader.readexactly(length)
        length = struct.unpack('>h', await reader.readexactly(2))[0]
        await reader.readexactly(length)
    elif packet_id == 0x83:
        await reader.readexactly(4)
        length = struct.unpack('>B', await reader.readexactly(1))[0]
        await reader.readexactly(length)
    elif packet_id == 0xff:
        print("kick")
        length = struct.unpack('>h', await reader.readexactly(2))[0]
        print((await reader.readexactly(length * 2)).decode('utf-16-be'))
        writer.close()
        await writer.wait_closed()
    elif packet_id in packet_ids:
        await reader.readexactly(packet_ids[packet_id])

def send_packet(writer, packet_id, data):
    writer.write(struct.pack('>b', packet_id) + data)
    
async def handle_input(writer):
    while True:
        try:
            message = await asyncio.to_thread(input)
            send_packet(writer, ID_CHAT, encode_string16(message))
        except (EOFError, KeyboardInterrupt):
            print("Exiting input handler.")
            writer.close()
            return
            
async def handle_keepalive(writer):
    global has_logged_in
    while True:
        if not has_logged_in:
            send_packet(writer, ID_HANDSHAKE, encode_string16(USERNAME))
            has_logged_in = True
        send_packet(writer, ID_KEEPALIVE, b'')
        await asyncio.sleep(KEEPALIVE_INTERVAL)

async def main():
    print(f"Connecting to {SERVER}:{PORT}...")
    try:
        reader, writer = await asyncio.open_connection(SERVER, PORT)
    except Exception as e:
        print(f"Connection failed: {e}. Exiting.")
        return

    print("Connected to server. Initiating tasks...")
    
    tasks = [
        asyncio.create_task(handle_input(writer)),
        asyncio.create_task(handle_keepalive(writer)),
    ]

    while True:
        packet_id = await read_packet(reader)
        if packet_id is None:
            break
        await handle_packet(packet_id, reader, writer)
    
    print("Connection closed. Shutting down...")
    for task in tasks:
        task.cancel()
    await asyncio.gather(*tasks, return_exceptions=True)
    writer.close()
    await writer.wait_closed()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Client shut down by user.")
