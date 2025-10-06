from flask import Flask, request, jsonify, render_template, send_from_directory
import os
import pandas as pd
import PyPDF2
import requests
import json
from werkzeug.utils import secure_filename
import tempfile
import csv
from io import StringIO

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Create uploads directory if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Load configuration
try:
    from config import DATABRICKS_CONFIG
    DATABRICKS_TOKEN = DATABRICKS_CONFIG['token']
    DATABRICKS_ENDPOINTS = DATABRICKS_CONFIG['endpoints']
except ImportError:
    print("Warning: config.py not found. Please copy config_template.py to config.py and update with your credentials.")
    DATABRICKS_TOKEN = 'YOUR_DATABRICKS_TOKEN_HERE'
    DATABRICKS_ENDPOINTS = {
        'claude-sonnet-4': 'https://dbc-3735add4-1cb6.cloud.databricks.com/serving-endpoints/databricks-claude-sonnet-4/invocations',
        'llama-3-70b': 'https://dbc-3735add4-1cb6.cloud.databricks.com/serving-endpoints/databricks-meta-llama-3-3-70b-instruct/invocations'
    }

# Output layouts available
OUTPUT_LAYOUTS = ['member', 'service_provider', 'bill_custom_detail']

def allowed_file(filename, allowed_extensions):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

def parse_csv_data_dictionary(file_path):
    """Parse CSV data dictionary and extract table information"""
    try:
        df = pd.read_csv(file_path)
        return df.to_dict('records')
    except Exception as e:
        return {"error": f"Error parsing CSV: {str(e)}"}

def parse_pdf_data_dictionary(file_path):
    """Parse PDF data dictionary and extract text content"""
    try:
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
        return {"pdf_content": text}
    except Exception as e:
        return {"error": f"Error parsing PDF: {str(e)}"}

def load_output_layout(layout_name):
    """Load the specified output layout CSV file"""
    try:
        layout_path = f"output_layouts/{layout_name}.csv"
        df = pd.read_csv(layout_path)
        # Handle NaN values by replacing them with empty strings
        df = df.fillna('')
        return df.to_dict('records')
    except Exception as e:
        return {"error": f"Error loading output layout: {str(e)}"}

def filter_data_dictionary_by_tables(data_dict, table_names):
    """Filter data dictionary to include only specified table names"""
    if isinstance(data_dict, list):
        # For CSV data dictionary
        filtered_data = []
        for entry in data_dict:
            # Check if any column contains table name information
            for key, value in entry.items():
                if isinstance(value, str) and any(table_name.lower() in value.lower() for table_name in table_names):
                    filtered_data.append(entry)
                    break
        return filtered_data
    elif isinstance(data_dict, dict) and 'pdf_content' in data_dict:
        # For PDF data dictionary - extract relevant sections
        content = data_dict['pdf_content']
        relevant_sections = []
        lines = content.split('\n')
        for line in lines:
            if any(table_name.lower() in line.lower() for table_name in table_names):
                relevant_sections.append(line)
        return {"filtered_pdf_content": '\n'.join(relevant_sections)}
    return data_dict

def call_databricks_llm(endpoint_key, prompt, max_tokens=4000):
    """Call Databricks LLM endpoint"""
    try:
        url = DATABRICKS_ENDPOINTS[endpoint_key]
        
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {DATABRICKS_TOKEN}'
        }
        
        payload = {
            "inputs": prompt,
            "parameters": {
                "max_tokens": max_tokens,
                "temperature": 0.1
            }
        }
        
        response = requests.post(url, headers=headers, json=payload)
        
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"API call failed with status {response.status_code}: {response.text}"}
            
    except Exception as e:
        return {"error": f"Error calling LLM: {str(e)}"}

