# All the dependencies 
import pandas as pd 
import textblob
import matplotlib.pyplot as plt
import seaborn as sns
import string
from nltk.corpus import stopwords
from collections import Counter
from textblob import TextBlob
import nltk
import numpy as np
from wordcloud import WordCloud

# Cloud  needs a restructure(redudancy,efficency), this iteration was to start with the Analysis work 

# Create a Data Frame from the CSV
dff = pd.read_csv('/Users/virajdattkohir/Downloads/Amazon_Dataset/amazonReviews.csv')

# Use text blob to get sentiments,polarity (should improve on this)
dff['polarity'] = dff.apply(lambda x: TextBlob(x['Review-Text']).sentiment.polarity, axis=1)


# Visulatization of the no of reviews grouped by Stars
dff['text_length'] = dff['Review-Text'].apply(len)
g = sns.FacetGrid(data=dff, col = "Ratings")
g.map(plt.hist,'text_length',bins=30)
plt.show()

# Ratings Box Plot
dff['Ratings'].plot.hist(bins=20)
plt.show()

# Using the polaruty to assess the comments sentiment(+ve or -ve)
print("The number of positive comments are ",len(dff[dff["polarity"]>0.15]))
print("The number of negative comments are",len(dff[dff["polarity"]<0.15]))
meanPolarity = dff['polarity'].mean()
if meanPolarity > 0.15:
    print("Positive Product")
else:
    print("Negative Product")


# Intantiate a set of stop words( stop words, includes words like is, a, an, the)
stopwords = nltk.corpus.stopwords.words('english')
RE_stopwords = r'\b(?:{})\b'.format('|'.join(stopwords))
# Print the stop words
print("\n The Stop Words are as follows:")
print(RE_stopwords)
# remove the stop words 
words = (dff["Review-Text"].str.lower().replace([r'\|', RE_stopwords], [' ', ''], regex=True).str.cat(sep=' ').split())
# Remove the puntications
words = [''.join(c for c in s if c not in string.punctuation) for s in words]
col = ["coll"]
# Create a data frame from the words in Review-Text(excluding stop words and punctuations)
pdd = pd.DataFrame(words,columns=col)
# This is to remove the space charecters, induced when we replace the stop words with ''.
# First we fill the space characters('') with nan and then drop those rows
pdd['coll'].replace('', np.nan, inplace=True)
pdd.dropna(subset=['coll'], inplace = True)



#Counter counts the number of words along with its frequency. We use most_common method to include the top 20 
#words used across all the reviews for the product
rslt = pd.DataFrame(Counter(pdd["coll"]).most_common(20),columns=['Word', 'Frequency']).set_index('Word')
rslt.plot.bar(rot=0, figsize=(16,10), width=0.8)
plt.show()


print("The least occuring words are :")
for word, count in Counter(words).most_common()[-20:]:
    print ('%s %s' % (word, count))


#Building the word cloud for MOST used WORDS
print("The MOST used WORDS:")
wordcloud = WordCloud(width = 1000, height = 500).generate(' '.join(pdd['coll']))
plt.figure(figsize=(15,8))
plt.imshow(wordcloud)
plt.axis("off")
plt.show()


# Create a Data frame for the least used words
least_used = Counter(pdd["coll"]).most_common()[-50:] # Returns the least used words (50 in this case)
cols = ['Word', 'Frequency']
least_pd = pd.DataFrame(least_used,columns=cols)


# Build the word cloud for the least used words
print("The LEAST used WORDS :")
leastwordcloud = WordCloud(width = 1000, height = 500).generate(' '.join(least_pd['Word']))
plt.figure(figsize=(15,8))
plt.imshow(leastwordcloud)
plt.axis("off")
plt.show()

