# Whisper Transcription App Setup and Usage

This application transcribes audio files using the Whisper library. Follow these steps to set up and run the application.

## Files Provided

1. **setup_whisper.sh**
   - Bash script to set up the environment.
   - Ensures Python, pip, and FFmpeg are installed.
   - Creates and configures a Python virtual environment.

2. **requirements.txt**
   - Contains the list of Python libraries required by the app.
   - Used to install dependencies with `pip`.

3. **build_linux.py**
   - Python script to package the application for distribution.
   - Builds the executable version of the app.

4. **whisper_transcription.py**
   - Main application script.
   - Handles audio transcription and includes a graphical user interface (GUI).

5. **whisper_app.spec**
   - PyInstaller specification file for building the app executable.

## Setup Instructions

1. **Run the Setup Script**
   Execute the setup script to prepare your environment:
   ```bash
   chmod +x setup_whisper.sh
   ./setup_whisper.sh
   ```
   The script will:
   - Check and install Python3, pip3, and FFmpeg if they are missing.
   - Create a Python virtual environment (`whisper_env`).
   - Install the required dependencies listed in `requirements.txt`.

2. **Build the Application**
   After setting up the environment, the script will automatically build the application using `build_linux.py`. If needed, you can manually run:
   ```bash
   python build_linux.py
   ```

3. **Run the Application**
   Activate the virtual environment and execute the app:
   ```bash
   source whisper_env/bin/activate
   python whisper_transcription.py
   ```

## Additional Information

- **Dependencies**:
  The app requires:
  - `whisper`
  - `sounddevice`
  - `numpy`
  - `scipy`
  - `tkinter`
  - `pyperclip`

- **FFmpeg**:
  Ensure FFmpeg is properly installed for audio handling.

- **Executable**:
  After building, you can find the executable in the `dist` folder (for Linux).

- **Virtual Environment**:
  Activate it using:
  ```bash
  source whisper_env/bin/activate
  