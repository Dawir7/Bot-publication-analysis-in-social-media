import configparser
import csv
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
LIMIT = 10
FETCHED_SUBREDDITS_FILE = f"{DIRECTORY}\\fetched_subreddits.txt"
USER_DATA_FILE = f"{DIRECTORY}\\user_data.csv"
FETCHED_USERS_FILE = f"{DIRECTORY}\\fetched_users.txt"

MAX_WORKERS = os.cpu_count() * 6
print(f"Max workers: {MAX_WORKERS}")


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
        }
        comments.append(comment_data)

    return post_data, comments


@retry(TooManyRequests)
def process_user(username):
    user = reddit.redditor(username)
    user_data = {
        "username": username,
        "link_karma": user.link_karma,
        "comment_karma": user.comment_karma,
        "account_age": (
            pd.to_datetime("now") - pd.to_datetime(user.created_utc, unit="s")
        ).days,
        "is_verified": user.has_verified_email,
    }
    return user_data


@retry(TooManyRequests)
def fetch_user_activity(username):
    user = reddit.redditor(username)
    submissions = []
    comments = []

    for submission in user.submissions.new(limit=LIMIT):
        submissions.append(
            {
                "username": username,
                "name": submission.name,
                "title": submission.title,
                "text": submission.selftext,
                "is_original_content": submission.is_original_content,
                "num_comments": submission.num_comments,
                "score": submission.score,
                "upvote_ratio": submission.upvote_ratio,
                "date": pd.to_datetime(submission.created_utc, unit="s"),
            }
        )

    for comment in user.comments.new(limit=LIMIT):
        comments.append(
            {
                "username": username,
                "body": comment.body,
                "post_title": comment.submission.title,
                "score": comment.score,
                "num_replies": len(comment.replies),
                "is_submitter": comment.is_submitter,
                "id": comment.id,
                "parent_id": comment.parent_id,
                "stickied": comment.stickied,
                "date": pd.to_datetime(comment.created_utc, unit="s"),
            }
        )

    return submissions, comments


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

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
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


def get_users_from_data(posts, comments):
    users = set()
    for post in posts:
        if post["username"]:
            users.add(post["username"])
    for comment in comments:
        if comment["username"]:
            users.add(comment["username"])
    return users


def get_fetched_users():
    if not os.path.isfile(FETCHED_USERS_FILE):
        return set()
    with open(FETCHED_USERS_FILE, "r") as file:
        return set(line.strip() for line in file)


def mark_user_as_fetched(username):
    with open(FETCHED_USERS_FILE, "a") as file:
        file.write(f"{username}\n")


def get_user_data(posts, comments):
    fetched_users = get_fetched_users()
    users = get_users_from_data(posts, comments)
    users_to_fetch = users - fetched_users

    user_data = []
    user_posts = []
    user_comments = []

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = [executor.submit(process_user, user) for user in users_to_fetch]
        for future in tqdm(
            as_completed(futures), total=len(futures), desc="Processing user data"
        ):
            user_data.append(future.result())

        futures = [
            executor.submit(fetch_user_activity, user) for user in users_to_fetch
        ]
        for future in tqdm(
            as_completed(futures), total=len(futures), desc="Fetching user activity"
        ):
            user_submissions, user_comments_data = future.result()
            user_posts.extend(user_submissions)
            user_comments.extend(user_comments_data)

    user_df = pd.DataFrame(user_data)
    user_posts_df = pd.DataFrame(user_posts)
    user_comments_df = pd.DataFrame(user_comments)

    for user in users_to_fetch:
        mark_user_as_fetched(user)

    return user_df, user_posts_df, user_comments_df


def main(subreddit: str):
    posts, comments = get_posts_for_subreddit(subreddit)
    print(
        f"Found {len(posts)} posts and {len(comments)} comments for subreddit {subreddit}\n"
    )

    posts_df = pd.DataFrame(posts)
    comments_df = pd.DataFrame(comments)

    user_df, user_posts_df, user_comments_df = get_user_data(posts, comments)

    combined_posts_df = pd.concat([posts_df, user_posts_df]).drop_duplicates(
        subset=["name"]
    )
    combined_comments_df = pd.concat([comments_df, user_comments_df]).drop_duplicates(
        subset=["id"]
    )

    return combined_posts_df, combined_comments_df, user_df


def save_data(posts_df, comments_df, user_df, directory, subreddit):
    posts_file = f"{directory}\\all_posts.csv"
    comments_file = f"{directory}\\all_comments.csv"
    user_file = USER_DATA_FILE

    if not os.path.isfile(posts_file):
        posts_df.to_csv(posts_file, index=False, escapechar='\\', quoting=csv.QUOTE_NONE)
    else:
        posts_df.to_csv(posts_file, mode="a", header=False, index=False, escapechar='\\', quoting=csv.QUOTE_NONE)

    if not os.path.isfile(comments_file):
        comments_df.to_csv(comments_file, index=False, escapechar='\\', quoting=csv.QUOTE_NONE)
    else:
        comments_df.to_csv(comments_file, mode="a", header=False, index=False, escapechar='\\', quoting=csv.QUOTE_NONE)

    if not os.path.isfile(user_file):
        user_df.to_csv(user_file, index=False, escapechar='\\', quoting=csv.QUOTE_NONE)
    else:
        user_df.to_csv(user_file, mode="a", header=False, index=False, escapechar='\\', quoting=csv.QUOTE_NONE)

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
        # "funny",
        "AskReddit",
        # "gaming",
    ]

    for subreddit in subreddits:
        if subreddit in fetched_subreddits:
            print(f"Subreddit {subreddit} already fetched. Skipping.")
            continue

        posts_df, comments_df, user_df = main(subreddit)
        save_data(posts_df, comments_df, user_df, DIRECTORY, subreddit)
        mark_subreddit_as_fetched(subreddit)
        print(f"Data processed for subreddit {subreddit}\n")
        print(f"Time elapsed for subreddit {subreddit}: {datetime.now() - start}")

    print("All data saved successfully\n")
    print(f"Time elapsed (final): {datetime.now() - start}")
