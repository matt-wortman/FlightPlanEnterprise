from FpDatabase import buildSelect

grid_line_color= 'rgba(192, 192, 192, 50)'

maxImageResults = 10
maxCaseResults = 5
maxPatientResults = 10
maxDiagnosisShown = 6

riskStatuses = [
        {'category': 'Discharged', 'level': 1, 'values': ['discharged', 'discharge']},
        {'category': 'ACCU', 'level': 2, 'values': ['accu', 'pre-op']},
        {'category': 'Extubated', 'level': 3, 'values': ['extubated', 'cicu_extubated', 
                                                         'extubated_nippv', 'extubated_iNO', 'extubated / ra', 'extubated_hvs', 'extubated_tc',
                                                         'extubated / hfnc', 'extubated / cpap', 'extubated / nc', 'extubated / bipap',
                                                         'trach / home vent settings', 'trach collar'
                                                        ]},
        {'category': 'Intubated', 'level': 4, 'values': ['intubated', 'cicu_intubated', 
                                                         'intubated_hfov', 'intubated_ino', 'intubated_evs',
                                                         'intubated / conv vent', 'intubated / bivent', 'intubated / hfov',
                                                         'trach / vent settings'
                                                        ]},
        {'category': 'Procedure', 'level': 5, 'values': ['procedure']},
    ]

locationList = [
     {'category': 'ACCU',         
            'labels': ['ACCU'],              
            'heading': 'Arrival to ACCU',
            'line_color':  'rgb(90, 176, 196)',
            'ecmo_color': 'rgba(90, 176, 196, .5)',
            'annotation_color': 'rgb(10,80,155)',
        },
     {'category': 'CTOR',         
            'labels': ['CTOR', 'CVOR'],              
            'heading': 'Arrival to CTOR',
            'line_color':  'rgb(125, 91, 166)',
            'ecmo_color': 'rgba(125, 91, 166, .5)',
            'annotation_color': 'rgb(150,50,255)',
        },
     {'category': 'Preop',        
            'labels': ['Preop', 'Pre-op'],             
            'heading': 'Admission',
            'line_color':  'rgb(125, 91, 166)',
            'ecmo_color': 'rgba(125, 91, 166, .5)',
            'annotation_color': 'rgb(150,50,255)',
        },
    #  {'category': 'non-CV Unit',  
    #         'labels': ['non-CV Unit'],       
    #         'heading': 'non-CV Unit',
    #         'line_color':  'rgb(150,20,0)',
    #         'ecmo_color': 'rgba(215, 230, 180, .5)',
    #         'annotation_color': 'rgb(150,20,0)',
    #     },
     {'category': 'Cath',         
            'labels': ['CATH', 'Cath'],              
            'heading': 'Arrival to Cath',
            'line_color':  'rgb(248, 119, 149)',
            'ecmo_color': 'rgba(248, 119, 149, .5)',
            'annotation_color': 'rgb(255,0,255)',
        },
     {'category': 'CICU',         
            'labels': ['CICU'],              
            'heading': 'Arrival to CICU',
            'line_color':  'rgb(255, 150, 51)',
            'ecmo_color': 'rgba(255, 150, 51, .5)',
            'annotation_color': 'rgb(240,120,0)',
        },
     {'category': 'non-HI',       
            'labels': ['non-HI', 'NonHI-ACCU', 'NonHI-CICU', 'NonHI-CTOR'],            
            'heading': 'Arrival to Non HI Unit',
            'line_color':  'rgb(169, 169, 169)',
            'ecmo_color': 'rgba(169, 169, 169, .5)',
            'annotation_color': 'rgb(105,144,37)',
        },
     {'category': 'DC',           
            'labels': ['DC', 'Discharge', 'Discharged'],                
            'heading': 'Discharge',
            'line_color':  'rgb(78, 179, 74)',
            'ecmo_color': 'rgba(78, 179, 74, 0.5)',
            'annotation_color': 'rgb(0,150,70)',
        },
]

defaultLocationColor = {
    'locations' : ['DEFAULT'],
    'line_color':  'rgb(150,50,255)',
    'ecmo_color': 'rgb(150,50,255)',
    'annotation_color': 'rgb(150,50,255)',
}

