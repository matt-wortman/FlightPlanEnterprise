-- FlightPlan2 Database Initialization Script
-- This script creates the database, tables, stored procedures, and seed data
-- Run with: sqlcmd -S localhost -U sa -P "password" -i init-database.sql

USE master;
GO

-- Create database if not exists
IF NOT EXISTS (SELECT name FROM sys.databases WHERE name = 'FlightPlan')
BEGIN
    CREATE DATABASE FlightPlan;
END
GO

USE FlightPlan;
GO

-- ============================================
-- DROP EXISTING TABLES (if any)
-- ============================================

IF OBJECT_ID('dbo.attachments', 'U') IS NOT NULL DROP TABLE dbo.attachments;
IF OBJECT_ID('dbo.course_corrections', 'U') IS NOT NULL DROP TABLE dbo.course_corrections;
IF OBJECT_ID('dbo.conferences', 'U') IS NOT NULL DROP TABLE dbo.conferences;
IF OBJECT_ID('dbo.feedbacks', 'U') IS NOT NULL DROP TABLE dbo.feedbacks;
IF OBJECT_ID('dbo.annotations', 'U') IS NOT NULL DROP TABLE dbo.annotations;
IF OBJECT_ID('dbo.continuous_therapy', 'U') IS NOT NULL DROP TABLE dbo.continuous_therapy;
IF OBJECT_ID('dbo.bedside_procedures', 'U') IS NOT NULL DROP TABLE dbo.bedside_procedures;
IF OBJECT_ID('dbo.location_risks', 'U') IS NOT NULL DROP TABLE dbo.location_risks;
IF OBJECT_ID('dbo.location_steps', 'U') IS NOT NULL DROP TABLE dbo.location_steps;
IF OBJECT_ID('dbo.admissions', 'U') IS NOT NULL DROP TABLE dbo.admissions;
IF OBJECT_ID('dbo.patients', 'U') IS NOT NULL DROP TABLE dbo.patients;
IF OBJECT_ID('dbo.users', 'U') IS NOT NULL DROP TABLE dbo.users;
GO

-- ============================================
-- CREATE TABLES
-- ============================================

CREATE TABLE patients (
    MRN varchar(50) not null,
    LastName varchar(100) not null,
    FirstName varchar(100) not null,
    DOB datetime not null,
    sex varchar(20) not null,
    KeyDiagnosis varchar(500),
    Deceased varchar(10),
    Username varchar(100),
    ActivityDate datetime,
    PRIMARY KEY (MRN)
);
GO

CREATE TABLE admissions (
    MRN varchar(50) not null,
    ADM int,
    ADMDATE datetime,
    Status varchar(3000),
    Interventions varchar(3000),
    Diagnosis varchar(1000),
    ReviewDate datetime,
    CrossCheck varchar(10),
    Thumbnail text,
    Username varchar(100),
    ActivityDate datetime,
    PRIMARY KEY (MRN, ADM)
);
GO

CREATE TABLE location_steps (
    MRN varchar(50) not null,
    ADM int,
    LocationStepID int IDENTITY(1,1),
    EntryDatetime datetime,
    Location varchar(50),
    Teams varchar(500),
    Weight varchar(50),
    Notes varchar(3000),
    Extra varchar(3000),
    Username varchar(100),
    ActivityDate datetime,
    PRIMARY KEY (MRN, ADM, LocationStepID)
);
GO

CREATE TABLE location_risks (
    MRN varchar(50) not null,
    ADM int,
    LocationStepID int,
    LocationRiskID int IDENTITY(1,1),
    StartDatetime datetime,
    Risk varchar(50),
    Notes varchar(3000),
    Extra varchar(3000),
    Username varchar(100),
    ActivityDate datetime,
    PRIMARY KEY (MRN, ADM, LocationStepID, LocationRiskID)
);
GO

