# coding=utf-8
#
# LQA related functions come here.
# 
# 1) Build LQA request
# 2) Read LQA response
# 

from risk_report.blp import readBlpFile
from risk_report.geneva import readGenevaFile
from clamc_datafeed.feeder import fileToLines
from utils.iter import pop
from functools import partial, reduce
from itertools import chain, filterfalse, dropwhile, takewhile
from toolz.functoolz import compose
from toolz.itertoolz import groupby as groupbyToolz
from utils.utility import mergeDict
from os.path import join
import logging
logger = logging.getLogger(__name__)



def getLqaData(lines):
	"""
	[Iterator] lines => [Dictionary] security id -> LQA result

	lines are from the LQA response (saved as Excel) from Bloomberg.
	"""
	toPosition = lambda headers, line: dict(zip(headers, line))

	# Take the lines between 'START-OF-DATA' and 'END-OF-DATA'
	takeInBetween = compose(
		lambda t: takewhile(lambda L: L[0] != 'END-OF-DATA', t[1])
	  , lambda lines: (pop(lines), lines)
	  , partial(dropwhile, lambda L: len(L) == 0 or L[0] != 'START-OF-DATA')
	)


	return compose(
		lambda positions: dict(map(lambda p: (p['SECURITIES'], p), positions))
	  , lambda t: map(partial(toPosition, t[0]), t[1])
	  , lambda lines: (pop(lines), lines)
	  , takeInBetween
	)(lines)



"""
	[String] file (LQA result in Excel File) => [Dictionary] LQA result
"""
readLqaDataFromFile = compose(
  	getLqaData
  , fileToLines
  , lambda file: lognContinue('readLqaDataFromFile(): {0}'.format(file), file)
)



def argumentsAsTuple(func):
	"""
	[Function] func => [Function] inner

	NOTE: CANNOT be used if func takes only one argument.

	A decorator function. When used to decorate another function (func), the
	function then takes a tuple as a single argument, unpack it and then calls
	func to return results.

	This can be handy in composing functions, becuase return values of the 
	previous function is passed to the next function in the form of a tuple 
	when multiple results are returned.
	"""
	def inner(t):
		return func(*t)

	return inner



def buildLqaRequestFromFiles(blpFile, genevaFile):
	"""
	[String] blpFile, [String] genevaFile
		=> ( [String] master list CLO csv file
		   , [STring] master list non-CLO csv file
		   )

	Side effect: create 2 LQA request files
	"""

	"""
		[String] file 
			=> ( [String] date (yyyy-mm-dd)
			   , [Iterable] clo
			   , [Iterable] nonCLO
			   )
	"""
	processBlpFile = compose(
		lambda t: (t[0], *getBlpLqaPositions(t[1]))
	  , readBlpFile
	)


	"""[String] file => ([String] date (yyyy-mm-dd), [Iterable] positions)"""
	processGenevaFile = compose(
		lambda t: (t[0], getGenevaLqaPositions(t[1]))
	  , readGenevaFile
	)


	processDatenPosition = lambda dt, clo, nonCLO, genevaPositions: \
		( buildLqaRequest( 'masterlist_nonCLO'
						 , dt
						 , consolidate(chain(nonCLO, genevaPositions))
						 )
		, buildLqaRequest('masterlist_CLO', dt, consolidate(clo))
		)


	checkDate = lambda d1, clo, nonCLO, d2, genevaPositions: \
  		lognRaise('inconsistent dates: {0}, {1}'.format(d1, d2)) \
  		if d1 != d2 else (d1, clo, nonCLO, genevaPositions)


	return compose(
		argumentsAsTuple(processDatenPosition)  
	  , argumentsAsTuple(checkDate)
	  , lambda blpFile, genevaFile: ( *processBlpFile(blpFile)
	  								, *processGenevaFile(genevaFile)
	  								)
	)(blpFile, genevaFile)



def investIdToLqaId(investId, assetType):
	"""
	[String] investId (InvestID field from Geneva reports)
	[String] assetType (Geneva asset type: common stock, corporate bond etc.)
		=> ( [String] lqa id,
		   , [String] lqa id type
		   )

	# FIXME: this function is incomplete, some assetType like open ended fund
	is not handled.
	"""
	ISINfromInvestID = lambda investId: \
		lognRaise('ISINfromInvestID(): failed to get ISIN from id: {0}'.format(investId)) \
		if len(investId) < 12 else investId[0:12]


	isEquityType = lambda assetType: \
		assetType in [ 'Common Stock', 'Real Estate Investment Trust'
					 , 'Stapled Security', 'Exchange Trade Fund']

	isBondType = lambda assetType: assetType.split()[-1] == 'Bond'


	return \
	(investId + ' Equity', 'TICKER') if isEquityType(assetType) else \
	(ISINfromInvestID(investId), 'ISIN') if isBondType(assetType) else \
	lognRaise('investIdToLqaId(): unsupported type: {0}'.format(assetType))



