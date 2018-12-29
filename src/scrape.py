#Review Scrapper for products on amazon.in site

import math
import http
import sys
import os
import re
import pandas as pd
from time import sleep
from dateparser import parse

from bs4 import BeautifulSoup
import urllib.request,urllib.error

from threading import Lock
from functools import partial
from multiprocessing.dummy import Pool as EpicPool

from .googledrive import sendCSV

cols = ('Product-ID', 'Product-Title', 'Date-First-Available' ,'Ratings', 'Review-Title', 'Review-Text', 'Helpful-Votes', 'Review-ID', 'Review-Date')
mainDataFrame = pd.DataFrame(columns = cols)

debug = False
numberOfReviewPages = 1
lock = Lock()

def openAndParse(success,product):
	""" openAndParse(success,product) function returns a parsed HTML soup object"""
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

def getReviewData_mThreading(pagePairs,pdt,dfa,pTitle,prid):
	"""Collects reviews in parallel and pushes them onto a mainDataFrame"""
	df_list = []
	product = pdt
	dateFirstAvaliable = dfa
	HC_PRODUCT_TITLE = pTitle
	start = pagePairs[0]

	while start <= pagePairs[1]:
		RE_PAGE_NUMBER = re.search(r'pageNumber=', product)
		review_page = product[:RE_PAGE_NUMBER.end()] + str(start)

		soup = openAndParse(False,review_page)
		"""
			# AMAZON-HTML-Content update: No longer need to traverse HC_REVIEW_BODIES to get Title, Rating and Review text
			# HC_REVIEW_BODIES -> Changed to HC_REVIEW_IDS to only look for Review ID

			#'a-section-cell-widget' class contains the review body
			#There are total of ten reviews per page
		"""
		HC_REVIEW_IDS = soup.find_all(class_=re.compile("a-section celwidget"))
		#'a-row a-expander-container a-expander-inline-container' class contains body of helpful votes a review received
		HC_REVIEW_VOTES = soup.find_all(class_ = re.compile("a-row a-expander-container a-expander-inline-container"))
		
		HC_REVIEW_DATES = soup.find_all("span",{"data-hook":"review-date"})

		HC_REIVEW_RATINGS = soup.find_all("i",{"data-hook":"review-star-rating"})

		HC_REVIEW_TITLES = soup.find_all("a",{"data-hook":"review-title"})

		HC_REVIEW_BODY = soup.find_all("span",{"data-hook":"review-body"})
		
		for HC_REVIEW_ID, HC_VOTES_COUNT, HC_DATE_TEXT,HC_RATING_TEXT, HC_REVIEW_TITLE, HC_REVIEW_BODY_TEXT in zip(HC_REVIEW_IDS, HC_REVIEW_VOTES, HC_REVIEW_DATES, HC_REIVEW_RATINGS,HC_REVIEW_TITLES,HC_REVIEW_BODY):
			RE_PID = re.compile(r'\/[A-Z0-9]{10}\/')
			RE_REVIEW_TEXT = re.compile(r', <br\/>,|\[|\]')
			RE_VOTES = re.compile(r'(people|person) found this helpful')
			if(debug):
				print("Product ID: "+ prid)
				print("Product Title: " + HC_PRODUCT_TITLE)
				print("Ratings: " + HC_RATING_TEXT.text)
				print("Review Title: " + HC_REVIEW_TITLE.text)
				print("Review Text: " + RE_REVIEW_TEXT.sub('',str(HC_REVIEW_BODY_TEXT.text)))
				if(len(HC_VOTES_COUNT.contents[0].contents[1].contents[0])!=1):
					print("Votes: 0")
				else:
					votes = str(HC_VOTES_COUNT.contents[0].contents[1].contents[0].contents[0])
					votes = RE_VOTES.sub('',str(HC_VOTES_COUNT.contents[0].contents[1].contents[0].contents[0]))
					votes = votes.replace('One','1')
					print("Helpful Votes: "+votes)
				print("Review ID: " + str(HC_REVIEW_ID.get('id')).replace('customer_review-',''))
				print("Review Date:" + str(parse(HC_DATE_TEXT.text.replace('on ','')).strftime("%d/%m/%Y")))
				print("")
			cols = ('Product-ID', 'Product-Title', 'Date-First-Available' ,'Ratings', 'Review-Title', 'Review-Text', 'Helpful-Votes', 'Review-ID', 'Review-Date')
			lst=[]
			pdtTitle = HC_PRODUCT_TITLE
			ratings = str(HC_RATING_TEXT.text)
			ratings = ratings[0]
			title = str(HC_REVIEW_TITLE.text)
			text = RE_REVIEW_TEXT.sub('',str(HC_REVIEW_BODY_TEXT.text))
			if(len(HC_VOTES_COUNT.contents[0].contents[1].contents[0])!=1):
					votes = 0
			else:
					votes = str(HC_VOTES_COUNT.contents[0].contents[1].contents[0].contents[0])
					votes = RE_VOTES.sub('',str(HC_VOTES_COUNT.contents[0].contents[1].contents[0].contents[0]))
					votes = votes.replace('One','1')
			rid = str(HC_REVIEW_ID.get('id')).replace('customer_review-','')
			rDate = str(parse(HC_DATE_TEXT.text.replace('on ','')).strftime("%d/%m/%Y"))
			lst.append([prid,pdtTitle,dateFirstAvaliable,ratings,title,text,votes,rid,rDate])
			df = pd.DataFrame(lst, columns = cols)
			global lock
			lock.acquire()
			global mainDataFrame
			mainDataFrame = pd.concat([mainDataFrame,df], ignore_index=True)
			df_list.append(df)
			lock.release()
		start +=1
	
