import discord
from discord.ext import pages
from functions import *
import paginator
import modal
import os
from datetime import datetime

bot = discord.Bot()

@bot.slash_command(name = 'verbose', 
                   description = 'Look up statistics about a class. Usage: /lookup classes:ECE 35, CSE 11, BILD 4', 
                   guild_ids=GUILD_IDS)

async def verbose(interaction, classes: str):
    courses = list(map(str.strip, classes.split(',')))

    # results is a list of Pages
    results = []
    unreadable = []
    for c in courses:
        # check if course is readable
        course = c.replace(" ", "").upper()
        # reformat to add the space back
        for i in range(2, 5):
            if course[:i].isalpha() and course[i].isdigit():
                course = course[:i] + ' ' + course[i:]
                break
        if not os.path.exists(f'../csv/{course}.csv'):
            unreadable.append(c)
            continue
    
        # read course data
        filepath = f'../csv/{course}.csv'
        data = readcsv(filepath)

        result = get_info(data, course, 1)

        embed = result

        data_stream = plot_enrollment(data, course)
        data_stream.seek(0)
        chart = discord.File(data_stream, filename='plot.png')
        embed.set_image(
            url="attachment://plot.png"
        )
        results.append(pages.Page(embeds=[embed], files=[chart]))

    if len(results) == 0:
        em = discord.Embed(title='No results found!', description='Please check your spelling(s) and make sure the classes are properly comma-separated.\nUsage: ')
        em.add_field(name='Usage', value='`/lookup classes:ECE 35, CSE 11, BILD 4`')
        em.add_field(name='Your Query', value=f'`{classes}`')
        await interaction.respond(embed=em)
    else:
        msg = paginator.MultiPage(bot)
        msg.set_pages(results)
        await msg.paginate(interaction)

@bot.slash_command(name = 'query', 
                   description = 'Provide a list of classes and see enrollment recommendations.', 
                   guild_ids=GUILD_IDS)

async def query(interaction):
    await interaction.response.send_modal(modal.OverviewInputModal(bot, title='Input Details'))



