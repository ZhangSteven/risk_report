# coding=utf-8
#
# Asset allocation logic for SFC
# 
from risk_report.lqa import getBlpIdnType, getGenevaIdnType
from risk_report.geneva import isGenevaPosition, getGenevaPortfolioId, getGenevaFundType \
							, isGenevaFund, isGenevaFxForward, isGenevaCash \
							, isGenevaRepo, isGenevaMoneyMarket, isGenevaPrivateSecurity
from risk_report.blp import getBlpPortfolioId, getBlpFundType, isBlpFund, isBlpFxForward \
							, isBlpCash, isBlpRepo, isBlpMoneyMarket, isBlpPrivateSecurity
from utils.excel import getRawPositions, fileToLines
from utils.iter import pop, firstOf
from utils.utility import mergeDict
from toolz.functoolz import compose
from functools import partial, lru_cache
from itertools import filterfalse, takewhile
import logging
logger = logging.getLogger(__name__)



def byCountryGroup(blpData, countryGroup, positions):
	"""
	[Dictionary] blpData, [String] countryGroup, [Iterator] positions
		=> [Iterator] positions from that country group
	"""
	# [Dictionary] blpData, [Dictionary] position => [String] country code
	toCountryGroup = compose(
		lambda code: \
			loadCountryGroupMappingFromFile('SFC_Country.xlsx')[code] \
			if code in loadCountryGroupMappingFromFile('SFC_Country.xlsx') else \
			lognRaise('toCountryGroup(): unsupported country code: {0}'.format(code))
	  , getCountryCode
	)


	matchCountryGroup = lambda blpData, countryGroup, position: \
		countryGroup.lower().startswith(toCountryGroup(blpData, position).lower())


	return filter(partial(matchCountryGroup, blpData, countryGroup), positions)
# End of byCountryGroup



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



def getAssetType(blpData, position):
	"""
	[Dictionary] position (a Geneva or Blp position)
		=> [Tuple] asset type

	The asset type is a tuple containing the category and sub category, like
	('Cash', ), ('Fixed Income', 'Corporate') or ('Equity', 'Listed')
	"""
	logger.debug('getAssetType(): {0}'.format(getIdnType(position)))



	
	return \
	getSpecialCaseAssetType(position) if isSpecialCase(position) else \
	getPrivateSecurityAssetType(position) if isPrivateSecurity(position) else \
	('Cash', ) if isCash(position) else \
	('Foreign Exchange Derivatives', ) if isFxForward(position) else \
	('Fixed Income', 'Cash Equivalents') if isMoneyMarket(position) else \
	getRepoAssetType(position) if isRepo(position) else \
	getFundType(position) if isFund(position) else \
	getOtherAssetType(blpData, position)
# End of getAssetType()



getFundType = lambda position: \
	getGenevaFundType(position) if isGenevaPosition(position) else \
	getBlpFundType(position)



# FIXME: add implementation
getRepoAssetType = lambda position: \
	lognRaise('getRepoAssetType(): not supported')



