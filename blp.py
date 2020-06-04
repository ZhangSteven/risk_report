# coding=utf-8
#
# Read the Bloomberg input file (Excel) and output positions.
# 

import logging
logger = logging.getLogger(__name__)



""" [Dictionary] position => [Bool] is this a Bloomberg position """
isBlpPosition = lambda position: \
	position['Remarks1'].startswith('Bloomberg')



""" [Dictionary] position => [Bool] is this a Bloomberg fund position """
isBlpFund = lambda position: \
	position['Industry Sector'] == 'Funds'



""" [Dictionary] position => [Bool] is this a Bloomberg FX Forward position """
isBlpFxForward = lambda position: \
	position['Asset Type'] == 'Foreign Exchange Forward'



""" [Dictionary] position => [Bool] is this a Bloomberg Cash position """
isBlpCash = lambda position: \
	position['Asset Type'] == 'Cash'



""" [Dictionary] position => [Bool] is this a Bloomberg Money Market position """
isBlpMoneyMarket = lambda position: \
	position['Asset Type'] == 'Money Market'



""" [Dictionary] position => [Bool] is this a Bloomberg Repo position """
isBlpRepo = lambda position: \
	position['Asset Type'].startswith('Repo')



""" [Dictionary] position => [Bool] is this a Bloomberg private security position """
isBlpPrivateSecurity = lambda position: \
	position['Name'].startswith('.') 



"""
	[Dictionary] position => [Float] market value of the position

# FIXME: add implementation
"""
getBlpMarketValue = lambda position: \
	lognRaise('getBlpMarketValue(): not implemented')



""" [Dictionary] position => [String] date of the position (yyyy-mm-dd) """
getBlpPositionDate = lambda position: position['AsOfDate']



""" [Dictionary] position => [String] portfolio id of the position """
getBlpPortfolioId = lambda position: position['Account Code']



""" [Dictionary] position => [String] Book currency of the position """
getBlpBookCurrency = lambda position: \
	getBookCurrency(position['Account Code'])



"""
	[String] account code => [String] Book currency of the account

# FIXME: add implementation
"""
getBookCurrency = lambda accountCode: \
	lognRaise('getBookCurrency(): not implemented')



def getBlpFundType(position):
	"""
	[Dictionary] position => [Tuple] Asset Class

	If position is a fund type in Bloomberg, output its exact fund type
	"""
	# FIXME: Add implementation
	lognRaise('getBlpFundType(): {0}'.format(getIdnType(position)))



# def saveBlpPositionToDB(file):
# 	"""
# 	[String] file => [Int] 0 (if successful or raise exception otherwise)

# 	Side effect: save positions to a database

# 	Read Blp Positions from a file and save them into a database
# 	"""

# 	"""
# 		[Dictionary] position => [Dictionary] position

# 		Enrich the position before saving the document to database.

# 		1) Shall we add a 'AsOfDate' field, or keep using the 'PeriodEndDate'?

# 		If we add an 'AsOfDate' field for all database documents for which
# 		this field makes sense, then in the future it can make our query more
# 		standardized, since we are going to have lots of queries that require
# 		the as of date for something.

# 		To do this, we need to use a consistent format for this AsOfDate, 
# 		maybe the 'date' type of MongoDB?

# 		2) Shall we add a '_id' field to prevent saving identical positions 
# 		into the MongoDB?

# 		Say we run this function twice on the same file. Then we will have two 
# 		identical sets of records except their "_id" fields. Maybe we should 
# 		add an '_id' field to avoid this.
		
# 		Idealy, there is be no more than one document for a position if:

# 		1) It's a position record from Geneva system;
# 		2) For any particular security;
# 		3) For any particular portfolio;
# 		4) For any particular date;
	
# 		So:

# 		_id = 'blp' + portfolio id + date + name?

# 		The purpose is make the id unique as long as the above (1-4) are satisfied.
# 	"""
# 	addNewFields = lambda date, p: \
# 		mergeDict(p, {'DataSource': 'aim', 'RecordType': 'position'})


# 	return 0
# End of saveBlpPositionToDB()



def lognContinue(msg, x):
	logger.debug(msg)
	return x


def lognRaise(msg):
	logger.error(msg)
	raise ValueError