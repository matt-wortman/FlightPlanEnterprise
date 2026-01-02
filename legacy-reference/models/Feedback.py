import datetime as dt
import json

from FpCodes import *
from FpConfig import sqlDatabaseConnect
from FpDatabase import SqlDatabase


class Feedback():
    def __init__(self, feedbackID, entryDatetime, exitDatetime, score, performance, outcome, attachmentKeys, notes, graphVisible, suggestedEdit, username, activityDate = dt.datetime.now().replace(microsecond=0)):
        self.feedbackID = feedbackID
        self.entryDatetime = entryDatetime
        self.exitDatetime = exitDatetime
        self.score = score
        self.performance = performance
        self.outcome = outcome
        self.attachmentKeys = attachmentKeys
        self.notes = notes
        self.graphVisible = graphVisible
        self.suggestedEdit = suggestedEdit
        self.username = username
        self.activityDate = activityDate

    def editFeedback(self, entryDatetime = '', exitDatetime = '', score = '', performance = '', outcome = '', attachmentKeys = '', notes = '', graphVisible = '', suggestedEdit = '', username = ''):
        self.entryDatetime = entryDatetime if entryDatetime != '' else self.entryDatetime
        self.exitDatetime = exitDatetime if exitDatetime != '' else self.exitDatetime
        self.score = score if score != '' else self.score
        self.performance = performance if performance != '' else self.performance
        self.outcome = outcome if outcome != '' else self.outcome
        self.attachmentKeys = attachmentKeys if attachmentKeys  != '' else self.attachmentKeys
        self.notes = notes if notes != '' else self.notes
        self.graphVisible = graphVisible if graphVisible != '' else self.graphVisible
        self.suggestedEdit = suggestedEdit if suggestedEdit != '' else self.suggestedEdit
        self.username =  username if username != '' else self.username
        self.activityDate = dt.datetime.now().replace(microsecond=0)
        self.updateDatabaseEntry()

    def updateDatabaseEntry(self):
        ### Update the feedback in the database
        # Using parameters for user input fields for now. Probably should replace it all eventually
        with SqlDatabase(sqlDatabaseConnect) as db:
            params = []
            sql = 'update feedbacks set ' 
            sql += 'EntryDatetime = \'{}\', '.format(self.entryDatetime)
            if self.exitDatetime:
                sql += 'ExitDatetime = \'{}\', '.format(self.exitDatetime)
            sql += 'Score = \'{}\', '.format(self.score)
            sql += 'Performance = \'{}\', '.format(self.performance)
            sql += 'Outcome = \'{}\', '.format(self.outcome)
            sql += 'AttachmentKeys = \'{}\', '.format(self.attachmentKeys)

            sql += 'Notes = ?, '
            params.append(self.notes)

            sql += 'GraphVisible = \'{}\', '.format(self.graphVisible)

            sql += 'SuggestedEdit = ?, '
            params.append(self.suggestedEdit)

            sql += 'Username = \'{}\', '.format(self.username)
            sql += 'ActivityDate = \'{}\' '.format(self.activityDate)
            sql += ' where FeedbackID = {}'.format(self.feedbackID)

            db.sendSqlNoReturn(sql, params)

        return self
    
    def removeAttachment(self, storageKey):
        with SqlDatabase(sqlDatabaseConnect) as db:
            try:
                parsed = json.loads(self.attachmentKeys)
                del parsed[storageKey]
                parsed = json.dumps(parsed)
                self.attachmentKeys = parsed

                sql = 'update feedbacks set '
                sql += ' AttachmentKeys = \'{}\' '.format(parsed)
                sql += ' where FeedbackID = \'{}\''.format(self.feedbackID)

                db.sendSqlNoReturn(sql)
            except:
                print('Couldn\'t clean up {} from feedbacks'.format(storageKey))

    def toDict(self):
        return {'dbId': self.feedbackID, 'dbType': 'feedback', 'feedbackID': self.feedbackID, 'entryDatetime': self.entryDatetime, 'exitDatetime': self.exitDatetime, 'score': self.score, 'performance': self.performance, 'outcome': self.outcome, 'attachmentKeys': self.attachmentKeys, 'notes': self.notes, 'graphVisible': self.graphVisible, 'suggestedEdit': self.suggestedEdit, 'username': self.username, 'activityDate': self.activityDate}