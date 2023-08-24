from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory, session, jsonify
from mtcnn import MTCNN
from flask_restful import Api, Resource
import cv2
from flaskext.mysql import MySQL
import os
import qrcode
import numpy as np
from PIL import Image
import tempfile
import shutil
import numpy as np
import face_recognition
from pyzbar import pyzbar


app = Flask(__name__)
# MySQL configurations
app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = ''
app.config['MYSQL_DATABASE_DB'] = 'vision_sec'
app.config['MYSQL_DATABASE_HOST'] = 'localhost'
mysql = MySQL(app)

app.secret_key = 'secret_key_here'
app.config['UPLOAD_FOLDER'] = 'uploads'

# Function to save student photo and return the path


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


def generate_qr_code(data):
    import qrcode
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(data)
    qr.make(fit=True)
    qr_code = qr.make_image(fill_color='black', back_color='white')
    return qr_code


def save_student_photo(photo):
    # Create the 'uploads' directory if it doesn't exist
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])

    # Generate a unique filename for the photo
    photo_filename = f"{photo.filename.rsplit('.', 1)[0]}_photo.{photo.filename.rsplit('.', 1)[1]}"
    photo_path = os.path.join(app.config['UPLOAD_FOLDER'], photo_filename)

    # Save the photo only if it exists
    if photo:
        photo.save(photo_path)

    return photo_filename


def detect_single_face(student_photo):
    detector = MTCNN()
    # Convert the student_photo object to a NumPy array
    if isinstance(student_photo, np.ndarray):
        image_data = student_photo
    else:
        # If the student_photo is a FileStorage object (as provided by Flask's request), convert it to a PIL image
        img = Image.open(student_photo)
        image_data = np.array(img)

    # Ensure the image has three channels (RGB)
    if len(image_data.shape) == 2:
        image_data = cv2.cvtColor(image_data, cv2.COLOR_GRAY2RGB)
    elif len(image_data.shape) == 4:
        image_data = image_data[..., :3]

    results = detector.detect_faces(image_data)

    if len(results) != 1:
        return False
    else:
        return True

def save_student_data(student_name, student_id, course_end_date, password, student_photo):
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a temporary copy of the photo
        temp_photo_path = os.path.join(temp_dir, "temp_photo.jpg")
        student_photo.save(temp_photo_path)

        # Check if there is a single face in the temporary photo
        if not detect_single_face(temp_photo_path):
            # Raise a ValueError with a custom error message
            raise ValueError(
                "Invalid photo. Please upload a photo with a single face.")

        # Save the student photo with a unique filename
        photo_filename = f"{student_name.replace(' ', '_')}_photo.jpg"
        photo_path = os.path.join(app.config['UPLOAD_FOLDER'], photo_filename)
        shutil.move(temp_photo_path, photo_path)

        # Generate the QR code and save it with a unique filename
    qr_data = f"Name: {student_name}, ID: {student_id}, Course End Date: {course_end_date}, Password: {password}"
    qr_code = generate_qr_code(qr_data)
    qr_filename = f"{student_name.replace(' ', '_')}_qrcode.png"
    qr_path = os.path.join(app.config['UPLOAD_FOLDER'], qr_filename)
    qr_code.save(qr_path)

     #Save the student data and photo/QR code paths to the database
    connection = mysql.connect()
    cursor = connection.cursor()
    try:
        query = "INSERT INTO students (student_name, student_id, course_end_date, password, photo_path, qr_code_path) VALUES (%s, %s, %s, %s, %s, %s)"
        data = (student_name, student_id, course_end_date, password,
                photo_path.replace('\\', '/'), qr_path.replace('\\', '/'))
        cursor.execute(query, data)
        connection.commit()
    except Exception as e:
        # In case of an error, remove the uploaded files
        os.remove(photo_path)
        os.remove(qr_path)
        raise e
    finally:
        connection.close()

    pubnub.publish().channel("new_student_channel").message({
        "student_name": student_name,
        "student_id": student_id,
        "message": "New student registered!"
    }).sync()

    return photo_path, qr_path


@app.errorhandler(ValueError)
def handle_value_error(e):
    return render_template('error.html', error_message="Invalid photo. Please upload a photo with a single face.")


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Get form data
        student_name = request.form['student_name']
        student_id = request.form['student_id']
        course_end_date = request.form['course_end_date']
        password = request.form['password']
        student_photo = request.files['student_photo']

        # Save student data, photo, and QR code, and get their paths
        photo_path, qr_code_path = save_student_data(
            student_name, student_id, course_end_date, password, student_photo)

        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        student_id = request.form['student_id']
        password = request.form['password']

        connection = mysql.connect()
        cursor = connection.cursor()
        try:
            query = "SELECT * FROM students WHERE student_id = %s AND password = %s"
            data = (student_id, password)
            cursor.execute(query, data)
            student = cursor.fetchone()

            if student:
                session['logged_in'] = True
                # Use student name for session
                session['username'] = student[1]
                flash('Login successful', 'success')
                return redirect(url_for('profile'))
            else:
                flash('Invalid credentials. Please try again.', 'danger')
        except Exception as e:
            flash('Error occurred during login: ' + str(e), 'danger')
        finally:
            connection.close()

    return render_template('login.html')


