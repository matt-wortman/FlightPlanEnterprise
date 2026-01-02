import datetime as dt
import json

from FpConfig import sqlDatabaseConnect
from FpDatabase import SqlDatabase



class Annotation():
    def __init__(self, annotationID, entryDatetime, annotation, type, href, specialNode, format, username, activityDate = dt.datetime.now().replace(microsecond=0)):
        self.annotationID = annotationID
        self.entryDatetime = entryDatetime
        self.annotation = annotation
        self.type = type
        self.href = href
        self.specialNode = specialNode
        self.format = format
        self.username = username
        self.activityDate = activityDate

    def editAnnotation(self, entryDatetime = '', annotation = '', type = '', href = '', specialNode = '', format = '', username = ''):
        self.entryDatetime = entryDatetime if entryDatetime != '' else self.entryDatetime
        self.annotation = annotation if annotation != '' else self.annotation
        self.type = type if type != '' else self.type
        self.href = href if href != '' else self.href
        self.specialNode = specialNode if specialNode != '' else self.specialNode
        self.format = format if format != '' else self.format
        self.username = username if username != '' else self.username
        self.activityDate = dt.datetime.now().replace(microsecond=0)
        return self.updateDatabaseEntry()

    def updateDatabaseEntry(self):
        ### Add things here to update the annotation in the database
        # Using parameters for user input fields for now. Probably should replace it all eventually
        with SqlDatabase(sqlDatabaseConnect) as db:
            params = []
            sql = 'update annotations set ' 
            sql += 'EntryDatetime = \'{}\', '.format(self.entryDatetime)

            sql += 'annotation = ?, '
            params.append(self.annotation)

            sql += 'type = \'{}\', '.format(self.type)
            sql += 'href = \'{}\', '.format(self.href)
            sql += 'specialNode = \'{}\', '.format(self.specialNode)
            sql += 'format = \'{}\', '.format(self.format)
            sql += 'Username = \'{}\', '.format(self.username)
            sql += 'ActivityDate = \'{}\' '.format(self.activityDate)
            sql += ' where AnnotaionID = {}'.format(self.annotationID)

            db.sendSqlNoReturn(sql, params)

        return self
    
    def removeAttachment(self, storageKey):
        with SqlDatabase(sqlDatabaseConnect) as db:
            try:
                parsed = json.loads(self.href)
                del parsed[storageKey]
                parsed = json.dumps(parsed)
                self.href = parsed

                sql = 'update annotations set '
                sql += ' href = \'{}\' '.format(parsed)
                sql += ' where AnnotaionID = \'{}\''.format(self.annotationID)

                db.sendSqlNoReturn(sql)
            except:
                print('Couldn\'t clean up {} from annotations'.format(storageKey))