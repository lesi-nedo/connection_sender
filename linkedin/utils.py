import re
import datetime
import os

def extract_number_from_text(text: str, logger) -> int:
    try:
        # Match digits and commas inside parentheses
        match = re.search(r'\(([0-9,]+)\)', text)
        if match:
            # Remove commas and convert to int
            number = int(match.group(1).replace(',', ''))
            logger.info(f"Extracted number: {number}")
            return number
            
        logger.error(f"No number found in text: {text}")
        return 0
        
    except Exception as e:
        logger.error(f"Error extracting number: {e}")
        return 0

def get_week_number():
    return datetime.datetime.now().isocalendar()[1]


def create_file(file_path):
    try:
        with open(file_path, 'w') as f:
            f.write('')
    except Exception as e:
        print(f"Error creating file: {e}")
        return False
    return True

def remove_files_in_directory(directory):
    try:
        for file in os.listdir(directory):
            os.remove(os.path.join(directory, file))
    except Exception as e:
        print(f"Error removing files in directory: {e}")
        return False
    return True