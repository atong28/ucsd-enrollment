import csv
from datetime import datetime
import re
from matplotlib import pyplot as plt, patches
import os
import json
import io
import discord

EPOCH = datetime(1970,1,1)
VERBOSE = False
BUTTONS = [u"\u23EA", u"\u2B05", u"\u27A1", u"\u23E9"]

# Enrollment times for 2023 Winter
TIMES = [
    datetime(2022, 11, 7, 8),  # first pass prio + seniors [0]
    datetime(2022, 11, 9, 8),  # first pass juniors [1]
    datetime(2022, 11, 10, 8), # first pass sophomores [2]
    datetime(2022, 11, 11, 8), # first pass freshmen [3]
    datetime(2022, 11, 14, 8), # second pass prio + seniors [4]
    datetime(2022, 11, 16, 8), # second pass juniors [5]
    datetime(2022, 11, 17, 8), # second pass sophomores [6]
    datetime(2022, 11, 18, 8), # second pass freshmen [7]
    datetime(2022, 11, 20),    # enrollment ends [8]
    datetime(2023, 1, 4),      # classes start [9]
    datetime(2023, 1, 21)      # deadline to enroll/add [10]
]

# Enrollment times for 2024 Winter
TIMES_NEW = [
    datetime(2023, 11, 6, 8),  # first pass prio + seniors [0]
    datetime(2023, 11, 8, 8),  # first pass juniors [1]
    datetime(2023, 11, 9, 8),  # first pass sophomores [2]
    datetime(2023, 11, 10, 8), # first pass freshmen [3]
    datetime(2023, 11, 13, 8), # second pass prio + seniors [4]
    datetime(2023, 11, 15, 8), # second pass juniors [5]
    datetime(2023, 11, 16, 8), # second pass sophomores [6]
    datetime(2023, 11, 17, 8), # second pass freshmen [7]
    datetime(2023, 11, 19),    # enrollment ends [8]
    datetime(2024, 1, 3),      # classes start [9]
    datetime(2024, 1, 20)      # deadline to enroll/add [10]
]

# String representations of each corresponding enrollment itme
TIMES_TO_STR = [
    "First Pass: Seniors",
    "First Pass: Juniors",
    "First Pass: Sophomores",
    "First Pass: First-Years",
    "Second Pass: Seniors",
    "Second Pass: Juniors",
    "Second Pass: Sophomores",
    "Second Pass: First-Years",
    "Registation Closed",
    "Classes Begin",
    "Deadline to Enroll"
]

# Colors for the background rectangles alternating dark, light for each pass
COLORS = ['#82ffa1', '#bdffce', '#6bfffa', '#adfffc', '#d84aff', '#eba1ff', '#ffee52', '#fff59e']

# Get number of seconds since epoch with datetime
def get_seconds(dt: datetime) -> int:
    return (dt - EPOCH).total_seconds()

# Enrollment times in seconds
SECONDS = list(map(get_seconds, TIMES))
SECONDS_NEW = list(map(get_seconds, TIMES_NEW))

# Reads the csv file and returns data in the following format:
# [seconds, [enrolled, available, waitlisted, total]]
def readcsv(filepath):
    with open(filepath, newline='') as csvfile:
        reader = csv.reader(csvfile, delimiter=' ', quotechar='|')
        data = []
        # Skip formatting line
        next(reader)
        # Iterate through every datapoint and format into data
        for line in reader:
            tokenized = line[0].split(',')
            date = [int(num) for num in re.findall(r'\d+', tokenized[0])]
            seconds = get_seconds(datetime(*date))
            data.append({
                "seconds": seconds,
                "enrolled": int(tokenized[1]),
                "available": int(tokenized[2]),
                "waitlisted": int(tokenized[3]),
                "total": int(tokenized[4])
            })
        return data

def new_to_old(enrollment_time):
    return enrollment_time - (SECONDS_NEW[0] - SECONDS[0])

