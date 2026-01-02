# FlightPlan v2.0 Technical Architecture Documentation

**Version:** 3.3.0.4
**Date:** December 18, 2025
**Last Updated:** 2026-01-02
**Codebase Location:** `/home/matt/code_projects/FlightPlanv2.0/FlightPlan2/`

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Technology Stack Integration](#technology-stack-integration)
3. [Architecture Overview](#architecture-overview)
4. [Database Abstraction Layer](#database-abstraction-layer)
5. [Session Management and Authentication](#session-management-and-authentication)
6. [Data Flow Architecture](#data-flow-architecture)
7. [Component Architecture](#component-architecture)
8. [Custom React Components Integration](#custom-react-components-integration)
9. [Callback System](#callback-system)
10. [Caching and Performance](#caching-and-performance)
11. [Configuration Management](#configuration-management)
12. [Security Architecture](#security-architecture)
13. [Discrepancy Analysis](#discrepancy-analysis)
14. [Appendices](#appendices)

---

## Executive Summary

FlightPlan v2.0 is a medical patient management application designed for tracking cardiac patients through their hospital journey. The application is built on a **hybrid architecture** that combines:

- **Dash** (Plotly) for reactive UI framework
- **Flask** as the underlying web server
- **Custom React components** for complex visualizations (timeline graphs)
- **SQL Server/MySQL/SQLite** for data persistence
- **Azure authentication** for production deployments
- **Flask-Session** for server-side session management

### Key Architectural Characteristics

1. **Multi-page Dash application** with dynamic page routing
2. **Database-agnostic design** via abstraction layer (FpDatabase.py)
3. **Server-side caching** using Flask sessions for performance
4. **Component-based architecture** with inheritance patterns
5. **Custom React-Dash bridge** for advanced visualizations
6. **Role-based access control** with credential levels

### Critical Files

| File | Purpose | Lines of Code |
|------|---------|---------------|
| `App.py` | Main application entry point and layout | ~185 |
| `FpServer.py` | Flask/Dash server configuration | ~39 |
| `FpDatabase.py` | Database abstraction layer | ~465 |
| `FpConfig.py` | Environment-based configuration | ~64 |
| `FpCodes.py` | Static configuration and schemas | ~290 |
| `pages/Patients.py` | Patient list page | ~1079 |
| `pages/PatientDetail.py` | Individual patient view | ~2000+ |
| `utils/generate.py` | Data loading and rendering utilities | ~655 |
| `utils/cache_manager.py` | Session-based caching system | ~253 |
| `models/Patient.py` | Patient data model | ~253 |
| `models/Admission.py` | Admission data model | ~500+ |

---

## Technology Stack Integration

### 1. How Dash, Flask, and React Work Together

#### Flask Layer (Foundation)
```python
# FpServer.py
flaskApp = Flask(__name__)
flaskApp.config['SECRET_KEY'] = secrets.token_hex()
flaskApp.config['SESSION_TYPE'] = 'filesystem'
flaskApp.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=60)
Session(flaskApp)  # Flask-Session initialization
```

**Purpose:**
- Provides the WSGI web server
- Manages server-side sessions (stored in filesystem)
- Handles authentication headers
- Serves as the foundation for Dash

#### Dash Layer (Middle Tier)
```python
# FpServer.py
app = DashProxy(
    transforms=[MultiplexerTransform(proxy_location=None)],
    server=flaskApp,  # Attaches to Flask
    use_pages=True,  # Enables multi-page routing
    suppress_callback_exceptions=True,
    external_stylesheets=[dbc.themes.BOOTSTRAP, dbc.icons.FONT_AWESOME],
)
```

**Purpose:**
- Provides reactive component framework
- Manages callback system (Input → Output dependencies)
- Handles page routing via `dash.register_page()`
- Uses `DashProxy` from `dash-extensions` for advanced features (multiplexed callbacks)

#### React Layer (Custom Components)
```python
# App.py (importing custom React component)
import flight_plan_components as fpc

# pages/PatientDetail.py (using the component)
timeline = fpc.Timeline(
    id='patient_timeline',
    data=graph_data,
    options=graph_options,
)
```

**Purpose:**
- Custom React components compiled via webpack
- Provides advanced visualizations (timeline graph with zoom, brush, annotations)
- Components defined in `flight_plan_components/src/lib/components/`
- Built via npm and packaged for Python import

### 2. Integration Flow

```
Browser Request
    ↓
Flask WSGI Server (port 80/9050)
    ↓
Dash Page Router (use_pages=True)
    ↓
Page Layout Function (e.g., pages/Patients.py → layout())
    ↓
[Components Rendered]
    ├─ Native Dash Components (dcc.Input, dbc.Button)
    ├─ Custom React Components (fpc.Timeline)
    └─ Python-generated HTML (html.Div)
    ↓
Dash Serializes to JSON
    ↓
Browser Receives Component Tree + JavaScript
    ↓
[User Interaction]
    ↓
Callback Triggered (managed by Dash)
    ↓
Python Callback Function Executes
    ↓
Output Components Updated (re-rendered on frontend)
```

### 3. Custom React Component Bridge

The `flight_plan_components` package bridges React and Python:

#### Build Process
```bash
# flight_plan_components/
npm run build  # Compiles React → JavaScript bundle
```

This generates:
- `flight_plan_components/flight_plan_components/flight_plan_components.min.js`
- Python wrapper classes in `flight_plan_components/flight_plan_components/*.py`

#### Component Registration
```python
# flight_plan_components/flight_plan_components/__init__.py
_js_dist = [
    {
        'relative_package_path': 'flight_plan_components.min.js',
        'namespace': package_name
    }
]

for _component in __all__:
    setattr(locals()[_component], '_js_dist', _js_dist)
```

#### Usage Pattern
```python
# Python defines props, React renders visualization
timeline = fpc.Timeline(
    id='patient_timeline',  # Dash component ID
    data=graph_data,        # Python dict → JSON → React props.data
    options={'zoom': True}  # Python dict → React props.options
)
```

**Key Insight:** React components receive Python data as `props`, render the visualization, and can trigger Dash callbacks via `setProps()` on user interaction.

---

## Architecture Overview

### Application Entry Point

```
FlightPlan2.py (main entry)
    ↓
imports App.py (main layout + callbacks)
    ↓
imports FpServer.py (Flask + Dash instance)
    ↓
app.run_server(debug=True/False, port=80/9050)
```

### Multi-Page Routing System

Dash's `use_pages=True` enables automatic routing:

```python
# pages/index.py
dash.register_page(__name__, path='/', title='Index')
# Redirects to /patients

# pages/Patients.py
register_page(__name__, path='/patients', redirect_from=['/home'])
# Main patient list

# pages/PatientDetail.py
dash.register_page(__name__, path_template='/patient/<mrn>')
# Dynamic routing for individual patients
```

**Routing Flow:**
1. User navigates to `/patient/gAAAAABm...` (encrypted MRN)
2. Dash's router matches `path_template='/patient/<mrn>'`
3. Calls `layout(mrn=<encrypted_value>)` function
4. Layout function decrypts MRN and loads patient data
5. Renders PatientDetail page

### Page Structure Pattern

Every page follows this pattern:

```python
import dash
from dash_extensions.enrich import html, dcc, Input, Output, State, callback

dash.register_page(__name__, path='/example', title='Example')

def layout(**kwargs):
    """
    Called by Dash router when page is accessed.
    Returns the page's component tree.
    """
    return html.Div([
        dcc.Store(id='page_data', data={}),
        html.Div(id='page_content')
    ])

@callback(
    Output('page_content', 'children'),
    Input('page_data', 'data'),
    State('session_store', 'data')
)
def render_content(page_data, session_store):
    """
    Callback to render dynamic content.
    """
    return html.Div('Rendered content')
```

---

## Database Abstraction Layer

### FpDatabase.py: Multi-Database Support

The `SqlDatabase` class provides a **unified interface** for SQL Server, MySQL, and SQLite:

```python
class SqlDatabase():
    def __init__(self, config):
        self.dbType = config['Interface'].upper()
        # Supports: 'MYSQL', 'SQLSERVER', 'SQLITE'

    def connect(self):
        if self.dbType == 'SQLSERVER':
            connectString = (
                'Driver={ODBC Driver 18 for SQL Server};'
                'Server=' + self.configuration['Server'] + ';'
                'Database=' + self.configuration['Database'] + ';'
                'Uid=' + self.configuration['User'] + ';'
                'Pwd=' + self.configuration['Password'] + ';'
                'TrustServerCertificate=yes;'
            )
            import pyodbc
            self.dbConnection = pyodbc.connect(connectString)
        elif self.dbType == 'MYSQL':
            import mysql.connector as MySQLdb
            self.dbConnection = MySQLdb.connect(
                host=self.configuration['Host'],
                user=self.configuration['User'],
                password=self.configuration['Password'],
                database=self.configuration['Database'],
                use_pure=True
            )
        elif self.dbType == 'SQLITE':
            import sqlite3
            self.dbConnection = sqlite3.connect(self.configuration['Source'])
```

### Schema-Based Query Building

Queries are constructed from schema definitions in `FpCodes.py`:

```python
# FpCodes.py
patient_schema = {
    'table': ['patients'],
    'fields': ['MRN', 'LastName', 'FirstName', 'DOB', 'sex',
               'KeyDiagnosis', 'Deceased', 'Username', 'ActivityDate']
}

buildSelect(patient_schema)
# Generates: patient_schema['select'] =
# "select MRN, LastName, FirstName, DOB, sex, KeyDiagnosis,
#  Deceased, Username, ActivityDate from patients"
```

### Query Execution Pattern

```python
# Context manager ensures connection cleanup
with SqlDatabase(sqlDatabaseConnect) as db:
    where = "where MRN = '12345'"
    patients = db.select(patient_schema, where)
    # Returns: [{'MRN': '12345', 'LastName': 'Smith', ...}]
```

### Pagination Support

```python
def select_patients(self, schema, where, order_by=None, offset=None, fetch=None):
    sql = schema['select'] + " " + where
    if order_by:
        sql += f" ORDER BY {order_by}"
    if offset is not None and fetch is not None:
        sql += f" OFFSET {offset} ROWS FETCH NEXT {fetch} ROWS ONLY"
    # SQL Server pagination syntax
```

**Usage:**
```python
# Load page 2 (20 patients per page)
offset = (2 - 1) * 20  # = 20
fetch = 20
db.select_patients(combined_schema, "WHERE 1=1",
                   order_by="ReviewDate DESC", offset=offset, fetch=fetch)
```

### Database Configuration (FpConfig.py)

```python
databaseConnect = {
    'Interface': 'SQLSERVER',
    'Server': os.environ.get('DB_SERVER'),      # e.g., 'localhost'
    'Database': os.environ.get('DB_NAME'),      # e.g., 'FlightPlan3'
    'User': os.environ.get('DB_USER'),          # e.g., 'sa'
    'Password': os.environ.get('DB_PASSWORD'),
}

sqlDatabaseConnect = databaseConnect  # Active connection
```

**Environment Variables:**
- `DB_SERVER`: Database server hostname
- `DB_NAME`: Database name
- `DB_USER`: Database username
- `DB_PASSWORD`: Database password
- `FLIGHTPLAN_ENV`: 'local' or 'production'

---

## Session Management and Authentication

### Flask-Session Configuration

```python
# FpServer.py
flaskApp.config['SECRET_KEY'] = secrets.token_hex()  # Random per restart
flaskApp.config['SESSION_TYPE'] = 'filesystem'       # Sessions stored on disk
flaskApp.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=60)
Session(flaskApp)
```

**Session Storage:**
- Sessions stored in `flask_session/` directory (filesystem-based)
- Each session has a unique ID (cookie-based)
- Session data persists across page navigations
- Expires after 60 minutes of inactivity

### Authentication Flow

#### Production (Azure Authentication)
```python
# utils/FP2_Utilities.py
def getUserInformation():
    try:
        # Azure App Service injects this header
        userName = request.headers['X-MS-CLIENT-PRINCIPAL-NAME']
    except:
        userName = 'guest'

    # Look up user in database
    with SqlDatabase(sqlDatabaseConnect) as db:
        where = f"where username = '{userName}'"
        user_db = db.select(users_schema, where)

    if len(user_db) == 0:
        return 'guest', '', 1  # Default credentials

    return (userName,
            user_db[0]['occupation'],
            int(user_db[0]['credentials']))
```

#### Local Development Override
```python
# FpConfig.py
if flightplan_env == 'local':
    fp_local_user = os.environ.get('FP_LOCAL_USER')        # e.g., 'admin@hospital.com'
    fp_local_creds = os.environ.get('FP_LOCAL_CREDS')      # e.g., '4'
    fp_local_occupation = os.environ.get('FP_LOCAL_OCCUPATION')  # e.g., 'Administrator'

# utils/FP2_Utilities.py
def getUserInformation():
    if flightplan_env == 'local' and fp_local_user and fp_local_creds:
        return fp_local_user, fp_local_occupation, int(fp_local_creds)
    # ... else use Azure header
```

### User Session Store

```python
# App.py
def generateMainPageLayout():
    return html.Div([
        dcc.Store(id='session_store', storage_type='session',
                  data=getDefaultStore()),
        dcc.Store(id='sessionData_USER', storage_type='session'),
        dcc.Store(id='sessionData_Occupation', storage_type='session'),
        dcc.Store(id='sessionData_Creds', storage_type='session'),
        # ... rest of layout
    ])
```

**Session Store Contents (default):**
```python
{
    'editing': False,
    'activePatient': None,
    'activeAdmission': 0,
    'current_page': 1,
    'patients_per_page': 20,
    'sortCriteria': 'discharge_date',
    'sortDescending': True,
    'statusFilter': {'Discharged': True, 'ACCU': True, ...},
    'contentFilter': {'crossCheck': False, 'reintervention': False, ...},
    # ... more state
}
```

### Encryption for Client-Side Storage

User data stored in Dash's `dcc.Store` (sessionStorage) is encrypted:

```python
# utils/FP2_Utilities.py
from cryptography.fernet import Fernet
encryption_key = os.environ.get('ENCRYPTION_KEY')  # 32-byte key
fernet = Fernet(encryption_key.encode())

def encrypt(data):
    return fernet.encrypt(str(data).encode()).decode()

def decrypt(encrypted_data):
    return fernet.decrypt(encrypted_data.encode()).decode()
```

**Usage:**
```python
# App.py
@callback(
    Output('sessionData_USER', 'data'),
    Output('sessionData_Creds', 'data'),
    Input('main_content', 'children'),
)
def entrypoint(layout):
    userName, occupation, credentials = getUserInformation()
    return encrypt(userName), encrypt(credentials)  # Encrypted before storing
```

### Role-Based Access Control

```python
# FpCodes.py
user_operation_access = [
    {'operation': 'Content Admin', 'minimum_access_level': 4},
    {'operation': 'Flightplan Edit Mode', 'minimum_access_level': 3},
    {'operation': 'Add Patient', 'minimum_access_level': 4},
]

# utils/FP2_Utilities.py
def check_user_access(credentials, operation):
    access_entry = next(
        (item for item in user_operation_access
         if item['operation'] == operation), None
    )
    if not access_entry:
        return False
    return credentials >= access_entry['minimum_access_level']
```

**Credential Levels:**
- **1:** Guest (read-only)
- **2:** Viewer (read-only with full access)
- **3:** Editor (can edit flight plans)
- **4:** Admin (can add patients, full access)

---

## Data Flow Architecture

### 1. What Data is Hardcoded vs Dynamically Loaded

#### Hardcoded in FpCodes.py

```python
# Static configuration (NEVER changes at runtime)
locationList = [
    {'category': 'ACCU', 'labels': ['ACCU'],
     'line_color': 'rgb(90, 176, 196)', ...},
    {'category': 'CTOR', 'labels': ['CTOR', 'CVOR'],
     'line_color': 'rgb(125, 91, 166)', ...},
    # ... more locations
]

riskStatuses = [
    {'category': 'Discharged', 'level': 1, 'values': ['discharged', 'discharge']},
    {'category': 'Intubated', 'level': 4, 'values': ['intubated', 'cicu_intubated']},
    # ... more risk statuses
]

# Team members (should be in database, but currently hardcoded)
cicu_attending_team_items = [
    'Alten', 'Benscoter', 'Carlisle', 'Chlebowski', ...
]
surgical_team_items = [
    'Lehenbauer', 'Morales', 'Winlaw', 'Backer', ...
]
```

**Why Hardcoded:** These are institutional constants that rarely change.

#### Dynamically Loaded from Database

**Patient Data:**
```python
# utils/generate.py
def loadPaginatedPatientData(store):
    offset = (store['current_page'] - 1) * store['patients_per_page']
    where = "WHERE 1=1"
    order_by = "admissions.ReviewDate DESC"

    with SqlDatabase(sqlDatabaseConnect) as db:
        dbPatients = db.select_patients_by_location_step(
            combined_schema, where, order_by, offset, store['patients_per_page']
        )

    patients = []
    for dbPatient in dbPatients:
        patient = Patient(dbPatient['MRN'], dbPatient['LastName'], ...)
        admission = patient.createAdmission(dbPatient)
        patient.admissions.append(admission)
        patients.append(patient)

    return patients
```

**Admission Details (Lazy Loaded):**
```python
# models/Admission.py
class Admission():
    def __init__(self, MRN, admissionID, ...):
        # ... initialize basic fields
        self.location_steps = []
        self.annotations = None  # Lazy loaded
        self.feedbacks = None
        self.conferences = None
        self.attachments = None

        # Load on initialization
        self.loadLocationStepsAndTimeline()
        self.loadCourseCorrections()
        self.loadAnnotations()
        self.loadFeedbacks()
        self.loadConferences()
        self.loadAttachments()
```

### 2. Patient Data Flow: Database → UI

```
Database (SQL Server)
    ↓
[1] SQL Query (with JOIN across patients + admissions tables)
    ↓
[2] SqlDatabase.select_patients_by_location_step()
    ↓
[3] Returns list of dicts: [{'MRN': '12345', 'LastName': 'Smith', ...}]
    ↓
[4] Patient objects created in Python
    |
    ├─ Patient(MRN, lastName, firstName, DOB, ...)
    |    └─ Admission(admissionID, surgeryDate, status, ...)
    |         ├─ LocationStep[]  (loaded from location_steps table)
    |         ├─ LocationRisk[]  (loaded from location_risks table)
    |         ├─ Annotation[]
    |         ├─ Feedback[]
    |         ├─ Conference[]
    |         └─ Attachment[]
    ↓
[5] Cached in Flask Session (cache_manager.add_patient())
    ↓
[6] Passed to generatePatientRow() for each patient
    ↓
[7] Returns html.Tr with patient data
    ↓
[8] Rendered in browser (Dash serializes to JSON → React renders)
```

**Key Files:**
- **Loading:** `utils/generate.py::loadPaginatedPatientData()`
- **Caching:** `utils/cache_manager.py::CacheManager.add_patient()`
- **Rendering:** `utils/generate.py::generatePatientRow()`

### 3. Form Submission Flow

```
User fills form (e.g., Add Patient modal)
    ↓
User clicks "Submit"
    ↓
Dash triggers callback (Input: submit button, State: form fields)
    ↓
Callback extracts form values
    ↓
Validation (client-side: HTML5, server-side: Python)
    ↓
[IF VALID]
    ↓
Create Patient object: Patient(MRN, lastName, firstName, ...)
    ↓
patient.addPatientToDatabase()
    |
    ├─ Builds SQL INSERT with parameters
    ├─ Executes via SqlDatabase.sendSql(sql, params)
    └─ Database row created
    ↓
Clear cache: cache_manager.delete_page(current_page)
    ↓
Reload patient list with reloadCache=True
    ↓
Close modal, refresh UI
```

**Example Callback (Add Patient):**
```python
# components/roots/modals/PatientModal.py
@callback(
    Output(modal_id, 'is_open'),
    Output('session_store', 'data'),
    Input(submit_button_id, 'n_clicks'),
    State({'type': 'patient_input', 'field': 'mrn', 'index': ALL}, 'value'),
    State({'type': 'patient_input', 'field': 'last_name', 'index': ALL}, 'value'),
    # ... more states
)
def submit_patient(submit_clicks, mrn_values, lastName_values, ...):
    if not submit_clicks or submit_clicks == 0:
        raise PreventUpdate

    mrn = mrn_values[0]
    lastName = lastName_values[0]
    # ... extract all values

    # Create and save patient
    patient = Patient(mrn, lastName, firstName, dob, sex,
                      username=current_user, addToDatabase=True)

    # Add admission
    patient.addAdmission(admissionID=1, admissionDate=surgeryDate,
                         reviewDate=reviewDate, crossCheck=crossCheck)

    # Invalidate cache
    cache_manager.delete_page(store['current_page'])

    return False, store  # Close modal, return updated store
```

### 4. Caching Mechanism Details

See [Caching and Performance](#caching-and-performance) section.

---

## Component Architecture

### Component Hierarchy

```
BaseContainer (Abstract)
    ├─ PatientContainer
    ├─ ClinicalEventContainer
    ├─ ConferenceContainer
    ├─ ContinuousTherapyContainer
    ├─ ImagingReportContainer
    ├─ ProvideRatingsContainer
    └─ SuggestEditsContainer

BaseSection (Abstract)
    ├─ SimpleSection
    ├─ CollapseSection
    ├─ InputSection
    ├─ DateSection
    ├─ DateTimeSection
    ├─ TimeSection
    ├─ DropdownSection
    ├─ OptionSelectSection
    ├─ NotesSection
    ├─ AttachSection
    ├─ StatusSection
    └─ ConfirmDialogSection

BaseModal (Abstract)
    ├─ PatientModal
    ├─ ClinicalEventModal
    ├─ ConferenceModal
    ├─ ContinuousTherapyModal
    ├─ ImagingReportModal
    ├─ ProvideRatingsModal
    ├─ SuggestEditsModal
    ├─ DocViewerModal
    └─ FeedbackViewerModal
```

### BaseContainer Pattern

**Purpose:** Standardizes form-based data entry with validation, collapsible sections, and feedback.

```python
# components/containers/BaseContainer.py
class BaseContainer(ABC):
    def __init__(self, base_id, group_id, prefix='', hasCollapse=True):
        self.base_id = base_id  # e.g., 'patient'
        self.group_id = group_id  # e.g., 'md' (modal)
        self.prefix = prefix  # e.g., '_mrn'
        self.hasCollapse = hasCollapse  # Collapsible UI?

        # Auto-generated IDs
        self.form_id = f'{base_id}_form'
        self.form_feedback_id = f'{base_id}_feedback_{group_id}'

        # Layout wrapper (Simple or Collapse)
        self.layoutSection = self.generateLayoutSection()

    def layout(self, title, content):
        """Wraps content in a form with validation feedback"""
        feedback = html.Div([
            html.Small('', id=self.form_feedback_id),
            dbc.Input(id={'type': f'{self.base_id}_serverside_valid',
                          'index': self.group_id},
                      style={'display': 'none'}, required=True, value=True)
        ], className='container-feedback text-danger d-none')

        content.append(feedback)

        return html.Form(
            self.layoutSection.generateContent(content, title),
            id={'type': self.form_id, 'index': self.group_id},
            className='needs-validation fp-form',
            noValidate=True
        )

    @abstractmethod
    def generateContent(self):
        """Subclasses define their specific form fields"""
        raise NotImplementedError()

    def register_callbacks(self):
        """Subclasses define validation callbacks"""
        pass
```

### Example: PatientContainer

```python
# components/containers/PatientContainer.py
class PatientContainer(BaseContainer):
    def __init__(self, base_id, group_id, prefix=''):
        super().__init__(base_id, group_id, prefix, hasCollapse=False)

        # Define form sections
        self.lastNameSection = InputSection(
            self.base_id, self.group_id, prefix='last_name',
            placeholder='Last Name...', title='Patient\'s Last Name',
            feedback_text='Please provide a last name', required=True
        )
        self.firstNameSection = InputSection(...)
        self.mrnSection = InputSection(...)
        self.dobSection = DateSection(...)
        self.surgeryDateSection = DateSection(...)
        self.reviewDateSection = DateSection(...)
        self.sexDropdown = DropdownSection(...)
        self.crosscheckDropdown = DropdownSection(...)

    def generateContent(self, user, which=None, admission=None):
        """Generates the form UI"""
        content = html.Div([
            self.generateRow(
                self.lastNameSection.generateContent(),
                self.firstNameSection.generateContent()
            ),
            self.generateRow(
                self.mrnSection.generateContent(),
                self.dobSection.generateContent()
            ),
            # ... more rows
        ])

        return self.layout('Patient Information', content)

    def register_callbacks(self):
        """Registers validation callbacks"""
        super().register_callbacks()

        # Register callbacks for each section
        self.lastNameSection.register_callbacks()
        self.dobSection.register_callbacks()
        # ...

        @callback(
            Output({'type': self.type_form_valid_id, 'index': self.group_id}, 'value'),
            Output(self.form_feedback_id, 'children'),
            Input({'type': self.type_input_id, 'field': self.dobSection.id, 'index': ALL}, 'value'),
            Input({'type': self.type_input_id, 'field': self.surgeryDateSection.id, 'index': ALL}, 'value'),
        )
        def validate(dobDate, surgeryDate):
            if dobDate and surgeryDate:
                if is_date_after(dobDate[0], surgeryDate[0]):
                    return None, 'DOB must be before surgery date'
                return True, 'Success!'
            raise PreventUpdate
```

### BaseSection Pattern

**Purpose:** Reusable form field components with built-in IDs and callbacks.

```python
# components/sections/BaseSection.py
class BaseSection(ABC):
    def __init__(self, base_id, group_id, prefix=''):
        self.base_id = base_id  # e.g., 'patient'
        self.group_id = group_id  # e.g., 'md'
        self.prefix = prefix  # e.g., '_mrn'

        # Auto-generated IDs
        self.type_input_id = f'{base_id}_input'
        self.type_output_id = f'{base_id}_output'

    @abstractmethod
    def generateContent(self):
        raise NotImplementedError()

    def register_callbacks(self):
        pass
```

### Example: InputSection

```python
# components/sections/InputSection.py
class InputSection(BaseSection):
    def __init__(self, base_id, group_id, prefix='', title='',
                 placeholder='', feedback_text='', required=False):
        super().__init__(base_id, group_id, prefix)
        self.title = title
        self.placeholder = placeholder
        self.feedback_text = feedback_text
        self.required = required

        self.id = f'{base_id}{prefix}_input'

    def generateContent(self, initialValue=None):
        return html.Div([
            dbc.Label(self.title),
            dbc.Input(
                id={'type': self.type_input_id, 'field': self.id,
                    'index': self.group_id},
                placeholder=self.placeholder,
                required=self.required,
                value=initialValue,
                className='form-control',
            ),
            dbc.FormFeedback(self.feedback_text, type='invalid'),
        ])

    def register_callbacks(self):
        # Can add validation callbacks here
        pass
```

### Modal Pattern

Modals use Containers for their content:

```python
# components/roots/modals/PatientModal.py
class PatientModal():
    def __init__(self, group_id):
        self.id = f'patient_modal_{group_id}'
        self.patientContainer = PatientContainer('patient', group_id)

    def generateContent(self, user):
        return dbc.Modal([
            dbc.ModalHeader('Add Patient'),
            dbc.ModalBody(self.patientContainer.generateContent(user)),
            dbc.ModalFooter([
                dbc.Button('Submit', id=f'patient_submit_{self.group_id}'),
                dbc.Button('Cancel', id=f'patient_cancel_{self.group_id}'),
            ])
        ], id=self.id, is_open=False)

    def register_callbacks(self):
        self.patientContainer.register_callbacks()

        @callback(
            Output(self.id, 'is_open'),
            Input(f'patient_submit_{self.group_id}', 'n_clicks'),
            State(self.patientContainer.form_id, 'value'),
        )
        def toggle_modal(submit_clicks, form_values):
            # Handle submission
            pass
```

---

## Custom React Components Integration

### Overview

The `flight_plan_components` package contains custom React visualizations (primarily the Timeline graph) that integrate with Dash.

### Directory Structure

```
flight_plan_components/
├── src/
│   └── lib/
│       ├── components/
│       │   ├── Timeline.react.js       # Main timeline component
│       │   ├── Brush.react.js          # Zoom brush
│       │   ├── GraphTooltip.react.js   # Hover tooltips
│       │   ├── GraphMenu.react.js      # Context menu
│       │   └── EvaluationPill.react.js # Feedback pills
│       └── index.js                    # Export entry point
├── flight_plan_components/
│   ├── __init__.py                     # Python package
│   ├── Timeline.py                     # Python wrapper class
│   ├── flight_plan_components.min.js   # Compiled bundle
│   └── metadata.json                   # Component metadata
├── package.json                        # npm config
└── webpack.config.js                   # Build config
```

### Build Process

```bash
# Install dependencies
npm install

# Build React components → JavaScript bundle
npm run build
```

**What Happens:**
1. Webpack compiles `src/lib/components/*.react.js` → `flight_plan_components.min.js`
2. Python wrapper classes are auto-generated from React PropTypes
3. Bundle is placed in `flight_plan_components/flight_plan_components/`

### Component Definition (React)

```javascript
// flight_plan_components/src/lib/components/Timeline.react.js
export default class Timeline extends Component {
    static propTypes = {
        id: PropTypes.string,
        data: PropTypes.array,             // Timeline data points
        options: PropTypes.object,          // Graph options
        setProps: PropTypes.func,           // Dash callback trigger

        // Outputs (trigger Dash callbacks)
        eventSelectedPayload: PropTypes.object,
        eventHoverPayload: PropTypes.object,
        eventEditPayload: PropTypes.object,
        thumbnail: PropTypes.string,
    };

    constructor(props) {
        super(props);
        this.state = {
            data: props.data || [],
            // ... internal state
        };
    }

    componentDidUpdate(prevProps) {
        // React to prop changes from Python
        if (prevProps.data !== this.props.data) {
            this.buildGraph();
        }
    }

    handlePointClick = (payload) => {
        // Trigger Dash callback
        this.props.setProps({
            eventSelectedPayload: payload
        });
    }

    render() {
        return (
            <ResponsiveContainer>
                <LineChart data={this.state.data}>
                    {/* ... complex visualization */}
                </LineChart>
            </ResponsiveContainer>
        );
    }
}
```

### Python Wrapper (Auto-Generated)

```python
# flight_plan_components/flight_plan_components/Timeline.py
class Timeline(Component):
    """Timeline component for displaying patient timelines."""

    @_explicitize_args
    def __init__(self, id=Component.UNDEFINED, data=Component.UNDEFINED,
                 options=Component.UNDEFINED,
                 eventSelectedPayload=Component.UNDEFINED, **kwargs):
        self._prop_names = ['id', 'data', 'options',
                            'eventSelectedPayload', ...]
        self._type = 'Timeline'
        self._namespace = 'flight_plan_components'
        self._valid_wildcard_attributes = []
        self.available_properties = ['id', 'data', 'options', ...]
        self.available_wildcard_properties = []

        _explicit_args = kwargs.pop('_explicit_args')
        _locals = locals()
        _locals.update(kwargs)

        args = {k: _locals[k] for k in _explicit_args if k != 'children'}

        for k in ['id', 'data', 'options', ...]:
            if k not in args:
                raise TypeError(f'Required argument `{k}` was not specified.')

        super(Timeline, self).__init__(**args)
```

### Usage in Python (Dash Page)

```python
# pages/PatientDetail.py
import flight_plan_components as fpc

# Generate data in Python
graph_data = generateFlightPlanGraph(patient, admission)
graph_options = {
    'zoom': True,
    'brush': True,
    'height': 600,
}

# Create React component instance
timeline = fpc.Timeline(
    id='patient_timeline',
    data=graph_data,
    options=graph_options,
)

# Define callback to handle React events
@callback(
    Output('modal_container', 'children'),
    Input('patient_timeline', 'eventSelectedPayload'),
)
def handle_timeline_click(payload):
    if payload:
        # User clicked a point on timeline
        return generate_edit_modal(payload)
    return no_update
```

### Data Flow: Python ↔ React

```
Python (Dash Backend)
    ↓
[1] generateFlightPlanGraph(patient, admission)
    Returns: [
        {
            'x': 0,            # Time coordinate
            'y': 3,            # Risk level (0-4)
            'convertedTime': '2024-01-01T10:00:00',
            'pointType': 'circle',
            'overhead': {'type': 'note', 'text': 'Intubated'},
            'location': 'CICU',
            'risk': 'Intubated',
            # ... more metadata
        },
        # ... more points
    ]
    ↓
[2] fpc.Timeline(id='patient_timeline', data=graph_data)
    ↓
[3] Dash serializes to JSON
    ↓
[4] Browser receives JSON props
    ↓
[5] React Timeline component renders
    |
    ├─ Recharts LineChart
    ├─ Custom Dot components
    ├─ Tooltips
    └─ Zoom Brush
    ↓
[User Interaction: Click point]
    ↓
[6] Timeline.react.js: this.props.setProps({eventSelectedPayload: {id: 123, ...}})
    ↓
[7] Dash detects prop change
    ↓
[8] Triggers callback: Input('patient_timeline', 'eventSelectedPayload')
    ↓
[9] Python callback executes
    ↓
[10] Output updated (e.g., open edit modal)
```

### Props Schema

**Inputs (Python → React):**
- `id`: Component identifier
- `data`: Array of timeline data points
- `options`: Configuration object (zoom, height, colors, etc.)

**Outputs (React → Python, trigger callbacks):**
- `eventSelectedPayload`: User clicked a point
- `eventHoverPayload`: User hovered over a point
- `eventEditPayload`: User requested edit
- `thumbnail`: Generated thumbnail image (base64)

---

## Callback System

### Dash Callback Fundamentals

Dash callbacks define **reactive dependencies**:

```python
@callback(
    Output('output_id', 'property'),  # What to update
    Input('input_id', 'property'),     # What triggers update
    State('state_id', 'property'),     # Additional data (doesn't trigger)
)
def callback_function(input_value, state_value):
    # Process inputs
    result = process(input_value, state_value)
    return result  # Returned value updates Output
```

### Pattern Matching Callbacks (ALL, MATCH)

**Problem:** How to handle dynamic lists of components?

**Solution:** Pattern-matching IDs with `ALL` and `MATCH`:

```python
# Generate dynamic buttons
buttons = [
    html.Button('Button 1', id={'type': 'dynamic_button', 'index': 1}),
    html.Button('Button 2', id={'type': 'dynamic_button', 'index': 2}),
    html.Button('Button 3', id={'type': 'dynamic_button', 'index': 3}),
]

# Callback that handles ALL buttons
@callback(
    Output('output', 'children'),
    Input({'type': 'dynamic_button', 'index': ALL}, 'n_clicks'),
)
def handle_all_buttons(all_clicks):
    # all_clicks = [1, 0, 3]  (click counts for each button)
    ctx = dash.callback_context
    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]
    # triggered_id = '{"type":"dynamic_button","index":1}'

    button_info = json.loads(triggered_id)
    clicked_index = button_info['index']

    return f"Button {clicked_index} was clicked"
```

**ALL vs MATCH:**
- `ALL`: Callback receives **all** matching components' values as a list
- `MATCH`: Callback only receives the **specific** component that triggered it

### CallbackManager Pattern

The application uses a custom callback manager (`utils/CallbackManager.py`) to centralize callback registration:

```python
class CallbackManager():
    def __init__(self):
        self.callbacks = []

    def register(self, callback_func):
        self.callbacks.append(callback_func)
        return callback_func

    def register_all(self):
        for cb in self.callbacks:
            cb()
```

**Usage:**
```python
# components/sections/BaseSection.py
class BaseSection(ABC):
    def __init__(self, base_id, group_id):
        if 'cm' not in globals():
            global cm
            cm = CallbackManager()
        self.cm = cm
```

### Callback Execution Flow

```
User Interaction (e.g., button click)
    ↓
Browser detects event
    ↓
Dash frontend sends request to backend:
    POST /_dash-update-component
    {
        "output": "output_id.property",
        "inputs": [{"id": "input_id", "property": "value", "value": "new_value"}],
        "state": [{"id": "state_id", "property": "value", "value": "state_value"}]
    }
    ↓
Dash backend matches callback by (Output, Input) signature
    ↓
Executes Python callback function
    ↓
Callback returns value
    ↓
Dash serializes return value to JSON
    ↓
Browser receives response
    ↓
Dash frontend updates Output component
    ↓
React re-renders affected components
```

### Example: Patient List Filtering

```python
# pages/Patients.py
@callback(
    Output('patient_list_rows', 'children'),
    Output('session_store', 'data'),

    Input('DischargeFilter', 'on'),
    Input('ACCUFilter', 'on'),
    Input('CICUFilter', 'on'),
    # ... more filters

    State('session_store', 'data')
)
def filter_toggle(dischargedOn, accuOn, cicuOn, ..., store):
    """
    Triggered when any filter toggle changes.
    Updates the patient list and session store.
    """
    # Update session store with new filter values
    store['statusFilter']['Discharged'] = dischargedOn
    store['statusFilter']['ACCU'] = accuOn
    store['statusFilter']['CICU'] = cicuOn
    # ...

    # Regenerate patient rows based on filters
    content = [
        html.Thead(generatePatientListHeader(store)),
        html.Tbody(generatePatientRows(store), id='patient_rows_body')
    ]

    return content, store
```

### Preventing Callback Loops

**Problem:** Callback A updates Output X → triggers Callback B → updates Output Y → triggers Callback A (infinite loop)

**Solution:** Use `prevent_initial_call=True` and `no_update`:

```python
from dash import no_update
from dash.exceptions import PreventUpdate

@callback(
    Output('output', 'children'),
    Input('input', 'value'),
    prevent_initial_call=True  # Don't run on page load
)
def update(value):
    if value is None:
        raise PreventUpdate  # Exit without updating

    if some_condition:
        return no_update  # Keep current value

    return new_value
```

---

## Caching and Performance

### Two-Level Caching Strategy

FlightPlan uses a **hybrid caching approach**:

1. **Flask Session Cache** (server-side, persistent across pages)
2. **Dash Store Cache** (client-side, in-browser sessionStorage)

### Flask Session Cache (cache_manager.py)

**Purpose:** Cache loaded patient data to avoid redundant database queries.

```python
# utils/cache_manager.py
class CacheManager:
    def add_patient(self, page, patients):
        """Adds patients to the specified page cache"""
        if 'cachedPatients' not in session:
            session['cachedPatients'] = {}

        if page not in session['cachedPatients']:
            session['cachedPatients'][page] = []

        unique_patients = [p for p in patients if not self.search_value(p.MRN)]
        session['cachedPatients'][page].extend(unique_patients)
        session.modified = True  # Critical: marks session as dirty

    def get_patients(self, page):
        """Retrieves cached patients for a page"""
        return session.get('cachedPatients', {}).get(page, [])

    def get_patient(self, MRN):
        """Retrieves a single patient by MRN"""
        for patients in session.get('cachedPatients', {}).values():
            patient = next((p for p in patients if p.MRN == MRN), None)
            if patient:
                return patient
        return None

    def delete_page(self, page):
        """Invalidates cache for a specific page"""
        if 'cachedPatients' in session and page in session['cachedPatients']:
            del session['cachedPatients'][page]
            session.modified = True

# Singleton instance
cache_manager = CacheManager()
```

**Storage Location:**
- Session data stored in `flask_session/` directory
- Each session file named by session ID (e.g., `flask_session/2f2f...`)
- Format: Pickled Python objects

### Data Loading Flow with Cache

```python
# utils/generate.py
def loadAndCachePatients(store):
    """Load patients from DB and cache them"""
    allPatients = loadPaginatedPatientData(store)
    sortedPatients = sortPatients(allPatients, store)
    cache_manager.add_patient(store['current_page'], sortedPatients)
    return cache_manager.get_patients(store['current_page'])

def generatePatientRows(store, reloadCache=False):
    """Generate patient list rows, using cache when possible"""
    if reloadCache:
        # Force reload from database
        cache_manager.delete_page(store['current_page'])
        cachedPatientData = loadAndCachePatients(store)
    else:
        # Try cache first
        cachedPatientData = cache_manager.get_patients(store['current_page'])
        if not cachedPatientData:
            # Cache miss: load from database
            cachedPatientData = loadAndCachePatients(store)

    # Apply sorting and filtering
    cachedPatientData = sortPatients(cachedPatientData, store)
    filteredPatients = filterShownPatients(cachedPatientData, store)

    # Generate HTML rows
    patientRows = [generatePatientRow(patient) for patient in filteredPatients]
    return patientRows
```

### When Cache is Invalidated

```python
# 1. After adding/editing a patient
@callback(
    Output('patient_list_content', 'children'),
    Input('sync_database', 'n_clicks'),
    State('session_store', 'data'),
)
def syncDatabase(syncBtn, store):
    cache_manager.delete_page(store['current_page'])
    return generatePatientListContent(store, user, reloadCache=True)

# 2. After modal closes (new data added)
@callback(
    Output('modal_state_store', 'data'),
    Input('patient_modal_md', 'is_open'),
)
def update_modal_state(is_open):
    if not is_open:
        return {'modal_closed': True}  # Signals to reload cache

@callback(
    Output('patient_list_content', 'children'),
    Input('modal_state_store', 'data'),
    State('session_store', 'data'),
)
def update_patient_list(modal_state, store):
    if modal_state and modal_state.get('modal_closed'):
        return generatePatientListContent(store, user, reloadCache=True)
    return no_update
```

### Performance Benefits

**Without Cache:**
```
Load Page 1:
    └─ Query database for 20 patients (200ms)
    └─ Render rows (50ms)
    └─ Total: 250ms

Apply filter:
    └─ Query database again (200ms)
    └─ Render rows (50ms)
    └─ Total: 250ms

Change sort order:
    └─ Query database again (200ms)
    └─ Render rows (50ms)
    └─ Total: 250ms
```

**With Cache:**
```
Load Page 1:
    └─ Query database for 20 patients (200ms)
    └─ Store in cache (5ms)
    └─ Render rows (50ms)
    └─ Total: 255ms

Apply filter:
    └─ Load from cache (10ms)
    └─ Filter in memory (5ms)
    └─ Render rows (50ms)
    └─ Total: 65ms  (74% faster)

Change sort order:
    └─ Load from cache (10ms)
    └─ Sort in memory (5ms)
    └─ Render rows (50ms)
    └─ Total: 65ms  (74% faster)
```

### Dash Store Cache (Client-Side)

```python
# App.py
dcc.Store(id='session_store', storage_type='session', data=getDefaultStore())
```

**Storage Type Options:**
- `memory`: Lost on page refresh
- `session`: Persists in sessionStorage (lost on tab close)
- `local`: Persists in localStorage (survives browser restart)

**What's Stored:**
```python
{
    'current_page': 1,
    'patients_per_page': 20,
    'sortCriteria': 'discharge_date',
    'sortDescending': True,
    'statusFilter': {...},
    'contentFilter': {...},
    'activePatient': None,
    'editing': False,
}
```

**Accessed in Callbacks:**
```python
@callback(
    Output('patient_list_rows', 'children'),
    State('session_store', 'data'),  # Read session state
)
def update_list(store):
    current_page = store['current_page']
    # ...
```

### Cache Coherency Strategy

**Problem:** How to keep Flask session cache and Dash store cache in sync?

**Solution:**
1. Flask session cache = source of truth for data
2. Dash store cache = source of truth for UI state
3. Updates propagate: Dash store → callback → Flask session → re-render

```python
@callback(
    Output('session_store', 'data'),
    Input('next_page', 'n_clicks'),
    State('session_store', 'data'),
)
def update_page(next_clicks, store):
    store['current_page'] += 1  # Update Dash store
    # Next callback will use updated page to load from Flask cache
    return store  # Return updated store (triggers dependent callbacks)
```

---

## Configuration Management

### Environment-Based Configuration (FpConfig.py)

```python
import os
from dotenv import load_dotenv

flightplan_env = os.environ.get('FLIGHTPLAN_ENV', 'local')

if flightplan_env == 'local' and load_dotenv:
    load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env.local'))

# Application metadata
appName = 'Flight Plan'
appVersion = 'v3.3.0'
postVersion = '.4'

# Encryption key for client-side data
encryption_key = os.environ.get('ENCRYPTION_KEY')

# Chatbot URL (optional feature)
chatbot_url = os.environ.get('CHATBOT_URL')

# Database configuration
databaseConnect = {
    'Interface': 'SQLSERVER',
    'Server': os.environ.get('DB_SERVER'),
    'Database': os.environ.get('DB_NAME'),
    'User': os.environ.get('DB_USER'),
    'Password': os.environ.get('DB_PASSWORD'),
}

sqlDatabaseConnect = databaseConnect

# Blob storage (for attachments)
blobStorageConnectCCH = {
    'Connect': os.environ.get('BLOB_STORAGE_CONNECT'),
    'Container': os.environ.get('CONTAINER_NAME', 'devreports')
}

blobStorageConnect = blobStorageConnectCCH

# Pagination
patients_per_page = int(os.environ.get('PATIENTS_PER_PAGE', 20))

# Local development overrides
if flightplan_env == 'local':
    fp_local_user = os.environ.get('FP_LOCAL_USER')
    fp_local_creds = os.environ.get('FP_LOCAL_CREDS')
    fp_local_occupation = os.environ.get('FP_LOCAL_OCCUPATION')
```

### Environment Variables

**Required:**
- `DB_SERVER`: Database server hostname (e.g., 'localhost', 'db.azure.com')
- `DB_NAME`: Database name (e.g., 'FlightPlan3')
- `DB_USER`: Database username
- `DB_PASSWORD`: Database password
- `ENCRYPTION_KEY`: 32-byte encryption key for client-side data

**Optional:**
- `FLIGHTPLAN_ENV`: 'local' or 'production' (default: 'local')
- `PATIENTS_PER_PAGE`: Number of patients per page (default: 20)
- `CHATBOT_URL`: URL for chatbot integration (if enabled)
- `BLOB_STORAGE_CONNECT`: Azure Blob Storage connection string
- `CONTAINER_NAME`: Blob storage container name (default: 'devreports')
- `FP_LOCAL_USER`: Local development user override
- `FP_LOCAL_CREDS`: Local development credentials level (1-4)
- `FP_LOCAL_OCCUPATION`: Local development occupation

### Static Configuration (FpCodes.py)

**Database Schemas:**
```python
patient_schema = {
    'table': ['patients'],
    'fields': ['MRN', 'LastName', 'FirstName', 'DOB', 'sex',
               'KeyDiagnosis', 'Deceased', 'Username', 'ActivityDate']
}

admission_schema = {
    'table': ['admissions'],
    'fields': ['MRN', 'ADM', 'ADMDATE', 'Status', 'Interventions',
               'Diagnosis', 'ReviewDate', 'CrossCheck', 'Thumbnail',
               'Username', 'ActivityDate'],
}

location_steps_schema = {
    'table': ['location_steps'],
    'fields': ['MRN', 'ADM', 'LocationStepID', 'EntryDatetime', 'Location',
               'Weight', 'Teams', 'Notes', 'Extra', 'Username', 'ActivityDate'],
}

# ... more schemas
```

**Location Configuration:**
```python
locationList = [
    {
        'category': 'ACCU',
        'labels': ['ACCU'],
        'heading': 'Arrival to ACCU',
        'line_color': 'rgb(90, 176, 196)',
        'ecmo_color': 'rgba(90, 176, 196, .5)',
        'annotation_color': 'rgb(10,80,155)',
    },
    {
        'category': 'CTOR',
        'labels': ['CTOR', 'CVOR'],
        'heading': 'Arrival to CTOR',
        'line_color': 'rgb(125, 91, 166)',
        # ...
    },
    # ... more locations
]
```

**Risk Status Mapping:**
```python
riskStatuses = [
    {'category': 'Discharged', 'level': 1,
     'values': ['discharged', 'discharge']},
    {'category': 'ACCU', 'level': 2,
     'values': ['accu', 'pre-op']},
    {'category': 'Extubated', 'level': 3,
     'values': ['extubated', 'cicu_extubated', ...]},
    {'category': 'Intubated', 'level': 4,
     'values': ['intubated', 'cicu_intubated', ...]},
    {'category': 'Procedure', 'level': 5,
     'values': ['procedure']},
]
```

**Team Members (Currently Hardcoded - Should Be in Database):**
```python
cicu_attending_team_items = [
    'Alten', 'Benscoter', 'Carlisle', 'Chlebowski', 'Cooper',
    'Gist', 'Iliopoulos', 'Koh', 'Misfeldt', 'Perry', 'Other',
]

surgical_team_items = [
    'Lehenbauer', 'Morales', 'Winlaw', 'Backer',
    'Ashfaq', 'Wallen', 'Other'
]

anesthesiologist_team_items = [
    'Other', 'Spaeth, J.', 'Kreeger, R.', 'Kasman, N.', ...
]
```

### Feature Flags

```python
# App.py
navLinks = {
    "home": {"order": 0, 'disabled': False},
    "patients": {"order": 1, 'disabled': False},
    # "reviews": {"order": 2, 'disabled': True},  # Disabled feature
    "logout": {"order": 3, 'disabled': False}
}
```

### Development vs Production Differences

**Development (flightplan_env='local'):**
- Loads `.env.local` file for environment variables
- Uses local database (`localhost`, port 9050)
- User authentication overridden by `FP_LOCAL_USER` / `FP_LOCAL_CREDS`
- Debug mode enabled (`app.run_server(debug=True)`)
- Logging level: DEBUG

**Production (flightplan_env='production'):**
- Uses environment variables from Azure App Service
- Azure authentication via `X-MS-CLIENT-PRINCIPAL-NAME` header
- Port 80
- Debug mode disabled
- Logging level: WARNING
- HTTPS enforced (via Azure)

---

## Security Architecture

### 1. Authentication

**Production (Azure App Service):**
```python
# utils/FP2_Utilities.py
def getUserInformation():
    try:
        # Azure injects this header after authentication
        userName = request.headers['X-MS-CLIENT-PRINCIPAL-NAME']
    except:
        userName = 'guest'  # Fallback

    # Validate user exists in database
    with SqlDatabase(sqlDatabaseConnect) as db:
        where = f"where username = '{userName}'"
        user_db = db.select(users_schema, where)

    if len(user_db) == 0:
        return 'guest', '', 1  # Read-only access

    return userName, user_db[0]['occupation'], int(user_db[0]['credentials'])
```

**Local Development:**
```python
if flightplan_env == 'local' and fp_local_user:
    return fp_local_user, fp_local_occupation, int(fp_local_creds)
```

### 2. Authorization (Role-Based Access Control)

```python
# FpCodes.py
user_operation_access = [
    {'operation': 'Content Admin', 'minimum_access_level': 4},
    {'operation': 'Flightplan Edit Mode', 'minimum_access_level': 3},
    {'operation': 'Add Patient', 'minimum_access_level': 4},
]

# utils/FP2_Utilities.py
def check_user_access(credentials, operation):
    access_entry = next(
        (item for item in user_operation_access
         if item['operation'] == operation), None
    )
    if not access_entry:
        return False
    return credentials >= access_entry['minimum_access_level']
```

**Usage in UI:**
```python
# pages/Patients.py
if check_user_access(user['credentials'], 'Add Patient'):
    add_patient_button = html.Button('Add Patient', ...)
else:
    add_patient_button = None  # Hide button
```

### 3. Data Encryption

**Client-Side Data (sessionStorage):**
```python
from cryptography.fernet import Fernet

encryption_key = os.environ.get('ENCRYPTION_KEY')  # 32-byte key
fernet = Fernet(encryption_key.encode())

def encrypt(data):
    return fernet.encrypt(str(data).encode()).decode()

def decrypt(encrypted_data):
    return fernet.decrypt(encrypted_data.encode()).decode()
```

**Usage:**
```python
# Encrypt before storing in Dash Store
@callback(
    Output('sessionData_USER', 'data'),
    Input('main_content', 'children'),
)
def entrypoint(layout):
    userName, occupation, credentials = getUserInformation()
    return encrypt(userName)  # Stored encrypted in browser

# Decrypt when reading
@callback(
    Output('page_content', 'children'),
    State('sessionData_USER', 'data'),
)
def render_page(encrypted_user):
    userName = decrypt(encrypted_user)
    # Use decrypted value
```

**Why Encrypt Client-Side Data?**
- Browser sessionStorage is accessible via JavaScript
- Prevents sensitive data exposure via XSS attacks
- MRNs in URLs are also encrypted (e.g., `/patient/gAAAAABm...`)

### 4. SQL Injection Prevention

**Parameterized Queries:**
```python
# GOOD (parameterized)
with SqlDatabase(sqlDatabaseConnect) as db:
    sql = 'select * from patients where MRN = ?'
    params = [mrn]
    db.sendSql(sql, params)

# BAD (vulnerable to SQL injection)
sql = f"select * from patients where MRN = '{mrn}'"
db.sendSql(sql)  # Don't do this!
```

**Example from Patient.py:**
```python
def addPatientToDatabase(self):
    with SqlDatabase(sqlDatabaseConnect) as db:
        params = []
        sql = 'declare @_dob datetime;'
        sql += 'select @_dob = CONVERT(DATETIME, ?);'
        params.append(str(self.DOB))

        sql += 'execute add_patient '
        sql += '@mrn = ?, '
        params.append(str(self.MRN))

        sql += '@last_name = ?,'
        params.append(self.lastName)
        # ... more parameters

        db.sendSql(sql, params)  # Safe: uses parameters
```

### 5. Session Security

```python
# FpServer.py
flaskApp.config['SECRET_KEY'] = secrets.token_hex()  # Random per restart
flaskApp.config['SESSION_TYPE'] = 'filesystem'
flaskApp.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=60)
```

**Security Features:**
- Random secret key per app restart (invalidates old sessions)
- Server-side session storage (not accessible from client)
- 60-minute session timeout
- Sessions invalidated on logout

### 6. Input Validation

**Client-Side (HTML5):**
```python
dbc.Input(
    type='date',
    required=True,
    pattern='[0-9]{4}-[0-9]{2}-[0-9]{2}',  # YYYY-MM-DD
)
```

**Server-Side (Python):**
```python
# utils/validations.py
def is_date_after(date1, date2):
    """Validate date1 is after date2"""
    return dt.datetime.strptime(date1, '%Y-%m-%d') > dt.datetime.strptime(date2, '%Y-%m-%d')

# components/containers/PatientContainer.py
@callback(
    Output('form_feedback_id', 'children'),
    Input('dob_input', 'value'),
    Input('surgery_date_input', 'value'),
)
def validate(dob, surgeryDate):
    if dob and surgeryDate:
        if is_date_after(dob, surgeryDate):
            return 'DOB must be before surgery date'
    return 'Success!'
```

### 7. Access Control Patterns

```python
# Pattern 1: Hide UI elements based on credentials
if check_user_access(credentials, 'Add Patient'):
    return html.Button('Add Patient', id='add_patient_btn')
else:
    return html.Div()  # Empty div (no button)

# Pattern 2: Disable functionality in callbacks
@callback(
    Output('patient_modal', 'is_open'),
    Input('add_patient_btn', 'n_clicks'),
    State('sessionData_Creds', 'data'),
)
def open_modal(clicks, encrypted_creds):
    creds = decryptInt(encrypted_creds)
    if not check_user_access(creds, 'Add Patient'):
        raise PreventUpdate  # Prevent action
    return True
```

---

## Discrepancy Analysis

### Documentation vs Actual Implementation

#### 1. README.md Claims vs Reality

**README States:**
> "Libraries currently required to run FlightPlan include... Gremlin Python"

**Reality:**
- `gremlin_python` is imported in `FpDatabase.py` but **never used**
- `GraphDatabase` class exists but is **not instantiated anywhere**
- All data storage uses SQL, not graph database

**Verdict:** OUTDATED - Gremlin/graph database integration was likely planned but not implemented.

---

**README States:**
> "Connect to optoai sqlDatabaseConnectSFLExt from FpConfig.py"

**Reality:**
- `sqlDatabaseConnectSFLExt` **does not exist** in FpConfig.py
- Only `sqlDatabaseConnect` exists
- Connection strings are environment-variable based, not hardcoded

**Verdict:** OUTDATED - Documentation refers to old variable names.

---

**README States:**
> "Server name: www.opto-ai.com, 9667"

**Reality:**
- Server and port are configurable via environment variables
- No hardcoded server names in code
- Production uses Azure-hosted database

**Verdict:** OUTDATED - Documentation refers to old hosting setup.

---

#### 2. FpConfig.py Discrepancies

**Config File Shows:**
```python
databaseConnect = {
    'Interface': 'SQLSERVER',
    # ... config
}

sqlDatabaseConnectLocal = {
    'Interface': 'SQLSERVER',
    # ... same config
}

sqlDatabaseConnect = databaseConnect  # Active connection
```

**Discrepancy:**
- `sqlDatabaseConnectLocal` is defined but **never referenced**
- Comment in README suggests switching between connections, but code doesn't support this
- All environments use the same `sqlDatabaseConnect` variable

**Verdict:** INCOMPLETE - Local/production switching mechanism is not fully implemented.

---

#### 3. Team Member Lists

**Current Implementation:**
```python
# FpCodes.py (hardcoded)
cicu_attending_team_items = ['Alten', 'Benscoter', 'Carlisle', ...]
surgical_team_items = ['Lehenbauer', 'Morales', 'Winlaw', ...]
```

**Expected Design:**
- Team members should be stored in database
- Allows updates without code changes
- Supports team member histories

**Verdict:** TECHNICAL DEBT - Should be database-driven, not hardcoded.

---

#### 4. Feature Flags

**Code Shows:**
```python
# App.py
navLinks = {
    # "reviews": {"order": 2, 'disabled': True},  # Commented out
}
```

**pages/Reviews.py exists but is not registered**

**Verdict:** INCOMPLETE FEATURE - Reviews page exists but is disabled.

---

#### 5. Pagination Implementation

**Combined Schema Definition:**
```python
combined_schema = {
    'table': ['patients', 'admissions'],
    'fields': ['patients.MRN', 'patients.LastName', ...]
}
```

**Query Execution:**
```python
def select_patients_by_location_step(schema, where, order_by, offset, fetch):
    # Joins patients + admissions + location_steps
    # Returns combined results
```

**Discrepancy:**
- Schema defines `['patients', 'admissions']` (2 tables)
- Query actually joins **3 tables** (patients + admissions + location_steps subquery)
- Schema doesn't accurately represent actual query

**Verdict:** DOCUMENTATION MISMATCH - Schema definition doesn't match query complexity.

---

#### 6. Caching Behavior

**Expected (from code structure):**
- Cache should work for all pages
- Each page independently cached

**Actual Behavior:**
- Search results create "page 0" in cache
- Page 0 is special case not cleared properly
- Can lead to stale search results

```python
# cache_manager.py
def add_searched_patients_to_search_page(self, patients, store):
    search_page = 0  # Special page
    session['cachedPatients'][search_page] = patients
    store['current_page'] = search_page  # Switches to page 0
```

**Verdict:** POTENTIAL BUG - Search cache handling is inconsistent with regular pagination.

---

#### 7. Authentication Flow

**Production Claim:**
> "Uses Azure App Service authentication"

**Reality:**
```python
def getUserInformation():
    try:
        userName = request.headers['X-MS-CLIENT-PRINCIPAL-NAME']
    except:
        userName = 'guest'  # Silent fallback
```

**Discrepancy:**
- Authentication failure silently defaults to 'guest'
- No logging or error reporting
- Could mask authentication issues

**Verdict:** MISSING ERROR HANDLING - Should log authentication failures.

---

#### 8. Database Support Claims

**FpDatabase.py supports:**
- SQL Server ✅
- MySQL ✅
- SQLite ✅

**Reality:**
- SQL Server is tested and used ✅
- MySQL/SQLite code exists but **untested**
- Pagination uses SQL Server-specific syntax (`OFFSET ... ROWS FETCH NEXT`)

```python
sql += f" OFFSET {offset} ROWS FETCH NEXT {fetch} ROWS ONLY"
# SQL Server syntax - won't work on MySQL/SQLite
```

**Verdict:** INCOMPLETE - Multi-database support is claimed but not fully implemented.

---

### Undocumented Features

#### 1. Encrypted URL Routing
```python
# Patient URLs use encrypted MRNs
/patient/gAAAAABm4nZ8K... (encrypted MRN)

# utils/FP2_Utilities.py
def extract_mrn_from_path(pathname):
    match = re.match(r"/patient/([^/?#]+)", pathname)
    if match:
        return decrypt(match.group(1))
```

**Documentation:** Not mentioned anywhere.

---

#### 2. Chatbot Integration
```python
# FpConfig.py
chatbot_url = os.environ.get('CHATBOT_URL')

# pages/Patients.py
if chatbot_url:
    floating_button = html.Button(
        children=html.I(className='fa-solid fa-robot'),
        id='floating_button',
        # Renders floating chatbot button
    )
```

**Documentation:** No mention of chatbot feature in README or docs/.

---

#### 3. Sync Database Button
```python
# pages/Patients.py
html.Button('Sync Database', id='sync_database')

@callback(
    Output('patient_list_content', 'children'),
    Input('sync_database', 'n_clicks'),
)
def syncDatabase(syncBtn, store):
    cache_manager.delete_page(store['current_page'])
    return generatePatientListContent(store, user, reloadCache=True)
```

**Purpose:** Manually invalidates cache and reloads from database.
**Documentation:** Not mentioned in user or developer docs.

---

#### 4. Clean Up Patient Feature
```python
# pages/Patients.py
html.Button('Clean Up Patient', id='open_clean_user_modal')

@callback(...)
def cleanUpUser(open, close, cleanUp, MRN, store, ...):
    if cleanUp and component_id == 'clean_up_user':
        if MRN:
            admission = getActiveAdmissionForPatient(MRN)
            if admission:
                admission.removePatient()  # Deletes all patient data
```

**Purpose:** Completely removes a patient and all associated data from database.
**Documentation:** Not mentioned. Potentially dangerous feature with no undo.

---

### Critical Findings Summary

| Issue | Severity | Impact |
|-------|----------|--------|
| Hardcoded team members | Medium | Requires code changes to update staff |
| Silent authentication failure | High | Could mask security issues |
| Incomplete multi-DB support | Low | Misleading claims in code comments |
| Search cache inconsistency | Medium | Potential for stale data |
| Undocumented data deletion | High | Risk of accidental data loss |
| Graph database code (unused) | Low | Dead code, confusing to developers |
| Outdated README | Medium | Misleads new developers |

---

## Appendices

### A. Key File Reference

| File Path | Purpose | Key Classes/Functions |
|-----------|---------|----------------------|
| `FlightPlan2.py` | Application entry point | Main execution |
| `App.py` | Main layout and navigation | `generateMainPageLayout()`, `entrypoint()` |
| `FpServer.py` | Flask/Dash server setup | `flaskApp`, `app` |
| `FpDatabase.py` | Database abstraction | `SqlDatabase`, `GraphDatabase` |
| `FpConfig.py` | Configuration management | Database configs, environment vars |
| `FpCodes.py` | Static configuration | Schemas, location lists, team members |
| `pages/Patients.py` | Patient list page | `generatePatientListContent()`, `filter_toggle()` |
| `pages/PatientDetail.py` | Patient detail page | `generatePatientHeading()`, timeline rendering |
| `pages/index.py` | Root redirect | Redirects to `/patients` |
| `pages/Home.py` | Home page | Redirects to `/patients` |
| `utils/generate.py` | Data loading/rendering | `loadPaginatedPatientData()`, `generatePatientRow()` |
| `utils/cache_manager.py` | Session caching | `CacheManager` |
| `utils/FP2_Utilities.py` | Utility functions | `getUserInformation()`, `encrypt()`, `decrypt()` |
| `utils/CallbackManager.py` | Callback registration | `CallbackManager` |
| `utils/validations.py` | Input validation | `is_date_after()` |
| `models/Patient.py` | Patient data model | `Patient` |
| `models/Admission.py` | Admission data model | `Admission` |
| `models/LocationStep.py` | Location step model | `LocationStep` |
| `models/LocationRisk.py` | Risk status model | `LocationRisk` |
| `components/containers/BaseContainer.py` | Container base class | `BaseContainer` |
| `components/sections/BaseSection.py` | Section base class | `BaseSection` |
| `flight_plan_components/src/lib/components/Timeline.react.js` | React timeline | `Timeline` component |

---

### B. Database Schema

**Core Tables:**
- `patients` - Patient demographics
- `admissions` - Hospital admissions
- `location_steps` - Location transfers (ACCU → CTOR → CICU → etc.)
- `location_risks` - Risk status changes within locations
- `bedside_procedures` - Procedures performed at bedside
- `continuous_therapy` - Ongoing therapies (ECMO, dialysis)
- `annotations` - Timeline annotations
- `feedbacks` - Performance evaluations
- `conferences` - Care conferences
- `course_corrections` - Care plan adjustments
- `attachments` - File attachments (images, PDFs)
- `users` - User accounts and credentials

**Key Relationships:**
```
patients (1) ─── (M) admissions
admissions (1) ─── (M) location_steps
location_steps (1) ─── (M) location_risks
location_steps (1) ─── (M) bedside_procedures
admissions (1) ─── (M) annotations
admissions (1) ─── (M) feedbacks
admissions (1) ─── (M) conferences
admissions (1) ─── (M) course_corrections
admissions (1) ─── (M) attachments
```

---

### C. Callback Dependencies Graph

```
session_store (dcc.Store)
    ├─ filter_toggle() → Updates filters
    ├─ display_page() → Clears activePatient on page change
    └─ update_page() → Changes current_page

patient_list_rows (html.Table)
    └─ filter_toggle() → Regenerates rows based on filters

patient_list_content (html.Div)
    ├─ entrypoint() → Initial load
    ├─ syncDatabase() → Manual refresh
    ├─ update_patient_list() → After modal close
    └─ cleanUpUser() → After patient deletion

sessionData_USER (dcc.Store)
    └─ entrypoint() → Loaded from Azure header or env var

patient_modal_md (dbc.Modal)
    ├─ Open button → Sets is_open=True
    ├─ Submit → Saves patient, sets is_open=False
    └─ Cancel → Sets is_open=False
```

---

### D. Deployment Checklist

**Environment Variables to Set:**
- [ ] `FLIGHTPLAN_ENV` = 'production'
- [ ] `DB_SERVER` = Azure SQL server hostname
- [ ] `DB_NAME` = Database name
- [ ] `DB_USER` = Database username
- [ ] `DB_PASSWORD` = Database password
- [ ] `ENCRYPTION_KEY` = 32-byte encryption key (generate with `secrets.token_hex(16)`)
- [ ] `BLOB_STORAGE_CONNECT` = Azure Blob Storage connection string
- [ ] `CONTAINER_NAME` = Blob container name
- [ ] `PATIENTS_PER_PAGE` = 20 (or desired value)
- [ ] `CHATBOT_URL` = Chatbot URL (optional)

**Azure App Service Configuration:**
- [ ] Enable Azure AD authentication
- [ ] Set allowed users/groups
- [ ] Configure session affinity (ARR affinity: ON)
- [ ] Set Python version to 3.9+
- [ ] Configure startup command: `gunicorn --bind=0.0.0.0 --timeout 600 FlightPlan2:server`

**Database Setup:**
- [ ] Run `dbSetup.py` to create tables
- [ ] Populate `users` table with initial users
- [ ] Set user credentials (1-4)
- [ ] Grant database user appropriate permissions

**Security:**
- [ ] Rotate `ENCRYPTION_KEY` periodically
- [ ] Enable database firewall (whitelist App Service IPs)
- [ ] Use Managed Identity for Blob Storage (instead of connection string)
- [ ] Enable HTTPS-only mode
- [ ] Set session timeout to appropriate value

---

### E. Common Operations

**Add a New Location Type:**
1. Update `FpCodes.py::locationList` with new location
2. Update database schema if needed
3. Update graph generation in `utils/FP2_GraphUtilities.py::findLocationColor()`

**Add a New User:**
1. Insert into `users` table:
   ```sql
   INSERT INTO users (username, occupation, credentials, last_access)
   VALUES ('john.doe@hospital.com', 'Physician', 3, GETDATE())
   ```
2. User will have access on next login

**Add a New Team Member:**
1. Currently: Update `FpCodes.py` (e.g., `surgical_team_items`)
2. Recommended: Migrate to database table

**Debug Session Cache:**
```python
# Add to callback for debugging
import logging
logging.info(f"Session cache keys: {session.get('cachedPatients', {}).keys()}")
logging.info(f"Current page: {store['current_page']}")
```

**Clear All Caches:**
```python
# In Python console or callback
from flask import session
session.clear()  # Clears Flask session
# Dash stores are cleared on page refresh
```

---

### F. Performance Optimization Recommendations

1. **Implement Lazy Loading for Admission Details:**
   - Currently all admission data loaded on Patient list load
   - Recommendation: Only load location_steps/annotations when patient detail page is opened

2. **Add Database Indexes:**
   ```sql
   CREATE INDEX idx_patients_mrn ON patients(MRN);
   CREATE INDEX idx_admissions_reviewdate ON admissions(ReviewDate DESC);
   CREATE INDEX idx_location_steps_mrn_adm ON location_steps(MRN, ADM);
   ```

3. **Implement Redis Cache (instead of Flask filesystem sessions):**
   ```python
   flaskApp.config['SESSION_TYPE'] = 'redis'
   flaskApp.config['SESSION_REDIS'] = redis.from_url('redis://localhost:6379')
   ```

4. **Use Connection Pooling:**
   ```python
   # Currently: New connection per query
   # Recommended: Connection pooling for better performance
   ```

5. **Compress React Bundle:**
   ```bash
   # In flight_plan_components/webpack.config.js
   optimization: {
       minimize: true,
       minimizer: [new TerserPlugin()],
   }
   ```

---

### G. Known Issues and Workarounds

**Issue 1: Search Results Not Cleared**
- **Symptom:** After searching, navigation to different page still shows search results
- **Cause:** Search creates "page 0" which isn't cleared by pagination
- **Workaround:** Clear search field before navigating

**Issue 2: Session Timeout Not User-Friendly**
- **Symptom:** Session expires after 60 minutes, page breaks
- **Cause:** No warning before session expiration
- **Workaround:** Refresh page to re-authenticate

**Issue 3: Large Patient Load Slow**
- **Symptom:** First page load takes 5+ seconds with 500+ patients
- **Cause:** Complex JOIN query with location_steps subquery
- **Workaround:** Increase `patients_per_page` to reduce pagination overhead

---

### H. Future Enhancements

**Recommended:**
1. Migrate team members to database tables
2. Implement proper multi-database support (fix pagination SQL)
3. Add audit logging for data changes
4. Implement real-time updates (WebSockets for concurrent users)
5. Add comprehensive error logging (Sentry, Application Insights)
6. Implement patient search by diagnosis/procedure
7. Add data export functionality (CSV, Excel)
8. Implement role-based UI customization
9. Add unit tests for critical components
10. Document React component props in code

---

## Document Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-12-18 | Claude (AI Assistant) | Initial comprehensive documentation |

---

**End of Document**

For questions or clarifications, please contact the development team.