def getOtherAssetType(blpData, position):
	"""
	For Fixed Income or Equity asset type, use Bloomberg "MARKET_SECTOR_DES" 
	field to lookup:

	If the field is "Equity", then asset class = "Equity", sub category
	"Listed Equity" if Bloomberg field "EXCH_MARKET_STATUS" = "ACTV", else
	sub category "Unlisted Equity".

	If the field is "Comdty", then asset type = ('Commodity', 'Derivatives')

	Otherwise its Bloomberg field "CAPITAL_CONTINGENT_SECURITY" 
	= "Y", then asset class is:

	('Fixed Income', 'Additional Tier 1, Contingent Convertibles')

	Else use the below mapping

	Corp -> Fixed Income, sub catetory "Corporate Bond"
	Govt -> Fixed Income, sub catetory "Government Bond"
	"""
	isEquityType = lambda blpData, position: \
		blpData[getIdnType(position)[0]]['MARKET_SECTOR_DES'] == 'Equity'


	isCommodityType = lambda blpData, position: \
		blpData[getIdnType(position)[0]]['MARKET_SECTOR_DES'] == 'Comdty'


	isFIType = lambda blpData, position: \
		blpData[getIdnType(position)[0]]['MARKET_SECTOR_DES'] in ['Corp', 'Govt']


	isCapitalContingentSecurity = lambda blpData, position: \
		blpData[getIdnType(position)[0]]['CAPITAL_CONTINGENT_SECURITY'] == 'Y'


	# FIXME: this function is not complete, as index futures are not included
	getEquityAssetType = lambda blpData, position: \
		('Equity', 'Listed Equities') if blpData[getIdnType(position)[0]]['EXCH_MARKET_STATUS'] == 'ACTV' \
		else ('Equity', 'Unlisted Equities')


	# FIXME: this function is not complete, as physical commodity is not included
	getCommodityAssetType = lambda blpData, position: \
		('Commodity', 'Derivatives')


	getFIAssetType = lambda blpData, position: \
		('Fixed Income', 'Additional Tier 1, Contingent Convertibles') \
		if isCapitalContingentSecurity(blpData, position) else \
		('Fixed Income', 'Corporate') if blpData[getIdnType(position)[0]]['MARKET_SECTOR_DES'] == 'Corp' else \
		('Fixed Income', 'Government') if blpData[getIdnType(position)[0]]['MARKET_SECTOR_DES'] == 'Govt' else \
		lognRaise('getFIAssetType(): unsupported FI type {0}'.format(getIdnType(position)))


	return \
	getEquityAssetType(blpData, position) if isEquityType(blpData, position) else \
	getCommodityAssetType(blpData, position) if isCommodityType(blpData, position) else \
	getFIAssetType(blpData, position) if isFIType(blpData, position) else \
	lognRaise('getOtherAssetType(): invalid asset type: {0}'.format(getIdnType(position)))



def getPrivateSecurityAssetType(position):
	"""
	[Dictionary] position => [Tuple] Asset Type

	Handle special cases for private securities
	"""
	# FIXME: add implementation
	logger.debug('getPrivateSecurityAssetType()')
	raise ValueError



""" [Dictionary] position => [Tuple] asset type """
getSpecialCaseAssetType = lambda position: \
	loadAssetTypeSpecialCaseFromFile('AssetType_SpecialCase.xlsx')[getIdnType(position)[0]]['AssetType']



def isSpecialCase(position):
	"""
	[Dictionary] position => [Bool] is this a special case in asset type,
								private security, open ended fund or something
								that needs override.
	"""
	portfolioMatched = lambda p1, p2: True if p2 == '' or p1 == p2 else False

	return compose(
		lambda t: t[0] in t[2] and portfolioMatched(t[1], t[2][t[0]]['Portfolio'])
	  , lambda position: ( getIdnType(position)[0]
	  					 , getPortfolioId(position)
	  					 , loadAssetTypeSpecialCaseFromFile('AssetType_SpecialCase.xlsx')
	  					 )
	)(position)


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



def getCountryCode(blpData, position):
	"""
	[Dictionary] blpInfo, [Dictionary] position => [String] country code
	"""
	logger.debug('getCountryCode(): {0}'.format(getIdnType(position)))

	isCommodityType = lambda blpData, position: \
		getAssetType(blpData, position)[0] == 'Commodity'


	isFundType = lambda blpData, position: \
		getAssetType(blpData, position)[0] == 'Fund'


	isEquityType = lambda blpData, position: \
		getAssetType(blpData, position)[0] == 'Equity'


	isFIType = lambda blpData, position: \
		getAssetType(blpData, position)[0] == 'Fixed Income'


	return \
	getPrivateSecurityCountry(position) if isPrivateSecurity(position) else \
	getRepoCountry(position) if isRepo(position) else \
	getMoneyMarketCountry(position) if isMoneyMarket(position) else \
	getCommodityCountry(blpData, position) if isCommodityType(blpData, position) else \
	getFundCountry(blpData, position) if isFundType(blpData, position) else \
	getEquityCountry(blpData, position) if isEquityType(blpData, position) else \
	getFICountry(blpData, position) if isFIType(blpData, position) else \
	lognRaise('getCountryCode(): unsupported asset type')



def getEquityCountry(blpData, position):
	"""
	[Dictionary] blpData, [Dictionary] position => [String] country
	"""
	logger.debug('getEquityCountry()')
	return blpData[getIdnType(position)[0]]['CNTRY_ISSUE_ISO']



def getFICountry(blpData, position):
	"""
	[Dictionary] blpData, [Dictionary] position => [String] country
	"""
	logger.debug('getFICountry()')
	return blpData[getIdnType(position)[0]]['CNTRY_OF_RISK']



