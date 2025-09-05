
import os
import sys
import shutil
import logging
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
from datetime import datetime
from geopy.geocoders import Nominatim
from time import sleep
import argparse
from pathlib import Path
import hashlib
from tqdm import tqdm

# Try to import additional libraries for enhanced support
try:
    from pillow_heif import register_heif_opener
    register_heif_opener()
    HEIF_SUPPORT = True
except ImportError:
    HEIF_SUPPORT = False
    print("⚠️  HEIF/HEIC support not available. Install pillow-heif for iPhone photo support.")

try:
    from hachoir.parser import createParser
    from hachoir.metadata import extractMetadata
    HACHOIR_SUPPORT = True
except ImportError:
    HACHOIR_SUPPORT = False
    print("⚠️  Video metadata support limited. Install hachoir for better video support.")

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('photo_organizer.log'),
        logging.StreamHandler()
    ]
)

# Supported file extensions
PHOTO_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.tiff', '.tif', '.bmp', '.gif'}
VIDEO_EXTENSIONS = {'.mp4', '.mov', '.avi', '.mkv', '.wmv', '.flv', '.webm', '.m4v', '.3gp'}
IPHONE_EXTENSIONS = {'.heic', '.heif'}  # iPhone specific formats

# All supported extensions
SUPPORTED_EXTENSIONS = PHOTO_EXTENSIONS | VIDEO_EXTENSIONS | IPHONE_EXTENSIONS

# Setup geocoder
geolocator = Nominatim(user_agent="photo_organizer_v2")

# Cache to avoid API throttling and file hashes to avoid duplicates
location_cache = {}
processed_files = set()  # To track duplicate files

def calculate_file_hash(file_path):
    """Calculate MD5 hash of a file to detect duplicates."""
    hash_md5 = hashlib.md5()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    except Exception as e:
        logging.error(f"Failed to calculate hash for {file_path}: {e}")
        return None

def get_file_creation_date(file_path):
    """Get file creation date from file system as fallback."""
    try:
        timestamp = os.path.getctime(file_path)
        return datetime.fromtimestamp(timestamp)
    except Exception as e:
        logging.error(f"Failed to get creation date for {file_path}: {e}")
        return None

def get_exif_data(image_path):
    """Extract EXIF data from image files."""
    try:
        with Image.open(image_path) as image:
            exif = image._getexif()
            if not exif:
                return {}
            exif_data = {}
            for tag, value in exif.items():
                decoded = TAGS.get(tag, tag)
                if decoded == "GPSInfo":
                    gps_data = {}
                    for gps_tag, gps_value in value.items():
                        gps_decoded = GPSTAGS.get(gps_tag, gps_tag)
                        gps_data[gps_decoded] = gps_value
                    exif_data[decoded] = gps_data
                else:
                    exif_data[decoded] = value
            return exif_data
    except Exception as e:
        logging.error(f"Failed to get EXIF data from {image_path}: {e}")
        return {}

def get_video_metadata(video_path):
    """Extract metadata from video files using hachoir."""
    if not HACHOIR_SUPPORT:
        return {}
    
    try:
        parser = createParser(video_path)
        if not parser:
            return {}
        
        metadata = extractMetadata(parser)
        if not metadata:
            return {}
        
        video_data = {}
        for line in metadata.exportPlaintext():
            if 'Creation date' in line or 'Date' in line:
                try:
                    # Extract date from metadata line
                    date_str = line.split(': ', 1)[1]
                    video_data['creation_date'] = date_str
                except:
                    continue
        return video_data
    except Exception as e:
        logging.error(f"Failed to get video metadata from {video_path}: {e}")
        return {}

