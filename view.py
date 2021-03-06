import random
import StringIO
import pandas as pd
import sys, os
from flask import Flask, url_for
from model import *
import flask
import tempfile
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import ScalarFormatter, FormatStrFormatter

class Page:
	def home(self, params):
		section = PageSection()
		header = section.site_header(params)
	
		#SECTION HEADING
		tb1 = TextBlock('section_heading', 'section_heading', 'Percent ' + Lookup.panel_text[params['ind_code']])
	
		obj = VisualObjectPanel('ind_change_table', params) 
		vop1 = obj.html

		tb2 = TextBlock('section_heading', 'section_heading', 'Year by year ' + Lookup.panel_text[params['ind_code']])
	
		obj = VisualObjectPanel('multi_year_chart', params)
		vop2 = obj.html

		#BUILD AND OUTPUT THE PAGE
		html = header + tb1.html + vop1 + tb2.html + vop2
	
		html += '</div></body></html>'
		return html

	def region(self, params):
		section = PageSection()
		header = section.site_header(params)
		output = header
		return output


class PageSection:
	def site_header(self, params):

		#flask_version = flask.__version__
		flask_version = pd.__version__
		css_file = url_for('static', filename='styles.css', _external=True)
		js_file = url_for('static', filename='indicators.js', _external=True)
		image_file = url_for('static', filename='d3-sample.png', _external=True)
		cb_image_file = url_for('static', filename='contact-box-head.png', _external=True)
		style_string = '<link rel=stylesheet type=text/css href="' + css_file + '">'
		js_string = '<script type="text/javascript" src="' + js_file + '"></script>'
		image_string = '<img class="header_image" src="' + image_file + '" alt="Analytics">'
		contact_box_image = '<img src="' + cb_image_file + '" alt="Contact">'
		if params['page_name'] == 'home':
			item_list = ItemList('indicators', 'Indicator:', Lookup.ind_text, 'EN.ATM.CO2E.PC', False)
		
		elif params['page_name'] == 'index_vs_indicator':
			rl = RegionList()
			regions = rl.data;
			#convert list to dict since the ItemList class requires a dictionary of key:value pairs
			regions_dict = dict((k,k) for k in regions)
			item_list = ItemList('region', 'Region:', regions_dict, 'North America', False)

		start_year = InputBox('start_year', 'Start Year:', 'year', params['start_year'], True)
		end_year = InputBox('end_year', 'End Year:', 'year', params['end_year'], True)

		output = """<!DOCTYPE html>
		<head>
		    <title>Indicator Analysis -- Developing Countries</title>
			<link href='//fonts.googleapis.com/css?family=Montserrat' rel='stylesheet' type='text/css'>
			%s
			<script src="//ajax.googleapis.com/ajax/libs/jquery/1.10.2/jquery.min.js"></script>
			%s
		</head>
			<html>
			<body>
			<div class="page">
				<div class="site_header">
					<div class="site_menu">
						<div class="home_link">Home</div>
						<div class="site_menu_link">Index Analysis</div>
						<div class="site_menu_link">About</div>
						<div class="site_menu_link">Contact Me</div>
						<div class="site_menu_link">%s</div>
					</div>
					<div class="banner">
						<div class="header_left">World Development Indicators Analysis
							<p class="hlp_1">Created By Jordan Schatzman</p>
							<p class="hlp_2">Python/Pandas/Matplotlib/Flask/Javascript/HTML/CSS</p>
						</div>
						<div class="banner_image">%s</div>
					</div>
					<div class="header_panel">
						<div class="filter_panel">
						%s
						%s
						%s
						</div>
						<div class="header_panel_button" id="main_submit">Submit</div>
					</div>
				</div>
                <div class="contact_box">
					<div class="contact_box_head">%s</div>
					<div class="contact_box_text">
						<div class="cb_text1">Feel free to contact me at</div>
						<div class="cb_text2">
							<a href="mailto:jordan.schatzman@outlook.com">jordan.schatzman@outlook.com</a>
						</div>
					</div>
					<div class="close_parent">x</div>
				</div>
			""" % (style_string, js_string, flask_version, image_string, item_list.get_html(), start_year.html, end_year.html, contact_box_image)
		
		return output  + about_box()