def getPrivateSecurityCountry(position):
	"""
	[Dictionary] position => [String] country

	A private security is a non-listed security, non-listed fund or others
	that cannot find their information through Bloomberg. So we deal with them
	here.
	"""
	# FIXME: Add implementation
	lognRaise('getPrivateSecurityCountry(): {0}'.format(getIdnType(position)))



def getRepoCountry(position):
	"""
	[Dictionary] position => [String] country

	A repo position is an OTC product, so we deal with them here.
	"""
	# FIXME: Add implementation
	lognRaise('getRepoCountry(): {0}'.format(getIdnType(position)))



def getMoneyMarketCountry(position):
	"""
	[Dictionary] position => [String] country

	A money market product can be an OTC product, for example, a fixed deposit,
	so we deal with them here.
	"""
	# FIXME: Add implementation
	lognRaise('getMoneyMarketCountry(): {0}'.format(getIdnType(position)))



def getCommodityCountry(blpData, position):
	"""
	[Dictionary] blpData, [Dictionary] position => [String] country

	The logic to deal with commodity product is not yet clear, so we put it
	here.
	"""
	# FIXME: Add implementation
	lognRaise('getCommodityCountry(): {0}'.format(getIdnType(position)))



def getFundCountry(blpData, position):
	"""
	[Dictionary] blpData, [Dictionary] position => [String] country

	The logic to deal with fund, no matter listed fund (ETF) or open ended fund,
	is not yet clear, so we put it here.
	"""
	# FIXME: Need a formal implementation, now just case by case
	fundCountry = { '2823 HK Equity': 'HK'	# iShares FTSE A50 China ETF
				  , '823 HK Equity': 'HK'	# LINK REITs
				  }

	try:
		return fundCountry[getIdnType(position)[0]]
	except KeyError:
		lognRaise('getFundCountry(): {0}'.format(getIdnType(position)))



def getAverageRatingScoreSpecialCase(position):
	"""
	[Dictionary] position => [Float] score

	When none of the rating agencies gives a credit rating, we provide the 
	ratings here.

	The current implementation gives a rating score of 0 in such case.
	"""
	logger.warning('getAverageRatingScoreSpecialCase(): {0}'.format(getIdnType(position)))
	return 0



def getAverageRatingScore(blpData, position, specialCaseHandler=getAverageRatingScoreSpecialCase):
	"""
	[Dictionary] blpData, [Dictionary] position
		=> [Float] score
	"""
	logger.debug('getAverageRatingScore(): {0}'.format(getIdnType(position)))

	averageScore = lambda position, scores: \
		specialCaseHandler(position) if len(scores) == 0 else \
		scores[0] if len(scores) == 1 else \
		min(scores) if len(scores) == 2 else \
		sorted(scores)[1]


	return \
	compose(
		partial(averageScore, position)
	  , lambda scores: list(filterfalse(lambda x: x == 0, scores))
	  , getRatingScores
	)(blpData, position)



"""
	[Dictionary] blpData, [Dictionary] position
		=> [Tuple] ( S&P Rating score
				   , Moody's Rating score
				   , Fitch Rating score
				   )
"""
getRatingScores = lambda blpData, position: \
	( getRatingScore('S&P', blpData[getIdnType(position)[0]]['RTG_SP'])
	, getRatingScore('Moody\'s', blpData[getIdnType(position)[0]]['RTG_MOODY'])
	, getRatingScore('Fitch', blpData[getIdnType(position)[0]]['RTG_FITCH'])
	)



"""
	[String] agency, [String] rating => [Float] rating score
"""
getRatingScore = lambda agency, rating: \
	0 if rating.startswith('#N/A') else \
	loadRatingScoreMappingFromFile('RatingScore.xlsx')[(agency, rating)]



@lru_cache(maxsize=32)
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



@lru_cache(maxsize=32)
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



@lru_cache(maxsize=32)
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



"""
	[Dictionary] blpData, [Dictionary] position
			=> [Bool] is investment grade position
"""
isInvestmentGrade = lambda blpData, position: \
	False if getAverageRatingScore(blpData, position) < 12 else True



"""
	[Dictionary] blpData, [Dictionary] position
			=> [Bool] is investment financial industry
"""
isFinancial = lambda blpData, position: \
	True if blpData[getIdnType(position)[0]]['INDUSTRY_SECTOR'] == 'Financial' else False



