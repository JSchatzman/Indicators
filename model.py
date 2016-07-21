import sqlite3
import os, time, sys
import pandas as pd
import json
from constants import *
from datetime import datetime

class YearList:
	years = []

	def years(self, indicator_code):
		
		if indicator is None:
			sql = 'SELECT DISTINCT Year FROM Indicators'
		else:
			sql = 'SELECT DISTINCT Year FROM Indicators WHERE IndicatorCode = ' + "'" + indicator_code + "'"
		
		conn = sqlite3.connect(DB_PATH)
		c = conn.cursor()
	 	c.execute(sql)
		self.years = c.fetchall()
		c.close()
		return self.years

class RegionList:
	def __init__(self):
		self.data = []
		conn = sqlite3.connect(DB_PATH)
		c = conn.cursor()
		sql = 'SELECT DISTINCT region_name FROM X_Country ORDER BY region_name'
	 	c.execute(sql)
		rows = c.fetchall()
		c.close()
		
		#rows contains an array of tuples, each of which has one element, so extract the value from the tuple wrapper to create an array of simple strings
		for row in rows:
			self.data.append(row[0])
		
class CountryList:
	def __init__(self):
		self.data = []

	def by_region(self, region):

		conn = sqlite3.connect(DB_PATH)
		c = conn.cursor()
		sql = 'SELECT country_name FROM X_Country WHERE region_name = ' + "'" + region + "'" + ' ORDER BY country_name'
	 	c.execute(sql)
		rows = c.fetchall()
		c.close()
		
		#rows contains an array of tuples, each of which has one element, so extract the value from the tuple wrapper to create an array of simple strings
		for row in rows:
			self.data.append(row[0])
		
		return self.data

	def by_region_full(self, region):
		conn = sqlite3.connect(DB_PATH)
		c = conn.cursor()
		sql = 'SELECT country_code, country_name, region_name FROM X_Country WHERE region_name = ' + "'" + region + "'"
	 	c.execute(sql)
		rows = c.fetchall()

		c.close()
		return rows

	def by_samplename(self, sample_name):
		if(sample_name == 'developed_countries_1'):
			return {'USA':'United States', 'CAN':'Canada', 'FRA':'France', 'DEU':'Germany', 'GBR':'Great Britain', 'ESP':'Spain', 'RUS':'Russia', 'SWE':'Sweden', 'IRL':'Ireland', 'ITA':'Italy'}

class Lookup:
	'''
	Provides a set of dictionaries that are useful throughout the application.	
	'''
	
	#Very short indicator descriptions for use within list boxes, etc.
	ind_text = {
		'EN.ATM.CO2E.KT' : 'CO2 Emissions (KT)', 
		'EN.ATM.CO2E.PC' : 'CO2 Emissions (MT/Capita)', 
		'EN.ATM.CO2E.KD.GD' : 'CO2 Emissions kg/2005 US GDP', 
		'EN.ATM.CO2E.PP.GD.KD' : 'CO2 Emissions,kg/2011 US GDP', 
		'EG.USE.COMM.GD.PP.KD' : 'Energy Use kg/$1000 GDP'
		}
	
	#Panel descriptions
	panel_text = {
		'EN.ATM.CO2E.PC' : 'change in total carbon dioxide emissions per capita over the selected timeframe. Values shown are metric tons per capita.',
		'EN.ATM.CO2E.KT' : 'change in total carbon dioxide emissions over the selected timeframe.  Values shown are in kilotons.',
		'EN.ATM.CO2E.KD.GD' : 'change in total carbon dioxide emissions over the selected timeframe. Values shown are in kilograms per 2005 U.S. Gross Domestic Product',
		'EN.ATM.CO2E.PP.GD.KD' : 'change in total carbon dioxide emissions over the seleted timeframe.  Values shown are in kilograms per 2011 U.S. Gross Domestic Product',
		'EG.USE.COMM.GD.PP.KD' : 'change in energy consumption over the selected timeframe.  Values shown are in kilograms per $1,000 Gross Domestic Product'
	}

	#Sets of column names for specific table types:
	table_columns = {
		'indicator_1': ['Country', 'start_year', 'end_year', '% Change'],
		'indicator_2': ['Country', 'Year', 'Value']
	}

	def get_column_names(self, table_key, params):
		
		'''Returns a list of table columns from the table_columns dictionary in this class, performing any column name substitutions using the params argument.'''
		
		column_names = list(self.table_columns[table_key])  #make a new list of the column names from the desired table
		for col in column_names:
			if col in params.keys():
				index = get_element_index(col, column_names)
				if index != None:
					column_names[index] = params[col]

		return column_names

