import base64
import datetime as dt
import json

from FpCodes import *
from FpConfig import sqlDatabaseConnect
from FpDatabase import SqlDatabase
from models.Annotation import Annotation
from models.Attachment import Attachment
from models.Conference import Conference
from models.CourseCorrection import CourseCorrection
from models.Feedback import Feedback
from models.LocationRisk import LocationRisk
from models.LocationStep import LocationStep
from models.TimelineStep import TimelineStep
from utils.common import getReportImage
from utils.FP2_AttachmentUtils import deleteBlob, writeBlob
from utils.FP2_Utilities import makeJsonRecord

class Admission():
    def __init__(self, MRN, admissionID, surgeryDate, reviewDate, crossCheck = False, status = '', thumbnail = '', diagnosis = '', interventions = '', username = '', activityDate = dt.datetime.now().replace(microsecond=0)):
        self.MRN = MRN
        self.admissionID = admissionID
        self.surgeryDate = surgeryDate if not isinstance(surgeryDate, str) else dt.datetime.strptime(surgeryDate, '%Y-%m-%d')
        self.reviewDate = reviewDate
        self.crossCheck = True if crossCheck == '1' or crossCheck == 'True' or crossCheck == True else False
        self.status = {
            "RiskStatus": "ACCU",
            "Location": "Pre-op",
            "Cardiologist": [
                ""
            ],
            "Surgeon": [
                ""
            ],
            "Anesthesia": [],
            "Attending": [],
            "Index": 1,
            "LOS": 0,
            "ReviewDate": "",
            "DischargeDate": "",
            "Procedures": 0,
            "ACCU": [],
            "CICU": [],
            "CATH": [],
            "SurgeryDate": dt.datetime.now().strftime('%Y-%m-%d %H:%M'),
            "Weight": ""
        } if status == '' else status
        self.thumbnail = thumbnail
        self.diagnosis = diagnosis if diagnosis != '' else {}
        self.interventions = interventions if interventions != '' else {}
        self.username = username
        self.activityDate = activityDate
        self.where = 'where MRN = \'{}\' AND ADM = {} Order By EntryDatetime asc'.format(self.MRN, self.admissionID)
        self.course_corrections = None
        self.annotations = None
        self.feedbacks = None
        self.conferences = None
        self.attachments = None
        self.location_steps = []
        self.timeline = []
        self.loadLocationStepsAndTimeline()
        self.loadCourseCorrections()
        self.loadAnnotations()
        self.loadFeedbacks()
        self.loadConferences()
        self.loadAttachments()

    def removePatient(self):
        try:
            for a in self.attachments:
                deleteBlob(a.storageKey)

            with SqlDatabase(sqlDatabaseConnect) as db:
                sql = 'delete from location_steps where MRN = \'{}\' AND ADM = {}'.format(self.MRN, self.admissionID)
                db.sendSqlNoReturn(sql)
                sql = 'delete from location_risks where MRN = \'{}\' AND ADM = {}'.format(self.MRN, self.admissionID)
                db.sendSqlNoReturn(sql)
                sql = 'delete from bedside_procedures where MRN = \'{}\' AND ADM = {}'.format(self.MRN, self.admissionID)
                db.sendSqlNoReturn(sql)
                sql = 'delete from attachments where MRN = \'{}\' AND ADM = {}'.format(self.MRN, self.admissionID)
                db.sendSqlNoReturn(sql)
                sql = 'delete from admissions where MRN = \'{}\' AND ADM = {}'.format(self.MRN, self.admissionID)
                db.sendSqlNoReturn(sql)
                sql = 'delete from annotations where MRN = \'{}\' AND ADM = {}'.format(self.MRN, self.admissionID)
                db.sendSqlNoReturn(sql)
                sql = 'delete from conferences where MRN = \'{}\' AND ADM = {}'.format(self.MRN, self.admissionID)
                db.sendSqlNoReturn(sql)
                sql = 'delete from continuous_therapy where MRN = \'{}\' AND ADM = {}'.format(self.MRN, self.admissionID)
                db.sendSqlNoReturn(sql)
                sql = 'delete from course_corrections where MRN = \'{}\' AND ADM = {}'.format(self.MRN, self.admissionID)
                db.sendSqlNoReturn(sql)
                sql = 'delete from feedbacks where MRN = \'{}\' AND ADM = {}'.format(self.MRN, self.admissionID)
                db.sendSqlNoReturn(sql)
                sql = 'delete from patients where MRN = \'{}\''.format(self.MRN)
                db.sendSqlNoReturn(sql)
        except:
            print('Error occurred cleaning up MRN: {}, ADM: {}'.format(self.MRN, self.admissionID))

    def editAdmissionInfo(self, surgeryDate = '', reviewDate = '', crossCheck = '', thumbnail = '', diagnosis = '', interventions = '', username = ''):
        self.surgeryDate = surgeryDate if surgeryDate != '' else self.surgeryDate
        self.reviewDate = reviewDate if reviewDate != '' else self.reviewDate
        self.crossCheck = crossCheck if crossCheck != '' else self.crossCheck
        self.thumbnail = thumbnail if thumbnail != '' else self.thumbnail
        self.diagnosis = diagnosis if diagnosis != '' else self.diagnosis
        self.interventions = interventions if interventions != '' else self.interventions
        self.username = username if username != '' else self.username
        self.activityDate = dt.datetime.now().replace(microsecond=0)

        return self.updateDatabaseEntry()

    def updateDatabaseEntry(self):
        ### update the admission in the database
        with SqlDatabase(sqlDatabaseConnect) as db:
            params = []
            sql = 'declare @_admission_dt datetime;'
            sql += 'declare @_review_dt datetime;'
            sql += 'declare @_activity_dt datetime;'
            sql += 'select @_admission_dt = CONVERT(DATETIME, \'{}\');'.format(self.surgeryDate)
            sql += 'select @_review_dt = CONVERT(DATETIME, \'{}\');'.format(self.reviewDate)
            sql += 'select @_activity_dt = CONVERT(DATETIME, \'{}\');'.format(self.activityDate)

            sql += 'update admissions set ' 
            sql += 'ADMDATE = @_admission_dt, '.format()

            sql += 'Status = ?, '
            params.append(json.dumps(self.status))

            sql += 'Interventions = ?, '
            params.append(json.dumps(self.interventions))

            sql += 'Diagnosis = ?, '
            params.append(json.dumps(self.diagnosis))

            sql += 'ReviewDate = @_review_dt, '
            sql += 'CrossCheck = \'{}\', '.format(self.crossCheck)
            sql += 'Thumbnail = \'{}\', '.format(self.thumbnail)
            sql += 'Username = \'{}\', '.format(self.username)
            sql += 'ActivityDate = @_activity_dt '
            sql += ' where MRN = \'{}\' AND ADM = {}'.format(self.MRN, 
                                                            self.admissionID)

            db.sendSqlNoReturn(sql, params)

        return self

    def loadCourseCorrections(self):
        with SqlDatabase(sqlDatabaseConnect) as db:
            dbCourseCorrections = db.select(course_correction_schema, self.where)   
            self.course_corrections = []
            for cc in dbCourseCorrections:
                self.course_corrections.append(CourseCorrection(cc['course_correct_id'], cc['EntryDatetime'], cc['detail'], cc['type'], cc['User'], cc['ActivityDate']))

    def loadConferences(self):
        with SqlDatabase(sqlDatabaseConnect) as db:
            dbConferences = db.select(conferences_schema, self.where)   
            self.conferences = []
            for conference in dbConferences:
                self.conferences.append(Conference(conference['ConferenceID'], conference['EntryDatetime'], conference['Type'], conference['AttachmentKeys'], conference['ActionItems'], conference['Notes'], conference['Username'], conference['ActivityDate']))
    def loadAttachments(self):
        with SqlDatabase(sqlDatabaseConnect) as db:
            dbAttachments = db.select(attachments_schema, self.where)
            self.attachments = []
            for attachment in dbAttachments:
                self.attachments.append(Attachment(attachment['AttachmentID'], attachment['LocationStepID'], attachment['LocationRiskID'], attachment['EntryDatetime'], attachment['Description'], attachment['storage_key'], attachment['Filename'], attachment['AttachmentType'], attachment['ContentType'], attachment['Thumbnail'], attachment['Username'], attachment['ActivityDate']))

    def loadAnnotations(self):
        with SqlDatabase(sqlDatabaseConnect) as db:
            dbAnnotations = db.select(annotation_schema, self.where)
            self.annotations = []
            for annotation in dbAnnotations:
                self.annotations.append(Annotation(annotation['AnnotaionID'], annotation['EntryDatetime'], annotation['annotation'],  annotation['type'], annotation['href'], annotation['SpecialNode'], annotation['format'], annotation['Username'], annotation['ActivityDate']))
    def loadFeedbacks(self):
        with SqlDatabase(sqlDatabaseConnect) as db:
            dbFeedbacks = db.select(feedbacks_schema, self.where)
            self.feedbacks = []
            for feedback in dbFeedbacks:
                self.feedbacks.append(Feedback(feedback['FeedbackID'], feedback['EntryDatetime'], feedback['ExitDatetime'], feedback['Score'], feedback['Performance'], feedback['Outcome'],  feedback['AttachmentKeys'], feedback['Notes'], feedback['GraphVisible'], feedback['SuggestedEdit'], feedback['Username'], feedback['ActivityDate']))

    def loadLocationStepsAndTimeline(self):
        with SqlDatabase(sqlDatabaseConnect) as db:
            # Combine location_steps, location_risks, and timeline data into a single query
            combined_query = """
                SELECT 
                    ls.LocationStepID AS ls_LocationStepID, ls.EntryDatetime AS ls_EntryDatetime, ls.Location AS ls_Location, 
                    ls.Teams AS ls_Teams, ls.Weight AS ls_Weight, ls.Notes AS ls_Notes, ls.Extra AS ls_Extra, 
                    ls.Username AS ls_Username, ls.ActivityDate AS ls_ActivityDate,
                    lr.LocationRiskID AS lr_LocationRiskID, lr.StartDatetime AS lr_StartDatetime, lr.Risk AS lr_Risk, 
                    lr.Notes AS lr_Notes, lr.Extra AS lr_Extra, lr.Username AS lr_Username, lr.ActivityDate AS lr_ActivityDate,
                    lr.Risk AS RiskStatus, lr.StartDatetime AS EntryDatetime, lr.Notes AS RiskNotes
                FROM location_steps ls
                LEFT JOIN location_risks lr ON ls.LocationStepID = lr.LocationStepID
                WHERE ls.MRN = '{}' AND ls.ADM = {}
                ORDER BY ls.EntryDatetime ASC, lr.StartDatetime ASC
            """.format(self.MRN, self.admissionID)
    
            dbResults = db.sendSql(combined_query)
            # Step 1: Group location steps and risks
            location_steps_dict = {}
            for result in dbResults:
                # Handle tuple-based results by using indices
                location_step_id = result[0]  # ls_LocationStepID
                if location_step_id not in location_steps_dict:
                    location_steps_dict[location_step_id] = {
                        'location_step': LocationStep(
                            location_step_id, result[1], result[2], result[3], 
                            result[4], result[5], result[6], result[7], 
                            result[8], risks=[]
                        ),
                        'risks': []
                    }
    
                if result[9]:  # Check if lr_LocationRiskID (index 9) is not None
                    location_steps_dict[location_step_id]['risks'].append(LocationRisk(
                        location_step_id, result[9], result[10], result[11], 
                        result[12], result[13], result[14], result[15]
                    ))
    
                # Step 2: Add timeline data
                if result[0]:  # Check if ls_LocationStepID (index 0) is present
                    self.timeline.append(TimelineStep(
                        result[0], result[2], result[16], 
                        result[17], result[4], result[5], result[18]
                    ))
    
            # Step 3: Create LocationStep objects and associate risks
            for location_step_id, data in location_steps_dict.items():
                location_step = data['location_step']
                location_step.risks = data['risks']
                self.location_steps.append(location_step)
    
            # Sort location steps and timeline
            self.location_steps = sorted(self.location_steps, key=lambda d: d.entryDatetime)
            self.timeline = sorted(self.timeline, key=lambda d: d.entryDatetime)
    
    # GETTER METHODS
    def getLastProcedureTime(self):
        lastProcedure = next((timelineEntry for timelineEntry in reversed(self.timeline) if timelineEntry.riskStatus == 'Procedure'), None)
        return lastProcedure.entryDatetime if lastProcedure != None else self.surgeryDate

    def getProcedures(self):
        return [step for step in self.timeline if step.riskStatus == 'Procedure']

    def getLastStepTime(self):
        lastEntry = self.timeline[-1] if len(self.timeline) != 0 else None
        return lastEntry.entryDatetime if lastEntry != None else self.surgeryDate

    def getMostRecentSurgeon(self):
        surgery = next((locationStep for locationStep in reversed(self.location_steps) if locationStep.location == 'CTOR'), None)
        return surgery.getSurgeons()[0] if surgery != None else ''

    def getAdmissionDateTime(self):
        return self.timeline[0].entryDatetime if len(self.timeline) > 0 else dt.datetime.now()

    def getDischargeEntry(self):
        return next((timelineEntry for timelineEntry in self.timeline if timelineEntry.riskStatus == 'Discharge'), None)

    def getDischargeTime(self):
        discharge_entry = self.getDischargeEntry()
        return discharge_entry.entryDatetime if discharge_entry != None else dt.datetime.max

    def getLengthOfStay(self):
        endDate = self.getDischargeTime()
        endDate = endDate if endDate != dt.datetime.max else dt.datetime.now()
        endDate = endDate.date()
        startDate = self.getAdmissionDateTime().date()
        return (endDate - startDate).days


    def getCurrentRiskStatus(self):
        if len(self.location_steps) == 0 or len(self.location_steps[-1].risks) == 0:
            return 'ACCU'

        risk = self.location_steps[-1].risks[-1].risk
        risk = risk.split()[0]
        risk = risk if risk != 'Discharge' else 'Discharged'

        return risk

    def getCurrentLocationStatus(self):
        if len(self.location_steps) == 0:
            return 'ACCU'

        location = self.location_steps[-1].location
        location =  'Discharged' if location == 'DC' else 'ACCU' if location == 'Pre-op' else location
        return location

    def getCourseCorrection(self, courseCorrectID):
        return next((course_correction for course_correction in self.course_corrections if course_correction.courseCorrectID == courseCorrectID), None)
    
    def getAttachment(self, attachmentID):
        return next((attachment for attachment in self.attachments if attachment.attachmentID == attachmentID), None)

    def getAttachments(self, storage_keys):
        # Use safe_json_loads for annotation href parsing elsewhere if needed
        return [attachment for attachment in self.attachments if attachment.storageKey in storage_keys]

    # Example usage elsewhere (if you filter annotations by storageKey):
    # annotations = list(filter(lambda x: storageKey in Admission.safe_json_loads(x.href), self.annotations))
    # ...existing code...
    def getAnnotation(self, annotationID):
        if self.annotations is None or annotationID is None:
            return None
        return next((annotation for annotation in self.annotations if getattr(annotation, 'annotationID', None) == annotationID), None)

    def getConference(self, conferenceID):
        return next((conference for conference in self.conferences if conference.conferenceID == conferenceID), None)

    def getFeedback(self, feedbackID):
        return next((feedback for feedback in self.feedbacks if feedback.feedbackID == feedbackID), None)

    def getLocationStep(self, locationStepID):
        return next((location_step for location_step in self.location_steps if location_step.locationStepID == locationStepID), None)

    def getLocationRisk(self, locationStepID, locationRiskID):
        locationStep = self.getLocationStep(locationStepID)
        return next((location_risk for location_risk in locationStep.risks if location_risk.locationRiskID == locationRiskID), None)

    def getSurgeons(self):
        surgeons = []
        for step in reversed(self.location_steps):
            teams = step.getTeams()

            if teams and step.location == 'CTOR':
                if 'surgeon' in teams:
                    for member in teams['surgeon']:
                        name = member['name']
                        if name != '' and not name in surgeons: 
                            surgeons.append(name)

        return surgeons

    def getAnesthesiologists(self):
        anesthesiologists = []
        for step in reversed(self.location_steps):
            teams = step.getTeams()
            
            if teams and step.location == 'CTOR' or step.location == 'Cath':
                if 'anesthesia' in teams:
                    for member in teams['anesthesia']:
                        name = member['name']
                        if name != '' and not name in anesthesiologists: 
                            anesthesiologists.append(name)

        return anesthesiologists

    def getCicuAttendings(self):
        cicu = []
        for step in reversed(self.location_steps):
            teams = step.getTeams()

            if teams and step.location == 'CICU':
                for area in teams.values():
                    for member in area:
                        name = member['name']
                        if member['name'] != '' and not name in cicu:
                            cicu.append(name)

        return cicu

    def getAccuAttendings(self):
        accu = []
        for step in reversed(self.location_steps):
            teams = step.getTeams()

            if teams and step.location == 'ACCU':
                for area in teams.values():
                    for member in area:
                        name = member['name']
                        if member['name'] != '' and not name in accu:
                            accu.append(name)

        return accu

    def getInterventionalists(self):
        interventions = []
        for step in reversed(self.location_steps):
            teams = step.getTeams()
            if teams and step.location == 'Cath':
                if 'intervention' in teams:
                    for member in teams['intervention']:
                        name = member['name']
                        if name != '' and not name in interventions:
                            interventions.append(name)
        return interventions

    def getCardiologists(self):
        if isinstance(self.status['Cardiologist'], list):
            return self.status['Cardiologist']
        else:
            return [self.status['Cardiologist']]

    def getTeamScores(self):
        return list(map(lambda feedback: feedback.score, self.feedbacks or []))

    def getOutcomes(self):
        return list(map(lambda feedback: feedback.outcome, self.feedbacks or []))

    def getAnnotationNotes(self):
        annotations = list(map(lambda annotation: annotation.annotation, self.annotations or []))
        annotations = [annotation for annotation in annotations if annotation is not None]
        return annotations

    def getWholeCareTeam(self):
        return self.getSurgeons() + self.getAccuAttendings() + self.getCicuAttendings() + self.getInterventionalists() + self.getAnesthesiologists() + self.getCardiologists()

    def getMostRecentSurgeon(self):
        surgery = next((locationStep for locationStep in reversed(self.location_steps) if locationStep.location == 'CTOR'), None)
        return surgery.getSurgeons()[0] if surgery != None else ''

    def getTimelineStep(self, locationStepID):
        return next((timelineStep for timelineStep in self.timeline if timelineStep.locationStepID == locationStepID), None)

    # BULK GETTER METHODS
    def getInterventions(self):
        return list(filter(lambda x: x.location == 'Cath' or x.location == 'CTOR', self.location_steps))


    def getFeedbacksDict(self):
        feedbacksDict = []
        for feedback in self.feedbacks:
            if feedback.graphVisible == 'Y':
                feedbacksDict.append(feedback.toDict())
        
        return feedbacksDict

    def getConferencesDict(self):
        conferencesDict = []
        for conference in self.conferences:
            conferencesDict.append(conference.toDict())
    
        return conferencesDict

    # SETTER METHODS
    def addCourseCorrection(self, entryDatetime, detail, type, username):
        self.course_corrections.append(CourseCorrection(entryDatetime, detail, type, username, 'Needs date'))
        ### Add things here to add course correction to DB
        raise NotImplemented

    def addConference(self, entryDatetime, type, attachmentKeys, actionItems, notes, username):
        conference = Conference('', entryDatetime, type, attachmentKeys, actionItems, notes, username)

        ### Add things here to add conference to DB
        with SqlDatabase(sqlDatabaseConnect) as db:
            params = []
            sql = 'declare @_entry_dt datetime;'
            sql += 'declare @_id int;'
            sql += 'declare @_activity_dt datetime;'
            sql += 'select @_entry_dt = CONVERT(DATETIME, \'{}\');'.format(conference.entryDatetime)
            sql += 'select @_activity_dt = CONVERT(DATETIME, \'{}\');'.format(conference.activityDate)

            sql += 'execute add_conference '
            sql += '@mrn = \'{}\', '.format(self.MRN)
            sql += '@adm = {}, '.format(self.admissionID)
            sql += '@entry_dt = @_entry_dt,'
            sql += '@type = \'{}\', '.format(conference.type) 
            if conference.attachmentKeys:
                sql += '@att_keys = \'{}\', '.format(conference.attachmentKeys) 
            else:
                sql += '@att_keys = NULL, '
            sql += '@action_items = ?, '
            params.append(conference.actionItems)
            if conference.notes:
                sql += '@notes = ?, '
                params.append(conference.notes)
            else:
                sql += '@notes = NULL, '
            sql += '@username = \'{}\', '.format(self.username)
            sql += '@activity_date = @_activity_dt, ' 
            sql += '@id = @_id OUTPUT;'
            sql += 'select @_id;'
            conference_id = db.sendSql(sql, params)[0][0]

            conference.conferenceID = conference_id
            self.conferences.append(conference)
        # Reload conferences from DB after mutation
        self.conferences = None
        self.loadConferences()
        return conference

    def addAttachment(self, entryDatetime, description, storageKey, fileName, attachmentType, contentType, contentData, username, locationStepID = 0, locationRiskID = 0):
        attachment = Attachment('', locationStepID, locationRiskID, entryDatetime, description, storageKey, fileName, attachmentType, contentType, '', username)

        ### add attachment to DB
        with SqlDatabase(sqlDatabaseConnect) as db:
            sql = 'declare @_entry_dt datetime;'
            sql += 'declare @_id int;'
            sql += 'declare @_activity_dt datetime;'
            sql += 'select @_entry_dt = CONVERT(DATETIME, \'{}\');'.format(entryDatetime.strftime('%Y-%m-%d %H:%M'))
            sql += 'select @_activity_dt = CONVERT(DATETIME, \'{}\');'.format(attachment.activityDate)

            sql += 'execute add_attachment '
            sql += '@mrn = \'{}\', '.format(self.MRN)
            sql += '@adm = {}, '.format(self.admissionID)
            sql += '@location_id = {}, '.format(attachment.locationStepID)
            sql += '@risk_id = \'{}\', '.format(attachment.locationRiskID) 
            sql += '@entry_dt = @_entry_dt,'
            sql += '@username = \'{}\', '.format(self.username)
            sql += '@activity_date = @_activity_dt, ' 
            sql += '@id = @_id OUTPUT;'
            sql += 'select @_id;'
            attachmment_id = db.sendSql(sql)[0][0]

            storageKey = '{}_{}_{}'.format(self.MRN, self.admissionID, attachmment_id)
            # A new attachment needs to be saved
            writeBlob(storageKey, contentData)

            try:
                type = contentType.split(';')[0].split('/')[-1]
            except:
                type = 'pdf'
            thumbnail = getReportImage(type, base64.b64decode(contentData), {'width': 200, 'max_pages': 1}).decode('utf-8')

            sql = 'update attachments set ' 
            sql += 'storage_key = \'{}\', '.format(storageKey)
            sql += 'Filename = \'{}\', '.format(fileName)
            sql += 'Description = \'{}\', '.format(description)
            sql += 'AttachmentType = \'{}\', '.format(attachmentType)
            sql += 'ContentType = \'{}\', '.format(contentType)
            sql += 'Thumbnail = \'{}\' '.format(thumbnail)
            sql += ' where MRN = \'{}\' AND ADM = {} AND AttachmentID = {}'.format(self.MRN, 
                                                                                self.admissionID, 
                                                                                attachmment_id)

            db.sendSqlNoReturn(sql)

            attachment.attachmentID = attachmment_id
            attachment.storageKey = storageKey
            attachment.thumbnail = thumbnail
            self.attachments.append(attachment)
        
        # Reload attachments from DB after mutation
        self.attachments = None
        self.loadAttachments()
        return attachment

    def addAnnotation(self, entryDatetime, annotation, type, href, specialNode, format, username):
        annotation = Annotation('', entryDatetime, annotation, type, href, specialNode, format, username)

        ### Add things here to add annotation to DB
        with SqlDatabase(sqlDatabaseConnect) as db:
            params = []
            sql = 'declare @_entry_dt datetime;'
            sql += 'declare @_id int;'
            sql += 'declare @_activity_dt datetime;'
            sql += 'select @_entry_dt = CONVERT(DATETIME, \'{}\');'.format(annotation.entryDatetime)
            sql += 'select @_activity_dt = CONVERT(DATETIME, \'{}\');'.format(annotation.activityDate)

            sql += 'execute add_annotation '
            sql += '@mrn = \'{}\', '.format(self.MRN)
            sql += '@adm = {}, '.format(self.admissionID)
            sql += '@entry_dt = @_entry_dt,'
            if annotation.annotation:
                sql += '@annotation = ?, '
                params.append(annotation.annotation)
            else:
                sql += '@annotation = NULL, '
            sql += '@type = \'{}\', '.format(annotation.type) 
            if annotation.href:
                sql += '@href = \'{}\', '.format(annotation.href) 
            else:
                sql += '@href = NULL, '
            sql += '@special_node = \'{}\', '.format(annotation.specialNode) 
            sql += '@format = \'{}\', '.format(annotation.format) 
            sql += '@username = \'{}\', '.format(self.username)
            sql += '@activity_date = @_activity_dt, ' 
            sql += '@id = @_id OUTPUT;'
            sql += 'select @_id;'
            annotation_id = db.sendSql(sql, params)[0][0]

            annotation.annotationID = annotation_id
            self.annotations.append(annotation)
        # Reload annotations from DB after mutation
        self.annotations = None
        self.loadAnnotations()
        return annotation

    def addFeedback(self, entryDatetime, exitDatetime, score, performance, outcome, attachmentKeys, notes, graphVisible, suggestedEdit, username):
        feedback = Feedback('', entryDatetime, exitDatetime, str(score), performance, outcome, attachmentKeys, notes, graphVisible, suggestedEdit, username)

        ### Add feedback to DB
        with SqlDatabase(sqlDatabaseConnect) as db:
            params = []
            sql = 'declare @_entry_dt datetime;'
            sql += 'declare @_exit_dt datetime;'
            sql += 'declare @_id int;'
            sql += 'declare @_activity_dt datetime;'
            sql += 'select @_entry_dt = CONVERT(DATETIME, \'{}\');'.format(feedback.entryDatetime)
            if feedback.exitDatetime:
                sql += 'select @_exit_dt = CONVERT(DATETIME, \'{}\');'.format(feedback.exitDatetime)
            else:
                sql += 'select @_exit_dt = NULL;'
            sql += 'select @_activity_dt = CONVERT(DATETIME, \'{}\');'.format(feedback.activityDate)

            sql += 'execute add_feedback '
            sql += '@mrn = \'{}\', '.format(self.MRN)
            sql += '@adm = {}, '.format(self.admissionID)
            sql += '@entry_dt = @_entry_dt,'
            sql += '@exit_dt = @_exit_dt,'
            sql += '@score = \'{}\', '.format(feedback.score) 
            sql += '@performance = \'{}\', '.format(feedback.performance) 
            sql += '@outcome = \'{}\', '.format(feedback.outcome) 
            if feedback.attachmentKeys:
                sql += '@att_keys = \'{}\', '.format(feedback.attachmentKeys) 
            else:
                sql += '@att_keys = NULL, '
            if feedback.notes:
                sql += '@notes = ?, '
                params.append(feedback.notes)
            else:
                sql += '@notes = NULL, '
            sql += '@graph_visible = \'{}\', '.format(feedback.graphVisible)
            sql += '@suggested_edit = ?, '
            params.append(feedback.suggestedEdit)
            sql += '@username = \'{}\', '.format(self.username)
            sql += '@activity_date = @_activity_dt, ' 
            sql += '@id = @_id OUTPUT;'
            sql += 'select @_id;'
            feedback_id = db.sendSql(sql, params)[0][0]

            feedback.feedbackID = feedback_id
            self.feedbacks.append(feedback)
        # Reload feedbacks from DB after mutation
        self.feedbacks = None
        self.loadFeedbacks()
        return feedback

    def addTimelineStep(self, locationStepID, location, riskStatus, entryDatetime, weight, locationNotes, riskNotes):
        self.timeline.append(TimelineStep(locationStepID, location, riskStatus, entryDatetime, weight, locationNotes, riskNotes))
        self.timeline = sorted(self.timeline, key=lambda d: d.entryDatetime)

    def addLocationStep(self, entryDatetime, location, teams, weight, notes, extra, username):
        locationStep = LocationStep('', entryDatetime, location, teams, weight, notes, extra, username, risks = [])
        ### Add things here to add step to timeline
        with SqlDatabase(sqlDatabaseConnect) as db:
            sql = 'declare @_entry_date datetime;'
            sql += 'declare @_id int;'
            sql += 'declare @_activity_dt datetime;'
            sql += 'select @_entry_date = CONVERT(DATETIME, \'{}\');'.format(locationStep.entryDatetime.strftime('%Y-%m-%d %H:%M'))
            sql += 'select @_activity_dt = CONVERT(DATETIME, \'{}\');'.format(locationStep.activityDate)

            sql += 'execute add_location_step '
            sql += '@mrn = \'{}\', '.format(self.MRN)
            sql += '@adm = {}, '.format(self.admissionID)
            sql += '@location = \'{}\', '.format(locationStep.location) 
            sql += '@entry_date = @_entry_date,'
            sql += '@username = \'{}\', '.format(self.username)
            sql += '@activity_date = @_activity_dt, ' 
            sql += '@id = @_id OUTPUT;'
            sql += 'select @_id;'
            location_step_id = db.sendSql(sql)[0][0]

            # Using parameters for user input fields for now. Probably should replace it all eventually
            params = []
            sql = 'update location_steps set '
            sql += 'Weight = ?, '
            params.append(locationStep.weight)

            sql += 'Teams = ?, '
            params.append(makeJsonRecord(locationStep.teams))

            sql += 'Notes = ? '
            params.append(makeJsonRecord(locationStep.notes))

            sql += 'where MRN = ? AND ADM = ? AND LocationStepID = ?'
            params.append(self.MRN)
            params.append(self.admissionID)
            params.append(location_step_id)
            db.sendSqlNoReturn(sql, params)

            locationStep.locationStepID = location_step_id
            self.location_steps.append(locationStep)
            self.location_steps = sorted(self.location_steps, key=lambda d: d.entryDatetime)

        return locationStep

    def addLocationRisk(self, locationStepID, startDatetime, risk, notes, extra, username):
        locationRisk = LocationRisk(locationStepID, '', startDatetime, risk, notes, extra, username)
        ### Add things here to add step to timeline
        with SqlDatabase(sqlDatabaseConnect) as db:
            sql  = 'declare @_start_dt datetime;'
            sql += 'declare @_id int;'
            sql += 'declare @_activity_dt datetime;'
            sql += 'select @_start_dt = CONVERT(DATETIME, \'{}\');'.format(locationRisk.startDatetime.strftime('%Y-%m-%d %H:%M'))
            sql += 'select @_activity_dt = CONVERT(DATETIME, \'{}\');'.format(locationRisk.activityDate)

            sql += 'execute add_location_risk '
            sql += '@mrn = \'{}\', '.format(self.MRN)
            sql += '@adm = {}, '.format(self.admissionID)
            sql += '@location_id = {}, '.format(locationRisk.locationStepID) 
            sql += '@start_dt = @_start_dt,'
            sql += '@risk = \'{}\', '.format(locationRisk.risk)
            sql += '@username = \'{}\', '.format(username)
            sql += '@activity_date = @_activity_dt, ' 
            sql += '@id = @_id OUTPUT;'
            sql += 'select @_id;'
            location_risk_id = db.sendSql(sql)[0][0]

            locationRisk.locationRiskID = location_risk_id
            # self.location_risks.append(locationRisk)

            locationStep = self.getLocationStep(locationRisk.locationStepID)
            locationStep.risks.append(locationRisk)
            locationStep.risks = sorted(locationStep.risks, key=lambda d: d.startDatetime)

            self.addTimelineStep(locationRisk.locationStepID, locationStep.location, locationRisk.risk, locationRisk.startDatetime, locationStep.weight, locationStep.notes, locationRisk.notes)

            return locationRisk

    # BULK SETTER METHODS
    def addAttachments(self, attachments, locationStepID = 0, locationRiskID = 0):
        ref_ids = {}
        for a in attachments:
            if 'content_data' in a:
                attachment = self.addAttachment(a['entryDatetime'], a['description'], a['storage_key'], a['filename'], a['type'], a['content_type'], a['content_data'], a['username'], locationStepID, locationRiskID)
                ref_ids[attachment.storageKey] = attachment.fileName
        
        # Reload attachments from DB after mutation
        self.attachments = None
        self.loadAttachments()
        return ref_ids

    # UPDATE METHODS
    def updateLocationStep(self, locationStepID, entryDatetime = '', location = '', teams = '', weight = '', notes = '', extra = '', username = ''):
        locationStep = self.getLocationStep(locationStepID)
        if entryDatetime  != '':
            # update location risk
            locationStep.risks[0].editLocationRisk(startDatetime = entryDatetime)
            locationStep.risks = sorted(locationStep.risks, key=lambda d: d.startDatetime)

            # update timeline step
            timelineStep = self.getTimelineStep(locationStepID)
            timelineStep = timelineStep.editTimelineStep(entryDatetime = entryDatetime)
            self.timeline = sorted(self.timeline, key=lambda d: d.entryDatetime)

        # update location step
        locationStep.editLocationStep(entryDatetime, location, teams, weight, notes, extra, username)
        self.location_steps = sorted(self.location_steps, key=lambda d: d.entryDatetime)

    # REMOVE METHODS
    def removeAttachment(self, attachmentID):
        toRemove = None
        for i, o in enumerate(self.attachments):
            if o.attachmentID == attachmentID:
                toRemove = o.removeAttachment()
                self.attachments.pop(i) # remove from attachments cache

                # find any refs to storageKey on annotationsTable
                storageKey = '{}_{}_{}'.format(self.MRN, self.admissionID, toRemove)
                annotations = list(filter(lambda x: storageKey in Admission.safe_json_loads(x.href), self.annotations)) # get annotations with storage key
                for a in annotations:
                    a.removeAttachment(storageKey)
                conferences = list(filter(lambda x: storageKey in json.loads(x.attachmentKeys), self.conferences)) # get conferences with storage key
                for c in conferences:
                    c.removeAttachment(storageKey)
                feedbacks = list(filter(lambda x: storageKey in json.loads(x.attachmentKeys), self.feedbacks)) # get conferences with storage key
                for f in feedbacks:
                    f.removeAttachment(storageKey)

                break

        # Reload all related caches from DB after mutation
        self.attachments = None
        self.loadAttachments()
        self.annotations = None
        self.loadAnnotations()
        self.conferences = None
        self.loadConferences()
        self.feedbacks = None
        self.loadFeedbacks()
        return toRemove

    def removeLocationStep(self, locationStepID):
        toRemove = next((i for i, locationStep in enumerate(self.location_steps) if locationStep.locationStepID == locationStepID), None)

        if toRemove != None and toRemove >= 0:
            self.location_steps.pop(toRemove)

            self.timeline = [timelineStep for timelineStep in self.timeline if timelineStep.locationStepID != locationStepID]
            self.attachments = [attachment for attachment in self.attachments if attachment.locationStepID != locationStepID]

            with SqlDatabase(sqlDatabaseConnect) as db:
                sql = 'delete from location_steps where MRN = \'{}\' AND ADM = {} AND LocationStepID = {}'.format(self.MRN, self.admissionID, locationStepID)
                db.sendSqlNoReturn(sql)
                sql = 'delete from location_risks where MRN = \'{}\' AND ADM = {} AND LocationStepID = {}'.format(self.MRN, self.admissionID, locationStepID)
                db.sendSqlNoReturn(sql)
                sql = 'delete from bedside_procedures where MRN = \'{}\' AND ADM = {} AND LocationStepID = {}'.format(self.MRN, self.admissionID, locationStepID)
                db.sendSqlNoReturn(sql)
                sql = 'delete from attachments where MRN = \'{}\' AND ADM = {} AND LocationStepID = {}'.format(self.MRN, self.admissionID, locationStepID)
                db.sendSqlNoReturn(sql)

        return toRemove

    # BULK REMOVE METHODS
    def removeAttachments(self, attachments):
        ref_ids = []
        for a in attachments:
            removed = self.removeAttachment(a.attachmentID)
            ref_ids.append(removed)

        # Reload attachments from DB after mutation
        self.attachments = None
        self.loadAttachments()
        return ref_ids

    # MISC METHODS
    def updateStatus(self, key, value):
        self.status[key] = value

    def getStatus(self, key = None):
        if key and self.status:
            return self.status[key]

        return self.status

    def setStatus(self, value, key = None):
        if key and self.status:
            self.status[key] = value

        return self.updateDatabaseEntry()

    def getCurrentWeight(self):
        weight = 0
        for location_step in reversed(self.location_steps):
            if location_step.weight:
                return location_step.weight

        return weight

    # Utility: safe JSON loads for annotation href
    @staticmethod
    def safe_json_loads(s):
        import json
        try:
            d = json.loads(s)
            return d if isinstance(d, dict) else {}
        except Exception:
            return {}
