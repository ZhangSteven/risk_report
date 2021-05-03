# coding=utf-8
#
# Asset allocation logic for SFC
# 
from risk_report.geneva import isGenevaPosition, getGenevaAssetType
from risk_report.data import getRatingScoreMapping, getCountryMapping, getAssetTypeSpecialCaseData \
							, getPortfolioId, getIdnType, isPrivateSecurity, isCash \
							, isMoneyMarket, isRepo, isFxForward, isFund
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
	matchCountryGroup = lambda blpData, countryGroup, position: \
		countryGroup.lower().startswith(toCountryGroup(blpData, position).lower())


	return filter(partial(matchCountryGroup, blpData, countryGroup), positions)
# End of byCountryGroup



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
	getFundAssetType(position) if isFund(position) else \
	getOtherAssetType(blpData, position)
# End of getAssetType()



def getFundAssetType(position):
	"""
		[Dictionary] position => [Tuple] Asset Type

		Assume: the position is already a fund
	"""
	toAssetTypeGeneva = lambda tp: \
		('Fund', 'Exchange Traded Funds') if tp == 'Exchange Trade Fund' else \
		('Fund', 'Real Estate Investment Trusts') if tp == 'Real Estate Investment Trust' else \
		lognRaise('toAssetTypeGeneva(): unsupported {0}'.format(tp))

	return \
	toAssetTypeGeneva(getGenevaAssetType(position)) if isGenevaPosition(position) \
	else lognRaise('getFundAssetType(): Bloomberg asset not supported yet')



# FIXME: add implementation
getRepoAssetType = lambda position: \
	('Others', )
	# lognRaise('getRepoAssetType(): not supported')



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
	# getCommodityAssetType = lambda blpData, position: \
	# 	('Commodity', 'Derivatives')


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



def getCommodityAssetType(blpData, position):
	# FIXME: add implementation. In 19437, they use US treasury futures
	# to hedge, but in Bloomberg those are classified as commondity futures,
	# actually they are better classified as others.
	return ('Others', )



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
	getAssetTypeSpecialCaseData()[getIdnType(position)[0]]['AssetType']



""" [Dictionary] position => [String] country """
getSpecialCaseCountry = lambda position: \
	getAssetTypeSpecialCaseData()[getIdnType(position)[0]]['CountryCode']



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
	  					 , getAssetTypeSpecialCaseData()
	  					 )
	)(position)



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


	isOthersType = lambda blpData, position: \
		getAssetType(blpData, position)[0] == 'Others'


	return \
	getSpecialCaseCountry(position) if isSpecialCase(position) else \
	getPrivateSecurityCountry(position) if isPrivateSecurity(position) else \
	getRepoCountry(position) if isRepo(position) else \
	getMoneyMarketCountry(position) if isMoneyMarket(position) else \
	getCommodityCountry(blpData, position) if isCommodityType(blpData, position) else \
	getFundCountry(blpData, position) if isFundType(blpData, position) else \
	getOthersCountry(blpData, position) if isOthersType(blpData, position) else \
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
	# FIXME: Assume HK as the repo country
	return 'HK'
	# lognRaise('getRepoCountry(): {0}'.format(getIdnType(position)))



def getMoneyMarketCountry(position):
	"""
	[Dictionary] position => [String] country

	A money market product can be an OTC product, for example, a fixed deposit,
	so we deal with them here.
	"""
	# FIXME: Assume all money market instruments are made in Hong Kong
	return lognContinue( 'getMoneyMarketCountry(): {0}'.format(getIdnType(position))
					   , 'HK')



def getCommodityCountry(blpData, position):
	"""
	[Dictionary] blpData, [Dictionary] position => [String] country

	The logic to deal with commodity product is not yet clear, so we put it
	here.
	"""
	# FIXME: not implemented
	lognRaise('getCommodityCountry(): {0}'.format(getIdnType(position)))



def getOthersCountry(blpData, position):
	"""
	[Dictionary] blpData, [Dictionary] position => [String] country

	The logic to deal with commodity product is not yet clear, so we put it
	here.
	"""
	_id, _id_type = getIdnType(position)
	if (_id, _id_type) == ('TYM1 Comdty', 'TICKER'):
		return 'US'
	else:
		# FIXME: Add implementation
		lognRaise('getCommodityCountry(): {0}'.format(getIdnType(position)))



def getFundCountry(blpData, position):
	"""
	[Dictionary] blpData, [Dictionary] position => [String] country

	The logic to deal with fund, no matter listed fund (ETF) or open ended fund,
	is not yet clear, so we put it here.
	"""
	# FIXME: Need a formal implementation, now just case by case
	fundCountry = {}

	try:
		return fundCountry[getIdnType(position)[0]]
	except KeyError:
		lognRaise('getFundCountry(): {0}'.format(getIdnType(position)))



"""
	[Dictionary] blpData, [Dictionary] position => [String] country group
"""
toCountryGroup = compose(
	lambda code: \
		getCountryMapping()[code] if code in getCountryMapping() else \
		lognRaise('toCountryGroup(): unsupported country code: {0}'.format(code))
  , getCountryCode
)



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
	0 if rating.startswith('#N/A') else getRatingScoreMapping()[(agency, rating)]



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

	# FIXME: rely on hardcoded special cases
