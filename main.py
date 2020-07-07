# coding=utf-8
#
# Read the Bloomberg input file (Excel) and Geneva input file, then produce
# master list files and LQA request files.
# 

from risk_report.utility import getCurrentDirectory
from risk_report.asset import isPrivateSecurity, isCash, isMoneyMarket \
							, isRepo, isFxForward, getIdnType, getAssetType \
							, getAverageRatingScore, getCountryCode \
							, byCountryFilter, countryNotApplicable \
							, toCountryGroup, fallsInAssetType \
							, getAverageRatingScore
from risk_report.sfc import readSfcTemplate
from risk_report.data import getFX, getPortfolioPositions, getBlpData, getMarketValue \
							, getBookCurrency, getLqaData, isCash, getLiquiditySpecialCaseData \
							, getQuantity
from utils.iter import pop
from utils.utility import writeCsv, mergeDict, fromExcelOrdinal
from toolz.functoolz import compose, juxt
from toolz.itertoolz import groupby as groupbyToolz
from toolz.dicttoolz import valmap
from functools import partial, reduce
from itertools import filterfalse, chain, takewhile
from datetime import datetime
from os.path import join
import logging
logger = logging.getLogger(__name__)



def getLiquidityCategory(date, mode, blpData, lqaData, position):
	"""
	[String] date (yyyymmdd),
	[Dictionary] lqaData,
	[Dictionary] position
		=> [Int] liquidity category
	
	Liquidity Category:

	L0: highly liquid
	L1: medium liquid
	L2: low liquid
	L3: illiquid
	"""
	# import sys
	# for x in lqaData:
	# 	print(x)

	# sys.exit(0)

	logger.debug('getLiquidityCategory(): {0}'.format(getIdnType(position)))

	toLiquiditCategory = lambda daysToCash: \
		'L0' if daysToCash <= 3 else \
		'L1' if daysToCash <= 7 else \
		'L2' if daysToCash <= 10 else 'L3'


	isLiquidAsset = lambda blpData, position: \
		True if getAssetType(blpData, position) == ('Cash', ) else False


	isLiquiditySpecialCase = lambda date, mode, position: \
		getIdnType(position)[0] in getLiquiditySpecialCaseData(date, mode)


	return \
	'L0' if isLiquidAsset(blpData, position) or getQuantity(position) == 0 else \
	getLiquidityCategorySpecialCase(date, mode, blpData, position) \
	if isLiquiditySpecialCase(date, mode, position) else \
	toLiquiditCategory(lqaData[getIdnType(position)[0]]['LQA_TIME_TO_CASH'])



def getLiquidityCategorySpecialCase(date, mode, blpData, position):
	"""
	[String] date (yyyymmdd),
	[Dictionary] lqaData,
	[Dictionary] position
		=> [Int] liquidity category
	"""
	logger.debug('getLiquidityCategorySpecialCase(): {0}'.format(getIdnType(position)))


	# [String] date, [String] mode => [Int] score
	maturityScore = compose(
		lambda yearToMaturity: 4 if yearToMaturity < 1 else \
			3 if yearToMaturity < 3 else \
			2 if yearToMaturity < 5 else 1
	  , lambda delta: delta.days // 365
	  , lambda maturityDate: maturityDate - datetime.strptime(date, '%Y%m%d')
	  , lambda d: d[getIdnType(position)[0]]['CALC_MATURITY']
	  , getLiquiditySpecialCaseData
	)


	# [Dictionary] blpData, [Dictionary] position => [Int] score
	ratingScore = compose(
		lambda score: 4 if score >= 15 else \
			3 if score >= 12 else \
			2 if score >= 6 else 1
	  , getAverageRatingScore
	)


	# [String] date, [String] mode => [Int] score
	concentrationScore = compose(
		lambda percentage: 4 if percentage < 5 else \
			3 if percentage < 10 else \
			2 if percentage < 20 else 1
	  , lambda outStandingAmount: getQuantity(position)/outStandingAmount * 100
	  , lambda d: d[getIdnType(position)[0]]['AMT_OUTSTANDING']
	  , getLiquiditySpecialCaseData
	)


	liquidityRating = lambda x: \
		'L0' if x >= 12 else \
		'L1' if x >=  9 else \
		'L2' if x >=  6 else 'L3'


	return \
	compose(
		liquidityRating
	  , lambda x, y, z: x + y + z
	)( maturityScore(date, mode)
	 , ratingScore(blpData, position)
	 , concentrationScore(date, mode)
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



""" [Dictionary] position, [String] reportingCurrency
		=> [Float] market value in reporting currency
"""
marketValueWithFX = lambda FX, position: \
	getMarketValue(position) / FX[getBookCurrency(position)]



""" 
	[String] date, [String] reportingCurrency, [Iterator] positions
		=> [Float] sum of market value of positions in reporting currency
"""
sumMarketValueInCurrency = lambda date, reportingCurrency, positions: \
compose(
	sum
  , partial( map
  		   , partial(marketValueWithFX, getFX(date, reportingCurrency))
  		   )
)(positions)



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
		partial(sumMarketValueInCurrency, date, reportingCurrency)
	  , partial(filter, partial(fallsInAssetType, blpData, assetTypeStrings))
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
		partial(sumMarketValueInCurrency, date, reportingCurrency)
	  , partial(filter, partial(fallsInAssetType, blpData, assetTypeStrings))
	)(positions)



