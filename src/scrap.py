#Review Scrapper for products on amazon.in site

#Libs for opening url and parsing html data
import urllib.request,urllib.error
from bs4 import BeautifulSoup
from dateparser import parse
import sys
import http
from .googledrive import sendCSV
#For RegEX operations
import re

import math
from multiprocessing.dummy import Pool as EpicPool
from functools import partial

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
				page = urllib.request.urlopen(req).read()
				success = True
				#print("opened")
			except urllib.error.URLError as e: 
				print(e.reason)
				success = False
			#Wait some time before making another request
			except http.client.IncompleteRead as e: 
				print('partial load')
				success = False
			#sleep(2)
	if(success):
		#Parse review page
		return BeautifulSoup(page, 'html5lib')
		#print("parsed")
	else:
		return -1

def getReviewData_mThreading(linksList,pdt,dfa):
	df_list = []
	product = pdt
	dateFirstAvaliable = dfa
	start = linksList[0]

	while start <= linksList[1]:
		matchPageNum = re.search(r'pageNumber=', product)
		startPdt = product[:matchPageNum.end()] + str(start)

		soup = openAndParse(False,startPdt)
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
			df_list.append(df)
		start +=1
	return df_list
	


def getReviewData(p):
	product = ""
	productURLPattern = re.compile(r'(\/gp\/product\/)|\/dp\/')
	product = productURLPattern.sub('/product-reviews/',p)
	matchProduct = re.search(r'product-reviews/.{11}',product)
	product = product.replace(product[matchProduct.end():],'?pageNumber=1')
	
	#print(product)
	success = False
	soup = openAndParse(success,p)
	### TO DO : 
	# Inlcude Sales Rank 
	# scrap appropriately for different types of products
	### TO DO
	#salesRank = soup.find(id="SalesRank")
	#print( re.compile(r'[\n()]').sub('', str(salesRank.contents[1].contents[0])))
	
	try:
		dateFirstAvaliable = parse(str(soup.find(class_="date-first-available").contents[1].contents[0])).strftime("%d/%m/%Y")
	except: 
		try: 
			#print("This is a book")
			dateFirstAvaliable = soup.find('b', text="Publisher:").next_sibling
			dateFirstAvaliable = re.compile(r'[0-9]{1,2} [a-zA-Z]{1,10} [0-9]{1,4}').findall(str(dateFirstAvaliable))
			dateFirstAvaliable = parse(dateFirstAvaliable[0]).strftime("%d/%m/%Y")
			#print(dateFirstAvaliable)
		except: dateFirstAvaliable = "NA"

	
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
		reviewCount = '1'
	success = False
	reviewCount = int(reviewCount.replace(',',''))
	#print(reviewCount)
	
	#Load review pages as ranges in startList and endList arrays
	#A range value (start in startList, end in endList) is taken to load reviews between page number [start] to page number [end]
	#Total review pages (reviewCount) is divided by 10 to get 10 equal (except maybe the last set) range sets
	startList = []
	endList = []
	x = math.ceil(reviewCount/10)
	startNUM = 1
	endNUM = x
	totalNUM = 0
	multiplier = 2
	#iterate and load startNUM and endNUM into startList and endList respectively - for (start, end) pairs
	while(totalNUM<reviewCount):
		startList.append(startNUM)
		endList.append(endNUM)
		totalNUM += x
		startNUM = endNUM + 1
		#check if the page number doesn't exceed actual page numbers avaliable (reviewCount)
		if multiplier*x < reviewCount:
			endNUM = multiplier*x
			multiplier += 1
		else:
			break
	
	#coumpute remainder pages start,end pair
	lastNUM = reviewCount - endNUM
	startNUM = endNUM+1
	endNUM = startNUM + lastNUM - 1
	startList.append(startNUM)
	endList.append(endNUM)
	
	#generate range pairs [start,end]
	linksList = []
	for s,e in zip(startList,endList):
		linksList.append([s,e])
	
	#setup multi threading
	pool = EpicPool(10)
	#load constant paramenters to be passed to getReviewData_mThreading
	partial_fn = partial(getReviewData_mThreading, pdt=product, dfa = dateFirstAvaliable)
	#df_set will hold a list of Data Frames computed from getReviewData_mThreading
	df_set = pool.map(partial_fn, linksList)
	
	#extract Data Frames from df_list and append to df1 (main) Data Frame
	for eachDf in df_set:
		for x in eachDf:
			global df1
			df1 = pd.concat([df1,x], ignore_index=True)

	#get pid value to save the Data Frame as <pid>.csv
	pidPattern = re.compile(r'\/[A-Z0-9]{10}\/')
	pid = pidPattern.search(product).group().replace('/','')
	df1.to_csv(pid +".csv", index=False)
	sendCSV(pid)
