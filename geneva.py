# coding=utf-8
#
# Read DIF position from Geneva tax lot appraisal report
#

from xlrd import open_workbook
from clamc_datafeed.feeder import getPositions
from utils.excel import fileToLines
from utils.utility import mergeDict
from toolz.functoolz import compose
from functools import partial
import logging
logger = logging.getLogger(__name__)



""" [String] dt (yyyy-mm-dd) => [String] dt (yyyymmdd) """
changeDateFormat = lambda dt: ''.join(dt.split('-'))



"""
	[Iterator] lines => ( [String] date (yyyymmdd)
						, [Iterator] positions
						)

	lines: an iterator over lines (each line being a List of values) of an Excel
	spread sheet from Geneva investment positions report.
	
	Each position are enriched by the below fields:

	[String] Remarks1
"""
getGenevaInvestmentPositions = compose(
	lambda t: ( changeDateFormat(t[0]['PeriodEndDate'])
			  , map( lambda p: \
			  			mergeDict(p, {'Remarks1': 'Geneva investment positions report'})
			  	   , t[1]
			  	   )
			  )
  , getPositions
)



"""
	[String] file (Geneva investment positions report, Excel format)
		=> ([String] date (yyyymmdd), [Iterator] positions)
"""
readGenevaInvestmentPositionFile = compose(
	getGenevaInvestmentPositions
  , fileToLines
  , lambda file: lognContinue('readGenevaInvestmentPositionFile(): {0}'.format(file), file)
)



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



""" [Dictionary] position => [Bool] is it a Geneva position """
isGenevaPosition = lambda position: \
	position['Remarks1'].lower().startswith('geneva')



""" [Dictionary] position => [Bool] is it a Geneva fund position """
isGenevaFund = lambda position: \
	position['SortKey'] in ['Open-End Fund', 'Exchange Trade Fund', 'Real Estate Investment Trust']



""" [Dictionary] position => [Bool] is it a Geneva FX Forward position """
isGenevaFxForward = lambda position: \
	position['SortKey'] == 'FX Forward'



""" [Dictionary] position => [Bool] is it a Geneva Repo position """
isGenevaRepo = lambda position: False	# REPO not implemented in Geneva yet



""" [Dictionary] position => [Bool] is it a Geneva Money Market position """
isGenevaMoneyMarket = lambda position: \
	position['SortKey'] == 'Fixed Deposit'



""" [Dictionary] position => [Bool] is it a cash or cash equivalent Geneva position """
isGenevaCash = lambda position: \
	position['SortKey'] == 'Cash and Equivalents'



""" 
	[Dictionary] position => [Bool] is it a private security 
# FIXME: to be implemented
"""
isGenevaPrivateSecurity = lambda position: False



""" [Dictionary] position => [Float] market value of this position """
getGenevaMarketValue = lambda position: \
	position['AccruedInterest'] + position['MarketValueBook']



""" [Dictionary] position => [String] date (yyyy-mm-dd) """
getGenevaPositionDate = lambda position: \
	changeDateFormat(position['PeriodEndDate'])



""" [Dictionary] position => [String] book currency of this position """
getGenevaBookCurrency = lambda position: \
	position['BookCurrency']



""" [Dictionary] position => [String] portfolio id of this position """
getGenevaPortfolioId = lambda position: \
	position['Portfolio']



def getGenevaFundType(position):
	"""
	[Dictionary] position => [Tuple] Asset Class
	"""

	# For open ended fund types, we use special case handling here.
	fMap = {  }


	return \
	('Fund', 'Exchange Traded Funds') if position['SortKey'] == 'Exchange Trade Fund' else \
	('Fund', 'Real Estate Investment Trusts') if position['SortKey'] == 'Real Estate Investment Trust' else \
	fMap[position['InvestID']] if position['InvestID'] in fMap else \
	lognRaise('getGenevaFundType(): not supported: {0}'.format(getIdnType(position)))



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