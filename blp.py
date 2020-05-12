# coding=utf-8
#
# Read the Bloomberg input file (Excel) and output positions.
# 

from itertools import takewhile, dropwhile, filterfalse
from functools import partial
from toolz.functoolz import compose
from utils.iter import pop, firstOf
from utils.excel import worksheetToLines
from utils.utility import mergeDict
from risk_report.utility import getCurrentDirectory
from xlrd import open_workbook
from datetime import datetime
from os.path import join
import logging, re
logger = logging.getLogger(__name__)



def lognContinue(msg, x):
	logger.debug(msg)
	return x


def lognRaise(msg):
	logger.error(msg)
	raise ValueError



# def getBlpLqaPositions(positions):
# 	"""
# 	[Iterable] positions => ( [Iterable] CLO positions
# 					 	    , [Iterable] nonCLO positions
# 					 	    )

# 	Read Bloomberg raw positions, then do the following: 

# 	1) take out those not suitable to do liquidity test (cash, FX forward, etc.);
# 	2) take out DIF fund positions, since they will come from Geneva;
# 	2) split into clo and nonCLO positions.

# 	Return (CLO positions, nonCLO positions)
# 	"""
# 	removeUnwantedPositions = compose(
# 		partial(filterfalse, lambda p: p['Account Code'][:5] == '19437')

# 	  , partial( filterfalse
# 	  		   , lambda p: p['Asset Type'] in [ 'Cash', 'Foreign Exchange Forward'
# 	  		   								  , 'Repo Liability', 'Money Market'] \
# 					or p['Name'] in ['.FSFUND HK', 'CLFLDIF HK']	# open ended funds
# 			   )
	  
# 	  , partial(filterfalse, lambda p: p['Position'] == '' or p['Position'] <= 0)
# 	)


# 	updatePositionId = lambda p: \
# 		mergeDict(p, {'Id': p['Name'] + ' Equity', 'IdType': 'TICKER'}) \
# 		if p['Asset Type'] == 'Equity' else \
# 		mergeDict(p, {'Id': p['ISIN'], 'IdType': 'ISIN'})


# 	isCLOPortfolio = lambda p: p['Account Code'] in \
# 						['12229', '12734', '12366', '12630', '12549', '12550', '13007']


# 	"""
# 	[Iterable] positions => ( [Iterable] CLO positions
# 							, [Iterable] non CLO positions
# 							)

# 	Split the positions into All, CLO and non-CLO group
# 	"""
# 	splitCLO = lambda positions: \
# 		reduce( lambda acc, el: ( chain(acc[0], [el])
# 								, acc[1]
# 								) if isCLOPortfolio(el) else \
								
# 								( acc[0]
# 								, chain(acc[1], [el])
# 								)
# 	  		  , positions
# 	  		  , ([], [])
# 	  		  )


# 	return \
# 	compose(
# 		splitCLO
# 	  , partial(map, updatePositionId)
# 	  , removeUnwantedPositions		
# 	  , lambda positions: lognContinue('getBlpLqaPositions(): start', positions)
# 	)(positions)



def readBlpFile(file):
	"""
	[String] file => ( [String] date (yyyy-mm-dd)
					 , [Iterable] positions (with 'date' field updated)
					 )
	"""
	# [Iterable] lines => [List] line that contains the date
	findDateLine = partial(
		firstOf
	  , lambda line: len(line) > 1 and line[1].startswith('Risk-Mon Steven')
	)


	# [String] The string containing date => [String] date (yyyymmdd)
	# it looks like: Risk Report LQA Master as of 20200429
	getDateFromString = lambda s: s.split()[-1]


	getDateFromLines = compose(
		getDateFromString
	  , lambda line: lognRaise('Failed to find date line') if line == None else line[1]
	  , findDateLine
	)


	return \
	compose(
		lambda t: (t[0], filterfalse(lambda p: p['Account Code'] == '', t[1]))
	  , lambda lines: (getDateFromLines(lines), getPositions(lines))
	  , fileToLines
	  , lambda file: lognContinue('readBlpFile(): {0}'.format(file), file)
	)(file)



def saveBlpPositionToDB(file):
	"""
	[String] file => [Int] 0 (if successful or raise exception otherwise)

	Side effect: save positions to a database

	Read Blp Positions from a file and save them into a database
	"""

	"""
		[Dictionary] position => [Dictionary] position

		Enrich the position before saving the document to database.

		1) Shall we add a 'AsOfDate' field, or keep using the 'PeriodEndDate'?

		If we add an 'AsOfDate' field for all database documents for which
		this field makes sense, then in the future it can make our query more
		standardized, since we are going to have lots of queries that require
		the as of date for something.

		To do this, we need to use a consistent format for this AsOfDate, 
		maybe the 'date' type of MongoDB?

		2) Shall we add a '_id' field to prevent saving identical positions 
		into the MongoDB?

		Say we run this function twice on the same file. Then we will have two 
		identical sets of records except their "_id" fields. Maybe we should 
		add an '_id' field to avoid this.
		
		Idealy, there is be no more than one document for a position if:

		1) It's a position record from Geneva system;
		2) For any particular security;
		3) For any particular portfolio;
		4) For any particular date;
	
		So:

		_id = 'blp' + portfolio id + date + name?

		The purpose is make the id unique as long as the above (1-4) are satisfied.
	"""
	addNewFields = lambda date, p: \
		mergeDict(p, {'DataSource': 'aim', 'RecordType': 'position'})


	return 0
# End of saveBlpPositionToDB()



def fileToLines(file):
	"""
	[String] file => [Iterable] lines

	Read an Excel file, convert its first sheet into lines, each line is
	a list of the columns in the row.
	"""
	return worksheetToLines(open_workbook(file).sheet_by_index(0))



"""
	[Iterable] lines => [Iterable] positions

	Read all positions from the Bloomberg Excel file.
"""
getPositions = compose(
	  lambda t: map(lambda line: dict(zip(t[0], line)), t[1])
	, lambda lines: (pop(lines), lines)
	, lambda lines: dropwhile(lambda line: line[0] != 'Name', lines)
)