class Query:
	
	def indicator_over_time(self, country_list, params):
		
		#Validate parameters
		if params['start_year'] < 1960 or params['end_year'] > 2015:
			return INVALID_PARAMETER
		
		#Create SQL 'IN' clause for country list
		in_clause = self.in_clause('CountryName', country_list, True)
		
		#Get all indicator values for each country and for all years:
		conn = sqlite3.connect(DB_PATH)
		c = conn.cursor()
		sql = "SELECT CountryName, CountryCode, Year, Value FROM Indicators WHERE IndicatorCode = " 
		sql += "'" + params['ind_code'] + "'" + " AND Year Between " + str(params['start_year']) + " AND " + str(params['end_year']) + " AND " + in_clause
		sql += " ORDER BY CountryName, Year"

		c.execute(sql)
		rowset = c.fetchall()

		#Convert tuples to list so the dataset can be modified by the caller.
		array = [list(row) for row in rowset]
		
		return array
		
	def indicator_change(self, country_list, params):
		
		#Validate parameters
		if params['start_year'] < 1960 or params['end_year'] > 2015:
			return INVALID_PARAMETER
		
		in_clause = self.in_clause('CountryName', country_list, True)

		#Get all indicator values for each country for the starting year:
		conn = sqlite3.connect(DB_PATH)
		c = conn.cursor()
		sql = "SELECT CountryName, Year, Value FROM Indicators WHERE IndicatorCode = " 
		sql += "'" + params['ind_code'] + "'" + " AND Year = " + str(params['start_year']) + " AND " + in_clause
		sql += " ORDER BY CountryName"

		c.execute(sql)
		rowset1 = c.fetchall()
		
		#If rowset1 has no row for a particular country because it wasn't in the database, append it as a row with no value: 
		if len(rowset1) != len(country_list):
			xl = [(i[0]) for i in rowset1]
			for element in country_list:
				if element not in xl:
					rowset1.append((element, params['start_year'], '--'))
		
		#If rowset1 has no row because 
		#re-sort the list based on the first element in each row:
		rowset1.sort(key=lambda x: x[0])

		#Get all indicator values for each country for the ending year: 
		sql = "SELECT CountryName, Year, Value FROM Indicators WHERE IndicatorCode = " 
		sql += "'" + params['ind_code'] + "'" + " AND Year = " + str(params['end_year']) + " AND " + in_clause
		sql += " ORDER BY CountryName"

		c.execute(sql)
		rowset2 = c.fetchall()
		
		#If rowset2 has no row for a particular country because it wasn't in the database, append it as a row with no value: 
		if len(rowset2) != len(country_list):
			xl = [(j[0]) for j in rowset2]
			for element in country_list:
				if element not in xl:
					rowset2.append((element, params['end_year'], '--'))
		
		rowset2.sort(key=lambda x: x[0])
		
		#Combine the two rowsets into a single rowset equivalent to a SQL PIVOT.  This is needed because the PIVOT operator
		#is not supported in sqlite.
		array = []
		for i in range(0,len(rowset1)):
			array.append([rowset1[i][0], rowset1[i][2], rowset2[i][2]])
		
		ap = ArrayProcessor()
		output = ap.do_pivot(array)
		output = ap.format_cells(output, 2)
		
		return output 

	def getAvg(self, startYear, endYear):
		c = self.conn.cursor()
		sql = "SELECT CountryCode, AVG(Value) FROM Indicators WHERE CountryCode = " + "'" + self.countryCode + "'" + " AND IndicatorCode = " + "'" + self.indicatorCode + "'" + " AND YEAR BETWEEN " + str(startYear) + " AND " + str(endYear) + " GROUP BY CountryCode"
		c.execute(sql)
		row = c.fetchall()
		return row

	def in_clause(self, col_name, item_list, add_apostrophes):
		string = ''
		#If items are string or dates, apostrophes must be added:
		if add_apostrophes == True:
			for item in item_list:
				string += "'" + item + "'" + ', '
		else:
			for item in item_list:
				string += item + ', '

		#Remove extra space and comma on right side of string
		string = string[0: len(string) - 2]

		return col_name + ' IN (' + string + ')'
		
