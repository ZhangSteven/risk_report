# coding=utf-8
#
# Asset allocation logic for SFC
# 
from risk_report.lqa import getBlpIdnType, getGenevaIdnType
from toolz.functoolz import compose
from functools import partial
from itertools import filterfalse
import logging
logger = logging.getLogger(__name__)



def positionsByCountry(blpData, country, positions):
	"""
	[Dictionary] blpData, [String] country, [Iterator] positions
		=> [Iterabor] positions (from that country)
	"""
	countryNotApplicable = lambda p: \
		True if getAssetType(blpData, p)[0].lower() in \
			['cash', 'foreign exchange derivatives'] else False


	def assignCountryToPosition(blpData, p):
		logger.debug('assignCountryToPosition(): {0}'.getIdnType(p))
		return country(blpData, p)


	return compose(
		partial(map, lambda t: t[1])
	  , partial(filter, lambda t: t[0] == country)
	  , partial(map, partial(assignCountryToPosition, blpData))
	  , partial(filterfalse, countryNotApplicable)
	)(positions)



isPrivateSecurity = lambda position: \
	False if isGenevaPosition(position) else position['Name'].startswith('.') 



isCash = lambda position: \
	position['SortKey'] == 'Cash and Equivalents' if isGenevaPosition(position) \
	else position['Asset Type'] == 'Cash'



isMoneyMarket = lambda position: \
	position['SortKey'] == 'Fixed Deposit' if isGenevaPosition(position) \
	else position['Asset Type'] == 'Money Market'



isRepo = lambda position: \
	False if isGenevaPosition(position) \
	else position['Asset Type'] == 'Repo Liability'



isFxForward = lambda position: \
	position['SortKey'] == 'FX Forward' if isGenevaPosition(position) \
	else position['Asset Type'] == 'Foreign Exchange Forward'



isFund = lambda position: \
	position['SortKey'] in ['Open-End Fund', 'Exchange Trade Fund', 'Real Estate Investment Trust'] \
	if isGenevaPosition(position) else position['Industry Sector'] == 'Funds'



def getAssetType(blpData, position):
	"""
	[Dictionary] position (a Geneva or Blp position)
		=> [Tuple] asset type

	The asset type is a tuple containing the category and sub category, like
	('Cash', ), ('Fixed Income', 'Corporate') or ('Equity', 'Listed')

	The logic is:

	If it's cash on hand, payables and receivables, money market instrucments 
	(say fixed deposit), asset class = "Cash Equivalents"


	"""
	logger.debug('getAssetType(): {0}'.format(getIdnType(position)))

	getFundType = lambda position: \
		getGenevaFundType(position) if isGenevaPosition(position) else \
		getBlpFundType(position)


	# NOTE: Geneva does not book repo yet
	isRepo = lambda position: \
		False if isGenevaPosition(position) else position['Asset Type'].startswith('Repo')

	# FIXME: add implementation
	getRepoAssetType = lambda position: \
		lognRaise('getRepoAssetType(): not supported')

	
	return \
	getPrivateSecurityAssetType(position) if isPrivateSecurity(position) else \
	('Cash', ) if isCash(position) else \
	('Foreign Exchange Derivatives', ) if isFxForward(position) else \
	('Fixed Income', 'Cash Equivalents') if isMoneyMarket(position) else \
	getRepoAssetType(position) if isRepo(position) else \
	getFundType(position) if isFund(position) else \
	getOtherAssetType(blpData, position)
# End of getAssetType()



def getOtherAssetType(blpData, position):
	"""
	For Fixed Income or Equity asset type, use Bloomberg "MARKET_SECTOR_DES" 
	field to lookup:

	If the field is "Equity", then asset class = "Equity", sub category
	"Listed Equity" if Bloomberg field "EXCH_MARKET_STATUS" = "ACTV", else
	sub category "Unlisted Equity".

	If the field is "Comdty", then asset type = ('Commodity', 'Derivatives')

	Otherwise its Bloomberg field "CAPITAL_CONTINGENT_SECURITY" 
	= "Y", then asset class is:

	('Fixed Income', 'Additional Tier 1, Contingent Convertibles')

	Else use the below mapping

	Corp -> Fixed Income, sub catetory "Corporate Bond"
	Govt -> Fixed Income, sub catetory "Government Bond"
	"""
	isEquityType = lambda blpData, position: \
		blpData[getIdnType(position)[0]]['MARKET_SECTOR_DES'] == 'Equity'


	isCommodityType = lambda blpData, position: \
		blpData[getIdnType(position)[0]]['MARKET_SECTOR_DES'] == 'Comdty'


	isFIType = lambda blpData, position: \
		blpData[getIdnType(position)[0]]['MARKET_SECTOR_DES'] in ['Corp', 'Govt']


	isCapitalContingentSecurity = lambda blpData, position: \
		blpData[getIdnType(position)[0]]['CAPITAL_CONTINGENT_SECURITY'] == 'Y'


	# FIXME: this function is not complete, as index futures are not included
	getEquityAssetType = lambda blpData, position: \
		('Equity', 'Listed Equities') if blpData[getIdnType(position)[0]]['EXCH_MARKET_STATUS'] == 'ACTV' \
		else ('Equity', 'Unlisted Equities')


	# FIXME: this function is not complete, as physical commodity is not included
	getCommodityAssetType = lambda blpData, position: \
		('Commodity', 'Derivatives')


	getFIAssetType = lambda blpData, position: \
		('Fixed Income', 'Additional Tier 1, Contingent Convertibles') \
		if isCapitalContingentSecurity(blpData, position) else \
		('Fixed Income', 'Corporate') if blpData[getIdnType(position)[0]]['MARKET_SECTOR_DES'] == 'Corp' else \
		('Fixed Income', 'Government') if blpData[getIdnType(position)[0]]['MARKET_SECTOR_DES'] == 'Govt' else \
		lognRaise('getFIAssetType(): unsupported FI type {0}'.format(getIdnType(position)))


	return \
	getEquityAssetType(blpData, position) if isEquityType(blpData, position) else \
	getCommodityAssetType(blpData, position) if isCommodityType(blpData, position) else \
	getFIAssetType(blpData, position) if isFIType(blpData, position) else \
	lognRaise('getOtherAssetType(): invalid asset type: {0}'.format(getIdnType(position)))



