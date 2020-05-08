# coding=utf-8
#
# Read DIF position from Geneva tax lot appraisal report
#

from xlrd import open_workbook
from clamc_datafeed.feeder import getTaxlotInfo
from itertools import filterfalse
from functools import partial
from toolz.functoolz import compose
from utils.utility import mergeDict
import logging
logger = logging.getLogger(__name__)



def lognRaise(msg):
	logger.error(msg)
	raise ValueError



def lognContinue(msg, x):
	logger.debug(msg)
	return x



def getGenevaLqaPositions(positions):
	"""
	[Iterable] positions => [Iterable] positions

	Read Geneva consolidated tax lot positions, then do the following: 

	1) take out those not suitable to do liquidity test (cash, FX forward, etc.);
	2) Add Id and IdType fields for LQA processing.
	3) Add 'Position' field (same as quantity) for LQA processing.

	Return the positions
	"""
	removeHTMfromInvestID = lambda investId: \
		investId[0:12] if len(investId) > 15 and investId[-4:] == ' HTM' else investId


	isEquityType = lambda securityType: \
		securityType in [ 'Common Stock', 'Real Estate Investment Trust'
								  , 'Stapled Security', 'Exchange Trade Fund']

	isBondType = lambda securityType: securityType.split()[-1] == 'Bond'


	addIdnType = lambda p: \
		mergeDict(p, {'Id': p['InvestID'] + ' Equity', 'IdType': 'TICKER'}) \
		if isEquityType(p['ThenByDescription']) else \
	  	mergeDict(p, {'Id': removeHTMfromInvestID(p['InvestID']), 'IdType': 'ISIN'}) \
	  	if isBondType(p['ThenByDescription']) else \
	  	lognRaise('addIdnType(): unsupported type: {0}'.format(p['ThenByDescription']))


	addPosition = lambda p: \
		mergeDict(p, {'Position': p['Quantity']})


	return compose(
		partial(map, addIdnType)
	  , partial(map, addPosition)
	  , partial(filterfalse, lambda p: p['Quantity'] == 0)
	  , partial(filterfalse, lambda p: p['ThenByDescription'] == 'Cash and Equivalents')
	  , lambda positions: lognContinue('getGenevaLqaPositions(): start', positions)
	)(positions)



def readGenevaFile(file):
	"""
	[String] file => ( [String] date (yyyy-mm-dd)
					 , [Iterable] positions)

	Read a Geneva tax lot appraisal with accrued interest report, get the
	raw consolidated positions, utilizing the getTaxlotInfo() function.

	'Name': name of the security
	'Position': quantity
	'ISIN': isin code if this is a bond (equity position may not have)
	'TICKER': Ticker code if this is an equity (bond may not have)
	'Asset Type': either 'Equity', or 'xxx Bond'
	'Currency': currency
	'Date': date of the report's PeriodEndDate
	"""
	addNewFields = lambda p: mergeDict(
		p
	  , {'DataSource': 'geneva', 'RecordType': 'position'}
	)


	# Convert yyyy-mm-dd to yyyymmdd
	convertDateFormat = lambda d: ''.join(d.split('-'))


	return \
	compose(
		lambda t: ( convertDateFormat(t[0]['PeriodEndDate'])
				  , map(addNewFields, t[1].values())
				  )
	  , getTaxlotInfo
	  , lambda file: lognContinue('readGenevaFile(): {0}'.format(file), file)
	)(file)
# End of readGenevaFile()
