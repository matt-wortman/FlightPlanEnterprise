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