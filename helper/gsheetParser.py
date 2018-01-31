from __future__ import print_function
import httplib2
import os
import http.client as sghttpclient
from time import sleep
from apiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage
from google.oauth2 import service_account


def get_credentials():
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
    SERVICE_ACCOUNT_FILE = '/app/helper/service.json'
    credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    return credentials


def addUser(name, email):

    credentials = get_credentials()
    discoveryUrl = ('https://sheets.googleapis.com/$discovery/rest?'
                    'version=v4')
    service = discovery.build('sheets', 'v4', credentials=credentials,
                              discoveryServiceUrl=discoveryUrl)

    ###### GET THE LATEST ROW ######
    service = discovery.build('sheets', 'v4', credentials=credentials)

    # The ID of the spreadsheet to retrieve data from.
    spreadsheet_id = os.getenv('SPREADSHEET_URL')

    # The A1 notation of the values to retrieve.
    range_ = 'Codes!D:D'

    request = service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id, range=range_)
    response = request.execute()

    ##### Check for duplicate entries ######
    email = email.lower()
    emailList = [email]
    if emailList in response['values']:
        print("Duplicate email, exiting")
        return

    nextRow = len(response['values']) + 1

    ###### UPDATE THE ROW ######
    values = [
        [
            "TRUE", name, email
        ],
    ]

    body = {
        'values': values
    }

    range_name = 'Codes!B' + str(nextRow) + ":" + str(nextRow)
    value_input_option = 'RAW'
    result = service.spreadsheets().values().update(
        spreadsheetId=spreadsheet_id, range=range_name,
        valueInputOption=value_input_option, body=body).execute()
    print('{0} cells updated.'.format(result.get('updatedCells')))
    sleep(1)

    ###### GET THE CODE ######
    range_2 = 'Codes!A:A'
    request2 = service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id, range=range_2)
    response2 = request2.execute()
    sleep(1)

    passID = ""
    try:
        passID = response2['values'][nextRow - 1][0]
    except IndexError:
        print("We're out of passes!")

    ###### SEND THE EMAIL ######

    conn = sghttpclient.HTTPSConnection("api.sendgrid.com")

    useremail = email
    username = name

    adminEmail = os.getenv('ADMINEMAIL')
    adminName = os.getenv('ADMINNAME')
    successTemplate = os.getenv('SUCCESSTEMPLATE')
    if passID != "":
        payload = "{\"personalizations\":[{\"to\":[{\"email\":\"" + useremail + "\",\"name\":\"" + username + "\"}],\"subject\":\"Your Azure Pass\",\"substitutions\":{\"%pass%\":\"" + passID + \
            "\"}}],\"from\":{\"email\":\"" + adminEmail + "\",\"name\":\"" + adminName + "\"},\"reply_to\":{\"email\":\"" + adminEmail + \
            "\",\"name\":\"" + adminName + \
            "\"},\"subject\":\"Your Azure Pass!\",\"template_id\":\"" + successTemplate + "\"}"
    else:
        payload = "{\"personalizations\":[{\"to\":[{\"email\":\"" + useremail + "\",\"name\":\"" + username + "\"}],\"subject\":\"Your Azure Pass\",\"substitutions\":{\"%pass%\":\"" + passID + \
            "\"}}],\"from\":{\"email\":\"distributrapp@distributr.io\",\"name\":\"Microsoft at Berkeley\"},\"reply_to\":{\"email\":\"distributrapp@distributr.io\",\"name\":\"Microsoft at Berkeley\"},\"subject\":\"Your Azure Pass!\",\"template_id\":\"e02b052a-d8d2-49f7-af34-3be7a30caede\"}"

    bearer = "Bearer " + os.getenv('SENDGRID_API_KEY')
    headers = {
        'authorization': bearer,
        'content-type': "application/json"
    }

    conn.request("POST", "/v3/mail/send", payload, headers)

    res = conn.getresponse()
    data = res.read()

    print(data.decode("utf-8") + "Email sent")
