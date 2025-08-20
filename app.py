import os
import re
import json
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import datetime

# DB imports (install with pip if needed)
import psycopg2
import psycopg2.extras
import mysql.connector

import pandas as pd
from werkzeug.utils import secure_filename


app = Flask(__name__, static_folder='public', static_url_path='')
CORS(app)

# --- Environment Variables ---
DATABASE_TYPE = os.getenv("DATABASE_TYPE", "postgresql")  # 'postgresql' or 'mysql'

# --- DB Connection ---
db_conn = None
db_cursor = None

def get_db():
    global db_conn, db_cursor
    if DATABASE_TYPE == "postgresql":
        if db_conn is None or db_conn.closed:
            db_conn = psycopg2.connect(
                user=os.getenv("DB_USER", "postgres"),
                password=os.getenv("DB_PASSWORD", "Jacobben@2448015"),
                host=os.getenv("DB_HOST", "localhost"),
                port=int(os.getenv("DB_PORT", 5432)),
                database=os.getenv("DB_NAME", "agmarknet_db"),
            )
        db_cursor = db_conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    else:  # mysql
        if db_conn is None or not db_conn.is_connected():
            db_conn = mysql.connector.connect(
                user=os.getenv("DB_USER", "your_username"),
                password=os.getenv("DB_PASSWORD", "your_password"),
                host=os.getenv("DB_HOST", "localhost"),
                port=int(os.getenv("DB_PORT", 3306)),
                database=os.getenv("DB_NAME", "csv_data"),
            )
        db_cursor = db_conn.cursor(dictionary=True)
    return db_conn, db_cursor

def sanitize_table_name(name):
    return re.sub(r"[^a-zA-Z0-9_]", "_", name).lower()

def sanitize_column_name(name):
    return re.sub(r"[^a-zA-Z0-9_]", "_", name).lower()

def get_sql_type(value, db_type):
    if isinstance(value, bool):
        return "BOOLEAN"
    if isinstance(value, (int, float)):
        return "NUMERIC" if db_type == "postgresql" else "DECIMAL(10,2)"
    if isinstance(value, str):
        try:
            # Check if date
            datetime.datetime.fromisoformat(value)
            return "TIMESTAMP" if db_type == "postgresql" else "DATETIME"
        except Exception:
            pass
        return "TEXT"
    return "TEXT"

def is_number_column(col_type):
    # Accepts SQL type as string, returns True if it's a numeric type
    col_type = col_type.lower()
    return any(
        t in col_type for t in ["int", "decimal", "numeric", "float", "double", "real"]
    )

# --- API Endpoints ---

@app.route('/api/save-data', methods=['POST'])
def save_data():
    db, cursor = get_db()
    data = request.json
    table_name = data.get("tableName")
    rows = data.get("data")
    if not table_name or not rows:
        return jsonify({"error": "Invalid data provided"}), 400
    sanitized_table = sanitize_table_name(table_name)
    df = pd.DataFrame(rows)
    headers = list(df.columns)
    sanitized_headers = [sanitize_column_name(h) for h in headers]

    # Build CREATE TABLE if not exists
    columns = []
    col_types = []
    pandas_to_sql = {
        'int64':   ("NUMERIC", "DECIMAL(10,2)"),
        'float64': ("NUMERIC", "DECIMAL(10,2)"),
        'bool':    ("BOOLEAN", "BOOLEAN"),
        'datetime64[ns]': ("TIMESTAMP", "DATETIME"),
        'object':  ("TEXT", "TEXT"),
        'string':  ("TEXT", "TEXT"),
    }
    for i, header in enumerate(sanitized_headers):
        orig_header = headers[i]
        dtype_str = str(df[orig_header].dtype) if orig_header in df.columns else 'object'
        sql_type = pandas_to_sql.get(dtype_str, ("TEXT", "TEXT"))
        dtype = sql_type[0] if DATABASE_TYPE == "postgresql" else sql_type[1]
        columns.append(f"{header} {dtype}")
        col_types.append(dtype)
    id_col = "SERIAL PRIMARY KEY" if DATABASE_TYPE == "postgresql" else "INT AUTO_INCREMENT PRIMARY KEY"
    # Add a unique constraint on all data columns
    unique_constraint = f", UNIQUE ({', '.join(sanitized_headers)})" if sanitized_headers else ""
    create_table_sql = f"CREATE TABLE IF NOT EXISTS {sanitized_table} (id {id_col}, {', '.join(columns)}{unique_constraint});"
    cursor.execute(create_table_sql)
    db.commit()

    # Build INSERT statement with duplicate prevention
    insert_cols = sanitized_headers
    placeholders = (
        ','.join(["%s"] * len(insert_cols)) if DATABASE_TYPE == "mysql"
        else ','.join([f"%s"] * len(insert_cols))
    )
    if DATABASE_TYPE == "postgresql":
        insert_sql = f"INSERT INTO {sanitized_table} ({', '.join(insert_cols)}) VALUES ({placeholders}) ON CONFLICT DO NOTHING"
    else:
        insert_sql = f"INSERT IGNORE INTO {sanitized_table} ({', '.join(insert_cols)}) VALUES ({placeholders})"
    inserted_count = 0
    for row in rows:
        values = []
        for i, h in enumerate(headers):
            val = row.get(h, None)
            # If column is numeric and value is empty string, set to None
            if is_number_column(col_types[i]) and (val == "" or val is None):
                values.append(None)
            else:
                values.append(val)
        cursor.execute(insert_sql, values)
        if cursor.rowcount > 0:
            inserted_count += 1
    db.commit()
    return jsonify({"message": "Data saved successfully (duplicates ignored)", "tableName": sanitized_table, "recordCount": inserted_count})

