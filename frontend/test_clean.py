import cv2
import numpy as np

def remove_watermark(img):
    # The star watermark is centered at approx x: 1150..1170, y: 570..600
    # Let's create an inpaint mask around the star
    mask = np.zeros(img.shape[:2], dtype=np.uint8)
    
    # In the region x: 1130..1185, y: 555..615
    # The star shape is within this ~60x60 box in the bottom right corner
    cv2.circle(mask, (1157, 584), 38, 255, -1)
    
    # Inpaint using Navier-Stokes based method
    result = cv2.inpaint(img, mask, inpaintRadius=5, flags=cv2.INPAINT_NS)
    return result

img_light = cv2.imread('frontend/public/frames/frame_0001.jpg')
img_dark = cv2.imread('frontend/public/frames_dark/frame_0001.jpg')

res_light = remove_watermark(img_light)
res_dark = remove_watermark(img_dark)

cv2.imwrite('frontend/test_light_clean.jpg', res_light)
cv2.imwrite('frontend/test_dark_clean.jpg', res_dark)
print("Cleaned test frames written.")
