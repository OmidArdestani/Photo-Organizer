# Photo & Video Organizer

An enhanced Python tool to automatically organize your photos and videos by date and location. Supports iPhone formats (HEIC/HEIF) and video files with GPS metadata extraction.

## Features

✨ **Enhanced Media Support**
- Photos: JPG, JPEG, PNG, TIFF, BMP, GIF
- iPhone formats: HEIC, HEIF
- Videos: MP4, MOV, AVI, MKV, WMV, FLV, WebM, M4V, 3GP

📍 **Smart Organization**
- Organizes by Year/Month/Location
- GPS-based location detection with reverse geocoding
- Fallback to file creation date when metadata is missing

🔧 **Advanced Features**
- Duplicate file detection using MD5 hashing
- Progress tracking with progress bars
- Comprehensive logging
- Command-line interface
- Move or copy files
- Dry-run mode

## Installation

1. Clone the repository:
```bash
git clone https://github.com/OmidArdestani/Photo-Organizer.git
cd Photo-Organizer
```

2. Install Python dependencies:
```bash
pip install -r requirements.txt
```

### Optional Enhancements

For full iPhone support (HEIC/HEIF):
```bash
pip install pillow-heif
```

For enhanced video metadata support:
```bash
pip install hachoir
```

## Usage

### Basic Usage

Copy files (keeps originals):
```bash
python main.py -s "C:\Photos" -o "C:\Organized"
```

Move files (removes originals):
```bash
python main.py -s "C:\Photos" -o "C:\Organized" --move
```

### Advanced Options

Dry run (see what would happen without changing anything):
```bash
python main.py -s "C:\Photos" -o "C:\Organized" --dry-run
```

With debug logging:
```bash
python main.py -s "C:\Photos" -o "C:\Organized" --log-level DEBUG
```

### Command Line Arguments

- `-s, --source`: Source directory containing photos and videos (required)
- `-o, --output`: Output directory for organized media (required)
- `--move`: Move files instead of copying them
- `--dry-run`: Show what would be done without actually organizing files
- `--log-level`: Set logging level (DEBUG, INFO, WARNING, ERROR)

## Folder Structure

The tool creates an organized structure like this:

```
Organized/
├── 2024/
│   ├── 01-January/
│   │   ├── Paris_France/
│   │   │   ├── IMG_001.jpg
│   │   │   └── VID_001.mp4
│   │   └── Unknown_Location/
│   │       └── IMG_002.heic
│   └── 12-December/
│       └── New_York_United_States/
│           └── IMG_003.jpg
├── 2023/
│   └── ...
└── Unknown_Year/
    └── Unknown_Location/
        └── corrupted_file.jpg
```

## Supported Metadata

### Photos
- EXIF DateTimeOriginal, DateTime, DateTimeDigitized
- GPS coordinates from EXIF GPSInfo
- File creation date (fallback)

### Videos
- Creation date from video metadata
- File creation date (fallback)
- Note: GPS support for videos depends on format and metadata availability

## Logging

The tool creates a `photo_organizer.log` file with detailed information about:
- Processed files
- Errors and warnings
- GPS coordinates and location resolution
- Duplicate file detection

## Troubleshooting

### Missing Dependencies
If you see warnings about missing support:
- `HEIF/HEIC support not available`: Install `pillow-heif`
- `Video metadata support limited`: Install `hachoir`

### GPS/Location Issues
- Some files may not have GPS data
- Network required for reverse geocoding
- Rate limiting may slow down location resolution

### Common Issues
- **Permission errors**: Run as administrator or check file permissions
- **Large libraries**: Use `--move` to save disk space
- **Slow processing**: GPS lookups are cached but initial processing may be slow

## Examples

### iPhone Photos from iCloud
```bash
python main.py -s "C:\Users\Username\iCloudDrive\Photos" -o "D:\Organized Photos"
```

### Camera SD Card
```bash
python main.py -s "E:\DCIM" -o "C:\My Photos" --move
```

### Test Run First
```bash
python main.py -s "C:\Test Photos" -o "C:\Organized" --dry-run --log-level DEBUG
```

## Contributing

Feel free to submit issues and pull requests to improve the tool!

## License

This project is open source. Feel free to use and modify as needed.
