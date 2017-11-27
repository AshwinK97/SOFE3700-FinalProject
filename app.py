from flask import Flask, render_template, request
import sqlite3 as sql
import json, plotly
import numpy as np
import pandas as pd

from plot import *

# file imports
from setup import setup

setup() # run initial setup
app = Flask(__name__)

# perform insert query
def select(query, params):
	con = sql.connect("db/database.db")
	con.row_factory = sql.Row
	cur = con.cursor()
	try:
		cur.execute(query, params)
	 	return cur
	except:
	 	return "error: could not return cursor"

# Define routes
@app.route('/')
def home():
	return render_template("homepage.html", rows = select("select * from Tickers", []).fetchall())

@app.route('/about')
def about():
	return render_template('about.html')

@app.route('/compare', methods=['GET'])
def compare():
	cmp1, cmp2 = "", ""
	if request.args:
		cmp1, cmp2 = request.args.get('compare1'), request.args.get('compare2')
	return render_template('compare.html', tickers = select("select * from Tickers", []).fetchall(), data = [cmp1, cmp2])

## move to seperate file
@app.route('/graph/<int:ticker>')
def graph(ticker):
	ticker_info = select("select name, company from Tickers where id = ?", [ticker]).fetchone()
	cur = select('''select Prices.date, Prices.open, Prices.close, Prices.high, Prices.low, Prices.volume
		from Prices join Tickers on Tickers.id = Prices.ticker_id
		where Prices.ticker_id = ?
		order by price_id ASC
		limit 500''', [ticker])

	rows = cur.fetchall();
	columns = list(map(lambda col: col[0], cur.description))

	df = pd.DataFrame(rows)
	df.columns = columns

	tables = [df.head(25).to_html(classes='pure-table', index=False)]
	
	#Testing new plot functions
	plot_candlestick = candlestick(df.date.tolist(), df.open.tolist(), df.close.tolist(), df.high.tolist(), df.low.tolist())
	plot_line_close = line(ticker_info[0]+'.Close', df.date.tolist(), df.close.tolist())

	data = [plot_candlestick, plot_line_close]

	graphs = [{
		"data": data,
		"layout": {
			"title": ticker_info[0],
			"dragmode": 'zoom', 
			"margin": {
				"r": 10, 
				"t": 25, 
				"b": 40, 
				"l": 60
			},
			"showlegend": False
		}
	}]

	# Add "ids" to each of the graphs to pass up to the client
	# for templating
	ids = ['graph-{}'.format(i) for i, _ in enumerate(graphs)]

	# Convert the figures to JSON
	# PlotlyJSONEncoder appropriately converts pandas, datetime, etc
	# objects to their JSON equivalents
	graphJSON = json.dumps(graphs, cls=plotly.utils.PlotlyJSONEncoder)

	return render_template("graph.html", tables = tables, ids = ids, graphJSON = graphJSON, name = ticker_info[0], company = ticker_info[1])

@app.route('/stock/<int:ticker>')
def stock(ticker):
	price_select_all = select("select date, open, high, low, close, volume from Prices where ticker_id = ? order by price_id asc", [ticker])
	
	price_rows = price_select_all.fetchall()
	price_columns = list(map(lambda col: col[0].title().replace('_', ''), price_select_all.description))
	
	price = pd.DataFrame(price_rows)
	price.columns = price_columns

	ticker_info = select("select id, name, company from Tickers where id = ?", [ticker]).fetchone()

	return render_template("stock.html", table = price.to_html(classes='pure-table pure-table-bordered', index=False), info = ticker_info)

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

if __name__ == '__main__':
	app.run(debug=True, port=8080)
