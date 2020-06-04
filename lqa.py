# coding=utf-8
#
# LQA related functions come here.
# 
# 1) Build LQA request
# 2) Read LQA response
# 

from risk_report.data import getPortfolioPositions
from utils.excel import fileToLines
from utils.iter import pop
from functools import partial, reduce
from itertools import chain, filterfalse, dropwhile, takewhile
from toolz.functoolz import compose
from toolz.itertoolz import groupby as groupbyToolz
from utils.utility import mergeDict, writeCsv
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



# def buildLqaRequestFromFilesCombined(portfolioGroup, date, writer):
# 	"""
# 	[String] portfolioGroup, [String] date (yyyymmdd), [Function] writer
# 		=> [String] combined master list csv file

# 	Where "writer" is an output function that takes name, date and positions
# 	and write to an output file.

# 	Side effect: create one LQA request file with all positions combined
# 	"""

# 	"""
# 		[String] file 
# 			=> ( [String] date (yyyy-mm-dd)
# 			   , [Iterable] clo
# 			   , [Iterable] nonCLO
# 			   )
# 	"""
# 	processBlpFile = compose(
# 		lambda t: (t[0], *getBlpLqaPositions(t[1]))
# 	  , readBlpFile
# 	)


# 	"""[String] file => ([String] date (yyyy-mm-dd), [Iterable] positions)"""
# 	processGenevaFile = compose(
# 		lambda t: (t[0], getGenevaLqaPositions(t[1]))
# 	  , readGenevaInvestmentPositionFile
# 	)


# 	processDatenPosition = lambda dt, clo, nonCLO, genevaPositions: \
# 		writer( 'masterlist_combined'
# 			  , dt
# 			  , consolidate(chain(clo, nonCLO, genevaPositions))
# 			)


# 	checkDate = lambda d1, clo, nonCLO, d2, genevaPositions: \
#   		lognRaise('inconsistent dates: {0}, {1}'.format(d1, d2)) \
#   		if d1 != d2 else (d1, clo, nonCLO, genevaPositions)


# 	return compose(
# 		argumentsAsTuple(processDatenPosition)  
# 	  , argumentsAsTuple(checkDate)
# 	  , lambda blpFile, genevaFile: ( *processBlpFile(blpFile)
# 	  								, *processGenevaFile(genevaFile)
# 	  								)
# 	)(blpFile, genevaFile)



# def buildLqaRequestFromFiles(blpFile, genevaFile, writer):
# 	"""
# 	[String] blpFile, [String] genevaFile, [Function] writer
# 		=> ( [String] master list CLO csv file
# 		   , [STring] master list non-CLO csv file
# 		   )

# 	Where "writer" is an output function that takes name, date and positions
# 	and write to an output file.

# 	Side effect: create 2 LQA request files
# 	"""

# 	"""
# 		[String] file 
# 			=> ( [String] date (yyyy-mm-dd)
# 			   , [Iterable] clo
# 			   , [Iterable] nonCLO
# 			   )
# 	"""
# 	processBlpFile = compose(
# 		lambda t: (t[0], *getBlpLqaPositions(t[1]))
# 	  , readBlpFile
# 	)


# 	"""[String] file => ([String] date (yyyy-mm-dd), [Iterable] positions)"""
# 	processGenevaFile = compose(
# 		lambda t: (t[0], getGenevaLqaPositions(t[1]))
# 	  , readGenevaInvestmentPositionFile
# 	)


# 	processDatenPosition = lambda dt, clo, nonCLO, genevaPositions: \
# 		( writer( 'masterlist_nonCLO'
# 				, dt
# 				, consolidate(chain(nonCLO, genevaPositions))
# 				)
# 		, writer('masterlist_CLO', dt, consolidate(clo))
# 		)


# 	checkDate = lambda d1, clo, nonCLO, d2, genevaPositions: \
#   		lognRaise('inconsistent dates: {0}, {1}'.format(d1, d2)) \
#   		if d1 != d2 else (d1, clo, nonCLO, genevaPositions)


# 	return compose(
# 		argumentsAsTuple(processDatenPosition)  
# 	  , argumentsAsTuple(checkDate)
# 	  , lambda blpFile, genevaFile: ( *processBlpFile(blpFile)
# 	  								, *processGenevaFile(genevaFile)
# 	  								)
# 	)(blpFile, genevaFile)



def getGenevaIdnType(position):
	"""
	[Dictionary] position
		=> ( [String] id,
		   , [String] id type
		   )

	NOTE: this function should never throw an exception. So we make it always
	return something even if we cannot determine what should be the asset type.
	"""
	ISINfromInvestID = lambda investId: \
		lognContinue( 'getGenevaIdnType(): ISINfromInvestID: special case: {0}'.format(investId)
					, investId) \
		if len(investId) < 12 else investId[0:12]


	isEquityType = lambda assetType: \
		assetType in [ 'Common Stock', 'Real Estate Investment Trust'
					 , 'Stapled Security', 'Exchange Trade Fund']

	isBondType = lambda assetType: assetType.split()[-1] == 'Bond'

	investId, assetType = position['InvestID'], position['SortKey']
	

	return \
	(investId + ' Equity', 'TICKER') if isEquityType(assetType) else \
	(ISINfromInvestID(investId), 'ISIN') if isBondType(assetType) else \
	lognContinue( 'getGenevaIdnType(): special case: {0}'.format(position['InvestID'])
				, (position['InvestID'], position['SortKey']))



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
	if position['Quantity'] == 0 or position['SortKey'] in \
	['Cash and Equivalents', 'Fixed Deposit', 'Open-End Fund'] \
	else False