CREATE TABLE bedside_procedures (
    MRN varchar(50) not null,
    ADM int,
    LocationStepID int,
    BedsideProcedureID int IDENTITY(1,1),
    StartDatetime datetime,
    EndDatetime datetime,
    ProcedureType varchar(50),
    Teams varchar(500),
    Notes varchar(3000),
    Username varchar(100),
    ActivityDate datetime,
    PRIMARY KEY (MRN, ADM, LocationStepID, BedsideProcedureID)
);
GO

CREATE TABLE continuous_therapy (
    MRN varchar(50) not null,
    ADM int,
    CtId int IDENTITY(1,1),
    EntryDatetime datetime,
    Type varchar(200),
    Status varchar(200),
    AttachmentKeys varchar(8000),
    Notes varchar(3000),
    Username varchar(100),
    ActivityDate datetime,
    PRIMARY KEY (MRN, ADM, CtId)
);
GO

CREATE TABLE annotations (
    MRN varchar(50) not null,
    ADM int,
    AnnotaionID int IDENTITY(1,1),
    EntryDatetime datetime,
    annotation varchar(500),
    type varchar(50),
    href varchar(8000),
    SpecialNode varchar(200),
    format varchar(300),
    Username varchar(100),
    ActivityDate datetime,
    PRIMARY KEY (MRN, ADM, AnnotaionID)
);
GO

CREATE TABLE feedbacks (
    MRN varchar(50) not null,
    ADM int,
    FeedbackID int IDENTITY(1,1),
    EntryDatetime datetime,
    ExitDatetime datetime,
    Score varchar(50),
    Performance varchar(50),
    Outcome varchar(50),
    AttachmentKeys varchar(8000),
    Notes varchar(500),
    GraphVisible varchar(10),
    SuggestedEdit varchar(10),
    Username varchar(100),
    ActivityDate datetime,
    PRIMARY KEY (MRN, ADM, FeedbackID)
);
GO

CREATE TABLE course_corrections (
    MRN varchar(50) not null,
    ADM int,
    course_correct_id int IDENTITY(1,1),
    EntryDatetime datetime,
    type varchar(50),
    detail varchar(500),
    Username varchar(100),
    ActivityDate datetime,
    PRIMARY KEY (MRN, ADM, course_correct_id)
);
GO

CREATE TABLE conferences (
    MRN varchar(50) not null,
    ADM int,
    ConferenceID int IDENTITY(1,1),
    EntryDatetime datetime,
    Type varchar(50),
    AttachmentKeys varchar(8000),
    ActionItems varchar(100),
    Notes varchar(500),
    Username varchar(100),
    ActivityDate datetime,
    PRIMARY KEY (MRN, ADM, ConferenceID)
);
GO

CREATE TABLE attachments (
    MRN varchar(50) not null,
    ADM int,
    AttachmentID int IDENTITY(1,1),
    LocationStepID int,
    LocationRiskID int,
    EntryDatetime datetime,
    storage_key varchar(8000),
    Filename varchar(500),
    Description varchar(500),
    AttachmentType varchar(100),
    ContentType varchar(100),
    Thumbnail text,
    Username varchar(100),
    ActivityDate datetime,
    PRIMARY KEY (MRN, ADM, AttachmentID)
);
GO

CREATE TABLE users (
    username varchar(100) not null,
    occupation varchar(100) not null,
    credentials int,
    last_access datetime,
    PRIMARY KEY (username)
);
GO

-- ============================================
-- CREATE STORED PROCEDURES
-- ============================================

