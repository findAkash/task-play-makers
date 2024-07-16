from typing import Tuple
from PIL import Image
import numpy as np


def is_happy_image(image_path: str, happy_threshold=0.10) -> Tuple[bool, str]:
    try:
        image = Image.open(image_path).convert('HSV')
        image_array = np.array(image)

        # Split the channels
        hue, saturation, value = image_array[:, :, 0], image_array[:, :, 1], image_array[:, :, 2]

        # Define thresholds for happy colors
        happy_hue_range = ((20, 50), (330, 360))  # Approximate hue ranges for yellow to red
        happy_saturation_threshold = 100  # Minimum saturation for vibrant colors
        happy_value_threshold = 150  # Minimum brightness for bright colors

        # Check if a significant portion of the image falls into the "happy" category
        happy_pixels = 0
        total_pixels = hue.size

        for h, s, v in zip(hue.flatten(), saturation.flatten(), value.flatten()):
            # Check if the hue is in the happy range
            is_happy_hue = False
            for start, end in happy_hue_range:
                if start <= h <= end:
                    is_happy_hue = True
                    break

            # Check if the saturation and brightness are above the thresholds
            is_happy_saturation = s >= happy_saturation_threshold
            is_happy_value = v >= happy_value_threshold
            
            # If all conditions are met, count the pixel as happy
            if is_happy_hue and is_happy_saturation and is_happy_value:
                happy_pixels += 1
        
        happy_percentage = happy_pixels / total_pixels * 100
        print(happy_percentage)
        if happy_percentage > happy_threshold:  
            return True, "The image gives a happy feeling.", 

        return False, "The image does not give a happy feeling."

    except Exception as e:
        print("An error occurred while checking color happiness :", e)
        return False, str(e)

def adjust_image_for_happiness(image_array: np.ndarray) -> np.ndarray:
    try:
        # Convert to HSV
        image_hsv = Image.fromarray(image_array, 'RGBA').convert('HSV')
        h, s, v = image_hsv.split()

        # Enhance hue by rotating it
        h_data = np.array(h, dtype=np.uint16)  # Use uint16 to prevent overflow
        h_data = (h_data + 15) % 256  # Rotate hue by 15 degrees
        h_data = h_data.astype(np.uint8)  # Convert back to uint8
        h = Image.fromarray(h_data, 'L')

        # Enhance saturation and brightness
        s_data = np.array(s, dtype=np.uint16)  # Use uint16 to prevent overflow
        s_data = np.clip(s_data * 1.5, 0, 255).astype(np.uint8)  # Enhance and clip values
        s = Image.fromarray(s_data, 'L')

        v_data = np.array(v, dtype=np.uint16)  # Use uint16 to prevent overflow
        v_data = np.clip(v_data * 1.2, 0, 255).astype(np.uint8)  # Enhance and clip values
        v = Image.fromarray(v_data, 'L')

        # Merge the channels back
        image_hsv = Image.merge('HSV', (h, s, v))

        # Convert back to RGBA
        image_rgba = image_hsv.convert('RGBA')
        adjusted_image_array = np.array(image_rgba)

        return adjusted_image_array

    except Exception as e:
        print(f"An error occurred while adjusting image happiness color : {e}")
        return image_array

def check_non_transparent_within_circle(image_array: np.array, fill=False) -> Tuple[bool, str, np.array]:
    try:
        height, width, _ = image_array.shape
        center_x, center_y = width // 2, height // 2
        radius = min(center_x, center_y)
        
        for y in range(height):
            for x in range(width):
                distance = np.sqrt((x - center_x) ** 2 + (y - center_y) ** 2)
                if distance <= radius:
                    if image_array[y, x][3] == 0:  # Transparent pixel inside the circle
                        if fill:
                            # Initialize sum and count for averaging
                            r_sum, g_sum, b_sum, count = 0, 0, 0, 0
                            
                            # Iterate over neighboring pixels (3x3 window)
                            for j in range(max(0, y-1), min(height, y+2)):
                                for i in range(max(0, x-1), min(width, x+2)):
                                    if image_array[j, i][3] != 0:  # Non-transparent pixel
                                        r_sum += image_array[j, i][0]
                                        g_sum += image_array[j, i][1]
                                        b_sum += image_array[j, i][2]
                                        count += 1
                            
                            # Calculate average color
                            if count > 0:
                                avg_color = (r_sum // count, g_sum // count, b_sum // count, 255)  # Ensure alpha is fully opaque
                                image_array[y, x] = avg_color  # Fill the transparent pixel with the average color                    
                        else:
                            return False, "Transparent pixels found inside the circle.", None
        
        return True, "All non-transparent pixels are within the circle.", image_array
    
    except Exception as e:
        print("An error occurred while verifing non-transparent pixels ", e)
        return False, str(e), None

def verify_badge(img_path: str, colorThreshold=100) -> Tuple[bool, str]:
    try:
        image = Image.open(img_path).convert('RGBA')

        # condition1: Check if the image is a square of (512, 512)
        if image.size != (512, 512):
            return False, "The image must be 512x512 pixels."
        
        # condition2: The only non transparent pixels are within a circle
        image_array = np.array(image)
        is_within_circle, msg, image_array = check_non_transparent_within_circle(image_array)
        if not is_within_circle:
            return False, msg
                
        # condition3: The colors in the badge give a "happy" feeling
        is_happy, msg = is_happy_image(img_path)
        if not is_happy:
            return False, msg
        
        return True, "Badge is verified."
                
    except Exception as e:
        print("An error occured while verifing the badge: ", e)
        return False, str(e)
    

# function that converts the given image (of any format) into the specified image badge.
def covert_image_to_badge(image_path: str, output_path: str, add_happy_color=True) -> Tuple[bool, str]:
    try:
        image = Image.open(image_path).convert('RGBA')

        # Resize the image to 512x512
        if image.size != (512, 512):
            image = image.resize((512, 512), Image.Resampling.LANCZOS)

        # Check and adjust the badge to ensure it contains happy colors
        image_array = np.array(image)
        is_happy, msg = is_happy_image(image_path)
        if not is_happy and add_happy_color:
            image_array = adjust_image_for_happiness(image_array)
            print("Happy color adjusted ..... ")

        # Remove transparent pixels inside the circular area
        _, _, image_array = check_non_transparent_within_circle(image_array, fill=True)
        print("transparent pixels inside the circular area has been adjusted.....")
        adjusted_image = Image.fromarray(image_array)
        adjusted_image.save(f"{output_path}{image_path}", 'PNG')
        return True, "Image converted to badge successfully."
    
    except Exception as e:
        print("An error occured while coverting image to badge : ", e)
        return False, str(e)
    
    
if __name__ == "__main__":
    img_path = "testImage2.png"
    output_path = "./output/"
    image = Image.open(img_path)

    if image.format != 'PNG':
        print("The image must be a PNG file.")
        exit(1)

    is_verified, msg = verify_badge(img_path)
    if not is_verified:
        print(msg)
        covert_image_to_badge(img_path, output_path)
    else:
        print(msg)