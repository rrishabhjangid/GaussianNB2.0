import os
from flask import Flask, request, render_template_string
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import GaussianNB
from sklearn.metrics import accuracy_score, confusion_matrix

app = Flask(__name__)

# --- Render-Compatible Database Configuration ---
# Render provides DATABASE_URL for Postgres; otherwise, use local SQLite
database_url = os.environ.get('DATABASE_URL', 'sqlite:///students.db')
if database_url and database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)

# --- Student Model ---
class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.String(20), unique=True, nullable=False)
    sap_id = db.Column(db.String(20), unique=True, nullable=False)
    roll_no = db.Column(db.Integer)
    name = db.Column(db.String(100))
    gender = db.Column(db.String(10))
    attendance_pct = db.Column(db.Float) 
    test_score = db.Column(db.Float)
    result_status = db.Column(db.String(20)) 

# --- HTML Template with Dropdown ---
HTML_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>Student AI Classifier</title>
    <style>
        body { font-family: 'Segoe UI', sans-serif; background:#f4f7f6; padding:40px; }
        .container { background:white; padding:30px; border-radius:12px; width:600px; margin:auto; box-shadow: 0 4px 15px rgba(0,0,0,0.1); }
        h2 { text-align:center; color: #2c3e50; }
        .section { border-bottom: 1px solid #eee; padding-bottom: 20px; margin-bottom: 20px; }
        label { font-weight: bold; display: block; margin: 10px 0 5px; }
        select, input, button { width:100%; padding:12px; border-radius: 6px; border: 1px solid #ddd; box-sizing: border-box; }
        button { background: #27ae60; color: white; border: none; cursor: pointer; font-size: 16px; transition: 0.3s; }
        button:hover { background: #219150; }
        .result { background:#ebf5fb; padding:20px; border-radius: 8px; border-left: 5px solid #3498db; }
        .matrix { font-family: monospace; background: #fff; padding: 10px; display: block; border: 1px solid #ccc; }
    </style>
</head>
<body>
<div class="container">
    <h2>Student Data Classifier</h2>
    
    <div class="section">
        <form method="POST" action="/train" enctype="multipart/form-data">
            <label>1. Upload Dataset (CSV)</label>
            <input type="file" name="file" required>
            
            <label>2. Select Target Column (What to Predict?)</label>
            <select name="target">
                <option value="result_status">Result Status (Pass/Fail)</option>
                <option value="gender">Gender (Male/Female)</option>
            </select>
            
            <button type="submit" style="margin-top:20px;">Upload & Train Model</button>
        </form>
    </div>

    {% if result %}
    <div class="result">
        <h3>Model Insights</h3>
        <p><b>Total Samples:</b> {{result.count}}</p>
        <p><b>Target Selected:</b> {{result.target}}</p>
        <p><b>Test Accuracy:</b> {{result.test}}</p>
        <p><b>Confusion Matrix:</b></p>
        <span class="matrix">{{result.cm}}</span>
    </div>
    {% endif %}
</div>
</body>
</html>
"""

@app.route("/")
def home():
    return render_template_string(HTML_PAGE)

@app.route("/train", methods=["POST"])
def train():
    file = request.files["file"]
    target_choice = request.form["target"]
    
    # 1. Sync CSV to DB
    df_upload = pd.read_csv(file)
    for _, row in df_upload.iterrows():
        exists = Student.query.filter_by(student_id=str(row['student_id'])).first()
        if not exists:
            new_s = Student(
                student_id=str(row['student_id']),
                sap_id=str(row['sap_id']),
                roll_no=int(row['roll_no']),
                name=row['name'],
                gender=row['gender'],
                attendance_pct=float(row['attendance_pct']),
                test_score=float(row['test_score']),
                result_status=row['result_status']
            )
            db.session.add(new_s)
    db.session.commit()

    # 2. Fetch and Prepare Data
    all_data = Student.query.all()
    df = pd.DataFrame([{
        'gender': 1 if s.gender.lower() == 'male' else 0,
        'attendance': s.attendance_pct,
        'test': s.test_score,
        'result_status': 1 if s.result_status.lower() == 'pass' else 0
    } for s in all_data])

    # 3. Model Training based on Dropdown Choice
    if target_choice == 'result_status':
        X = df[['gender', 'attendance', 'test']]
        y = df['result_status']
    else:
        X = df[['attendance', 'test', 'result_status']]
        y = df['gender']

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    model = GaussianNB()
    model.fit(X_train, y_train)
    
    acc = round(accuracy_score(y_test, model.predict(X_test)) * 100, 2)
    cm = confusion_matrix(y_test, model.predict(X_test)).tolist()

    return render_template_string(
        HTML_PAGE,
        result={
            "count": len(all_data),
            "target": target_choice,
            "test": f"{acc}%",
            "cm": cm
        }
    )

if __name__ == "__main__":
    app.run(debug=True)
