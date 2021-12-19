# coding=utf-8
#
# Functions related to data retrieving are grouped here.
# 
from risk_report.utility import getInputDirectory, getDataDirectory
from risk_report.blp import getBlpPortfolioId, getBlpPositionDate, getBlpMarketValue \
							, getBlpBookCurrency, getBlpPortfolioId, getBlpIdnType \
							, getBlpQuantity, isBlpPrivateSecurity, isBlpRepo \
							, isBlpMoneyMarket, isBlpCash, isBlpFxForward, isBlpFund
from risk_report.geneva import isGenevaPosition, getGenevaPortfolioId, getGenevaPositionDate \
							, getGenevaMarketValue, getGenevaBookCurrency, getGenevaPortfolioId \
							, getGenevaIdnType, getGenevaAssetType, isGenevaFund, isGenevaFxForward, isGenevaCash \
							, isGenevaRepo, isGenevaMoneyMarket, isGenevaPrivateSecurity \
							, getGenevaQuantity
from clamc_datafeed.feeder import getPositions
from steven_utils.excel import getRawPositionsFromLines, fileToLines, getRawPositionsFromFile \
							, fromExcelOrdinal
from steven_utils.iter import pop, firstOf
from steven_utils.utility import mergeDict
from toolz.functoolz import compose
from toolz.dicttoolz import valmap
from functools import partial, lru_cache
from itertools import filterfalse, takewhile, dropwhile, chain
from datetime import datetime
from os.path import join
import logging
logger = logging.getLogger(__name__)



getCountryMapping = lambda: loadCountryGroupMappingFromFile('SFC_Country.xlsx')


getRatingScoreMapping = lambda: loadRatingScoreMappingFromFile('RatingScore.xlsx')


getAssetTypeSpecialCaseData = lambda: loadAssetTypeSpecialCaseFromFile('AssetType_SpecialCase.xlsx')


""" [String] date (yyyymmdd), [String] mode => [Dictionary] id -> [Dictionary] data """
getLiquiditySpecialCaseData = lambda date, mode: \
	loadLiquiditySpecialCaseFromFile(getLiquiditySpecialCaseFile(date, mode))



"""
	[String] portfolio, [String] date (yyyymmdd), [String] mode
		=> [Iterator] positions of the portfolio 
"""
getPortfolioPositions = lambda portfolio, date, mode='production': \
	getAllPositions(date, mode) if portfolio.lower() == 'all' else \
	getGenevaPositions(portfolio, date, mode) if portfolio in ['19437', '60001'] else \
	getBlpPositions(portfolio, date, mode)



@lru_cache(maxsize=3)
def getBlpData(date, mode='production'):
	"""
	[String] date (yyyymmdd), [String] mode
		=> [Dictionary] meta data of the positions 
	"""
	getBlpDataFile = lambda date, mode: \
		join(getInputDirectory(mode), 'BlpData_' + date + '.xlsx')


	return \
	compose(
		dict
	  , partial(map, lambda p: (p['ID'], p))
	  , getRawPositionsFromFile
	  , getBlpDataFile
	)(date, mode)



