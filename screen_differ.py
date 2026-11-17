from PIL import Image
import subprocess, time, os, math

def get_screen_hash_and_diff(ref_img_path, new_img_path):
    if not os.path.exists(ref_img_path):
        return 1.0 # 100% diff if no previous
    try:
        im1 = Image.open(ref_img_path).convert("L").resize((64, 64))
        im2 = Image.open(new_img_path).convert("L").resize((64, 64))
        p1 = list(im1.getdata())
        p2 = list(im2.getdata())
        diff_sq = sum((a - b) ** 2 for a, b in zip(p1, p2))
        rms = math.sqrt(diff_sq / len(p1))
        # Normalized diff: rms / 255.0
        return rms / 255.0
    except Exception as e:
        return 1.0

if __name__ == "__main__":
    print("Zero-token local diff analyzer ready.")
