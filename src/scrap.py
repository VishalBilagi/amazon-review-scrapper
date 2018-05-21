#Review Scrapper for products on amazon.in site

#Libs for opening url and parsing html data
import urllib.request,urllib.error
from bs4 import BeautifulSoup
from dateparser import parse
import sys

#For RegEX operations
import re

#Everybody needs sleep :P even pyhtons
from time import sleep

import pandas as pd

cols = ('Product-ID', 'Date-First-Available' ,'Ratings', 'Review-Title', 'Review-Text', 'Helpful-Votes', 'Review-ID', 'Review-Date')
df1 = pd.DataFrame(columns = cols)

debug = False
pageNum = 2
reviewCount = 1

def openAndParse(success,product):
	while success == False:
			try:
				#Open reviews site url
				req = urllib.request.Request(
					product, 
					data=None, 
					headers={
						'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.139 Safari/537.36'
					}
				)
				page = urllib.request.urlopen(req)
				success = True
				#print("opened")
			except urllib.error.URLError as e: print(e.reason)
			#Wait some time before making another request
			sleep(2)
	if(success):
		#Parse review page
		return BeautifulSoup(page, 'html5lib')
		#print("parsed")
	else:
		return -1

def getReviewData():
	product = ""
	productURLPattern = re.compile(r'(\/gp\/product\/)|\/dp\/')
	product = productURLPattern.sub('/product-reviews/',sys.argv[1])
	matchProduct = re.search(r'product-reviews/.{11}',product)
	product = product.replace(product[matchProduct.end():],'?pageNumber=1')
	
	#print(product)
	success = False
	soup = openAndParse(success,sys.argv[1])
	salesRank = soup.find("tr",{"id":"SalesRank"})
	print( re.compile(r'[\n()]').sub('', str(salesRank.contents[1].contents[0])))
	dateFirstAvaliable = parse(str(soup.find(class_="date-first-available").contents[1].contents[0])).strftime("%d/%m/%Y")
	# print(dateFirstAvaliable)
	success = False
	soup = openAndParse(success,product)

	reviewPageCount = soup.find("div",{"id":"cm_cr-pagination_bar"})
	if(reviewPageCount is not None):
		if(len(reviewPageCount.contents[0]) <8):
			reviewCount = reviewPageCount.contents[0].contents[len(reviewPageCount.contents[0])-2].contents[0].contents[0]
		else:
			reviewCount = reviewPageCount.contents[0].contents[6].contents[0].contents[0]
	else:
		reviewCount = 1
	#print(reviewCount)
	success = False
	for x in range(0,int(reviewCount)):
		print("Loading reviews "+str(x+1)+" of "+ str(reviewCount))

		soup = openAndParse(success,product)
		#'a-section-cell-widget' class contains the review body
		#There are total of ten reviews per page
		reviewBody = soup.find_all(class_=re.compile("a-section celwidget"))
		#'a-row a-expander-container a-expander-inline-container' class contains body of helpful votes a review received
		reviewVotes = soup.find_all(class_ = re.compile("a-row a-expander-container a-expander-inline-container"))
		#print(str(len(reviewBody)) + " "+str(len(reviewVotes)))
		reviewDate = soup.find_all("span",{"data-hook":"review-date"})

		# Navigating reviewBody to find:
		# 1) 0-2-0 Review Title
		# 2) 0-0-0-0 Review Rating
		# 3) 3-0-0 Review Text
		# 4) Review ID

		for reviewContent, reviewVoteCount, date in zip(reviewBody, reviewVotes, reviewDate):
			pidPattern = re.compile(r'\/[A-Z0-9]{10}\/')
			reviewPattern = re.compile(r', <br\/>,|\[|\]')
			votePattern = re.compile(r'(people|person) found this helpful')
			if(debug):
				print("Product ID: "+ pidPattern.search(product).group().replace('/',''))
				print("Ratings: " + str(reviewContent.contents[0].contents[0].contents[0].contents[0].contents[0]))
				print("Review Title: " + str(reviewContent.contents[0].contents[2].contents[0]))
				print("Review Text: " + reviewPattern.sub('',str(reviewContent.contents[3].contents[0].contents)))
				if(len(reviewVoteCount.contents[0].contents[1].contents[0])!=1):
					print("Votes: 0")
				else:
					votes = str(reviewVoteCount.contents[0].contents[1].contents[0].contents[0])
					votes = votePattern.sub('',str(reviewVoteCount.contents[0].contents[1].contents[0].contents[0]))
					votes = votes.replace('One','1')
					print("Helpful Votes: "+votes)
				print("Review ID: " + str(reviewContent.get('id')).replace('customer_review-',''))
				print("Review Date:" + str(parse(date.text.replace('on ','')).strftime("%d/%m/%Y")))
				print("")
			cols = ('Product-ID', 'Date-First-Available' ,'Ratings', 'Review-Title', 'Review-Text', 'Helpful-Votes', 'Review-ID', 'Review-Date')
			lst=[]
			pid = pidPattern.search(product).group().replace('/','')
			ratings = str(reviewContent.contents[0].contents[0].contents[0].contents[0].contents[0])
			ratings = ratings[0]
			title = str(reviewContent.contents[0].contents[2].contents[0])
			text = reviewPattern.sub('',str(reviewContent.contents[3].contents[0].contents))
			if(len(reviewVoteCount.contents[0].contents[1].contents[0])!=1):
					votes = 0
			else:
					votes = str(reviewVoteCount.contents[0].contents[1].contents[0].contents[0])
					votes = votePattern.sub('',str(reviewVoteCount.contents[0].contents[1].contents[0].contents[0]))
					votes = votes.replace('One','1')
			rid = str(reviewContent.get('id')).replace('customer_review-','')
			rDate = str(parse(date.text.replace('on ','')).strftime("%d/%m/%Y"))
			lst.append([pid,dateFirstAvaliable,ratings,title,text,votes,rid,rDate])
			df = pd.DataFrame(lst, columns = cols)
			global df1
			df1 = pd.concat([df1,df], ignore_index=True)
		global pageNum
		matchPageNum = re.search(r'pageNumber=', product)
		product = product[:matchPageNum.end()] + str(pageNum)
		pageNum = pageNum+1
		success = False
		
	df1.to_csv(pid+".csv", index=False)

getReviewData()