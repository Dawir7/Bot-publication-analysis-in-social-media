import re
from datetime import datetime
from string import punctuation

import emoji
import pandas as pd
import textstat
from nltk.tokenize import word_tokenize
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import normalize
from tqdm import tqdm

DIR = "data"
comments_file_path = f"{DIR}/all_comments-merged.csv"
posts_file_path = f"{DIR}/all_posts-merged.csv"
users_file_path = f"{DIR}/user_data-merged.csv"
x_file_path = f"{DIR}/features.csv"
y_file_path = f"{DIR}/labels.csv"


# Load data
def load_data(posts_file_path, comments_file_path, users_file_path):
    print("Loading data...")
    posts_df = pd.read_csv(posts_file_path)
    comments_df = pd.read_csv(comments_file_path)
    users_df = pd.read_csv(users_file_path)

    # Remove rows with NaN values in the 'body' column
    comments_df = comments_df.dropna(subset=["body"])

    # Remove duplicate rows in posts_df and comments_df
    posts_df = posts_df.drop_duplicates()
    comments_df = comments_df.drop_duplicates()

    # Remove duplicate usernames in users_df
    users_df = users_df.drop_duplicates(subset="username")

    print("Data loaded successfully.\n")
    return posts_df, comments_df, users_df


# Helper functions
def clean_text(text):
    text = re.sub(r"[^\w\s]", "", text)
    text = text.lower()
    return text


def add_tfidf_vectors(comments_df):
    comments_df["cleaned_body"] = comments_df["body"].apply(clean_text)
    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform(comments_df["cleaned_body"])
    tfidf_matrix = normalize(tfidf_matrix)
    tfidf_vectors = [vec for vec in tfidf_matrix]
    comments_df["vector"] = tfidf_vectors

    return comments_df


def remove_zwj(comment):
    zwj = "\u200d"
    return comment.replace(zwj, "")


def is_weird_comment(comments):
    if all(
        len(comment) <= 1 or all(char in punctuation for char in comment)
        for comment in comments
    ):
        return True
    if all(
        len(emoji.emoji_list(comment)) == 1
        and emoji.emoji_list(comment)[0]["emoji"] == comment
        for comment in comments
    ):
        return True
    if all(all(emoji.is_emoji(char) for char in comment) for comment in comments):
        return True
    if all(
        len(emoji.emoji_list(comment))
        == len([char for char in comment if emoji.is_emoji(char)])
        for comment in comments
    ):
        return True
    if all(
        all(char in emoji.EMOJI_DATA for char in remove_zwj(comment))
        for comment in comments
    ):
        return True

    return False


# New features
def add_avg_cosine_similarity(df, comments_df):
    vectorizer = TfidfVectorizer()
    grouped_comments = comments_df.groupby("username")["cleaned_body"].apply(list)
    avg_cosine_similarities = {}

    for username, comments in tqdm(
        grouped_comments.items(),
        desc="Processing cosine similarities of comments",
        total=len(grouped_comments),
    ):
        if is_weird_comment(comments) and len(comments) > 1:
            avg_cosine_similarity = 1.0
        elif len(comments) > 1:
            tfidf_matrix = vectorizer.fit_transform(comments)
            cosine_sim_matrix = cosine_similarity(tfidf_matrix)
            avg_cosine_similarity = (cosine_sim_matrix.sum() - len(comments)) / (
                len(comments) * (len(comments) - 1)
            )
        else:
            avg_cosine_similarity = None

        avg_cosine_similarities[username] = avg_cosine_similarity

    avg_cosine_similarities_df = pd.DataFrame(
        list(avg_cosine_similarities.items()),
        columns=["username", "avg_cosine_similarity"],
    )
    df = df.merge(avg_cosine_similarities_df, on="username", how="left")
    print("Feature avg_cosine_similarity created successfully.")

    return df


def add_all_users_similarity(df, comments_df):
    sampled_comments = comments_df["cleaned_body"].sample(n=5000, random_state=42).tolist()

    vectorizer = TfidfVectorizer()
    sampled_matrix = vectorizer.fit_transform(sampled_comments)

    grouped_comments = comments_df.groupby("username")["cleaned_body"].apply(list)
    all_users_similarities = {}

    for username, comments in tqdm(
        grouped_comments.items(),
        desc="Processing cosine similarities of comments",
        total=len(grouped_comments),
    ):
        if len(comments) > 0:
            user_matrix = vectorizer.transform(comments)
            cosine_sim_matrix = cosine_similarity(user_matrix, sampled_matrix)
            avg_cosine_similarity = cosine_sim_matrix.mean(axis=1).mean()
        else:
            avg_cosine_similarity = None

        all_users_similarities[username] = avg_cosine_similarity

    all_users_similarities_df = pd.DataFrame(
        list(all_users_similarities.items()),
        columns=["username", "all_users_similarity"],
    )
    df = df.merge(all_users_similarities_df, on="username", how="left")
    print("Feature all_users_similarity created successfully.")

    return df


