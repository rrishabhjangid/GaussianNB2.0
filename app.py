from flask import Flask, request, render_template_string
import sqlite3
import os

app = Flask(__name__)

# Create database table
def init_db():
    conn = sqlite3.connect("students.db")
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS students(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        sap_id TEXT,
        roll_no TEXT,
        marks INTEGER,
        gender TEXT
    )
    """)
    conn.commit()
    conn.close()

init_db()

# --- Updated Frontend Design ---
HTML_PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Student Portal | Dashboard</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&display=swap" rel="stylesheet">
    <style>
        :root {
            --primary: #4f46e5;
            --primary-hover: #4338ca;
            --bg: #f8fafc;
            --card-bg: #ffffff;
            --text-main: #1e293b;
            --text-muted: #64748b;
            --border: #e2e8f0;
        }

        body { 
            font-family: 'Inter', sans-serif; 
            background: var(--bg); 
            color: var(--text-main);
            margin: 0;
            padding: 40px 20px;
        }

        .dashboard {
            max-width: 800px;
            margin: auto;
        }

        header {
            text-align: center;
            margin-bottom: 40px;
        }

        header h1 { margin: 0; color: var(--primary); font-weight: 600; }
        header p { color: var(--text-muted); margin-top: 5px; }

        .grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
        }

        .card {
            background: var(--card-bg);
            padding: 25px;
            border-radius: 12px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
            border: 1px solid var(--border);
        }

        .card h2 { 
            margin-top: 0; 
            font-size: 1.25rem; 
            border-bottom: 2px solid var(--bg);
            padding-bottom: 10px;
            margin-bottom: 20px;
        }

        .form-group { margin-bottom: 15px; }
        label { display: block; font-size: 0.85rem; font-weight: 600; margin-bottom: 5px; color: var(--text-muted); }

        input, select {
            width: 100%;
            padding: 10px;
            border: 1px solid var(--border);
            border-radius: 6px;
            font-size: 0.95rem;
            box-sizing: border-box;
            transition: border-color 0.2s;
        }

        input:focus, select:focus {
            outline: none;
            border-color: var(--primary);
            ring: 2px solid var(--primary);
        }

        button {
            width: 100%;
            padding: 12px;
            background: var(--primary);
            color: white;
            border: none;
            border-radius: 6px;
            font-weight: 600;
            cursor: pointer;
            transition: background 0.2s;
            margin-top: 10px;
        }

        button:hover { background: var(--primary-hover); }

        .result-card {
            grid-column: span 2;
            background: #eff6ff;
            border: 1px solid #bfdbfe;
        }

        .info-row {
            display: flex;
            justify-content: space-between;
            padding: 10px 0;
            border-bottom: 1px solid #dbeafe;
        }

        .info-row:last-child { border-bottom: none; }
        .info-label { font-weight: 600; color: #1e40af; }
        
        @media (max-width: 600px) {
            .grid { grid-template-columns: 1fr; }
            .result-card { grid-column: span 1; }
        }
    </style>
</head>
<body>

<div class="dashboard">
    <header>
        <h1>Student Records Portal</h1>
        <p>Manage and retrieve student information securely</p>
    </header>

    <div class="grid">
        <div class="card">
            <h2>Add New Student</h2>
            <form method="POST" action="/add">
                <div class="form-group">
                    <label>Full Name</label>
                    <input type="text" name="name" placeholder="John Doe" required>
                </div>
                <div class="form-group">
                    <label>SAP ID</label>
                    <input type="text" name="sap_id" placeholder="500012345" required>
                </div>
                <div class="form-group">
                    <label>Roll Number</label>
                    <input type="text" name="roll_no" placeholder="R214220" required>
                </div>
                <div class="form-group">
                    <label>Total Marks</label>
                    <input type="number" name="marks" placeholder="0-100" required>
                </div>
                <div class="form-group">
                    <label>Gender</label>
                    <select name="gender" required>
                        <option value="Male">Male</option>
                        <option value="Female">Female</option>
                        <option value="Other">Other</option>
                    </select>
                </div>
                <button type="submit">Register Student</button>
            </form>
        </div>

        <div class="card">
            <h2>Quick Search</h2>
            <form method="POST" action="/search">
                <div class="form-group">
                    <label>Select Student Name</label>
                    <select name="search_name" required>
                        <option value="">-- Choose from Database --</option>
                        {% for name in names %}
                        <option value="{{name}}">{{name}}</option>
                        {% endfor %}
                    </select>
                </div>
                <button type="submit" style="background: #334155;">View Details</button>
            </form>

            {% if student %}
            <div style="margin-top: 30px; text-align: center; color: var(--text-muted); font-size: 0.9rem;">
                Search results displayed below ↓
            </div>
            {% endif %}
        </div>

        {% if student %}
        <div class="card result-card">
            <h2 style="color: #1e40af; border-bottom-color: #dbeafe;">Student Profile: {{student[0]}}</h2>
            <div class="info-row">
                <span class="info-label">SAP ID</span>
                <span>{{student[1]}}</span>
            </div>
            <div class="info-row">
                <span class="info-label">Roll Number</span>
                <span>{{student[2]}}</span>
            </div>
            <div class="info-row">
                <span class="info-label">Academic Marks</span>
                <span>{{student[3]}} / 100</span>
            </div>
            <div class="info-row">
                <span class="info-label">Gender</span>
                <span>{{student[4]}}</span>
            </div>
        </div>
        {% endif %}
    </div>
</div>

</body>
</html>
"""

def get_names():
    conn = sqlite3.connect("students.db")
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM students")
    data = cursor.fetchall()
    conn.close()
    return [x[0] for x in data]

@app.route("/")
def home():
    names = get_names()
    return render_template_string(HTML_PAGE, names=names)

@app.route("/add", methods=["POST"])
def add_student():
    name = request.form["name"]
    sap_id = request.form["sap_id"]
    roll_no = request.form["roll_no"]
    marks = request.form["marks"]
    gender = request.form["gender"]

    conn = sqlite3.connect("students.db")
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO students(name,sap_id,roll_no,marks,gender) VALUES (?,?,?,?,?)",
        (name, sap_id, roll_no, marks, gender)
    )
    conn.commit()
    conn.close()

    names = get_names()
    return render_template_string(HTML_PAGE, names=names)

@app.route("/search", methods=["POST"])
def search():
    name = request.form["search_name"]
    conn = sqlite3.connect("students.db")
    cursor = conn.cursor()
    cursor.execute(
        "SELECT name,sap_id,roll_no,marks,gender FROM students WHERE name=?",
        (name,)
    )
    student = cursor.fetchone()
    conn.close()
    names = get_names()
    return render_template_string(HTML_PAGE, student=student, names=names)

if __name__ == "__main__":
    app.run(debug=True)
    
