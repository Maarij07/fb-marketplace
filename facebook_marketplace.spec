# -*- mode: python ; coding: utf-8 -*-
"""
Facebook Marketplace Automation - PyInstaller Spec File
Comprehensive configuration for creating a production-ready EXE
"""

import os
import sys
from pathlib import Path

# Define project paths
PROJECT_DIR = os.path.abspath('.')
WEB_TEMPLATES_DIR = os.path.join(PROJECT_DIR, 'web', 'templates')
WEB_STATIC_DIR = os.path.join(PROJECT_DIR, 'web', 'static')
CONFIG_DIR = os.path.join(PROJECT_DIR, 'config')

# Collect all data files and directories
datas = []

# Include web templates (HTML files)
if os.path.exists(WEB_TEMPLATES_DIR):
    for root, dirs, files in os.walk(WEB_TEMPLATES_DIR):
        for file in files:
            if file.endswith(('.html', '.htm')):
                src_path = os.path.join(root, file)
                dst_path = os.path.relpath(src_path, PROJECT_DIR)
                datas.append((src_path, os.path.dirname(dst_path)))

# Include static files (CSS, JS, images)
if os.path.exists(WEB_STATIC_DIR):
    for root, dirs, files in os.walk(WEB_STATIC_DIR):
        for file in files:
            if file.endswith(('.css', '.js', '.png', '.jpg', '.jpeg', '.gif', '.ico', '.svg')):
                src_path = os.path.join(root, file)
                dst_path = os.path.relpath(src_path, PROJECT_DIR)
                datas.append((src_path, os.path.dirname(dst_path)))

# Include configuration files
config_files = ['default_config.json', 'settings.json', '.env.example']
for config_file in config_files:
    config_path = os.path.join(CONFIG_DIR, config_file)
    if os.path.exists(config_path):
        datas.append((config_path, 'config'))

# Include root configuration files
root_config_files = ['.env', 'config.json', 'credentials.json']
for config_file in root_config_files:
    config_path = os.path.join(PROJECT_DIR, config_file)
    if os.path.exists(config_path):
        datas.append((config_path, '.'))

# Hidden imports for packages that might not be detected automatically
hiddenimports = [
    # Core application modules
    'config.settings',
    'core.scraper',
    'core.scheduler',
    'core.json_manager',
    'core.product_filter',
    'core.persistent_session',
    'core.deep_scraper',
    'core.excel_manager',
    'core.google_sheets_manager',
    'core.price_monitor',
    'core.notification_monitor',
    'web.app',
    
    # Essential dependencies
    'flask',
    'selenium',
    'requests',
    'apscheduler',
    'openpyxl',
    'bs4',
    'dotenv',
]

# Exclude problematic modules
excludes = [
    'tkinter',
    'matplotlib',
    'IPython',
    'jupyter',
    'test',
    'unittest',
    'distutils',
]

# Analysis configuration
a = Analysis(
    ['facebook_marketplace_launcher.py'],
    pathex=[PROJECT_DIR],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

# Remove duplicate files
pyz = PYZ(a.pure, a.zipped_data, cipher=None)

# EXE configuration
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='FacebookMarketplaceAutomation',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # Keep console for logging and user interaction
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # Add icon path here if you have one
    version_info=None,  # Add version info here if needed
)