app.route('/')
def home():
    return render_template('home.html')


@app.route('/profile')
def profile():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    # Use student name stored in session
    student_name = session.get('username')

    connection = mysql.connect()
    cursor = connection.cursor()
    try:
        query = "SELECT student_name, student_id, course_end_date, photo_path, qr_code_path FROM students WHERE student_name = %s"
        data = (student_name,)
        cursor.execute(query, data)
        student = cursor.fetchone()

        if student:
            student_name, student_id, course_end_date, photo_path, qr_code_path = student
        else:
            flash('Student details not found.', 'danger')
            return redirect(url_for('login'))
    except Exception as e:
        flash('Error occurred while accessing student details: ' + str(e), 'danger')
        return redirect(url_for('login'))
    finally:
        connection.close()

    return render_template('profile.html', student_name=student_name, student_id=student_id,
                           course_end_date=course_end_date, photo_path=photo_path, qr_code_path=qr_code_path)


@app.route('/uploaded_file/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


@app.route('/download_qr_code/<filename>')
def download_qr_code(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True, mimetype='image/png')

@app.route('/logout', methods=['GET', 'POST'])
def logout():
    # Clear the session data to log the user out
    session.clear()
    flash('You have been logged out.', 'success')
    return redirect(url_for('login'))


@app.route('/delete_account', methods=['POST'])
def delete_account():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    # Get the QR code path and student photo path from the database
    connection = mysql.connect()
    cursor = connection.cursor()
    try:
        query = "SELECT qr_code_path, photo_path FROM students WHERE student_name = %s"
        data = (session['username'],)
        cursor.execute(query, data)
        paths = cursor.fetchone()

        if paths:
            qr_code_path, photo_path = paths

            # Delete the user's photo and QR code files if they exist
            if os.path.exists(photo_path):
                os.remove(photo_path)
            if os.path.exists(qr_code_path):
                os.remove(qr_code_path)

            # Delete the user account from the database
            delete_query = "DELETE FROM students WHERE student_name = %s"
            cursor.execute(delete_query, data)
            connection.commit()

            # Clear the session data to log the user out after account deletion
            session.clear()
            flash('Your account has been deleted.', 'success')
            return redirect(url_for('login'))
        else:
            flash('Student details not found.', 'danger')
            return redirect(url_for('login'))
    except Exception as e:
        flash('Error occurred while deleting the account: ' + str(e), 'danger')
        return redirect(url_for('profile'))
    finally:
        connection.close()


# Function to calculate the face embeddings using FaceNet model
def get_face_embedding(image):
    resnet = face_recognition.api.face_encodings(image)
    return resnet


# Function to calculate the cosine distance between two embeddings
def calculate_cosine_distance(embedding1, embedding2):
    embedding1 = embedding1[0]
    embedding2 = embedding2[0]
    return 1.0 - np.dot(embedding1, embedding2) / (np.linalg.norm(embedding1) * np.linalg.norm(embedding2))


# Function to check if the image contains a QR code and return its details
def is_qr_code(image):
    decoded_objects = pyzbar.decode(image)
    if decoded_objects:
        qr_code_data = []
        for obj in decoded_objects:
            qr_code_data.append(obj.data.decode('utf-8'))
        return qr_code_data
    return None

@app.route('/process_photo', methods=['POST'])
def process_photo():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if not file or not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file format or type'}), 400

    # Save the uploaded photo temporarily
    temp_path = 'temp.jpg'
    file.save(temp_path)

    # Load the input photo
    input_image = face_recognition.load_image_file(temp_path)

    # Check if it is a QR code
    qr_code_data = is_qr_code(input_image)
    if qr_code_data:
        os.remove(temp_path)
        return jsonify({'qr_code_data': qr_code_data})

    # Detect faces in the input image
    input_encodings = get_face_embedding(input_image)

    # If no face is detected or more than one face detected, or if QR code is detected, exit
    if len(input_encodings) != 1:
        os.remove(temp_path)
        return jsonify({'error': 'Invalid photo: No face or multiple faces detected'}), 400

    # Directory containing face photos for comparison
    uploads_dir = "uploads"

    # Load the face encodings for the photos in the uploads folder
    known_face_encodings = []
    known_face_names = []

    for filename in os.listdir(uploads_dir):
        if filename.endswith(".jpg") or filename.endswith(".png"):
            face_photo_path = os.path.join(uploads_dir, filename)
            face_photo = face_recognition.load_image_file(face_photo_path)
            face_encoding = face_recognition.api.face_encodings(face_photo)

            # If no face is detected in the photo, skip comparison
            if not face_encoding:
                continue

            # Use the first face encoding (assuming one face per photo)
            known_face_encodings.append(face_encoding[0])
            known_face_names.append(filename)

    # Compare the face encodings
    face_distances = face_recognition.api.face_distance(
        known_face_encodings, input_encodings[0])

    # You can adjust this distance threshold based on your needs
    distance_threshold = 0.4

    # Print the result
    for i, face_distance in enumerate(face_distances):
        if face_distance < distance_threshold:
            os.remove(temp_path)
            return jsonify({'result': f'Face matches with {known_face_names[i]}'})

    os.remove(temp_path)
    return jsonify({'result': 'Face does not match with any uploaded face'})


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'jpg', 'jpeg', 'png'}


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)