"""
isSFCAuthorized = lambda blpData, position: \
	False if getIdnType(position)[0] == '.FSFUND HK Equity' else \
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



# byAssetTypeFilter = lambda blpData, *assetTypeStrings: \
# 	byAssetTypeFilterTuple(blpData, tuple(assetTypeStrings))
	


# def byAssetTypeFilterTuple(blpData, assetTypeStringTuple):
# 	"""
# 	[Dictionary] blpData, [Tuple] (tier1 type string, tier 2 type string, ...)
# 		=> [Function] f ([Iterator] positions -> [Iterable] positions)

# 	Returns a filter function that filters out positions with type specified by
# 	the type strings in the tuple. For example, if the tuple is like:

# 		('Fixed Income', 'Corporate', 'Investment Grade', 'Financial Institution')

# 	Then we return a filter function that filters all positions that are 
# 	listed equities and belong to Financial	industry sector.
# 	"""
# 	attributeFilter = \
# 	{ 'investment grade': partial(filter, partial(isInvestmentGrade, blpData))
# 	, 'non-investment grade': partial(filterfalse, partial(isInvestmentGrade, blpData))
# 	, 'financial': partial(filter, partial(isFinancial, blpData))
# 	, 'non-financial': partial(filterfalse, partial(isFinancial, blpData))
# 	, 'sfc authorized': partial(filter, partial(isSFCAuthorized, blpData))
# 	, 'non-sfc authorized': partial(filterfalse, partial(isSFCAuthorized, blpData))
# 	}

# 	getFilter = compose(
# 		partial(firstOf, lambda f: f != None)
# 	  , lambda assetString: map( lambda key: \
# 	  								attributeFilter[key] if assetString.lower().startswith(key) else None
# 	  						   , attributeFilter.keys()
# 	  						   )
# 	)


# 	return \
# 	partial(filter, lambda _: True) if len(assetTypeStringTuple) == 0 else \
# 	compose( getFilter(assetTypeStringTuple[-1])
# 		   , byAssetTypeFilterTuple(blpData, assetTypeStringTuple[0:-1])
# 		   ) \
# 	if getFilter(assetTypeStringTuple[-1]) != None else \
# 	byAssetTypeOnlyFilterTuple(blpData, assetTypeStringTuple)



# def byAssetTypeOnlyFilterTuple(blpData, assetTypeStringTuple):
# 	"""
# 	[Dictionary] blpData, [Tuple] (tier1 type string, tier 2 type string, ...)
# 		=> [Function] f ([Iterator] positions -> [Iterable] positions)

# 	Returns a filter function that filters out positions with type specified by
# 	the type strings in the tuple. For example, if the tuple is like:

# 		('Equity', 'Listed Equities')

# 	Then we return a filter function that takes positions with the asset type
# 	string matching the above.

# 	The difference between this function and byAssetTypeFilter() is that the
# 	latter also 
# 	"""
# 	matched = lambda t: t[0].lower().startswith(t[1].lower())

# 	compareStringTuple = lambda t1, t2: \
# 		False if len(t1) > len(t2) else all(map(matched, zip(t1, t2)))


# 	inner = lambda blpData, assetTypeStringTuple, position: \
# 		compareStringTuple(assetTypeStringTuple, getAssetType(blpData, position))


# 	return \
# 	partial(filter, lambda _: True) if len(assetTypeStringTuple) == 0 else \
# 	partial(filter, partial(inner, blpData, assetTypeStringTuple))



def fallsInAssetType(blpData, assetTypeTuple, position):
	"""
	[Tuple] assetTypeTuple, [Dictionary] position
		=> [Bool] does the position fall into the asset type described by 
					the asset type tuple

	An asssetTypeTuple will consist of asset type and (optional) relevant
	attributes, for example:

	('Equity', 'Listed equities')

	('Fixed Income', )

	('Fixed Income', 'Corporate', 'Investment Grade')

	('Fund', 'Exchange Traded Funds', 'SFC Authorized')
	"""
	assetTypeMatched = lambda t1, t2: \
		False if len(t1) > len(t2) else \
		all(map(lambda t: t[0].lower().startswith(t[1].lower()), zip(t1, t2)))


	attributeFunctions = \
	{ 'investment grade': partial(isInvestmentGrade, blpData)
	, 'non-investment grade': lambda p: not isInvestmentGrade(blpData, p)
	, 'financial': partial(isFinancial, blpData)
	, 'non-financial': lambda p: not isFinancial(blpData, p)
	, 'sfc authorized': partial(isSFCAuthorized, blpData)
	, 'non-sfc authorized': lambda p: not isSFCAuthorized(blpData, p)
	}


	# [String] string => [Function] f if string matches one of the attributes
	# else None
	getAttributeFunction = compose(
		partial(firstOf, lambda f: f != None)
	  , lambda s: map( lambda key: attributeFunctions[key] if s.lower().startswith(key) else None
	  		   		 , attributeFunctions.keys())
	)


	return \
	True if len(assetTypeTuple) == 0 else \
	fallsInAssetType(blpData, assetTypeTuple[:-1], position) and getAttributeFunction(assetTypeTuple[-1])(position) \
	if getAttributeFunction(assetTypeTuple[-1]) != None else \
	assetTypeMatched(assetTypeTuple, getAssetType(blpData, position))



def lognContinue(msg, x):
	logger.debug(msg)
	return x


def lognRaise(msg):
	logger.error(msg)
	raise ValueError