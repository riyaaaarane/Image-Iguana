from flask import Flask, render_template, request, flash, redirect, url_for, send_file, send_from_directory
from werkzeug.utils import secure_filename
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from markupsafe import Markup
import cv2
import os
import numpy as np
import zipfile
import tempfile
import shutil
import time

from flask_wtf.csrf import CSRFProtect

import base64
from PIL import Image
from io import BytesIO
from flask import after_this_request

app = Flask(__name__)
csrf = CSRFProtect(app)
app.secret_key = "your-secret-key-here"  # Change this to a secure secret key
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5MB max upload size

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Allowed file extensions and upload folder
ALLOWED_EXTENSIONS = {'webp', 'png', 'jpg', 'jpeg', 'gif'}
UPLOAD_FOLDER = 'uploads'

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def processImage(filename, format_conversion=None, image_processing=None):
    print(f"Format Conversion: {format_conversion}, Image Processing: {image_processing}, Filename: {filename}")
    input_path = os.path.join("uploads", filename)
    img = cv2.imread(input_path)

    if img is None:
        print(f"Failed to load image: {input_path}")
        return None

    file_base = os.path.splitext(filename)[0]
    file_ext = os.path.splitext(filename)[1].lower().lstrip('.')
    img_processed = img.copy()

    # Apply image processing
    if image_processing:
        match image_processing:
            case "cgray":
                img_processed = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                file_base += "_gray"
            case "histeq":
                gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                img_processed = cv2.equalizeHist(gray)
                file_base += "_histeq"
            case "blur":
                img_processed = cv2.GaussianBlur(img, (5, 5), 0)
                file_base += "_blur"
            case "canny":
                img_processed = cv2.Canny(img, 100, 200)
                file_base += "_edges"
            case "rotate":
                img_processed = cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE)
                file_base += "_rotated"
            case "sharpen":
                kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])
                img_processed = cv2.filter2D(img, -1, kernel)
                file_base += "_sharpened"

    # Set new format extension
    ext_map = {
        "cwebp": "webp",
        "cpng": "png",
        "cjpg": "jpg",
        "cjpeg": "jpeg"
    }
    output_ext = ext_map.get(format_conversion, file_ext)

    # Ensure output folder exists
    output_dir = os.path.join("static", "uploads")
    os.makedirs(output_dir, exist_ok=True)

    # Compose output file path
    new_filename = f"{file_base}_processed.{output_ext}"
    output_path = os.path.join(output_dir, new_filename)

    # Save final processed image
    success = cv2.imwrite(output_path, img_processed)
    if not success:
        print(f"Failed to write image to {output_path}")
        return None

    return output_path
@app.route("/")
def home():
    if not current_user.is_authenticated:
        return redirect(url_for('login'))
    return render_template("index.html")

@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('home'))
        else:
            flash('Invalid username or password')
    
    return render_template('login.html')

@app.route("/signup", methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists')
            return redirect(url_for('signup'))
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered')
            return redirect(url_for('signup'))
        
        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        flash('Registration successful! Please login.')
        return redirect(url_for('login'))
    
    return render_template('signup.html')

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route("/about")
@login_required
def about():
    return render_template("about.html", title="About")


@app.route("/edit", methods=["GET", "POST"])
@login_required
def edit():
    if request.method == 'POST':
        # Annotation handling
        if 'annotated_image' in request.form and request.form['annotated_image']:
            data_url = request.form['annotated_image']
            original_filename = request.form['original_filename']
            edited_filename = request.form['edited_filename']

            header, encoded = data_url.split(",", 1)
            data = base64.b64decode(encoded)
            img = Image.open(BytesIO(data))

            annotated_path = os.path.join("static", "uploads", "annotated_" + os.path.basename(edited_filename))
            img.save(annotated_path)

            return render_template(
                "preview.html",
                original_filename=original_filename,
                edited_filename=os.path.relpath(annotated_path, "static").replace("\\", "/")
            )

        format_conversion = request.form.get("format_conversion")
        image_processing = request.form.get("image_processing")

        if 'file' not in request.files:
            flash('No file part in request')
            return redirect(url_for('edit'))

        files = request.files.getlist('file')

        if not files or files[0].filename == '':
            flash('No files selected')
            return redirect(url_for('edit'))

        processed_files = []
        error_files = []

        for file in files:
            try:
                if file and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    file.save(file_path)

                    processed_path = processImage(filename, format_conversion, image_processing)
                    if processed_path:
                        processed_files.append((filename, processed_path))
                    else:
                        error_files.append(f"{filename} (processing failed)")
                else:
                    error_files.append(f"{file.filename} (invalid file)")
            except Exception as e:
                error_files.append(f"{file.filename} (error: {str(e)})")

        if error_files:
            flash(f"Errors: {', '.join(error_files[:3])}{'...' if len(error_files) > 3 else ''}")

        if not processed_files:
            flash("No files processed")
            return redirect(url_for("edit"))

        # Handle single image preview
        if len(processed_files) == 1:
            filename, processed_file = processed_files[0]
            original_path = os.path.join('static', 'uploads', filename)
            uploaded_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            shutil.copy(uploaded_path, original_path)

            original_filename = f"uploads/{filename}".replace("\\", "/")
            edited_filename = os.path.relpath(processed_file, 'static').replace("\\", "/")

            return render_template(
                "preview.html",
                original_filename=original_filename,
                edited_filename=edited_filename
            )

        # Handle multiple files: zip download
        else:
            temp_dir = tempfile.mkdtemp()
            zip_path = os.path.join(temp_dir, "processed_images.zip")

            with zipfile.ZipFile(zip_path, 'w') as zipf:
                for _, file_path in processed_files:
                    zipf.write(file_path, os.path.basename(file_path))

            def cleanup():
                try:
                    shutil.rmtree(temp_dir)
                except Exception as e:
                    print(f"Cleanup error: {e}")

            response = send_file(
                zip_path,
                as_attachment=True,
                download_name="processed_images.zip",
                mimetype="application/zip"
            )
            response.call_on_close(cleanup)
            return response

    return render_template("index.html")
@app.route("/usage")
@login_required
def usage():
    return render_template("usage.html", title="Usage")

@app.route("/download/<path:filename>")
@login_required
def download(filename):
    file_path = os.path.join("static", filename)
    return send_file(file_path, as_attachment=True)

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        os.makedirs('static', exist_ok=True)
        os.makedirs('uploads', exist_ok=True)
    app.run(debug=True)