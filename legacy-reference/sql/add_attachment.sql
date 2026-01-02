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

	INSERT INTO  attachments (MRN, ADM, LocationStepID, LocationRiskID, EntryDatetime, Username, ActivityDate) 
			VALUES (@mrn, @adm, @location_id, @risk_id, @entry_dt, @username, @activity_date)
    SET @id=SCOPE_IDENTITY()
    RETURN  @id

END