-- Drop existing procedures
IF OBJECT_ID('dbo.add_patient', 'P') IS NOT NULL DROP PROCEDURE dbo.add_patient;
IF OBJECT_ID('dbo.add_admission', 'P') IS NOT NULL DROP PROCEDURE dbo.add_admission;
IF OBJECT_ID('dbo.add_location_step', 'P') IS NOT NULL DROP PROCEDURE dbo.add_location_step;
IF OBJECT_ID('dbo.add_location_risk', 'P') IS NOT NULL DROP PROCEDURE dbo.add_location_risk;
IF OBJECT_ID('dbo.add_bedside_procedure', 'P') IS NOT NULL DROP PROCEDURE dbo.add_bedside_procedure;
IF OBJECT_ID('dbo.add_annotation', 'P') IS NOT NULL DROP PROCEDURE dbo.add_annotation;
IF OBJECT_ID('dbo.add_feedback', 'P') IS NOT NULL DROP PROCEDURE dbo.add_feedback;
IF OBJECT_ID('dbo.add_conference', 'P') IS NOT NULL DROP PROCEDURE dbo.add_conference;
IF OBJECT_ID('dbo.add_attachment', 'P') IS NOT NULL DROP PROCEDURE dbo.add_attachment;
IF OBJECT_ID('dbo.add_continuous_therapy', 'P') IS NOT NULL DROP PROCEDURE dbo.add_continuous_therapy;
GO

-- add_patient
CREATE PROCEDURE [dbo].[add_patient]
    @mrn varchar(50),
    @last_name varchar(100),
    @first_name varchar(100),
    @dob datetime,
    @sex varchar(20),
    @key_diagnosis varchar(500),
    @deceased varchar(1),
    @username varchar(100),
    @activity_date datetime
AS
BEGIN
    SET NOCOUNT ON;
    INSERT INTO patients (MRN, LastName, FirstName, DOB, sex, KeyDiagnosis, Deceased, Username, ActivityDate)
        VALUES (@mrn, @last_name, @first_name, @dob, @sex, @key_diagnosis, @deceased, @username, @activity_date)
END
GO

-- add_admission
CREATE PROCEDURE [dbo].[add_admission]
    @mrn varchar(50),
    @adm int,
    @admdate datetime,
    @status varchar(500),
    @interventions varchar(50),
    @diagnosis varchar(100),
    @review_date varchar(200),
    @cross_check varchar(300),
    @username varchar(100),
    @activity_date datetime
AS
BEGIN
    SET NOCOUNT ON;
    INSERT INTO admissions (MRN, ADM, ADMDATE, Status, Interventions, Diagnosis, ReviewDate, CrossCheck, Username, ActivityDate)
        VALUES (@mrn, @adm, @admdate, @status, @interventions, @diagnosis, @review_date, @cross_check, @username, @activity_date)
END
GO

-- add_location_step
CREATE PROCEDURE [dbo].[add_location_step]
    @mrn varchar(50),
    @adm int,
    @location varchar(50),
    @entry_date datetime,
    @username varchar(100),
    @activity_date datetime,
    @id int output
AS
BEGIN
    SET NOCOUNT ON;
    INSERT INTO location_steps (MRN, ADM, Location, EntryDatetime, Username, ActivityDate)
        VALUES (@mrn, @adm, @location, @entry_date, @username, @activity_date)
    SET @id=SCOPE_IDENTITY()
    RETURN @id
END
GO

-- add_location_risk
CREATE PROCEDURE [dbo].[add_location_risk]
    @mrn varchar(50),
    @adm int,
    @location_id int,
    @start_dt datetime,
    @risk varchar(50),
    @username varchar(100),
    @activity_date datetime,
    @id int output
AS
BEGIN
    SET NOCOUNT ON;
    INSERT INTO location_risks (MRN, ADM, LocationStepID, StartDatetime, Risk, Username, ActivityDate)
        VALUES (@mrn, @adm, @location_id, @start_dt, @risk, @username, @activity_date)
    SET @id=SCOPE_IDENTITY()
    RETURN @id
END
GO

-- add_bedside_procedure
CREATE PROCEDURE [dbo].[add_bedside_procedure]
    @mrn varchar(50),
    @adm int,
    @location_id int,
    @start_dt datetime,
    @end_dt datetime,
    @proceduretype varchar(50),
    @username varchar(100),
    @activity_date datetime,
    @id int output
AS
BEGIN
    SET NOCOUNT ON;
    INSERT INTO bedside_procedures (MRN, ADM, LocationStepID, StartDatetime, EndDatetime, ProcedureType, Username, ActivityDate)
        VALUES (@mrn, @adm, @location_id, @start_dt, @end_dt, @proceduretype, @username, @activity_date)
    SET @id=SCOPE_IDENTITY()
    RETURN @id
