"""
Helper utility functions
"""

import os
import secrets
import hashlib
from datetime import datetime
from werkzeug.utils import secure_filename
from flask import current_app


def allowed_file(filename):
    """Check if file extension is allowed"""
    if '.' not in filename:
        return False
    
    ext = filename.rsplit('.', 1)[1].lower()
    return ext in current_app.config['ALLOWED_EXTENSIONS']


def save_uploaded_file(file, person_id):
    """
    Save uploaded file to disk
    Returns: (success, filename, filepath, error_message)
    """
    try:
        if not file or file.filename == '':
            return False, None, None, "No file selected"
        
        if not allowed_file(file.filename):
            return False, None, None, "File type not allowed"
        
        # Create person-specific directory
        upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], str(person_id))
        os.makedirs(upload_dir, exist_ok=True)
        
        # Generate unique filename
        original_filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        random_string = secrets.token_hex(4)
        filename = f"{timestamp}_{random_string}_{original_filename}"   
       

 # Save file
        filepath = os.path.join(upload_dir, filename)
        file.save(filepath)
        
        return True, filename, filepath, None
        
    except Exception as e:
        return False, None, None, str(e)


def get_file_icon(filename):
    """Get Font Awesome icon class based on file extension"""
    if '.' not in filename:
        return 'fa-file'
    
    ext = filename.rsplit('.', 1)[1].lower()
    
    icon_map = {
        'pdf': 'fa-file-pdf',
        'doc': 'fa-file-word',
        'docx': 'fa-file-word',
        'xls': 'fa-file-excel',
        'xlsx': 'fa-file-excel',
        'jpg': 'fa-file-image',
        'jpeg': 'fa-file-image',
        'png': 'fa-file-image',
        'gif': 'fa-file-image',
        'txt': 'fa-file-alt',
        'zip': 'fa-file-archive',
        'rar': 'fa-file-archive',
    }
    
    return icon_map.get(ext, 'fa-file')


def format_file_size(size_bytes):
    """Format file size in human-readable format"""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.2f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.2f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"


def generate_token(length=32):
    """Generate a secure random token"""
    return secrets.token_urlsafe(length)


def verify_token(token, stored_hash):
    """Verify a token against its hash"""
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    return token_hash == stored_hash


def get_file_extension(filename):
    """Get file extension from filename"""
    if '.' not in filename:
        return ''
    return filename.rsplit('.', 1)[1].lower()


def sanitize_filename(filename):
    """Sanitize filename for safe storage"""
    # Remove any path components
    filename = os.path.basename(filename)
    # Secure the filename
    filename = secure_filename(filename)
    return filename


def create_directory_if_not_exists(directory):
    """Create directory if it doesn't exist"""
    try:
        os.makedirs(directory, exist_ok=True)
        return True
    except Exception as e:
        print(f"Error creating directory {directory}: {e}")
        return False


def delete_file_safely(filepath):
    """Safely delete a file"""
    try:
        if os.path.exists(filepath):
            os.remove(filepath)
            return True
        return False
    except Exception as e:
        print(f"Error deleting file {filepath}: {e}")
        return False


def get_upload_path(person_id, filename):
    """Get the full upload path for a file"""
    upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], str(person_id))
    return os.path.join(upload_dir, filename)


def calculate_response_rate(total, responded):
    """Calculate response rate percentage"""
    if total == 0:
        return 0
    return round((responded / total) * 100, 1)


def format_phone_number(phone):
    """Format phone number for display"""
    # Remove all non-numeric characters
    digits = ''.join(filter(str.isdigit, phone))

 # Format as (XXX) XXX-XXXX for US numbers
    if len(digits) == 10:
        return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
    elif len(digits) == 11 and digits[0] == '1':
        return f"+1 ({digits[1:4]}) {digits[4:7]}-{digits[7:]}"
    else:
        return phone


def truncate_string(text, length=50, suffix='...'):
    """Truncate string to specified length"""
    if len(text) <= length:
        return text
    return text[:length].rsplit(' ', 1)[0] + suffix


def get_status_badge_class(status):
    """Get Bootstrap badge class for status"""
    status_map = {
        'pending': 'bg-warning',
        'confirmed': 'bg-success',
        'declined': 'bg-danger',
        'completed': 'bg-info',
        'cancelled': 'bg-secondary'
    }
    return status_map.get(status.lower(), 'bg-secondary')


def validate_email(email):
    """Basic email validation"""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def generate_export_filename(prefix, extension='csv'):
    """Generate filename for exports"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    return f"{prefix}_{timestamp}.{extension}"