@app.route('/api/load-data', methods=['GET'])
def load_data():
    db, cursor = get_db()
    table_name = request.args.get("tableName")
    if not table_name:
        return jsonify({"error": "Table name is required"}), 400
    sanitized_table = sanitize_table_name(table_name)
    try:
        cursor.execute(f"SELECT * FROM {sanitized_table}")
        rows = cursor.fetchall()
        return jsonify({"message": "Data loaded successfully", "tableName": sanitized_table, "data": rows})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

import pandas as pd
from werkzeug.utils import secure_filename

ALLOWED_EXTENSIONS = {'xls', 'xlsx'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/api/upload-excel', methods=['POST'])
def upload_excel():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file type'}), 400

    filename = secure_filename(file.filename)
    ext = filename.rsplit('.', 1)[1].lower()
    try:
        if ext == "csv":
            df = pd.read_csv(file)
        elif ext == "xlsx":
            df = pd.read_excel(file, engine='openpyxl')
        elif ext == "xls":
            try:
                df = pd.read_excel(file, engine='xlrd')
            except Exception:
                file.seek(0)
                df = pd.read_csv(file)
        else:
            return jsonify({'error': 'Unsupported file extension'}), 400
        data = df.fillna('').to_dict(orient='records')
        headers = df.columns.tolist()
        return jsonify({'headers': headers, 'data': data, 'filename': filename})
    except Exception as e:
        return jsonify({'error': f'Failed to parse file: {str(e)}'}), 500

# --- Monthly Averages Endpoint ---
@app.route('/api/monthly-averages', methods=['GET'])
def monthly_averages():
    db, cursor = get_db()
    table_name = request.args.get("tableName")
    date_col = request.args.get("dateColumn")
    value_col = request.args.get("valueColumn")
    if not table_name or not date_col or not value_col:
        return jsonify({"error": "tableName, dateColumn, and valueColumn are required"}), 400
    sanitized_table = sanitize_table_name(table_name)
    sanitized_date_col = sanitize_column_name(date_col)
    sanitized_value_col = sanitize_column_name(value_col)
    try:
        if DATABASE_TYPE == "postgresql":
            sql = f"""
                SELECT DATE_TRUNC('month', {sanitized_date_col}) AS month, AVG({sanitized_value_col}) AS avg_value
                FROM {sanitized_table}
                WHERE {sanitized_value_col} IS NOT NULL AND {sanitized_date_col} IS NOT NULL
                GROUP BY month
                ORDER BY month
            """
        else:
            sql = f"""
                SELECT DATE_FORMAT({sanitized_date_col}, '%Y-%m-01') AS month, AVG({sanitized_value_col}) AS avg_value
                FROM {sanitized_table}
                WHERE {sanitized_value_col} IS NOT NULL AND {sanitized_date_col} IS NOT NULL
                GROUP BY month
                ORDER BY month
            """
        cursor.execute(sql)
        rows = cursor.fetchall()
        return jsonify({"message": "Monthly averages loaded successfully", "tableName": sanitized_table, "data": rows})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@app.route('/api/list-tables', methods=['GET'])
def list_tables():
    db, cursor = get_db()
    if DATABASE_TYPE == "postgresql":
        cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' AND table_type = 'BASE TABLE' ORDER BY table_name;")
        tables = [row['table_name'] for row in cursor.fetchall()]
    else:
        cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = DATABASE() ORDER BY table_name;")
        tables = [row['table_name'] for row in cursor.fetchall()]
    return jsonify({"message": "Tables listed successfully", "tables": tables})

@app.route('/api/delete-table', methods=['DELETE'])
def delete_table():
    db, cursor = get_db()
    table_name = request.json.get("tableName")
    if not table_name:
        return jsonify({"error": "Table name is required"}), 400
    sanitized_table = sanitize_table_name(table_name)
    cursor.execute(f"DROP TABLE IF EXISTS {sanitized_table}")
    db.commit()
    return jsonify({"message": "Table deleted successfully", "tableName": sanitized_table})

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({
        "status": "OK",
        "database": DATABASE_TYPE,
        "timestamp": datetime.datetime.utcnow().isoformat()
    })

# --- Serve Static HTML/JS ---

@app.route('/')
def root():
    return send_from_directory('public', 'index.html')

@app.route('/<path:path>')
def static_proxy(path):
    return send_from_directory('public', path)

if __name__ == '__main__':
    app.run(port=int(os.getenv("PORT", 3000)), debug=True)