END
GO

-- add_annotation
CREATE PROCEDURE [dbo].[add_annotation]
    @mrn varchar(50),
    @adm int,
    @entry_dt datetime,
    @annotation varchar(500),
    @type varchar(50),
    @href varchar(100),
    @special_node varchar(200),
    @format varchar(300),
    @username varchar(100),
    @activity_date datetime,
    @id int output
AS
BEGIN
    SET NOCOUNT ON;
    INSERT INTO annotations (MRN, ADM, EntryDatetime, annotation, type, href, SpecialNode, format, Username, ActivityDate)
        VALUES (@mrn, @adm, @entry_dt, @annotation, @type, @href, @special_node, @format, @username, @activity_date)
    SET @id=SCOPE_IDENTITY()
    RETURN @id
END
GO

-- add_feedback
CREATE PROCEDURE [dbo].[add_feedback]
    @mrn varchar(50),
    @adm int,
    @entry_dt datetime,
    @exit_dt datetime,
    @score varchar(50),
    @performance varchar(50),
    @outcome varchar(100),
    @att_keys varchar(100),
    @notes varchar(500),
    @graph_visible varchar(10),
    @suggested_edit varchar(10),
    @username varchar(100),
    @activity_date datetime,
    @id int output
AS
BEGIN
    SET NOCOUNT ON;
    INSERT INTO feedbacks (MRN, ADM, EntryDatetime, ExitDatetime, Score, Performance, Outcome, AttachmentKeys, Notes, GraphVisible, SuggestedEdit, Username, ActivityDate)
        VALUES (@mrn, @adm, @entry_dt, @exit_dt, @score, @performance, @outcome, @att_keys, @notes, @graph_visible, @suggested_edit, @username, @activity_date)
    SET @id=SCOPE_IDENTITY()
    RETURN @id
END
GO

-- add_conference
CREATE PROCEDURE [dbo].[add_conference]
    @mrn varchar(50),
    @adm int,
    @entry_dt datetime,
    @type varchar(50),
    @att_keys varchar(100),
    @action_items varchar(100),
    @notes varchar(500),
    @username varchar(100),
    @activity_date datetime,
    @id int output
AS
BEGIN
    SET NOCOUNT ON;
    INSERT INTO conferences (MRN, ADM, EntryDatetime, Type, AttachmentKeys, ActionItems, Notes, Username, ActivityDate)
        VALUES (@mrn, @adm, @entry_dt, @type, @att_keys, @action_items, @notes, @username, @activity_date)
    SET @id=SCOPE_IDENTITY()
    RETURN @id
END
GO

-- add_attachment
CREATE PROCEDURE [dbo].[add_attachment]
    @mrn varchar(50),
    @adm int,
    @location_id int,
    @risk_id int,
    @entry_dt datetime,
    @username varchar(100),
    @activity_date datetime,
    @id int output
AS
BEGIN
    SET NOCOUNT ON;
    INSERT INTO attachments (MRN, ADM, LocationStepID, LocationRiskID, EntryDatetime, Username, ActivityDate)
        VALUES (@mrn, @adm, @location_id, @risk_id, @entry_dt, @username, @activity_date)
    SET @id=SCOPE_IDENTITY()
    RETURN @id
END
GO

-- add_continuous_therapy
CREATE PROCEDURE [dbo].[add_continuous_therapy]
    @mrn varchar(50),
    @adm int,
    @entry_dt datetime,
    @type varchar(50),
    @status varchar(200),
    @att_keys varchar(1000),
    @notes varchar(3000),
    @username varchar(100),
    @activity_date datetime,
    @id int output
AS
BEGIN
    SET NOCOUNT ON;
    INSERT INTO continuous_therapy (MRN, ADM, EntryDatetime, Type, Status, AttachmentKeys, Notes, Username, ActivityDate)
        VALUES (@mrn, @adm, @entry_dt, @type, @status, @att_keys, @notes, @username, @activity_date)
    SET @id=SCOPE_IDENTITY()
    RETURN @id
