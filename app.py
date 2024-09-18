import os

import joblib
import numpy as np
import pandas as pd
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import mysql.connector
import re
import logging
from functools import wraps
from werkzeug.utils import secure_filename


app = Flask(__name__)

app.secret_key = "SFSFar6gzada"  # Change this to a random string

UPLOAD_FOLDER = 'uploads/'
ALLOWED_EXTENSIONS = {'xls', 'xlsx', 'csv'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# MySQL configurations
mysql_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'part_of_speech'
}

def get_db_connection():
    connection = mysql.connector.connect(**mysql_config)
    return connection

def role_required(*allowed_roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'userRole' not in session or session['userRole'] not in allowed_roles:
                return redirect(url_for('dashboard'))  # Redirect to the dashboard or another page
            return f(*args, **kwargs)
        return decorated_function
    return decorator


# Home Route
@app.route('/')
def index():
    # if 'username' not in session:
    #     return redirect(url_for('login'))
    # return render_template('dashboard.html' if session.get('userRole') == 'Admin' else 'index.html')
    return render_template('index.html')

# Login Route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()

        # Check if the user exists and the password matches
        if user and (user['password'] == password):
            # Check userState conditions
            if user['userState'] == 'Pending':
                return render_template('login.html', error='Please wait until the admin approves your account.')
            elif user['userState'] == 'Decline':
                return render_template('login.html', error='You cannot use the system. Your request was declined by the admins.')
            elif user['userState'] == 'Approve':
                # Check if status is blocked
                if user['status'] == 'Block':
                    return render_template('login.html', error='Your account has been blocked. Please contact admin for more information.')

                # If all checks pass, log in the user
                session['username'] = user['name']
                session['id'] = user['id']
                session['userRole'] = user['userRole']

                # Redirect to the dashboard (or relevant page) based on user role
                return redirect(url_for('dashboard')) if user['userRole'] == 'Admin' else redirect(url_for('dashboard'))

        # If login credentials don't match
        return render_template('login.html', error='Invalid email or password')

    return render_template('login.html')

from flask import jsonify

# Signup Route
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form['name']
        age = request.form['age']
        email = request.form['email']
        gender = request.form['gender']
        password = request.form['password']
        userState = "Pending"
        status = 'Active'

        if not is_valid_name(name):
            return jsonify({'error': 'Invalid name. Please enter a valid name.'}), 400

        if not age.isdigit() or int(age) < 18 or int(age) > 70:
            return jsonify({'error': 'Age must be a number between 18 and 70.'}), 400

        age = int(age)

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()
        if user:
            cursor.close()
            conn.close()
            return jsonify({'error': 'Email already exists.'}), 400

        cursor.execute("INSERT INTO users (name, age, gender, email, password, userState, status) VALUES (%s, %s, %s, %s, %s,%s,%s)",
                       (name, age, gender, email, password, userState, status))
        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({'redirect': url_for('login')})
    return render_template('signup.html')


# Logout Route
@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard.html')

@app.route('/dashboard_data')
def dashboard_data():
    if 'id' not in session:
        return jsonify({'error': 'User not logged in'}), 403

    user_id = session['id']  # Get the current user's ID from the session
    user_role = session['userRole']  # Get the current user's role from the session

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Total Users (only for Admin)
    if user_role == 'Admin':
        cursor.execute("SELECT COUNT(*) AS total_users FROM users")
        total_users = cursor.fetchone()['total_users']
    else:
        total_users = 0  # For User and Moderator, we might not show total users

    # Total Admins (only for Admin)
    if user_role == 'Admin':
        cursor.execute("SELECT COUNT(*) AS total_admins FROM users WHERE userRole = 'Admin'")
        total_admins = cursor.fetchone()['total_admins']
    else:
        total_admins = 0  # Default to 0 for User and Moderator

    # Total Moderators (only for Admin)
    if user_role == 'Admin':
        cursor.execute("SELECT COUNT(*) AS total_moderators FROM users WHERE userRole = 'Moderator'")
        total_moderators = cursor.fetchone()['total_moderators']
    else:
        total_moderators = 0  # Default to 0 for User and Moderator

    # Total Regular Users (only for Admin)
    if user_role == 'Admin':
        cursor.execute("SELECT COUNT(*) AS total_regular_users FROM users WHERE userRole = 'User'")
        total_regular_users = cursor.fetchone()['total_regular_users']
    else:
        total_regular_users = 0  # Default to 0 for User and Moderator

    # Total Active Users (status = 'Active')
    if user_role == 'Admin':
        cursor.execute("SELECT COUNT(*) AS total_actives FROM users WHERE status = 'Active'")
        total_actives = cursor.fetchone()['total_actives']
    else:
        total_actives = 0  # Default for User and Moderator

    # Total Blocked Users (status = 'Block')
    if user_role == 'Admin':
        cursor.execute("SELECT COUNT(*) AS total_blocks FROM users WHERE status = 'Block'")
        total_blocks = cursor.fetchone()['total_blocks']
    else:
        total_blocks = 0  # Default for User and Moderator

    # Total Approved Users (userState = 'Approve')
    if user_role == 'Admin':
        cursor.execute("SELECT COUNT(*) AS total_approved FROM users WHERE userState = 'Approve'")
        total_approved = cursor.fetchone()['total_approved']
    else:
        total_approved = 0  # Default for User and Moderator

    # Total Declined Users (userState = 'Decline')
    if user_role == 'Admin':
        cursor.execute("SELECT COUNT(*) AS total_declined FROM users WHERE userState = 'Decline'")
        total_declined = cursor.fetchone()['total_declined']
    else:
        total_declined = 0  # Default for User and Moderator

    # Total Pending Users (userState = 'Pending')
    if user_role == 'Admin':
        cursor.execute("SELECT COUNT(*) AS total_pendings FROM users WHERE userState = 'Pending'")
        total_pendings = cursor.fetchone()['total_pendings']
    else:
        total_pendings = 0  # Default for User and Moderator

    # Gender Distribution (only for Admin)
    if user_role == 'Admin':
        cursor.execute("SELECT gender, COUNT(*) AS count FROM users GROUP BY gender")
        gender_distribution = cursor.fetchall()
    else:
        gender_distribution = []  # Empty for User and Moderator

    # Age Distribution (only for Admin)
    if user_role == 'Admin':
        cursor.execute("SELECT age, COUNT(*) AS count FROM users GROUP BY age")
        age_distribution = cursor.fetchall()
    else:
        age_distribution = []  # Empty for User and Moderator

    # Total Asalka Ereyada for current user (User/Moderator see their own, Admin sees all)
    if user_role == 'Admin' or user_role == 'Moderator':
        cursor.execute("SELECT COUNT(*) AS total_asalka_ereyada FROM asalka_ereyada")
        total_asalka_ereyada = cursor.fetchone()['total_asalka_ereyada']
    else:
        cursor.execute("SELECT COUNT(*) AS total_asalka_ereyada FROM asalka_ereyada WHERE userId = %s", (user_id,))
        total_asalka_ereyada = cursor.fetchone()['total_asalka_ereyada']

    # Total Faraca Erayada (User/Moderator see their own, Admin sees all)
    if user_role == 'Admin' or user_role == 'Moderator':
        cursor.execute("SELECT COUNT(*) AS total_faraca_erayada FROM erayga_hadalka")
        total_faraca_erayada = cursor.fetchone()['total_faraca_erayada']
    else:
        cursor.execute("SELECT COUNT(*) AS total_faraca_erayada FROM erayga_hadalka WHERE userId = %s", (user_id,))
        total_faraca_erayada = cursor.fetchone()['total_faraca_erayada']

    # Maximum number of derivatives (Faraca) for any Asalka_Erayga (only for Admin)
    if user_role == 'Admin':
        cursor.execute("""
            SELECT MAX(farac_count) AS max_derivatives
            FROM (
                SELECT COUNT(*) AS farac_count
                FROM erayga_hadalka
                GROUP BY Asalka_erayga
            ) AS derived
        """)
        max_derivatives = cursor.fetchone()['max_derivatives']
    else:
        max_derivatives = 0  # Default for User and Moderator

    # Minimum number of derivatives (Faraca) for any Asalka_Erayga (only for Admin)
    if user_role == 'Admin':
        cursor.execute("""
            SELECT MIN(farac_count) AS min_derivatives
            FROM (
                SELECT COUNT(*) AS farac_count
                FROM erayga_hadalka
                GROUP BY Asalka_erayga
            ) AS derived
        """)
        min_derivatives = cursor.fetchone()['min_derivatives']
    else:
        min_derivatives = 0  # Default for User and Moderator

    # User Role Distribution (only for Admin)
    if user_role == 'Admin':
        cursor.execute("SELECT userRole, COUNT(*) AS count FROM users GROUP BY userRole")
        user_role_distribution = cursor.fetchall()
    else:
        user_role_distribution = []

    # User State Distribution (only for Admin)
    if user_role == 'Admin':
        cursor.execute("SELECT userState, COUNT(*) AS count FROM users GROUP BY userState")
        user_state_distribution = cursor.fetchall()
    else:
        user_state_distribution = []

    # User Status Distribution (only for Admin)
    if user_role == 'Admin':
        cursor.execute("SELECT status, COUNT(*) AS count FROM users GROUP BY status")
        user_status_distribution = cursor.fetchall()
    else:
        user_status_distribution = []  # Default empty for User and Moderator


    cursor.close()
    conn.close()

    return jsonify({
        'user_role': user_role,
        'total_users': total_users,
        'total_admins': total_admins,
        'total_moderators': total_moderators,
        'total_regular_users': total_regular_users,
        'total_actives': total_actives,
        'total_blocks': total_blocks,
        'total_approved': total_approved,
        'total_declined': total_declined,
        'total_pendings': total_pendings,
        'gender_distribution': gender_distribution,
        'age_distribution': age_distribution,
        'total_asalka_ereyada': total_asalka_ereyada,
        'total_faraca_erayada': total_faraca_erayada,
        'max_derivatives': max_derivatives,  
        'min_derivatives': min_derivatives,
        'user_role_distribution': user_role_distribution,
        'user_state_distribution': user_state_distribution,
        'user_status_distribution': user_status_distribution 
    })


@app.route('/users')
@role_required('Admin')
def users():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('users.html')

@app.route('/get_users', methods=['GET'])
@role_required('Admin')
def get_users():
    if 'username' not in session:
        return jsonify({'error': 'User not logged in'}), 403

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users")
    users = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(users)

@app.route('/get_user/<int:user_id>', methods=['GET'])
@role_required('Admin')
def get_user(user_id):
    if 'username' not in session:
        return jsonify({'error': 'User not logged in'}), 403

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()

    if not user:
        return jsonify({'error': 'User not found'}), 404

    return jsonify(user)

def is_valid_username(username):
    return re.match("^[a-zA-Z-]+$", username)

@app.route('/add_user', methods=['POST'])
@role_required('Admin')
def add_user():
    if 'username' not in session:
        return jsonify({'error': 'User not logged in'}), 403

    try:
        data = request.form
        username = data['name']
        age = int(data['age'])
        gender = data['gender']
        email = data['email']
        password = data['password']
        userRole = data['userRole']
        userState = data['userState']
        status = data['status']

        if not is_valid_name(username):
            return jsonify(
                {'error': 'Invalid username. Only letters, numbers, underscores, and hyphens are allowed.'}), 400

        conn = mysql.connector.connect(**mysql_config)
        cursor = conn.cursor(dictionary=True)
        if age > 70 or age < 18:
            return jsonify({'error': 'Age must be between 18 and 70.'}), 400

        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        if cursor.fetchone():
            cursor.close()
            conn.close()
            return jsonify({'error': 'Email already exists'}), 400

        cursor.execute("INSERT INTO users (name, age, gender, userRole,email, password, userState, status) VALUES (%s, %s,%s, %s, %s, %s,%s,%s)",
                       (username, age, gender, userRole, email, password, userState, status))
        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({'message': 'User added successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/edit_user/<int:user_id>', methods=['POST'])
@role_required('Admin')
def edit_user(user_id):
    if 'username' not in session:
        return jsonify({'error': 'User not logged in'}), 403

    logging.debug(f"Received request to edit user with ID: {user_id}")

    try:
        data = request.form
        username = data.get('name')
        age = data.get('age', type=int)
        gender = data.get('gender')
        email = data.get('email')
        password = data.get('password')
        userRole = data.get('userRole')
        userState = data.get('userState')
        status = data.get('status')

        # Validate username
        if not is_valid_name(username):
            return jsonify({'error': 'Invalid username. Only letters, numbers, underscores, and hyphens are allowed.'}), 400

        # Validate age range
        if age is None or age < 18 or age > 70:
            return jsonify({'error': 'Age must be between 18 and 70.'}), 400

        # Check for duplicate email
        conn = mysql.connector.connect(**mysql_config)
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE email = %s AND id != %s", (email, user_id))
        if cursor.fetchone():
            cursor.close()
            conn.close()
            return jsonify({'error': 'Email already exists for another user'}), 400

        # Update user details
        cursor.execute("""
            UPDATE users 
            SET name = %s, age = %s, gender = %s, userRole = %s, email = %s, password = %s, userState = %s, status = %s 
            WHERE id = %s
        """, (username, age, gender, userRole, email, password, userState, status, user_id))

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({'message': 'User updated successfully'}), 200

    except mysql.connector.Error as err:
        logging.error(f"MySQL Error: {err}")
        return jsonify({'error': f"MySQL Error: {str(err)}"}), 500

    except Exception as e:
        logging.error(f"Error editing user: {e}")
        return jsonify({'error': f"Error: {str(e)}"}), 500


@app.route('/delete_user/<int:user_id>', methods=['DELETE'])
@role_required('Admin')
def delete_user(user_id):
    if 'username' not in session:
        return jsonify({'error': 'User not logged in'}), 403

    conn = mysql.connector.connect(**mysql_config)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({'message': 'User deleted successfully'})

@app.route('/qeybaha_hadalka')
@role_required('Admin', 'Moderator')
def qeybaha_hadalka():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('qeybaha_hadalka.html')

# CRUD Operations for Qeybaha Hadalka
@app.route('/readAll', methods=['GET'])
def get_all_qeybaha_hadalka():
    if 'id' not in session:
        return jsonify({'error': 'User not logged in'}), 403

    user_role = session.get('userRole')

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Admins and Moderators can see all Qeybta_hadalka
    if user_role == 'Admin' or user_role == 'Moderator':
        cursor.execute("SELECT * FROM qeybaha_hadalka")
    else:
        # Users can also see all Qeybta_hadalka
        cursor.execute("SELECT * FROM qeybaha_hadalka")

    data = cursor.fetchall()
    cursor.close()
    conn.close()

    return jsonify(data)


@app.route('/readInfo/<int:id>', methods=['GET'])
@role_required('Admin', 'Moderator')
def get_qeybaha_hadalka(id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM qeybaha_hadalka WHERE Aqoonsiga_hadalka = %s", (id,))
    data = cursor.fetchone()
    cursor.close()
    conn.close()
    if data:
        return jsonify(data)
    return jsonify({'error': 'Record not found'}), 404

@app.route('/create', methods=['POST'])
@role_required('Admin', 'Moderator')  # Only Admin can insert
def create_qeybaha_hadalka():
    if 'id' not in session:
        return jsonify({'error': 'User not logged in'}), 403

    user_role = session.get('userRole')

    # Deny access if the user is a Moderator
    if user_role == 'Moderator':
        return jsonify({'error': 'Permission denied: Moderators cannot insert data'}), 403

    # Proceed with insertion for other roles
    new_record = request.json
    Qaybta_hadalka = new_record.get('Qaybta_hadalka')
    Loo_gaabsho = new_record.get('Loo_gaabsho')
    userId = session['id']  # Get the current user's ID from the session

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM qeybaha_hadalka WHERE Qaybta_hadalka = %s", (Qaybta_hadalka,))
    existing_record = cursor.fetchone()

    if existing_record:
        cursor.close()
        conn.close()
        return jsonify({'error': 'This word is already recorded! Please enter a new one.'}), 400

    cursor.execute("INSERT INTO qeybaha_hadalka (Qaybta_hadalka, Loo_gaabsho, userId) VALUES (%s, %s, %s)",
                   (Qaybta_hadalka, Loo_gaabsho, userId))
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({'message': 'Record created successfully'}), 201


@app.route('/update/<int:id>', methods=['PUT'])
@role_required('Admin', 'Moderator')  # Allow both Admin and Moderator to update
def update_qeybaha_hadalka(id):
    if 'id' not in session:
        return jsonify({'error': 'User not logged in'}), 403

    if not request.is_json:
        return jsonify({"error": "Missing JSON in request"}), 400

    update_record = request.get_json()
    Qaybta_hadalka = update_record.get('Qaybta_hadalka')
    Loo_gaabsho = update_record.get('Loo_gaabsho')

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Proceed with updating the record (Admins and Moderators can update)
    cursor.execute("""
        UPDATE qeybaha_hadalka 
        SET Qaybta_hadalka = %s, Loo_gaabsho = %s 
        WHERE Aqoonsiga_hadalka = %s
    """, (Qaybta_hadalka, Loo_gaabsho, id))

    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({'message': 'Record updated successfully'})

@app.route('/delete/<int:id>', methods=['DELETE'])
@role_required('Admin', 'Moderator')  # Only Admin can delete
def delete_qeybaha_hadalka(id):
    if 'id' not in session:
        return jsonify({'error': 'User not logged in'}), 403

    user_role = session.get('userRole')

    # Deny access if the user is a Moderator
    if user_role == 'Moderator':
        return jsonify({'error': 'Permission denied: Moderators cannot delete data'}), 403

    current_user_id = session['id']  # Get the current user's ID from the session

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Retrieve the record to check the user who created it
    cursor.execute("SELECT userId FROM qeybaha_hadalka WHERE Aqoonsiga_hadalka = %s", (id,))
    record = cursor.fetchone()

    if not record:
        cursor.close()
        conn.close()
        return jsonify({'error': 'Record not found'}), 404

    # Proceed with deleting the record
    cursor.execute("DELETE FROM qeybaha_hadalka WHERE Aqoonsiga_hadalka = %s", (id,))
    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({'message': 'Record deleted successfully'})



@app.route('/asalka_ereyada')
def asalka_ereyada():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('asalka_ereyada.html')

# CRUD Operations for Asalka Ereyada
@app.route('/readAllAsalka', methods=['GET'])
def get_all_asalka_ereyada():
    if 'id' not in session:
        return jsonify({'error': 'User not logged in'}), 403

    userId = session['id']
    userRole = session['userRole']  # Get the user's role

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Modify the query based on userRole
    if userRole == 'Admin' or userRole == 'Moderator':
        # Admin or Moderator can see all records
        cursor.execute("SELECT * FROM asalka_ereyada")
    else:
        # Regular User can only see their own records
        cursor.execute("SELECT * FROM asalka_ereyada WHERE userId = %s", (userId,))

    data = cursor.fetchall()

    # Count total records based on role
    if userRole == 'Admin' or userRole == 'Moderator':
        cursor.execute("SELECT COUNT(*) AS total_records FROM asalka_ereyada")
    else:
        cursor.execute("SELECT COUNT(*) AS total_records FROM asalka_ereyada WHERE userId = %s", (userId,))

    total_records = cursor.fetchone()['total_records']

    cursor.close()
    conn.close()

    return jsonify({'data': data, 'total_records': total_records})



@app.route('/readInfoAsalka/<int:id>', methods=['GET'])
def get_asalka_ereyada(id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM asalka_ereyada WHERE Aqonsiga_Erayga = %s", (id,))
    data = cursor.fetchone()
    cursor.close()
    conn.close()
    if data:
        return jsonify(data)
    return jsonify({'error': 'Record not found'}), 404

@app.route('/createAsalka', methods=['POST'])
def create_asalka_ereyada():
    if 'id' not in session:
        return jsonify({'error': 'User not logged in'}), 403

    new_record = request.json
    Erayga_Asalka = new_record.get('Erayga_Asalka')
    userId = session['id']  # Get the current user's ID from the session

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM asalka_ereyada WHERE Erayga_Asalka = %s", (Erayga_Asalka,))
    existing_record = cursor.fetchone()

    if existing_record:
        cursor.close()
        conn.close()
        return jsonify({'error': 'The original word (Asalka Erayga) is already recorded! please enter new one.'}), 400

    cursor.execute("INSERT INTO asalka_ereyada (Erayga_Asalka, userId) VALUES (%s, %s)", (Erayga_Asalka, userId))
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({'message': 'Record created successfully'}), 201

@app.route('/updateAsalka/<int:id>', methods=['PUT'])
def update_asalka_ereyada(id):
    if 'id' not in session:
        return jsonify({'error': 'User not logged in'}), 403

    update_record = request.json
    Erayga_Asalka = update_record.get('Erayga_Asalka')

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM asalka_ereyada WHERE Erayga_Asalka = %s AND Aqonsiga_Erayga != %s",
                   (Erayga_Asalka, id))
    existing_record = cursor.fetchone()

    if existing_record:
        cursor.close()
        conn.close()
        return jsonify({'error': 'The original word (Asalka Erayga) is already recorded! please enter new one.'}), 400

    cursor.execute("UPDATE asalka_ereyada SET Erayga_Asalka = %s WHERE Aqonsiga_Erayga = %s",
                   (Erayga_Asalka, id))
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({'message': 'Record updated successfully'})


@app.route('/deleteAsalka/<int:id>', methods=['DELETE'])
def delete_asalka_ereyada(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM asalka_ereyada WHERE Aqonsiga_Erayga = %s", (id,))
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({'message': 'Record deleted successfully'})


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Route to handle Excel file uploads
@app.route('/uploadAsalka', methods=['POST'])
def upload_asalka_ereyada():
    if 'id' not in session:
        return jsonify({'error': 'User not logged in'}), 403

    if 'asalkaFile' not in request.files:
        return jsonify({'error': 'No file part in the request'}), 400

    file = request.files['asalkaFile']

    if file.filename == '':
        return jsonify({'error': 'No file selected for uploading'}), 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        # Process the file
        try:
            # Determine the file extension and choose the appropriate method
            if filename.endswith('.xls'):
                df = pd.read_excel(filepath, engine='xlrd')
            elif filename.endswith('.xlsx'):
                df = pd.read_excel(filepath, engine='openpyxl')
            elif filename.endswith('.csv'):
                df = pd.read_csv(filepath)
            else:
                return jsonify({'error': 'Unsupported file extension'}), 400

            if 'Erayga_Asalka' not in df.columns:
                return jsonify({'error': 'The file must contain an "Erayga_Asalka" column.'}), 400

            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)

            for _, row in df.iterrows():
                erayga_asalka = row['Erayga_Asalka']

                # Check if the word is already recorded by the user
                cursor.execute("SELECT * FROM asalka_ereyada WHERE Erayga_Asalka = %s AND userId = %s",
                               (erayga_asalka, session['id']))
                existing_record = cursor.fetchone()

                if not existing_record:
                    cursor.execute("INSERT INTO asalka_ereyada (Erayga_Asalka, userId) VALUES (%s, %s)",
                                   (erayga_asalka, session['id']))

            conn.commit()
            cursor.close()
            conn.close()

            return jsonify({'message': 'File uploaded and data imported successfully'}), 201

        except Exception as e:
            return jsonify({'error': str(e)}), 500

    return jsonify({'error': 'Allowed file types are .xls, .xlsx, .csv'}), 400

@app.route('/erayga_hadalka')
def erayga_hadalka():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('erayga_hadalka.html')

# CRUD Operations for Erayga Hadalka
@app.route('/readAllErayga', methods=['GET'])
def get_all_erayga_hadalka():
    if 'id' not in session:
        return jsonify({'error': 'User not logged in'}), 403

    user_id = session['id']  # Get the current user's ID from the session
    user_role = session['userRole']  # Get the current user's role

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Modify the query based on userRole
    if user_role == 'Admin' or user_role == 'Moderator':
        # Admin or Moderator can see all records
        query = """
        SELECT 
            eh.Aqoonsiga_erayga, 
            eh.Erayga, 
            eh.Nooca_erayga, 
            qh.Qaybta_hadalka AS Qeybta_hadalka_name, 
            ae.Erayga_Asalka AS Asalka_erayga_name
        FROM 
            erayga_hadalka eh
            JOIN qeybaha_hadalka qh ON eh.Qeybta_hadalka = qh.Aqoonsiga_hadalka
            JOIN asalka_ereyada ae ON eh.Asalka_erayga = ae.Aqonsiga_Erayga
        ORDER BY ae.Erayga_Asalka ASC
        """
        cursor.execute(query)  # No filtering by userId
    else:
        # Regular User can only see their own records
        query = """
        SELECT 
            eh.Aqoonsiga_erayga, 
            eh.Erayga, 
            eh.Nooca_erayga, 
            qh.Qaybta_hadalka AS Qeybta_hadalka_name, 
            ae.Erayga_Asalka AS Asalka_erayga_name
        FROM 
            erayga_hadalka eh
            JOIN qeybaha_hadalka qh ON eh.Qeybta_hadalka = qh.Aqoonsiga_hadalka
            JOIN asalka_ereyada ae ON eh.Asalka_erayga = ae.Aqonsiga_Erayga
        WHERE 
            eh.userId = %s
        ORDER BY ae.Erayga_Asalka ASC
        """
        cursor.execute(query, (user_id,))  # Filter by userId

    data = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(data)


@app.route('/readInfoErayga/<int:id>', methods=['GET'])
def get_erayga_hadalka(id):
    if 'id' not in session:
        return jsonify({'error': 'User not logged in'}), 403

    user_id = session['id']
    user_role = session['userRole']  # Get the current user's role from the session

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Admins and Moderators can access any record, regular users can only access their own
    if user_role == 'Admin' or user_role == 'Moderator':
        cursor.execute("SELECT * FROM erayga_hadalka WHERE Aqoonsiga_erayga = %s", (id,))
    else:
        cursor.execute("SELECT * FROM erayga_hadalka WHERE Aqoonsiga_erayga = %s AND userId = %s", (id, user_id))

    erayga_data = cursor.fetchone()

    if not erayga_data:
        cursor.close()
        conn.close()
        return jsonify({'error': 'Record not found or you do not have permission to view it'}), 404

    asalka_erayga_id = erayga_data['Asalka_erayga']  # Get the Asalka_erayga ID for this record

    # Fetch all Erayga words that share the same Asalka_erayga
    cursor.execute("SELECT Erayga FROM erayga_hadalka WHERE Asalka_erayga = %s", (asalka_erayga_id,))
    related_erayga_words = cursor.fetchall()

    # Join the related words with commas
    related_erayga_words_str = ', '.join([row['Erayga'] for row in related_erayga_words])

    # Admins and Moderators can view all Asalka Erayga options, regular users only see their own
    if user_role == 'Admin' or user_role == 'Moderator':
        cursor.execute("SELECT Aqonsiga_Erayga, Erayga_Asalka FROM asalka_ereyada")
    else:
        cursor.execute("SELECT Aqonsiga_Erayga, Erayga_Asalka FROM asalka_ereyada WHERE userId = %s", (user_id,))

    asalka_options = cursor.fetchall()

    cursor.close()
    conn.close()

    return jsonify({
        'erayga_data': erayga_data,
        'related_erayga_words': related_erayga_words_str,  # Return the related Erayga words as a string
        'asalka_options': asalka_options
    })

@app.route('/createErayga', methods=['POST'])
def create_erayga_hadalka():
    if 'id' not in session:
        return jsonify({'error': 'User not logged in'}), 403

    user_role = session['userRole']

    # Allow Admin and User to insert, but deny Moderator
    if user_role == 'Moderator':
        return jsonify({'error': 'Permission denied: Moderators cannot insert data'}), 403

    new_record = request.json
    Erayga = new_record.get('Erayga')
    Nooca_erayga = new_record.get('Nooca_erayga')
    Qeybta_hadalka = new_record.get('Qeybta_hadalka')
    Asalka_erayga = new_record.get('Asalka_erayga')
    user_id = session['id']

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Split the Erayga input by both commas and spaces to get individual words
    erayga_words = re.split(r'[,\s]+', Erayga.strip())

    # Initialize counter for inserted words
    inserted_count = 0

    # Iterate over each word and insert it as a unique row
    for word in erayga_words:
        # Check if the word already exists in the `erayga_hadalka` table
        cursor.execute("SELECT * FROM erayga_hadalka WHERE Erayga = %s", (word,))
        existing_record = cursor.fetchone()

        if existing_record:
            continue  # Skip the word if it already exists in the table

        # Check if the Asalka_Erayga already exists in `asalka_ereyada`
        cursor.execute("SELECT * FROM asalka_ereyada WHERE Erayga_Asalka = %s", (word,))
        existing_asalka_record = cursor.fetchone()

        if existing_asalka_record:
            continue  # Skip the word if it already exists in Asalka

        # Proceed with inserting the new word
        cursor.execute(
            "INSERT INTO erayga_hadalka (Erayga, Nooca_erayga, Qeybta_hadalka, Asalka_erayga, userId) "
            "VALUES (%s, %s, %s, %s, %s)",
            (word, Nooca_erayga, Qeybta_hadalka, Asalka_erayga, user_id)
        )
        inserted_count += 1  # Increment the counter

    # Commit the transaction to the database
    conn.commit()
    cursor.close()
    conn.close()

    # Return a success message with the number of inserted words
    return jsonify({
        'message': f'Record created successfully with {inserted_count} words inserted.'
    }), 201

@app.route('/updateErayga/<int:id>', methods=['PUT'])
def update_erayga_hadalka(id):
    if 'id' not in session:
        return jsonify({'error': 'User not logged in'}), 403

    user_role = session['userRole']
    user_id = session['id']

    update_record = request.json
    Erayga = update_record.get('Erayga')
    Nooca_erayga = update_record.get('Nooca_erayga')
    Qeybta_hadalka = update_record.get('Qeybta_hadalka')
    Asalka_erayga = update_record.get('Asalka_erayga')

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Check if the user has permission to update
    if user_role == 'User':
        cursor.execute("SELECT userId FROM erayga_hadalka WHERE Aqoonsiga_erayga = %s", (id,))
        record = cursor.fetchone()
        if not record or record['userId'] != user_id:
            cursor.close()
            conn.close()
            return jsonify({'error': 'Permission denied: You can only update your own records'}), 403

    # Split the new Erayga input by both commas and spaces to get individual words
    new_erayga_words = re.split(r'[,\s]+', Erayga.strip())

    # Fetch existing Erayga words for this record
    cursor.execute("SELECT Erayga FROM erayga_hadalka WHERE Aqoonsiga_erayga = %s", (id,))
    existing_erayga_words = [row['Erayga'] for row in cursor.fetchall()]

    # Words to add (new words that don't already exist)
    words_to_add = set(new_erayga_words) - set(existing_erayga_words)

    # Words to delete (existing words not in the updated list)
    words_to_delete = set(existing_erayga_words) - set(new_erayga_words)

    # Update existing words (if needed) and insert new words
    inserted_count = 0
    updated_count = 0

    # Add new words
    for word in words_to_add:
        # Check if the word already exists
        cursor.execute("SELECT * FROM erayga_hadalka WHERE Erayga = %s", (word,))
        existing_record = cursor.fetchone()

        if existing_record:
            continue  # Skip if the word already exists

        cursor.execute(
            "INSERT INTO erayga_hadalka (Erayga, Nooca_erayga, Qeybta_hadalka, Asalka_erayga, userId) "
            "VALUES (%s, %s, %s, %s, %s)",
            (word, Nooca_erayga, Qeybta_hadalka, Asalka_erayga, user_id)
        )
        inserted_count += 1

    # Delete old words that are not in the updated list
    for word in words_to_delete:
        cursor.execute("DELETE FROM erayga_hadalka WHERE Erayga = %s AND Aqoonsiga_erayga = %s", (word, id))

    # Commit the transaction to the database
    conn.commit()
    cursor.close()
    conn.close()

    # Return a success message with the number of inserted/updated words
    return jsonify({
        'message': f'Record updated successfully with {inserted_count} words added and {len(words_to_delete)} words deleted.'
    }), 200


@app.route('/deleteErayga/<int:id>', methods=['DELETE'])
def delete_erayga_hadalka(id):
    if 'id' not in session:
        return jsonify({'error': 'User not logged in'}), 403

    user_role = session['userRole']
    user_id = session['id']

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Admin can delete any record
    if user_role == 'Moderator':
        cursor.close()
        conn.close()
        return jsonify({'error': 'Permission denied: Moderators cannot delete data'}), 403

    if user_role == 'User':
        # Ensure the user only deletes their own data
        cursor.execute("SELECT userId FROM erayga_hadalka WHERE Aqoonsiga_erayga = %s", (id,))
        record = cursor.fetchone()
        if not record or record['userId'] != user_id:
            cursor.close()
            conn.close()
            return jsonify({'error': 'Permission denied: You can only delete your own records'}), 403

    cursor.execute("DELETE FROM erayga_hadalka WHERE Aqoonsiga_erayga = %s", (id,))
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({'message': 'Record deleted successfully'}), 200


@app.route('/reports')
def reports():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('reports.html')

@app.route('/reports_data')
def reports_data():
    search_query = request.args.get('query', '')

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if search_query:
        # First, check if the search_query is in Asalka_erayga
        check_asalka_query = """
        SELECT Aqonsiga_Erayga, Erayga_Asalka
        FROM asalka_ereyada
        WHERE Erayga_Asalka LIKE %s
        """
        search_param = f"%{search_query}%"
        cursor.execute(check_asalka_query, (search_param,))
        asalka_result = cursor.fetchone()

        if asalka_result:
            # If the search_query is found in Asalka_erayga, fetch all related records
            query = """
            SELECT 
                ae.Aqonsiga_Erayga,
                ae.Erayga_Asalka AS Asalka_erayga,
                GROUP_CONCAT(eh.Erayga SEPARATOR ', ') AS Farac,
                qh.Qaybta_hadalka,
                COUNT(eh.Erayga) AS total_farac  -- New column to count Farac words
            FROM 
                erayga_hadalka eh
                JOIN qeybaha_hadalka qh ON eh.Qeybta_hadalka = qh.Aqoonsiga_hadalka
                JOIN asalka_ereyada ae ON eh.Asalka_erayga = ae.Aqonsiga_Erayga
            WHERE 
                eh.Asalka_erayga = %s
            GROUP BY 
                ae.Aqonsiga_Erayga, ae.Erayga_Asalka, qh.Qaybta_hadalka
            ORDER BY eh.Nooca_erayga ASC
            """
            cursor.execute(query, (asalka_result['Aqonsiga_Erayga'],))
        else:
            # If it's not in Asalka_erayga, perform a normal LIKE search across erayga_hadalka and asalka_ereyada
            query = """
            SELECT 
                ae.Aqonsiga_Erayga,
                ae.Erayga_Asalka AS Asalka_erayga,
                GROUP_CONCAT(eh.Erayga SEPARATOR ', ') AS Farac,
                qh.Qaybta_hadalka,
                COUNT(eh.Erayga) AS total_farac  -- New column to count Farac words
            FROM 
                erayga_hadalka eh
                JOIN qeybaha_hadalka qh ON eh.Qeybta_hadalka = qh.Aqoonsiga_hadalka
                JOIN asalka_ereyada ae ON eh.Asalka_erayga = ae.Aqonsiga_Erayga
            WHERE 
                eh.Erayga LIKE %s OR ae.Erayga_Asalka LIKE %s
            GROUP BY 
                ae.Aqonsiga_Erayga, ae.Erayga_Asalka, qh.Qaybta_hadalka
            ORDER BY eh.Nooca_erayga ASC
            """
            cursor.execute(query, (search_param, search_param))
    else:
        query = """
        SELECT 
            ae.Aqonsiga_Erayga,
            ae.Erayga_Asalka AS Asalka_erayga,
            GROUP_CONCAT(eh.Erayga SEPARATOR ', ') AS Farac,
            qh.Qaybta_hadalka,
            COUNT(eh.Erayga) AS total_farac  -- New column to count Farac words
        FROM 
            erayga_hadalka eh
            JOIN qeybaha_hadalka qh ON eh.Qeybta_hadalka = qh.Aqoonsiga_hadalka
            JOIN asalka_ereyada ae ON eh.Asalka_erayga = ae.Aqonsiga_Erayga
        GROUP BY 
            ae.Aqonsiga_Erayga, ae.Erayga_Asalka, qh.Qaybta_hadalka
        ORDER BY eh.Nooca_erayga ASC
        """
        cursor.execute(query)

    data = cursor.fetchall()

    cursor.close()
    conn.close()

    return jsonify(data)

@app.route('/reportsRootWords')
@role_required('Admin')
def reports_root():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('reportsRootWords.html')

@app.route('/readAllAsalkaOrderedByUsername', methods=['GET'])
def get_all_asalka_ereyada_ordered_by_username():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        query = """
           SELECT ae.Aqonsiga_Erayga, ae.Erayga_Asalka, u.name
            FROM asalka_ereyada ae
            JOIN users u ON ae.userId = u.id
            ORDER BY u.name ASC;
        """
        cursor.execute(query)
        data = cursor.fetchall()
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/userReports')
@role_required('Admin')
def usersReports():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('usersReports.html')

@app.route('/user_reports', methods=['GET'])
def user_reports():
    if 'id' not in session:
        return jsonify({'error': 'User not logged in'}), 403

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        query = """
            SELECT 
                u.name,
                COUNT(DISTINCT ae.Aqonsiga_Erayga) AS total_asalka_recorded,
                COUNT(DISTINCT eh.Aqoonsiga_erayga) AS total_rafaca_erayada,
                (COUNT(DISTINCT ae.Aqonsiga_Erayga) + COUNT(DISTINCT eh.Aqoonsiga_erayga)) AS total_count
            FROM 
                users u
                LEFT JOIN asalka_ereyada ae ON u.id = ae.userId
                LEFT JOIN erayga_hadalka eh ON u.id = eh.userId
            GROUP BY 
                u.name
            ORDER BY 
                u.name ASC;
        """
        cursor.execute(query)
        data = cursor.fetchall()
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/ereyadaReports')
def ereyada_reports():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('ereyadaReports.html')
@app.route('/report', methods=['GET'])
def report():
    if 'id' not in session:
        return jsonify({'error': 'User not logged in'}), 403

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    query = """
    SELECT 
        eh.Aqoonsiga_erayga, 
        eh.Erayga, 
        eh.Nooca_erayga, 
        qh.Qaybta_hadalka AS Qeybta_hadalka_name, 
        ae.Erayga_Asalka AS Asalka_erayga_name
    FROM 
        erayga_hadalka eh
        JOIN qeybaha_hadalka qh ON eh.Qeybta_hadalka = qh.Aqoonsiga_hadalka
        JOIN asalka_ereyada ae ON eh.Asalka_erayga = ae.Aqonsiga_Erayga
    ORDER BY ae.Erayga_Asalka ASC
    """
    cursor.execute(query)


    data = cursor.fetchall()
    cursor.close()
    conn.close()

    return jsonify(data)

def is_valid_name(name):
    return bool(re.match("^[a-zA-Z ]+$", name))

if __name__ == '__main__':
    app.run(debug=True)