def create_mapping_prompt(output_layout, data_dictionary, table_names):
    """Create a comprehensive prompt for the LLM to generate data mapping"""
    
    prompt = f"""
You are a US Healthcare Data Modeler and Data Analyst expert. Your task is to create a comprehensive data mapping and transformation plan.

**TASK**: Generate SQL-like transformation logic to map source healthcare data tables to the target output layout.

**TARGET OUTPUT LAYOUT**:
{json.dumps(output_layout, indent=2)}

**SOURCE DATA TABLES TO USE**:
{', '.join(table_names)}

**DATA DICTIONARY (Source Table Details)**:
{json.dumps(data_dictionary, indent=2)}

**REQUIREMENTS**:
1. Create mapping logic for each field in the target output layout
2. Use appropriate transformations like:
   - CAST() for data type conversions
   - JOIN operations between source tables
   - TRIM() for cleaning string data
   - CASE/WHEN for conditional logic
   - COALESCE() for handling nulls
   - String concatenation where needed
   - Date formatting functions

3. Consider US Healthcare data standards (FHIR, HL7, etc.)
4. Handle common healthcare data sources like Cigna, Facets, etc.
5. Ensure data quality and validation

**OUTPUT FORMAT**:
Provide a detailed mapping document with:
1. Field-by-field mapping table
2. SQL transformation queries
3. Data quality checks
4. Notes on assumptions made

Generate comprehensive transformation logic that can be used to map the source tables to the target output layout.
"""
    
    return prompt

@app.route('/')
def index():
    return render_template('index.html', layouts=OUTPUT_LAYOUTS)

@app.route('/api/generate_mapping', methods=['POST'])
def generate_mapping():
    try:
        # Get form data
        selected_layout = request.form.get('layout')
        table_names = request.form.get('table_names', '').split(',')
        table_names = [name.strip() for name in table_names if name.strip()]
        llm_model = request.form.get('llm_model', 'claude-sonnet-4')
        
        # Validate inputs
        if not selected_layout or selected_layout not in OUTPUT_LAYOUTS:
            return jsonify({'error': 'Invalid or missing layout selection'}), 400
        
        if not table_names:
            return jsonify({'error': 'Please specify at least one source table name'}), 400
        
        # Handle data dictionary file upload
        data_dict_file = request.files.get('data_dictionary')
        if not data_dict_file or data_dict_file.filename == '':
            return jsonify({'error': 'Please upload a data dictionary file'}), 400
        
        # Save uploaded file
        filename = secure_filename(data_dict_file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        data_dict_file.save(file_path)
        
        # Parse data dictionary based on file type
        file_extension = filename.rsplit('.', 1)[1].lower()
        if file_extension == 'csv':
            data_dictionary = parse_csv_data_dictionary(file_path)
        elif file_extension == 'pdf':
            data_dictionary = parse_pdf_data_dictionary(file_path)
        else:
            return jsonify({'error': 'Unsupported file format. Please upload CSV or PDF.'}), 400
        
        # Check for parsing errors
        if isinstance(data_dictionary, dict) and 'error' in data_dictionary:
            return jsonify(data_dictionary), 400
        
        # Filter data dictionary by specified table names
        filtered_data_dict = filter_data_dictionary_by_tables(data_dictionary, table_names)
        
        # Load target output layout
        output_layout = load_output_layout(selected_layout)
        if isinstance(output_layout, dict) and 'error' in output_layout:
            return jsonify(output_layout), 400
        
        # Create prompt for LLM
        prompt = create_mapping_prompt(output_layout, filtered_data_dict, table_names)
        
        # Call Databricks LLM
        llm_response = call_databricks_llm(llm_model, prompt)
        
        # Clean up uploaded file
        os.remove(file_path)
        
        # Prepare response
        response_data = {
            'layout': selected_layout,
            'table_names': table_names,
            'llm_model': llm_model,
            'mapping_result': llm_response,
            'output_layout_fields': len(output_layout),
            'data_dict_entries': len(filtered_data_dict) if isinstance(filtered_data_dict, list) else 1
        }
        
        return jsonify(response_data)
        
    except Exception as e:
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500

@app.route('/api/layouts/<layout_name>')
def get_layout_preview(layout_name):
    """Get a preview of the selected output layout"""
    if layout_name not in OUTPUT_LAYOUTS:
        return jsonify({'error': 'Invalid layout name'}), 400
    
    layout_data = load_output_layout(layout_name)
    if isinstance(layout_data, dict) and 'error' in layout_data:
        return jsonify(layout_data), 400
    
    # Return first 10 fields for preview
    preview_data = layout_data[:10] if len(layout_data) > 10 else layout_data
    
    return jsonify({
        'layout_name': layout_name,
        'total_fields': len(layout_data),
        'preview': preview_data
    })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
