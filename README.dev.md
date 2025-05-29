# Flask Project Structure Guide  

**Ingeniería de Software II**  

This document explains how to structure the project so everyone can contribute consistently. 

In short. If you want to contribute, we use 3 files mostly:
- **Blueprints** to organize code (`routes.py`)
- **Flask-WTF** for validation (`forms.py`)
- **service modules** to handle business logic (`service.py`) 

#### **Flow Summary**  
1. **User visits `/tournament/create`** (`GET`):  
   - Route renders an empty page and form.  
2. **User submits form** (`POST`):  
   - Flask-WTF validates data.  
   - If valid, service saves to DB.  
   - Route redirects to a new page.  

This keeps code **modular** and **secure**.

## 🧩 Project Structure: Blueprints First  
**Blueprints** are Flask’s way of organizing code into reusable components. Think of them as "mini-apps" (e.g., `user`, `tournament`) that plug into the main app.

### Example Structure:
```
your-app/  
├── app.py                  # Entry point  
├── modules/  
│   ├── user/              # Blueprint: user management  
│   │   ├── routes.py      # URL endpoints (e.g., /login, /profile)  
│   │   ├── forms.py       # Forms & validation  
│   │   └── service.py     # Database interactions & logic  
│   ├── tournament/        # Blueprint: tournaments  
│   │   ├── routes.py  
│   │   ├── forms.py  
│   │   └── service.py  
│   └── ...  
├── templates/             # HTML templates  
├── static/                # CSS/JS/images  
└── requirements.txt  
```

### How Blueprints Work:  
Here's the improved, more pedagogical version with clear explanations for each part:

---

#### **1. Defining a Blueprint (routes.py)**  

Every module has its own `routes.py` file (e.g., `modules/user/routes.py`). This is where we:  
1. **Create the Blueprint** (a group of related routes).  
2. **Define routes** under the blueprint's URL prefix.  

#### Example: User Module (`modules/user/routes.py`)  
```python
# Import Blueprint from Flask
from flask import Blueprint

# 1. Create the Blueprint instance:
# - 'user' = blueprint name (for Flask's internal use)
# - __name__ = helps Flask locate the blueprint
# - url_prefix='/user' = all routes start with /user
user_bp = Blueprint('user', __name__, url_prefix='/user')

# 2. Define routes using the blueprint (@user_bp.route('/route_name'))
@user_bp.route('/profile')  # Full URL: /user/profile
def profile():
    """Handles GET requests for user profiles."""
    return "User profile page"

@user_bp.route('/settings')  # Full URL: /user/settings
def settings():
    """Handles GET requests for user settings."""
    return "User settings page"
```

No matter the route name (`/profile`, `/create`, etc), the URL always starts with the blueprint’s prefix (`/user`, in this case).

#### 2. **Register the Blueprint** in `app.py`:  
```python
from modules.user.routes import user_bp

app = Flask(__name__)
app.register_blueprint(user_bp)
```

Now, visiting `/user/register` triggers the `register()` function.  

## 🔍 Flow: From URL to Response  
Every(almost) request follows this flow:  
**Endpoint (Blueprint) → Validation (Flask-WTF) → Service → Response**  

### Step 1: Endpoint (URL → Blueprint)  
When a user visits `/user/register` (GET) or clicks a button (e.g., submits a form: POST):  
- The **blueprint’s route** (`routes.py`) handles the request.  
- Example (`modules/user/routes.py`):  
```python
# modules/user/routes.py
@user_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST': # Not a GET here!
        # Getting the values from the form
        email = request.form.get('email')
        password = request.form.get('password')

        # Validations here!
        # 1. Check if email is valid (e.g., contains '@')
        # 2. Check if password is >= 6 characters
        # 3. Verify email isn't already registered

        # If valid, proceed:
        create_user(email, password)  # Call service layer (do something on DB)
        return redirect('/login')

    return render_template('user/register.html')  # Show empty form. This is a GET!
```

---

### Step 2: Validation (Flask-WTF)  
Define forms in `forms.py` to validate incoming data (e.g., registration fields).  
- Example (`modules/user/forms.py`):  
```python
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, validators
from .service import get_user_by_email  # Assume this queries the DB

def email_not_registered(form, field): # This is a custom validator
    if get_user_by_email(field.data):  # Check if email exists
        raise ValidationError("Email already registered. Use a different one.")

class RegistrationForm(FlaskForm):
    email = StringField('Email', 
        validators=[
            validators.DataRequired(),
            validators.Email(message="Invalid email address."),
            email_not_registered  # <-- Custom validator
        ]
    )

    password = PasswordField('Password', 
        validators=[
            validators.DataRequired(),
            validators.Length(min=6, message="Password must be 6+ characters.")
        ]
    )
```

