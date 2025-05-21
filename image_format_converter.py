import os
from PIL import Image

class ImageFormatConverter:
    """
    A utility class for Image-Iguana that allows converting images between different formats.
    Supports conversion to PNG, JPEG, WebP, GIF, TIFF, and BMP formats.
    """
    
    SUPPORTED_FORMATS = {
        'png': '.png',
        'jpg': '.jpg', 
        'jpeg': '.jpg',
        'webp': '.webp',
        'gif': '.gif',
        'tiff': '.tiff',
        'bmp': '.bmp'
    }
    
    @staticmethod
    def convert_image(input_path, output_format, output_directory=None, quality=85):
        """
        Convert an image to the specified format.
        
        Args:
            input_path (str): Path to the input image file.
            output_format (str): Desired output format (png, jpg, webp, etc.).
            output_directory (str, optional): Directory to save the output image. 
                                             If None, uses the same directory as input.
            quality (int, optional): Quality for lossy formats (1-100, higher is better). Default is 85.
            
        Returns:
            str: Path to the converted image if successful, None otherwise.
        """
        # Validate format
        output_format = output_format.lower()
        if output_format not in ImageFormatConverter.SUPPORTED_FORMATS:
            print(f"Error: Unsupported format '{output_format}'. Supported formats: {', '.join(ImageFormatConverter.SUPPORTED_FORMATS.keys())}")
            return None
        
        try:
            # Open the image
            img = Image.open(input_path)
            
            # Determine output path
            file_name = os.path.basename(input_path)
            file_name_without_ext = os.path.splitext(file_name)[0]
            extension = ImageFormatConverter.SUPPORTED_FORMATS[output_format]
            
            if output_directory is None:
                output_directory = os.path.dirname(input_path)
            
            # Create directory if it doesn't exist
            if output_directory and not os.path.exists(output_directory):
                os.makedirs(output_directory)
                
            output_path = os.path.join(output_directory, f"{file_name_without_ext}{extension}")
            
            # Convert and save
            if output_format in ['jpg', 'jpeg', 'webp']:
                # For formats that support quality parameter
                img.save(output_path, quality=quality)
            else:
                img.save(output_path)
                
            print(f"Successfully converted image to {output_format.upper()}: {output_path}")
            return output_path
            
        except Exception as e:
            print(f"Error converting image: {str(e)}")
            return None
    
    @staticmethod
    def batch_convert(input_directory, output_format, output_directory=None, quality=85):
        """
        Convert all images in a directory to the specified format.
        
        Args:
            input_directory (str): Directory containing images to convert.
            output_format (str): Desired output format.
            output_directory (str, optional): Directory to save the output images.
                                             If None, uses the same directory as input.
            quality (int, optional): Quality for lossy formats (1-100). Default is 85.
            
        Returns:
            list: Paths to the successfully converted images.
        """
        if not os.path.isdir(input_directory):
            print(f"Error: Input directory '{input_directory}' does not exist.")
            return []
            
        converted_files = []
        
        for filename in os.listdir(input_directory):
            # Skip non-image files and hidden files
            lower_filename = filename.lower()
            if not any(lower_filename.endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.tiff']):
                continue
                
            input_path = os.path.join(input_directory, filename)
            if os.path.isfile(input_path):
                result = ImageFormatConverter.convert_image(
                    input_path,
                    output_format,
                    output_directory,
                    quality
                )
                if result:
                    converted_files.append(result)
                    
        return converted_files


# Example usage
if __name__ == "__main__":
    # Convert a single image
    converter = ImageFormatConverter()
    converter.convert_image("path/to/image.jpg", "png")
    
    # Convert all images in a directory
    converter.batch_convert("path/to/images/", "webp", "path/to/output/", quality=90)