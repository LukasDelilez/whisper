# -*- mode: python ; coding: utf-8 -*-
import sys
from PyInstaller.utils.hooks import collect_data_files
import os

block_cipher = None

# Get the absolute path to the project directory
project_dir = os.path.abspath(os.path.dirname('whisper_transcription.py'))

# Collect whisper model files
whisper_models = collect_data_files('whisper', include_py_files=True)

# Collect model files if they exist
models_dir = os.path.join(project_dir, "models")
model_files = []
if os.path.exists(models_dir):
    for model_file in os.listdir(models_dir):
        if model_file.endswith('.pt'):
            model_files.append((
                os.path.join(models_dir, model_file),
                os.path.join('models', model_file)
            ))

a = Analysis(
    ['whisper_transcription.py'],
    pathex=[],
    binaries=[],
    datas=[
        # Add FFmpeg path for Windows
        ('C:\\Users\\lukas\\AppData\\Local\\Microsoft\\WinGet\\Packages\\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\\ffmpeg-7.1-full_build\\bin\\ffmpeg.exe', '.'),
        ('C:\\Users\\lukas\\AppData\\Local\\Microsoft\\WinGet\\Packages\\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\\ffmpeg-7.1-full_build\\bin\\ffprobe.exe', '.')
    ] + whisper_models + model_files,
    hiddenimports=[
        'tiktoken',
        'scipy',
        'sounddevice',
        'numpy',
        'whisper',
        'pyperclip',
        'encodings',
        'tkinter',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='WhisperTranscription',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='app_icon.ico'  # Optional: Add this line if you have an icon
) 