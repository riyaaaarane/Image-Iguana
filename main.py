from flask import Flask, render_template, request, flash,send_from_directory
from werkzeug.utils import secure_filename
import cv2
import os
import numpy as np

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

    # Handle format conversions
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

    # Handle image processing
    if image_processing:
        match image_processing:
            case "cgray":
                imgProcessed = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                newFilename = f"static/{filename}"
                cv2.imwrite(newFilename, imgProcessed)
                return newFilename
            case "histeq":
                imgGray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                imgProcessed = cv2.equalizeHist(imgGray)
                newFilename = f"static/{filename.split('.')[0]}_histeq.png"
                cv2.imwrite(newFilename, imgProcessed)
                return newFilename
            case "blur":
                imgProcessed = cv2.GaussianBlur(img, (5, 5), 0)
                newFilename = f"static/{filename.split('.')[0]}_blurred.png"
                cv2.imwrite(newFilename, imgProcessed)
                return newFilename
            case "canny":
                imgProcessed = cv2.Canny(img, 100, 200)
                newFilename = f"static/{filename.split('.')[0]}_edges.png"
                cv2.imwrite(newFilename, imgProcessed)
                return newFilename
            case "rotate":
                imgProcessed = cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE)
                newFilename = f"static/{filename.split('.')[0]}_rotated.png"
                cv2.imwrite(newFilename, imgProcessed)
                return newFilename
            case "sharpen":
                kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])
                imgProcessed = cv2.filter2D(img, -1, kernel)
                newFilename = f"static/{filename.split('.')[0]}_sharpened.png"
                cv2.imwrite(newFilename, imgProcessed)
                return newFilename

    return None

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
            new = processImage(filename, format_conversion, image_processing)
            if new:
                image_name = new.split('/')[-1]
                flash(f"Your image has been processed and is available "
                      f"<a href='/static/{image_name}' target='_blank'>View Image</a> or "
                      f"<a href='/download/{image_name}' target='_blank'>Download</a>")
            else:
                flash('Image processing failed. Please try again.')
                return render_template("error.html")

    else:
        flash('File type not allowed. Please upload an image file.')
        return render_template("error.html")
            
    return render_template("index.html")

# Download route
@app.route('/download/<path:filename>')
def download_file(filename):
    return send_from_directory('static', filename, as_attachment=True)

@app.route("/usage")
def usage():
    return render_template("usage.html", title="Usage")

if __name__ == "__main__":
    app.run(debug=True)  # Can specify the port too app.run(debug=True, port=5001)