class ArrayProcessor:

	def format_for_plot(self, dataset):
		""" Converts a list having rows like [<country_name>, <country_code>, <year>, <indicator_value>] into a list having rows like
			[<country_name>, <country_code>, [<year1>,<year2>,<year3>,<year4>], [<ind_value1>,<ind_value2>,<ind_value3>,<ind_value4>]]
			Pyplot expects this format.
		"""
		x = []
		y = [] 
		plot_data = []
		
		cn = dataset[0][0] #Remember the first country name
		cc = dataset[0][1]
		log = Log()
		for row in dataset:
			if row[0] == cn:  #If the country name has not changed, continue to accumulate values
				x.append(row[2])
				y.append(row[3])
			else:
				plot_data.append([cn, cc, x, y])  #If the country name is new, save all the accumulated values in the new list
				cn = row[0]  #Remember the new country name and reset the lists
				cc = row[1]
				x = []
				y = []
				x.append(row[2])
				y.append(row[3])
		
		#Must append the data for the last country encountered 
		plot_data.append([cn, cc, x, y])

		return plot_data
			
	
	def do_pivot(self, array):
		pivoted = []
		
		for i in range(0, len(array)):
			if not isinstance(array[i][1], basestring) and not isinstance(array[i][2], basestring):
				change = 100 * ((array[i][2] - array[i][1])/array[i][1])
				pivoted.append([array[i][0], array[i][1], array[i][2], format(change, '.2f')])
			
		return pivoted

	def format_cells(self, array, digits):
		log = Log()
		fmt = '.' + str(digits) + 'f'
		for i in range(0, len(array)):
			for j in range(0, len(array[0])):
				if(not isinstance(array[i][j], basestring)):  #if this list element is not a string, format it as a number
					array[i][j] = format(array[i][j], fmt)
		
		#for i in range(0, len(array)):
		#	line = ', '.join(map(str, array[i]))
		#	log.writeline('debug', 'array', 'do_pivot', line)

		return array

class Index:
    def __init__(self, indicators = [], weights = []):
        self.indicators = indicators
        self.weights = weights
        self.output = [[]]
        self.conn = sqlite3.connect('/home/azureuser/python/wdi/database.sqlite')

    
    def validate(self):
        if len(self.indicators) != len(self.weights):
            return 'This index cannot be validated because the number of indicators and weights do not match'
        elif any([i == 0 for i in self.weights]):
            return 'This index cannot be validated because one or more of the assigned weights is 0'
        
    def build(self):
        self.index = dict(zip(self.indicators, self.weights))
        return self.index
    
    def generate_array(self, comparison, region = None):
        self.region = region
        sql = 'SELECT I.CountryName, I.IndicatorName, I.Year, I.Value, I.Indicatorcode  \n'
        sql += 'FROM INDICATORS IT JOIN X_COUNTRY C \n' 
        sql += 'ON I.CountryCode = C.Country_Code \n'
        sql += 'WHERE REGION_NAME != \'\' \n'
        if region is not None:
            sql += 'AND REGION_NAME = \''+region+'\'\n'
        sql += 'AND INDICATORCODE in \n( \n'
        for i in range(len(self.indicators)):
            sql += '\'' + indicators[i] + '\' \n ,'
        sql += '\'' + comparison + '\'\n)'
        
        #print (sql)

        
        #Run SQL Query
        Indicators_Raw = pd.read_sql(sql,self.conn)
        
        #Create Indicator Dictionary
        Unique_Indicators = list(set(Indicators_Raw['IndicatorCode'] + '-----' + Indicators_Raw['IndicatorName']))
        self.Indicator_dict = dict(zip([x[0:x.index('-----')] for x in Unique_Indicators], [x[x.index('-----')+5:] for x in Unique_Indicators]))
        
        #Format dataframe into tabular form
        Indicators_Raw.drop('IndicatorCode', axis = 1, inplace = True)
        Indicators_df = Indicators_Raw.set_index(['Year','CountryName', 'IndicatorName']).unstack('IndicatorName')
        Indicators_df.reset_index(level =  ['Year', 'CountryName'], inplace = True)
        Indicators_df.columns = [' '.join(col).strip() for col in Indicators_df.columns.values]
        Indicators_df.columns = [col.strip('Value ') if col not in ('Year', 'CountryName') else col for col in Indicators_df.columns]
 
        #Drop rows with at least one unknown indicator value
        Indicators_df.dropna(inplace = True)
        
        #Create Index Column
        Indicators_df['Index'] = 1
        
        
        #Create Index Column
        self.build()
        for i in indicators:
            Indicators_df['Index'] = (Indicators_df['Index']) * (Indicators_df[self.Indicator_dict[i]] * self.index[i]) 
        Indicators_df['Index'] = (Indicators_df['Index'])**(1/len(indicators))
        
        #Create output array
        count = 0
        for Year, CountryName, Index, Comparison in zip(Indicators_df['Year'], Indicators_df['CountryName'],
                                                       Indicators_df['Index'], Indicators_df[self.Indicator_dict[comparison]]):
            self.output[count].append(Year)
            self.output[count].append(CountryName)
            self.output[count].append(float('%s' % float('%.4g' % Index)))
            self.output[count].append(float('%s' % float('%.4g' % Comparison)))
            self.output.append([])
            count = count + 1
        
    def generate_dataframe(self, comparison, region = None, start_year = 1960, end_year = 2015):
		self.region = region
		sql = 'SELECT I.CountryName, I.IndicatorName, I.Year, I.Value, I.Indicatorcode  \n'
		sql += 'FROM INDICATORS I JOIN X_COUNTRY C \n' 
		sql += 'ON I.CountryCode = C.Country_Code \n'
		sql += 'WHERE REGION_NAME != \'\' \n'
		if region is not None:
			sql += 'AND REGION_NAME = \''+region+'\'\n'
		sql += 'AND INDICATORCODE in \n( \n'
		for i in range(len(self.indicators)):
			sql += '\'' + self.indicators[i] + '\' \n ,'
		sql += '\'' + comparison + '\'\n)'
		sql += 'AND YEAR BETWEEN ' + str(start_year) + ' AND ' + str(end_year) + '\n' 
		
		log = Log()
		log.writeline('debug', 'sql', 'indicators_vs_index', sql)
        
        #print (sql)

        
        #Run SQL Query
		self.df = pd.read_sql(sql,self.conn)
        
        #Create Indicator Dictionary
		Unique_Indicators = list(set(self.df['IndicatorCode'] + '-----' + self.df['IndicatorName']))
		
		self.Indicator_dict = dict(zip([x[0:x.index('-----')] for x in Unique_Indicators], [x[x.index('-----')+5:] for x in Unique_Indicators]))

        #Format dataframe into tabular form
		self.df.drop('IndicatorCode', axis = 1, inplace = True)
		self.df = self.df.set_index(['Year','CountryName', 'IndicatorName']).unstack('IndicatorName')
		self.df.reset_index(level =  ['Year', 'CountryName'], inplace = True)
		self.df.columns = [' '.join(col).strip() for col in self.df.columns.values]
		self.df.columns = [col.strip('Value ') if col not in ('Year', 'CountryName') else col for col in self.df.columns]
 
        #Drop rows with at least one unknown indicator value
		self.df.dropna(inplace = True)
        
        #Create Index Column
		self.df['Index'] = 1

		#Calculate Index Column
		self.build()
		#log.writeline('debug', 'indicators', 'indicators_vs_index', self.indicators)
		#log.writeline('debug', 'self.indicator_dict[i]', 'indicators_vs_index', self.Indicator_dict)
		for i in self.indicators:
			self.df['Index'] = (self.df['Index']) * (self.df[self.Indicator_dict[i]] * self.index[i]) 
       # self.df['Index'] = (self.df['Index'])**(1/len(indicators))
        
        #Drop columns used to create index
		[self.df.drop(self.Indicator_dict[x], axis = 1, inplace = True) for x in self.Indicator_dict if x != comparison]
        
        #Reduce to 4 significant digits	
       # self.df['Index'] =  self.df['Index'].map(lambda x: float('%s' % float('%.4g' % x)))
		self.df[self.Indicator_dict[comparison]] = self.df[self.Indicator_dict[comparison]].map(lambda x: float('%s' % float('%.4g' % x)))
		

