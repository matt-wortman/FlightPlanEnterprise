
import datetime as dt
import os
import pickle
import random
import sys

import numpy as np
from FpConfig import sqlDatabaseConnect
from FpDatabase import GraphDatabase, SqlDatabase
from utils.FP2_AttachmentUtils import deleteBlob, listBlobs


def removeAllBlobs():
    blobs = listBlobs()
    for blob in blobs:
        deleteBlob(blob['name'])

def createTables():
    
    with SqlDatabase(sqlDatabaseConnect) as db:
        
        sql  = 'DROP TABLE IF EXISTS patients'
        db.sendSqlNoReturn(sql)

        sql  = 'CREATE TABLE patients ('
        sql += '    MRN varchar(50) not null,'
        sql += '    LastName varchar(100) not null,'
        sql += '    FirstName varchar(100) not null,'
        sql += '    DOB datetime not null,'
        sql += '    sex varchar(20) not null,'
        sql += '    KeyDiagnosis varchar(500),'
        sql += '    Deceased varchar(10),'
        sql += '    Username varchar(100),'
        sql += '    ActivityDate datetime'
        sql += '    PRIMARY KEY (MRN)'
        sql += ')'
        db.sendSqlNoReturn(sql)

        sql  = 'DROP TABLE IF EXISTS admissions'
        db.sendSqlNoReturn(sql)

        sql  = 'CREATE TABLE admissions ('
        sql += '    MRN varchar(50) not null,'
        sql += '    ADM int,'
        sql += '    ADMDATE datetime,'
        sql += '    Status varchar(3000),'
        sql += '    Interventions varchar(3000),'
        sql += '    Diagnosis varchar(1000),'
        sql += '    ReviewDate datetime,'
        sql += '    CrossCheck varchar(10),'
        sql += '    Thumbnail text,'
        sql += '    Username varchar(100),'
        sql += '    ActivityDate datetime'
        sql += '    PRIMARY KEY (MRN, ADM)'
        sql += ')'
        db.sendSqlNoReturn(sql)


        sql  = 'DROP TABLE IF EXISTS location_steps'
        db.sendSqlNoReturn(sql)

        sql  = 'CREATE TABLE location_steps ('
        sql += '    MRN varchar(50) not null,'
        sql += '    ADM int,'
        sql += '    LocationStepID int IDENTITY(1,1),'
        sql += '    EntryDatetime datetime,'
        sql += '    Location varchar(50),'
        sql += '    Teams varchar(500),'
        sql += '    Weight varchar(50),'
        sql += '    Notes varchar(3000),'
        sql += '    Extra varchar(3000),'
        sql += '    Username varchar(100),'
        sql += '    ActivityDate datetime'
        sql += '    PRIMARY KEY (MRN, ADM, LocationStepID)'
        sql += ')'
        db.sendSqlNoReturn(sql)

        sql  = 'DROP TABLE IF EXISTS location_risks'
        db.sendSqlNoReturn(sql)

        sql  = 'CREATE TABLE location_risks ('
        sql += '    MRN varchar(50) not null,'
        sql += '    ADM int,'
        sql += '    LocationStepID int,'
        sql += '    LocationRiskID int IDENTITY(1,1),'
        sql += '    StartDatetime datetime,'
        sql += '    Risk varchar(50),'
        sql += '    Notes varchar(3000),'
        sql += '    Extra varchar(3000),'
        sql += '    Username varchar(100),'
        sql += '    ActivityDate datetime'
        sql += '    PRIMARY KEY (MRN, ADM, LocationStepID, LocationRiskID)'
        sql += ')'
        db.sendSqlNoReturn(sql)


        sql  = 'DROP TABLE IF EXISTS bedside_procedures'
        db.sendSqlNoReturn(sql)

        sql  = 'CREATE TABLE bedside_procedures ('
        sql += '    MRN varchar(50) not null,'
        sql += '    ADM int,'
        sql += '    LocationStepID int,'
        sql += '    BedsideProcedureID int IDENTITY(1,1),'
        sql += '    StartDatetime datetime,'
        sql += '    EndDatetime datetime,'
        sql += '    ProcedureType varchar(50),'
        sql += '    Teams varchar(500),'
        sql += '    Notes varchar(3000),'
        sql += '    Username varchar(100),'
        sql += '    ActivityDate datetime'
        sql += '    PRIMARY KEY (MRN, ADM, LocationStepID, BedsideProcedureID)'
        sql += ')'
        db.sendSqlNoReturn(sql)


        sql  = 'DROP TABLE IF EXISTS ecmo'
        db.sendSqlNoReturn(sql)

        sql  = 'DROP TABLE IF EXISTS continuous_therapy'
        db.sendSqlNoReturn(sql)

        sql  = 'CREATE TABLE continuous_therapy ('
        sql += '    MRN varchar(50) not null,'
        sql += '    ADM int,'
        sql += '    CtId int IDENTITY(1,1),'
        sql += '    EntryDatetime datetime,'
        sql += '    Type varchar(200),'
        sql += '    Status varchar(200),'
        sql += '    AttachmentKeys varchar(8000),'
        sql += '    Notes varchar(3000),'
        sql += '    Username varchar(100),'
        sql += '    ActivityDate datetime'
        sql += '    PRIMARY KEY (MRN, ADM, CtId)'
        sql += ')'
        db.sendSqlNoReturn(sql)

        sql  = 'DROP TABLE IF EXISTS annotations'
        db.sendSqlNoReturn(sql)

        sql  = 'CREATE TABLE annotations ('
        sql += '    MRN varchar(50) not null,'
        sql += '    ADM int,'
        sql += '    AnnotaionID int IDENTITY(1,1),'
        sql += '    EntryDatetime datetime,'
        sql += '    annotation varchar(500),'
        sql += '    type varchar(50),'
        sql += '    href varchar(8000),'
        sql += '    SpecialNode varchar(200),'
        sql += '    format varchar(300),'
        sql += '    Username varchar(100),'
        sql += '    ActivityDate datetime'
        sql += '    PRIMARY KEY (MRN, ADM, Annotaionid)'
        sql += ')'
        db.sendSqlNoReturn(sql)


        sql  = 'DROP TABLE IF EXISTS feedbacks'
        db.sendSqlNoReturn(sql)

        sql  = 'CREATE TABLE feedbacks ('
        sql += '    MRN varchar(50) not null,'
        sql += '    ADM int,'
        sql += '    FeedbackID int IDENTITY(1,1),'
        sql += '    EntryDatetime datetime,'
        sql += '    ExitDatetime datetime,'
        sql += '    Score varchar(50),'
        sql += '    Performance varchar(50),'
        sql += '    Outcome varchar(50),'
        sql += '    AttachmentKeys varchar(8000),'
        sql += '    Notes varchar(500),'
        sql += '    GraphVisible varchar(10),'
        sql += '    SuggestedEdit varchar(10),'
        sql += '    Username varchar(100),'
        sql += '    ActivityDate datetime'
        sql += '    PRIMARY KEY (MRN, ADM, FeedbackID)'
        sql += ')'
        db.sendSqlNoReturn(sql)


        sql  = 'DROP TABLE IF EXISTS course_corrections'
        db.sendSqlNoReturn(sql)

        sql  = 'CREATE TABLE course_corrections ('
        sql += '    MRN varchar(50) not null,'
        sql += '    ADM int,'
        sql += '    course_correct_id int IDENTITY(1,1),'
        sql += '    EntryDatetime datetime,'
        sql += '    type varchar(50),'
        sql += '    detail varchar(500),'
        sql += '    Username varchar(100),'
        sql += '    ActivityDate datetime'
        sql += '    PRIMARY KEY (MRN, ADM, course_correct_id)'
        sql += ')'
        db.sendSqlNoReturn(sql)

        sql  = 'DROP TABLE IF EXISTS conferences'
        db.sendSqlNoReturn(sql)

        sql  = 'CREATE TABLE conferences ('
        sql += '    MRN varchar(50) not null,'
        sql += '    ADM int,'
        sql += '    ConferenceID int IDENTITY(1,1),'
        sql += '    EntryDatetime datetime,'
        sql += '    Type varchar(50),'
        sql += '    AttachmentKeys varchar(8000),'
        sql += '    ActionItems varchar(100),'
        sql += '    Notes varchar(500),'
        sql += '    Username varchar(100),'
        sql += '    ActivityDate datetime'
        sql += '    PRIMARY KEY (MRN, ADM, ConferenceID)'
        sql += ')'
        db.sendSqlNoReturn(sql)

        sql  = 'DROP TABLE IF EXISTS conference_details'
        db.sendSqlNoReturn(sql)

        sql  = 'DROP TABLE IF EXISTS reports'
        db.sendSqlNoReturn(sql)

        sql  = 'DROP TABLE IF EXISTS attachments'
        db.sendSqlNoReturn(sql)

        sql  = 'CREATE TABLE attachments ('
        sql += '    MRN varchar(50) not null,'
        sql += '    ADM int,'
        sql += '    AttachmentID int IDENTITY(1,1),'
        sql += '    LocationStepID int,'
        sql += '    LocationRiskID int,'
        sql += '    EntryDatetime datetime,'
        sql += '    storage_key varchar(8000),'
        sql += '    Filename varchar(500),'
        sql += '    Description varchar(500),'
        sql += '    AttachmentType varchar(100),'
        sql += '    ContentType varchar(100),'
        sql += '    Thumbnail text,'
        sql += '    Username varchar(100),'
        sql += '    ActivityDate datetime'
        sql += '    PRIMARY KEY (MRN, ADM, AttachmentID)'
        sql += ')'
        db.sendSqlNoReturn(sql)

        return

