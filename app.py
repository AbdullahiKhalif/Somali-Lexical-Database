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

def role_required(required_role):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'userRole' not in session or session['userRole'] != required_role:
                return redirect(url_for('dashboard'))  # Redirect to the dashboard or another page
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# Home Route
@app.route('/')
def index():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard.html' if session.get('userRole') == 'Admin' else 'index.html')

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

        if user and (user['password'] == password):
            session['username'] = user['name']
            session['id'] = user['id']
            session['userRole'] = user['userRole']
            return redirect(url_for('dashboard')) if user['userRole'] == 'Admin' else redirect(url_for('dashboard'))
        else:
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

        cursor.execute("INSERT INTO users (name, age, gender, email, password) VALUES (%s, %s, %s, %s, %s)",
                       (name, age, gender, email, password))
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

# Dashboard Route
@app.route('/dashboard_data')
def dashboard_data():
    if 'id' not in session:
        return jsonify({'error': 'User not logged in'}), 403

    user_id = session['id']  # Get the current user's ID from the session

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Total Users
    cursor.execute("SELECT COUNT(*) AS total_users FROM users")
    total_users = cursor.fetchone()['total_users']

    # Total Admins
    cursor.execute("SELECT COUNT(*) AS total_admins FROM users WHERE userRole = 'Admin'")
    total_admins = cursor.fetchone()['total_admins']

    # Gender Distribution
    cursor.execute("SELECT gender, COUNT(*) AS count FROM users GROUP BY gender")
    gender_distribution = cursor.fetchall()

    # Age Distribution
    cursor.execute("SELECT age, COUNT(*) AS count FROM users GROUP BY age")
    age_distribution = cursor.fetchall()

    # Total Asalka Ereyada for the current user
    cursor.execute("SELECT COUNT(*) AS total_asalka_ereyada FROM asalka_ereyada WHERE userId = %s", (user_id,))
    total_asalka_ereyada = cursor.fetchone()['total_asalka_ereyada']

    # Total Faraca Erayada in erayga_hadalka for the current user
    cursor.execute("SELECT COUNT(*) AS total_faraca_erayada FROM erayga_hadalka WHERE userId = %s", (user_id,))
    total_faraca_erayada = cursor.fetchone()['total_faraca_erayada']

    cursor.close()
    conn.close()

    return jsonify({
        'total_users': total_users,
        'total_admins': total_admins,
        'gender_distribution': gender_distribution,
        'age_distribution': age_distribution,
        'total_asalka_ereyada': total_asalka_ereyada,
        'total_faraca_erayada': total_faraca_erayada
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

        cursor.execute("INSERT INTO users (name, age, gender, userRole,email, password) VALUES (%s, %s,%s, %s, %s, %s)",
                       (username, age, gender, userRole, email, password))
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
        username = data['name']
        age = int(data['age'])
        gender = data['gender']
        email = data['email']
        password = data['password']
        roll = data['userRole']

        if not is_valid_name(username):
            return jsonify(
                {'error': 'Invalid username. Only letters, numbers, underscores, and hyphens are allowed.'}), 400

        conn = mysql.connector.connect(**mysql_config)
        cursor = conn.cursor(dictionary=True)


        if age > 70 or age < 18:
            return jsonify({'error': 'Age must be between 18 and 70.'}), 400

        cursor.execute("SELECT * FROM users WHERE email = %s AND id != %s", (email, user_id))
        if cursor.fetchone():
            cursor.close()
            conn.close()
            return jsonify({'error': 'Email already exists for another user'}), 400

        cursor.execute("UPDATE users SET name = %s, age = %s, gender = %s, userRole = %s, email = %s , password = %s WHERE id = %s",
                       (username, age, gender, roll, email, password, user_id))
        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({'message': 'User updated successfully'}), 200

    except Exception as e:
        logging.error(f"Error updating user: {str(e)}")
        return jsonify({'error': 'An error occurred while updating the user.'}), 500

        logging.debug(f"User with ID: {user_id} updated successfully")
        return jsonify({'message': 'User updated successfully'})
    except Exception as e:
        logging.error(f"Error updating user with ID: {user_id} - {e}")
        return jsonify({'error': str(e)}), 500

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
@role_required('Admin')
def qeybaha_hadalka():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('qeybaha_hadalka.html')

# CRUD Operations for Qeybaha Hadalka
@app.route('/readAll', methods=['GET'])
@role_required('Admin')
def get_all_qeybaha_hadalka():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM qeybaha_hadalka")
    data = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(data)

@app.route('/readInfo/<int:id>', methods=['GET'])
@role_required('Admin')
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
@role_required('Admin')
def create_qeybaha_hadalka():
    if 'id' not in session:
        return jsonify({'error': 'User not logged in'}), 403

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
@role_required('Admin')
def update_qeybaha_hadalka(id):
    if 'id' not in session:
        return jsonify({'error': 'User not logged in'}), 403

    if not request.is_json:
        return jsonify({"error": "Missing JSON in request"}), 400

    update_record = request.get_json()
    Qaybta_hadalka = update_record.get('Qaybta_hadalka')
    Loo_gaabsho = update_record.get('Loo_gaabsho')
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

    if record['userId'] != current_user_id:
        cursor.close()
        conn.close()
        return jsonify({'error': 'Sorry! You cannot update this data. Only the original user can update it.'}), 403

    # Check if Qaybta_hadalka is unique except for the current record
    cursor.execute("""
        SELECT * FROM qeybaha_hadalka 
        WHERE Qaybta_hadalka = %s AND Aqoonsiga_hadalka != %s AND userId = %s
    """, (Qaybta_hadalka, id, current_user_id))
    existing_record = cursor.fetchone()

    if existing_record:
        cursor.close()
        conn.close()
        return jsonify({'error': 'This word is already recorded! Please enter a new one.'}), 400

    # Proceed with updating the record
    cursor.execute("""
        UPDATE qeybaha_hadalka 
        SET Qaybta_hadalka = %s, Loo_gaabsho = %s 
        WHERE Aqoonsiga_hadalka = %s AND userId = %s
    """, (Qaybta_hadalka, Loo_gaabsho, id, current_user_id))

    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({'message': 'Record updated successfully'})

@app.route('/delete/<int:id>', methods=['DELETE'])
@role_required('Admin')
def delete_qeybaha_hadalka(id):
    if 'id' not in session:
        return jsonify({'error': 'User not logged in'}), 403

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

    if record['userId'] != current_user_id:
        cursor.close()
        conn.close()
        return jsonify({'error': 'Sorry! You cannot delete this data. Only the original user can delete it.'}), 403

    # Proceed with deleting the record
    cursor.execute("DELETE FROM qeybaha_hadalka WHERE Aqoonsiga_hadalka = %s AND userId = %s", (id, current_user_id))
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

    userId = session['id']  # Get the current user's ID from the session

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Query to get the records for the current user
    cursor.execute("SELECT * FROM asalka_ereyada WHERE userId = %s", (userId,))
    data = cursor.fetchall()

    # Query to count the total number of records for the current user
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
    WHERE 
        eh.userId = %s
    """
    cursor.execute(query, (user_id,))
    data = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(data)


@app.route('/readInfoErayga/<int:id>', methods=['GET'])
def get_erayga_hadalka(id):
    if 'id' not in session:
        return jsonify({'error': 'User not logged in'}), 403

    user_id = session['id']  # Get the current user's ID from the session

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Fetch the specific Erayga Hadalka record, ensuring it belongs to the current user
    cursor.execute("SELECT * FROM erayga_hadalka WHERE Aqoonsiga_erayga = %s AND userId = %s", (id, user_id))
    erayga_data = cursor.fetchone()

    if not erayga_data:
        cursor.close()
        conn.close()
        return jsonify({'error': 'Record not found or you do not have permission to view it'}), 404

    # Fetch all Erayga Asalka options
    cursor.execute("SELECT Aqonsiga_Erayga, Erayga_Asalka FROM asalka_ereyada WHERE userId = %s", (user_id,))
    asalka_options = cursor.fetchall()

    cursor.close()
    conn.close()

    return jsonify({
        'erayga_data': erayga_data,
        'asalka_options': asalka_options
    })

@app.route('/createErayga', methods=['POST'])
def create_erayga_hadalka():
    if 'id' not in session:
        return jsonify({'error': 'User not logged in'}), 403

    new_record = request.json
    Erayga = new_record.get('Erayga')
    Nooca_erayga = new_record.get('Nooca_erayga')
    Qeybta_hadalka = new_record.get('Qeybta_hadalka')
    Asalka_erayga = new_record.get('Asalka_erayga')
    user_id = session['id']  # Get the current user's ID from the session

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Check if the word already exists in the erayga_hadalka table
    cursor.execute("SELECT * FROM erayga_hadalka WHERE Erayga = %s", (Erayga,))
    existing_record = cursor.fetchone()

    if existing_record:
        cursor.close()
        conn.close()
        return jsonify({'error': 'The original word (Erayga Hadalka) is already recorded! Please enter a new one.'}), 400

    # Check if the word exists in the asalka_ereyada table
    cursor.execute("SELECT * FROM asalka_ereyada WHERE Erayga_Asalka = %s", (Erayga,))
    existing_asalka_record = cursor.fetchone()

    if existing_asalka_record:
        cursor.close()
        conn.close()
        return jsonify({'error': 'This word is already recorded as a Root word in Asalka Ereyada. Please use another word.'}), 400

    # If both checks pass, insert the new record with the userId
    cursor.execute(
        "INSERT INTO erayga_hadalka (Erayga, Nooca_erayga, Qeybta_hadalka, Asalka_erayga, userId) VALUES (%s, %s, %s, %s, %s)",
        (Erayga, Nooca_erayga, Qeybta_hadalka, Asalka_erayga, user_id)
    )
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({'message': 'Record created successfully'}), 201

@app.route('/updateErayga/<int:id>', methods=['PUT'])
def update_erayga_hadalka(id):
    if 'id' not in session:
        return jsonify({'error': 'User not logged in'}), 403

    update_record = request.json
    Erayga = update_record.get('Erayga')
    Nooca_erayga = update_record.get('Nooca_erayga')
    Qeybta_hadalka = update_record.get('Qeybta_hadalka')
    Asalka_erayga = update_record.get('Asalka_erayga')
    user_id = session['id']  # Get the current user's ID from the session

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Check if the current user is the one who created the record
    cursor.execute("SELECT userId FROM erayga_hadalka WHERE Aqoonsiga_erayga = %s", (id,))
    record = cursor.fetchone()

    if not record or record['userId'] != user_id:
        cursor.close()
        conn.close()
        return jsonify({'error': 'Sorry! You cannot update this data. Only the original user can update it.'}), 403

    # Check if the word is already recorded in erayga_hadalka for a different record
    cursor.execute("SELECT * FROM erayga_hadalka WHERE Erayga = %s AND Aqoonsiga_erayga != %s",
                   (Erayga, id))
    existing_record = cursor.fetchone()

    if existing_record:
        cursor.close()
        conn.close()
        return jsonify({'error': 'The original word (Erayga Hadalka) is already recorded! Please enter a new one.'}), 400

    # Check if the word is recorded in the asalka_ereyada table
    cursor.execute("SELECT * FROM asalka_ereyada WHERE Erayga_Asalka = %s", (Erayga,))
    existing_asalka_record = cursor.fetchone()

    if existing_asalka_record:
        cursor.close()
        conn.close()
        return jsonify({'error': 'This word is already recorded as a Root word in Asalka Ereyada. Please use another word.'}), 400

    # If all checks pass, update the record
    cursor.execute(
        "UPDATE erayga_hadalka SET Erayga = %s, Nooca_erayga = %s, Qeybta_hadalka = %s, Asalka_erayga = %s WHERE Aqoonsiga_erayga = %s",
        (Erayga, Nooca_erayga, Qeybta_hadalka, Asalka_erayga, id)
    )
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({'message': 'Record updated successfully'})


@app.route('/deleteErayga/<int:id>', methods=['DELETE'])
def delete_erayga_hadalka(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM erayga_hadalka WHERE Aqoonsiga_erayga = %s", (id,))
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({'message': 'Record deleted successfully'})


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
                qh.Qaybta_hadalka
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
                qh.Qaybta_hadalka
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
            qh.Qaybta_hadalka
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


def is_valid_name(name):
    return bool(re.match("^[a-zA-Z ]+$", name))

if __name__ == '__main__':
    app.run(debug=True)
