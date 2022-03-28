from flask import Flask, render_template, request, redirect
import pandas as pd
import json
import plotly
import plotly.express as px
from sqlalchemy import create_engine, insert
import pymysql 
import datetime
from operator import itemgetter

def formatRows(rows):
    for r, row in enumerate(rows):
        for c, col in enumerate(row):
            if c == 1:
                rows[r][c] = f"{col:.2f} Kg"
            if c == 2:
                rows[r][c] = f"{col:.2f} Kg"
            if c == 3:
                rows[r][c] = f"{col:.2f} %"
            if c == 4:
                rows[r][c] = f"{col:.2f} Kg"
            if c == 5:
                rows[r][c] = f"{col:.2f} Kg/m²"
    return rows

def getUsersAndWeightList():
    frameUsers = pd.read_sql("select * from Users", con=sqlEngine);
   
    users = list(frameUsers.User)
    heights = list(frameUsers.Height)
    
    rows = []

    for i, user in enumerate(users):
        frameWeights = pd.read_sql(f"select * from Weights where `User` = '{user}'", con=sqlEngine)

        orderDate = pd.read_sql(f"SELECT * FROM Weights where `User` = '{user}' ORDER BY Time", con=sqlEngine)

        sinceLast = 0
        weightLoss = 0 
        relative = 0

        timestamp = None
        
        if len(frameWeights) > 0:
            
            #Change order of date
            orderDate['Time'] = orderDate['Time'].apply(lambda x: pd.Timestamp(x).strftime('%d-%m-%Y'))

            timestamp = orderDate['Time'].iloc[-1]
            newestEntry = orderDate['Weight'].iloc[-1]
            bmi = calculateBMI(heights[i], newestEntry)
        else:
            newestEntry = 0
            bmi = 0

        if len(orderDate) > 1:
            firstEntry = orderDate['Weight'].iloc[0]
            lastEntry = orderDate['Weight'].iloc[-2]
            
            sinceLast = lastEntry - newestEntry
            weightLoss = firstEntry - newestEntry
            relative = ( weightLoss / firstEntry ) * 100
           
        rows.append( [users[i], newestEntry, weightLoss, relative, sinceLast, bmi, timestamp])

    return users, rows

def calculateBMI(height, weight):
    bmi = weight / (height**2)
    return bmi

app = Flask(__name__)
sqlEngine = create_engine('mysql+pymysql://pi:Me200790Hc@localhost/db', echo=False)

@app.route('/')
def hello_world():    
        
    users, rows = getUsersAndWeightList()

    rows = formatRows(rows) 

    return render_template('index.htm', users=users, rows=rows)

@app.route('/enterweight', methods = ['POST'])
def enterWeight():
    user = request.form['user']
    weight = request.form['weight']

    if not weight:
        return "You Must Input a Valid Weight"
    
    time = datetime.datetime.now()
    time = f"{time.year}-{time.month}-{time.day} {time.hour}:{time.minute}:{time.second}"

    insert = sqlEngine.execute(f"INSERT INTO Weights (`User`, `Weight`, `Time`) VALUES ('{user}', '{weight}', '{time}')")

    return redirect('/')

@app.route('/byrel')
def rel():
    users, rows = getUsersAndWeightList()
    
    rows.sort(key=lambda x: x[3], reverse=True)

    rows = formatRows(rows) 

    return render_template('index.htm', users=users, rows=rows)

@app.route('/byweight')
def weight():
    users, rows = getUsersAndWeightList()
    
    rows.sort(key=lambda x: x[1], reverse=False)

    rows = formatRows(rows) 
    
    return render_template('index.htm', users=users, rows=rows)

@app.route('/bybmi')
def bmi():
    users, rows = getUsersAndWeightList()
    
    rows.sort(key=lambda x: x[5], reverse=False)
        
    rows = formatRows(rows) 

    return render_template('index.htm', users=users, rows=rows)

@app.route('/bytotalloss')
def total():
    users, rows = getUsersAndWeightList()
    
    rows.sort(key=lambda x: x[2], reverse=True)

    rows = formatRows(rows) 

    return render_template('index.htm', users=users, rows=rows)

@app.context_processor
def inject_enumerate():
    return dict(enumerate=enumerate)
