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

	INSERT INTO  feedbacks (MRN, ADM, EntryDatetime, ExitDatetime, Score, Performance, Outcome, AttachmentKeys, Notes, GraphVisible, SuggestedEdit, Username, ActivityDate) 
			VALUES (@mrn, @adm, @entry_dt, @exit_dt, @score, @performance, @outcome, @att_keys, @notes, @graph_visible, @suggested_edit, @username, @activity_date)
    SET @id=SCOPE_IDENTITY()
    RETURN @id

END