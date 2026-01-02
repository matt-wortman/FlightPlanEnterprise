import datetime as dt

from FpConfig import sqlDatabaseConnect
from FpDatabase import SqlDatabase


class Attachment():
    def __init__(self, attachmentID, locationStepID, locationRiskID, entryDatetime, description, storageKey, fileName, attachmentType, contentType, thumbnail, username, activityDate = dt.datetime.now().replace(microsecond=0)):
        self.attachmentID = attachmentID
        self.locationStepID = locationStepID
        self.locationRiskID = locationRiskID
        self.entryDatetime = entryDatetime
        self.description = description
        self.storageKey = storageKey
        self.fileName = fileName
        self.attachmentType = attachmentType
        self.contentType = contentType
        self.thumbnail =  thumbnail
        self.username = username
        self.activityDate = activityDate

    def editAttachment(self, locationStepID = '', locationRiskID = '', entryDatetime = '', description = '', storageKey = '', fileName = '', attachmentType = '', contentType = '', thumbnail = '', username = ''):
        self.locationStepID = locationStepID if locationStepID != '' else self.locationStepID
        self.locationRiskId = locationRiskID if locationRiskID != '' else self.locationRiskID
        self.entryDatetime = entryDatetime if entryDatetime != '' else self.entryDatetime
        self.description = description if description != '' else self.description
        self.storageKey = storageKey if storageKey != '' else self.storageKey
        self.fileName = fileName if fileName != '' else self.fileName
        self.attachmentType = attachmentType if attachmentType != '' else self.attachmentType
        self.contentType = contentType if contentType != '' else self.contentType
        self.thumbnail =  thumbnail if thumbnail != '' else self.thumbnail
        self.username =  username if username != '' else self.username
        self.activityDate = dt.datetime.now().replace(microsecond=0)
        self.updateDatabaseEntry()

    def removeAttachment(self):
        # remove attachment from DB
        with SqlDatabase(sqlDatabaseConnect) as db:
            sql = 'delete from attachments '
            sql += ' where AttachmentID = \'{}\''.format(self.attachmentID)

            db.sendSqlNoReturn(sql)
        
        return self.attachmentID

    def updateDatabaseEntry(self):
        ### Add things here to update the report in the database
        return