import io
from PIL import Image
import pandas as pd
from datetime import datetime
import csv
import io

def validate_image(image_file, max_size_mb=5):
    try:
        # Check file size
        image_data = image_file.read()
        file_size_mb = len(image_data) / (1024 * 1024)
        if file_size_mb > max_size_mb:
            return None, f"Image size exceeds {max_size_mb}MB limit"
        
        # Reset file pointer
        image_file.seek(0)
        
        # Open and validate image
        image = Image.open(image_file)
        
        # Resize image to a reasonable size
        max_dimensions = (800, 800)
        image.thumbnail(max_dimensions, Image.LANCZOS)
        
        # Convert to RGB if necessary
        if image.mode != 'RGB':
            image = image.convert('RGB')
            
        # Save to bytes
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format='JPEG', quality=85)
        return img_byte_arr.getvalue(), None
    except Exception as e:
        return None, f"Invalid image format: {str(e)}"

def validate_deck_data(deck_data):
    current_year = datetime.now().year
    errors = []
    
    if deck_data['release_year'] > current_year:
        errors.append(f"Release year cannot be in the future (current year: {current_year})")
    
    if deck_data['purchase_price'] < 0:
        errors.append("Purchase price cannot be negative")
    
    return errors

def prepare_export_data(df):
    # Remove binary image data and system columns for export
    export_df = df.drop(columns=['image_data', 'id', 'created_at'])
    return export_df

def parse_bulk_import_data(file):
    try:
        content = file.read().decode('utf-8')
        csv_data = csv.DictReader(io.StringIO(content))
        decks = []
        errors = []
        
        for row_num, row in enumerate(csv_data, start=2):  # Start from 2 to account for header row
            try:
                deck = {
                    'deck_name': row['deck_name'].strip(),
                    'manufacturer': row['manufacturer'].strip(),
                    'release_year': int(row['release_year']),
                    'condition': row['condition'].strip(),
                    'purchase_date': datetime.strptime(row['purchase_date'], '%Y-%m-%d').date(),
                    'purchase_price': float(row['purchase_price']),
                    'notes': row.get('notes', '').strip()
                }
                
                # Validate the deck data
                validation_errors = validate_deck_data(deck)
                if validation_errors:
                    errors.append(f"Row {row_num}: {', '.join(validation_errors)}")
                else:
                    decks.append(deck)
                    
            except (ValueError, KeyError) as e:
                errors.append(f"Row {row_num}: Invalid data format - {str(e)}")
                
        return decks, errors
    except Exception as e:
        return [], [f"Failed to parse CSV file: {str(e)}"]
