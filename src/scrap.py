#Review Scrapper for products on amazon.in site

#Libs for opening url and parsing html data
import urllib.request
from bs4 import BeautifulSoup

import sys

#For RegEX operations
import re

#Everybody needs sleep :P even pyhtons
from time import sleep

import pandas as pd

cols = ('Product-ID', 'Ratings', 'Review-Title', 'Review-Text', 'Helpful-Votes', 'Review-ID')
df1 = pd.DataFrame(columns = cols)

debug = False

def getReviewData():
	product = ""
	
	product = sys.argv[1].replace('/dp/','/product-reviews/')
	print(product)

	#Open and parse the reviews site url
	page = urllib.request.urlopen(product)
	soup = BeautifulSoup(page, 'html5lib')

	#'a-section-cell-widget' class contains the review body
	#There are total of ten reviews per page
	reviewBody = soup.find_all(class_=re.compile("a-section celwidget"))
	#'cr-vote-text' class contains number of helpful votes a review received
	reviewVotes = soup.find_all(class_ = re.compile("cr-vote-text"))

	# Navigating reviewBody to find:
	# 1) 0-2-0 Review Title
	# 2) 0-0-0-0 Review Rating
	# 3) 3-0-0 Review Text
	# 4) Review ID

	for reviewContent, reviewVoteCount in zip(reviewBody, reviewVotes):
		pidPattern = re.compile(r'\/[A-Z0-9]{10}\/')
		reviewPattern = re.compile(r', <br\/>,|\[|\]')
		votePattern = re.compile(r'\n|[ a-zA-Z.]')
		if(debug):
			print("Product ID: "+ pidPattern.search(product).group().replace('/',''))
			print("Ratings: " + str(reviewContent.contents[0].contents[0].contents[0].contents[0].contents[0]))
			print("Review Title: " + str(reviewContent.contents[0].contents[2].contents[0]))
			print("Review Text: " + reviewPattern.sub('',str(reviewContent.contents[3].contents[0].contents)))
			re.compile(r'One person found this helpful').sub('1', str(reviewVoteCount.get_text()))
			print("Helpful Votes: " + votePattern.sub('',str(reviewVoteCount.get_text())))
			print("Review ID: " +str(reviewContent.get('id')).replace('customer_review-',''))
			print("")
		cols = ('Product-ID', 'Ratings', 'Review-Title', 'Review-Text', 'Helpful-Votes', 'Review-ID')
		lst=[]
		pid = pidPattern.search(product).group().replace('/','')
		ratings = str(reviewContent.contents[0].contents[0].contents[0].contents[0].contents[0])
		ratings = ratings[0]
		title = str(reviewContent.contents[0].contents[2].contents[0])
		text = reviewPattern.sub('',str(reviewContent.contents[3].contents[0].contents))
		re.compile(r'One person found this helpful').sub('1', str(reviewVoteCount.get_text()))
		votes = votePattern.sub('',str(reviewVoteCount.get_text()))
		rid = str(reviewContent.get('id')).replace('customer_review-','')
		lst.append([pid,ratings,title,text,votes,rid])
		df = pd.DataFrame(lst, columns = cols)
		global df1
		df1 = pd.concat([df1,df], ignore_index=True)
		df1.to_csv("amazonReviews.csv", index=False)

getReviewData()