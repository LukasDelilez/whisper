import os
import subprocess
import sys
import whisper
import sounddevice as sd
import numpy as np
import scipy.io.wavfile as wav
import tkinter as tk
from tkinter import scrolledtext, messagebox
import threading
import pyperclip

# Add FFmpeg to PATH at script startup with absolute paths
ffmpeg_dir = r"C:\Users\lukas\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-7.1-full_build\bin"
ffmpeg_exe = os.path.join(ffmpeg_dir, "ffmpeg.exe")
ffprobe_exe = os.path.join(ffmpeg_dir, "ffprobe.exe")

# Verify FFmpeg exists
if not os.path.exists(ffmpeg_exe):
    print(f"FFmpeg not found at: {ffmpeg_exe}")
    sys.exit(1)

# Set environment variables for FFmpeg
os.environ["FFMPEG_BINARY"] = ffmpeg_exe
os.environ["FFPROBE_BINARY"] = ffprobe_exe

# Also add to PATH
if ffmpeg_dir not in os.environ['PATH']:
    os.environ['PATH'] = os.environ['PATH'] + os.pathsep + ffmpeg_dir

# For whisper specifically
os.environ["PATH"] = ffmpeg_dir + os.pathsep + os.environ["PATH"]

# Globale Variablen
OUTPUT_FILENAME = os.path.join(os.path.dirname(os.path.abspath(__file__)), "recorded_audio.wav")
TRANSCRIPTION_TEXT = ""
is_recording = False
audio_data = []
sample_rate = 44100