def old_to_new(enrollment_time):
    return enrollment_time + (SECONDS[0] - SECONDS_NEW[0])

def get_overview(data, course, enrollment_times):
    prev_data = data[0]
    full_capacity = False
    fptime, sptime = new_to_old(enrollment_times[0]), new_to_old(enrollment_times[1])

    capacity_time = -1
    
    # rec = 0: entirely unobtainable
    # rec = 1: should first pass
    # rec = 2: should second pass
    # rec = 3: can wait until classes start
    rec = 0
    # wl_rec = 0: likely
    # wl_rec = 1: possible
    # wl_rec = 2: unlikely
    wl_rec = 0

    embed = discord.Embed(title=f'Enrollment Statistics for {course}')

    for i in range(1, len(data)):
        prev_data = data[i - 1]
        curr_data = data[i]
        wl_msg = None
        # show recommendations
        if prev_data['seconds'] < fptime < curr_data['seconds']:
            embed.add_field(name='First Pass', value=f'Approximately {curr_data["enrolled"] * 100 // curr_data["total"]}% full')
        elif prev_data['seconds'] < sptime < curr_data['seconds']:
            if curr_data['waitlisted'] > 0:
                if curr_data['waitlisted'] * 0.1 < curr_data['total']:
                    wl_msg = 'It is likely to get in through waitlist.'
                    wl_rec = 0
                elif curr_data['waitlisted'] * 0.15 < curr_data['total']:
                    wl_msg = 'It is possible to get in through waitlist.'
                    wl_rec = 1
                else:
                    wl_msg = 'It is unlikely to get in through waitlist.'
                    wl_rec = 2
            else:
                wl_msg = f'Expected Capacity: {curr_data["enrolled"] * 100 // curr_data["total"]}% full.'
                wl_rec = 3

        # full milestone
        if not full_capacity and prev_data['enrolled'] != prev_data['total'] and curr_data['enrolled'] == curr_data['total']:
            capacity_time = datetime.fromtimestamp(curr_data["seconds"])
            full_capacity = True

    if not full_capacity:
        embed.add_field(name='Capacity', value=f'Capacity is never reached.\nYou can wait to second pass this course.\n{wl_msg}', inline=False)
        rec = 3
    else:
        # if capacity is reached after second pass enrollment time
        if capacity_time > enrollment_times[1]:
            embed.add_field(name='Capacity', value=f'Capacity reached after your second pass (on {old_to_new(capacity_time)}).\nYou can wait to second pass this course.', inline=False)
            rec = 2
        # if capacity is reached before second pass enrollment time but after first pass enrollment time
        elif enrollment_times[0] < capacity_time < enrollment_times[1]:
            embed.add_field(name='Capacity', value=f'Capacity reached before your second pass (on {old_to_new(capacity_time)}).\nYou can first pass this course, but\nit is unlikely that you can enroll second pass.\n{wl_msg}', inline=False)
            rec = 1
        # if capacity is reached before first pass enrollment time
        elif capacity_time < enrollment_times[0]:
            embed.add_field(name='Capacity', value=f'Capacity reached before your first pass (on {old_to_new(capacity_time)}).\nYou likely cannot first pass this course.\n{wl_msg}', inline=False)
            rec = 0

    result = {
        'embed': embed,
        'rec': rec,
        'wl_rec': wl_rec,
        'capacity_time': capacity_time
    }

    return result