combined_schema = {
    'table': ['patients', 'admissions'],
    'fields': [
        'patients.MRN', 'patients.LastName', 'patients.FirstName', 'patients.DOB', 'patients.sex',
        'patients.KeyDiagnosis', 'patients.Deceased', 'patients.Username', 'patients.ActivityDate',
        'admissions.ADM', 'admissions.ADMDATE', 'admissions.ReviewDate', 'admissions.CrossCheck',
        'admissions.Status', 'admissions.Thumbnail', 'admissions.Diagnosis', 'admissions.Interventions',
        'admissions.Username', 'admissions.ActivityDate'
    ]
}



patient_schema = { 
    'table': ['patients'],
    'fields': ['MRN', 'LastName', 'FirstName', 'DOB', 'sex', 'KeyDiagnosis', 'Deceased', 'Username', 'ActivityDate']
}
admission_schema = {
    'table': ['admissions'],
    'fields': ['MRN', 'ADM', 'ADMDATE',  'Status', 'Interventions', 'Diagnosis', 'ReviewDate', 'CrossCheck', 'Thumbnail', 'Username', 'ActivityDate'],
}
timeline_schema = {
    'table': ['location_steps ls', 'location_risks lr'],
    'fields': ['ls.MRN', 'ls.ADM', 'lr.LocationStepID', 'ls.Location', 'lr.Risk RiskStatus', 'lr.StartDatetime EntryDatetime', 'ls.Weight', 'ls.Notes LocationNotes', 'lr.Notes RiskNotes']
}		
location_steps_schema = {
    'table': ['location_steps'],
    'fields': ['MRN', 'ADM', 'LocationStepID', 'EntryDatetime', 'Location', 'Weight', 'Teams', 'Notes', 'Extra', 'Username', 'ActivityDate'],
}
location_risks_schema = {
    'table': ['location_risks'],
    'fields': ['MRN', 'ADM', 'LocationStepID', 'LocationRiskID', 'StartDatetime', 'Risk', 'Notes', 'Extra', 'Username', 'ActivityDate'],
}
bedside_procedures_schema = {
    'table': ['bedside_procedures'],
    'fields': ['MRN', 'ADM', 'LocationStepID', 'BedsideProcedureID', 'StartDatetime', 'EndDatetime', 'ProcedureType', 'Teams', 'Notes', 'Username', 'ActivityDate'],
}
continuous_therapy_schema = {
    'table': ['continuous_therapy'],
    'fields': ['MRN', 'ADM', 'CtID', 'EntryDatetime', 'Type', 'Status', 'AttachmentKeys', 'Notes', 'Username', 'ActivityDate'],
}		
annotation_schema = {
    'table': ['annotations'],
    'fields': ['MRN', 'ADM', 'AnnotaionID', 'EntryDatetime', 'annotation', 'type', 'href', 'SpecialNode', 'format', 'Username', 'ActivityDate'],
}		
feedbacks_schema = {
    'table': ['feedbacks'],
    'fields': ['MRN', 'ADM', 'FeedbackID', 'EntryDatetime', 'ExitDatetime', 'Score', 'Performance', 'Outcome', 'AttachmentKeys', 'Notes', 'GraphVisible', 'SuggestedEdit', 'Username', 'ActivityDate'],
}		
conferences_schema = {
    'table': ['conferences'],
    'fields': ['MRN', 'ADM', 'ConferenceID', 'EntryDatetime', 'Type', 'AttachmentKeys', 'ActionItems', 'Notes', 'Username', 'ActivityDate'],
}			
course_correction_schema = {
    'table': ['course_corrections'],
    'fields': ['MRN', 'ADM', 'course_correct_id', 'EntryDatetime', 'type', 'detail', 'Username', 'ActivityDate'],
}
attachments_schema = {
    'table': ['attachments'],
    'fields': ['MRN', 'ADM', 'AttachmentID', 'LocationStepID', 'LocationRiskID', 'storage_key', 'Description',
                'Filename', 'AttachmentType', 'ContentType', 'EntryDatetime', 'Thumbnail', 'Username', 'ActivityDate'],
}		
users_schema = {
    'table': ['users'],
    'fields': ['username', 'occupation', 'credentials', 'last_access'],
}		

buildSelect(patient_schema)
buildSelect(admission_schema)
buildSelect(timeline_schema)
buildSelect(location_steps_schema)
buildSelect(location_risks_schema)
buildSelect(bedside_procedures_schema)
buildSelect(continuous_therapy_schema)
buildSelect(annotation_schema)
buildSelect(feedbacks_schema)
buildSelect(conferences_schema)
buildSelect(course_correction_schema)
buildSelect(attachments_schema)
buildSelect(users_schema)

