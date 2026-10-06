import os
import cv2
import numpy as np
import concurrent.futures

def remove_watermark(img):
    mask = np.zeros(img.shape[:2], dtype=np.uint8)
    # Circle covering the watermark star
    cv2.circle(mask, (1156, 582), 46, 255, -1)
    result = cv2.inpaint(img, mask, inpaintRadius=5, flags=cv2.INPAINT_TELEA)
    return result

def process_file(filepath):
    img = cv2.imread(filepath)
    if img is not None:
        clean = remove_watermark(img)
        cv2.imwrite(filepath, clean, [int(cv2.IMWRITE_JPEG_QUALITY), 95])

def main():
    print("Starting watermark removal for all 240 light and 240 dark frames...")
    
    light_files = [f"frontend/public/frames/frame_{i:04d}.jpg" for i in range(1, 241)]
    dark_files = [f"frontend/public/frames_dark/frame_{i:04d}.jpg" for i in range(1, 241)]
    all_files = light_files + dark_files
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        list(executor.map(process_file, all_files))
        
    print("All 480 frames cleaned successfully!")

if __name__ == "__main__":
    main()