class  VisualObjectPanel:
	
	'''
		A Visual Object Panel is a group of related html objects such as charts or tables that display the same type of data but in different ways
		such as for different regions.

		This class encloses all of its items into an html flexbox div.
	'''
	
	def __init__(self, panel_type, params):	
		self.items = []
		self.params = params
		
		self.build_items(panel_type)
		self.html = '<div class="visual_object_panel">'
		for item in self.items:
			self.html += item
		
		self.html += '</div>'  #close the panel
	
	def build_items(self, panel_type):
		rlist = RegionList()
		regions = rlist.data
		
		if panel_type == 'ind_change_table':
			lookup = Lookup()
			for region in regions:
				q = Query()
				cl = CountryList()
				country_list = cl.by_region(region)
				data = q.indicator_change(country_list, self.params)
				ht = HTMLTable('indicator_1', 'ind_table', 'ind_table_1', region, lookup.get_column_names('indicator_1', self.params), data)
				
				self.items.append(ht.html)
		
		elif panel_type == 'multi_year_chart':
			for region in regions:
				q = Query()
				cl = CountryList()
				country_list = cl.by_region(region)
				data = q.indicator_over_time(country_list, self.params)
				ap = ArrayProcessor()
				plot_data = ap.format_for_plot(data)
				
				chart = Chart(region, 'Year', 'Indicator Value', plot_data)
				self.items.append(chart.plot_values_over_years(self.params))
		
		elif panel_type == 'indicator_vs_index_panel':
			for img in self.params['img_array']:
				self.items.append(img)


class TextBlock:
	
	def __init__(self, css_class, block_type, text):

		self.block_type = block_type
		self.css_class = css_class
		self.text = text
		self.html =  '<div class="' + self.css_class + '">' + self.text + '</div>'
	
class Chart:
	#Class-level variables common to all chart objects:
	#plot_formats = ['b-', 'r-', 'g-', 'c-', 'm-', 'y-', 'bo', 'ro', 'go', 'co', 'mo', 'yo']
	line_styles = [('#ff3232', '-'), ('#ff8e32', '-'), ('#32c8ff', '-'), ('#979ffc', '-'), 
					('#60cbf2', '-'), ('#81bf78', '-'), ('#b877ce', '-'), ('#dd6cd8', '--'), ('#6b73ce', '--'), ('#7ac992', '--'), ('#564f4c', '--'), ('#f4e258', '--')]
	def __init__(self, title, x_label, y_label, data):
		#Initialize instance variables
		self.title = title
		self.x_label = x_label
		self.y_label = y_label
		self.data = data

	def plot_values_over_years(self, params):
		
		#Get the range of years
		start_year = params['start_year'] 
		end_year = params['end_year']

		#Use Python list comprehension to get the highest indicator value in the data. For now, assume the lowest value is 0
		min_val = 0.0
		max_val = max( [max(self.data[i][3]) for i in range(0, len(self.data))] )
		plt.xticks(rotation=70)	
		#For vertical padding on the chart, add 10% to highest value so the plot values don't hit the very top of the graph
		plt.axis([start_year, end_year, min_val, 1.1 * max_val])
		ax = plt.gca()
		ax.xaxis.set_major_formatter(FormatStrFormatter('%.0f'))  #Prevent years from being displayed in default scientific notation
		ax.set_axis_bgcolor('#f2f2f2')
		#Up to 12 plots per chart are supported.
		i = 0
		#log = Log()
		#log.writeline('debug', 'self.data before loop', 'plot_values_over_years', self.data)
		for row in self.data:
			plt.plot(row[2], row[3], color=self.line_styles[i][0], linestyle=self.line_styles[i][1], linewidth=2, label=self.data[i][1])
			i += 1
			if i == 11:
				break

		plt.xlabel(self.x_label)
		plt.ylabel(self.y_label)
		plt.title(self.title)
		plt.legend()	
		
		plt.gcf().subplots_adjust(bottom=0.15) #stretch the bottom of the chart to prevent the x-axis label from being cut off
		
		f = tempfile.NamedTemporaryFile(dir = '/var/www/flasky/flasky/static/temp', suffix='.png', delete=False)
		plt.savefig(f)

		#Need to close the current plot or matplotlib will plot future graphs on the same chart, even if using a different chart object
		plt.close()
		f.close()
		plotPng = f.name.split('/')[-1]
		#The URL http://lockers.cloudapp.net points to /var/www/flasky/flasky so all references to relative file paths automatically have that path appended.
		#Therefore, the relative path static/temp actually points to the absolute path /var/www/flasky/flasky/static/temp
		html = '<div class="ind_chart"><img src="http://lockers.cloudapp.net/static/temp/' + plotPng + '"></div>'
		return html

	def index_vs_indicator(self, ind_code, region, start_year, end_year):
		indicators = ['EG.USE.COMM.CL.ZS', 'NY.GDP.PCAP.PP.CD', 'SH.H2O.SAFE.ZS']
		index_test = Index(indicators,[.01,.00001333, .01])
		index_test.generate_dataframe(ind_code, region, start_year, end_year)
		colors = ('blue', 'green', 'red', 'black', 'orange', 'blue', 'green', 'red', 'black')
		titlesize = 20
		axeslabelsize = 20
		ticksize = 17
		legendsize = 15
		country_list = list(set(index_test.df['CountryName']))
		column_list = [col for col in index_test.df.columns if col not in ['Year', 'CountryName']]
