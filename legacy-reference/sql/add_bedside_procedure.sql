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

	INSERT INTO  bedside_procedures (MRN, ADM, LocationStepID, StartDatetime, EndDatetime, ProcedureType, Username, ActivityDate) 
			VALUES (@mrn, @adm, @location_id, @start_dt, @end_dt, @proceduretype, @username, @activity_date)
    SET @id=SCOPE_IDENTITY()
    RETURN  @id

END
