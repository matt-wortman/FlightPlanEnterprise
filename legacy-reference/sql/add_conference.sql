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

	INSERT INTO  conferences (MRN, ADM, EntryDatetime, Type, AttachmentKeys, ActionItems, Notes, Username, ActivityDate) 
			VALUES (@mrn, @adm, @entry_dt, @type, @att_keys, @action_items, @notes, @username, @activity_date)
    SET @id=SCOPE_IDENTITY()
    RETURN @id

END