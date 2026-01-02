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

	INSERT INTO  admissions (MRN, ADM, ADMDATE, Status, Interventions, Diagnosis, ReviewDate, CrossCheck, Username, ActivityDate) 
			VALUES (@mrn, @adm, @admdate, @status, @interventions, @diagnosis, @review_date, @cross_check, @username, @activity_date)

END