def get_date_taken(file_path, exif_data=None, video_data=None):
    """Get the date when photo/video was taken."""
    # Try EXIF data first (for photos)
    if exif_data:
        for date_tag in ['DateTimeOriginal', 'DateTime', 'DateTimeDigitized']:
            if date_tag in exif_data:
                try:
                    return datetime.strptime(exif_data[date_tag], '%Y:%m:%d %H:%M:%S')
                except:
                    continue
    
    # Try video metadata
    if video_data and 'creation_date' in video_data:
        try:
            # Try different date formats
            date_str = video_data['creation_date']
            for fmt in ['%Y-%m-%d %H:%M:%S', '%Y:%m:%d %H:%M:%S', '%Y-%m-%dT%H:%M:%S']:
                try:
                    return datetime.strptime(date_str.split('.')[0], fmt)  # Remove microseconds
                except:
                    continue
        except:
            pass
    
    # Fallback to file creation date
    return get_file_creation_date(file_path)

def get_gps_info(exif_data):
    """Extract GPS coordinates from EXIF data."""
    gps_info = exif_data.get("GPSInfo")
    if not gps_info:
        return None, None

    def convert_to_degrees(value):
        """Convert GPS coordinates to decimal degrees."""
        try:
            if isinstance(value, (list, tuple)) and len(value) >= 3:
                d = float(value[0])
                m = float(value[1])
                s = float(value[2])
                return d + (m / 60.0) + (s / 3600.0)
            else:
                return float(value)
        except (ValueError, TypeError, ZeroDivisionError):
            return 0.0

    try:
        # Get latitude
        lat_ref = gps_info.get('GPSLatitudeRef', 'N')
        lat_data = gps_info.get('GPSLatitude')
        if lat_data:
            lat = convert_to_degrees(lat_data)
            if lat_ref == 'S':
                lat = -lat
        else:
            return None, None

        # Get longitude
        lon_ref = gps_info.get('GPSLongitudeRef', 'E')
        lon_data = gps_info.get('GPSLongitude')
        if lon_data:
            lon = convert_to_degrees(lon_data)
            if lon_ref == 'W':
                lon = -lon
        else:
            return None, None

        return lat, lon
    except Exception as e:
        logging.error(f"Failed to extract GPS info: {e}")
        return None, None

def get_location_name(lat, lon):
    """Get location name from GPS coordinates using reverse geocoding."""
    if not lat or not lon:
        return "Unknown_Location"
        
    # Round coordinates to reduce cache misses for nearby locations
    lat_rounded = round(lat, 3)
    lon_rounded = round(lon, 3)
    cache_key = (lat_rounded, lon_rounded)
    
    if cache_key in location_cache:
        return location_cache[cache_key]

    try:
        location = geolocator.reverse((lat, lon), language='en')
        if location:
            address = location.raw.get('address', {})
            # Try to get the most specific location available
            city = (address.get('city') or 
                   address.get('town') or 
                   address.get('village') or 
                   address.get('suburb') or 
                   address.get('neighbourhood') or
                   address.get('county') or
                   address.get('state'))
            country = address.get('country')
            
            # Create a clean name
            city_name = city.replace(" ", "_").replace(",", "") if city else "Unknown"
            country_name = country.replace(" ", "_").replace(",", "") if country else "Unknown"
            name = f"{city_name}_{country_name}"
            
            location_cache[cache_key] = name
            sleep(1)  # Avoid being blocked by Nominatim
            return name
    except Exception as e:
        logging.error(f"Geocode failed for ({lat}, {lon}): {e}")
    
    location_cache[cache_key] = "Unknown_Location"
    return "Unknown_Location"

def is_supported_file(file_path):
    """Check if file is a supported media format."""
    return Path(file_path).suffix.lower() in SUPPORTED_EXTENSIONS

