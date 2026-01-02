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

	INSERT INTO  annotations (MRN, ADM, EntryDatetime, annotation, type, href, SpecialNode, format, Username, ActivityDate) 
			VALUES (@mrn, @adm, @entry_dt, @annotation, @type, @href, @special_node, @format, @username, @activity_date)
    SET @id=SCOPE_IDENTITY()
    RETURN @id

END