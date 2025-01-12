import os
import cv2
import pytesseract
from pytesseract import Output
import re
import csv

# Set the directory containing the images
image_folder = ''  # Change to your folder path
output_csv_file = ''  # Change to your output CSV file path

# Initialize a list to hold the extracted data
extracted_data = []

# Function to extract details from a single image
def extract_details(image_path):
    img = cv2.imread(image_path)

    # Check if the image is loaded correctly
    if img is None:
        print(f"Error: Could not load image {image_path}. Please check the file path.")
        return

    # Preprocess the image
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    contrast_img = cv2.convertScaleAbs(gray, alpha=1.5, beta=20)
    _, thresh = cv2.threshold(contrast_img, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
    dilated = cv2.dilate(thresh, kernel, iterations=1)

    # Perform OCR on the preprocessed image
    pytesseract.pytesseract.tesseract_cmd = '/usr/bin/tesseract'  # Adjust path if needed
    custom_config = r'--oem 3 --psm 6'
    data = pytesseract.image_to_data(dilated, config=custom_config, output_type=Output.DICT)

    # Extract the recognized text line by line
    text = ""
    for i, word in enumerate(data['text']):
        if int(data['conf'][i]) > 50:  # Filter by confidence level
            text += word + " "

    # Output text to see what was extracted
    print(f"Extracted Text from {image_path}: {text}")

    # Initialize variables for extracted details
    pan_number = ""
    name = ""
    fathers_name = ""

    # Define regex pattern for PAN number
    pan_pattern = r"[A-Z]{5}[0-9]{4}[A-Z]"  # PAN format

    # Find the PAN number using regex
    pan_match = re.search(pan_pattern, text)
    if pan_match:
        pan_number = pan_match.group(0)

    # Improved extraction logic based on the provided text
    words = text.split()

    # Logic to extract name
    try:
        # Identify the section where the name is likely to appear
        card_index = words.index("Card") + 1  # Get the index after 'Card'

        # Join until we reach 'Father's Name'
        name_parts = []
        for word in words[card_index:]:
            if word.startswith("Father's"):  # Stop before 'Father's Name'
                break
            # Clean up unwanted characters (e.g., symbols or digits)
            cleaned_word = re.sub(r'[^A-Za-z\s]', '', word)
            if cleaned_word:  # Only add non-empty strings
                name_parts.append(cleaned_word.strip())

        # Remove any leading/trailing unwanted characters from name parts
        name = " ".join(name_parts).strip()  # Join parts to form the name

        # Extract Father's Name
        fathers_name_index = words.index("Father's") + 2  # Get the index after 'Father's Name'
        fathers_name_parts = []
        for word in words[fathers_name_index:]:
            if word.startswith("of"):  # Stop if we reach 'of Birth'
                break
            # Clean up unwanted characters
            cleaned_word = re.sub(r'[^A-Za-z\s]', '', word)
            if cleaned_word:  # Only add non-empty strings
                fathers_name_parts.append(cleaned_word.strip())

        fathers_name = " ".join(fathers_name_parts).strip()  # Join parts to form the father's name

        # Clean up name by removing extraneous characters
        name = re.sub(r'\s+', ' ', name).strip()  # Remove extra spaces
        name = re.sub(r'^(IHAPD\s)?', '', name)  # Remove unwanted starting characters if present

    except ValueError:
        print("Could not find the specified keywords in the text.")

    # Append the extracted details to the list
    extracted_data.append({
        "Image File": os.path.basename(image_path),
        "Name": name,
        "Father's Name": fathers_name,
        "PAN Number": pan_number
    })


# Function to get user input and validate with extracted data
def user_input_validation():
    # Get user input for PAN number, Name, and Father's Name
    user_pan = input("Enter your PAN number: ").strip().upper()
    user_name = input("Enter your Name: ").strip().title()
    user_fathers_name = input("Enter your Father's Name: ").strip().title()

    # Check if the details match any record in the extracted data
    for record in extracted_data:
        if (record["PAN Number"] == user_pan and
            record["Name"].lower() == user_name.lower() and
            record["Father's Name"].lower() == user_fathers_name.lower()):
            print(f"Verification successful for PAN: {user_pan}")
            return True

    print(f"Fraud detected or details do not match for PAN: {user_pan}")
    return False


# Loop through all images in the specified folder
for filename in os.listdir(image_folder):
    if filename.endswith(('.png', '.jpg', '.jpeg')):  # Add other formats as needed
        image_path = os.path.join(image_folder, filename)
        extract_details(image_path)

# Write the extracted data to a single CSV file
with open(output_csv_file, mode='w', newline='', encoding='utf-8') as csvfile:
    fieldnames = ["Image File", "Name", "Father's Name", "PAN Number"]
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

    # Write the header
    writer.writeheader()

    # Write the data
    for data in extracted_data:
        writer.writerow(data)

print(f"All extracted details saved to {output_csv_file}")

# Call the user validation function for fraud detection
user_input_validation()
