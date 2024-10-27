import configparser
import functools
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

import pandas as pd
import praw
from prawcore.exceptions import TooManyRequests
from tqdm import tqdm

config = configparser.ConfigParser()
config.read("config.ini")

reddit = praw.Reddit(
    client_id=config["reddit"]["client_id"],
    client_secret=config["reddit"]["client_secret"],
    password=config["reddit"]["password"],
    user_agent=config["reddit"]["user_agent"],
    username=config["reddit"]["username"],
)

DIRECTORY = "data"
TIME_FILTER = "month"
LIMIT = None
FETCHED_SUBREDDITS_FILE = f"{DIRECTORY}\\fetched_subreddits.txt"


def retry(exceptions, tries=4, delay=3, backoff=2):
    def decorator_retry(func):
        @functools.wraps(func)
        def wrapper_retry(*args, **kwargs):
            _tries, _delay = tries, delay
            while _tries > 1:
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    print(f"{e}, Retrying in {_delay} seconds...")
                    time.sleep(_delay)
                    _tries -= 1
                    _delay *= backoff
            return func(*args, **kwargs)

        return wrapper_retry

    return decorator_retry


@retry(TooManyRequests)
def process_submission(submission, subreddit):
    post_data = {
        "subreddit": subreddit,
        "username": submission.author.name if submission.author else None,
        "name": submission.name,
        "title": submission.title,
        "text": submission.selftext,
        "is_original_content": submission.is_original_content,
        "num_comments": submission.num_comments,
        "score": submission.score,
        "upvote_ratio": submission.upvote_ratio,
        "date": pd.to_datetime(submission.created_utc, unit="s"),
        # "author_karma": submission.author.link_karma + submission.author.comment_karma if submission.author else None,
        # "author_account_age": (pd.to_datetime('now') - pd.to_datetime(submission.author.created_utc, unit="s")).days if submission.author else None,
        # "author_is_verified": submission.author.has_verified_email if submission.author else None,
    }

    comments = []
    submission.comments.replace_more(limit=0)
    for comment in submission.comments.list():
        comment_data = {
            "subreddit": subreddit,
            "username": comment.author.name if comment.author else None,
            "body": comment.body,
            "post_title": submission.title,
            "score": comment.score,
            "num_replies": len(comment.replies),
            "is_submitter": comment.is_submitter,
            "id": comment.id,
            "parent_id": comment.parent_id,
            "stickied": comment.stickied,
            "date": pd.to_datetime(comment.created_utc, unit="s"),
            # "author_karma": comment.author.link_karma + comment.author.comment_karma if comment.author else None,
            # "author_account_age": (pd.to_datetime('now') - pd.to_datetime(comment.author.created_utc, unit="s")).days if comment.author else None,
            # "author_is_verified": comment.author.has_verified_email if comment.author else None,
        }
        comments.append(comment_data)

    return post_data, comments


def remove_duplicates(submissions):
    seen = set()
    unique_submissions = []
    for submission in tqdm(submissions, desc="Removing duplicates"):
        if submission.id not in seen:
            unique_submissions.append(submission)
            seen.add(submission.id)
    return unique_submissions


def get_posts_for_subreddit(subreddit: str):
    print(f"Fetching data for subreddit {subreddit}")
    posts = []
    comments = []

    submissions = list(
        reddit.subreddit(subreddit).top(time_filter=TIME_FILTER, limit=LIMIT)
    )
    top1_submissions = list(reddit.subreddit(subreddit).top(time_filter="year", limit=LIMIT))
    top2_submissions = list(reddit.subreddit(subreddit).controversial(time_filter="year", limit=LIMIT))
    top3_submissions = list(reddit.subreddit(subreddit).top(time_filter="month", limit=LIMIT))
    top4_submissions = list(reddit.subreddit(subreddit).controversial(time_filter="month", limit=LIMIT))
    top5_submissions = list(reddit.subreddit(subreddit).top(time_filter="week", limit=LIMIT))
    new_submissions = list(reddit.subreddit(subreddit).new(limit=LIMIT))
    hot_submissions = list(reddit.subreddit(subreddit).hot(limit=LIMIT))
    rising_submissions = list(reddit.subreddit(subreddit).rising(limit=LIMIT))

    all_submissions = top1_submissions + top2_submissions + top3_submissions + top4_submissions + top5_submissions + new_submissions + hot_submissions + rising_submissions
    submissions = remove_duplicates(all_submissions)

    with ThreadPoolExecutor() as executor:
        futures = [
            executor.submit(process_submission, submission, subreddit)
            for submission in submissions
        ]

        for future in tqdm(
            as_completed(futures),
            total=len(futures),
            desc=f"Processing submissions for {subreddit}",
        ):
            post_data, comment_data = future.result()
            posts.append(post_data)
            comments.extend(comment_data)

    return posts, comments


def main(subreddit: str):
    posts, comments = get_posts_for_subreddit(subreddit)
    print(
        f"Found {len(posts)} posts and {len(comments)} comments for subreddit {subreddit}\n"
    )

    posts_df = pd.DataFrame(posts)
    comments_df = pd.DataFrame(comments)

    return posts_df, comments_df


def save_data(posts_df, comments_df, directory, subreddit):
    posts_file = f"{directory}\\all_posts.csv"
    comments_file = f"{directory}\\all_comments.csv"

    if not os.path.isfile(posts_file):
        posts_df.to_csv(posts_file, index=False, escapechar='\\', quoting=csv.QUOTE_NONE)
    else:
        posts_df.to_csv(posts_file, mode="a", header=False, index=False, escapechar='\\', quoting=csv.QUOTE_NONE)

    if not os.path.isfile(comments_file):
        comments_df.to_csv(comments_file, index=False, escapechar='\\', quoting=csv.QUOTE_NONE)
    else:
        comments_df.to_csv(comments_file, mode="a", header=False, index=False, escapechar='\\', quoting=csv.QUOTE_NONE)

    print(f"Data saved for subreddit {subreddit}")


def mark_subreddit_as_fetched(subreddit):
    with open(FETCHED_SUBREDDITS_FILE, "a") as file:
        file.write(f"{subreddit}\n")


def get_fetched_subreddits():
    if not os.path.isfile(FETCHED_SUBREDDITS_FILE):
        return set()
    with open(FETCHED_SUBREDDITS_FILE, "r") as file:
        return set(line.strip() for line in file)


if __name__ == "__main__":
    start = datetime.now()

    if not os.path.isdir(DIRECTORY):
        os.mkdir(DIRECTORY)
        print(f"Directory {DIRECTORY} created")

    fetched_subreddits = get_fetched_subreddits()

    subreddits = [
        "funny",
        "AskReddit",
        "gaming",
        "worldnews",
        "todayilearned",
    ]

    for subreddit in subreddits:
        if subreddit in fetched_subreddits:
            print(f"Subreddit {subreddit} already fetched. Skipping.")
            continue

        posts_df, comments_df = main(subreddit)
        save_data(posts_df, comments_df, DIRECTORY, subreddit)
        mark_subreddit_as_fetched(subreddit)
        print(f"Data processed for subreddit {subreddit}\n")
        print(f"Time elapsed for subreddit {subreddit}: {datetime.now() - start}")

    print("All data saved successfully\n")
    print(f"Time elapsed (final): {datetime.now() - start}")