# GUI-Klasse
class WhisperApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Whisper Transkriptions-Tool")
        self.root.geometry("600x400")
        
        # Define translations dictionary first
        self.translations = {
            "de": {
                "welcome": "Willkommen! Starte die Aufnahme, um die Transkription zu beginnen...",
                "start_recording": "Start Aufnahme",
                "stop_recording": "Stop Aufnahme",
                "copy_text": "Text kopieren",
                "recording_started": "Aufnahme gestartet...",
                "recording_stopped": "Aufnahme gestoppt. Speichere Datei...",
                "audio_saved": "Audio gespeichert als:",
                "file_not_found": "Warnung: Datei wurde nicht gefunden nach dem Speichern!",
                "transcription_started": "Transkription gestartet. Dies kann etwas dauern...",
                "no_text": "Es gibt keinen Text zum Kopieren.",
                "copied": "\nText wurde in die Zwischenablage kopiert!",
                "loading_model": "Lade Modell {}...",
                "model_loaded": "Modell geladen!"
            },
            "en": {
                "welcome": "Welcome! Start recording to begin transcription...",
                "start_recording": "Start Recording",
                "stop_recording": "Stop Recording",
                "copy_text": "Copy Text",
                "recording_started": "Recording started...",
                "recording_stopped": "Recording stopped. Saving file...",
                "audio_saved": "Audio saved as:",
                "file_not_found": "Warning: File not found after saving!",
                "transcription_started": "Transcription started. This may take a while...",
                "no_text": "There is no text to copy.",
                "copied": "\nText copied to clipboard!",
                "loading_model": "Loading model {}...",
                "model_loaded": "Model loaded!"
            }
        }

        # Add model selection variables before creating the dropdown
        self.whisper_models = ["tiny", "base", "small", "medium", "turbo"]
        self.selected_model = tk.StringVar(value="base")  # Default model

        # Add language selection frame at top
        self.lang_frame = tk.Frame(root)
        self.lang_frame.pack(anchor='ne', padx=10, pady=5)
        
        # Language selection buttons
        self.selected_lang = "en"  # Default language
        self.de_btn = tk.Label(self.lang_frame, text="Deutsch")
        self.en_btn = tk.Label(self.lang_frame, text="English")
        
        self.de_btn.pack(side=tk.LEFT, padx=2)
        self.en_btn.pack(side=tk.LEFT, padx=2)
        
        # Bind click events
        self.de_btn.bind("<Button-1>", lambda e: self.change_language("de"))
        self.en_btn.bind("<Button-1>", lambda e: self.change_language("en"))
        
        # Update initial language selection visual
        self.update_language_selection()
        
        # Define button colors
        self.default_color = "#ADD8E6"  # Light blue
        self.recording_color = "#90EE90"  # Light green
        self.stop_color = "#FFB6C1"      # Light red
        
        # Create a frame for the buttons and dropdown
        self.control_frame = tk.Frame(root)
        self.control_frame.pack(pady=10)
        
        # Move buttons to the control frame and pack them to the left
        self.start_button = tk.Button(self.control_frame, text=self.get_text("start_recording"), 
                                    command=self.start_recording,
                                    bg=self.default_color)
        self.start_button.pack(side=tk.LEFT, padx=5)
        
        self.stop_button = tk.Button(self.control_frame, text=self.get_text("stop_recording"), 
                                   command=self.stop_recording,
                                   state=tk.DISABLED,
                                   bg=self.default_color)
        self.stop_button.pack(side=tk.LEFT, padx=5)
        
        # Scrollbares Textfeld für Transkription
        self.text_area = scrolledtext.ScrolledText(root, wrap=tk.WORD, height=15)
        self.text_area.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.text_area.insert(tk.END, self.get_text("welcome") + "\n")
        self.text_area.config(state=tk.DISABLED)
        
        # Add model selection frame
        self.model_frame = tk.Frame(root)
        self.model_frame.pack(anchor='nw', padx=10, pady=5)
        
        # Add model selection dropdown
        tk.Label(self.model_frame, text="Model:").pack(side=tk.LEFT, padx=2)
        self.model_dropdown = tk.OptionMenu(self.model_frame, self.selected_model, *self.whisper_models)
        self.model_dropdown.pack(side=tk.LEFT, padx=2)
        
        # Set up cache directory based on whether we're running as exe or script
        if getattr(sys, 'frozen', False):
            # Running as executable
            self.cache_dir = os.path.join(os.path.dirname(sys.executable), "models")
        else:
            # Running as script
            self.cache_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "models")
        
        # Ensure cache directory exists and set environment variable
        self.ensure_cache_dir()
        os.environ["WHISPER_CACHE_DIR"] = self.cache_dir
        
        # Print debug info about cache directory
        print(f"Cache directory: {self.cache_dir}")
        print(f"Cache directory exists: {os.path.exists(self.cache_dir)}")
        print(f"Cache directory is writable: {os.access(self.cache_dir, os.W_OK)}")
    
    def ensure_cache_dir(self):
        """Create cache directory if it doesn't exist"""
        try:
            os.makedirs(self.cache_dir, exist_ok=True)
            print(f"Created/verified model cache directory: {self.cache_dir}")
            
            # Test write permissions by creating a test file
            test_file = os.path.join(self.cache_dir, "test.txt")
            try:
                with open(test_file, 'w') as f:
                    f.write("test")
                os.remove(test_file)
                print("Cache directory is writable")
            except Exception as e:
                print(f"Warning: Cache directory is not writable: {e}")
                
        except Exception as e:
            print(f"Error creating cache directory: {e}")
            # Try using a fallback location in user's home directory
            self.cache_dir = os.path.join(os.path.expanduser("~"), ".whisper_cache")
            os.makedirs(self.cache_dir, exist_ok=True)
            print(f"Using fallback cache directory: {self.cache_dir}")
    
    def get_cached_model_path(self, model_name):
        """Get path for cached model"""
        return os.path.join(self.cache_dir, f"{model_name}.pt")
    
    def is_model_cached(self, model_name):
        """Check if model is already cached"""
        model_path = self.get_cached_model_path(model_name)
        return os.path.exists(model_path)
    
    def get_text(self, key):
        """Helper method to get translated text"""
        return self.translations[self.selected_lang][key]
    
    def update_text_area(self, text):
        self.text_area.config(state=tk.NORMAL)
        self.text_area.insert(tk.END, text + "\n")
        self.text_area.see(tk.END)  # Scroll nach unten
        self.text_area.config(state=tk.DISABLED)

    def set_text_area(self, text):
        self.text_area.config(state=tk.NORMAL)
        self.text_area.delete(1.0, tk.END)
        self.text_area.insert(tk.END, text + "\n")
        self.text_area.see(tk.END)  # Scroll nach unten
        self.text_area.config(state=tk.DISABLED)
    
    def start_recording(self):
        global is_recording, audio_data
        is_recording = True
        audio_data = []
        self.set_text_area(self.get_text("recording_started"))
        
        # Update button states and colors
        self.start_button.config(state=tk.DISABLED, bg=self.recording_color)
        self.stop_button.config(state=tk.NORMAL, bg=self.stop_color)
        
        # Start audio recording in thread
        threading.Thread(target=self.record_audio).start()
    
    def record_audio(self):
        global is_recording, audio_data
        stream = sd.InputStream(samplerate=sample_rate, channels=1, dtype='int16', callback=self.audio_callback)
        with stream:
            while is_recording:
                sd.sleep(100)
    
    def audio_callback(self, indata, frames, time, status):
        global audio_data
        audio_data.append(indata.copy())
    
    def stop_recording(self):
        global is_recording, audio_data
        is_recording = False
        self.update_text_area(self.get_text("recording_stopped"))
        
        try:
            # Audio speichern
            full_audio = np.concatenate(audio_data, axis=0)
            wav.write(OUTPUT_FILENAME, sample_rate, full_audio)
            
            # Verify file exists after saving
            if os.path.exists(OUTPUT_FILENAME):
                self.update_text_area(f"{self.get_text('audio_saved')} {OUTPUT_FILENAME} ({os.path.abspath(OUTPUT_FILENAME)})")
            else:
                self.update_text_area(self.get_text("file_not_found"))
            
        except Exception as e:
            self.update_text_area(f"Fehler beim Speichern der Audio-Datei: {str(e)}")
            return
        
        # Starte Transkription in Thread
        threading.Thread(target=self.transcribe_audio).start()
    
    def transcribe_audio(self):
        global TRANSCRIPTION_TEXT
        self.update_text_area(self.get_text("transcription_started"))
        
        try:
            # Debug FFmpeg installation
            self.update_text_area("\nDebug FFmpeg:")
            self.update_text_area(f"FFMPEG_BINARY: {os.environ.get('FFMPEG_BINARY', 'Not set')}")
            self.update_text_area(f"FFmpeg exists: {os.path.exists(ffmpeg_exe)}")
            
            try:
                ffmpeg_result = subprocess.run([ffmpeg_exe, '-version'], 
                                             capture_output=True, text=True)
                self.update_text_area(f"FFmpeg version check: {ffmpeg_result.stdout.splitlines()[0]}")
            except Exception as e:
                self.update_text_area(f"FFmpeg check failed: {str(e)}")
            
            # Debug audio file
            abs_path = os.path.abspath(OUTPUT_FILENAME)
            self.update_text_area(f"\nDebug Audio File:")
            self.update_text_area(f"File path: {abs_path}")
            self.update_text_area(f"File exists: {os.path.exists(abs_path)}")
            self.update_text_area(f"File size: {os.path.getsize(abs_path)} bytes")
            
            # Load model - updated to use selected model
            model_name = self.selected_model.get()
            
            # Update text area with cache information
            self.update_text_area(f"\nCache directory: {self.cache_dir}")
            
            # Check if model is cached
            model_path = os.path.join(self.cache_dir, f"{model_name}.pt")
            if os.path.exists(model_path):
                self.update_text_area(f"Using cached model from: {model_path}")
            else:
                self.update_text_area(f"Model will be downloaded to: {model_path}")
            
            # Set environment variable for whisper
            os.environ["WHISPER_CACHE_DIR"] = self.cache_dir
            
            # Load model
            self.update_text_area(self.get_text("loading_model").format(model_name))
            model = whisper.load_model(model_name)
            self.update_text_area(self.get_text("model_loaded"))
            
            # Try transcription
            self.update_text_area("\nStarting transcription...")
            result = model.transcribe(
                abs_path,
                language=self.selected_lang,
                fp16=False,
                verbose=True
            )
            
            TRANSCRIPTION_TEXT = result["text"]
            self.set_text_area(TRANSCRIPTION_TEXT)
            
            # Automatically copy text to clipboard
            pyperclip.copy(TRANSCRIPTION_TEXT)
            self.update_text_area(self.get_text("copied"))
            
        except Exception as e:
            error_msg = f"Fehler bei der Transkription: {str(e)}\n"
            error_msg += f"Error type: {type(e).__name__}\n"
            
            import traceback
            error_msg += f"\nFull traceback:\n{traceback.format_exc()}"
            
            self.update_text_area(error_msg)
            print(f"Error details: {str(e)}")
        finally:
            self.start_button.config(state=tk.NORMAL, bg=self.default_color)
            self.stop_button.config(state=tk.DISABLED, bg=self.default_color)
    
    def copy_text(self):
        if TRANSCRIPTION_TEXT:
            pyperclip.copy(TRANSCRIPTION_TEXT)
            self.update_text_area(self.get_text("copied"))
        else:
            messagebox.showwarning("Info", self.get_text("no_text"))
    
    def change_language(self, lang):
        self.selected_lang = lang
        self.update_language_selection()
        
        # Update all GUI texts
        self.start_button.config(text=self.get_text("start_recording"))
        self.stop_button.config(text=self.get_text("stop_recording"))
        
        # Update welcome message if no transcription is present
        if not TRANSCRIPTION_TEXT:
            self.set_text_area(self.get_text("welcome"))
    
    def update_language_selection(self):
        # Reset borders
        self.de_btn.config(relief=tk.FLAT)
        self.en_btn.config(relief=tk.FLAT)
        
        # Set border for selected language
        if self.selected_lang == "de":
            self.de_btn.config(relief=tk.SOLID)
        else:
            self.en_btn.config(relief=tk.SOLID)

# Hauptprogramm
def main():  
    root = tk.Tk()
    app = WhisperApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
