from flask import Flask, render_template, request, redirect
import pandas as pd
import json
import plotly
import plotly.express as px
import plotly.graph_objects as go
from sqlalchemy import create_engine, insert
import pymysql 
import datetime
from operator import itemgetter
import numpy as np

def formatRows(rows):
    for r, row in enumerate(rows):
        for c, col in enumerate(row):
            if c == 1:
                rows[r][c] = f"{col:.1f} Kg"
            if c == 2:
                rows[r][c] = f"{col:.1f} Kg"
            if c == 3:
                rows[r][c] = f"{col:.2f} %"
            if c == 4:
                rows[r][c] = f"{col:.1f} Kg"
            if c == 5:
                rows[r][c] = f"{col:.1f} Kg/m²"
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
#sqlEngine = create_engine('mysql+pymysql://root:root@localhost/db', echo=False)
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

@app.route('/plot', methods = ['POST'])
def plot():

    user = request.form['user']
    users, rows = getUsersAndWeightList()
    
    weights = []
    dates = []
    
    fig = go.Figure()

    if user == 'all':
        
        for i, user in enumerate(users):
            frameWeights = pd.read_sql(f"select * from Weights where `User` = '{user}'", con=sqlEngine)
            weights.append( list( frameWeights['Weight'] ) )
            dates.append( list( frameWeights['Time'] ) )
            
            fig.add_trace(
            go.Scatter(x=dates[i], y=weights[i], mode='lines+markers', name=user)
            )
        fig.update_layout(
                   xaxis_title='Date and Time',
                   yaxis_title='Weight[Kg]')
    else:
        frameWeights = pd.read_sql(f"select * from Weights where `User` = '{user}'", con=sqlEngine)
    
        weights = list( frameWeights['Weight'] )
        dates = list( frameWeights['Time'] )
        
        fig.add_trace(
            go.Scatter(x=dates, y=weights, mode='lines+markers', name=user)
            )
        fig.update_layout(
                   xaxis_title='Date and Time',
                   yaxis_title='Weight[Kg]')

    #fig.update_xaxes(tickformat="%b %d %I \n%Y")
    graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

    header="Development of Weight over Time"
    
    return render_template('plot.html', graphJSON=graphJSON, header=header)

@app.route('/user', methods = ['POST'])
def user():

    user = request.form['user']
    
    frameWeights = pd.read_sql(f"select * from Weights where `User` = '{user}'", con=sqlEngine)
    #frameWeights['Time'] = frameWeights['Time'].apply(lambda x: pd.Timestamp(x).strftime('%d-%m-%Y'))

    rows = frameWeights.values.tolist()
    rows = np.array(rows)
    rows = np.flip(rows, axis=0)
    ids = rows[:, 0].copy()

    

    rows[:, 0:2] = rows[:,1:3]
    rows[:, 2] = rows[:, 4]
    rows[:, 3] = rows[:, 0]
    rows = rows[:, 0:4]

    for row in rows:
        if pd.isnull(row[2]):
            print("not modified")
            row[2] = "Not Modified"
        

    print(rows)

    return render_template('user.html', user=user, rows=rows, ids=ids)

@app.route('/modify', methods = ['POST'])
def modify():

    user = request.form['user']
    weight = request.form['weight']
    Id = request.form['id']

    if not weight:
        return "You Must Input a Valid Weight"
    
    time = datetime.datetime.now()
    time = f"{time.year}-{time.month}-{time.day} {time.hour}:{time.minute}:{time.second}"

    modify = sqlEngine.execute(f"   UPDATE Weights \
                                    SET `Weight` = '{weight}' \
                                    WHERE id = {Id} \
                                ")
    
  
    return redirect('/')

@app.context_processor
def inject_enumerate():
    return dict(enumerate=enumerate)
