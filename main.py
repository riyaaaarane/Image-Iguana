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
    img = cv2.imread(f"uploads/{filename}")
    
    if img is None:
        print(f"Failed to load image: uploads/{filename}")
        return None

    if format_conversion:
        match format_conversion:
            case "cwebp":
                newFilename = f"static/{filename.split('.')[0]}.webp"
                cv2.imwrite(newFilename, img)
                return newFilename
            case "cpng":
                newFilename = f"static/{filename.split('.')[0]}.png"
                cv2.imwrite(newFilename, img)
                return newFilename
            case "cjpg":
                newFilename = f"static/{filename.split('.')[0]}.jpg"
                cv2.imwrite(newFilename, img)
                return newFilename
            case "cjpeg":
                newFilename = f"static/{filename.split('.')[0]}.jpeg"
                cv2.imwrite(newFilename, img)
                return newFilename


    output_dir = "static/uploads"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    base = filename.rsplit('.', 1)[0]
    ext = filename.rsplit('.', 1)[1]

    # 1. Apply image processing if selected
    if image_processing:
        match image_processing:
            case "cgray":
                img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                base += "_gray"
                imgProcessed = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                newFilename = f"static/{filename}"
                cv2.imwrite(newFilename, imgProcessed)
            case "histeq":
                imgGray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                imgProcessed = cv2.equalizeHist(imgGray)
                newFilename = f"static/{filename.split('.')[0]}_histeq.png"
                cv2.imwrite(newFilename, imgProcessed)
                img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                img = cv2.equalizeHist(img)
                base += "_histeq"
            case "blur":
                imgProcessed = cv2.GaussianBlur(img, (5, 5), 0)
                newFilename = f"static/{filename.split('.')[0]}_blurred.png"
                cv2.imwrite(newFilename, imgProcessed)
                img = cv2.GaussianBlur(img, (5, 5), 0)
                base += "_blurred"
            case "canny":
                imgProcessed = cv2.Canny(img, 100, 200)
                newFilename = f"static/{filename.split('.')[0]}_edges.png"
                cv2.imwrite(newFilename, imgProcessed)
                img = cv2.Canny(img, 100, 200)
                base += "_edges"
            case "rotate":
                img = cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE)
                base += "_rotated"
                imgProcessed = cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE)
                newFilename = f"static/{filename.split('.')[0]}_rotated.png"
                cv2.imwrite(newFilename, imgProcessed)
            case "sharpen":
                kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])
                imgProcessed = cv2.filter2D(img, -1, kernel)
                newFilename = f"static/{filename.split('.')[0]}_sharpened.png"
                cv2.imwrite(newFilename, imgProcessed)

    file_format = filename.rsplit('.', 1)[1].lower()
    new_format = file_format

    # Handle Format Conversions Simultaneously also if required by user
    if format_conversion:
        if format_conversion == "cwebp":
            new_format= "webp"
        elif format_conversion == "cpng":
            new_format = "png"
        elif format_conversion == "cjpg":
            new_format = "jpg"
        elif format_conversion == "cjpeg":
            new_format = "jpeg"

    # --- Final output filename ---
    newFilename = f"static/{file_base}_processed.{new_format}"
    cv2.imwrite(newFilename, imgProcessed)
    return newFilename
                img = cv2.filter2D(img, -1, kernel)
                base += "_sharpened"

    # 2. Apply format conversion if selected
    if format_conversion:
        match format_conversion:
            case "cwebp":
                ext = "webp"
            case "cpng":
                ext = "png"
            case "cjpg":
                ext = "jpg"
            case "cjpeg":
                ext = "jpeg"

    # 3. Save the final image
    newFilename = f"{output_dir}/{base}.{ext}"
    cv2.imwrite(newFilename, img)
    return newFilename

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
        # Handle annotation submission
        if 'annotated_image' in request.form and request.form['annotated_image']:
            data_url = request.form['annotated_image']
            original_filename = request.form['original_filename']  # Always the true original
            edited_filename = request.form['edited_filename']      # The current edited image

            # Decode base64 image
            header, encoded = data_url.split(",", 1)
            data = base64.b64decode(encoded)
            img = Image.open(BytesIO(data))
            # Save annotated image (always create a new file)
            annotated_path = os.path.join("static", "uploads", "annotated_" + os.path.basename(edited_filename))
            img.save(annotated_path)
            return render_template(
                "preview.html",
                original_filename=original_filename,  # Always show the true original
                edited_filename=os.path.relpath(annotated_path, "static").replace("\\", "/")
            )
        format_conversion = request.form.get("format_conversion")
        image_processing = request.form.get("image_processing")

        if 'file' not in request.files:
            flash('No file part in request')
            return redirect(url_for('edit'))
        
        files = request.files.getlist('file')
        
        if len(files) == 0 or files[0].filename == '':
            flash('No files selected for upload')
            return redirect(url_for('edit'))
        
        processed_files = []
        error_files = []
        
        for file in files:
            try:
                if file and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    file.save(file_path)
                    
                    processed_file = processImage(filename, format_conversion, image_processing)
                    
                    if processed_file:
                        processed_files.append(processed_file)
                    else:
                        error_files.append(f"{filename} (processing failed)")
                else:
                    error_files.append(f"{file.filename} (invalid type)")
            except Exception as e:
                error_files.append(f"{file.filename} (error: {str(e)}")
        
        if error_files:
            flash(f"Errors with {len(error_files)} file(s): {', '.join(error_files[:3])}{'...' if len(error_files) > 3 else ''}")
        
        if not processed_files:
            flash('No files were processed successfully')
            return redirect(url_for('edit'))
        
        if len(processed_files) == 1:
            download_filename = os.path.basename(processed_files[0])
            return send_file(
                processed_files[0],
                as_attachment=True,
                download_name=download_filename,
                mimetype='image/png'
            )
        else:
            try:
                temp_dir = tempfile.mkdtemp()
                zip_path = os.path.join(temp_dir, 'processed_images.zip')
                
                with zipfile.ZipFile(zip_path, 'w') as zipf:
                    for file_path in processed_files:
                        zipf.write(file_path, os.path.basename(file_path))
                
                # Create a cleanup function
                def cleanup():
                    try:
                        shutil.rmtree(temp_dir)
                    except Exception as e:
                        print(f"Cleanup error: {e}")
                
                # Send file with callback for cleanup
                response = send_file(
                    zip_path,
                    as_attachment=True,
                    download_name='processed_images.zip',
                    mimetype='application/zip'
                )
                
                # Set callback to run after response is sent
                response.call_on_close(cleanup)
                return response
                
            except Exception as e:
                flash(f'Error creating zip file: {str(e)}')
                return redirect(url_for('edit'))
        file = request.files['file']
        if file.filename == '':
            flash('No selected file')
            return render_template("error.html")
        elif file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            processed_file = processImage(filename, format_conversion, image_processing)
            
            if processed_file:
                # Always copy uploaded file to static/uploads for preview
                import shutil
                original_path = os.path.join('static', 'uploads', filename)
                uploaded_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                shutil.copy(uploaded_path, original_path)  # Overwrite every time

                original_filename = f"uploads/{filename}".replace("\\", "/")
                edited_filename = os.path.relpath(processed_file, 'static').replace("\\", "/")
                return render_template(
                    "preview.html",
                    original_filename=original_filename,
                    edited_filename=edited_filename
                )
            else:
                flash('Error processing image')
                return render_template("error.html")
        else:
            flash('File type not allowed. Please upload an image file.')
            return render_template("error.html")
            
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