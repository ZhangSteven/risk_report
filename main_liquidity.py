# coding=utf-8
#
# Using the pandas dataframe to get liquidity statistics.
# 
from risk_report.asset import getAverageRatingScore
from risk_report.data import getQuantity
from toolz.functoolz import compose
from datetime import datetime
import logging
logger = logging.getLogger(__name__)



def getLiquidityCategorySpecialCaseBond(date, blpData, position):
    """
    [String] date (yyyymmdd),
    [Dictionary] blpData,
    [Dictionary] position
        => [String] liquidity category
    """
    logger.debug('getLiquidityCategorySpecialCaseBond()')

    # [String] date, [Dictionary] position => [Int] score
    maturityScore = compose(
        lambda yearToMaturity: 4 if yearToMaturity < 1 else \
            3 if yearToMaturity < 3 else \
            2 if yearToMaturity < 5 else 1
      , lambda delta: delta.days // 365
      , lambda date, position: position['CALC_MATURITY'] - datetime.strptime(date, '%Y%m%d')
    )


    # [Dictionary] blpData, [Dictionary] position => [Int] score
    ratingScore = compose(
        lambda score: 4 if score >= 15 else \
            3 if score >= 12 else \
            2 if score >= 6 else 1
      , getAverageRatingScore
    )


    # [Dictionary] position => [Int] score
    concentrationScore = compose(
        lambda percentage: 4 if percentage < 5 else \
            3 if percentage < 10 else \
            2 if percentage < 20 else 1
      , lambda p: getQuantity(p)/p['AMT_OUTSTANDING'] * 100
    )


    liquidityRating = lambda x: \
        'L0' if x >= 12 else \
        'L1' if x >=  9 else \
        'L2' if x >=  6 else 'L3'


    return liquidityRating(
    			maturityScore(date, position) \
    		  + ratingScore(blpData, position) \
    		  + concentrationScore(position)
    	   )
# End of getLiquidityCategorySpecialCaseBond()




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