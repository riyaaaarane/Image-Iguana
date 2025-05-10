from flask import Flask, render_template, request, flash
from werkzeug.utils import secure_filename
import cv2
import os
import numpy as np
import time

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS 

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'webp', 'png', 'jpg', 'jpeg', 'gif'}

app = Flask(__name__)
app.secret_key = "secret key"
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def processImage(filename, format_conversion=None, image_processing=None):
    print(f"Format Conversion: {format_conversion}, Image Processing: {image_processing}, Filename: {filename}")
    img = cv2.imread(f"uploads/{filename}")
    print(image_processing)
    imgProcessed = img
    file_base = filename.rsplit('.', 1)[0]
    # Handle image processing
    if image_processing:
        match image_processing:
            case "cgray":
                imgProcessed = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                newFilename = f"static/{filename}"
                print("Grayed")
                cv2.imwrite(newFilename, imgProcessed)
            case "histeq":
                imgGray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                imgProcessed = cv2.equalizeHist(imgGray)
                newFilename = f"static/{filename.split('.')[0]}_histeq.png"
                cv2.imwrite(newFilename, imgProcessed)
            case "blur":
                imgProcessed = cv2.GaussianBlur(img, (5, 5), 0)
                newFilename = f"static/{filename.split('.')[0]}_blurred.png"
                cv2.imwrite(newFilename, imgProcessed)
            case "canny":
                imgProcessed = cv2.Canny(img, 100, 200)
                newFilename = f"static/{filename.split('.')[0]}_edges.png"
                cv2.imwrite(newFilename, imgProcessed)
            case "rotate":
                imgProcessed = cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE)
                newFilename = f"static/{filename.split('.')[0]}_rotated.png"
                cv2.imwrite(newFilename, imgProcessed)
                print("Image Rotated and saved to", newFilename)
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
    print(f"Saved: {newFilename}")
    return newFilename

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/about")
def about():
    return render_template("about.html", title="About")

@app.route("/edit", methods=["GET", "POST"])
def edit():
    if request.method == 'POST':
        format_conversion = request.form.get("format_conversion")
        image_processing = request.form.get("image_processing")
        # Check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return render_template("error.html")
        
        file = request.files['file']
        # If the user does not select a file, the browser submits an empty file without a filename.
        if file.filename == '':
            flash('No selected file')
            return render_template("error.html")
        elif file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            new = processImage(filename, format_conversion=format_conversion, image_processing=image_processing)
            print(new)
            flash(f"Your image has been processed and is available <a href='/{new}?t={int(time.time())}' target='_blank'>here!</a>")
            return render_template("index.html")
        else:
            flash('File type not allowed. Please upload an image file.')
            return render_template("error.html")
            
    return render_template("index.html")

@app.route("/usage")
def usage():
    return render_template("usage.html", title="Usage")

if __name__ == "__main__":
    app.run(debug=True)  # Can specify the port too app.run(debug=True, port=5001)