So the function (`modules/user/routes.py`) should be something like this now:

```python
# modules/user/routes.py
from .forms import RegistrationForm

@user_bp.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():  # Auto-checks validations
        create_user(form.email.data, form.password.data)  # Data is clean!
        return redirect('/login')
    return render_template('user/register.html', form=form)  # Pass form to template
```

- **Why?** Ensures data is correct *before* processing (e.g., valid email, password length).  

---

### **Step 3: Service Layer & Final Response**  

#### Example: Creating a Tournament  
##### 1. Route (`modules/tournament/routes.py`)  
```python
from .forms import TournamentForm
from .service import create_tournament

@tournament_bp.route('/create', methods=['GET', 'POST'])
def create_tournament_route():
    form = TournamentForm()
    if form.validate_on_submit():  # Step 2: Validation passed
        # Step 3: Call service
        tournament = create_tournament(
            name=form.name.data,
            date=form.date.data
        )
        return redirect(f'/tournament/{tournament.id}')  # Return: Redirect
    return render_template('tournament/create.html', form=form)  # Return: Render form
```

##### 2. Service (`modules/tournament/service.py`)  
```python
from ..database import db
from .models import Tournament

def create_tournament(name, date):
    tournament = Tournament(name=name, date=date)
    db.session.add(tournament)
    db.session.commit()
    return tournament  # Return: Database object
```

**Key Points**:  
- The **service** doesn’t know about HTTP (no `request` or `form` objects). It just handles data.  
- The **route** decides the HTTP response (redirect/render) based on the service’s result.  

---

## **Bonus Sections**  

### **1. Flask Return Types**  
Flask routes can return:  
- **`render_template('page.html')`**: Renders an HTML template.  
- **`redirect('/some-url')`**: Redirects the user to another URL.  
- **`jsonify({'data': 'value'})`**: Sends JSON (for APIs).  
- **`"Plain text"`**: Raw text (debugging).  
- **`Response(status=404)`**: Custom HTTP status codes.  

Example:  
```python
@user_bp.route('/data')
def get_data():
    if request.args.get('format') == 'json':
        return jsonify({'user': 'Alice'})  # JSON response
    return render_template('user/data.html')  # HTML response
```

---

### **2. Why `methods=['GET', 'POST']`?**  
- **`GET`**: Used when fetching data (e.g., loading a page).  
- **`POST`**: Used when submitting data (e.g., forms).  

By default, routes only accept `GET`. Adding `POST` allows the endpoint to handle form submissions.  

Example:  
```python
@user_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':  # User submitted the form
        return handle_login(request.form)
    return render_template('login.html')  # Show empty form (GET)
```

---

### **3. Why `if request.method == 'POST'`?**  
This checks **how the request was sent**:  
- **`POST`**: The user submitted data (e.g., form, API call).  
- **`GET`**: The user loaded the page (e.g., via URL).  

Without this, a `GET` request could accidentally trigger form processing.  

#### Bad Practice:  
```python
# THIS WOULD RUN ON PAGE LOAD (GET) AND DELETE DATA!
@user_bp.route('/delete', methods=['GET', 'POST'])
def delete():
    delete_user(request.args.get('id'))  # Runs even on GET!
    return redirect('/users')
```

#### Correct Approach:  
```python
@user_bp.route('/delete', methods=['POST'])  # Only POST allowed
def delete():
    delete_user(request.form.get('id'))
    return redirect('/users')
```

---

## 🎯 Why This Structure?  
- **Separation of Concerns**: Routes handle URLs, forms validate data, services handle logic.  
- **Collaboration**: Teams can work on different blueprints (e.g., one group on `tournament`, another on `team`).  
- **Scalability**: Adding a new feature? Create a new blueprint (e.g., `event`) and follow the same pattern.  

---

## 🚀 Getting Started  
1. **Clone the repo**, create a virtual environment and install dependencies:  
```bash
# Create virtual environment
python -m venv .venv

# Activate the venv
#   For Linux use: source venv/bin/activate
#   If there is an error, change it manually in the bottom right corner (open a .py file first)
.venv\Scripts\activate

# Once the venv if active, install the requirements
.venv\Scripts\pip.exe install -r requirements.txt
```

2. **Create a .env file**:

Or rename `.env_example`...

3. **Run the app**:  

```bash
.venv\Scripts\python.exe run.py
```

Then, go to the site:
http://localhost:5000


4. **Contribute**:  
- Need to add a feature? Create a new blueprint (e.g., `modules/teams`).  
- Use the **endpoint → validation → service** flow.  
