from flask import Flask, request, render_template_string
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import GaussianNB
from sklearn.metrics import accuracy_score, confusion_matrix

app = Flask(__name__)

HTML_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>Gaussian Naive Bayes Classifier</title>
    <style>
        body { font-family: Arial; background:#f4f6f8; padding:40px; }
        .container { background:white; padding:30px; border-radius:8px; width:500px; margin:auto; }
        h2 { text-align:center; }
        input, button { width:100%; padding:10px; margin-top:10px; }
        .result { margin-top:20px; background:#eef; padding:15px; }
    </style>
</head>
<body>
<div class="container">
<h2>Gaussian Naive Bayes Classifier</h2>

<form method="POST" action="/train" enctype="multipart/form-data">
<label>Upload CSV Dataset</label>
<input type="file" name="file" required>

<label>Target Column Name</label>
<input type="text" name="target" placeholder="Example: species" required>

<button type="submit">Train Model</button>
</form>

{% if result %}
<div class="result">
<h3>Results</h3>
<p><b>Training Accuracy:</b> {{result.train}}</p>
<p><b>Testing Accuracy:</b> {{result.test}}</p>
<p><b>Confusion Matrix:</b> {{result.cm}}</p>
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
    target = request.form["target"]

    df = pd.read_csv(file)

    X = df.drop(columns=[target])
    y = df[target]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    model = GaussianNB()
    model.fit(X_train, y_train)

    train_preds = model.predict(X_train)
    test_preds = model.predict(X_test)

    train_acc = round(accuracy_score(y_train, train_preds) * 100, 2)
    test_acc = round(accuracy_score(y_test, test_preds) * 100, 2)

    cm = confusion_matrix(y_test, test_preds).tolist()

    return render_template_string(
        HTML_PAGE,
        result={"train": f"{train_acc}%", "test": f"{test_acc}%", "cm": cm}
    )

if __name__ == "__main__":
    app.run(debug=True)