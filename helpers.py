# -*- coding: utf-8 -*-
import re
import time
import locale
import datetime

import humanize
import logging
import requests

# For converting from string numbers with english-based commas to floats
# locale.setlocale(locale.LC_ALL, 'eng_USA') # Windows
locale.setlocale(locale.LC_ALL, 'en_GB.utf8') # Linux (Raspberry Pi 2)



# === Logging === #
logger = logging.getLogger(__name__)


# === Helper functions === #
FOOTER_MESSAGE = 'DNStats BOT'


def generate_response_footer():
    """Generates a response footer using the footer message. TODO: (CHANGE IT TO WHATEVER YOU WANT)"""
    return f"\n\n---\n\n {FOOTER_MESSAGE}"


def humanize_minutes(minutes):
    """Humanizes a minute duration to the past"""
    return humanize.naturaltime(datetime.datetime.now() - datetime.timedelta(minutes=minutes))


def get_marketname_data(marketname):
    """
    Gets a market status from the given marketname from the dnstats.net api
    :param marketname: market name used on the api query
    :return marketname: the marketname api response if the status code is ok. If not it raises an HTTPError.
    """
    logger.debug('Fetching the marketname status')
    response = requests.get('https://dnstats.net/apii.php', params={'market': marketname})
    # Checking the response code.
    if response.status_code == requests.codes.ok:
        return response.json()
    else:
        # Raising an exception if the response code is not ok
        raise requests.exceptions.HTTPError('The DNstats api seems to be having problems')


def generate_response_message(marketname):
    """
    Generates the response message from the marketname result
    :param marketname: name to look if it's down 
    :return: a formatted response message
    """
    logger.debug(f'Generating a formatted response message for the market {marketname}')
    data = get_marketname_data(marketname)
    logger.debug(f'marketname data retrieved with body: {data}')
    # Checking if the response has an id to see if the marketname exists
    if data['id']:
        # Formatting the middle message according to the site status
        if data['status'] == 'Up':
            middle_message = f"is up and in the last hour it has been up {data['1hr_uptime']}%"
        elif data['status'] == 'Down':
            middle_message = (
                f"is down. In the last hour it has been up {data['1hr_uptime']}%. " +
                f"The last time online was {humanize_minutes(int(data['last online in minutes']))}""")
        else:
            # If we get an unknown status we just add it to the message
            middle_message = f"is {data['status']}"
    else:
        # If the data id is null (None on python) the market doesn't exist
        middle_message = "doesn't exist."
    response_message = f'[{marketname}](https://dnstats.net/market/{marketname}) {middle_message}'

    logger.debug(f'Response message generated: {response_message}')
    return response_message


# Regex pattern to look for IS X DOWN in a string. Created outside the search_for_pattern function to cache the regex pattern.
# This pattern should match anything in the middle of `is XXXXX down?`. Accepting a max of 5 random characters after down
# and the ? symbol. Ejem: is agora downxadw? matches. is agora downasdasdad? dont.
pattern = re.compile(r'is (.+) (down|up|offline).{0,5}\?', re.IGNORECASE)

#pattern = re.compile(r'is (.+) down.{0,5}\?', re.IGNORECASE)


def search_for_pattern(body_text):
    """Uses the pre-compiled regex pattern to search on the message body. Returns just the matched group"""
    result = pattern.search(body_text)
    if result:
        logger.debug(f'Result {result} was found on {body_text}')
        return result.group(1)
    else:
        return None


def has_been_replied_by_bot(comment, me):
    """Checks if a comment has been replied already by the bot. It checks if any the replies on the comment has been made by the 
    reddit bot
    """
    # Checking if the parent comment has been made by the bot.
    if comment.author == me:
        return True

    # Getting the comment replies
    comment.refresh()
    for reply in comment.replies.list():
        if reply.author == me:
            return True

    # If *True* hasn't been returned to this point. It means that nor the parent comment nor any of the replies was made by the
    # bot, so we return False
    return False


def wait_with_comments(sleep_time, segment=60):
    """Sleep for sleep_time seconds, printing to stdout every segment of time"""
    print("\t%s - %s seconds to go..." % (datetime.datetime.now(), sleep_time))
    while sleep_time > segment:
        time.sleep(segment)  # sleep in increments of 1 minute
        sleep_time -= segment
        print("\t%s - %s seconds to go..." % (datetime.datetime.now(), sleep_time))
    time.sleep(sleep_time)


def log_comment(comment, status=""):
    print("{} | {} {}: {}".format(datetime.datetime.now(), comment.id, status,
                                  comment.body[:80].replace('\n', '\\n').encode('utf-8')))
