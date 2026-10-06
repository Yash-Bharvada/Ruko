import cv2
import numpy as np

# Load light and dark frame
img_light = cv2.imread('frontend/public/frames/frame_0001.jpg')
img_dark = cv2.imread('frontend/public/frames_dark/frame_0001.jpg')

h, w, _ = img_light.shape
print(f"Image dimensions: {w}x{h}")

# Star is in the bottom right region. Let's crop x: 1100 to 1200, y: 550 to 650
# Let's find the star in region x: 1000..1280, y: 500..720
roi_light = img_light[500:720, 1000:1280]
roi_dark = img_dark[500:720, 1000:1280]

cv2.imwrite('frontend/roi_light.jpg', roi_light)
cv2.imwrite('frontend/roi_dark.jpg', roi_dark)
print("Saved ROI")
