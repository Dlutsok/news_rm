#!/usr/bin/env python3
"""
Compare image quality across different YandexART models
"""
import os
import sys
from pathlib import Path
import asyncio
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from yandex_cloud_ml_sdk import YCloudML

# Get credentials
YC_FOLDER_ID = os.getenv("YC_FOLDER_ID", "")
YC_API_KEY = os.getenv("YC_API_KEY", "")

if not YC_FOLDER_ID or not YC_API_KEY:
    print("ERROR: YC_FOLDER_ID or YC_API_KEY not set")
    sys.exit(1)

# Test prompt (medical context)
TEST_PROMPT = """Фотореалистичная фотография: Врач в белом халате проводит УЗИ диагностику беременной женщине в современном медицинском кабинете.
Снято камерой Canon EOS, естественное дневное освещение, реальная земная обстановка, подлинные материалы и текстуры.
Документальный стиль, как в National Geographic, реальные физические объекты, обычная земная среда, достоверные пропорции и перспектива."""

# Models to test
MODELS = [
    ("yandex-art", "YandexART (default/legacy)"),
    ("yandex-art-latest", "YandexART Latest"),
    ("yandex-art-2", "YandexART 2.0"),
    ("yandex-art-2.5", "YandexART 2.5"),
]

# Output directory
OUTPUT_DIR = Path(__file__).parent.parent / "storage" / "model_comparison"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

print("=" * 80)
print("YandexART Models Quality Comparison")
print("=" * 80)
print(f"Test prompt: {TEST_PROMPT[:100]}...")
print(f"Output directory: {OUTPUT_DIR}")
print()

# Initialize SDK
sdk = YCloudML(folder_id=YC_FOLDER_ID, auth=YC_API_KEY)

results = []

for model_name, model_desc in MODELS:
    print(f"\nTesting: {model_desc} ({model_name})")
    print("-" * 80)

    try:
        # Get model
        model = sdk.models.image_generation(model_name)
        model = model.configure(width_ratio=1, height_ratio=1, seed=42)  # Same seed for comparison

        # Generate
        start_time = datetime.now()
        print(f"⏳ Generating image...")

        operation = model.run_deferred(TEST_PROMPT)
        result = operation.wait()

        generation_time = (datetime.now() - start_time).total_seconds()

        # Save image
        image_bytes = result.image_bytes
        if image_bytes:
            filename = f"{model_name.replace('.', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpeg"
            filepath = OUTPUT_DIR / filename
            filepath.write_bytes(image_bytes)

            file_size_kb = len(image_bytes) / 1024

            print(f"✅ SUCCESS")
            print(f"   Generation time: {generation_time:.2f}s")
            print(f"   File size: {file_size_kb:.1f} KB")
            print(f"   Saved to: {filename}")

            results.append({
                "model": model_name,
                "description": model_desc,
                "success": True,
                "time": generation_time,
                "size_kb": file_size_kb,
                "file": filename
            })
        else:
            print(f"❌ FAIL: Empty response")
            results.append({
                "model": model_name,
                "description": model_desc,
                "success": False,
                "error": "Empty response"
            })

    except Exception as e:
        print(f"❌ ERROR: {str(e)[:200]}")
        results.append({
            "model": model_name,
            "description": model_desc,
            "success": False,
            "error": str(e)[:200]
        })

# Summary
print("\n" + "=" * 80)
print("COMPARISON SUMMARY")
print("=" * 80)

successful_results = [r for r in results if r["success"]]

if successful_results:
    print("\n✅ Successful generations:")
    print(f"{'Model':<30} {'Time':<12} {'Size':<12} {'File':<30}")
    print("-" * 84)
    for r in successful_results:
        print(f"{r['description']:<30} {r['time']:.2f}s      {r['size_kb']:.1f} KB     {r['file']}")

    # Find best model
    fastest = min(successful_results, key=lambda x: x["time"])
    print(f"\n🏆 Fastest: {fastest['description']} ({fastest['time']:.2f}s)")

    print("\n📊 Quality comparison:")
    print("   Please manually review images in:")
    print(f"   {OUTPUT_DIR}")
    print("\n   Compare:")
    print("   - Photorealism (как настоящее фото?)")
    print("   - Medical accuracy (правильность медицинской сцены)")
    print("   - Prompt adherence (соответствие запросу)")
    print("   - Artifacts (дефекты, искажения)")
    print("   - Overall impression (общее впечатление)")

failed_results = [r for r in results if not r["success"]]
if failed_results:
    print("\n\n❌ Failed generations:")
    for r in failed_results:
        print(f"   {r['description']}: {r['error']}")

print("\n" + "=" * 80)
print("RECOMMENDATION")
print("=" * 80)

if len(successful_results) >= 2:
    print("""
Based on Yandex's announcement (March 2025):
- YandexART 2.5 has improved prompt following (+30% text accuracy)
- YandexART 2.5 creates more realistic images without fantasy elements
- YandexART 2.5 is better for real-life object design

RECOMMENDED: Switch to 'yandex-art-2.5' or 'yandex-art-latest'

Next steps:
1. Manually review generated images above
2. If quality is better, update backend/api/image_generation.py line 110:
   Change: model = sdk.models.image_generation("yandex-art")
   To:     model = sdk.models.image_generation("yandex-art-2.5")
3. Test in production with real medical news content
""")
else:
    print("Too many failures to make a recommendation. Check API access and credentials.")
