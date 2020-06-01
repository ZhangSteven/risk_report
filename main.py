# coding=utf-8
#
# Read the Bloomberg input file (Excel) and Geneva input file, then produce
# master list files and LQA request files.
# 

from risk_report.utility import getCurrentDirectory
from risk_report.asset import isPrivateSecurity, isCash, isMoneyMarket \
							, isRepo, isFxForward, getIdnType, getAssetType \
							, getAverageRatingScore, getCountryCode, byCountryGroup \
							, byAssetTypeFilterTuple, byCountryFilter
from risk_report.geneva import readGenevaInvestmentPositionFile, isGenevaPosition \
							, getGenevaMarketValue, getGenevaBookCurrency
from risk_report.blp import getBlpMarketValue, getBlpBookCurrency
from risk_report.sfc import readSfcTemplate
from clamc_datafeed.feeder import getRawPositions, fileToLines
from utils.iter import pop
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

	# [Dictionary] blpData, [Dictionary] position => [Bool] position needs rating
	needsRating = compose(
		ratingsApplicable
	  , getAssetType
	)


	compose(
		lambda L: list(map( lambda p: getAverageRatingScore(blpData, p, accumulate)
						  , L))
	  , lambda blpData, positions: filter(partial(needsRating, blpData), positions)
	)(blpData, positions)


	return missing
# End of getFISecuritiesWoRatings()



"""
	[Dictionary] position => [Float] market value of the position
"""
getMarketValue = lambda position: \
	getGenevaMarketValue(position) if isGenevaPosition(position) else \
	getBlpMarketValue(position)



"""
	[Dictionary] position => [String] book currency of the position
"""
getBookCurrency = lambda position: \
	getGenevaBookCurrency(position) if isGenevaPosition(position) else \
	getBlpBookCurrency(position)



def getTotalMarketValueFromCountrynAssetType( positions
											, blpData
											, reportingCurrency
											, countryGroup
											, *assetTypeStrings):
	"""
	[Iterator] positions
	[Dictionary] blpData
	[String] reporting currency, 
	[String] countryGroup, 
	[String] tier 1 asset type,
	[String] tier 2 asset type, 
	...
		=> [Float] total market value of positions that match the criteria

	For example, 

	('USD', 'China') -> sum up market value in USD of all positions from China
	('HKD', 'Hong Kong', 'Equity') -> sum up in HKD of all positions from Hong Kong
										whose type is 'Equity'
	
	The below are also valid parameters
	('USD', 'America - others (1)', 'Fixed Income', 'Government / Municiple', 'Investment Grade')
	( 'USD', 'United States of America', 'Fixed Income', 'Corporate'
	, 'Investment Grade', 'Financial Institutions')
	"""
	marketValueInReportingCurrency = lambda position: \
		getMarketValue(position) / getFXRate(reportingCurrency, getBookCurrency(position))


	return \
	compose(
		sum
	  , partial(map, marketValueInReportingCurrency)
	  , byAssetTypeFilterTuple(blpData, assetTypeStrings)
	  , byCountryFilter(blpData, countryGroup)
	)(positions)



def getTotalMarketValueFromAssetType( positions
									, blpData
									, reportingCurrency
									, *assetTypeStrings):
	"""
	[Iterator] positions
	[Dictionary] blpData
	[String] reporting currency, 
	[String] tier 1 asset type,
	[String] tier 2 asset type, 
	...
		=> [Float] total market value of positions that match the criteria

	This function does not take country as input.

	# FIXME: Add implementation
	"""
	lognRaise('getTotalMarketValueFromAssetType(): not implemented')



def getFXRate(c1, c2):
	"""
	[String] c1 (currency), [String] c2 (currency)
		=> [Float] exchange rate to convert 1 unit of c1 to c2

	For example, getFXRate('USD', 'HKD') = 7.8120

	# FIXME: another parameter, date, is needed because FX rates change over time.
	"""
	return loadFXTableFromFile('FXRate.xlsx')[(c1, c2)]



def loadFXTableFromFile(file):
	"""
	[String] fx rate file => [Dictionary] (c1, c2) -> exchange rate

	# FIXME: add implementation
	"""
	return {('USD', 'HKD'): 7.7520}	# FX rate as of 2020-04-30



