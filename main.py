# coding=utf-8
#
# Read the Bloomberg input file (Excel) and Geneva input file, then produce
# master list files and LQA request files.
# 

from risk_report.utility import getCurrentDirectory
from risk_report.asset import isPrivateSecurity, isCash, isMoneyMarket \
							, isRepo, isFxForward, getIdnType, getAssetType \
							, getAverageRatingScore, getCountryCode, byCountryGroup \
							, byAssetTypeFilterTuple, byCountryFilter, countryNotApplicable
from risk_report.geneva import isGenevaPosition, getGenevaMarketValue, getGenevaBookCurrency
from risk_report.blp import getBlpMarketValue, getBlpBookCurrency
from risk_report.sfc import readSfcTemplate
from risk_report.data import getFX, getPortfolioPositions, getBlpData
from utils.iter import pop
from utils.utility import writeCsv, mergeDict, fromExcelOrdinal
from toolz.functoolz import compose, juxt
from functools import partial
from itertools import filterfalse, chain, takewhile
from datetime import datetime
from os.path import join
import logging
logger = logging.getLogger(__name__)



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
		list
	  , partial(map, lambda p: getAverageRatingScore(blpData, p, accumulate))
	  , partial(filter, partial(needsRating, blpData))
	)(positions)


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



""" [Dictionary] position, [String] reportingCurrency
		=> [Float] market value in reporting currency
"""
marketValueWithFX = lambda FX, position: \
	getMarketValue(position) / FX[getBookCurrency(position)]



def getTotalMarketValueFromCountrynAssetType( date
											, positions
											, blpData
											, reportingCurrency
											, countryGroup
											, *assetTypeStrings):
	"""
	[String] date (yyyymmdd),
	[Iterator] positions,
	[Dictionary] blpData,
	[String] reporting currency,
	[String] countryGroup,
	[String] tier 1 asset type,
	[String] tier 2 asset type, 
	...
		=> [Float] total market value of positions that match the criteria

	From the input positions, filter out those that match the selection criteria,
	and then sum up their market value in reporting currency.

	For example, 

	('USD', 'China') -> sum up market value in USD of all positions from China
	('HKD', 'Hong Kong', 'Equity') -> sum up in HKD of all positions from Hong Kong
										whose type is 'Equity'
	
	Other examples are:

	('USD', 'America - others (1)', 'Fixed Income', 'Government / Municiple', 'Investment Grade')
	( 'USD', 'United States of America', 'Fixed Income', 'Corporate'
	, 'Investment Grade', 'Financial Institutions')
	"""
	return \
	compose(
		sum
	  , partial( map
	  		   , partial( marketValueWithFX
	  		   			, getFX(date, reportingCurrency))
	  		   )
	  , byAssetTypeFilterTuple(blpData, assetTypeStrings)
	  , byCountryFilter(blpData, countryGroup)
	)(positions)



def getTotalMarketValueFromAssetType( date
									, positions
									, blpData
									, reportingCurrency
									, *assetTypeStrings):
	"""
	[String] date (yyyymmdd),
	[Iterator] positions
	[Dictionary] blpData
	[String] reporting currency, 
	[String] tier 1 asset type,
	[String] tier 2 asset type, 
	...
		=> [Float] total market value of positions that match the criteria

	"""
	return \
	compose(
		sum
	  , partial( map
	  		   , partial( marketValueWithFX
	  		   			, getFX(date, reportingCurrency))
	  		   )
	  , byAssetTypeFilterTuple(blpData, assetTypeStrings)
	)(positions)



