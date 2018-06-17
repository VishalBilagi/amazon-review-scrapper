from src.scrap import getReviewData
from apiclient.discovery import build
from apiclient.http import MediaFileUpload
from httplib2 import Http
from oauth2client import file, client, tools
from apiclient import errors
import json

SCOPES = 'https://www.googleapis.com/auth/drive'
store = file.Storage('./credentials.json')

creds = store.get()

if not creds or creds.invalid:
    flow = client.flow_from_clientsecrets('./client_secret.json', SCOPES)
    creds = tools.run_flow(flow, store)

service = build('drive','v3', http=creds.authorize(Http()))

def deleteTestFile(service, fid):
    try:
        body = service.files().delete(fileId=fid).execute()
    except errors.HttpError as error:
        print ('An error occurred: %s' % error)


with open('testlink.txt','r') as file:
    str = file.readlines()

for s in str:
    fid = getReviewData(s)
    assert(deleteTestFile(service, fid))