def noNeedLiquidityGeneva(position):
	"""
	[Dictionary] position => [Bool] no need to measure liquidity

	Certain positions do not need liquidity measure, 

	1. quantity = 0
	2. cash
	3. money market instruments
	4. open ended fund

	such as cash or money market instruments (fixed
	deposit), in this case this function return True. Otherwise False.
	"""
	return True \
	if position['Quantity'] == 0 or position['ThenByDescription'] in \
	['Cash and Equivalents', 'Fixed Deposit', 'Open-End Fund'] \
	else False



def getGenevaLqaPositions(positions):
	"""
	[Iterable] positions => [Iterable] positions

	Read Geneva consolidated tax lot positions, then do the following: 

	1) take out those not suitable for liquidity test (cash, FX forward, etc.);
	2) Add Id, IdType and Position fields for LQA processing.

	"""
	# addIdnType = lambda p: \
	# 	mergeDict(p, {'Id': p['InvestID'] + ' Equity', 'IdType': 'TICKER'}) \
	# 	if isEquityType(p['ThenByDescription']) else \
	#   	mergeDict(p, {'Id': ISINfromInvestID(p['InvestID']), 'IdType': 'ISIN'}) \
	#   	if isBondType(p['ThenByDescription']) else \
	#   	lognRaise('addIdnType(): unsupported type: {0}'.format(p['ThenByDescription']))

	# [Dictonary] p => [Dictionary] enriched position with id and idType
	addIdnType = compose(
		lambda t: mergeDict(t[2], {'Id': t[0], 'IdType': t[1]})
	  , lambda p: (*investIdToLqaId(p['InvestID'], p['ThenByDescription']), p)
	)


	# Add a field 'Postion', useful in consolidation with Bloommberg Lqa positions
	addPosition = lambda p: \
		mergeDict(p, {'Position': p['Quantity']})


	return compose(
		partial(map, addIdnType)
	  , partial(map, addPosition)
	  , partial(filterfalse, noNeedLiquidityGeneva)
	  , lambda positions: lognContinue('getGenevaLqaPositions(): start', positions)
	)(positions)



def getBlpLqaPositions(positions):
	"""
	[Iterable] positions => ( [Iterable] CLO positions
					 	    , [Iterable] nonCLO positions
					 	    )

	Read Bloomberg raw positions, then do the following: 

	1) take out those not suitable to do liquidity test (cash, FX forward, etc.);
	2) take out DIF fund positions, since they will come from Geneva;
	2) split into clo and nonCLO positions.

	Return (CLO positions, nonCLO positions)
	"""
	removeUnwantedPositions = compose(
		partial(filterfalse, lambda p: p['Account Code'][:5] == '19437')

	  , partial( filterfalse
	  		   , lambda p: p['Asset Type'] in [ 'Cash', 'Foreign Exchange Forward'
	  		   								  , 'Repo Liability', 'Money Market'] \
					or p['Name'] in ['.FSFUND HK', 'CLFLDIF HK']	# open ended funds
			   )
	  
	  , partial(filterfalse, lambda p: p['Position'] == '' or p['Position'] <= 0)
	)


	updatePositionId = lambda p: \
		mergeDict(p, {'Id': p['Name'] + ' Equity', 'IdType': 'TICKER'}) \
		if p['Asset Type'] == 'Equity' else \
		mergeDict(p, {'Id': p['ISIN'], 'IdType': 'ISIN'})


	isCLOPortfolio = lambda p: p['Account Code'] in \
						['12229', '12734', '12366', '12630', '12549', '12550', '13007']


	"""
	[Iterable] positions => ( [Iterable] CLO positions
							, [Iterable] non CLO positions
							)

	Split the positions into All, CLO and non-CLO group
	"""
	splitCLO = lambda positions: \
		reduce( lambda acc, el: ( chain(acc[0], [el])
								, acc[1]
								) if isCLOPortfolio(el) else \
								
								( acc[0]
								, chain(acc[1], [el])
								)
	  		  , positions
	  		  , ([], [])
	  		  )


	return \
	compose(
		splitCLO
	  , partial(map, updatePositionId)
	  , removeUnwantedPositions		
	  , lambda positions: lognContinue('getBlpLqaPositions(): start', positions)
	)(positions)