def add_comment_length_metrics(df, comments_df):
    grouped_comments = comments_df.groupby("username")["cleaned_body"].apply(list)

    avg_lengths = {}
    max_lengths = {}
    min_lengths = {}

    for username, comments in tqdm(
        grouped_comments.items(),
        desc="Processing comments length",
        total=len(grouped_comments),
    ):
        comment_lengths = [len(comment) for comment in comments]
        avg_lengths[username] = sum(comment_lengths) / len(comment_lengths)
        max_lengths[username] = max(comment_lengths)
        min_lengths[username] = min(comment_lengths)

    df["avg_comment_length"] = comments_df["username"].map(avg_lengths)
    df["max_comment_length"] = comments_df["username"].map(max_lengths)
    df["min_comment_length"] = comments_df["username"].map(min_lengths)

    print(
        "Features avg_comment_length, max_comment_length, min_comment_length created successfully."
    )

    return df


def add_comment_post_ratio(df, comments_df, posts_df):
    comments_per_user = (
        comments_df.groupby("username").size().reset_index(name="num_comments")
    )
    posts_per_user = posts_df.groupby("username").size().reset_index(name="num_posts")
    user_stats = comments_per_user.merge(
        posts_per_user, on="username", how="outer"
    ).fillna(0)
    user_stats["comment_post_ratio"] = user_stats.apply(
        lambda row: 0
        if row["num_comments"] == 0
        else (1 if row["num_posts"] == 0 else row["num_comments"] / row["num_posts"]),
        axis=1,
    )
    df = df.merge(
        user_stats[["username", "comment_post_ratio"]], on="username", how="left"
    )
    print("Feature comment_post_ratio created successfully.")

    return df


def add_average_thread_depth(df, comments_df):
    comments_df_copy = comments_df.copy()

    def calculate_depth(comment_id, parent_lookup):
        depth = 0
        while comment_id in parent_lookup and parent_lookup[comment_id].startswith(
            "t1_"
        ):
            parent_id = parent_lookup[comment_id]
            comment_id = parent_id[3:]
            depth += 1
        return depth

    comments_df_copy["depth"] = 0

    for post_title, group in comments_df_copy.groupby("post_title"):
        parent_lookup = dict(zip(group["id"], group["parent_id"]))
        comments_df_copy.loc[group.index, "depth"] = group["id"].apply(
            lambda x: calculate_depth(x, parent_lookup)
        )

    avg_depth_per_user = (
        comments_df_copy.groupby("username")["depth"]
        .mean()
        .reset_index(name="avg_thread_depth")
    )
    df = df.merge(avg_depth_per_user, on="username", how="left")

    print("Feature avg_thread_depth created successfully.")

    return df


def add_parent_child_similarity(df, comments_df):
    comments_df_copy = comments_df.copy()

    def calculate_average_similarity(comment_id, parent_lookup, comment_vectors):
        similarities = []
        current_id = comment_id

        while current_id in parent_lookup and parent_lookup[current_id].startswith(
            "t1_"
        ):
            parent_id = parent_lookup[current_id]
            current_id = parent_id[3:]
            if current_id in comment_vectors:
                similarity = cosine_similarity(
                    comment_vectors[comment_id], comment_vectors[current_id]
                )[0, 0]
                similarities.append(similarity)

        if similarities:
            return sum(similarities) / len(similarities)
        else:
            return 0

    comments_df_copy["similarity"] = 0.0

    for post_title, group in tqdm(
        comments_df_copy.groupby("post_title"),
        desc="Processing parent child similarity",
    ):
        parent_lookup = dict(zip(group["id"], group["parent_id"]))
        comment_vectors = dict(zip(group["id"], group["vector"]))
        comments_df_copy.loc[group.index, "similarity"] = group["id"].apply(
            lambda x: calculate_average_similarity(x, parent_lookup, comment_vectors)
        )

    user_similarity = (
        comments_df_copy.groupby("username")["similarity"].mean().reset_index()
    )
    user_similarity.columns = ["username", "parent_child_similarity"]
    df = df.merge(user_similarity, on="username", how="left")
    print("Feature parent_child_similarity created successfully.")

    return df


def calculate_ttr(text):
    tokens = word_tokenize(text)
    num_tokens = len(tokens)
    num_types = len(set(tokens))
    if num_tokens == 0:
        return 0
    return num_types / num_tokens


def add_average_ttr(df, comments_df):
    comments_df["ttr"] = comments_df["cleaned_body"].apply(calculate_ttr)
    avg_ttr_per_user = (
        comments_df.groupby("username")["ttr"].mean().reset_index(name="avg_ttr")
    )
    df = df.merge(avg_ttr_per_user, on="username", how="left")
    print("Feature avg_ttr created successfully.")

    return df


