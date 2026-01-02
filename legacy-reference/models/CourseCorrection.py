import datetime as dt

class CourseCorrection():
    def __init__(self, courseCorrectID, entryDatetime, detail, type, username):
        self.courseCorrectID = courseCorrectID
        self.entryDatetime = entryDatetime
        self.detail = detail
        self.type = type
        self.username = username
        self.activityDate = dt.datetime.now().replace(microsecond=0)

    def editCourseCorrection(self, entryDatetime = '', detail = '', type = '', username = ''):
        self.entryDatetime = entryDatetime if entryDatetime != '' else self.entryDatetime
        self.detail = detail if detail != '' else self.detail
        self.type = type if type != '' else self.type
        self.username =  username if username != '' else self.username
        self.activityDate = dt.datetime.now().replace(microsecond=0)
        self.updateDatabaseEntry()

    def updateDatabaseEntry(self):
        ### Add things here to update the course correction in the database
        return