#!/usr/bin/env python
# -*- coding: utf-8 -*-
# DNStats daemon
# Listens on DNSTats subreddit for comments that
# have is MARKETNAME down conversion requests in them and respond with conversion
# Run with --dry to dry run without actual submissions
from __future__ import print_function

import logging
import praw
import requests
import socket
import time
from datetime import datetime
import argparse

from helpers import (has_been_replied_by_bot,
                     search_for_pattern,
                     generate_response_message,
                     log_comment,
                     wait_with_comments,
                     submission_has_been_replied_by_bot)

# === Constants === #
REPLY_WAIT_TIME = 5
FAIL_WAIT_TIME = 30
NO_COMMENTS_OF_SUBMISSIONS_WAIT_TIME = 200

# === LOGGING === #
logger = logging.getLogger(__name__)


def start_stream(args):
    """
    Starts the comment stream from the DNStats subreddit using praw to interact with the reddit API
    """
    reddit = praw.Reddit('dnstatsbot')  # client credentials set up in local praw.ini file. Check praw.ini.example for more info.
    bot = reddit.user.me()  # Bot object. It refers to the user who has it's credentials set in praw.ini
    subreddit = reddit.subreddit('Dnstatsbot')  # Initializing the subreddit object with the subreddit name.

    # Set to store the submissions ID to avoid processing them again.
    seen_submissions_id = set()

    # Start live stream on comment stream for the subreddit
    for comment, submission in zip(subreddit.stream.comments(pause_after=2), subreddit.stream.submissions(pause_after=0)):

        # Sleepeing if there isn't comments of submission
        if not (comment and submission):
            logger.info(f'There is no new comments or submissions available. Sleeping: {NO_COMMENTS_OF_SUBMISSIONS_WAIT_TIME}s')
            time.sleep(NO_COMMENTS_OF_SUBMISSIONS_WAIT_TIME)

        # Submission processing
        # Checking if a submission was yield
        if submission and submission.id not in seen_submissions_id:
            seen_submissions_id.add(submission.id)
            if not submission_has_been_replied_by_bot(submission, bot):
                search_result_title, search_result_text = (search_for_pattern(submission.title),
                                                           search_for_pattern(submission.selftext))

                if search_result_title:
                    search_result_submission = search_result_title

                else:
                    search_result_submission = search_result_text

                if search_result_submission:
                    logger.debug(f'Generating response for {submission.id}')
                    response = generate_response_message(search_result_submission)

                    # Reply to comment with response
                    if not args.dry:
                        submission.reply(response)
                        logger.info(f'Responding to {submission.id} with response: {response}')
                    else:
                        logger.info(f'Responding (DRY) to {submission.id} with response: {response}')

        # Comment Processing.
        # Checking if a comment was yield
        if not comment:
            continue

        # Check if comment already has a reply
        if not has_been_replied_by_bot(comment, bot):
            logger.debug(f'Processing comment {comment.id} with body {comment.body}')
            if len(comment.body) > 9000:
                # Ignore really long comments, worst case 9000 nines takes ~27 seconds to search through
                logger.debug('Comment too long. Dropping it.')
                search_result = None
            else:
                # Checking if the comment body contains the regex pattern
                body = str(comment.body)
                search_result = search_for_pattern(body)
            if search_result:
                # Generate response
                logger.debug(f'Generating response for {comment.id}')
                response = generate_response_message(search_result)

                # Reply to comment with response
                if not args.dry:
                    comment.reply(response)
                    log_comment(comment, '[REPLIED]')
                else:
                    log_comment(comment, "[DRY-RUN-REPLIED]")

                # Wait after submitting to not overload
                wait_with_comments(REPLY_WAIT_TIME)

            else:
                # Not a schmeckle message
                logger.debug(f'comment {comment.id} did not match')
                time.sleep(1)  # Wait a second between normal submissions

        else:
            logger.debug(f'comment {comment.id} has been replied already. Skipping')  # Skip since replied to already

def main(args):
    running = True
    while running:
        try:
            start_stream(args)
        except (socket.error, requests.exceptions.ReadTimeout,
                requests.packages.urllib3.exceptions.ReadTimeoutError,
                requests.exceptions.ConnectionError) as e:
            print(
                "> %s - Connection error, retrying in %d seconds: %s" % (
                    FAIL_WAIT_TIME, datetime.now(), e))
            time.sleep(FAIL_WAIT_TIME)
            continue
        except Exception as e:
            raise e
            print('Unknown Error, {}, attempting restart in {} seconds:'.format(str(e), FAIL_WAIT_TIME))
            time.sleep(FAIL_WAIT_TIME)
            continue
        except KeyboardInterrupt:
            print("Keyboard Interrupt: Exiting...")
            running = False
    print('Finished')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--log_level', help='Log level for the bot (DEBUG, INFO, etc)', default='DEBUG')
    parser.add_argument('--dry', help='dry run (don\'t actually submit replies)',
                        action="store_true", default=False)
    args = parser.parse_args()
    logging.basicConfig(level=args.log_level)
    main(args)
