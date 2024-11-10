from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler, FunctionTransformer
from sklearn.impute import SimpleImputer


# Custom transformer to drop columns
def drop_columns(X, columns):
    return X.drop(columns, axis=1)


# Custom transformer to replace None with specific values
def replace_none(X, column_value_pairs):
    for column, value in column_value_pairs.items():
        X[column] = X[column].fillna(value)
    return X


# Custom transformer to convert is_bot to binary
def convert_is_bot(X):
    X["is_bot"] = X["is_bot"].apply(lambda x: 1 if x else 0)
    return X


# Define the columns to be processed
columns_to_drop = ["username"]
columns_to_standardize_after_replace = [
    "avg_comment_length",
    "max_comment_length",
    "min_comment_length",
    "avg_flesch_kincaid_grade",
]
columns_to_standardize_before_replace = [
    "link_karma",
    "comment_karma",
    "account_age",
    "is_verified",
]
columns_to_replace_none = {
    "avg_cosine_similarity": 0,
    "all_users_similarity": 0,
    "comment_post_ratio": 1,
    "avg_thread_depth": 0,
    "avg_ttr": 0,
    "ngram_overlap": 0,
}

# Create the preprocessing pipeline
preprocessing_pipeline = Pipeline(
    steps=[
        (
            "drop_columns",
            FunctionTransformer(drop_columns, kw_args={"columns": columns_to_drop}),
        ),
        (
            "replace_none",
            FunctionTransformer(
                replace_none, kw_args={"column_value_pairs": columns_to_replace_none}
            ),
        ),
        (
            "standardize",
            ColumnTransformer(
                transformers=[
                    (
                        "std_after_replace",
                        Pipeline(
                            steps=[
                                (
                                    "replace_none",
                                    SimpleImputer(strategy="constant", fill_value=0),
                                ),
                                ("std", StandardScaler()),
                            ]
                        ),
                        columns_to_standardize_after_replace,
                    ),
                    (
                        "std_before_replace",
                        Pipeline(
                            steps=[
                                ("std", StandardScaler()),
                                (
                                    "replace_none",
                                    SimpleImputer(strategy="constant", fill_value=1),
                                ),
                            ]
                        ),
                        columns_to_standardize_before_replace,
                    ),
                ],
                remainder="passthrough",
            ),
        ),
        ("convert_is_bot", FunctionTransformer(convert_is_bot)),
    ]
)