def addTest():

    patients = [{
            'MRN': '12345678',
             'LastName': 'Segala',   
             'FirstName': 'Jim',
             'DOB': '12/12/2002'   
            },
    ]

    with SqlDatabase(sqlDatabaseConnect) as db:
        for patient in patients:
            sql  = 'insert into patients (MRN, LastName, FirstName, DOB) values '
            sql += '(\'{0}\', \'{1}\',  \'{2}\',  \'{3}\')'
            sql = sql.format(patient['MRN'], patient['LastName'], patient['FirstName'], patient['DOB'])
            db.sendSqlNoReturn(sql)

def sqlTest():

    with SqlDatabase(sqlDatabaseConnect) as db:
        sql  = 'select *  from patients'
        records = db.sendSql(sql)
    print(records)

# def graphTest():
#     with GraphDatabase(graphDatabaseConnect) as db:
#         gremlin =  'g.V().hasLabel("patient")'
#         gremlin += '.values("MRN", "LastName", "FirstName")'
#         print(gremlin)
#         try:
#             patientResults = db.sendQuery(gremlin)
#         except Exception as excp:
#             print('Error found: {}'.format(excp))
#             raise excp
#         patientResults = db.reformatResults(patientResults, 3)
#         print(patientResults)

# def lumedxTest():

