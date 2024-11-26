# Is There a Human on the Other Side?

## Project Description

The project aims to analyze and identify posts (both comments and submissions) on the Reddit platform to determine whether they were created by bots or humans. With the growing number of technologically advanced bots, distinguishing between human activity and bots is becoming an increasing challenge.

## Main Objectives

1. **Analyzing differences between bots and humans:**
   - Assessing linguistic style, user activity, and interactions.
   - Determining whether bot characteristics can be automatically detected using classifiers.

2. **Activity classification:**
   - Utilizing methods such as **Random Forest**, **CatBoost**, **OneClassSVM** and **LocalOutlierFactor** to identify patterns specific to bots.

3. **Feature Engineering**
   - Based on a literature review and an analysis of the characteristics of Reddit platform users, we created 16 key features to describe bot publications. These features can be divided into four groups:
      - Activity
      - Language style and interactions
      - Linguistic complexity
      - Engagement

4. **Comparison of distributions:**
    - Using distribution comparison methods **Jensen-Shannon divergence** and **Wasserstein distance** to detect significant differences in patterns between bots and humans.
    - Visualisation of the multidimensional class space in two- and three-dimensional graphs using various dimensionality reduction techniques (**UMAP**, **PCA** and **TSNE**)

5. **Understanding future threats:**
   - Analyzing potential consequences of bot activities, including information manipulation and social impacts.

## Data Sources

The data was collected from five of the most popular subreddits on Reddit using the Reddit API.

**Data scope:**

- **Comments**: 800,000
- **Posts**: 4,500
- **Users**: 380,000 (including 10,000 identified bots)

**Data categorization:**

- Explicit bots (marked as bots by Reddit).
- Accounts not identified as bots (potential humans).

You can find our dataset in zip file in the `data` folder.

## Results

- **Identification Challenges:** Even with advanced machine learning techniques, it's difficult to definitively distinguish bots from humans.
- **Behavioral Similarities:** Bots are increasingly mimicking human behavior in terms of linguistic style and activity patterns.
- **Impact on Discussions:** The presence of bots can negatively impact the quality of discussions by spreading misinformation and manipulating information.

## Conclusions

**A concerning future for social media**:

- Bots are becoming increasingly advanced, making it harder to differentiate them from humans.
- This is due to the use of large language models (LLMs) trained on human-generated text.
- LLMs enable bots to mimic human language patterns and writing styles very effectively.
- Bots may be used for information manipulation, posing a threat to digital security and public trust.
- Their ability to mimic human language and activity is growing, making bot activities increasingly difficult to detect.

## Authors

This project was conducted as part of the **Social Media Analysis** course in the Artificial Intelligence major in 2024.

- Dawid Kopeć
- Dawid Krutul
- Maciej Wizerkaniuk
