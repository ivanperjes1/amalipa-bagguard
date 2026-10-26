import os
from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.utils import secure_filename
from supabase import create_client, Client

# --- SUPABASE CONFIGURATION ---
SUPABASE_URL = "https://dfowpkuoyztotlescnie.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImRmb3dwa3VveXp0b3RsZXNjbmllIiwicm9sZSI6ImFub24iLCJpYXQiOjE3OTIxNTIwODEsImV4cCI6MjEwNzcyODA4MX0.kLC4rUsyQfzb-b7AMvFRqV89oHjw71kTQ4O3qgQEsTw"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- UPLOAD FOLDER CONFIGURATION ---
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf'}

# --- APP INITIALIZATION ---
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.secret_key = 'ama_lipa_bagguard_secret_key' # Required for flash messages & sessions

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# --- ROUTES ---

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        student_name = request.form.get('student_name')
        usn = request.form.get('usn')
        department = request.form.get('department') # Captures M1, M2, or M3
        bag_description = request.form.get('bag_description')
        
        # Handle file / image upload
        file = request.files.get('bag_image')
        filename = None
        
        if file and file.filename != '' and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        
        # Insert record into Supabase table
        try:
            supabase.table('bag_registrations').insert({
                'student_name': student_name,
                'usn': usn,
                'department': department,
                'bag_description': bag_description,
                'image_filename': filename
            }).execute()
            
            flash('Bag registration successful and stored in Supabase!', 'success')
        except Exception as e:
            flash(f'Database error: {str(e)}', 'danger')
            
        return redirect(url_for('index'))
        
    return render_template('register.html')

@app.route('/scan', methods=['GET', 'POST'])
def scan():
    student = None
    error = None
    if request.method == 'POST':
        usn = request.form.get('usn', '').strip()
        try:
            # Query Supabase for the registered student by USN
            response = supabase.table('bag_registrations').select('*').eq('usn', usn).execute()
            
            if response.data and len(response.data) > 0:
                student = response.data[0] # Found the owner!
            else:
                error = f"❌ UNREGISTERED: No bag registration found for USN: {usn}"
        except Exception as e:
            error = f"Database error: {str(e)}"
            
    return render_template('scan.html', student=student, error=error)

# --- SYSTEM ADMIN LOGIN & PANEL ROUTES ---

@app.route('/developer-secret-panel-xyz789/login', methods=['GET', 'POST'])
def developer_login():
    if request.method == 'POST':
        entered_password = request.form.get('password')
        if entered_password == 'BAGlipamacc':
            session['admin_logged_in'] = True
            flash('Access granted to System Administration Panel.', 'success')
            return redirect(url_for('developer_panel'))
        else:
            flash('Incorrect administrative password.', 'danger')
            
    return render_template('admin_login.html')

@app.route('/developer-secret-panel-xyz789')
def developer_panel():
    # Check if admin is logged in via session
    if not session.get('admin_logged_in'):
        flash('Please enter the administrative password first.', 'warning')
        return redirect(url_for('developer_login'))
        
    # Fetch all registered bags from Supabase to display in the admin panel table
    try:
        response = supabase.table('bag_registrations').select('*').execute()
        registrations = response.data
    except Exception as e:
        registrations = []
        
    return render_template('developer.html', registrations=registrations)

@app.route('/developer-logout')
def developer_logout():
    session.pop('admin_logged_in', None)
    flash('Logged out from admin session successfully.', 'info')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)