END
GO

-- ============================================
-- INSERT SEED USERS
-- ============================================

INSERT INTO users (username, occupation, credentials) VALUES ('dev@local.dev', 'developer', 4);
INSERT INTO users (username, occupation, credentials) VALUES ('jsegala@sflscientific.com', 'developer', 4);
INSERT INTO users (username, occupation, credentials) VALUES ('briotto@sflscientific.com', 'developer', 4);
INSERT INTO users (username, occupation, credentials) VALUES ('ihall@sflscientific.com', 'developer', 4);
INSERT INTO users (username, occupation, credentials) VALUES ('mcleverley@sflscientific.com', 'developer', 4);
INSERT INTO users (username, occupation, credentials) VALUES ('brianne.reedy@cchmc.org', 'administrator', 4);
INSERT INTO users (username, occupation, credentials) VALUES ('kimberly.frickman@cchmc.org', 'administrator', 4);
INSERT INTO users (username, occupation, credentials) VALUES ('abbey.fugazzi@cchmc.org', 'administrator', 4);
INSERT INTO users (username, occupation, credentials) VALUES ('ryan.moore@cchmc.org', 'attending physician', 4);
INSERT INTO users (username, occupation, credentials) VALUES ('matt.wortman@cchmc.org', 'administrator', 4);
INSERT INTO users (username, occupation, credentials) VALUES ('mark.steiner@cchmc.org', 'administrator', 4);
INSERT INTO users (username, occupation, credentials) VALUES ('Guest', 'Guest', 1);
GO

-- ============================================
-- INSERT SEED DATA (Mickey Mouse patient)
-- ============================================

-- Patient
INSERT [dbo].[patients] ([MRN], [LastName], [FirstName], [DOB], [sex], [KeyDiagnosis], [Deceased])
    VALUES (N'1234567890', N'Mouse', N'Mickey', CAST(N'2017-08-17T14:13:00.000' AS DateTime), N'M', NULL, N'N');

-- Admission
INSERT [dbo].[admissions] ([MRN], [ADM], [ADMDATE], [Status], [Interventions], [Diagnosis], [ReviewDate], [Thumbnail], [CrossCheck])
    VALUES (N'1234567890', 1, CAST(N'2022-01-01T01:01:00.000' AS DateTime),
    N'{"RiskStatus": "ACCU", "Location": "CTOR", "Cardiologist": [""], "Surgeon": ["Morales, D."], "Anesthesia": [], "Attending": [], "Index": 1, "LOS": 0, "ReviewDate": "", "DischargeDate": "", "Procedures": 0, "ACCU": [], "CICU": [], "CATH": [], "SurgeryDate": "2022-09-07 17:13", "Weight": ""}',
    N'""', N'""', CAST(N'1900-01-01T00:00:00.000' AS DateTime), NULL, NULL);

-- Location Steps (need to set IDENTITY_INSERT)
SET IDENTITY_INSERT [dbo].[location_steps] ON;
INSERT [dbo].[location_steps] ([MRN], [ADM], [LocationStepID], [EntryDatetime], [Location], [Teams], [Weight], [Notes], [Extra])
    VALUES (N'1234567890', 1, 137, CAST(N'2022-01-01T01:01:00.000' AS DateTime), N'Pre-op', N'{}', N'15kg', N'{}', NULL);
INSERT [dbo].[location_steps] ([MRN], [ADM], [LocationStepID], [EntryDatetime], [Location], [Teams], [Weight], [Notes], [Extra])
    VALUES (N'1234567890', 1, 138, CAST(N'2022-01-02T11:12:00.000' AS DateTime), N'CICU',
    N'{"attending_day_shift": [{"name": "Cooper, D.", "shift": "On-Service (day shift)", "start_dt": "2022-01-03 06:12:00"}], "attending_night_shift": [{"name": "Gist, K.", "shift": "On-Service (night shift)", "start_dt": "2022-01-04 15:12:00"}]}',
    N'12kg', N'{}', NULL);
