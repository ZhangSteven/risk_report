# coding=utf-8
#
# Read the Bloomberg input file (Excel) and Geneva input file, then produce
# master list files and LQA request files.
# 

from risk_report.utility import getCurrentDirectory
from risk_report.asset import isPrivateSecurity, isCash, isMoneyMarket \
							, isRepo, isFxForward, getIdnType, getAssetType \
							, getAverageRatingScore
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
	[String] output file name, [Iterator] positions
		=> [String] output file name

	Side effect: write a csv file containing the id, idType for the positions

	A utility function, using which we can convert positions (Geneva or Bloomberg)
	to a file containing two columns (id, idType). The file will used to load
	Bloomberg information for asset type processing.
	"""
	noNeedId = lambda position: \
		any(juxt(isPrivateSecurity, isCash, isMoneyMarket, isRepo, isFxForward)(position))


	return \
	compose(
		lambda idnTypes: writeCsv(file, chain([('ID', 'ID_TYPE')], idnTypes))
	  , set
	  , partial(map, getIdnType)
	  , partial(filterfalse, noNeedId)
	)(positions)



"""
	[String] inputFile (geneva investment positions report, Excel Format) 
		=> [Int] 0 if successful

	Side Effect: create an output csv file
"""
createGenevaIdnTypeFile = compose(
	lambda t: writeIdnTypeToFile('geneva_' + t[0] + '_idntype.csv', t[1])
  , readGenevaInvestmentPositionFile
)



# [Tuple] assetType => [Bool] is credit rating applicable
ratingsApplicable = lambda assetType: \
	len(assetType) > 1 and \
	assetType[0] == 'Fixed Income' and \
	not assetType[1] in ['Cash Equivalents', 'Credit Derivatives', 'Asset-Backed']



def getFISecuritiesWoRatings(blpData, positions):

	missing = []
	def accumulate(position):
		missing.extend([getIdnType(position)])
		return 0


	compose(
		lambda L: list(map( lambda p: getAverageRatingScore(blpData, p, accumulate)
						  , L))
	  , partial(map, lambda t: t[1])
	  , partial(filter, lambda t: ratingsApplicable(t[0]))
	  , lambda blpData, positions: \
	  		map(lambda p: (getAssetType(blpData, p), p), positions)
	)(blpData, positions)


	return missing
# End of getFISecuritiesWoRatings()



def lognContinue(msg, x):
	logger.debug(msg)
	return x


def lognRaise(msg):
	logger.error(msg)
	raise ValueError




if __name__ == '__main__':
	import logging.config
	logging.config.fileConfig('logging.config', disable_existing_loggers=False)

	inputFile = join( getCurrentDirectory()
					, 'samples'
					, 'DIF_20200429_investment_position.xlsx'
					)

	# Step 1. Create a file containing the (id, idtype) columns.
	# createGenevaIdnTypeFile(inputFile)

	# Step 2. Use the BlpData_Template.xlsx to load Bloomberg data and save
	# the result to a new file (blpDataFile).

	# Step 3. Check if all asset types can be determined.
	blpDataFile = join( getCurrentDirectory()
					  , 'samples'
					  , 'DIF_20200429_BlpData.xlsx'
					  )

	# compose(
	# 	lambda t: writeCsv( 'geneva_assetType_' + t[0] + '.csv'
	# 					  , map(partial(getAssetType, t[2]), t[1]) 
	# 					  )
	#   , lambda inputFile, blpDataFile: \
	#   		( *readGenevaInvestmentPositionFile(inputFile)
	#   		, loadBlpDataFromFile(blpDataFile)
	#   		)
	# )(inputFile, blpDataFile)


	# Step 4. Check if all Fixed Income securities get credit ratings.
	# If there are missing ones, then it will be saved to a csv file.
	compose(
		print
	  , lambda t: 'All FI securities have at least one credit rating' if len(t[1]) == 0 else \
	  			  writeCsv( 'MissingCreditRating_' + t[0] + '_.csv'
						  , chain([('Id', 'IdType')], t[1])
						  )
	  , lambda t: (t[0], getFISecuritiesWoRatings(t[2], t[1]))
	  , lambda inputFile, blpDataFile: \
	  		( *readGenevaInvestmentPositionFile(inputFile)
	  		, loadBlpDataFromFile(blpDataFile)
	  		)	
	)(inputFile, blpDataFile)