def writeAssetAllocationCsv(portfolio, date, mode, reportingCurrency, countryGroups, assetTypeTuples):
	"""
	[String] portfolio,
	[String] date (yyyymmdd),
	[String] mode,
	[String] reportingCurrency
	[List] countries, (e.g., ['China - Hong Kong', 'China - Mainland', 'Singapore'])
	[List] assetTypeTuples (each assetTypeTuple is like ('Fixed Income', 'Corporate', 'Investment Grade'))
		
		=> [String] output csv file name

	Side effect: create a csv file.
	"""
	assetTypeToValues = lambda d, countryGroups, assetypeTuple: \
	compose(
		partial(map, partial(sumMarketValueInCurrency, date, reportingCurrency))
	  , lambda d: map(lambda cg: d[cg], countryGroups)
	  , lambda assetypeTuple: d[assetypeTuple]
	)(assetypeTuple)


	return \
	compose(
		partial(writeCsv, portfolio + '_asset_allocation_' + date + '.csv')
	  , lambda d: map(partial(assetTypeToValues, d, countryGroups), assetTypeTuples)
	  , partial(getAssetCountryAllocation, date, getBlpData(date, mode), assetTypeTuples, countryGroups)
	  , getPortfolioPositions
	)(portfolio, date, mode)



def getAssetTypeAllocation(date, blpData, assetTypeTuples, positions):
	"""
	[String] date (yyyymmdd),
	[Dictionary] blpData,
	[Iterator] assetTypeTuples,
	[Iterator] positions
		=> [Dictionary] assetypeTuple -> list of positions matching that 
				asset type

	Each position will be allocated to the first asset type it matches.
	"""
	def accumulate(acc, el):
		for assetType in acc:
			if fallsInAssetType(blpData, assetType, el):
				acc[assetType] = chain(acc[assetType], [el])
				break

		return acc


	return reduce( accumulate
				 , positions
				 , {assetType: [] for assetType in assetTypeTuples}
				 )



def getCountryGroupAllocation(date, blpData, countryGroups, positions):
	"""
	[String] date (yyyymmdd),
	[Dictionary] blpData,
	[Iterator] countryGroups,
	[Iterator] positions
		=> [Dictionary] country group -> list of positions in that country
			group

	Each position will be allocated to the first asset type it matches.
	"""
	def accumulate(acc, el):
		cg = toCountryGroup(blpData, el)
		try:
			acc[cg] = chain(acc[cg], [el])
		except KeyError:
			pass

		return acc


	return reduce( accumulate
				 , positions
				 , {cg: [] for cg in countryGroups}
				 )



