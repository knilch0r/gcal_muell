from __future__ import print_function
import pickle
import os.path
import sys
from datetime import tzinfo, timedelta, datetime
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/calendar.events']


creds = None
# The file token.pickle stores the user's access and refresh tokens, and is
# created automatically when the authorization flow completes for the first
# time.
if os.path.exists('token.pickle'):
    with open('token.pickle', 'rb') as token:
        creds = pickle.load(token)
# If there are no (valid) credentials available, let the user log in.
if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    else:
        flow = InstalledAppFlow.from_client_secrets_file(
            'credentials.json', SCOPES)
        creds = flow.run_local_server(port=0)
    # Save the credentials for the next run
    with open('token.pickle', 'wb') as token:
        pickle.dump(creds, token)

service = build('calendar', 'v3', credentials=creds)

# Call the Calendar API
now = datetime.utcnow().isoformat() + 'Z' # 'Z' indicates UTC time
print('Getting upcoming events')
events_result = service.events().list(calendarId='primary', timeMin=now,
                                      maxResults=250, singleEvents=False,
                                     ).execute()
events = events_result.get('items', [])

if not events:
    print('No upcoming events found.')
    sys.exit(1)

for event in events:
    if ( ( ('Biotonne' in event['summary']) or ('Papiertonne' in event['summary']) )
         and (event['start'].get('dateTime') is None)
       ):
        print('found:', event['start']['date'], event['summary'])
        if not (event['reminders'].get('overrides') is None):
            print('...fixing reminders')
            del event['reminders']['overrides']
            service.events().update(calendarId='primary', eventId=event['id'], body=event).execute()
        print('...creating tonneraus')
        tr = {}
        if 'Biotonne' in event['summary']:
            tr['summary'] = 'Tonne raus: R/B'
        else:
            tr['summary'] = 'Tonne raus: P/G'
        ds = datetime.fromisoformat(event['start']['date']) - timedelta(hours=7)
        de = ds + timedelta(minutes=15)
        tr['start'] = { 'dateTime': ds.isoformat(), 'timeZone': 'Europe/Berlin' }
        tr['end'] = { 'dateTime': de.isoformat(), 'timeZone': 'Europe/Berlin' }
        service.events().insert(calendarId='primary', body=tr).execute()
    else:
        start = event['start'].get('dateTime', event['start'].get('date'))
        print('ignoring:', start, event['summary'])