#     with SqlDatabase(sqlDatabaseConnectLUMEDX) as db:
#         sql  = 'exec sp_columns CCHMC_FlightPlan_STSProceduresView'
#         records = db.sendSql(sql)
#     for column in records:
#         print(column)



def createUsers():
    
    with SqlDatabase(sqlDatabaseConnect) as db:
        
        sql  = 'DROP TABLE IF EXISTS users'
        db.sendSqlNoReturn(sql)

        sql  = 'CREATE TABLE users ('
        sql += '    username varchar(100) not null,'
        sql += '    occupation varchar(100) not null,'
        sql += '    credentials int,'
        sql += '    last_access datetime,'
        sql += '    PRIMARY KEY (username)'
        sql += ')'
        db.sendSqlNoReturn(sql)

        users = [
                {'username': 'jsegala@sflscientific.com', 
                 'occupation': 'developer',
                 'credentials': 4},
                {'username': 'briotto@sflscientific.com', 
                 'occupation': 'developer',
                 'credentials': 4},
                {'username': 'ihall@sflscientific.com', 
                 'occupation': 'developer',
                 'credentials': 4},
                {'username': 'mcleverley@sflscientific.com', 
                 'occupation': 'developer',
                 'credentials': 4},

                {'username': 'brianne.reedy@cchmc.org', 
                 'occupation': 'administrator',
                 'credentials': 4},
                 {'username': 'kimberly.frickman@cchmc.org', 
                 'occupation': 'administrator',
                 'credentials': 4},
                 {'username': 'abbey.fugazzi@cchmc.org', 
                 'occupation': 'administrator',
                 'credentials': 4},
                {'username': 'ryan.moore@cchmc.org', 
                 'occupation': 'attending physician',
                 'credentials': 4},
                {'username': 'matt.wortman@cchmc.org', 
                 'occupation': 'administrator',
                 'credentials': 4},
                {'username': 'mark.steiner@cchmc.org', 
                 'occupation': 'administrator',
                 'credentials': 4},
                {'username': 'Guest', 
                 'occupation': 'Guest',
                 'credentials': 1},
            ]

        for user in users:
            sql = 'insert into users (username, occupation, credentials) values ('
            sql += '\'{}\', '.format(user['username'])
            sql += '\'{}\', '.format(user['occupation'])
            sql += '{} '.format(user['credentials'])
            sql += ')'

            db.sendSqlNoReturn(sql)
        return

def createAndPopulateDatabase():
    createTables()
    with SqlDatabase(sqlDatabaseConnect) as db:
        with open('../backup/OFFICIAL_backup.sql', 'r') as fp:
            sql = fp.read()
        db.sendSqlNoReturn(sql)

def createStoredProcedures():
    procedures = [
        {'name': 'add_annotation', 'file': 'sql/add_annotation.sql'},
        {'name': 'add_attachment', 'file': 'sql/add_attachment.sql'},
        {'name': 'add_bedside_procedure', 'file': 'sql/add_bedside_procedure.sql'},
        {'name': 'add_location_risk', 'file': 'sql/add_location_risk.sql'},
        {'name': 'add_location_step', 'file': 'sql/add_location_step.sql'},
        {'name': 'add_conference', 'file': 'sql/add_conference.sql'},
        {'name': 'add_feedback', 'file': 'sql/add_feedback.sql'},
        {'name': 'add_patient', 'file': 'sql/add_patient.sql'},
        {'name': 'add_admission', 'file': 'sql/add_admission.sql'},
        {'name': 'add_continuous_therapy', 'file': 'sql/add_continuous_therapy.sql'},
    ]
    with SqlDatabase(sqlDatabaseConnect) as db:
        for procedure in procedures:

            sql  = 'DROP PROCEDURE IF EXISTS dbo.{}'.format(procedure['name'])
            db.sendSqlNoReturn(sql)

            with open(procedure['file'], 'r') as fp:
                sql = fp.read()

            db.sendSqlNoReturn(sql)
            print('Created procedure {}'.format(procedure['name']))
            aaa = 1

removeAllBlobs()
createTables()
# createAndPopulateDatabase()
createUsers()
createStoredProcedures()

#addTest()
#sqlTest()   
#graphTest()   
#lumedxTest()

aaa = 1

