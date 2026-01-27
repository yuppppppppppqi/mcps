from rembg import remove
from PIL import Image
import os

input_path = os.path.join("input", "kawaii_cat_button_frame.png")
output_dir = "output"
os.makedirs(output_dir, exist_ok=True)

# Round 2 Variations based on feedback (FG 150 was best so far)
# Testing lower FG thresholds and different erode settings around that point
variations = [
    # Previous best for reference
    {"name": "ref_fg150_ae10", "afg": 150, "abg": 10, "ae": 10},
    
    # Lowering FG threshold further (keep even more)
    {"name": "fg100_ae10", "afg": 100, "abg": 10, "ae": 10},
    {"name": "fg050_ae10", "afg": 50, "abg": 10, "ae": 10},
    
    # Adjusting Erode on the "good" FG setting
    {"name": "fg150_ae00 (Sensitivity)", "afg": 150, "abg": 10, "ae": 0},
    {"name": "fg150_ae05 (Mild)", "afg": 150, "abg": 10, "ae": 5},
    {"name": "fg150_ae20 (Smooth)", "afg": 150, "abg": 10, "ae": 20},
    
    # Adjusting Background threshold with good FG (clean up noise)
    {"name": "fg150_bg50", "afg": 150, "abg": 50, "ae": 10},
]

print(f"Processing {input_path}...")
input_image = Image.open(input_path)

for v in variations:
    name = v["name"].replace(" ", "_").replace("(", "").replace(")", "")
    output_path = os.path.join(output_dir, f"r2_{name}.png")
    
    print(f"Generating {name} (afg={v['afg']}, abg={v['abg']}, ae={v['ae']})...")
    
    try:
        output_image = remove(
            input_image,
            alpha_matting=True,
            alpha_matting_foreground_threshold=v['afg'],
            alpha_matting_background_threshold=v['abg'],
            alpha_matting_erode_size=v['ae']
        )
        output_image.save(output_path)
    except Exception as e:
        print(f"Error generating {name}: {e}")

print("Done! Check the output directory for 'r2_' files.")
