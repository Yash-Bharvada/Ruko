import cv2
import numpy as np

img = cv2.imread('frontend/public/frames/frame_0001.jpg')
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

# In the region x: 1050 to 1250, y: 520 to 680
# Look for the star watermark:
# The star is slightly lighter than the background
crop = gray[500:700, 1050:1250]
med = np.median(crop)
diff = np.abs(crop.astype(float) - med)

# Find coordinates of top differences
ys, xs = np.where(diff > 5)
if len(xs) > 0:
    min_x, max_x = xs.min() + 1050, xs.max() + 1050
    min_y, max_y = ys.min() + 500, ys.max() + 500
    print(f"Star bounding box: x=[{min_x}, {max_x}], y=[{min_y}, {max_y}]")
    print(f"Center: x={(min_x+max_x)//2}, y={(min_y+max_y)//2}, width={max_x-min_x}, height={max_y-min_y}")
else:
    print("No diff found")