#		fix, ax = plt.subplots(1,1,figsize=(10,10))
#		ax2 = ax.twinx()
		count = 0
		html = []
		max_year = index_test.df['Year'].max()
		min_year = index_test.df['Year'].min()
		max_index = index_test.df['Index'].max()*(1.1)
		max_indicator = index_test.df[column_list[0]].max()*(1.1)
		for i in country_list:
			fig, ax = plt.subplots(1,1,figsize=(10,10))	
			#fig, ax = plt.subplots(1,1)	
			ax2 = ax.twinx()
			ax.set_title(i + '\n', fontsize = titlesize, fontweight = 'bold')
			ax.plot(index_test.df[index_test.df['CountryName'] == i]['Year'], 
            	    index_test.df[index_test.df['CountryName'] == i]['Index'],
				    label = 'Index',
					color = 'red',
					 #color = self.line_styles[count+1][0],
					 #linestyle=self.line_styles[count+1][1],
					linewidth=2)
			ax2.plot(index_test.df[index_test.df['CountryName'] == i]['Year'], 
					 index_test.df[index_test.df['CountryName'] == i][column_list[0]],
					 label = column_list[0],
					 color = 'blue',
					 #color = self.line_styles[count+1][0],
					 #linestyle=self.line_styles[count+1][1],
					 linewidth = 2)
			count = count + 1
			ax.set_xlabel('\n Value', fontsize = axeslabelsize)
			ax.set_xlim([min_year, max_year])
			ax.set_ylabel('\n Index', fontsize = axeslabelsize)
			ax.legend(loc='upper left', shadow=True, prop= {'size':legendsize})
			ax.set_axis_bgcolor('#f2f2f2')
			ax.tick_params(labelsize=ticksize)
			ax.set_ylim(0,max_index)
			ax2.set_ylabel(column_list[0], fontsize = axeslabelsize)
			ax2.legend(loc='upper right', shadow=True, prop= {'size':legendsize})
			ax2.set_axis_bgcolor('#f2f2f2')
			ax2.tick_params(labelsize=ticksize)
			ax2.set_ylim(0,max_indicator)
			ax.ticklabel_format(style='plain', useOffset=False)
			#Save the figure as a temporary file in the static/temp directory
			f = tempfile.NamedTemporaryFile(dir = '/var/www/flasky/flasky/static/temp', suffix='.png', delete=False)
			plt.savefig(f)	
			#Need to close the current plot or matplotlib will plot future graphs on the same chart, even if using a different chart object
			plt.close()
			f.close()
			plotPng = f.name.split('/')[-1]
			#The URL http://lockers.cloudapp.net points to /var/www/flasky/flasky so all references to relative file paths automatically have that path appended.
			#Therefore, the relative path static/temp actually points to the absolute path /var/www/flasky/flasky/static/temp
			html.append('<div class="ind_chart"><img src="http://lockers.cloudapp.net/static/temp/' + plotPng + '"></div>')
		return html
  

#		fig, ax = plt.subplots(1,1,figsize=(10,10))
#		count = 0
#		for i in country_list:
#			ax.plot(
#				index_test.df[index_test.df['CountryName'] == i]['Year'], 
#				index_test.df[index_test.df['CountryName'] == i]['Index'],
#				label = i, 
#				color = colors[count]
#				)
#			count = count + 1
#
#		ax.set_title(index_test.region + '\n', fontsize = titlesize, fontweight = 'bold')
#		ax.set_xlabel('\n Value', fontsize = axeslabelsize)
#		ax.set_ylabel('\n Index', fontsize = axeslabelsize)
#		ax.legend(loc='upper left', shadow=True, prop= {'size':legendsize})
#		ax.set_axis_bgcolor('#f2f2f2')
#		ax.tick_params(labelsize=ticksize)

		#Save the figure as a temporary file in the static/temp directory
#		f = tempfile.NamedTemporaryFile(dir = '/var/www/flasky/flasky/static/temp', suffix='.png', delete=False)
#		plt.savefig(f)
		
		#Need to close the current plot or matplotlib will plot future graphs on the same chart, even if using a different chart object
