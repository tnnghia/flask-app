from flask import Flask, render_template
app = Flask(__name__)

@app.route("/")
def home():
    return render_template("index.html", name="Sepkeo")

# Lưu ý: KHÔNG gọi app.run() khi deploy Render
# if __name__ == "__main__":
#     app.run(debug=True)
