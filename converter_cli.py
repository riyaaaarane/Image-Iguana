import argparse
from image_format_converter import ImageFormatConverter

def main():
    """
    Command-line interface for Image-Iguana's format converter
    """
    parser = argparse.ArgumentParser(description="Convert images between different formats")
    
    # Create subparsers for single and batch conversion
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Single image conversion
    single_parser = subparsers.add_parser("convert", help="Convert a single image")
    single_parser.add_argument("input", help="Path to the input image")
    single_parser.add_argument("format", help="Output format (png, jpg, webp, gif, tiff, bmp)")
    single_parser.add_argument("-o", "--output-dir", help="Output directory (optional)")
    single_parser.add_argument("-q", "--quality", type=int, default=85, 
                             help="Quality for lossy formats (1-100, higher is better)")
    
    # Batch conversion
    batch_parser = subparsers.add_parser("batch", help="Convert multiple images in a directory")
    batch_parser.add_argument("input_dir", help="Directory containing images to convert")
    batch_parser.add_argument("format", help="Output format (png, jpg, webp, gif, tiff, bmp)")
    batch_parser.add_argument("-o", "--output-dir", help="Output directory (optional)")
    batch_parser.add_argument("-q", "--quality", type=int, default=85, 
                            help="Quality for lossy formats (1-100, higher is better)")
    
    args = parser.parse_args()
    
    if args.command == "convert":
        ImageFormatConverter.convert_image(
            args.input, 
            args.format, 
            args.output_dir, 
            args.quality
        )
    elif args.command == "batch":
        ImageFormatConverter.batch_convert(
            args.input_dir, 
            args.format, 
            args.output_dir, 
            args.quality
        )
    else:
        parser.print_help()

if __name__ == "__main__":
    main()