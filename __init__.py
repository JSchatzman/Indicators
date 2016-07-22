from flask import Flask, url_for, render_template
import sqlite3
import json
from flask import request
from model import *
from view import *
app = Flask(__name__)

@app.route("/")
def home():
	log = Log()
	log.truncate()
	purge_temp_files(1) #delete all chart images in the temp directory over 1 day old so they don't accumulate

	#Set default parameters just to start the application.  The user may change these later.
	params = {'page_name':'home', 'ind_code':'EN.ATM.CO2E.PC', 'start_year':2000, 'end_year':2007}
	page = Page()

	return page.home(params)

	#If using Flask templates, move everything above into index.html and uncomment the following line:
	#return render_template('index.html')

@app.route('/params/<parameters>')
def home_request(parameters):
	param_list = parameters.split('+')
	params = {'page_name':'home', 'ind_code': param_list[0], 'start_year': int(param_list[1]), 'end_year': int(param_list[2])}
	page = Page()
	return page.home(params)

@app.route('/index_vs_indicator/<parameters>')
def ivi_request(parameters):
	param_list = parameters.split('+')
	regions = RegionList()
	if param_list[0] not in regions.data:
		param_list[0] = 'North America'
	if 1960 <= param_list[1] <= 2015:
		param_list[1] = 2001
	if 1960 <= param_list[2] <= 2015:
		param_list[2] = 2010
	page = Page()
	chart = Chart('Index vs Indicator', 'x label', 'y label', ['123', '456'])
	html = chart.index_vs_indicator('EG.USE.PCAP.KG.OE', 'North America', int(param_list[1]), int(param_list[2]))
	params = {'page_name':'index_vs_indicator', 'ind_code': param_list[0], 'start_year': int(param_list[1]), 'end_year': int(param_list[2]), 'img_array': html}
	vop = VisualObjectPanel('indicator_vs_index_panel', params)
	output = page.region(params) + vop.html
#	for i in html:
#		output = output + i
	return output


app.debug = True
if __name__ == "__main__":
	app.run(debug = True)