def buildLqaRequest(name, date, positions):
	"""
	[String] name (name of the lqa request, 'masterlist_clo' etc.)
	[String] date (yyyy-mm-dd)
	[Iterable] positions 
		=> [String] output lqa request file name

	Side effect: create a lqa request file
	"""
	# LQAHeaders = [ 'LQA_POSITION_TAG_1'
	# 		 	 , 'LQA_TGT_LIQUIDATION_VOLUME'
	# 		 	 , 'LQA_SOURCE_TGT_LIQUIDATION_COST'
	# 		 	 , 'LQA_FACTOR_TGT_LIQUIDATION_COST'
	# 		 	 , 'LQA_TGT_LIQUIDATION_HORIZON'
	# 		 	 , 'LQA_TGT_COST_CONF_LEVL'
	# 		 	 , 'LQA_MODEL_AS_OF_DATE'
	# 		 	 ]


	lqaLine = lambda name, date, position: \
		', '.join([ position['Id']
				  , position['IdType']
				  , 'LQA_POSITION_TAG_1={0}'.format(name)
				  , 'LQA_TGT_LIQUIDATION_VOLUME={0}'.format(r['Position'])
				  , 'LQA_SOURCE_TGT_LIQUIDATION_COST={0}'.\
				  		format('PR' if position['IdType'] == 'TICKER' else 'BA')
				  , 'LQA_FACTOR_TGT_LIQUIDATION_COST={0}'.\
				  		format(20 if position['IdType'] == 'TICKER' else 1)
				  , 'LQA_TGT_LIQUIDATION_HORIZON=1'
				  , 'LQA_TGT_COST_CONF_LEVL=95'
				  , 'LQA_MODEL_AS_OF_DATE={0}'.format(date)
				  ])


	"""
	  [String] name (name of the lqa request list, such as 'master_clo')
	, [String] date (yyyymmdd)
	, [Dictionary] r (position)
		=> [Dictionary] LQA record

	LQA_SOURCE_TGT_LIQUIDATION_COST: price source, 'BA' (bid ask) for bond and 
		'PR' (public price) for equity

	"""
	# lqaRecord = lambda name, date, r: \
	# 	{ 'Identifier ID': r['Id']
	# 	, 'Identifier ID Type': r['IdType']
	# 	, 'LQA_POSITION_TAG_1': name
	# 	, 'LQA_TGT_LIQUIDATION_VOLUME': str(r['Position'])
	# 	, 'LQA_SOURCE_TGT_LIQUIDATION_COST': 'PR' if r['IdType'] == 'TICKER' else 'BA'
	# 	, 'LQA_FACTOR_TGT_LIQUIDATION_COST': '20' if r['IdType'] == 'TICKER' else '1'
	# 	, 'LQA_TGT_LIQUIDATION_HORIZON': '1'
	# 	, 'LQA_TGT_COST_CONF_LEVL': '95'
	# 	, 'LQA_MODEL_AS_OF_DATE': date
	# 	}


	"""
		[Headers] headers, [Dictionary] r (LQA record) => [String] line
	"""
	# outputLine = lambda headers, r: \
	# 	'|'.join([r['Identifier ID'], r['Identifier ID Type'], str(len(headers))]) + '|' + \
	# 	'|'.join(headers) + '|' + '|'.join(map(lambda h: r[h], headers)) + '|'


	lqaFile = 'LQA_request_'+ name + '_' + date + '.txt'
	# lqaLines = map( partial(outputLine, LQAHeaders)
	# 			  , map(partial(lqaRecord, name, date), positions))


	# outputString = \
	# 	''.join(open('LQA_template_start.txt', 'r')) + \
	# 	'\n'.join(lqaLines) + \
	# 	''.join(open('LQA_template_end.txt', 'r'))


	with open(lqaFile, 'w') as outputFile:
		# outputFile.write(outputString)
		outputFile.write('\n'.join(map(partial(lqaLine, name, date), positions)))


	return lqaFile



"""
	[List] group (positions of the same security) 
		=> [Dictioanry] consolidated record

	Example:

	[ {'Id': '1 HK', 'Position': 100, ...}
	  , {'Id': '1 HK', 'Position': 200, ...}
	]

	=>

	{'Id': '1 HK', 'Position': 300, ...}
"""
consolidateGroup = lambda group: \
	mergeDict(group[0].copy(), {'Position': sum(map(lambda p: p['Position'], group))})



"""[Iterable] positions => [Iterable] consolidated positions"""
consolidate = compose(
	  partial(map, consolidateGroup)
	, lambda d: d.values()
	, partial(groupbyToolz, lambda p: p['Id'])
)	



def lognContinue(msg, x):
	logger.debug(msg)
	return x


def lognRaise(msg):
	logger.error(msg)
	raise ValueError
