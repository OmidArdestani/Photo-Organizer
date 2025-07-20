#!/usr/bin/env python3
"""
Setup and test script for Photo Organizer
"""

import subprocess
import sys
import os

def install_dependencies():
    """Install required and optional dependencies."""
    print("🔧 Installing core dependencies...")
    
    # Core dependencies
    core_deps = [
        "Pillow>=10.0.0",
        "geopy>=2.3.0", 
        "tqdm>=4.64.0"
    ]
    
    for dep in core_deps:
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", dep])
            print(f"✅ Installed: {dep}")
        except subprocess.CalledProcessError:
            print(f"❌ Failed to install: {dep}")
    
    # Optional dependencies
    print("\n🔧 Installing optional dependencies for enhanced support...")
    optional_deps = [
        ("pillow-heif", "iPhone HEIC/HEIF support"),
        ("hachoir", "Enhanced video metadata support")
    ]
    
    for dep, description in optional_deps:
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", dep])
            print(f"✅ Installed: {dep} ({description})")
        except subprocess.CalledProcessError:
            print(f"⚠️  Optional: {dep} ({description}) - install manually if needed")

def create_test_structure():
    """Create a test directory structure."""
    test_dir = "test_photos"
    if not os.path.exists(test_dir):
        os.makedirs(test_dir)
        print(f"📁 Created test directory: {test_dir}")
        print("   Add some photos/videos here to test the organizer!")
    return os.path.abspath(test_dir)

def main():
    print("🚀 Photo Organizer Setup")
    print("=" * 50)
    
    # Install dependencies
    install_dependencies()
    
    # Create test structure
    test_dir = create_test_structure()
    output_dir = os.path.abspath("organized_photos")
    
    print("\n📋 Usage Examples:")
    print("=" * 50)
    print(f"# Test with sample files:")
    print(f'python main.py -s "{test_dir}" -o "{output_dir}" --dry-run')
    print()
    print(f"# Organize your actual photos:")
    print(f'python main.py -s "C:/Users/YourName/Pictures" -o "C:/Organized" --dry-run')
    print()
    print(f"# iPhone photos from iCloud:")
    print(f'python main.py -s "C:/Users/YourName/iCloudDrive/Photos" -o "D:/Organized"')
    print()
    print("📖 See README.md for full documentation!")

if __name__ == "__main__":
    main()
