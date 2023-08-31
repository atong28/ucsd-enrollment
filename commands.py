import discord
from discord.ext import pages
from functions import *
import paginator
import os
from datetime import datetime

bot = discord.Bot()

@bot.slash_command(name = 'faq',
                   description = 'See the FAQ!',
                   guild_ids = GUILD_IDS)

async def faq(interaction):
    # import dict
    answers = import_faq()

    # create a table of contents
    contents = discord.Embed(title=f'FAQ', description='Use /help to read more about a specific question!')
    overflow = False

    for answer in answers:
        em = discord.Embed(title=answer['embed_data']['title'], 
                            description=answer['embed_data']['description'])
        em.set_footer(answer['embed_data']['footer'])
        em.set_author(answer['embed_data']['author'])
        filter.append(pages.Page(embeds=[em]))
        # show results
        if len(contents.fields) < MAX_SEARCH_RESULTS:
            contents.add_field(name=f'{len(filter)}. {answer["embed_data"]["title"]}', 
                                value=f'Keywords: {", ".join(answer["keywords"])}')
        elif len(contents.fields) == MAX_SEARCH_RESULTS:
            overflow = True

    # add overflow entry
    if overflow:
        contents.add_field(value=f'and {len(filter)-MAX_SEARCH_RESULTS} more...')

    # if filter is empty, return not found error
    if not filter:
        reply = discord.Embed(title='No results found',
                              description='Our FAQ is empty :(')
        await interaction.respond(embed=reply)
        return

    # if results came up, return paginator of answers
    contents.set_footer(f'{len(filter)} results')
    filter.insert(0, contents)
    msg = paginator.MultiPage(bot)
    msg.set_pages(filter)
    await msg.paginate(interaction)


@bot.slash_command(name = 'add_faq',
                   description = 'Add an FAQ to the database.',
                   guild_ids = GUILD_IDS)

async def add_faq(interaction, title: str):
    embed = {

    }

@bot.slash_command(name = 'help', 
                   description = 'Have a question? Search through an FAQ!',
                   guild_ids = GUILD_IDS)

async def help(interaction, query: str, id: int, strict=False):
    # import dict
    answers = import_faq()

    # if querying specific id, return that question
    if id:
        em = discord.Embed(title=answers[id - 1]['embed_data']['title'], 
                           description=answers[id - 1]['embed_data']['description'])
        em.set_footer(answers[id - 1]['embed_data']['footer'])
        em.set_author(answers[id - 1]['embed_data']['author'])
        await interaction.respond(embed=em)
        return
    
    # if no query, then return the faq
    if not query:
        await faq(interaction)
        return

    # split into only keywords
    keywords = query.lower().split('')

    filter = []

    # create a table of contents
    contents = discord.Embed(title=f'Search Results for {query}')
    overflow = False

    # filter out
    if strict:
        for answer in answers:
            if all(keyword in answer['keywords'] for keyword in keywords):
                em = discord.Embed(title=answer['embed_data']['title'], 
                                   description=answer['embed_data']['description'])
                em.set_footer(answer['embed_data']['footer'])
                em.set_author(answer['embed_data']['author'])
                filter.append(pages.Page(embeds=[em]))
                # show results
                if len(contents.fields) < MAX_SEARCH_RESULTS:
                    contents.add_field(name=f'{len(filter)}. {answer["embed_data"]["title"]}', 
                                       value=f'Keywords: {", ".join(answer["keywords"])}')
                elif len(contents.fields) == MAX_SEARCH_RESULTS:
                    overflow = True
    else:
        for answer in answers:
            if any(keyword in answer['keywords'] for keyword in keywords):
                em = discord.Embed(title=answer['embed_data']['title'], 
                                   description=answer['embed_data']['description'])
                em.set_footer(answer['embed_data']['footer'])
                em.set_author(answer['embed_data']['author'])
                filter.append(pages.Page(embeds=[em]))
                # show results
                if len(contents.fields) < MAX_SEARCH_RESULTS:
                    contents.add_field(name=f'{len(filter)}. {answer["embed_data"]["title"]}', 
                                       value=f'Keywords: {", ".join(answer["keywords"])}')
                elif len(contents.fields) == MAX_SEARCH_RESULTS:
                    overflow = True
    
    # add overflow entry
    if overflow:
        contents.add_field(value=f'and {len(filter)-MAX_SEARCH_RESULTS} more...')

    # if filter is empty, return not found error
    if not filter:
        reply = discord.Embed(title='No results found',
                              description='Try changing the keywords or your search type.')
        await interaction.respond(embed=reply)
        return

    # if results came up, return paginator of answers
    contents.set_footer(f'{len(filter)} results')
    filter.insert(0, contents)
    msg = paginator.MultiPage(bot)
    msg.set_pages(filter)
    await msg.paginate(interaction)

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