cath_interventionalist_team_items = [
    'Batlivala',
    'Hirsch',
    'Shahanavaz',
    'Other'
]

accu_attending_team_items = [
    'Critser',
    'Gaies',
    'Hanke',
    'Heydarian',
    'Marcuccio',
    'Moore',
    'Pater',
    'Spar',
    'Chin',
    'Czosek',
    'Lorts',
    'Ryan',
    'Wilmot',
    'Villa',
    'Anderson',
    'Knilans',
    'Other'
]

cicu_attending_team_items = [
    'Alten',
    'Benscoter',
    'Carlisle',
    'Chlebowski',
    'Cooper',
    'Gist',
    'Iliopoulos',
    'Koh',
    'Misfeldt',
    'Perry',
    'Other',
]

surgical_team_items = [
    'Lehenbauer',
    'Morales',
    'Winlaw',
    'Backer',
    'Ashfaq',
    'Wallen',
    'Other'
]

anesthesiologist_team_items = [
        'Other',
        'Spaeth, J.',
        'Kreeger, R.',
        'Kasman, N.',
        'Lin, E.',
        'Monteleone, M.',
        'Lam, J.',
        'Paquin, J.',
        'Varghese, J.',
        'Winograd Gomez, V.',
        'Chutipongtanate, A.',
        'Vu, D.',
        'Varghese, S',
        'Cuadrado, F'
]

respiratory_support_risks_cicu = [
    {'label': 'Intubated / Conv Vent', 'location': 'CICU', 'risk_level':4},
    {'label': 'Extubated / HFNC', 'location': 'CICU', 'risk_level':3},
    {'label': 'Extubated / NC', 'location': 'CICU', 'risk_level':3},
    {'label': 'Extubated / NC', 'location': 'NonHI-CICU', 'risk_level':3},
    {'label': 'Extubated / RA', 'location': 'CICU', 'risk_level':3},
    {'label': 'Extubated / CPAP', 'location': 'CICU', 'risk_level':3},
    {'label': 'Extubated / biPAP', 'location': 'CICU', 'risk_level':3},
    {'label': 'Intubated / BiVent', 'location': 'CICU', 'risk_level':4},
    {'label': 'Intubated / HFOV', 'location': 'CICU', 'risk_level':4},
    {'label': 'Trach / Vent Settings', 'location': 'CICU', 'risk_level':4},
    {'label': 'Trach / Home Vent Settings', 'location': 'CICU', 'risk_level':3},
    {'label': 'Trach Collar', 'location': 'CICU', 'risk_level':3},
]

respiratory_support_risks_accu = [
    {'label': 'Extubated / NC', 'location': 'ACCU', 'risk_level':2},
    {'label': 'Extubated / NC', 'location': 'NonHI-ACCU', 'risk_level':2},
    {'label': 'Extubated / RA', 'location': 'ACCU', 'risk_level':2},
    {'label': 'Extubated / HFNC', 'location': 'ACCU', 'risk_level':2},
    {'label': 'Extubated / biPAP', 'location': 'ACCU', 'risk_level':2},
    {'label': 'Extubated / CPAP', 'location': 'ACCU', 'risk_level':2},
    {'label': 'Trach / Home Vent Settings', 'location': 'ACCU', 'risk_level':2},
    {'label': 'Trach Collar', 'location': 'ACCU', 'risk_level':2},
]

bedside_surgical_procedures = [
    {'label': 'CT Surgery', 'risk_level':5},
    {'label': 'Gen Surg', 'risk_level':5},
    {'label': 'ENT', 'risk_level':5},
    {'label': 'Neuro', 'risk_level':5},
    {'label': 'Other', 'risk_level':5},
]

timeline_edit_modal_column_widths = [
    '25%',      # Location
    '15%',      # Info
    '35%',      # Date
    '35%',      # Time
    '5%',       # Expand Button
    '5%',       # Delete Button
]


user_operation_access = [
    {'operation': 'Content Admin', 'minimum_access_level': 4},
    {'operation': 'Flightplan Edit Mode', 'minimum_access_level': 3},
    {'operation': 'Add Patient', 'minimum_access_level': 4},
]
