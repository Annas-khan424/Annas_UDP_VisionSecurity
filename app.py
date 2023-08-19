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
