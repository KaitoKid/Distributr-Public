from flask import Flask, render_template, request, flash
from rq import Queue
from worker import conn
from helper import gsheetParser as g
import sys
import os

# Tell RQ what Redis connection to use
q = Queue(connection=conn)  # no args implies the default queue

app = Flask(__name__)
app.secret_key = os.getenv('SECRETKEY')


@app.route('/')
def loadMain():
    return render_template('index.html')


@app.route('/formSubmit', methods=['POST'])
def formSubmit():
    print(request.form, file=sys.stdout)
    if (request.form['eventCode'].upper() != os.getenv('EVENTCODE')):
        flash('Error: Your event code was not valid. Please try again.')
        return render_template('index.html')
    else:
        job = q.enqueue(
            g.addUser, request.form['contactName'], request.form['contactEmail'])
        return render_template('thanks.html')


if __name__ == "__main__":
    app.run(host='0.0.0.0')
