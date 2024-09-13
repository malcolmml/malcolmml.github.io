from flask import Flask, request, jsonify, render_template
from PIL import Image
import pytesseract
import re
import os

app = Flask(__name__)

# Ensure Tesseract is properly installed and recognized
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'  # Adjust this for your environment

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    
    filename = file.filename
    filepath = os.path.join('uploads', filename)
    file.save(filepath)
    
    try:
        # Extract text from the image
        img = Image.open(filepath)
        text = pytesseract.image_to_string(img)
        
        # Parse the extracted text
        extracted_values = parse_extracted_text(text)
        
        # Remove the file after processing
        os.remove(filepath)
        
        return jsonify(extracted_values)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def parse_extracted_text(text):
    """Parse extracted text to find specific values using regex."""
    if text is None:
        return {
            "Ledger Balance": None,
            "Current Month Average Daily Balance": None,
            "Average Daily Balance Increase": None
        }
    
    # Extract Ledger Balance
    ledger_balance = re.search(r"Ledger Balance.*?SGD\s+([\d,]+\.\d+)", text, re.DOTALL)
    
    # Extract Current Month Average Daily Balance
    current_month_avg = re.search(r"SGD\s+([\d,]+\.\d+)\s*Salary credited", text, re.DOTALL)
    
    # Extract Average Daily Balance Increase
    avg_daily_increase = re.search(r"SGD\s+([\d,]+\.\d+)\s*‘Average Daily Balance\s*Increase", text, re.DOTALL)

    def parse_float(value):
        """Convert string to float, removing commas."""
        return float(value.replace(',', '')) if value else None

    extracted_values = {
        "Ledger Balance": parse_float(ledger_balance.group(1) if ledger_balance else None),
        "Current Month Average Daily Balance": parse_float(current_month_avg.group(1) if current_month_avg else None),
        "Average Daily Balance Increase": parse_float(avg_daily_increase.group(1) if avg_daily_increase else None)
    }

    return extracted_values

if __name__ == '__main__':
    if not os.path.exists('uploads'):
        os.makedirs('uploads')
    app.run(debug=True)
