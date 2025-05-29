# Image Iguana

**Image Iguana** is a versatile image processing application designed to help users manage, edit, and enhance their images effortlessly. With a user-friendly interface and powerful features, Image Iguana is suitable for both beginners and professionals alike.

## Features

- **Image Editing**: Crop, resize, and adjust brightness/contrast.
- **Filters and Effects**: Apply various filters to enhance your images.
- **Batch Processing**: Process multiple images at once for efficiency.
- **User-Friendly Interface**: Intuitive design for easy navigation.
- **Cross-Platform Support**: Available on Windows, macOS, and Linux.

## Installation

To install Image Iguana, follow these steps:

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/image-iguana.git
   ```
2. Navigate to the project directory:
   ```
   cd image-iguana
   ```

3. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```
4. Run the application:
   ```
   python main.py
   ```

To install Image Iguana using Docker, follow these steps:
1. Check if you have Docker installed, if not install it from [here](https://docs.docker.com/get-docker/).
   ```bash
   docker --version
   ```
2. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/image-iguana.git
   ```
3. Navigate to the project directory:
   ```bash
   cd image-iguana
   ```
4. Build the Docker image:
   ```bash
   docker build -t image-iguana .
   ```
5. Run the Docker container:
   ```bash
   docker run -it --rm -p 8080:8080 image-iguana
   ```
      

## Fixes

1. For Linux you might need to install libGL1 in your system required for OpenCV:
   ```
   sudo apt update
   sudo apt install libgl1
   ```