#General logging class for this application
class Log:
	'''
	Description:
		Writes data to the application log. 
		
	Args: 
		entry_type:  'info', 'debug', 'error', 'warning'.
		label: The label associated with the data, typically the name of the variable being dumped.
		source: The method that was the source of the data, typically __method__ is used in the call.
		data: the data that is being dumped.  Lists are output in JSONP format for readability.
		
	Returns: 
		True if the write was successful.
		
	Todo: Need try/catch block for unexpected issues such as file access permission violations.
	'''

	def truncate(self):
		if os.path.isfile(LOG_PATH):
			os.remove(LOG_PATH)

	def writeline(self, entry_type, label, source, data):
		dt = datetime.now()
		dt_formatted = dt.strftime('%Y/%m/%d %H:%M:%S')

		f = open(LOG_PATH, 'a')
		
		if not isinstance(data, list) and not isinstance(data, dict):
			f.write(entry_type + "\t" + label + "\t" + source  + "\t" + data + "\n")
		else:
			f.write(entry_type + "\t" + label + "\t" + source  + "\n")
			json.dump(data, f, sort_keys = True, indent = 4)
			f.write("\n")

		f.close()
		
		return True

def purge_temp_files(N):
	'''
	Purge all files in the temp folder that are more than N days old.
	TEMP_PATH is defined in constants.py
	'''
	now = time.time()
	for x in os.listdir(TEMP_PATH):
		f = os.path.join(TEMP_PATH, x)
		if os.stat(f).st_mtime < now - N * 86400:
			if os.path.isfile(f):
				os.remove(f)

def get_element_index(element, input_list):
	'''Returns the index of the list element having the given value'''
	try:
		index = input_list.index(element)
		return index

	except ValueError:  #if value not found in list
		return None


def is_num(x):
	isnum = True
	try: 
		x + 1
	except TypeError: 
		isnum = False

	return isnum