#		plt.close()
#		f.close()
#		plotPng = f.name.split('/')[-1]
		#The URL http://lockers.cloudapp.net points to /var/www/flasky/flasky so all references to relative file paths automatically have that path appended.
		#Therefore, the relative path static/temp actually points to the absolute path /var/www/flasky/flasky/static/temp
#		html.append('<div class="ind_chart"><img src="http://lockers.cloudapp.net/static/temp/' + plotPng + '"></div>')


	def do_chart(self):

		APP_ROOT = os.path.dirname(os.path.abspath(__file__))
		exponent = .7 + random.random()*.6
		dta = []
		
		for i in range(50):
			rnum = int((random.random()*10)**exponent)
			dta.append(rnum)
		
		y = sorted(dta)
		x = range(len(y))

		fig = plt.figure(figsize=(5,4),dpi=100)
		axes = fig.add_subplot(1,1,1)
		axes.plot(x,y,'-')
		axes.set_xlabel('time')
		axes.set_ylabel('size')
		axes.set_title("A matplotlib plot")
		f = tempfile.NamedTemporaryFile(dir = '/var/www/flasky/flasky/static/temp', suffix='.png', delete=False)
		plt.savefig(f)
		f.close()
		plotPng = f.name.split('/')[-1]
		#The URL http://lockers.cloudapp.net points to /var/www/flasky/flasky so all references to relative file paths automatically have that path appended.
		#Therefore, the relative path static/temp actually points to the absolute path /var/www/flasky/flasky/static/temp
		html = '<div class="ind_chart"><img src="static/temp/' + plotPng + '"></div>'
		return html

class HTMLTable:
	
	def __init__(self, table_type, css_class, css_id, title, columns, data):
		self.data = data
		self.columns = map(str, columns)  #convert any non-string elements to string to avoid concatenation issues of different types
		self.html = '<table class="ind_table"><caption>' + title + '</caption>'
		self.table_type = table_type
		self.html += self.table_head()
		self.html += self.table_body()
		self.html += '</table>'

	def table_head(self):
		head = '<tr>'
		for i in range(0, len(self.columns)):
			head += '<th class="th_normal">' + self.columns[i] + '</th>'
		
		head += '</tr>'

		return head
	
	def table_body(self):
		output = ''
		for i in range(0, len(self.data)):
			output += '<tr>'	
			
			for j in range(0, len(self.data[0])):
				output += '<td>' + str(self.data[i][j]) + '</td>'
			
		output += '</tr>'
	
		return output

class ItemList:
	"""
	Creates a list of items in vertical format that are output to the browser as a listbox.
	"""
	def __init__(self, list_id, label, items, default_item_key, centered):

		self.list_id = list_id
		self.label = label
		self.items = items  #must be a dictionary of the form {key1:value1, key2:value2, ... }
		self.centered = centered
		self.default_item_key = default_item_key

	def get_html(self):
		output = '<div class="item_list_head">'  #flexbox: row layout 
		output += '<div class="item_list_label">' + self.label + '</div>'
		output += '<div class="selected_item" id="' + self.list_id + '_anchor" data-value="' + self.default_item_key + '">' + self.items[self.default_item_key] + '</div></div>' #end div.item_list_head

		list_items = '<div class="item_list" id="' + self.list_id + '">' #flexbox: column layout
		for item in self.items:
			if self.centered:
				list_items += '<div class="item text_align_center" data-value="' + str(item) + '">' + str(self.items[item]) + '</div>'  #flexbox column items
			else:
				list_items += '<div class="item" data-value="' + str(item) + '">' + str(self.items[item]) + '</div>'  #flexbox column items

		output += list_items + '</div>'  #end item_list
		self.html = output
		return self.html

class InputBox:

	def __init__(self, input_id, label, input_type, value, centered):
		self.input_id = input_id
		self.input_type = input_type
		self.label = label
		self.input_class = 'input_box'
		self.value = value
		
		self.centered = centered

		if input_type == 'year':
			self.placeholder = 'YYYY'
			self.input_class += ' input_year'

		if self.centered == True:
			self.input_class += ' text_align_center'

		if value is not None:
			self.value_string = 'value="' + str(value) + '"'
		else:
			self.value_string = ''
	
		self.html = '<div class="input_box_container">' #flexbox row layout
		self.html += '<div class="input_box_label">' + self.label + '</div>'
		self.html += '<input type="text" id="' + self.input_id + '" class="' + self.input_class + '" placeholder="' + self.placeholder + '"' + self.value_string + '>'
		self.html += '</div>'