""" 
	[Dictionary] blpData, [Dictionary] position
			=> [Bool] is SFC Authorized Fund
"""
isSFCAuthorized = lambda blpData, position: \
	True if blpData[getIdnType(position)[0]]['SFC_AUTHORIZED_FUND'] == 'Y' else False



"""
	[Dictionary] blpData, [Dictionary] position 
		=> [Bool] does country apply to this position
"""
countryNotApplicable = lambda blpData, position: \
	getAssetType(blpData, position)[0] in ['Cash', 'Foreign Exchange Derivatives']



"""
	[Dictionary] blpData, [String] countryGroup 
		=> [Function] f ([Iterator] positions -> [Iterator] positions)

	Taking the blpData and countryGroup, return a filter function that filters
	out positions from the particular country group.
"""
byCountryFilter = lambda blpData, countryGroup: \
	compose(
		lambda positions: byCountryGroup(blpData, countryGroup, positions)
	  , partial(filterfalse, partial(countryNotApplicable, blpData))
	)



byAssetTypeFilter = lambda blpData, *assetTypeStrings: \
	byAssetTypeFilterTuple(blpData, tuple(assetTypeStrings))
	


def byAssetTypeFilterTuple(blpData, assetTypeStringTuple):
	"""
	[Dictionary] blpData, [Tuple] (tier1 type string, tier 2 type string, ...)
		=> [Function] f ([Iterator] positions -> [Iterable] positions)

	Returns a filter function that filters out positions with type specified by
	the type strings in the tuple. For example, if the tuple is like:

		('Fixed Income', 'Corporate', 'Investment Grade', 'Financial Institution')

	Then we return a filter function that filters all positions that are 
	listed equities and belong to Financial	industry sector.
	"""
	attributeFilter = \
	{ 'investment grade': partial(filter, partial(isInvestmentGrade, blpData))
	, 'non-investment grade': partial(filterfalse, partial(isInvestmentGrade, blpData))
	, 'financial': partial(filter, partial(isFinancial, blpData))
	, 'non-financial': partial(filterfalse, partial(isFinancial, blpData))
	, 'sfc authorized': partial(filter, partial(isSFCAuthorized, blpData))
	, 'non-sfc authorized': partial(filterfalse, partial(isSFCAuthorized, blpData))
	}

	getFilter = compose(
		partial(firstOf, lambda f: f != None)
	  , lambda assetString: map( lambda key: \
	  								attributeFilter[key] if assetString.lower().startswith(key) else None
	  						   , attributeFilter.keys()
	  						   )
	)


	return \
	partial(filter, lambda _: True) if len(assetTypeStringTuple) == 0 else \
	compose( getFilter(assetTypeStringTuple[-1])
		   , byAssetTypeFilterTuple(blpData, assetTypeStringTuple[0:-1])
		   ) \
	if getFilter(assetTypeStringTuple[-1]) != None else \
	byAssetTypeOnlyFilterTuple(blpData, assetTypeStringTuple)



def byAssetTypeOnlyFilterTuple(blpData, assetTypeStringTuple):
	"""
	[Dictionary] blpData, [Tuple] (tier1 type string, tier 2 type string, ...)
		=> [Function] f ([Iterator] positions -> [Iterable] positions)

	Returns a filter function that filters out positions with type specified by
	the type strings in the tuple. For example, if the tuple is like:

		('Equity', 'Listed Equities')

	Then we return a filter function that takes positions with the asset type
	string matching the above.

	The difference between this function and byAssetTypeFilter() is that the
	latter also 
	"""
	matched = lambda t: t[0].lower().startswith(t[1].lower())

	compareStringTuple = lambda t1, t2: \
		False if len(t1) > len(t2) else all(map(matched, zip(t1, t2)))


	inner = lambda blpData, assetTypeStringTuple, position: \
		compareStringTuple(assetTypeStringTuple, getAssetType(blpData, position))


	return \
	partial(filter, lambda _: True) if len(assetTypeStringTuple) == 0 else \
	partial(filter, partial(inner, blpData, assetTypeStringTuple))



def lognContinue(msg, x):
	logger.debug(msg)
	return x


def lognRaise(msg):
	logger.error(msg)
	raise ValueError