@lru_cache(maxsize=3)
def getLqaData(date, mode='production', separator='|'):
	"""
	[String] date (yyyymmdd), [String] mode
		=> [Dictionary] id -> lqa data (dictionary)
	"""
	def fileToLines(file):
		with open(file, 'r') as lqaFile:
			for line in lqaFile:
				yield line.strip()


	getLqaDataFile = lambda date, mode: \
		join(getInputDirectory(mode), 'LqaData_' + date + '.bbg')


	toPosition = lambda headers, line: dict(zip(headers, line))

	# Take the lines between 'START-OF-DATA' and 'END-OF-DATA'
	takeInBetween = compose(
		lambda t: takewhile(lambda L: L[0] != 'END-OF-DATA', t[1])
	  , lambda lines: (pop(lines), lines)
	  , partial(dropwhile, lambda L: len(L) == 0 or L[0] != 'START-OF-DATA')
	)


	"""
	The below functions: 

	1. stipDoubleQuote()
	2. toNumberOrStripQuote()
	3. updateSecurityId()

	They are used to clean the data. Because sometimes the string data are 
	enclosed by a pair of double quotes, we need to removed. The float numbers
	may be read as string and sometimes we have security ids like "XS1234567890 PerfShs"
	and we need to take only the first part.
	"""
	stipDoubleQuote = lambda s: s.replace('"', '')


	def toNumberOrStripQuote(x):
		try:
			return float(x)
		except:
			return stipDoubleQuote(x)


	def updateSecurityId(p):
		if len(p['SECURITIES'].split()[0]) == 12: # it's ISIN
			return mergeDict(p, {'SECURITIES': p['SECURITIES'].split()[0]})
		else:
			return p


	return \
	compose(
		dict
	  , partial(map, lambda p: (p['SECURITIES'], p))
	  , partial(map, updateSecurityId)
	  , partial(map, partial(valmap, toNumberOrStripQuote))
	  , lambda t: map(partial(toPosition, t[0]), t[1])
	  , lambda lines: (list(map(stipDoubleQuote, pop(lines))), lines)
	  , takeInBetween
	  , partial(map, lambda line: line.split(separator))
	  , fileToLines
	  , lambda file: lognContinue('getLqaData(): from file: {0}'.format(file), file)
	  , getLqaDataFile
	)(date, mode)



""" [Float] excel date value => [String] date string (yyyymmdd) """
toDateString = lambda x: datetime.strftime(fromExcelOrdinal(x), '%Y%m%d')



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
	return \
	compose(
		partial(mergeDict, {targetCurrency: 1.0})
	  , dict
	  , partial(map, lambda p: (p['Currency'], p['FX']))
	  , partial( filter
	  		   , lambda p: toDateString(p['Date']) == date and p['Reporting Currency'] == targetCurrency
	  		   )
	  , getRawPositionsFromFile
	  , partial(join, getDataDirectory())
	)('FX.xlsx')



@lru_cache(maxsize=3)
def getLiquidityOverrideOnDate(date):
	"""
	[String] date (yyyymmdd) => [Dictionary] securityId -> liquidity category

	"""
	return \
	compose(
		dict
	  , partial(map, lambda t: (t[0][1], t[1]))
	  , partial(filter, lambda t: t[0][0] == date)
	  , lambda d: d.items()
	)(getLiquidityOverrideFromFile('Liquidity_Override.xlsx'))



@lru_cache(maxsize=3)
def getLiquidityOverrideFromFile(file):
	"""
	[String] file => [Dictionary] (date, securityId) -> liquidity category
	"""
	return \
	compose(
		dict
	  , partial( map
	  		   , lambda p: ( (toDateString(p['Date']), p['SecurityId'])
	  		   			   , p['Liquidity']
	  					   ))
	  , getRawPositionsFromFile
	  , partial(join, getDataDirectory())
	)(file)



getPositionDate = lambda position: \
	getGenevaPositionDate(position) if isGenevaPosition(position) else \
	getBlpPositionDate(position)



getQuantity = lambda position: \
	getGenevaQuantity(position) if isGenevaPosition(position) else \
	getBlpQuantity(position)



"""
	[Dictionary] position 
		=> [Float] market value of the position, in the portfolio's book
			currency
	
	# FIXME: is it true for Bloomberg positions?
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



"""
	[Dictionary] position (a Geneva or Blp position)
		=> [Tuple] (id, idType)
"""
getIdnType = lambda position: \
	getGenevaIdnType(position) if isGenevaPosition(position) else \
	getBlpIdnType(position)



"""
	[Dictionary] position (a Geneva or Blp position)
		=> [String] portfolio Id
