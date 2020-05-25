# coding=utf-8
#
# Read DIF position from Geneva tax lot appraisal report
#

from xlrd import open_workbook
from clamc_datafeed.feeder import getTaxlotInfo, getPositions, fileToLines
from toolz.functoolz import compose
from utils.utility import mergeDict
from functools import partial
import logging
logger = logging.getLogger(__name__)



"""
	[Iterator] lines => ( [String] date (yyyy-mm-dd)
						, [Iterator] positions
						)

	lines: an iterator over lines (each line being a List of values) of an Excel
	spread sheet from Geneva investment positions report.
	
	Each position contains the below fields:

	[String] Portfolio, [String] AsOfDate (yyyy-mm-dd), [String] BookCurrency,
	[String] Remarks1
"""
getGenevaInvestmentPositions = compose(
	lambda t: ( t[0]['PeriodEndDate']
			  , map( lambda p: \
			  			mergeDict( p
			  					 , { 'AsOfDate': p['PeriodEndDate']
			  					   , 'Remarks1': 'Geneva investment positions report'
			  					   }
			  					 )
			  	   , t[1])
			  )
  , getPositions
)



"""
	[String] file (Geneva investment positions report, Excel format)
		=> ([String] date (yyyy-mm-dd), [Iterator] positions)
"""
readGenevaInvestmentPositionFile = compose(
	getGenevaInvestmentPositions
  , fileToLines
  , lambda file: lognContinue('readGenevaInvestmentPositionFile(): {0}'.format(file), file)
)



def readGenevaFile(file):
	"""
	[String] file => ( [String] date (yyyy-mm-dd)
					 , [Iterable] positions
					 )

	Read a Geneva tax lot appraisal with accrued interest report, get the
	raw consolidated positions, utilizing the getTaxlotInfo() function.
	"""

	# Convert yyyy-mm-dd to yyyymmdd
	convertDateFormat = lambda d: ''.join(d.split('-'))


	return \
	compose(
		lambda t: ( convertDateFormat(t[0]['PeriodEndDate'])
				  , t[1].values()
				  )
	  , getTaxlotInfo
	  , lambda file: lognContinue('readGenevaFile(): {0}'.format(file), file)
	)(file)



def saveGenevaPositionToDB(file):
	"""
	[String] file => [Int] 0 (if successful or raise exception otherwise)

	Side effect: save positions to a database

	Read Geneva Positions from a file and save them into a database
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

		_id = 'geneva' + portfolio id + date + invest id?
	"""
	addNewFields = lambda p: mergeDict(
		p
	  , {'DataSource': 'geneva', 'RecordType': 'position'}
	)


	return 0
# End of saveGenevaPositionToDB()



"""
	These are like utility functions, but they have to be deployed to 
	each module, instead of being imported from one module. This is
	because the logger uses the module name in the logging message.
"""
def lognRaise(msg):
	logger.error(msg)
	raise ValueError


def lognContinue(msg, x):
	logger.debug(msg)
	return x