from flask import Flask, render_template

app = Flask(__name__)

@app.route("/")
def index():
    pagetitle = "HomePage"
    return render_template("index.html",
                            mytitle=pagetitle,
                            mycontent="Hello World My Name is Akash")

if __name__ == '__main__':
    app.run()