def getAssetCountryAllocation(date, blpData, assetTypeTuples, countryGroups, positions):
	"""
	[String] date (yyyymmdd),
	[Dictionary] blpData,
	[Iterator] assetTypeTuples,
	[List] countryGroups,
	[Iterator] positions
		=> [Dictionary] assetypeTuple -> [Dictionary] countryGroup -> List of
			positions that fall into this asset type and this country group
	"""
	return \
	valmap( partial(getCountryGroupAllocation, date, blpData, countryGroups)
		  , getAssetTypeAllocation(date, blpData, assetTypeTuples, positions)
		  )



def getLiquidityDistribution(portfolio, date, mode, reportingCurrency, separator='|'):
	"""
	[String] portfolio
	[String] date (yyyymmdd),
	[String] mode
	[String] reportingCurrency
	[String] separator

		=> [Iterator] rows of liquidity distribution

	Where each row consists of 3 items: liquidity category, total market value in
	this category, % of total market value
	"""
	getMarketValueForEachCategory = compose(
		lambda d: map( lambda key: ( key
	  							   , sumMarketValueInCurrency(date, reportingCurrency, d[key])
	  							   )
			         , d.keys()
			         )
	  , partial( groupbyToolz
	  		   , partial( getLiquidityCategory, date, mode
	  		   			, getBlpData(date, mode)
	  		   			, getLqaData(date, mode, separator))
	  		   )
	)


	checkTotal = lambda tuples: \
		tuples if abs(sum(map(lambda t: t[2], tuples)) - 1.0) < 0.0000001 else \
		lognRaise('getLiquidityDistribution(): sum of percentage is not 1.0')


	return \
	compose(
		checkTotal
	  , sorted
	  , lambda t: map(lambda ct: (ct[0], ct[1], ct[1]/t[1]), t[0])
	  , lambda positions: ( getMarketValueForEachCategory(positions)
	  					  , sumMarketValueInCurrency(date, reportingCurrency, positions)
	  					  )
	  , list
	)(getPortfolioPositions(portfolio, date, mode))



def lognContinue(msg, x):
	logger.debug(msg)
	return x


def lognRaise(msg):
	logger.error(msg)
	raise ValueError



