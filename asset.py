# coding=utf-8
#
# Asset allocation logic for SFC
# 
from risk_report.lqa import getBlpIdnType, getGenevaIdnType
from clamc_datafeed.feeder import getRawPositions, fileToLines
from utils.iter import pop
from toolz.functoolz import compose
from functools import partial, lru_cache
from itertools import filterfalse, takewhile
import logging
logger = logging.getLogger(__name__)



"""
	[Dictionary] blpData, [String] countryCode, [Iterator] positions
		=> [Bool] is position's country Code matches the countryCode passed in
"""
# fromCountry = lambda blpData, countryCode, position: \
# 	countryCode == getCountry(blpData, position)
	


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
		toCountryGroup(blpData, position).lower() == countryGroup.lower()


	return filter(partial(matchCountryGroup, blpData, countryGroup), positions)
# End of byCountryGroup



isPrivateSecurity = lambda position: \
	False if isGenevaPosition(position) else position['Name'].startswith('.') 



isCash = lambda position: \
	position['SortKey'] == 'Cash and Equivalents' if isGenevaPosition(position) \
	else position['Asset Type'] == 'Cash'



isMoneyMarket = lambda position: \
	position['SortKey'] == 'Fixed Deposit' if isGenevaPosition(position) \
	else position['Asset Type'] == 'Money Market'



isRepo = lambda position: \
	False if isGenevaPosition(position) \
	else position['Asset Type'] == 'Repo Liability'



isFxForward = lambda position: \
	position['SortKey'] == 'FX Forward' if isGenevaPosition(position) \
	else position['Asset Type'] == 'Foreign Exchange Forward'



isFund = lambda position: \
	position['SortKey'] in ['Open-End Fund', 'Exchange Trade Fund', 'Real Estate Investment Trust'] \
	if isGenevaPosition(position) else position['Industry Sector'] == 'Funds'



def getAssetType(blpData, position):
	"""
	[Dictionary] position (a Geneva or Blp position)
		=> [Tuple] asset type

	The asset type is a tuple containing the category and sub category, like
	('Cash', ), ('Fixed Income', 'Corporate') or ('Equity', 'Listed')
	"""
	logger.debug('getAssetType(): {0}'.format(getIdnType(position)))

	getFundType = lambda position: \
		getGenevaFundType(position) if isGenevaPosition(position) else \
		getBlpFundType(position)


	# NOTE: Geneva does not book repo yet
	isRepo = lambda position: \
		False if isGenevaPosition(position) else position['Asset Type'].startswith('Repo')

	# FIXME: add implementation
	getRepoAssetType = lambda position: \
		lognRaise('getRepoAssetType(): not supported')

	
	return \
	getPrivateSecurityAssetType(position) if isPrivateSecurity(position) else \
	('Cash', ) if isCash(position) else \
	('Foreign Exchange Derivatives', ) if isFxForward(position) else \
	('Fixed Income', 'Cash Equivalents') if isMoneyMarket(position) else \
	getRepoAssetType(position) if isRepo(position) else \
	getFundType(position) if isFund(position) else \
	getOtherAssetType(blpData, position)
# End of getAssetType()



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



def getBlpFundType(position):
	"""
	[Dictionary] position => [Tuple] Asset Class

	If position is a fund type in Bloomberg, output its exact fund type
	"""
	# FIXME: Add implementation
	lognRaise('getBlpFundType(): {0}'.format(getIdnType(position)))



def getGenevaFundType(position):
	"""
	[Dictionary] position => [Tuple] Asset Class

	If position is a fund type in Geneva, output its exact fund type
	"""
	def getGenevaOpenFundType(position):
		# FIXME: Add mapping for open end fund here, what's the fund type
		# for DIF?
		# fMap = {'CLFLDIF HK': ('Fund', 'Other Funds')}
		fMap = {}
		try:
			return fMap[position['InvestID']]
		except KeyError:
			lognRaise('getGenevaOpenFundType(): invalid position: {0}'.format(getIdnType(position)))


	return \
	('Fund', 'Exchange Traded Funds') if position['SortKey'] == 'Exchange Trade Fund' else \
	('Fund', 'Real Estate Investment Trusts') if position['SortKey'] == 'Real Estate Investment Trust' else \
	getGenevaOpenFundType(position) if position['SortKey'] == 'Open-End Fund' else \
	lognRaise('getGenevaFundType(): invalid position: {0}'.format(getIdnType(position)))



def getPrivateSecurityAssetType(position):
	"""
	[Dictionary] position => [Tuple] Asset Type

	Handle special cases for private securities
	"""
	# FIXME: add implementation
	logger.debug('getPrivateSecurityAssetType()')
	raise ValueError



isGenevaPosition = lambda p: p['Remarks1'].lower().startswith('geneva')



"""
	[Dictionary] position (a Geneva or Blp position)
		=> [Tuple] (id, idType)
"""
getIdnType = lambda position: \
	getGenevaIdnType(position) if isGenevaPosition(position) else \
	getBlpIdnType(position)



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
	  , partial(map, lambda line: (line[0], line[2]))
	  , partial(takewhile, lambda line: len(line) > 2 and line[0] != '')
	  , lambda t: t[1]
	  , lambda lines: (pop(lines), lines)
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



def lognContinue(msg, x):
	logger.debug(msg)
	return x


def lognRaise(msg):
	logger.error(msg)
	raise ValueError