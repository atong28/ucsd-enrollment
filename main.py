from functions import config_load
from commands import *

@bot.event
async def on_ready():
    print("Ready!")

config = config_load()
bot.run(config['token'])