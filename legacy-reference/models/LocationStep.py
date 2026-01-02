import datetime as dt
import json
import re

from FpCodes import *
from FpConfig import sqlDatabaseConnect
from FpDatabase import SqlDatabase
from utils.FP2_Utilities import makeJsonRecord


class LocationStep():
    def __init__(self, locationStepID, entryDatetime, location, teams, weight, notes, extra, username, activityDate = dt.datetime.now().replace(microsecond=0), risks = []):
        self.locationStepID = locationStepID
        self.entryDatetime = entryDatetime
        self.location = location
        self.teams = teams
        self.weight = self.convertWeight(weight)
        self.notes = notes
        self.extra = extra
        self.username = username
        self.activityDate = activityDate

        self.risks = risks

    def editLocationStep(self, entryDatetime = '', location = '', teams = '', weight = '', notes = '', extra = '', username = ''):
        self.entryDatetime = entryDatetime if entryDatetime and entryDatetime  != '' else self.entryDatetime
        self.location = location if location and location != '' else self.location
        self.teams = teams if teams and teams != '' else self.teams
        self.weight = self.convertWeight(weight) if weight and weight != '' else self.weight
        self.notes = notes if notes and notes != '' else self.notes
        self.extra = extra if extra and extra != '' else self.extra
        self.username =  username if username and username != '' else self.username
        self.activityDate = dt.datetime.now().replace(microsecond=0)
        self.updateDatabaseEntry()

    def updateDatabaseEntry(self):
        ### update the location step in the database
        # Using params for user input values. Should be updated for all of them in the future
        with SqlDatabase(sqlDatabaseConnect) as db:
            params = []

            sql = 'update location_steps set ' 
            sql += 'EntryDatetime = \'{}\', '.format(self.entryDatetime)
            sql += 'Location = \'{}\', '.format(self.location)
            sql += 'Teams = \'{}\', '.format(self.teams)
            
            sql += 'Weight = ?, '
            params.append(str(self.weight))

            sql += 'Notes = ?, '
            params.append(self.notes)

            sql += 'Extra = ?, '
            params.append(makeJsonRecord(self.extra))

            sql += 'Username = \'{}\', '.format(self.username)
            sql += 'ActivityDate = \'{}\' '.format(self.activityDate)
            sql += ' where LocationStepID = {}'.format(self.locationStepID)
            db.sendSqlNoReturn(sql, params)

        return self

    def convertWeight(self, weight):
        #match up to 2 decimal places of precision
        match = re.match("(^\d+(\.\d{0,2})?)|(^\.\d{0,2})", str(weight))
        if match:
            return match.group(0)
        return None

    def getSurgeons(self):
        team = json.loads(self.teams)
        if isinstance(team, str):
            team = json.loads(team)
        surgeons = team['surgeon']
        return [surgeon['name'] for surgeon in surgeons]

    def getTeams(self):
        try:
            team = json.loads(self.teams)
            if isinstance(team, str):
                team = json.loads(team)
        except:
            team = self.teams
        
        return team

    def getNotes(self):
        try:
            notes = json.loads(self.notes)
            if isinstance(notes, str):
                notes = json.loads(notes)
        except:
            notes = self.notes
            
        return notes

    def getExtra(self):
        try:
            extra = json.loads(self.extra)
            if isinstance(extra, str):
                extra = json.loads(extra)
        except:
            extra = self.extra
            
        return extra
