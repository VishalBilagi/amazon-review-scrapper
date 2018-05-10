#Review Scrapper for products on amazon.in site

#Libs for opening url and parsing html data
import urllib.request
from bs4 import BeautifulSoup

import sys

#For RegEX operations
import re

#Everybody needs sleep :P even pyhtons
from time import sleep

#To fetch address bar url text from chrome's current tab
import uiautomation as automation

#Listen to keyboard hits for capturing url when pause/break key is pressed
from pynput import keyboard

# def on_press(key):
#     try:
#         # print('alphanumeric key {0} pressed'.format(key.char))
#         ...
#     except AttributeError:
#         # print('special key {0} pressed'.format(key))
#         ...


# def on_release(key):
#     # print('{0} released'.format(key))
#     if key == keyboard.Key.esc:
#         # Stop listener
#         exit(0)
#     if key == keyboard.Key.pause:
#         getReviewData()


def getReviewData():
	product = ""
	# sleep(3)
	# control = automation.GetFocusedControl()
	# controlList = []
	# while control:
	# 	controlList.insert(0, control)
	# 	control = control.GetParentControl()
	# if len(controlList) == 1:
	# 	control = controlList[0]
	# else:
	# 	control = controlList[1]
    # #Look for chrome's current tab's address bar
	# address_control = automation.FindControl(control, lambda c, d: isinstance(
	#     c, automation.EditControl) and "Address and search bar" in c.Name)

	#Load product's review url into product
	product = sys.argv[1].replace('/dp/','/product-reviews/')# = address_control.CurrentValue().replace('/dp/', '/product-reviews/')
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
		print("Ratings: " +
		      str(reviewContent.contents[0].contents[0].contents[0].contents[0].contents[0]))
		print("Review Title: " +
		      str(reviewContent.contents[0].contents[2].contents[0]))
		pattern = re.compile(r', <br\/>,|\[|\]')
		print("Review Text: " + pattern.sub('',
		      str(reviewContent.contents[3].contents[0].contents)))
		votePattern = re.compile(r'\n|[ a-zA-Z.]')
		re.compile(r'One person found this helpful').sub('1', str(reviewVoteCount.get_text()))
		print("Helpful Votes: " + votePattern.sub('',str(reviewVoteCount.get_text())))
		print("Review ID: " +str(reviewContent.get('id')).replace('customer_review-',''))
		print("")
getReviewData()



# with keyboard.Listener(
#         on_press=on_press,
#         on_release=on_release) as listener:
#     listener.join()
