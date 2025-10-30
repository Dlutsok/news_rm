#!/usr/bin/env python3
"""
Test script to check available YandexART models
"""
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from yandex_cloud_ml_sdk import YCloudML

# Get credentials
YC_FOLDER_ID = os.getenv("YC_FOLDER_ID", "")
YC_API_KEY = os.getenv("YC_API_KEY", "")

if not YC_FOLDER_ID or not YC_API_KEY:
    print("ERROR: YC_FOLDER_ID or YC_API_KEY not set")
    sys.exit(1)

print(f"Testing YandexART models...")
print(f"Folder ID: {YC_FOLDER_ID}")
print(f"API Key: {YC_API_KEY[:20]}...")
print()

# Initialize SDK
sdk = YCloudML(folder_id=YC_FOLDER_ID, auth=YC_API_KEY)

# Test different model names
model_names = [
    "yandex-art",           # Current default
    "yandex-art-latest",    # Maybe latest version?
    "yandex-art-2",         # YandexART 2.0?
    "yandex-art-2.0",       # YandexART 2.0 alternative?
    "yandex-art-2.5",       # YandexART 2.5?
    "yandex-art-pro",       # Pro version?
]

print("Testing available model names:")
print("-" * 60)

for model_name in model_names:
    try:
        model = sdk.models.image_generation(model_name)
        print(f"✅ {model_name:20} - AVAILABLE")
        print(f"   Type: {type(model).__name__}")
        print(f"   Methods: {[m for m in dir(model) if not m.startswith('_')][:5]}")
    except Exception as e:
        error_msg = str(e)[:80]
        print(f"❌ {model_name:20} - NOT AVAILABLE")
        print(f"   Error: {error_msg}")
    print()

# Try to get model info
print("-" * 60)
print("Current model configuration:")
try:
    model = sdk.models.image_generation("yandex-art")
    print(f"Model class: {type(model).__name__}")
    print(f"Model URI: {getattr(model, '_model_uri', 'N/A')}")
    print(f"Available methods: {[m for m in dir(model) if not m.startswith('_')]}")
except Exception as e:
    print(f"Error getting model info: {e}")