def getGenevaLqaPositions(positions):
	"""
	[Iterable] positions => [Iterable] positions

	Read Geneva consolidated tax lot positions, then do the following: 

	1) take out those not suitable for liquidity test (cash, FX forward, etc.);
	2) Add Id, IdType and Position fields for LQA processing.

	"""

	# [Dictonary] p => [Dictionary] enriched position with id and idType
	addIdnType = compose(
		lambda t: mergeDict(t[2], {'Id': t[0], 'IdType': t[1]})
	  , lambda p: (*getGenevaIdnType(p), p)
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


	# [Dictionary] position => [Dictioanry] position with id and idtype
	updatePositionId = compose(
		lambda t: mergeDict(t[2], {'Id': t[0], 'IdType': t[1]})
	  , lambda position: (*getBlpIdnType(position), position)
	)


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



def getBlpIdnType(position):
	"""
	[Dictionary] position => [Tuple] (id, idType)
	
	Assume the position contain fields 'Name' (ticker), 'ISIN' and 'Asset Type'
	"""
	if position['Asset Type'] == 'Equity':
		return (position['Name'] + ' Equity', 'TICKER')
	elif position['ISIN'] == '':
		return (position['Name'], 'TICKER')
	else:
		return (position['ISIN'], 'ISIN')



def buildLqaRequest(name, date, positions):
	"""
	[String] name (name of the lqa request, 'masterlist_clo' etc.)
	[String] date (yyyy-mm-dd)
	[Iterable] positions 
		=> [String] output lqa request file name

	Side effect: create a lqa request file

	This version builds a txt file that is ready to be submitted as a universe
	file to the Bloomberg service center.
	"""
	lqaLine = lambda name, date, position: \
		', '.join([ position['Id']
				  , position['IdType']
				  , 'LQA_POSITION_TAG_1={0}'.format(name)
				  , 'LQA_TGT_LIQUIDATION_VOLUME={0}'.format(position['Position'])
				  , 'LQA_SOURCE_TGT_LIQUIDATION_COST={0}'.\
				  		format('PR' if position['IdType'] == 'TICKER' else 'BA')
				  , 'LQA_FACTOR_TGT_LIQUIDATION_COST={0}'.\
				  		format(20 if position['IdType'] == 'TICKER' else 1)
				  , 'LQA_TGT_LIQUIDATION_HORIZON=1'
				  , 'LQA_TGT_COST_CONF_LEVL=95'
				  , 'LQA_MODEL_AS_OF_DATE={0}'.format(date)
				  ])


	lqaFile = 'LQA_request_'+ name + '_' + date + '.txt'

	with open(lqaFile, 'w') as outputFile:
		outputFile.write('\n'.join(map(partial(lqaLine, name, date), positions)))


	return lqaFile



def buildLqaRequestOldStyle(name, date, positions):
	"""
	[String] name (name of the lqa request, 'masterlist_clo' etc.)
	[String] date (yyyy-mm-dd)
	[Iterable] positions 
		=> [String] output lqa request file name

	Side effect: create a lqa request file

	This version builds a csv file that is for human inspection.
	"""
	headers = [ 'Id'
			  , 'IdType'
			  , 'LQA_POSITION_TAG_1'
			  , 'LQA_TGT_LIQUIDATION_VOLUME'
			  , 'LQA_SOURCE_TGT_LIQUIDATION_COST'
			  , 'LQA_FACTOR_TGT_LIQUIDATION_COST'
			  , 'LQA_TGT_LIQUIDATION_HORIZON'
			  , 'LQA_TGT_COST_CONF_LEVL'
			  , 'LQA_MODEL_AS_OF_DATE'
			  ]


	lqaPosition = lambda name, date, position: \
		{ 'Id': position['Id']
		, 'IdType': position['IdType']
		, 'LQA_POSITION_TAG_1': name
		, 'LQA_TGT_LIQUIDATION_VOLUME': position['Position']
		, 'LQA_SOURCE_TGT_LIQUIDATION_COST': 'PR' if position['IdType'] == 'TICKER' else 'BA'
		, 'LQA_FACTOR_TGT_LIQUIDATION_COST': '20' if position['IdType'] == 'TICKER' else '1'
		, 'LQA_TGT_LIQUIDATION_HORIZON': '1'
		, 'LQA_TGT_COST_CONF_LEVL': '95'
		, 'LQA_MODEL_AS_OF_DATE': date
		}


	lqaFile = 'LQA_request_'+ name + '_' + date + '.csv'

	return writeCsv( lqaFile
				   , chain( [headers]
				   		  , map( lambda p: [p[key] for key in headers]
				   		  	   , map( partial(lqaPosition, name, date)
				   		  	   		, positions))))



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




if __name__ == '__main__':
	import logging.config
	logging.config.fileConfig('logging.config', disable_existing_loggers=False)

	import argparse
	parser = argparse.ArgumentParser(description='Process Bloomberg and Geneva holding File ' \
										+ 'and Geneva investment positions report (DIF only), ' \
										+ 'then produce LQA request files.')
	parser.add_argument( 'blp_file', metavar='blp_file', type=str
					   , help='Bloomberg holding file')
	parser.add_argument( 'geneva_file', metavar='geneva_file', type=str
				   	   , help='Geneva investment positions report')
	args = parser.parse_args()

	buildLqaRequestFromFiles(args.blp_file, args.geneva_file, buildLqaRequestOldStyle)

	# buildLqaRequestFromFiles(args.blp_file, args.geneva_file, buildLqaRequest)

	# buildLqaRequestFromFilesCombined(args.blp_file, args.geneva_file, buildLqaRequestOldStyle)