def writeAssetAllocationCsv(date, positions, blpData, sfcAssetAllocationTemplate):
	"""
	[String] date
	[Iterator] positions
	[Dictionary] blpData
	[String] sfc asset allocation template file
		=> [String] output csv file name

	Side effect: create a csv file.

	NOTE: this function can take a few minutes to complete, especially when logging
	level is set to DEBUG.
	"""
	assetTypeWithCountry = lambda headers, assetType: \
		map(lambda el: (el, ) + assetType, headers)

	assetTypeWithCountryToMarketValue = lambda positions, blpData, t: \
		getTotalMarketValueFromCountrynAssetType(positions, blpData, 'USD', *t)

	assetTypeLineToValues = lambda positions, blpData, line: \
		map( partial(assetTypeWithCountryToMarketValue, positions, blpData)
		   , line)


	return \
	compose(
		lambda lines: writeCsv( 'asset_allocation_' + date + '.csv'
							  , lines)
	  , partial( map
	  		   , partial(assetTypeLineToValues, list(positions), blpData))
	  , lambda t: map(partial(assetTypeWithCountry, t[0]), t[1])
	  , lambda _1, _2, _3, sfcFile: readSfcTemplate(sfcFile)
	)(date, positions, blpData, sfcAssetAllocationTemplate)



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
	# the result to "blpDataFile".

	# Step 3. Check if all asset types can be determined.
	blpDataFile = join( getCurrentDirectory()
					  , 'samples'
					  , 'DIF_20200429_BlpData.xlsx'
					  )

	# compose(
	# 	print
	#   , lambda t: writeCsv( 'geneva_assetType_' + t[0] + '.csv'
	# 					  , map(partial(getAssetType, t[2]), t[1]) 
	# 					  )
	#   , lambda inputFile, blpDataFile: \
	#   		( *readGenevaInvestmentPositionFile(inputFile)
	#   		, loadBlpDataFromFile(blpDataFile)
	#   		)
	# )(inputFile, blpDataFile)



	"""
	Step 4. Check if all Fixed Income securities get credit ratings.
	Those bonds with no credit ratings from any one of the 3 angencies or
	those with some ratings but all equal to zero, will be saved to a csv file. 
	Ask risk team to see if they want to give any manual credit scores to those. 
	"""
	# compose(
	# 	print
	#   , lambda t: 'All FI securities have at least one credit rating' if len(t[1]) == 0 else \
	#   			  writeCsv( 'MissingCreditRating_' + t[0] + '.csv'
	# 					  , chain([('Id', 'IdType')], t[1])
	# 					  )
	#   , lambda t: (t[0], getFISecuritiesWoRatings(t[2], t[1]))
	#   , lambda inputFile, blpDataFile: \
	#   		( *readGenevaInvestmentPositionFile(inputFile)
	#   		, loadBlpDataFromFile(blpDataFile)
	#   		)	
	# )(inputFile, blpDataFile)
	


	"""
	Step 5. Check if all securities except cash and FX forwards can get
	country code.
	"""
	# compose(
	# 	print
	#   , lambda t: writeCsv( 'countries_' + t[0] + '.csv'
	# 					  , chain([('Country Code', )], map(lambda s: [s], t[1]))
	# 					  )
	#   , lambda t: ( t[0]
	#   			  , map( partial(getCountryCode, t[2])
	#   			  	   , filterfalse(partial(countryNotApplicable, t[2]), t[1])
	#   			  	   )
	#   			  )
	#   , lambda inputFile, blpDataFile: \
	#   		( *readGenevaInvestmentPositionFile(inputFile)
	#   		, loadBlpDataFromFile(blpDataFile)
	#   		)	
	# )(inputFile, blpDataFile)


	"""
	Step 6. Write a output csv with the country groups and asset types in the
	SFC template file. Update that template file if necessary.
	"""
	# Do this to play around with different selection criteria.
	# 
	# compose(
	# 	print
	#   , lambda t: getTotalMarketValueFromCountrynAssetType(
	#   				  t[1]
	#   				, t[2]
	#   				, 'USD'
	#   			    , 'Asia - others (1)'
	#   			    , 'Fixed Income'
	#   			    , 'Corporate'
	#   			    , 'Non-Investment Grade'
	#   			    , 'Financial Institution'
	#   			  )
	#   , lambda inputFile, blpDataFile: \
	#   		( *readGenevaInvestmentPositionFile(inputFile)
	#   		, loadBlpDataFromFile(blpDataFile)
	#   		)	
	# )(inputFile, blpDataFile)


	sfcAssetAllocationTemplate = 'SFC_Asset_Allocation_Template.xlsx'
	compose(
		print
	  , lambda t: \
	  		writeAssetAllocationCsv(t[0], t[1], t[2], sfcAssetAllocationTemplate)

	  , lambda inputFile, blpDataFile, _: \
	  		( *readGenevaInvestmentPositionFile(inputFile)
	  		, loadBlpDataFromFile(blpDataFile)
	  		)
	)(inputFile, blpDataFile, sfcAssetAllocationTemplate)