def process_file(file_path, output_dir, move_files=False):
    """Process a single media file and organize it."""
    try:
        # Check for duplicates
        file_hash = calculate_file_hash(file_path)
        if file_hash and file_hash in processed_files:
            logging.info(f"Skipping duplicate file: {file_path}")
            return False
        
        if file_hash:
            processed_files.add(file_hash)
        
        # Get file extension
        file_ext = Path(file_path).suffix.lower()
        
        # Extract metadata based on file type
        exif_data = {}
        video_data = {}
        
        if file_ext in PHOTO_EXTENSIONS or file_ext in IPHONE_EXTENSIONS:
            exif_data = get_exif_data(file_path)
        elif file_ext in VIDEO_EXTENSIONS:
            video_data = get_video_metadata(file_path)
        
        # Get date and location
        date_taken = get_date_taken(file_path, exif_data, video_data)
        lat, lon = get_gps_info(exif_data) if exif_data else (None, None)
        
        # Create folder structure
        year = str(date_taken.year) if date_taken else "Unknown_Year"
        month = f"{date_taken.month:02d}-{date_taken.strftime('%B')}" if date_taken else "Unknown_Month"
        location = get_location_name(lat, lon) if lat and lon else "Unknown_Location"
        
        # Create destination folder: Year/Month/Location
        dest_folder = Path(output_dir) / year / month / location
        dest_folder.mkdir(parents=True, exist_ok=True)
        
        # Handle filename conflicts
        dest_file = dest_folder / Path(file_path).name
        counter = 1
        while dest_file.exists():
            stem = Path(file_path).stem
            suffix = Path(file_path).suffix
            dest_file = dest_folder / f"{stem}_{counter}{suffix}"
            counter += 1
        
        # Copy or move file
        if move_files:
            shutil.move(file_path, dest_file)
            logging.info(f"Moved: {file_path} → {dest_file}")
        else:
            shutil.copy2(file_path, dest_file)
            logging.info(f"Copied: {file_path} → {dest_file}")
        
        return True
        
    except Exception as e:
        logging.error(f"Failed to process {file_path}: {e}")
        return False

def organize_media(source_dir, output_dir, move_files=False):
    """Organize all media files in the source directory."""
    source_path = Path(source_dir)
    if not source_path.exists():
        logging.error(f"Source directory does not exist: {source_dir}")
        return
    
    # Find all supported files
    all_files = []
    for root, _, files in os.walk(source_dir):
        for file in files:
            file_path = os.path.join(root, file)
            if is_supported_file(file_path):
                all_files.append(file_path)
    
    if not all_files:
        logging.info("No supported media files found.")
        return
    
    logging.info(f"Found {len(all_files)} media files to process")
    
    # Process files with progress bar
    success_count = 0
    for file_path in tqdm(all_files, desc="Organizing files"):
        if process_file(file_path, output_dir, move_files):
            success_count += 1
    
    logging.info(f"Successfully processed {success_count}/{len(all_files)} files")
    print(f"📁 Organizing complete! Processed {success_count}/{len(all_files)} files")

def main():
    """Main function to parse arguments and run the organizer."""
    parser = argparse.ArgumentParser(
        description='Organize photos and videos by date and location',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py -s "C:/Photos" -o "C:/Organized" 
  python main.py -s "C:/Photos" -o "C:/Organized" --move
  python main.py -s "C:/Photos" -o "C:/Organized" --dry-run
        """
    )
    
    parser.add_argument('-s', '--source', required=True, 
                       help='Source directory containing photos and videos')
    parser.add_argument('-o', '--output', required=True,
                       help='Output directory for organized media')
    parser.add_argument('--move', action='store_true',
                       help='Move files instead of copying them')
    parser.add_argument('--dry-run', action='store_true',
                       help='Show what would be done without actually organizing files')
    parser.add_argument('--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                       default='INFO', help='Set the logging level')
    
    args = parser.parse_args()
    
    # Set logging level
    logging.getLogger().setLevel(getattr(logging, args.log_level))
    
    # Validate directories
    if not os.path.exists(args.source):
        logging.error(f"Source directory does not exist: {args.source}")
        return 1
    
    if args.dry_run:
        logging.info("DRY RUN MODE - No files will be moved or copied")
        # In dry run, we could show what would happen without actually doing it
        # For now, just log and exit
        logging.info(f"Would organize files from {args.source} to {args.output}")
        return 0
    
    # Create output directory if it doesn't exist
    os.makedirs(args.output, exist_ok=True)
    
    # Start organizing
    logging.info(f"Starting organization: {args.source} → {args.output}")
    organize_media(args.source, args.output, args.move)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
