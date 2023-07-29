from flask import Flask,request,render_template,jsonify,flash,Response

application=Flask(__name__)
app=application

@app.route('/')
def home_page():
    return render_template('base.html')


if __name__=="__main__":
    app.run(host='0.0.0.0',debug=True)