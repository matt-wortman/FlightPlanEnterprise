class TimelineStep():
    def __init__(self, locationStepID, location, riskStatus, entryDatetime, weight, locationNotes, riskNotes):
        self.locationStepID = locationStepID
        self.location = location
        self.riskStatus = riskStatus
        self.entryDatetime = entryDatetime
        self.weight = weight
        self.locationNotes = locationNotes
        self.riskNotes = riskNotes

    def editTimelineStep(self, locationStepID = '', location = '', riskStatus = '', entryDatetime = '', weight = '', locationNotes = '', riskNotes = ''):
        self.locationStepID = locationStepID if locationStepID  != '' else self.locationStepID
        self.location = location if location  != '' else self.location
        self.riskStatus = riskStatus if riskStatus != '' else self.riskStatus
        self.entryDatetime = entryDatetime if entryDatetime != '' else self.entryDatetime
        self.weight = weight if weight != '' else self.weight
        self.locationNotes = locationNotes if locationNotes != '' else self.locationNotes
        self.riskNotes = riskNotes if riskNotes != '' else self.riskNotes