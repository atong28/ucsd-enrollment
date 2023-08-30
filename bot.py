import discord
from discord import app_commands
from main import config_load, readcsv, get_info, plot_enrollment
import os

intents = discord.Intents.default()
client = discord.Client(intents=intents)
intents.message_content = True

tree = app_commands.CommandTree(client)

@tree.command(name = 'lookup', description = 'Look up general statistics about a list of classes.', guild=discord.Object(id=1146364521234055208))
async def lookup(interaction, classes: str, standing: int):
    courses = list(map(str.strip, classes.split(',')))

    msg = []
    imgs = []
    for c in courses:
        if not os.path.exists(f'../csv/{c}.csv'):
            await interaction.response.send_message("You entered an invalid class! Remember to separate classes with commas.")

    for course in courses:
        filepath = f'../csv/{course}.csv'
        data = readcsv(filepath)
        embed = get_info(data, standing, course)

        data_stream = plot_enrollment(data, course)
        data_stream.seek(0)
        chart = discord.File(data_stream, filename='plot.png')
        embed.set_image(
            url="attachment://plot.png"
        )
        # embed.set_thumbnail(url='https://a.espncdn.com/combiner/i?img=/i/teamlogos/ncaa/500/28.png')
        msg.append(embed)
        imgs.append(chart)
    await interaction.response.send_message(embeds=msg, files=imgs)
    
@client.event
async def on_ready():
    await tree.sync(guild=discord.Object(id=1146364521234055208))
    print("Ready!")

config = config_load()

client.run(config['token'])