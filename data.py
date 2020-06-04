# coding=utf-8
#
# Functions related to data retrieving are grouped here.
# 
from risk_report.utility import getInputDirectory
from clamc_datafeed.feeder import getPositions
from utils.excel import getRawPositions, fileToLines, getRawPositionsFromFile
from utils.iter import pop, firstOf
from utils.utility import mergeDict, fromExcelOrdinal
from toolz.functoolz import compose
from functools import partial, lru_cache
from itertools import filterfalse, takewhile
from datetime import datetime
from os.path import join
import logging
logger = logging.getLogger(__name__)



getCountryMapping = lambda : loadCountryGroupMappingFromFile('SFC_Country.xlsx')


getRatingScoreMapping = lambda : loadRatingScoreMappingFromFile('RatingScore.xlsx')


getAssetTypeSpecialCaseData = lambda: loadAssetTypeSpecialCaseFromFile('AssetType_SpecialCase.xlsx')



"""
	[String] date (yyyymmdd), [String] mode
		=> [Dictionary] meta data of the positions 
"""
getBlpData = lambda date, mode='production': \
	loadBlpDataFromFile(getBlpDataFile(date, mode))



"""
	[String] file => [Dictionary] data (ID -> [Dictioanry] blp information)
"""
loadBlpDataFromFile = compose(
	dict
  , partial(map, lambda p: (p['ID'], p))
  , getRawPositionsFromFile
)



getBlpDataFile = lambda date, mode: \
	join(getInputDirectory(mode), 'BlpData_' + date + '.xlsx')



"""
	[String] portfolio, [String] date (yyyymmdd), [String] mode
		=> [Iterator] positions of the portfolio 
"""
getPortfolioPositions = lambda portfolio, date, mode='production': \
	getGenevaPositions(portfolio, date, mode) if portfolio == '19437' else \
	getBlpPositions(portfolio, date, mode)



getBlpPositions = lambda portfolio, date, mode: \
	lognRaise('getBlpPositions(): not implemented')



def getGenevaPositions(portfolio, date, mode):
	"""
	[String] portfolio, [String] date (yyyymmdd), [String] mode
		=> [Iterator] Investment positions of the portfolio on that date
	"""

	"""
		[String] file (Geneva investment positions report, Excel format)
			=> [Iterator] positions
	"""
	readGenevaInvestmentPositionFile = compose(
		partial( map
			   , lambda p: mergeDict(p, {'Remarks1': 'Geneva investment positions report'})
			   )

	  , lambda lines: getPositions(lines)[1]
	  , fileToLines
	  , lambda file: lognContinue('readGenevaInvestmentPositionFile(): {0}'.format(file), file)
	)


	"""
		[String] portfolio, [String] date (yyyymmdd), [String] mode
			=> [String] file 
	"""
	getGenevaInvestmentPositionFile = lambda portfolio, date, mode: \
		join( getInputDirectory(mode)
			, portfolio + '_Investment_Positions_' + date + '.xlsx'
			)


	return \
	compose(
		readGenevaInvestmentPositionFile
	  , getGenevaInvestmentPositionFile
	)(portfolio, date, mode)



@lru_cache(maxsize=3)
def loadRatingScoreMappingFromFile(file):
	"""
	[String] rating score mapping file 
		=> [Dictionary] (agency, rating string) -> rating score
	"""
	return \
	compose(
		dict
	  , partial(map, lambda line: ((line[0], line[1]), line[2]))
	  , partial(takewhile, lambda line: len(line) > 2 and line[0] != '')
	  , lambda t: t[1]
	  , lambda lines: (pop(lines), lines)
	  , fileToLines
	)(file)



@lru_cache(maxsize=3)
def loadCountryGroupMappingFromFile(file):
	"""
	[String] file => [Dictionary] country code -> country group
	"""
	return \
	compose(
		dict
	  , partial(map, lambda line: (line[0], line[2].strip()))
	  , partial(takewhile, lambda line: len(line) > 2 and line[0] != '')
	  , lambda t: t[1]
	  , lambda lines: (pop(lines), lines)
	  , fileToLines
	)(file)



@lru_cache(maxsize=3)
def loadAssetTypeSpecialCaseFromFile(file):
	"""
	[String] file => [Dictionary] ID -> [Dictionary] security info
	"""
	stringToTuple = compose(
		tuple
	  , partial(map, lambda s: s.strip())
	  , lambda s: s.split(',')
	)


	updatePosition = lambda position: mergeDict(
		position
	  , { 'Portfolio': str(int(position['Portfolio'])) \
	  					if isinstance(position['Portfolio'], float) \
	  					else position['Portfolio']
	  	, 'AssetType': stringToTuple(position['AssetType'])
	  	}
	)


	return \
	compose(
		dict
	  , partial(map, lambda p: (p['ID'], p))
	  , partial(map, updatePosition)
	  , getRawPositions
	  , fileToLines
	)(file)



@lru_cache(maxsize=3)
def getFX(date, targetCurrency):
	"""
	[String] date (yyyymmdd),
	[String] targetCurrency
		=> [Dictionary] currency -> exchange rate

	Exchange rate: to get 1 unit of target currency, how many units of another 
	currency is needed.

	For example, d = loadFXTableFromFile('20200430', 'USD')

	Then

	d['HKD'] = 7.7520 (USDHKD as of 20200430)
	"""
	toDateString = lambda x: \
		datetime.strftime(fromExcelOrdinal(x), '%Y%m%d')


	return \
	compose(
		partial(mergeDict, {targetCurrency: 1.0})
	  , dict
	  , partial(map, lambda p: (p['Currency'], p['FX']))
	  , partial( filter
	  		   , lambda p: toDateString(p['Date']) == date and p['Reporting Currency'] == targetCurrency
	  		   )
	  , getRawPositionsFromFile
	)('FX.xlsx')



# def saveGenevaPositionToDB(file):
# 	"""
# 	[String] file => [Int] 0 (if successful or raise exception otherwise)

# 	Side effect: save positions to a database

# 	Read Geneva Positions from a file and save them into a database
# 	"""

# 	"""
# 		[Dictionary] position => [Dictionary] position

# 		Enrich the position before saving the document to database.

# 		1) Shall we add a 'AsOfDate' field, or keep using the 'PeriodEndDate'?

# 		If we add an 'AsOfDate' field for all database documents for which
# 		this field makes sense, then in the future it can make our query more
# 		standardized, since we are going to have lots of queries that require
# 		the as of date for something.

# 		To do this, we need to use a consistent format for this AsOfDate, 
# 		maybe the 'date' type of MongoDB?

# 		2) Shall we add a '_id' field to prevent saving identical positions 
# 		into the MongoDB?

# 		Say we run this function twice on the same file. Then we will have two 
# 		identical sets of records except their "_id" fields. Maybe we should 
# 		add an '_id' field to avoid this.
		
# 		Idealy, there is be no more than one document for a position if:

# 		1) It's a position record from Geneva system;
# 		2) For any particular security;
# 		3) For any particular portfolio;
# 		4) For any particular date;
	
# 		So:

# 		_id = 'geneva' + portfolio id + date + invest id?
# 	"""
# 	addNewFields = lambda p: mergeDict(
# 		p
# 	  , {'DataSource': 'geneva', 'RecordType': 'position'}
# 	)


# 	return 0
# End of saveGenevaPositionToDB()



def lognContinue(msg, x):
	logger.debug(msg)
	return x


def lognRaise(msg):
	logger.error(msg)
	raise ValueError