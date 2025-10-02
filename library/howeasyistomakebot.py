import bot

MrTracker = bot.Bot("MrTracker", "2beta2t.net", auto_login=True, auto_login_command="/login -----", bot_prefix="t!")

def help(s, args, sender):
    MrTracker.send_message("> Hello " + sender + "!")
    MrTracker.send_message("> ---------------------")
    MrTracker.send_message("> Commands: ")

commands = {
    "help", help
}

MrTracker.setCommands(commands)

while True:
    MrTracker.onTick()