def getReviewData(productURL):
	"""Collects review data of any product from amazon.in site and stores it as a CSV locally and uplaods a backup to Google Drive"""
	soup = openAndParse(False,productURL)
	#Look for parent ASIN for similar products that have same review data
	try:
		RE_MULTI_PRODUCT_PID = re.compile(r'\"parentAsin\":\"[A-Z-0-9]{10}\"')
		pid = soup.find_all('script',{'data-a-state':'{\"key\":\"page-refresh-data-mason\"}'})
		pid = RE_MULTI_PRODUCT_PID.search(pid[0].text)
		#Last 11 characters contain the ASIN
		pid = pid.group()[-11:-1]
	except:
		RE_PID = re.compile(r'\/[A-Z0-9]{10}(\/|\?)')
		pid = RE_PID.search(productURL).group()[-11:-1]

	if os.path.isfile(str(pid)+'.csv'):
		print("Reviews for this product already collected.")
		return
	
	reviewPage = ""
	RE_PRODUCT_URL = re.compile(r'(\/gp\/product\/)|\/dp\/')
	reviewPage = RE_PRODUCT_URL.sub('/product-reviews/',productURL)
	RE_REVIEW_PAGE_NUMBER = re.search(r'product-reviews/.{10}',reviewPage)
	reviewPage = reviewPage.replace(reviewPage[RE_REVIEW_PAGE_NUMBER.end():],'/?pageNumber=1')
	
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
	
	HC_PRODUCT_TITLE = soup.find('span',{'id':'productTitle'}).text
	RE_PRODUCT_TITLE = re.compile(r'[^ a-zA-Z0-9,()/] *')
	HC_PRODUCT_TITLE = RE_PRODUCT_TITLE.sub('',HC_PRODUCT_TITLE)
	# print(dateFirstAvaliable)
	soup = openAndParse(False,reviewPage)

	HC_LAST_REVIEW_PAGE_NUM = soup.find("div",{"id":"cm_cr-pagination_bar"})
	if(HC_LAST_REVIEW_PAGE_NUM is not None):
		if(len(HC_LAST_REVIEW_PAGE_NUM.contents[0]) <8):
			numberOfReviewPages = HC_LAST_REVIEW_PAGE_NUM.contents[0].contents[len(HC_LAST_REVIEW_PAGE_NUM.contents[0])-2].contents[0].contents[0]
		else:
			numberOfReviewPages = HC_LAST_REVIEW_PAGE_NUM.contents[0].contents[6].contents[0].contents[0]
	else:
		numberOfReviewPages = '1'
	numberOfReviewPages = int(numberOfReviewPages.replace(',',''))
	#print(numberOfReviewPages)
	
	#Load review pages as ranges in startPages and endPages arrays
	#A range value (start in startPages, end in endPages) is taken to load reviews between page number [start] to page number [end]
	#Total review pages (numberOfReviewPages) is divided by 10 to get 10 equal (except maybe the last set) range sets
	startPages = []
	endPages = []
	x = math.ceil(numberOfReviewPages/10)
	startPage = 1
	endPage = x
	totalPages = 0
	multiplier = 2
	#iterate and load startPage and endPage into startPages and endPages respectively - for (start, end) pairs
	while(totalPages<numberOfReviewPages):
		startPages.append(startPage)
		endPages.append(endPage)
		totalPages += x
		startPage = endPage + 1
		#check if the page number doesn't exceed actual page numbers avaliable (numberOfReviewPages)
		if multiplier*x < numberOfReviewPages:
			endPage = multiplier*x
			multiplier += 1
		else:
			break
	
	#coumpute remainder pages start,end pair
	lastPage = numberOfReviewPages - endPage
	startPage = endPage + 1
	endPage = startPage + lastPage - 1
	startPages.append(startPage)
	endPages.append(endPage)
	
	#generate range pairs [start,end]
	pagePairs = []
	for s,e in zip(startPages,endPages):
		pagePairs.append([s,e])
	
	#setup multi threading
	pool = EpicPool(10)
	#load constant paramenters to be passed to getReviewData_mThreading
	partial_fn = partial(getReviewData_mThreading, pdt=reviewPage, dfa = dateFirstAvaliable,pTitle=HC_PRODUCT_TITLE,prid=pid)
	#df_set will hold a list of Data Frames computed from getReviewData_mThreading
	pool.map(partial_fn, pagePairs)
	
	global mainDataFrame
	print("Collected "+ str(len(mainDataFrame))+" reviews")
	
	#save the Data Frame as <pid>.csv
	mainDataFrame.to_csv(pid +".csv", index=False)
	
	#clear data frame for next set of reviews
	mainDataFrame = mainDataFrame.iloc[0:0]
	#save csv to google drive
	fileID = sendCSV(pid)
	return fileID
