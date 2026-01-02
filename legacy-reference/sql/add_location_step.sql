CREATE PROCEDURE [dbo].[add_location_step] 
	-- Add the parameters for the stored procedure here
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

	INSERT INTO  location_steps (MRN, ADM, Location, EntryDatetime, Username, ActivityDate) VALUES 
							(@mrn, @adm, @location, @entry_date, @username, @activity_date)
    SET @id=SCOPE_IDENTITY()
    RETURN  @id

END
