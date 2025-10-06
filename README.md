# US Healthcare Data Mapping Generator

An AI-powered web application for mapping and transforming US healthcare data from various sources (Cigna, Facets, etc.) to standardized output layouts using Databricks LLM models.

## Features

- 🏥 **Healthcare Data Standardization**: Map data to standard US healthcare formats (Member, Service Provider, Bill Custom Detail)
- 🤖 **AI-Powered Mapping**: Uses Databricks Claude Sonnet 4 and Meta Llama 3.3 70B models
- 📄 **Data Dictionary Support**: Upload CSV or PDF data dictionaries
- 🗂️ **Table-Based Mapping**: Specify source table names for intelligent mapping
- 🎯 **Real-time Preview**: Preview output layouts before mapping
- 💾 **Export Results**: Download generated mapping as JSON

## Setup Instructions

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Databricks Credentials

1. Copy the configuration template:
   ```bash
   copy config_template.py config.py
   ```

2. Get your Databricks token:
   - Go to your Databricks workspace
   - Click on your user profile (top right)
   - Go to User Settings
   - Go to Access Tokens tab
   - Generate new token
   - Copy the token

3. Edit `config.py` and replace `YOUR_DATABRICKS_TOKEN_HERE` with your actual token.

### 3. Run the Application

```bash
python app.py
```

The application will be available at: `http://localhost:5000`

## Usage Guide

### 1. Select Target Output Layout
Choose from three standardized healthcare data layouts:
- **Member**: Patient/member demographic and insurance data
- **Service Provider**: Healthcare provider information
- **Bill Custom Detail**: Billing and financial data

### 2. Upload Data Dictionary
Upload a CSV or PDF file containing:
- Table schemas
- Field definitions
- Data types
- Business rules

### 3. Specify Source Tables
Enter the names of source data tables (comma-separated) that should be mapped. Examples:
- `member_demographics, claims_detail, provider_network`
- `cigna_member_table, facets_claims, provider_master`

### 4. Select AI Model
- **Claude Sonnet 4** (Recommended): Best for complex healthcare transformations
- **Meta Llama 3.3 70B**: Alternative high-performance model

### 5. Generate Mapping
The AI will analyze your inputs and generate:
- Field-by-field mapping tables
- SQL transformation queries
- Data quality checks
- Implementation notes

## Output Layouts

### Member Layout (455 fields)
- Member identification and demographics
- Insurance coverage details
- Plan and product information
- Subscriber relationships

### Service Provider Layout (430 fields)
- Provider identification
- Professional credentials
- Network participation
- Contact information

### Bill Custom Detail Layout (124 fields)
- Billing entity information
- Invoice and payment details
- Plan and product associations
- Component-level billing data

## Data Sources Supported

The system is designed to work with common US healthcare data sources:
- **Cigna**: Insurance and claims data
- **Facets**: Core administration platform
- **NASCO**: Claims processing system
- **Custom healthcare databases**

## Transformation Capabilities

The AI generates mapping logic with:
- **Data Type Conversion**: CAST() operations
- **Data Cleaning**: TRIM(), string functions
- **Conditional Logic**: CASE/WHEN statements
- **Null Handling**: COALESCE() functions
- **Table Joins**: Multi-table relationship mapping
- **Date Formatting**: Healthcare date standards
- **String Concatenation**: Composite field creation

## API Endpoints

- `GET /`: Main application interface
- `POST /api/generate_mapping`: Generate data mapping
- `GET /api/layouts/{layout_name}`: Preview output layouts

## File Structure

```
Mapping_Automation_Without_RAG/
├── app.py                  # Main Flask application
├── templates/
│   └── index.html         # Web interface
├── output_layouts/        # Standard healthcare layouts
│   ├── member.csv
│   ├── service_provider.csv
│   └── bill_custom_detail.csv
├── uploads/               # Temporary file storage
├── requirements.txt       # Python dependencies
├── config_template.py     # Configuration template
└── README.md             # This file
```

## Security Notes

- Data dictionaries are temporarily stored and deleted after processing
- No actual healthcare data is stored permanently
- Databricks tokens should be kept secure
- Use HTTPS in production environments

## Troubleshooting

### Common Issues

1. **Import Error for config.py**
   - Ensure you've copied `config_template.py` to `config.py`
   - Update the Databricks token in `config.py`

2. **API Authentication Errors**
   - Verify your Databricks token is correct and active
   - Check endpoint URLs are accessible

3. **File Upload Issues**
   - Ensure files are under 16MB
   - Support formats: CSV, PDF
   - Check file permissions

### Support

For healthcare data mapping questions or technical issues, please review the generated mapping outputs and adjust your data dictionary specifications as needed.

## License

This project is designed for healthcare data standardization and should comply with HIPAA and other healthcare data regulations in your environment.