INSERT [dbo].[location_steps] ([MRN], [ADM], [LocationStepID], [EntryDatetime], [Location], [Teams], [Weight], [Notes], [Extra])
    VALUES (N'1234567890', 1, 139, CAST(N'2022-01-05T11:12:00.000' AS DateTime), N'Cath',
    N'{"intervention": [{"name": "Morales, D.", "shift": "", "start_dt": ""}], "anesthesia": [{"name": "Spaeth, J.", "shift": "", "start_dt": ""}]}',
    N'12kg', N'{"cath_intervention": "This is a note for Cath Intervention 1", "notes": "This is a general note 1"}', NULL);
INSERT [dbo].[location_steps] ([MRN], [ADM], [LocationStepID], [EntryDatetime], [Location], [Teams], [Weight], [Notes], [Extra])
    VALUES (N'1234567890', 1, 140, CAST(N'2022-01-08T11:12:00.000' AS DateTime), N'CTOR',
    N'{"surgeon": [{"name": "Morales, D.", "shift": "", "start_dt": ""}], "anesthesia": [{"name": "Spaeth, J.", "shift": "", "start_dt": ""}]}',
    N'15kg', N'{"surgical_repair": "This is a note for surical repair", "notes": "This is a general note 2"}', NULL);
INSERT [dbo].[location_steps] ([MRN], [ADM], [LocationStepID], [EntryDatetime], [Location], [Teams], [Weight], [Notes], [Extra])
    VALUES (N'1234567890', 1, 141, CAST(N'2022-01-06T02:14:00.000' AS DateTime), N'Cath',
    N'{"intervention": [{"name": "Winlaw, D.", "shift": "", "start_dt": ""}], "anesthesia": [{"name": "Monteleone, M.", "shift": "", "start_dt": ""}]}',
    N'16kg', N'{"cath_intervention": "This is a note for Cath Intervention 2", "notes": "This is a general note 2"}', NULL);
INSERT [dbo].[location_steps] ([MRN], [ADM], [LocationStepID], [EntryDatetime], [Location], [Teams], [Weight], [Notes], [Extra])
    VALUES (N'1234567890', 1, 142, CAST(N'2022-01-22T01:14:00.000' AS DateTime), N'ACCU',
    N'{"attending_day_shift": [{"name": "Cooper, D.", "shift": "On-Service (day shift)", "start_dt": "2022-01-03 06:12:00"}], "attending_night_shift": [{"name": "Gist, K.", "shift": "On-Service (night shift)", "start_dt": "2022-01-04 15:12:00"}]}',
    N'22kg', N'{}', NULL);
INSERT [dbo].[location_steps] ([MRN], [ADM], [LocationStepID], [EntryDatetime], [Location], [Teams], [Weight], [Notes], [Extra])
    VALUES (N'1234567890', 1, 143, CAST(N'2022-02-01T01:01:00.000' AS DateTime), N'DC', N'{}', N'15kg', N'{}', NULL);
SET IDENTITY_INSERT [dbo].[location_steps] OFF;
GO

-- Location Risks
SET IDENTITY_INSERT [dbo].[location_risks] ON;
INSERT [dbo].[location_risks] ([MRN], [ADM], [LocationStepID], [LocationRiskID], [StartDatetime], [Risk], [Notes], [Extra])
    VALUES (N'1234567890', 1, 137, 162, CAST(N'2022-01-01T01:01:00.000' AS DateTime), N'ACCU', NULL, NULL);
INSERT [dbo].[location_risks] ([MRN], [ADM], [LocationStepID], [LocationRiskID], [StartDatetime], [Risk], [Notes], [Extra])
    VALUES (N'1234567890', 1, 138, 163, CAST(N'2022-01-02T11:12:00.000' AS DateTime), N'Intubated / Conv Vent', NULL, NULL);
