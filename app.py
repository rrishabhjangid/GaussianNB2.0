import os
from flask import Flask, request, render_template_string
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import GaussianNB
from sklearn.metrics import accuracy_score, confusion_matrix

app = Flask(__name__)

# --- Database Configuration ---
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'students.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)

# --- Database Model (Student Data) ---
class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.String(20), unique=True, nullable=False)
    sap_id = db.Column(db.String(20), unique=True, nullable=False)
    roll_no = db.Column(db.Integer)
    name = db.Column(db.String(100))
    gender = db.Column(db.String(10))  # "Male" or "Female"
    # These are example numeric features for the AI model to learn from
    attendance_pct = db.Column(db.Float) 
    test_score = db.Column(db.Float)
    # This is the target we want to predict
    result_status = db.Column(db.String(20)) # e.g., "Pass" or "Fail"

# --- HTML Template ---
HTML_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>Student Success Predictor (Gaussian NB)</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background:#f0f2f5; padding:40px; }
        .container { background:white; padding:30px; border-radius:12px; width:600px; margin:auto; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
        h2 { text-align:center; color: #333; }
        .form-group { margin-bottom: 15px; }
        label { display: block; margin-bottom: 5px; font-weight: bold; }
        input, button { width:100%; padding:12px; margin-top:5px; border-radius: 6px; border: 1px solid #ccc; box-sizing: border-box; }
        button { background-color: #007bff; color: white; border: none; cursor: pointer; font-size: 16px; }
        button:hover { background-color: #0056b3; }
        .result { margin-top:20px; background:#e7f3ff; padding:20px; border-radius: 8px; border-left: 5px solid #007bff; }
        .matrix { font-family: monospace; background: #fff; padding: 10px; display: block; margin-top: 10px; }
    </style>
</head>
<body>
<div class="container">
    <h2>Student Classifier (Database Driven)</h2>
    <p style="text-align:center; color:#666;">Upload CSV with: student_id, sap_id, roll_no, name, gender, attendance_pct, test_score, result_status</p>

    <form method="POST" action="/train" enctype="multipart/form-data">
        <div class="form-group">
            <label>Upload Student Dataset (CSV)</label>
            <input type="file" name="file" required>
        </div>
        <button type="submit">Sync to DB & Train AI</button>
    </form>

    {% if result %}
    <div class="result">
        <h3>Training Results</h3>
        <p><b>Records in Database:</b> {{result.count}}</p>
        <p><b>Training Accuracy:</b> {{result.train}}</p>
        <p><b>Testing Accuracy:</b> {{result.test}}</p>
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
    
    # 1. Load the uploaded CSV into Pandas
    df_upload = pd.read_csv(file)

    # 2. Save data to SQLite Database
    # Note: Using a try/except or checking for existing records is better for production
    for _, row in df_upload.iterrows():
        # Check if student already exists to avoid unique constraint errors
        exists = Student.query.filter_by(student_id=str(row['student_id'])).first()
        if not exists:
            student = Student(
                student_id=str(row['student_id']),
                sap_id=str(row['sap_id']),
                roll_no=int(row['roll_no']),
                name=row['name'],
                gender=row['gender'],
                attendance_pct=float(row['attendance_pct']),
                test_score=float(row['test_score']),
                result_status=row['result_status']
            )
            db.session.add(student)
    db.session.commit()

    # 3. Fetch ALL data from DB to train the model
    all_students = Student.query.all()
    if not all_students:
        return "No data found in database."

    # Prepare data for Machine Learning
    # Convert categorical 'gender' to numeric (Male=1, Female=0)
    data_list = []
    for s in all_students:
        data_list.append({
            'gender_val': 1 if s.gender.lower() == 'male' else 0,
            'attendance': s.attendance_pct,
            'test': s.test_score,
            'target': s.result_status
        })
    
    df = pd.DataFrame(data_list)

    # 4. Train Gaussian Naive Bayes
    X = df[['gender_val', 'attendance', 'test']]
    y = df['target']

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    model = GaussianNB()
    model.fit(X_train, y_train)

    # 5. Evaluate
    train_acc = round(accuracy_score(y_train, model.predict(X_train)) * 100, 2)
    test_preds = model.predict(X_test)
    test_acc = round(accuracy_score(y_test, test_preds) * 100, 2)
    cm = confusion_matrix(y_test, test_preds).tolist()

    return render_template_string(
        HTML_PAGE,
        result={
            "count": len(all_students),
            "train": f"{train_acc}%", 
            "test": f"{test_acc}%", 
            "cm": cm
        }
    )

if __name__ == "__main__":
    app.run(debug=True)
