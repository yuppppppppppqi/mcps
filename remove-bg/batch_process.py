from rembg import remove
from PIL import Image
import os

input_dir = "input"
output_dir = "output"
os.makedirs(output_dir, exist_ok=True)

# Images to process
images = ["bunny.png", "flower.png", "note.png", "star.png"]

for img_name in images:
    input_path = os.path.join(input_dir, img_name)
    output_path = os.path.join(output_dir, f"{os.path.splitext(img_name)[0]}_nobg.png")
    
    if not os.path.exists(input_path):
        print(f"Skipping {img_name} - file not found")
        continue
    
    print(f"Processing {img_name}...")
    
    try:
        input_image = Image.open(input_path)
        # Using default settings (no alpha matting)
        output_image = remove(input_image)
        output_image.save(output_path)
        print(f"  ✓ Saved to {output_path}")
    except Exception as e:
        print(f"  ✗ Error: {e}")

print("\nBatch processing complete!")