def about_box():
	html = '''
		<div class="about_box">
			<div class="close_parent">x</div>
			<div class="ab_menu">
				<div class="ab_menu_item" id="ab_item_1">Background</div>
				<div class="ab_menu_item" id="ab_item_2">Focus</div>			
				<div class="ab_menu_item" id="ab_item_3">Data</div>
				<div class="ab_menu_item" id="ab_item_4">Technology</div>
			</div>
			<div class="ab_content">
				<h1>Title</h1>
				<div class="ab_text" id="ab_text_1">
					<p>This project sprang from a desire to learn the Python programming language.  As a database developer, I wanted to
					complement my database design and SQL skills with additional data processing and analytical capabilities.  Since Python 
					seems designed for this, it seemed the natural choice.
					</p>
					<p>Since there are lots of public datasets on <a href="http://www.kaggle.com" target="_blank">kaggle.com</a>, I started there.  Eventually, I chose the
					<a href="http://www.kaggle.com/worldbank/world-development-indicators" target="_blank">World Development Indicators</a> (WDI) database since there are millions of
					rows of great data that can be used to visualize world trends and prove or disprove certain hypotheses.  WDI comes in a handy
					sqlite database container, which Python can access easily simply by importing sqlite3.
					</p>
				</div>
				<div class="ab_text" id="ab_text_2">
					<p>The WDI database contains hundreds of different indicators such as population trends, disease trends, etc, so to narrow the focus of the project, 
					I decided to focus on indicators associated with global energy use.  To make it a true data analytics project, I decided to come up with an interesting question
					and then apply different technologies over the dataset to try and answer that question.
					</p>
					<p>The question I asked was this:  "As a country becomes more advanced, does it consume more energy or less energy? This was a good question because the 
					answer wasn't necessarily obvious. It could actually go either way.  For example, as a country gets more advanced, more people use things that require energy,
					and that might lead to more overall energy use.  Or maybe it's the opposite:  As a country gets more advanced, things that use energy are replaced with more efficient
					things that consume less energy, leading to less overall energy use.
					</p>
					<p>Although the question is simple enough, answering simple questions can turn out to be surprisingly difficult if you want to answer them accurately.
					For example, how do you define "advanced" and then measure it?  What indicators are the best measure of energy consumption?
					</p>
				 
				</div>
				<div class="ab_text" id="ab_text_3">
					<p>The data used in this project has been compiled by the <a href="http://www.worldbank.org/">World Bank</a>, a non-profit organization dedicated to ending extreme
					poverty and increasing shared prosperity across the globe.  Data in this database has been gathered since the 1960s.  Although remarkably comprehensive, the dataset
					is not complete.  Some data points for certain countries and some years is not available, so the code had to take this into account.
					</p>
					<p>There are over 1,000 distinct indicators available in this dataset, many of which are very important descriptors of the quality of life of a country's citizens as well as its 
					overall development.  There's no limit to the different methods one could use to measure development, but we have chosen three that we find most important: GDP/capita, PPP ($US), access to an improved water source
					(% of total population) and alternative energy sources used (% of total).  The coefficients for each are the about equal to the inverse of the maximum of each indicator observed in the entire dataset.  
					This means that if a country has the greatest value for each of three indicators across all time and countries in a given year, then it will receive a "perfect" score of 1.   </p>
				</div>
				<div class="ab_text" id="ab_text_4">
					<p>A diverse set of technologies was used to create this project.  Server-side code was developed using Python, Numpy, Pandas, Matplotlib, and SQL. Client-side code 
					 involved "raw" coding in HTML5, CSS3, and jQuery.  The Flask framework was used to interact with the web server, but mostly for URL routing and 
					delivery of data to clients over HTTP.  No Flask templates were used, since the point was to develop a bit of proficiency in full-stack programming. 
					 </p>
					<p>All the layout and styles of the website are completely custom.  I took advantage of lots of invaluable guidance from a colleague who understands responsive front-end design.  
					This helped make the website look good and behave itself across a variety of browsers and devices.  I could not have done this project without his help.</p>
					<p>The host is a low-capacity Ubuntu Linux server running in the Microsoft Azure cloud.  Source code control was done exclusively using Git with a hub-and-spoke architecture and 
					a variation on the feature-branch workflow.  Three repositories were used for development and deployment: my laptop's local respository, a bare repository acting as the publishing hub,
					and a production repository in the web server (/var/www/...) where all the public files were made available. 
				</div>
			</div>
		</div>
		'''
	return html
