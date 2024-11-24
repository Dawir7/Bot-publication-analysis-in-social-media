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
from dotenv import load_dotenv

import re
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

load_dotenv(override=True)

# config = configparser.ConfigParser()
# config.read("config.ini")

reddit = praw.Reddit(
    client_id=os.getenv('BOTLOGIN'),
    client_secret=os.getenv('BOTSECRET'), 
    password=os.getenv('PASSWORD'),
    user_agent='lab7',
    username=os.getenv('LOGIN'),
)

DIRECTORY = "data"
TIME_FILTER = "month"
STEP = 999
LIMIT = 1000
FETCHED_SUBREDDITS_FILE = f"{DIRECTORY}/fetched_subreddits.txt"
FETCHED_USERS_FILE = f"{DIRECTORY}/fetched_users.txt"

MAX_WORKERS = os.cpu_count()
print(f"Max workers: {MAX_WORKERS}")

SCOPES = ['https://www.googleapis.com/auth/drive.file']
SERVICE_ACCOUNT_FILE = 'amc-data-apikey.json'
DRIVE_FOLDER_URL = 'https://drive.google.com/drive/folders/1ZpvINF1r_vgOk8IAsWoVIt_yhWChKpCA'
DRIVE_FOLDER_ID = re.search(r'/folders/([a-zA-Z0-9_-]+)', DRIVE_FOLDER_URL).group(1)

if not os.path.exists(SERVICE_ACCOUNT_FILE):
    print('Please download the API key file from Google Cloud Console and save it as amc-data-apikey.json')
    exit()

credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES)
service = build('drive', 'v3', credentials=credentials)

I = 0


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
        "title": str(submission.title).replace('\n', ''),
        "text": str(submission.selftext).replace('\n', ''),
        "is_original_content": submission.is_original_content,
        "num_comments": submission.num_comments,
        "score": submission.score,
        "upvote_ratio": submission.upvote_ratio,
        "date": pd.to_datetime(submission.created_utc, unit="s"),
    }
    if submission.author is not None:
        users = [submission.author.name]
    else:
        users = []
    comments = []
    submission.comments.replace_more(limit=0)
    for comment in submission.comments.list():
        comment_data = {
            "subreddit": subreddit,
            "username": comment.author.name if comment.author else None,
            "body": str(comment.body).replace('\n', ''),
            "post_title": str(submission.title).replace('\n', ''),
            "score": comment.score,
            "num_replies": len(comment.replies),
            "is_submitter": comment.is_submitter,
            "id": comment.id,
            "parent_id": comment.parent_id,
            "stickied": comment.stickied,
            "date": pd.to_datetime(comment.created_utc, unit="s"),
        }
        comments.append(comment_data)
        if comment.author is not None:
            users.append(comment.author.name)

    return post_data, comments, users