def writeAssetAllocationCsv(date, positions, blpData, reportingCurrency, countries, assetTypes):
	"""
	[String] date (yyyymmdd),
	[Iterator] positions,
	[Dictionary] blpData,
	[List] countries, (e.g., ['China - Hong Kong', 'China - Mainland', 'Singapore'])
	[Iterator] assetTypes (each assetType is a tuple like ('Fixed Income', 'Corporate', 'Investment Grade'))
		
		=> [String] output csv file name

	Side effect: create a csv file.

	NOTE: this function can take a few minutes to complete, especially when logging
	level is set to DEBUG.
	"""
	assetTypeWithCountry = lambda countries, assetType: \
		map(lambda el: (el, ) + assetType, countries)

	assetTypeWithCountryToMarketValue = lambda positions, blpData, t: \
		getTotalMarketValueFromCountrynAssetType(date, positions, blpData, reportingCurrency, *t)

	assetTypeLineToValues = lambda positions, blpData, line: \
		map( partial(assetTypeWithCountryToMarketValue, positions, blpData)
		   , line)


	return \
	compose(
		lambda lines: writeCsv( 'asset_allocation_' + date + '.csv'
							  , lines)
	  , partial(map, partial(assetTypeLineToValues, list(positions), blpData))
	  , partial(map, partial(assetTypeWithCountry, countries))
	)(assetTypes)



def lognContinue(msg, x):
	logger.debug(msg)
	return x


def lognRaise(msg):
	logger.error(msg)
	raise ValueError




if __name__ == '__main__':
	import logging.config
	logging.config.fileConfig('logging.config', disable_existing_loggers=False)

	date = '20200529'
	portfolio = '19437'

	# Step 1. Create a file containing the (id, idtype) columns.
	# compose(
	# 	print
	#   , lambda positions: \
	# 		writeIdnTypeToFile('geneva_' + date + '_idntype.csv', positions)
	#   , getPortfolioPositions
	# )(portfolio, date)


	# Step 2. Use the BlpData_Template.xlsx to load Bloomberg data and save
	# the result. In the case of using file as datastore, the blp file name
	# needs to follow the naming convention defined in data.py


	# Step 3. Check if all asset types can be determined.
	# compose(
	# 	print
	#   , lambda positions: writeCsv( 'geneva_assetType_' + date + '.csv'
	# 					  		  , map( partial(getAssetType, getBlpData(date))
	# 					  		  	   , positions) 
	# 					  		  )
	#   , getPortfolioPositions
	# )(portfolio, date)


	"""
	Step 4. Check if all Fixed Income securities get credit ratings.
	Those bonds with no credit ratings from any one of the 3 angencies or
	those with some ratings but all equal to zero, will be saved to a csv file. 
	Ask risk team to see if they want to give any manual credit scores to those. 
	"""
	# compose(
	# 	print
	#   , lambda positions: \
	#   		'All FI securities have at least one credit rating' if len(positions) == 0 else \
	#   		writeCsv( 'MissingCreditRating_' + date + '.csv'
	# 				, chain([('Id', 'IdType')], positions)
	# 				)
	#   , partial(getFISecuritiesWoRatings, getBlpData(date))
	#   , getPortfolioPositions
	# )(portfolio, date)
	

	"""
	Step 5. Check if all securities except cash and FX forwards can get
	country code.
	"""
	# compose(
	# 	print
	#   , lambda positions: writeCsv( 'countries_' + date + '.csv'
	# 					  		  , chain( [('Country Code', )]
	# 					  		  		 , map(lambda s: [s], positions))
	# 					  		  )
	#   , partial(map, partial(getCountryCode, getBlpData(date)))
	#   , partial(filterfalse, partial(countryNotApplicable, getBlpData(date)))
	#   , getPortfolioPositions
	# )(portfolio, date)


	"""
	Step 6. Write a output csv with the country groups and asset types in the
	SFC template file. Update that template file if necessary.
	"""
	# Get cash total (change type to 'Foreign exchange derivatives' if necessary)
	# compose(
	# 	print
	#   , lambda positions: \
	#   		getTotalMarketValueFromAssetType( date, positions, getBlpData(date)
	#   										, 'USD', 'Cash')
	#   , getPortfolioPositions
	# )(portfolio, date)


	compose(
		print
	  , lambda positions: writeAssetAllocationCsv( date
	  											 , positions
	  											 , getBlpData(date)
	  											 , 'USD'
	  											 , *readSfcTemplate('SFC_Asset_Allocation_Template.xlsx')
	  											 )
	  , getPortfolioPositions
	)(portfolio, date)