# This example requires the 'message_content' intent.

import discord
from discord import app_commands
import main

intents = discord.Intents.default()
client = discord.Client(intents=intents)
intents.message_content = True

tree = app_commands.CommandTree(client)

@tree.command(name = 'lookup', description = 'Look up general statistics about a list of classes.')
async def lookup(interaction):
    await interaction.response.send_message("Hello!")

    courses = ['CSE 11', 'MATH 20C']

    for course in courses:
        filepath = f'../csv/{course}.csv'
        data = main.readcsv(filepath)

@client.event
async def on_ready():
    await tree.sync(guild=discord.Object(id=1146364521234055208))
    print("Ready!")

client.run(main.config_load())