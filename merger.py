import pandas as pd
import os

files = os.listdir('amc-v2')


# pd.concat([pd.read_csv('amc/' + f) for f in files if f.startswith('user_data')], ignore_index=True).to_csv('amc-v2/user_data-todayilearned.csv', index=False)


pd.concat([pd.read_csv('amc-v2/' + f) for f in files if f.startswith('user_data')], ignore_index=True).to_csv('data/user_data-merged.csv', index=False)
pd.concat([pd.read_csv('amc-v2/' + f) for f in files if f.startswith('all_comments')], ignore_index=True).to_csv('data/all_comments-merged.csv', index=False)
pd.concat([pd.read_csv('amc-v2/' + f) for f in files if f.startswith('all_posts')], ignore_index=True).to_csv('data/all_posts-merged.csv', index=False)

print([pd.read_csv('amc-v2/' + f).shape for f in files if f.startswith('user_data')], pd.read_csv('data/user_data-merged.csv').shape)
print([pd.read_csv('amc-v2/' + f).shape for f in files if f.startswith('all_comments')], pd.read_csv('data/all_comments-merged.csv').shape)
print([pd.read_csv('amc-v2/' + f).shape for f in files if f.startswith('all_posts')], pd.read_csv('data/all_posts-merged.csv').shape)

