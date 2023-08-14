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
