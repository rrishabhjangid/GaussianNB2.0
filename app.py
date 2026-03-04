from flask import Flask, request, render_template_string
import sqlite3

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


HTML_PAGE = """
<!DOCTYPE html>
<html>
<head>
<title>Student Database</title>
<style>
body{font-family:Arial;background:#f2f2f2;padding:40px;}
.container{background:white;padding:30px;border-radius:10px;width:500px;margin:auto;}
input,select,button{width:100%;padding:10px;margin-top:10px;}
.result{margin-top:20px;background:#eef;padding:15px;border-radius:5px;}
</style>
</head>
<body>

<div class="container">
<h2>Add Student</h2>

<form method="POST" action="/add">
<input type="text" name="name" placeholder="Student Name" required>
<input type="text" name="sap_id" placeholder="SAP ID" required>
<input type="text" name="roll_no" placeholder="Roll Number" required>
<input type="number" name="marks" placeholder="Marks" required>
<input type="text" name="gender" placeholder="Gender" required>
<button type="submit">Save Student</button>
</form>

<hr>

<h2>Search Student</h2>

<form method="POST" action="/search">
<select name="search_name" required>
<option value="">Select Student</option>
{% for name in names %}
<option value="{{name}}">{{name}}</option>
{% endfor %}
</select>

<button type="submit">Show Details</button>
</form>

{% if student %}
<div class="result">
<h3>Student Information</h3>
<p><b>Name:</b> {{student[0]}}</p>
<p><b>SAP ID:</b> {{student[1]}}</p>
<p><b>Roll Number:</b> {{student[2]}}</p>
<p><b>Marks:</b> {{student[3]}}</p>
<p><b>Gender:</b> {{student[4]}}</p>
</div>
{% endif %}

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