def calculate_flesch_kincaid_grade(text):
    return textstat.flesch_kincaid_grade(text)


def add_average_flesch_kincaid_grade(df, comments_df):
    comments_df["flesch_kincaid_grade"] = comments_df["cleaned_body"].apply(
        calculate_flesch_kincaid_grade
    )
    avg_grade_per_user = (
        comments_df.groupby("username")["flesch_kincaid_grade"]
        .mean()
        .reset_index(name="avg_flesch_kincaid_grade")
    )
    df = df.merge(avg_grade_per_user, on="username", how="left")
    print("Feature avg_flesch_kincaid_grade created successfully.")

    return df


def get_ngrams(text, n=2):
    vectorizer = CountVectorizer(ngram_range=(n, n))
    analyzer = vectorizer.build_analyzer()
    return set(analyzer(text))


def calculate_overlap(comments, n=2):
    if len(comments) < 2:
        return 0.0

    all_ngrams = [get_ngrams(comment, n) for comment in comments]
    overlap_count = 0
    total_count = 0

    for i in range(len(all_ngrams)):
        for j in range(i + 1, len(all_ngrams)):
            overlap_count += len(all_ngrams[i].intersection(all_ngrams[j]))
            total_count += len(all_ngrams[i].union(all_ngrams[j]))

    if total_count == 0:
        return 0.0

    return overlap_count / total_count


def add_ngram_overlap(df, comments_df, n=2):
    grouped_comments = comments_df.groupby("username")["cleaned_body"].apply(list)

    overlap_ratios = {}

    for username, comments in tqdm(
        grouped_comments.items(),
        desc="Calculating n-gram overlap",
        total=len(grouped_comments),
    ):
        overlap_ratios[username] = calculate_overlap(comments, n)

    overlap_df = pd.DataFrame(
        list(overlap_ratios.items()), columns=["username", "ngram_overlap"]
    )

    df = df.merge(overlap_df, on="username", how="left")
    print(f"Feature ngram_overlap created successfully.")

    return df

def average_score(df, comments_df):
    comments_df['score'] = comments_df['score'].fillna(0)
    avg_score_per_user = comments_df.groupby('username')['score'].mean().reset_index(name='avg_score')
    df = df.merge(avg_score_per_user, on='username', how='left')
    
    return df

def average_num_replies(df, comments_df):
    comments_df['num_replies'] = comments_df['num_replies'].fillna(0)
    avg_num_replies_per_user = comments_df.groupby('username')['num_replies'].mean().reset_index(name='avg_num_replies')
    df = df.merge(avg_num_replies_per_user, on='username', how='left')
    
    return df

def average_stickied(df, comments_df):
    comments_df['stickied'] = comments_df['stickied'].fillna(False)
    avg_stickied_per_user = comments_df.groupby('username')['stickied'].mean().reset_index(name='avg_stickied')
    df = df.merge(avg_stickied_per_user, on='username', how='left')

# Label functions
def count_slashes_and_emojis(comments_df):
    comments_df = comments_df.copy()

    def count_special_chars(text):
        backslashes = text.count("/")
        forwardslashes = text.count("/")
        emojis = len([char for char in text if emoji.is_emoji(char)])
        return backslashes + forwardslashes, emojis

    comments_df[["slashes", "emojis"]] = comments_df["body"].apply(
        lambda x: pd.Series(count_special_chars(x))
    )
    comments_df["slashes_emojis"] = comments_df["slashes"] + comments_df["emojis"]

    return comments_df


def get_bot_usernames_from_comments(comments_df):
    com = count_slashes_and_emojis(comments_df)
    user_averages = (
        com.groupby("username")
        .agg({"emojis": "mean", "slashes": "mean", "slashes_emojis": "mean"})
        .rename(
            columns={
                "emojis": "avg_emojis",
                "slashes": "avg_slashes",
                "slashes_emojis": "avg_slashes_emojis",
            }
        )
    )

    filtered_users = user_averages[
        (user_averages["avg_slashes"] > 6)
        | (user_averages["avg_emojis"] > 5)
        | (user_averages["avg_slashes_emojis"] > 8)
    ]

    users_with_high_slashes = com[com["slashes"] > 10]["username"].unique()
    users_with_high_emojis = com[com["emojis"] > 10]["username"].unique()
    users_with_high_slashes_emojis = com[com["slashes_emojis"] > 15][
        "username"
    ].unique()
    unique_usernames = (
        set(filtered_users.index)
        | set(users_with_high_slashes)
        | set(users_with_high_emojis)
        | set(users_with_high_slashes_emojis)
    )

    return list(unique_usernames)


