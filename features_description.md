# Features for Bot Identification on Reddit

## Features description

*All of the embeddings were done using TfidfVectorize*

1. **Link Karma**  
   Total score from link posts. Bots may post excessive promotional content, resulting in unusually high or low scores.  
   *Calculation*: From User profile.

2. **Comment Karma**  
   Total score from comments. Low values may indicate low-quality, automatically generated content.  
   *Calculation*: From User profile.

3. **Account Age**  
   Time since the account's creation. Younger accounts are more likely to belong to bots.  
   *Calculation*: Days between account creation and data extraction.

4. **Avg. Cosine Similarity**  
   Average cosine similarity of the user's comments. High similarity indicates repetitive content.  
   *Calculation*:  Calculates the average cosine similarity between all pairs of comments embeddings made by a user. If the user has only one comment a *None* value is assigned.

6. **All Users Similarity**  
   Average similarity of a user’s comments to other users'. High values may indicate mimicry of human patterns.  
   *Calculation*: Computes the average cosine similarity between a user's comments embedding and a random sample of 5000 comments embeddings from all users. This measures how similar a user's comments are to the general population.

7. **Avg. Comment Length**  
   Average length of a user's comments. Bots often produce very short or excessively long comments.  
   *Calculation*: Total character count of all comments divided by the number of comments.

8. **Max Comment Length**  
   Extremes in comment length may suggest automated content generation.  
   *Calculation*: Maximum character counts in the user's comments.

9. **Min Comment Length**  
   Extremes in comment length may suggest automated content generation.  
   *Calculation*: Minimum character counts in the user's comments.

10. **Comment/Post Ratio**  
   Ratio of comments to posts. Bots often favor one type of activity over the other.  
   *Calculation*: Total number of comments divided by the total number of posts.

11. **Avg. Thread Depth**  
   Average depth of threads in which the user participates. Bots engage less often in deep discussions.  
   *Calculation*: Measures the average depth of a user's comments in the thread hierarchy, indicating how deep into the conversation the user typically comments.

12. **Parent-Child Similarity**  
   Similarity between a user's comments and their responses to other comments. High values can indicate mechanical repetition.  
   *Calculation*: Calculates the average cosine similarity between a user's comments embedding and their parent comments embeddings in the thread, indicating how similar a user's comments are to the preceding comments.

13. **Avg. TTR (Type-Token Ratio)**  
   Ratio of unique words to total words in comments. Low values suggest a limited vocabulary.  
   *Calculation*: Computes the average Type-Token Ratio (TTR) of a user's comments embedding, which is the ratio of unique words to the total number of words, indicating lexical diversity.

14. **Avg. Flesch-Kincaid Grade**  
   Average readability score of the user’s comments. Bots often generate simpler text structures.  
   *Calculation*: Calculates the average Flesch-Kincaid grade level of a user's comments, which measures the readability of the text.

15. **N-gram Overlap**  
   Repetition of linguistic patterns (e.g., bigrams). High overlap suggests low diversity.  
   *Calculation*: Measures the average overlap of bigrams (sequences of 2 words) between all pairs of a user's comments, indicating how repetitive the user's comments are.

16. **Avg. Score**  
   Average score received for comments and posts. Bots may have either unusually low or very high scores.  
   *Calculation*: Total score of all comments and posts divided by their count.

17. **Avg. Number of Replies**  
   Average number of responses to a user's comments. Bots tend to receive fewer replies.  
   *Calculation*: Total replies to the user’s comments divided by the number of comments.
