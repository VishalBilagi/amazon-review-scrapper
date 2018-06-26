#Review Scrapper for products on amazon.in site

#Libs for opening url and parsing html data
import math
import http
import sys
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

def getReviewData_mThreading(pagePairs,pdt,dfa,pTitle):
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
		#'a-section-cell-widget' class contains the review body
		#There are total of ten reviews per page
		HC_REVIEW_BODIES = soup.find_all(class_=re.compile("a-section celwidget"))
		#'a-row a-expander-container a-expander-inline-container' class contains body of helpful votes a review received
		HC_REVIEW_VOTES = soup.find_all(class_ = re.compile("a-row a-expander-container a-expander-inline-container"))
		#print(str(len(HC_REVIEW_BODIES)) + " "+str(len(HC_REVIEW_VOTES)))
		HC_REVIEW_DATES = soup.find_all("span",{"data-hook":"review-date"})

		# Navigating HC_REVIEW_BODIES to find:
		# 1) 0-2-0 Review Title
		# 2) 0-0-0-0 Review Rating
		# 3) 3-0-0 Review Text
		# 4) Review ID

		for HC_REVIEW_CONTENT, HC_VOTES_COUNT, HC_DATE_TEXT in zip(HC_REVIEW_BODIES, HC_REVIEW_VOTES, HC_REVIEW_DATES):
			RE_PID = re.compile(r'\/[A-Z0-9]{10}\/')
			RE_REVIEW_TEXT = re.compile(r', <br\/>,|\[|\]')
			RE_VOTES = re.compile(r'(people|person) found this helpful')
			if(debug):
				print("Product ID: "+ RE_PID.search(product).group().replace('/',''))
				print("Product Title: " + HC_PRODUCT_TITLE)
				print("Ratings: " + str(HC_REVIEW_CONTENT.contents[0].contents[0].contents[0].contents[0].contents[0]))
				print("Review Title: " + str(HC_REVIEW_CONTENT.contents[0].contents[2].contents[0]))
				print("Review Text: " + RE_REVIEW_TEXT.sub('',str(HC_REVIEW_CONTENT.contents[3].contents[0].contents)))
				if(len(HC_VOTES_COUNT.contents[0].contents[1].contents[0])!=1):
					print("Votes: 0")
				else:
					votes = str(HC_VOTES_COUNT.contents[0].contents[1].contents[0].contents[0])
					votes = RE_VOTES.sub('',str(HC_VOTES_COUNT.contents[0].contents[1].contents[0].contents[0]))
					votes = votes.replace('One','1')
					print("Helpful Votes: "+votes)
				print("Review ID: " + str(HC_REVIEW_CONTENT.get('id')).replace('customer_review-',''))
				print("Review Date:" + str(parse(HC_DATE_TEXT.text.replace('on ','')).strftime("%d/%m/%Y")))
				print("")
			cols = ('Product-ID', 'Product-Title', 'Date-First-Available' ,'Ratings', 'Review-Title', 'Review-Text', 'Helpful-Votes', 'Review-ID', 'Review-Date')
			lst=[]
			pid = RE_PID.search(product).group().replace('/','')
			pdtTitle = HC_PRODUCT_TITLE
			ratings = str(HC_REVIEW_CONTENT.contents[0].contents[0].contents[0].contents[0].contents[0])
			ratings = ratings[0]
			title = str(HC_REVIEW_CONTENT.contents[0].contents[2].contents[0])
			text = RE_REVIEW_TEXT.sub('',str(HC_REVIEW_CONTENT.contents[3].contents[0].contents))
			if(len(HC_VOTES_COUNT.contents[0].contents[1].contents[0])!=1):
					votes = 0
			else:
					votes = str(HC_VOTES_COUNT.contents[0].contents[1].contents[0].contents[0])
					votes = RE_VOTES.sub('',str(HC_VOTES_COUNT.contents[0].contents[1].contents[0].contents[0]))
					votes = votes.replace('One','1')
			rid = str(HC_REVIEW_CONTENT.get('id')).replace('customer_review-','')
			rDate = str(parse(HC_DATE_TEXT.text.replace('on ','')).strftime("%d/%m/%Y"))
			lst.append([pid,pdtTitle,dateFirstAvaliable,ratings,title,text,votes,rid,rDate])
			df = pd.DataFrame(lst, columns = cols)
			global lock
			lock.acquire()
			global mainDataFrame
			mainDataFrame = pd.concat([mainDataFrame,df], ignore_index=True)
			df_list.append(df)
			lock.release()
		start +=1
	
def getReviewData(p):
	"""Collects review data of any product from amazon.in site and stores it as a CSV locally and uplaods a backup to Google Drive"""
	reviewPage = ""
	RE_PRODUCT_URL = re.compile(r'(\/gp\/product\/)|\/dp\/')
	reviewPage = RE_PRODUCT_URL.sub('/product-reviews/',p)
	RE_REVIEW_PAGE_NUMBER = re.search(r'product-reviews/.{11}',reviewPage)
	reviewPage = reviewPage.replace(reviewPage[RE_REVIEW_PAGE_NUMBER.end():],'?pageNumber=1')
	
	#print(reviewPage)
	soup = openAndParse(False,p)
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
	partial_fn = partial(getReviewData_mThreading, pdt=reviewPage, dfa = dateFirstAvaliable,pTitle=HC_PRODUCT_TITLE)
	#df_set will hold a list of Data Frames computed from getReviewData_mThreading
	pool.map(partial_fn, pagePairs)
	
	global mainDataFrame
	print("Collected "+ str(len(mainDataFrame))+" reviews")
	
	#get pid value to save the Data Frame as <pid>.csv
	RE_PID = re.compile(r'\/[A-Z0-9]{10}\/')
	pid = RE_PID.search(reviewPage).group().replace('/','')
	mainDataFrame.to_csv(pid +".csv", index=False)
	
	#clear data frame for next set of reviews
	mainDataFrame = mainDataFrame.iloc[0:0]
	#save csv to google drive
	fileID = sendCSV(pid)
	return fileID
