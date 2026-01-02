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

	INSERT INTO  patients (MRN, LastName, FirstName, DOB, sex, KeyDiagnosis, Deceased, Username, ActivityDate) 
			VALUES (@mrn, @last_name, @first_name, @dob, @sex, @key_diagnosis, @deceased, @username, @activity_date)

END