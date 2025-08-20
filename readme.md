# Data Management Flask API

A robust Flask-based API for data management with support for Excel/CSV file uploads, database operations, and data analysis. The application provides a comprehensive solution for handling structured data with dual database support and automated data processing capabilities.

## 🚀 Features

- **Dual Database Support**: Works with both PostgreSQL and MySQL databases
- **File Upload Processing**: Upload and process Excel (.xlsx, .xls) and CSV files
- **Automatic Table Creation**: Dynamic table creation with proper data type mapping
- **Data Sanitization**: Automatic sanitization of table and column names
- **Duplicate Prevention**: Built-in duplicate detection with unique constraints
- **Monthly Aggregation**: Calculate monthly averages for time-series data
- **CORS Enabled**: Cross-Origin Resource Sharing support for web applications
- **Environment Configuration**: Flexible configuration through environment variables
- **Static File Serving**: Serve frontend files from the public directory

## 🛠️ Tech Stack

- **Backend**: Flask (Python)
- **Databases**: PostgreSQL / MySQL
- **Data Processing**: Pandas
- **File Handling**: openpyxl, xlrd
- **Database Drivers**: psycopg2-binary, mysql-connector-python

## 📋 Prerequisites

- Python 3.7+
- PostgreSQL or MySQL database
- pip (Python package manager)

## ⚡ Quick Start

### 1. Clone the Repository

```bash
git clone <your-repository-url>
cd <repository-name>
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Environment Setup

Create a `.env` file or set environment variables:

```bash
# Database Configuration
DATABASE_TYPE=postgresql  # or 'mysql'
DB_HOST=localhost
DB_PORT=5432              # 5432 for PostgreSQL, 3306 for MySQL
DB_USER=your_username
DB_PASSWORD=your_password
DB_NAME=your_database_name

# Application Configuration
PORT=3000
```

### 4. Database Setup

#### PostgreSQL
```sql
CREATE DATABASE agmarknet_db;
```

#### MySQL
```sql
CREATE DATABASE csv_data;
```

### 5. Run the Application

```bash
python app.py
```

The application will start on `http://localhost:3000`

## 📚 API Documentation

### Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health` | GET | Health check and database status |
| `/api/save-data` | POST | Save JSON data to database |
| `/api/load-data` | GET | Load data from a specific table |
| `/api/upload-excel` | POST | Upload and process Excel/CSV files |
| `/api/monthly-averages` | GET | Calculate monthly averages for data |
| `/api/list-tables` | GET | List all available database tables |
| `/api/delete-table` | DELETE | Delete a specific table |

### Example Usage

#### Upload Excel File
```bash
curl -X POST -F "file=@data.xlsx" http://localhost:3000/api/upload-excel
```

#### Save Data
```bash
curl -X POST -H "Content-Type: application/json" \
  -d '{"tableName": "sales_data", "data": [{"date": "2023-01-01", "amount": 100}]}' \
  http://localhost:3000/api/save-data
```

#### Load Data
```bash
curl "http://localhost:3000/api/load-data?tableName=sales_data"
```

#### Monthly Averages
```bash
curl "http://localhost:3000/api/monthly-averages?tableName=sales_data&dateColumn=date&valueColumn=amount"
```

## 🔧 Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_TYPE` | postgresql | Database type ('postgresql' or 'mysql') |
| `DB_HOST` | localhost | Database host |
| `DB_PORT` | 5432 | Database port |
| `DB_USER` | postgres | Database username |
| `DB_PASSWORD` | - | Database password |
| `DB_NAME` | agmarknet_db | Database name |
| `PORT` | 3000 | Application port |

### Supported File Formats

- **Excel**: .xlsx, .xls
- **CSV**: .csv (through pandas)

## 🏗️ Project Structure

```
├── app.py                 # Main application file
├── requirements.txt       # Python dependencies
├── public/               # Static files directory
│   └── index.html        # Frontend files
└── README.md            # This file
```

## 🔒 Security Features

- Input sanitization for table and column names
- SQL injection prevention through parameterized queries
- File type validation for uploads
- Environment variable configuration for sensitive data

## 🚦 Error Handling

The API includes comprehensive error handling for:
- Database connection issues
- Invalid file formats
- Missing required parameters
- SQL execution errors
- Data validation failures

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/new-feature`)
3. Commit your changes (`git commit -am 'Add new feature'`)
4. Push to the branch (`git push origin feature/new-feature`)
5. Create a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

If you encounter any issues or have questions:

1. Check the [Issues](../../issues) section
2. Create a new issue with detailed information
3. Include error logs and environment details

## 🔄 Changelog

### v1.0.0
- Initial release with basic CRUD operations
- Excel/CSV file upload support
- Dual database support (PostgreSQL/MySQL)
- Monthly aggregation functionality

---

**Note**: Remember to update your database credentials and remove any hardcoded passwords before deploying to production.