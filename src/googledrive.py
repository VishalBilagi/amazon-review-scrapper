from __future__ import print_function
from apiclient.discovery import build
from apiclient.http import MediaFileUpload
from httplib2 import Http
from oauth2client import file, client, tools
import json

SCOPES = 'https://www.googleapis.com/auth/drive'
store = file.Storage('./src/credentials.json')

creds = store.get()

if not creds or creds.invalid:
    flow = client.flow_from_clientsecrets('./src/client_secret.json', SCOPES)
    creds = tools.run_flow(flow, store)

service = build('drive','v3', http=creds.authorize(Http()))


def sendCSV(pid):
    with open('config.json','r') as f:
        config= json.load(f)
    folderID = config['DRIVE_ACCESS']['FOLDER_ID']
    file_metadata = {
        'name': pid,
        'parents': [folderID],
        'mimeType': 'application/vnd.google-apps.spreadsheet'
    }


    media = MediaFileUpload('./'+pid+'.csv',
                        mimetype='text/csv',
                        resumable=True)
    file = service.files().create(body=file_metadata,
                                media_body=media,
                                fields='id').execute()

    print('File ID is'+ file.get('id'))