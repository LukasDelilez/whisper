import os
import shutil
import subprocess
import sys
import time

def remove_readonly(func, path, excinfo):
    """Error handler for shutil.rmtree that attempts to handle read-only files"""
    os.chmod(path, 0o666)
    try:
        func(path)
    except PermissionError:
        time.sleep(0.1)  # Wait briefly
        try:
            func(path)
        except PermissionError as e:
            print(f"Warning: Could not remove {path}: {e}")

def copy_cached_models(dist_folder):
    """Copy cached models to distribution folder"""
    models_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "models")
    if os.path.exists(models_dir):
        dist_models_dir = os.path.join(dist_folder, "models")
        os.makedirs(dist_models_dir, exist_ok=True)
        
        # Copy all cached models
        for model_file in os.listdir(models_dir):
            if model_file.endswith('.pt'):
                src = os.path.join(models_dir, model_file)
                dst = os.path.join(dist_models_dir, model_file)
                print(f"Copying cached model: {model_file}")
                shutil.copy2(src, dst)

def prepare_models_directory(dist_folder):
    """Prepare models directory in distribution"""
    models_dir = os.path.join(dist_folder, "models")
    os.makedirs(models_dir, exist_ok=True)
    
    # Create a .keep file to ensure the directory is included
    with open(os.path.join(models_dir, ".keep"), "w") as f:
        f.write("This directory is used for caching Whisper models.")
    
    # Copy any existing cached models
    source_models = os.path.join(os.path.dirname(os.path.abspath(__file__)), "models")
    if os.path.exists(source_models):
        for model_file in os.listdir(source_models):
            if model_file.endswith('.pt'):
                src = os.path.join(source_models, model_file)
                dst = os.path.join(models_dir, model_file)
                print(f"Copying cached model: {model_file}")
                shutil.copy2(src, dst)

def build_executable():
    print("Starting build process...")
    
    # Create build and dist directories if they don't exist
    for dir_name in ['build', 'dist']:
        if os.path.exists(dir_name):
            print(f"Cleaning {dir_name} directory...")
            try:
                shutil.rmtree(dir_name, onerror=remove_readonly)
            except Exception as e:
                print(f"Warning: Could not fully clean {dir_name}: {e}")
                print("Continuing with build process...")
        
        try:
            os.makedirs(dir_name, exist_ok=True)
        except Exception as e:
            print(f"Error creating directory {dir_name}: {e}")
            return
    
    try:
        # Install required packages
        print("Installing required packages...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        
        # Build the executable
        print("Building executable...")
        subprocess.check_call([
            "pyinstaller",
            "--clean",
            "whisper_app.spec"
        ])
        
        # Create distribution folder
        dist_folder = "WhisperTranscription_dist"
        if os.path.exists(dist_folder):
            print(f"Cleaning {dist_folder} directory...")
            try:
                shutil.rmtree(dist_folder, onerror=remove_readonly)
            except Exception as e:
                print(f"Warning: Could not fully clean {dist_folder}: {e}")
        
        os.makedirs(dist_folder, exist_ok=True)
        
        # Copy executable and dependencies
        print("Creating distribution package...")
        shutil.copy("dist/WhisperTranscription.exe", dist_folder)
        
        # Copy cached models
        print("Copying cached models...")
        copy_cached_models(dist_folder)
        
        # Prepare models directory
        print("Preparing models directory...")
        prepare_models_directory(dist_folder)
        
        # Create README file
        with open(os.path.join(dist_folder, "README.txt"), "w", encoding='utf-8') as f:
            f.write("""Whisper Transcription Tool

First Time Setup:
1. Run WhisperTranscription.exe
2. Models will be cached in the 'models' directory next to the executable
3. First run for each model will require downloading (internet connection needed)

Cache Information:
- Models are stored in the 'models' directory next to the executable
- Once downloaded, models are reused for future transcriptions
- The application needs write permission in its directory

Pre-cached models (if included):
- base.pt
- small.pt
- tiny.pt (if downloaded)

Troubleshooting:
- Ensure the application has write permissions in its directory
- If caching fails, models will be stored in %USERPROFILE%\\.whisper_cache
- Check the application output for detailed cache location information
""")
        
        print("Build complete! Distribution package created in:", dist_folder)

    except subprocess.CalledProcessError as e:
        print(f"Error during build process: {e}")
        print(f"Command that failed: {e.cmd}")
        print(f"Output: {e.output if hasattr(e, 'output') else 'No output available'}")
    except Exception as e:
        print(f"Unexpected error during build process: {e}")

if __name__ == "__main__":
    try:
        build_executable()
    except KeyboardInterrupt:
        print("\nBuild process interrupted by user")
    except Exception as e:
        print(f"Fatal error: {e}") 