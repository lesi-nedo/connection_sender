import re
import datetime
import os
import socket
import requests
from typing import List
from time import sleep

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


def check_internet_connection(logger, retries: int = 3, timeout: int = 5) -> bool:
    """
    Check internet connectivity by testing connection to reliable hosts
    """
    hosts: List[str] = [
        "linkedin.com",
        "google.com", 
        "1.1.1.1"  # Cloudflare DNS
    ]
    
    for attempt in range(retries):
        for host in hosts:
            try:
                # Try socket connection first (faster)
                socket.create_connection((host, 80), timeout=timeout)
                logger.info(f"Internet connection verified via {host}")
                return True
            except OSError:
                try:
                    # Fallback to HTTP request
                    requests.get(f"http://{host}", timeout=timeout)
                    logger.info(f"Internet connection verified via HTTP to {host}")
                    return True
                except requests.RequestException:
                    continue
        
        if attempt < retries - 1:
            logger.warning(f"Connection attempt {attempt + 1} failed, retrying...")
            sleep(2)
    
    logger.error("No internet connection available")
    return False