@bot.slash_command(name = 'overview', 
                   description = 'Provide a list of classes and see enrollment recommendations.', 
                   guild_ids=GUILD_IDS)
async def overview(interaction, classes: str, first_pass_time: str, second_pass_time: str):
    courses = list(map(str.strip, classes.split(',')))

    enrollment_times = (int(first_pass_time), int(second_pass_time))

    # enrollment_times: Tuple[int], contains the first and second pass times in seconds since epoch
    # enrollment_times = (parse_times(first_pass_time), parse_times(second_pass_time))

    # main_em: pages.Page, the first main page to be displayed
    main_em = discord.Embed(title='Overview', description=f'Your first pass time: {datetime.fromtimestamp(enrollment_times[0])}\nYour second pass time: {datetime.fromtimestamp(enrollment_times[1])}')

    # results: List[pages.Page], to be displayed in the paginator
    results = [pages.Page(embeds=[main_em])]

    # unreadable: List[str], for all invalid courses
    unreadable = []

    # List[str], course lists for each type
    fp_only = []
    sp_only = []
    anytime = []
    waitlist = []
    drop = []

    for c in courses:
        # check if course is readable; first collapse all spaces and go to uppercase
        course = c.replace(' ', '').upper()

        # reformat to add the space back
        for i in range(2, 5):
            if course[:i].isalpha() and course[i].isdigit():
                course = course[:i] + ' ' + course[i:]
                break
        
        # if unreadable, skip
        if not os.path.exists(f'../csv/{course}.csv'):
            unreadable.append(c)
            continue
    
        # read course data
        filepath = f'../csv/{course}.csv'
        data = readcsv(filepath)

        # get overview of data and store in result
        result = get_overview(data, course, enrollment_times)

        # summary: List[str], stores results to be used in embed's course summary
        summary = None

        match result['rec']:
            case 0:
                summary = ['No', 'No', 'No']
                if result['wl_rec'] == 0:
                    waitlist.append(course)
                else:
                    drop.append(course)
            case 1:
                summary = ['Yes', 'No', 'No']
                fp_only.append(course)
            case 2:
                summary = ['Yes', 'Yes', 'No']
                sp_only.append(course)
            case 3:
                summary = ['Yes', 'Yes', 'Yes']
                anytime.append(course)

        match result['wl_rec']:
            case 0:
                summary.append('Likely')
            case 1:
                summary.append('Possible')
            case 2:
                summary.append('Unlikely')
            case 3:
                summary.append('N/A')

        main_em.add_field(name=course, value=f'First Pass: {summary[0]}\nSecond Pass: {summary[1]}\nClasses Start: {summary[2]}\nOff Waitlist: {summary[3]}', inline=True)
        embed = result['embed']

        # plot the enrollment and store it into the embed
        data_stream = plot_enrollment(data, course)
        data_stream.seek(0)
        chart = discord.File(data_stream, filename=f'{course}.png')
        embed.set_image(
            url=f'attachment://{course}.png'
        )
        results.append(pages.Page(embeds=[embed], files=[chart]))

    # if none of the classes were readable, output error message
    if len(results) == 0:
        em = discord.Embed(title='No results found!', description='Please check your spelling(s) and make sure the classes are properly comma-separated.')
        em.add_field(name='Usage', value='`/lookup classes:ECE 35, CSE 11, BILD 4`')
        em.add_field(name='Your Query', value=f'`{classes}`')
        await interaction.respond(embed=em)
    else:
        rec = []
        if fp_only:
            rec.append(f'You should enroll first pass the following courses:\n**{", ".join(fp_only)}**')
        if sp_only:
            rec.append(f'You should enroll second pass the following courses:\n**{", ".join(sp_only)}**')
        if waitlist:
            rec.append(f'You should waitlist the following courses:\n**{", ".join(waitlist)}**')
        if anytime:
            rec.append(f'You can always enroll in the following courses:\n**{", ".join(anytime)}**')
        if drop:
            rec.append(f'Do not expect to get the following courses):\n**{", ".join(drop)}**')
        main_em.add_field(name='Recommendations', value='\n\n'.join(rec), inline=False)
        if unreadable:
            main_em.add_field(name='Invalid Classes', value=f'**{", ".join(unreadable)}**', inline=False)
        msg = paginator.MultiPage(bot)
        msg.set_pages(results)
        await msg.paginate(interaction)