@retry(TooManyRequests)
def process_user(username):
    user = reddit.redditor(username)
    try:
        user_data = {
            "username": username,
            "link_karma": user.link_karma,
            "comment_karma": user.comment_karma,
            "account_age": (
                pd.to_datetime("now") - pd.to_datetime(user.created_utc, unit="s")
            ).days,
            "is_verified": user.has_verified_email,
        }
    except:
        user_data = {
            "username": username,
            "link_karma": None,
            "comment_karma": None,
            "account_age": None,
            "is_verified": None,
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


@retry(TooManyRequests)
def get_posts_for_subreddit(subreddit: str):
    print(f"Fetching data for subreddit {subreddit}")
    posts = []
    comments = []
    users = []

    submissions = list(
        reddit.subreddit(subreddit).top(time_filter=TIME_FILTER, limit=LIMIT)
    )

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = [
            executor.submit(process_submission, submission, subreddit)
            for submission in submissions
        ]

        counter = 0

        for future in tqdm(
            as_completed(futures),
            total=len(futures),
            desc=f"Processing submissions for {subreddit}",
        ):
            post_data, comment_data, users_list = future.result()
            posts.append(post_data)
            comments.extend(comment_data)
            users.extend(users_list)
            counter += 1
            

            if counter % STEP == 0:
                posts_df = pd.DataFrame(posts)
                comments_df = pd.DataFrame(comments)
                save_data(posts_df, comments_df, None, DIRECTORY, subreddit)

                posts = []
                comments = []
                posts_df = None
                comments_df = None

    return posts, comments, users


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


def get_user_data(users): # posts, comments
    fetched_users = get_fetched_users()
    # users = get_users_from_data(posts, comments)
    users = set(users)
    users_to_fetch = users - fetched_users

    user_data = []
    user_posts = []
    user_comments = []

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = [executor.submit(process_user, user) for user in users_to_fetch]

        counter = 0

        for future in tqdm(
            as_completed(futures), total=len(futures), desc="Processing user data"
        ):
            user_data.append(future.result())

            counter += 1

            if counter % STEP == 0:
                user_df = pd.DataFrame(user_data)
                save_data(None, None, user_df, DIRECTORY, subreddit)

                user_data = []
                user_df = None

        futures = [
            executor.submit(fetch_user_activity, user) for user in users_to_fetch
        ]

        counter = 0

        for future in tqdm(
            as_completed(futures), total=len(futures), desc="Fetching user activity"
        ):
            user_submissions, user_comments_data = future.result()
            user_posts.extend(user_submissions)
            user_comments.extend(user_comments_data)

            counter += 1

            if counter % STEP == 0:
                posts_df = pd.DataFrame(user_posts)
                comments_df = pd.DataFrame(user_comments)
                save_data(posts_df, comments_df, None, DIRECTORY, subreddit)

                user_posts = []
                user_comments = []
                posts_df = None
                comments_df = None

    user_df = pd.DataFrame(user_data)
    user_posts_df = pd.DataFrame(user_posts)
    user_comments_df = pd.DataFrame(user_comments)

    for user in users_to_fetch:
        mark_user_as_fetched(user)

    return user_df, user_posts_df, user_comments_df


def main(subreddit: str):
    posts, comments, users = get_posts_for_subreddit(subreddit)
    print(
        f"Found {len(posts)} posts and {len(comments)} comments for subreddit {subreddit}\n"
    )

    posts_df = pd.DataFrame(posts)
    comments_df = pd.DataFrame(comments)

    user_df, user_posts_df, user_comments_df = get_user_data(users)

    combined_posts_df = pd.concat([posts_df, user_posts_df]).drop_duplicates(
        subset=["name"]
    )
    combined_comments_df = pd.concat([comments_df, user_comments_df]).drop_duplicates(
        subset=["id"]
    )

    return combined_posts_df, combined_comments_df, user_df

def upload_csv_to_drive(file_path, folder_id):
    file_metadata = {
        'name': os.path.basename(file_path),
        'parents': [folder_id]
    }
    media = MediaFileUpload(file_path, mimetype='text/csv')
    file = service.files().create(
        body=file_metadata,
        media_body=media,
        fields='id'
    ).execute()
    print(f'File ID: {file.get("id")}')


def save_data(posts_df, comments_df, user_df, directory, subreddit):
    global I
    posts_file = f"{directory}/all_posts{I}.csv"
    comments_file = f"{directory}/all_comments{I}.csv"
    user_file = f"{directory}/user_data{I}.csv"
    posts_file_pickle = f"{directory}/all_posts{I}.pkl"
    comments_file_pickle = f"{directory}/all_comments{I}.pkl"
    user_file_pickle = f"{directory}/user_data{I}.pkl"

    if posts_df is not None:
        if not posts_df.empty:
            posts_df.text = posts_df.text.str.replace('\n', ' ')
            posts_df.title = posts_df.title.str.replace('\n', ' ')
            posts_df.to_csv(posts_file, index=False, quoting=csv.QUOTE_ALL, escapechar='\\', lineterminator='\n')
            upload_csv_to_drive(posts_file, DRIVE_FOLDER_ID)
            posts_df.to_pickle(posts_file_pickle)
            os.remove(posts_file)
    if comments_df is not None:
        if not comments_df.empty:
            comments_df.body = comments_df.body.str.replace('\n', ' ')
            comments_df.post_title = comments_df.post_title.str.replace('\n', ' ')
            comments_df.to_csv(comments_file, index=False, quoting=csv.QUOTE_ALL, escapechar='\\', lineterminator='\n')
            upload_csv_to_drive(comments_file, DRIVE_FOLDER_ID)
            comments_df.to_pickle(comments_file_pickle)
            os.remove(comments_file)
    if user_df is not None:
        if not user_df.empty:
            user_df.to_csv(user_file, index=False, quoting=csv.QUOTE_ALL, escapechar='\\', lineterminator='\n')
            upload_csv_to_drive(user_file, DRIVE_FOLDER_ID)
            user_df.to_pickle(user_file_pickle)
            os.remove(user_file)
    
    print(f"Data {I} saved for subreddit {subreddit}")
    I += 1


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

        posts_df, comments_df, user_df = main(subreddit)
        save_data(posts_df, comments_df, user_df, DIRECTORY, subreddit)
        mark_subreddit_as_fetched(subreddit)
        print(f"Data processed for subreddit {subreddit}\n")
        print(f"Time elapsed for subreddit {subreddit}: {datetime.now() - start}")

    print("All data saved successfully\n")
    print(f"Time elapsed (final): {datetime.now() - start}")
