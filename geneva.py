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



""" [Dictionary] position => [Float] quantity of this position """
getGenevaQuantity = lambda position: \
	position['Quantity']




def getGenevaIdnType(position):
	"""
	[Dictionary] position
		=> ( [String] id,
		   , [String] id type
		   )

	NOTE: this function should never throw an exception. So we make it always
	return something even if we cannot determine what should be the asset type.
	"""
	ISINfromInvestID = lambda investId: \
		lognContinue( 'getGenevaIdnType(): ISINfromInvestID: special case: {0}'.format(investId)
					, investId) \
		if len(investId) < 12 else investId[0:12]


	isEquityType = lambda assetType: \
		assetType in [ 'Common Stock', 'Real Estate Investment Trust'
					 , 'Stapled Security', 'Exchange Trade Fund']

	isBondType = lambda assetType: assetType.split()[-1] == 'Bond'

	investId, assetType = position['InvestID'], position['SortKey']
	

	return \
	(investId + ' Equity', 'TICKER') if isEquityType(assetType) else \
	(ISINfromInvestID(investId), 'ISIN') if isBondType(assetType) else \
	lognContinue( 'getGenevaIdnType(): special case: {0}'.format(position['InvestID'])
				, (position['InvestID'], position['SortKey']))



"""
	[Dictionary] position => [Tuple] Asset Class
"""
getGenevaAssetType = lambda position: \
	position['SortKey']



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