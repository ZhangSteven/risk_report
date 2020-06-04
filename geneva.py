# coding=utf-8
#
# Functions related to Geneva positions are grouped here.
#


import logging
logger = logging.getLogger(__name__)



""" [String] dt (yyyy-mm-dd) => [String] dt (yyyymmdd) """
changeDateFormat = lambda dt: ''.join(dt.split('-'))



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