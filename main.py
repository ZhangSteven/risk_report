# coding=utf-8
#
# Read the Bloomberg input file (Excel) and Geneva input file, then produce
# master list files and LQA request files.
# 

from risk_report.utility import getCurrentDirectory
from risk_report.asset import isPrivateSecurity, isCash, isMoneyMarket \
							, isRepo, isFxForward, getIdnType, getAssetType
from risk_report.geneva import readGenevaInvestmentPositionFile
from clamc_datafeed.feeder import getRawPositions, fileToLines
from utils.utility import writeCsv
from toolz.functoolz import compose, juxt
from functools import partial
from itertools import filterfalse, chain
from os.path import join
import logging
logger = logging.getLogger(__name__)



"""
	[String] file => [Dictionary] data (ID -> [Dictioanry] blp information)
	
	Assume Blp data is stored in an Excel file
"""
loadBlpDataFromFile = compose(
	dict
  , partial(map, lambda p: (p['ID'], p))
  , getRawPositions
  , fileToLines
)



def writeIdnTypeToFile(file, positions):
	"""
	[String] output file, [Iterator] positions
		=> [Int] 0 if successful

	Side effect: write a csv file containing the id, idType for the positions
	"""
	noNeedId = lambda position: \
		any(juxt(isPrivateSecurity, isCash, isMoneyMarket, isRepo, isFxForward)(position))


	compose(
		lambda idnTypes: writeCsv(file, chain([('ID', 'ID_TYPE')], idnTypes))
	  , set
	  , partial(map, getIdnType)
	  , partial(filterfalse, noNeedId)
	)(positions)

	return 0



def createGenevaIdnTypeFile(inputFile):
	"""
	[String] inputFile (geneva investment positions report, Excel Format) 
		=> [Int] 0 if successful

	Side Effect: create an output csv file
	"""
	date, positions = readGenevaInvestmentPositionFile(inputFile)
	writeIdnTypeToFile('geneva_' + date + '_idntype.csv', positions)



def lognContinue(msg, x):
	logger.debug(msg)
	return x


def lognRaise(msg):
	logger.error(msg)
	raise ValueError




if __name__ == '__main__':
	import logging.config
	logging.config.fileConfig('logging.config', disable_existing_loggers=False)

	inputFile = join( getCurrentDirectory(), 'samples'
					, 'DIF_20200429_investment_position.xlsx')
	# createGenevaIdnTypeFile(inputFile)

	date, positions = readGenevaInvestmentPositionFile(inputFile)
	blpData = loadBlpDataFromFile('DIF_20200429_BlpData.xlsx')
	writeCsv( 'geneva_assetType_' + date + '.csv'
			, map(partial(getAssetType, blpData), positions) 
			)
