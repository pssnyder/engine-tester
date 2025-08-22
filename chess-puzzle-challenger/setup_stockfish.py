"""
Utility script to download and set up Stockfish chess engine.
"""

import os
import platform
import sys
import subprocess
import zipfile
import tarfile
import urllib.request
import shutil

def get_stockfish_url():
    """Get the appropriate Stockfish download URL based on the OS."""
    system = platform.system().lower()
    machine = platform.machine().lower()
    
    # Latest Stockfish version as of July 2025
    # Update this URL with the latest version available
    base_url = "https://stockfishchess.org/files/"
    
    if system == "windows":
        if "64" in machine or "amd64" in machine:
            return base_url + "stockfish-windows-x86-64.zip"
        else:
            return base_url + "stockfish-windows-x86-32.zip"
    elif system == "linux":
        if "64" in machine or "amd64" in machine:
            return base_url + "stockfish-ubuntu-x86-64.zip"
        else:
            return base_url + "stockfish-ubuntu-x86-32.zip"
    elif system == "darwin":  # macOS
        if "arm64" in machine:
            return base_url + "stockfish-macos-arm64.zip"
        else:
            return base_url + "stockfish-macos-x86-64.zip"
    else:
        raise ValueError(f"Unsupported system: {system} {machine}")

def download_file(url, target_path):
    """Download a file from URL to the target path."""
    print(f"Downloading from {url}...")
    
    try:
        urllib.request.urlretrieve(url, target_path)
        print(f"Downloaded to {target_path}")
    except Exception as e:
        print(f"Error downloading file: {e}")
        sys.exit(1)

def extract_archive(archive_path, extract_dir):
    """Extract the downloaded archive."""
    print(f"Extracting {archive_path}...")
    
    try:
        if archive_path.endswith('.zip'):
            with zipfile.ZipFile(archive_path, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)
        elif archive_path.endswith('.tar.gz') or archive_path.endswith('.tgz'):
            with tarfile.open(archive_path, 'r:gz') as tar_ref:
                tar_ref.extractall(extract_dir)
        else:
            print(f"Unsupported archive format: {archive_path}")
            sys.exit(1)
            
        print(f"Extracted to {extract_dir}")
    except Exception as e:
        print(f"Error extracting archive: {e}")
        sys.exit(1)

def find_executable(directory):
    """Find the Stockfish executable in the extracted directory."""
    system = platform.system().lower()
    
    # Expected executable names
    if system == "windows":
        exe_pattern = "stockfish*.exe"
    else:
        exe_pattern = "stockfish*"
    
    # Search for the executable
    for root, _, files in os.walk(directory):
        for file in files:
            if file.lower().startswith("stockfish") and (file.endswith(".exe") if system == "windows" else True):
                if os.access(os.path.join(root, file), os.X_OK) or system == "windows":
                    return os.path.join(root, file)
    
    return None

def main():
    """Main function to download and set up Stockfish."""
    print("Stockfish Chess Engine Setup")
    print("===========================")
    
    # Create engines directory if it doesn't exist
    engines_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "engines")
    os.makedirs(engines_dir, exist_ok=True)
    
    # Get the Stockfish download URL
    try:
        stockfish_url = get_stockfish_url()
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)
    
    # Download Stockfish
    archive_name = os.path.basename(stockfish_url)
    archive_path = os.path.join(engines_dir, archive_name)
    download_file(stockfish_url, archive_path)
    
    # Extract the archive
    extract_dir = os.path.join(engines_dir, "stockfish")
    os.makedirs(extract_dir, exist_ok=True)
    extract_archive(archive_path, extract_dir)
    
    # Find the executable
    executable_path = find_executable(extract_dir)
    if executable_path:
        print(f"Stockfish executable found at: {executable_path}")
        
        # Make the file executable on Unix systems
        if platform.system().lower() != "windows":
            os.chmod(executable_path, 0o755)
        
        # Create a config file with the engine path
        config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "engine_config.txt")
        with open(config_path, 'w') as f:
            f.write(executable_path)
        
        print(f"Engine path saved to {config_path}")
        print("\nSetup complete!")
        print(f"You can now use Stockfish with puzzle-challenger:")
        print(f"python -m src.main solve --engine {executable_path} --quantity 5")
    else:
        print("Error: Could not find Stockfish executable in the extracted files.")
        sys.exit(1)
    
    # Clean up the downloaded archive
    os.remove(archive_path)

if __name__ == "__main__":
    main()