def getBlpFundType(position):
	"""
	[Dictionary] position => [Tuple] Asset Class

	If position is a fund type in Bloomberg, output its exact fund type
	"""
	# FIXME: Add implementation
	lognRaise('getBlpFundType(): {0}'.format(getIdnType(position)))



def getGenevaFundType(position):
	"""
	[Dictionary] position => [Tuple] Asset Class

	If position is a fund type in Geneva, output its exact fund type
	"""
	def getGenevaOpenFundType(position):
		# FIXME: Add mapping for open end fund here, what's the fund type
		# for DIF?
		# fMap = {'CLFLDIF HK': ('Fund', 'Other Funds')}
		fMap = {}
		try:
			return fMap[position['InvestID']]
		except KeyError:
			lognRaise('getGenevaOpenFundType(): invalid position: {0}'.format(getIdnType(position)))


	return \
	('Fund', 'Exchange Traded Funds') if position['SortKey'] == 'Exchange Trade Fund' else \
	('Fund', 'Real Estate Investment Trusts') if position['SortKey'] == 'Real Estate Investment Trust' else \
	getGenevaOpenFundType(position) if position['SortKey'] == 'Open-End Fund' else \
	lognRaise('getGenevaFundType(): invalid position: {0}'.format(getIdnType(position)))



def getPrivateSecurityAssetType(position):
	"""
	[Dictionary] position => [Tuple] Asset Type

	Handle special cases

	# FIXME: add implementation
	"""
	logger.debug('getPrivateSecurityAssetType()')
	raise ValueError



isGenevaPosition = lambda p: p['Remarks1'].lower().startswith('geneva')



"""
	[Dictionary] position (a Geneva or Blp position)
		=> [Tuple] (id, idType)
"""
getIdnType = lambda position: \
	getGenevaIdnType(position) if isGenevaPosition(position) else \
	getBlpIdnType(position)



def getCountry(blpData, position):
	"""
	[Dictionary] blpInfo => [String] country

	1) For equity asset class, use "CNTRY_ISSUE_ISO" field value
	2) For fixed income asset class, use "CNTRY_OF_RISK" field value

	# FIXME: For other asset classes, the logic is not determined yet,
	therefore will throw an exception.
	"""
	logger.debug('getCountry(): {0}'.format(getIdnType(position)))

	if getAssetType(position)[0] in ['Equity', 'Fixed Income']:
		blpInfo = blpData[getIdnType(position)[0]]

		return \
		blpInfo['CNTRY_ISSUE_ISO'] if blpInfo['MARKET_SECTOR_DES'] == 'Equity' else \
		blpInfo['CNTRY_OF_RISK']

	else:
		logger.error('getCountry(): unsupported asset type {0}'.format(getAssetType(position)))
		raise ValueError



def isFinancial(investment):
	"""
	The logic:

	1) If asset class is cash equivalent, then throw exception because it does
		not make sense.
	2) Otherwise use Bloomberg "INDUSTRY_SECTOR", if return result is "Financial",
		then YES, othereise NO.

	What about derivatives? Cannot see the logic in Excel
	"""
	return 0




def lognContinue(msg, x):
	logger.debug(msg)
	return x



def lognRaise(msg):
	logger.error(msg)
	raise ValueError




if __name__ == '__main__':
	import logging.config
	logging.config.fileConfig('logging.config', disable_existing_loggers=False)

	import argparse
	parser = argparse.ArgumentParser(description='Process Bloomberg and Geneva holding File ' \
										+ 'and Geneva holding file (DIF only), then produce '
										+ 'LQA request files.')
	parser.add_argument( 'blp_file', metavar='blp_file', type=str
					   , help='Bloomberg holding file')
	parser.add_argument( 'geneva_file', metavar='geneva_file', type=str
				   , help='Geneva holding file')
	args = parser.parse_args()

	buildLqaRequestFromFiles(args.blp_file, args.geneva_file)
