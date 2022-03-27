from flask import Flask, render_template
import pandas as pd
import json
import plotly
import plotly.express as px
from sqlalchemy import create_engine
import pymysql

app = Flask(__name__)
@app.route('/')
def hello_world():
    sqlEngine = create_engine('mysql+pymysql://root:root@localhost/db', echo=False)
    frameUsers = pd.read_sql("select * from Users", con=sqlEngine);
   
    userids = list(frameUsers.id)
    users = list(frameUsers.User)
    
    weightList = []

    for i, user in enumerate(userids):
        frameWeights = pd.read_sql(f"select * from Weights where User = {user}", con=sqlEngine)

        orderDate = pd.read_sql(f"SELECT * FROM Weights where User = {user} ORDER BY Time", con=sqlEngine)

        sinceLast = 0
        weightLoss = 0 
        relative = 0
        
        if len(frameWeights) > 0:
            newestEntry = orderDate['Weight'].iloc[-1]
        else:
            newestEntry = 0

        if len(orderDate) > 1:
            firstEntry = orderDate['Weight'].iloc[0]
            lastEntry = orderDate['Weight'].iloc[-2]
            
            sinceLast = lastEntry - newestEntry
            weightLoss = firstEntry - newestEntry
            relative = ( weightLoss / firstEntry ) * 100
            
        
        weightList.append( [users[i], newestEntry, weightLoss, relative, sinceLast])

    return render_template('index.htm', users=users, weights=weightList )


