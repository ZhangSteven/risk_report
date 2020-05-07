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



def readGenevaFile(file):
	"""
	[String] file => ( [String] date (yyyy-mm-dd)
					 , [List] positions)

	Read a Geneva tax lot appraisal with accrued interest report, get the equity
	and bond positions. Each position should have the below fields:

	'Name': name of the security
	'Position': quantity
	'ISIN': isin code if this is a bond (equity position may not have)
	'TICKER': Ticker code if this is an equity (bond may not have)
	'Asset Type': either 'Equity', or 'xxx Bond'
	'Currency': currency
	'Date': date of the report's PeriodEndDate
	"""
	processTaxlotInfo = compose(
		detectDuplicateISIN
	  , list
	  , partial(map, updateId)
	  , partial(map, addNewFields)
	  , partial(filterfalse, lambda p: p['Quantity'] == 0)
	  , partial(filterfalse, lambda p: p['ThenByDescription'] == 'Cash and Equivalents')
	  , lambda d: d.values()
	)


	return \
	compose(
		lambda t: ( t[0]['PeriodEndDate']
				  , processTaxlotInfo(t[1])
				  )
	  , getTaxlotInfo
	)(file)
# End of readGenevaFile()



removeHTMfromInvestID = lambda investId: \
	investId[0:12] if len(investId) > 15 and investId[-4:] == ' HTM' else investId



updateId = lambda p: \
	mergeDict(p, {'Id': p['InvestID'] + ' Equity', 'IdType': 'TICKER'}) \
	if p['Asset Type'] == 'Equity' else \
  	mergeDict(p, {'Id': removeHTMfromInvestID(p['InvestID']), 'IdType': 'ISIN'}) 



addNewFields = lambda p: mergeDict(
	p
  , { 'Name': p['TaxLotDescription']
	, 'Position': p['Quantity']
	, 'Asset Type': getSecurityType(p['ThenByDescription'])
	, 'Date': p['PeriodEndDate']
	}
)



"""
	[List] positions => [List] positions

	Raise error if there is duplicate ISIN codes among the positions. This will
	occur if a bond is in both AFS and HTM positions, these two positions will have
	different invest id, but after removing ' HTM' from invest id, they will have
	duplicate ISIN codes and thus need to be consolidated.
"""
detectDuplicateISIN = lambda positions: compose(
	lambda L: lognRaise('Duplicate ISIN detected') if len(set(L)) < len(L) else positions
  , list
  , partial(map, lambda p: p['ISIN'])
  , partial(filter, lambda p: 'ISIN' in p)
)(positions)



"""
	[String] securityType => [String] type
	
	Map the security's type from Geneva report to the new format

	If there is a type that is not recognized, then it will raise an error.
"""
getSecurityType = lambda securityType: \
	'Equity' if securityType in [ 'Common Stock', 'Real Estate Investment Trust'
								, 'Stapled Security', 'Exchange Trade Fund'] else \
	securityType if securityType.split()[-1] == 'Bond' else \
	lognRaise('getSecurityType(): unsupported type: {0}'.format(securityType))




if __name__ == '__main__':
	import logging.config
	logging.config.fileConfig('logging.config', disable_existing_loggers=False)

	inputFile = '19437 tax lot 20200429.xlsx'
	metaData, positions = readGenevaFile(inputFile)
	for p in positions:
		print(p)