def get_info(data, course, standing):
    max_waitlist = 0
    total_off = 0
    total_joined = 0
    prev_data = data[0]
    full_capacity = False
    period = 0
    prev_period_data = data[0]

    capacity_time = None
    capacity_period = None

    embed = discord.Embed(title=f'Enrollment Statistics for {course}')

    for i in range(1, len(data)):
        prev_data = data[i - 1]
        curr_data = data[i]
        max_waitlist = max(max_waitlist, curr_data['waitlisted'])

        waitlist_diff = curr_data['waitlisted'] - prev_data['waitlisted']
        if waitlist_diff > 0:
            total_joined += waitlist_diff
        else:
            total_off -= waitlist_diff

        # print milestones
        if period < len(TIMES_TO_STR) and prev_data['seconds'] < SECONDS[period] < curr_data['seconds']:
            if period == standing + 1 or period == standing + 5:
                embed.add_field(name=f'{TIMES_TO_STR[period-1]}', value=f'START | Enrolled: {prev_period_data["enrolled"]}/{prev_period_data["total"]} ({prev_period_data["enrolled"] * 100 // prev_period_data["total"]}%) Waitlisted: {prev_period_data["waitlisted"]}\nEND | Enrolled: {curr_data["enrolled"]}/{curr_data["total"]} ({curr_data["enrolled"] * 100 // curr_data["total"]}%) Waitlisted: {curr_data["waitlisted"]}', inline=False)
            elif 8 <= period <= 10:
                embed.add_field(name=f'{TIMES_TO_STR[period]}', value=f'Enrolled: {curr_data["enrolled"]}/{curr_data["total"]} ({curr_data["enrolled"] * 100 // curr_data["total"]}%) Waitlisted: {curr_data["waitlisted"]}', inline=False)
            prev_period_data = curr_data
            period += 1

        # full milestone
        if not full_capacity and prev_data['enrolled'] != prev_data['total'] and curr_data['enrolled'] == curr_data['total']:
            capacity_time = datetime.fromtimestamp(curr_data["seconds"])
            capacity_period = TIMES_TO_STR[period - 1]
            full_capacity = True

    if not full_capacity:
        embed.add_field(name = 'Capacity', value=f'Capacity never reached', inline=False)
    else:
        embed.add_field(name='Capacity', value=f'Capacity reached at time {capacity_time} (**{capacity_period}**)', inline=False)

    embed.add_field(name='Miscellaneous Statistics', value=f''' - Maximum number of waitlists: {max_waitlist}
 - Approximate total number of students that joined the waitlist: {total_joined}
 - Approximate total number of students off/left the waitlist: {total_off}''', inline=False)

    return embed

def plot_enrollment(data, course):

    data_stream = io.BytesIO()

    fig, ax = plt.subplots()

    ax.set_title(f'Enrollment Period for {course} for Winter 2023')
    ax.set_ylabel('Total Seats')

    ax.plot([e['seconds'] for e in data], [e['enrolled'] for e in data], color='red')
    ax.plot([e['seconds'] for e in data], [e['total'] for e in data], color='purple')
    ax.plot([e['seconds'] for e in data], [e['waitlisted'] for e in data], color='blue')


    y_lim = max([e['total'] for e in data]) * 1.05

    ax.set_xticks(list(map(get_seconds, TIMES)))
    ax.set_xticklabels(TIMES)
    ax.set(xlim=(SECONDS[0] - 86400, SECONDS[8] + 86400),
        ylim=(0, y_lim))

    ax.yaxis.grid()

    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(False)

    # Plot the background rectangles indicating time periods
    for i in range(8):
        rectangle = patches.Rectangle((SECONDS[i], 0), SECONDS[i+1]-SECONDS[i], y_lim, edgecolor=COLORS[(i%4)*2],
        facecolor=COLORS[(i%4)*2 + 1], linewidth=1)
        ax.add_patch(rectangle)
        rx, ry = rectangle.get_xy()
        cx = rx + rectangle.get_width()/2.0
        cy = ry + rectangle.get_height()/2.0
        ax.annotate(TIMES_TO_STR[i], (cx, cy), color='#424242', weight='bold', fontsize=10, ha='center', va='center', rotation=90)

    plt.setp(ax.get_xticklabels(), rotation=30, horizontalalignment='right')
    
    plt.savefig(data_stream, format='png', bbox_inches="tight", dpi = 80)
    plt.close()

    return data_stream

def parse_times(time):
    pass

def config_load():
    with open(os.path.join(os.getcwd(), 'config.json')) as f:
        data = json.load(f)
        return data