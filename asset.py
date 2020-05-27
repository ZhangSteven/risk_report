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
		True if getAssetType(blpData, p)[0] == 'Cash' else False


	def assignCountryToPosition(blpData, p):
		logger.debug('assignCountryToPosition(): {0}'.getIdnType(p))
		return country(blpData, p)


	return compose(
		partial(map, lambda t: t[1])
	  , partial(filter, lambda t: t[0] == country)
	  , partial(map, partial(assignCountryToPosition, blpData))
	  , partial(filterfalse, countryNotApplicable)
	)(positions)



def getAssetType(blpData, position):
	"""
	[Dictionary] position (a Geneva or Blp position)
		=> [Tuple] asset type

	The asset type is a tuple containing the category and sub category, like
	('Cash', ), ('Fixed Income', 'Corporate') or ('Equity', 'Listed')

	The logic is:

	If it's cash on hand, payables and receivables, money market instrucments 
	(say fixed deposit), asset class = "Cash Equivalents"

	If it's not cash, then use LQA "MARKET_SECTOR_DES" field to lookup:

	If LQA market sector = "Equity", then asset class = "Equity", sub category
	"Listed Equity" if Bloomberg field "EXCH_MARKET_STATUS" = "ACTV", else
	sub category "Unlisted Equity".

	If it's not equity and its Bloomberg field "CAPITAL_CONTINGENT_SECURITY" 
	= "Y", then asset class is "Additional Tier 1, Contingent Convertibles 
	and similar instrucments"

	Else use the below mapping

	Corp -> Fixed Income, sub catetory "Corporate Bond"
	Govt -> Fixed Income, sub catetory "Government Bond"
	Comdty -> Derivatives, sub category "Derivatives"
	"""
	isGenevaCash = lambda position: \
		position['SortKey'] == 'Cash and Equivalents'


	isBlpCash = lambda position: \
		position['Asset Type'] == 'Cash'


	isCash = lambda position: \
		isGenevaCash(position) if isGenevaPosition(position) else \
		isBlpCash(position)


	isMoneyMarket = 
	
	return ()



isGenevaPosition = lambda p: p['Remarks1'].lower().startswith('geneva')



def getIdnType(position):
	"""
	[Dictionary] position (a Geneva or Blp position)
		=> [Tuple] (id, idType)
	"""
	if isGenevaPosition(position):
		return getGenevaIdnType(position)
	else:
		return getBlpIdnType(position)



def country(blpData, position):
	"""
	[Dictionary] blpInfo => [String] country

	1) For equity asset class, use "CNTRY_ISSUE_ISO" field value
	2) For other asset class, use "CNTRY_OF_RISK" field value

	Note that country() does not apply to Cash.
	"""
	# FIXME: need handling when blp does not contain data for this position
	blpInfo = blpData[getIdnType(position)[0]]

	return \
	blpInfo['CNTRY_ISSUE_ISO'] if blpInfo['MARKET_SECTOR_DES'] = 'Equity' else \
	blpInfo['CNTRY_OF_RISK']



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