if __name__ == '__main__':
	import logging.config
	logging.config.fileConfig('logging.config', disable_existing_loggers=False)

	"""
		Generate asset allocation report. Say for 19437 on 2020-05-29, do

			$python main.py 19437 20200529

		If you want to use test datastore, so

			$python main.py 19437 20200529 --test

		Before generating the final asset allocation report in step 6, go through
		step 1 - 5 to make sure the blpData is ready.
	"""

	import argparse
	parser = argparse.ArgumentParser(description='Generate asset allocation reports.')
	parser.add_argument( 'portfolio', metavar='portfolio', type=str
					   , help='for which portfolio')
	parser.add_argument( 'date', metavar='date', type=str
					   , help='date of the positions (yyyymmdd)')
	parser.add_argument( '--test', type=str, nargs='?', const=True, default=False
					   , help='use test mode datastore')
	args = parser.parse_args()

	mode = 'test' if args.test else 'production'
	portfolio = args.portfolio
	date = args.date


	# Step 1. Create a file containing the (id, idtype) columns.
	# compose(
	# 	print
	#   , lambda positions: \
	# 		writeIdnTypeToFile(portfolio + '_idntype_' + date + '.csv', positions)
	#   , getPortfolioPositions
	# )(portfolio, date)


	# Step 2. Use the BlpData_Template.xlsx to load Bloomberg data and save
	# the result. In the case of using file as datastore, the blp file name
	# needs to follow the naming convention defined in data.py


	# Step 3. Check if all asset types can be determined.
	# compose(
	# 	print
	#   , lambda positions: writeCsv( portfolio + '_assetType_' + date + '.csv'
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
	# 				, chain([('Id', 'IdType')], set(positions))
	# 				)
	#   , partial(getFISecuritiesWoRatings, getBlpData(date))
	#   , getPortfolioPositions
	# )(portfolio, date)
	

	"""
	Step 5. Check if all securities get	country code and map to a country group,
	except those not applicable, e.g., cash and FX forwards.
	"""
	# compose(
	# 	print
	#   , partial(valmap, partial(sumMarketValueInCurrency, date, 'USD'))
	#   , partial(groupbyToolz, partial(toCountryGroup, getBlpData(date, mode)))
	#   , partial(filterfalse, partial(countryNotApplicable, getBlpData(date, mode)))
	#   , getPortfolioPositions
	# )(portfolio, date, mode)


	"""
	Step 6. Write a output csv with the country groups and asset types in the
	SFC template file. Update that template file if necessary.
	"""
	# Get cash total (change type to 'Foreign exchange derivatives' for FX forward)
	# compose(
	# 	print
	#   , lambda positions: \
	#   		getTotalMarketValueFromAssetType( date, positions, getBlpData(date)
	#   										, 'USD', 'Cash')
	#   , getPortfolioPositions
	# )(portfolio, date)


	# Write the final asset allocation csv
	# compose(
	# 	print
	#   , lambda t: writeAssetAllocationCsv(portfolio, date, mode, 'USD', t[0], t[1])
	#   , lambda t: (t[0], list(t[1]))
	#   , readSfcTemplate
	# )('SFC_Asset_Allocation_Template.xlsx')


	################################################################
	# Debug Section
	################################################################
	# def showPositions(L):
	# 	for x in L:
	# 		print(getIdnType(x)[0], getMarketValue(x))

	# def showKeys(d):
	# 	for key in d:
	# 		print(key)

	# Show all asset types except the cash and FX forward
	# compose(
	# 	showKeys
	#   , lambda t: getAssetCountryAllocation(date, getBlpData(date, mode), t[2], t[1], t[0])
	#   , lambda t: (t[0], t[1], list(t[2]))
	#   , lambda portfolio: ( getPortfolioPositions(portfolio, date, mode)
	#   					  , *readSfcTemplate('SFC_Asset_Allocation_Template.xlsx')
	#   					  )
	# )(portfolio)


	# Show the positions with a particular asset type and country group
	# compose(
	# 	showPositions
	#   , lambda d: d[('Fixed income (Note 2)', 'Corporate (Note 4)', 'Non-Investment Grade (Note 3)', 'Financial Institution')]['China - Mainland']
	#   , lambda t: getAssetCountryAllocation(date, getBlpData(date, mode), t[2], t[1], t[0])
	#   , lambda t: (t[0], t[1], list(t[2]))
	#   , lambda portfolio: ( getPortfolioPositions(portfolio, date, mode)
	#   					  , *readSfcTemplate('SFC_Asset_Allocation_Template.xlsx')
	#   					  )
	# )(portfolio)


	# Show cash
	# compose(
	# 	showPositions
	#   , partial(filter, partial(fallsInAssetType, getBlpData(date, mode), ('Cash',)))
	#   , lambda portfolio: getPortfolioPositions(portfolio, date, mode)
	# )(portfolio)


	#####################################
	#
	# Liquidit report
	#
	#####################################

	# Step 1. Search for any securities that do not have a valid response from
	# the LQA response file.
	# compose(
	# 	print
	#   , partial(writeCsv, 'MissingLiquidity_' + date + '.csv')
	#   , lambda rows: chain([('securities', )], rows)
	#   , partial(map, lambda p: (p['SECURITIES'], ))
	#   , lambda d: filter( lambda p: p['ERROR CODE'] != 0 or p['LQA_TIME_TO_CASH'] == 'N.A.'
	# 				  	, d.values())
	#   , getLqaData
	# )(date, mode)


	# Step 2. Generate the liquidity special case file, which contains information
	# needed to determine their liquidity bucket.


	# Step 3. Generate liquidity report.
	# compose(
	# 	print
	#   , partial(writeCsv, portfolio + '_liquidity_' + date + '.csv')
	#   , lambda rows: chain([('Category', 'Total', 'Percentage')], rows)
	#   , getLiquidityDistribution
	# )(portfolio, date, mode, 'USD')