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

	INSERT INTO  location_risks (MRN, ADM, LocationStepID, StartDatetime, Risk, Username, ActivityDate) 
			VALUES (@mrn, @adm, @location_id, @start_dt, @risk, @username, @activity_date)
    SET @id=SCOPE_IDENTITY()
    RETURN  @id

END
