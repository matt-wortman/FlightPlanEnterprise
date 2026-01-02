import datetime as dt
import json

from FpCodes import *
from FpConfig import sqlDatabaseConnect
from FpDatabase import SqlDatabase


class Conference():
    def __init__(self, conferenceID, entryDatetime, type, attachmentKeys, actionItems, notes, username, activityDate = dt.datetime.now().replace(microsecond=0)):
        self.conferenceID = conferenceID
        self.entryDatetime = entryDatetime
        self.type = type
        self.attachmentKeys = attachmentKeys
        self.actionItems = actionItems
        self.notes = notes
        self.username = username
        self.activityDate = activityDate

    def editConference(self, entryDatetime = '', type = '', attachmentKeys = '', actionItems = '', notes = '', username = ''):
        self.entryDatetime = entryDatetime if entryDatetime != '' else self.entryDatetime
        self.type = type if type != '' else self.type
        self.attachmentKeys = attachmentKeys if attachmentKeys != '' else self.attachmentKeys
        self.actionItems = actionItems if actionItems != '' else self.actionItems
        self.notes = notes if notes != '' else self.notes
        self.username =  username if username != '' else self.username
        self.activityDate = dt.datetime.now().replace(microsecond=0)
        self.updateDatabaseEntry()

    def updateDatabaseEntry(self):
        ### Add things here to update the conference in the database
        # Using parameters for user input fields for now. Probably should replace it all eventually
        with SqlDatabase(sqlDatabaseConnect) as db:
            params = []
            sql = 'update conferences set ' 
            sql += 'EntryDatetime = \'{}\', '.format(self.entryDatetime)
            sql += 'Type = \'{}\', '.format(self.type)
            sql += 'AttachmentKeys = \'{}\', '.format(self.attachmentKeys)

            sql += 'ActionItems = ?, '
            params.append(self.actionItems)

            sql += 'Notes = ?, '
            params.append(self.notes)
            
            sql += 'Username = \'{}\', '.format(self.username)
            sql += 'ActivityDate = \'{}\' '.format(self.activityDate)
            sql += ' where ConferenceID = {}'.format(self.conferenceID)

            db.sendSqlNoReturn(sql, params)

        return self
    
    def removeAttachment(self, storageKey):
        with SqlDatabase(sqlDatabaseConnect) as db:
            try:
                parsed = json.loads(self.attachmentKeys)
                del parsed[storageKey]
                parsed = json.dumps(parsed)
                self.attachmentKeys = parsed

                sql = 'update conferences set '
                sql += ' AttachmentKeys = \'{}\' '.format(parsed)
                sql += ' where ConferenceID = \'{}\''.format(self.conferenceID)

                db.sendSqlNoReturn(sql)
            except:
                print('Couldn\'t clean up {} from conferences'.format(storageKey))

    def toDict(self):
        return {'dbId': self.conferenceID, 'dbType': 'conference', 'conferenceID': self.conferenceID, 'entryDatetime': self.entryDatetime, 'type': self.type, 'attachmentKeys': self.attachmentKeys, 'actionItems': self.actionItems, 'notes': self.notes, 'username': self.username, 'activityDate': self.activityDate}