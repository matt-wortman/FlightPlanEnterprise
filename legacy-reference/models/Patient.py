import base64
import datetime as dt
import json
import math

from FpCodes import *
from FpConfig import sqlDatabaseConnect
from FpDatabase import SqlDatabase
from models.Admission import Admission
from utils.cache_manager import cache_manager
import logging
logging.basicConfig(level=logging.DEBUG)

class Patient():
    def __init__(self, MRN, lastName, firstName, DOB, sex, username, activityDate = dt.datetime.now().replace(microsecond=0), keyDiagnosis = '', deceased = 'N', addToDatabase = False, admissions = None):
        self.MRN = MRN
        self.lastName = lastName
        self.firstName = firstName
        self.DOB = DOB
        self.sex = sex
        self.username = username
        self.activityDate = activityDate
        self.keyDiagnosis = keyDiagnosis
        self.deceased = deceased == 'Y'
        # Ensure all admissions are Admission objects (eagerly loaded)
        if admissions is not None:
            self.admissions = [adm if isinstance(adm, Admission) else Admission(**adm) for adm in admissions]
        else:
            self.admissions = []
        self.activeAdmissionID = 0

        if addToDatabase:
            self.addPatientToDatabase()

    def editPatientInfo(self, lastName = '', firstName = '', DOB = '', sex = '', username = '', keyDiagnosis = '', deceased = ''):
        self.lastName = lastName if lastName != '' else self.lastName
        self.firstName = firstName if firstName != '' else self.firstName
        self.DOB = DOB if DOB != '' else self.DOB
        self.sex = sex if sex != '' else self.sex
        self.username =  username if username != '' else self.username
        self.activityDate = dt.datetime.now().replace(microsecond=0)
        self.keyDiagnosis = keyDiagnosis if keyDiagnosis != '' else self.keyDiagnosis
        self.deceased = deceased if deceased != '' else self.deceased
        self.updateDatabaseEntry()

    def addAdmission(self, admissionID, admissionDate, reviewDate, crossCheck, status = '', thumbnail = '', diagnosis = '', interventions = '', username = ''):
        admission = Admission(self.MRN, admissionID, admissionDate, reviewDate, crossCheck, status, thumbnail, diagnosis, interventions, username)

        with SqlDatabase(sqlDatabaseConnect) as db:
            params = []
            sql = 'declare @_admission_dt datetime;'
            sql += 'declare @_review_dt datetime;'
            sql += 'declare @_activity_dt datetime;'

            sql += 'select @_admission_dt = CONVERT(DATETIME, ?);'
            params.append(str(admission.surgeryDate))

            sql += 'select @_review_dt = CONVERT(DATETIME, ?);'
            params.append(str(admission.reviewDate))

            sql += 'select @_activity_dt = CONVERT(DATETIME, ?);'
            params.append(str(admission.activityDate))

            sql += 'execute add_admission '

            sql += '@mrn = ?, '
            params.append(str(self.MRN))

            sql += '@adm = ?, '
            params.append(str(admission.admissionID))

            sql += '@admdate = @_admission_dt,'

            sql += '@status = ?,'
            params.append(json.dumps(admission.status))

            sql += '@interventions = ?,'
            params.append(json.dumps(admission.interventions))

            sql += '@diagnosis = ?,'
            params.append(json.dumps(admission.diagnosis))

            sql += '@review_date = @_review_dt,'
            sql += '@cross_check = ?, '
            params.append(str(admission.crossCheck))

            sql += '@username = ?, '
            params.append(self.username)

            sql += '@activity_date = @_activity_dt; ' 
            sql += 'select @_admission_dt;'

            db.sendSql(sql, params)

        self.admissions.append(admission)
        self.activeAdmissionID = len(self.admissions)-1

        return admission

    def updateDatabaseEntry(self):
        with SqlDatabase(sqlDatabaseConnect) as db:
            params = []
            sql = 'declare @_activity_dt datetime;'
            sql += 'select @_activity_dt = CONVERT(DATETIME, ?);'
            params.append(str(self.activityDate))

            sql += 'update patients set ' 

            sql += 'LastName = ?, '
            params.append(self.lastName)

            sql += 'FirstName = ?, '
            params.append(self.firstName)

            sql += 'DOB = ?, '
            params.append(str(self.DOB))

            sql += 'sex = ?,  '
            params.append(self.sex)

            sql += 'KeyDiagnosis = ?, '
            params.append(self.keyDiagnosis)

            sql += 'Deceased = ?, '
            params.append(self.deceased)

            sql += 'Username = ?, '
            params.append(self.username)

            sql += 'ActivityDate = @_activity_dt '

            sql += ' where MRN = ?'
            params.append(str(self.MRN))

            db.sendSqlNoReturn(sql, params)

    def addPatientToDatabase(self):
        ### Add patient to database
        with SqlDatabase(sqlDatabaseConnect) as db:
            params = []
            sql = 'declare @_dob datetime;'
            sql += 'declare @_activity_dt datetime;'

            sql += 'select @_dob = CONVERT(DATETIME, ?);'
            params.append(str(self.DOB))

            sql += 'select @_activity_dt = CONVERT(DATETIME, ?);'
            params.append(str(self.activityDate))

            sql += 'execute add_patient '

            sql += '@mrn = ?, '
            params.append(str(self.MRN))

            sql += '@last_name = ?,'
            params.append(self.lastName)

            sql += '@first_name = ?,'
            params.append(self.firstName)

            sql += '@dob = @_dob,'

            sql += '@sex = ?, '
            params.append(self.sex) 

            sql += '@key_diagnosis = ?, '
            params.append(self.keyDiagnosis) 

            sql += '@deceased = ?, '
            params.append(self.deceased)

            sql += '@username = ?, '
            params.append(self.username)

            sql += '@activity_date = @_activity_dt; ' 
            sql += 'select @_dob;'

            db.sendSql(sql, params)
        #cache_manager.add_patients_to_new_page(self)
        return self

    def createAdmission(self, admission_data):
        interventions = {} if admission_data['Interventions'].strip('\"') == "" else json.loads(admission_data['Interventions'].strip('\"'))
        diagnosis = {} if admission_data['Diagnosis'].strip('\"') == '' else json.loads(admission_data['Diagnosis'].strip('\"'))
        return Admission(
            self.MRN,
            admission_data['ADM'],
            admission_data['ADMDATE'],
            admission_data['ReviewDate'],
            admission_data['CrossCheck'],
            json.loads(admission_data['Status']),
            admission_data['Thumbnail'],
            diagnosis,
            interventions,
            admission_data['Username'],
            admission_data['ActivityDate']
        )
    
    def getActiveAdmission(self):
        activeAdmission = None
        try:
            activeAdmission = self.admissions[self.activeAdmissionID]
        except Exception as e:
            logging.warning(f"No active admission for patient: {e}")
        

        return activeAdmission

    def isPatientOnTrack(self):
        course_corrections = self.getActiveAdmission().course_corrections
        lastSet = next((i for i in reversed(course_corrections) if i.type == 'set' and "ontrack:" in ''.join(i.detail.split()).lower()), None)
        if bool(lastSet) and "ontrack:no"  in ''.join(lastSet['detail'].split()).lower():
            return False
        return len(course_corrections) > 0

    def isPatientUpForReview(self):
        reviewTime = self.getActiveAdmission().reviewDate
        if reviewTime.date() >= dt.datetime.now().date():
            return True
        return False

    def reloadActiveAdmission(self):
        with SqlDatabase(sqlDatabaseConnect) as db:
            where = 'where MRN = \'{}\' AND ADM = {}'.format(self.MRN, self.activeAdmissionID)
            dbAdmission = db.select(admission_schema, where)[0]
            self.admissions[self.activeAdmissionID] = Admission(dbAdmission)

    def getInpatientStatus(self):
        return 'deceased' if self.deceased else 'outpatient' if self.admissions[0].getDischargeEntry() is not None else 'inpatient'

    def getAgeInTotalDays(self):
        age = dt.datetime.now() - self.DOB
        return age.days

    def getPatientYears(self):
        return math.floor(self.getAgeInTotalDays() / 365.25)

    def getPatientMonths(self):
        return math.floor((self.getAgeInTotalDays() - self.getPatientYears() * 365.25) * 12 / 365.25)

    def getPatientWeeks(self):
        return math.floor((self.getAgeInTotalDays() - self.getPatientYears() * 365.25 - self.getPatientMonths() * 365.25 / 12) / 7)

    def getPatientDays(self):
        return round(self.getAgeInTotalDays() - self.getPatientYears() * 365.25 - self.getPatientMonths() * 365.25 / 12 - self.getPatientWeeks() * 7)

    def getAgeString(self):
        years = self.getPatientYears()
        months = self.getPatientMonths()
        weeks = self.getPatientWeeks()
        days = self.getPatientDays()
        return "{}y {}m".format(years, months) if years > 0 else "{}m {}w".format(months, weeks) if months > 0 else "{}w {}d".format(weeks, days)
