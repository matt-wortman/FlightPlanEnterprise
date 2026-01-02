import datetime as dt

from FpCodes import *
from FpConfig import sqlDatabaseConnect
from FpDatabase import SqlDatabase


class LocationRisk():
    def __init__(self, locationStepID, locationRiskID, startDatetime, risk, notes, extra, username, activityDate = dt.datetime.now().replace(microsecond=0)):
        self.locationStepID = locationStepID
        self.locationRiskID = locationRiskID
        self.startDatetime = startDatetime
        self.risk = risk
        self.notes = notes
        self.extra = extra
        self.username = username
        self.activityDate = activityDate

    def editLocationRisk(self, locationStepID = '', startDatetime = '', risk = '', notes = '', extra = '', username = ''):
        self.locationStepID = locationStepID if locationStepID and locationStepID  != '' else self.locationStepID
        self.startDatetime = startDatetime if startDatetime and startDatetime != '' else self.startDatetime
        self.risk = risk if risk and risk != '' else self.risk
        self.notes = notes if notes and notes != '' else self.notes
        self.extra = extra if extra and extra != '' else self.extra
        self.username =  username if username and username != '' else self.username
        self.activityDate = dt.datetime.now().replace(microsecond=0)
        self.updateDatabaseEntry()

    def updateDatabaseEntry(self):
        ### Update the location risk in the database
        with SqlDatabase(sqlDatabaseConnect) as db:
            sql = 'update location_risks set ' 
            sql += 'LocationStepID = \'{}\', '.format(self.locationStepID)
            sql += 'StartDatetime = \'{}\', '.format(self.startDatetime)
            sql += 'Risk = \'{}\', '.format(self.risk)
            sql += 'Notes = \'{}\', '.format(self.notes)
            sql += 'Extra = \'{}\', '.format(self.extra)
            sql += 'Username = \'{}\', '.format(self.username)
            sql += 'ActivityDate = \'{}\' '.format(self.activityDate)
            sql += ' where LocationRiskID = {}'.format(self.locationRiskID)

            db.sendSqlNoReturn(sql)

        return self