"""
getPortfolioId = lambda position: \
	getGenevaPortfolioId(position) if isGenevaPosition(position) else \
	getBlpPortfolioId(position)



isPrivateSecurity = lambda position: \
	isGenevaPrivateSecurity(position) if isGenevaPosition(position) else isBlpPrivateSecurity(position)



isCash = lambda position: \
	isGenevaCash(position) if isGenevaPosition(position) else isBlpCash(position)



isMoneyMarket = lambda position: \
	isGenevaMoneyMarket(position) if isGenevaPosition(position) else isBlpMoneyMarket(position) 



isRepo = lambda position: \
	isGenevaRepo(position) if isGenevaPosition(position) else isBlpRepo(position)



isFxForward = lambda position: \
	isGenevaFxForward(position) if isGenevaPosition(position) else isBlpFxForward(position)



isFund = lambda position: \
	isGenevaFund(position) if isGenevaPosition(position) else isBlpFund(position)



def getAllPositions(date, mode='production'):
	"""
	[String] date (yyyymmdd), [String] mode
		=> [Iterator] positions of all portfolios on the date

	At the moment, we load DIF (19437) positions from Geneva and other
	portfolios from Bloomberg.
	"""
	return \
	chain(
		getGenevaPositions('19437', date, mode)
	  , filterfalse( lambda p: getBlpPortfolioId(p).startswith('19437')
	  			   , getAllPositionsBlp(date, mode)
	  			   )
	)



def getAllPositionsBlp(date, mode):
	"""
	[String] date (yyyymmdd), [String] mode
		=> [Iterator] positions of all portfolios on the date from Bloomberg
	"""
	getBlpPositionFile = lambda date, mode: \
		join(getInputDirectory(mode), 'risk_m2_mav_' + date + '.xlsx')


	# [Iterable] lines => [List] line that contains the date
	findDateLine = partial(
		firstOf
	  , lambda line: len(line) > 1 and line[1].startswith('Risk-Mon Steven')
	)


	# [String] The string containing date => [String] date (yyyymmdd)
	# it looks like: Risk Report LQA Master as of 20200429
	getDateFromString = lambda s: s.split()[-1]


	getDateFromLines = compose(
		getDateFromString
	  , lambda line: lognRaise('Failed to find date line') if line == None else line[1]
	  , findDateLine
	)


	floatToString = lambda x: str(int(x)) if isinstance(x, float) else x


	updatePosition = lambda date, position: \
		mergeDict( position
				 , { 'AsOfDate': date
				   , 'Remarks1': 'Bloomberg MAV Risk-Mon Steven'
				   , 'Account Code': floatToString(position['Account Code']) 
				   }
				 )


	getPositions = lambda date, lines: \
	compose(
		partial(map, partial(updatePosition, date))
	  , partial(filterfalse, lambda p: p['Account Code'] == '')
	  , getRawPositionsFromLines
	  , lambda lines: dropwhile(lambda line: line[0] != 'Name', lines)
	)(lines)


	return \
	compose(
		lambda t: getPositions(t[0], t[1])
	  , lambda lines: (getDateFromLines(lines), lines)
	  , fileToLines
	  , lambda file: lognContinue('getAllPositionsBlp(): {0}'.format(file), file)
	  , getBlpPositionFile
	)(date, mode)



getBlpPositions = lambda portfolio, date, mode: \
	filter( lambda p: getBlpPortfolioId(p) == portfolio
		  , getAllPositionsBlp(date, mode))



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
  	  , partial(join, getDataDirectory())
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
  	  , partial(join, getDataDirectory())
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
	  , partial(join, getDataDirectory())
	)(file)



getLiquiditySpecialCaseFile = lambda date, mode: \
	join(getInputDirectory(mode), 'Liquidity_SpecialCase_' + date + '.xlsx')



@lru_cache(maxsize=3)
def loadLiquiditySpecialCaseFromFile(file):
	"""
	[String] file => [Dictionary] id -> [Dictionary] liquidity data
	"""
	toDate = lambda x: \
		fromExcelOrdinal(x) if isinstance(x, float) else \
		datetime.strptime(x, '%m/%d/%Y')


	updatePosition = lambda position: mergeDict(
		position
	  , {'CALC_MATURITY': toDate(position['CALC_MATURITY'])}
	)


	return \
	compose(
		dict
	  , partial(map, lambda p: (p['ID'], p))
	  , partial(map, updatePosition)
	  , getRawPositionsFromFile
	)(file)



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