INSERT [dbo].[location_risks] ([MRN], [ADM], [LocationStepID], [LocationRiskID], [StartDatetime], [Risk], [Notes], [Extra])
    VALUES (N'1234567890', 1, 138, 164, CAST(N'2022-01-03T10:12:00.000' AS DateTime), N'Extubated / HFNC', NULL, NULL);
INSERT [dbo].[location_risks] ([MRN], [ADM], [LocationStepID], [LocationRiskID], [StartDatetime], [Risk], [Notes], [Extra])
    VALUES (N'1234567890', 1, 139, 165, CAST(N'2022-01-05T10:12:00.000' AS DateTime), N'Procedure', NULL, NULL);
INSERT [dbo].[location_risks] ([MRN], [ADM], [LocationStepID], [LocationRiskID], [StartDatetime], [Risk], [Notes], [Extra])
    VALUES (N'1234567890', 1, 140, 166, CAST(N'2022-01-08T10:12:00.000' AS DateTime), N'Procedure', NULL, NULL);
INSERT [dbo].[location_risks] ([MRN], [ADM], [LocationStepID], [LocationRiskID], [StartDatetime], [Risk], [Notes], [Extra])
    VALUES (N'1234567890', 1, 141, 167, CAST(N'2022-01-06T06:14:00.000' AS DateTime), N'Procedure', NULL, NULL);
INSERT [dbo].[location_risks] ([MRN], [ADM], [LocationStepID], [LocationRiskID], [StartDatetime], [Risk], [Notes], [Extra])
    VALUES (N'1234567890', 1, 142, 168, CAST(N'2022-01-22T11:12:00.000' AS DateTime), N'Intubated / Conv Vent', NULL, NULL);
INSERT [dbo].[location_risks] ([MRN], [ADM], [LocationStepID], [LocationRiskID], [StartDatetime], [Risk], [Notes], [Extra])
    VALUES (N'1234567890', 1, 142, 169, CAST(N'2022-01-23T10:12:00.000' AS DateTime), N'Extubated / HFNC', NULL, NULL);
INSERT [dbo].[location_risks] ([MRN], [ADM], [LocationStepID], [LocationRiskID], [StartDatetime], [Risk], [Notes], [Extra])
    VALUES (N'1234567890', 1, 143, 170, CAST(N'2022-02-01T01:01:00.000' AS DateTime), N'Discharge', NULL, NULL);
SET IDENTITY_INSERT [dbo].[location_risks] OFF;
GO

-- Annotations
SET IDENTITY_INSERT [dbo].[annotations] ON;
INSERT [dbo].[annotations] ([MRN], [ADM], [AnnotaionID], [EntryDatetime], [annotation], [type], [href], [format], [SpecialNode])
    VALUES (N'1234567890', 1, 23, CAST(N'2022-01-07T14:13:00.000' AS DateTime), N'Broken intra-cardiac line, return to OR', N'Note', NULL, N'{"angle": 0, "color": "", "location": "above_line", "y": 0, "x": 0}', NULL);
INSERT [dbo].[annotations] ([MRN], [ADM], [AnnotaionID], [EntryDatetime], [annotation], [type], [href], [format], [SpecialNode])
    VALUES (N'1234567890', 1, 24, CAST(N'2022-01-22T23:18:00.000' AS DateTime), N'Pneumothorax post chest tube removal', N'Note', NULL, N'{"angle": 0, "color": "", "location": "above_line", "y": 0, "x": 0}', NULL);
SET IDENTITY_INSERT [dbo].[annotations] OFF;
GO

PRINT 'FlightPlan database initialization complete!';
PRINT 'Tables created: patients, admissions, location_steps, location_risks, bedside_procedures,';
PRINT '                continuous_therapy, annotations, feedbacks, course_corrections, conferences, attachments, users';
PRINT 'Stored procedures created: add_patient, add_admission, add_location_step, add_location_risk,';
PRINT '                           add_bedside_procedure, add_annotation, add_feedback, add_conference,';
PRINT '                           add_attachment, add_continuous_therapy';
PRINT 'Seed data: 1 patient (Mickey Mouse), 1 admission, 7 location steps, 9 location risks, 2 annotations';
GO