def autolabel_bots(posts_df, comments_df, users_df):
    df_combined = pd.concat(
        [
            posts_df[
                ["username", "subreddit", "title", "text", "score", "upvote_ratio"]
            ],
            comments_df[["username", "subreddit", "body", "score"]],
        ]
    )

    user_activity = (
        df_combined.groupby("username")
        .agg(
            {
                "title": "count",
                "text": "count",
                "body": "count",
                "score": "mean",
                "upvote_ratio": "mean",
            }
        )
        .rename(
            columns={
                "title": "num_posts",
                "text": "num_texts",
                "body": "num_comments",
                "score": "avg_score",
                "upvote_ratio": "avg_upvote_ratio",
            }
        )
        .fillna(0)
    )

    df_users = pd.merge(users_df, user_activity, on="username", how="left").fillna(0)

    bot_usernames = [
        "bot",
        "auto",
        "mod",
        "helper",
        "AI",
        "assist",
        "news",
        "alert",
        "info",
    ]
    username_pattern = re.compile(
        r"\b(" + "|".join(bot_usernames) + r")\b", re.IGNORECASE
    )
    username_with_digits_pattern = re.compile(
        r"[a-zA-Z]+[0-9]{5,}$"
    )  # e.g., "user123456"

    def is_bot(row):
        validaion_count = 0
        validation_threshold = 3

        # Username patterns
        if username_pattern.search(
            row["username"]
        ) or username_with_digits_pattern.search(row["username"]):
            return True

        # Account age with high activity
        if row["account_age"] < 60 and row["num_posts"] + row["num_comments"] > 100:
            validaion_count += 1

        # Low karma
        if row["link_karma"] < -30 or row["comment_karma"] < -30:
            validaion_count += 1
            if validaion_count > validation_threshold:
                return True

        # Frequent low scores indicating low engagement
        if row["avg_score"] < 0.5 and row["num_posts"] + row["num_comments"] > 10:
            validaion_count += 1
            if validaion_count > validation_threshold:
                return True

        # Consistent upvote ratios (either too low or too high)
        if (row["avg_upvote_ratio"] < 0.05 or row["avg_upvote_ratio"] > 0.96) and row[
            "avg_upvote_ratio"
        ] != 0:
            validaion_count += 1
            if validaion_count > validation_threshold:
                return True

        # High comment-to-post ratio
        if row["link_karma"] > 10 * row["comment_karma"]:
            validaion_count += 1
            if validaion_count > validation_threshold:
                return True

        return False

    df_users["is_bot"] = df_users.apply(is_bot, axis=1)

    return df_users[["username", "is_bot"]]


def mark_bots(posts_df, comments_df, users_df):
    print("Labeling bots...")
    unique_usernames = get_bot_usernames_from_comments(comments_df)
    labeled_users = autolabel_bots(posts_df, comments_df, users_df)

    labeled_users.loc[labeled_users["username"].isin(unique_usernames), "is_bot"] = True
    print("Bots labeled successfully.\n")

    return labeled_users


# Main pipeline function
def create_features_pipeline(posts_df, comments_df, users_df):
    print("Creating features...")
    comments_df = add_tfidf_vectors(comments_df)
    features_df = users_df.copy()

    features_df = add_avg_cosine_similarity(features_df, comments_df)
    features_df = add_all_users_similarity(features_df, comments_df)
    features_df = add_comment_length_metrics(features_df, comments_df)
    features_df = add_comment_post_ratio(features_df, comments_df, posts_df)
    features_df = add_average_thread_depth(features_df, comments_df)
    features_df = add_parent_child_similarity(features_df, comments_df)
    features_df = add_average_ttr(features_df, comments_df)
    features_df = add_average_flesch_kincaid_grade(features_df, comments_df)
    features_df = add_ngram_overlap(features_df, comments_df)
    # features_df = average_score(features_df, comments_df)
    # features_df = average_num_replies(features_df, comments_df)
    # features_df = average_stickied(features_df, comments_df)
    print("All features created successfully.\n")

    # Fill NaN values with None
    features_df = features_df.where(pd.notnull(features_df), None)

    return features_df


# Save data
def save_data(df, file_path):
    df.to_csv(file_path, index=False)
    print(f"Data saved to {file_path} successfully.\n")


# Main function
def main(
    comments_file_path, posts_file_path, users_file_path, x_file_path, y_file_path
):
    start = datetime.now()
    posts_df, comments_df, users_df = load_data(
        posts_file_path, comments_file_path, users_file_path
    )
    x_df = create_features_pipeline(posts_df, comments_df, users_df)
    y_df = mark_bots(posts_df, comments_df, users_df)

    save_data(x_df, x_file_path)
    save_data(y_df, y_file_path)
    print("Data preprocessing completed successfully.")
    print("Time elapsed:", datetime.now() - start)


if __name__ == "__main__":
    main(comments_file_path, posts_file_path, users_file_path, x_file_path, y_file_path)
