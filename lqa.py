# coding=utf-8
#
# Read the Bloomberg input file (Excel) and Geneva input file, then produce
# master list files and LQA request files.
# 

from risk_report.utility import getCurrentDirectory
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



def getGenevaLqaPositions(positions):
	"""
	[Iterable] positions => [Iterable] positions

	Read Geneva consolidated tax lot positions, then do the following: 

	1) take out those not suitable for liquidity test (cash, FX forward, etc.);
	2) Add Id, IdType and Position fields for LQA processing.

	"""
	removeHTMfromInvestID = lambda investId: \
		investId[0:12] if len(investId) > 15 and investId[-4:] == ' HTM' else investId


	isEquityType = lambda securityType: \
		securityType in [ 'Common Stock', 'Real Estate Investment Trust'
						, 'Stapled Security', 'Exchange Trade Fund']

	isBondType = lambda securityType: securityType.split()[-1] == 'Bond'


	addIdnType = lambda p: \
		mergeDict(p, {'Id': p['InvestID'] + ' Equity', 'IdType': 'TICKER'}) \
		if isEquityType(p['ThenByDescription']) else \
	  	mergeDict(p, {'Id': removeHTMfromInvestID(p['InvestID']), 'IdType': 'ISIN'}) \
	  	if isBondType(p['ThenByDescription']) else \
	  	lognRaise('addIdnType(): unsupported type: {0}'.format(p['ThenByDescription']))


	addPosition = lambda p: \
		mergeDict(p, {'Position': p['Quantity']})


	return compose(
		partial(map, addIdnType)
	  , partial(map, addPosition)
	  , partial(filterfalse, lambda p: p['Quantity'] == 0)
	  , partial(filterfalse, lambda p: p['ThenByDescription'] == 'Cash and Equivalents')
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
	[Iterable] positions => [String] output lqa request file name

	Side effect: create a lqa request file
	"""
	LQAHeaders = [ 'LQA_POSITION_TAG_1'
			 	 , 'LQA_TGT_LIQUIDATION_VOLUME'
			 	 , 'LQA_SOURCE_TGT_LIQUIDATION_COST'
			 	 , 'LQA_FACTOR_TGT_LIQUIDATION_COST'
			 	 , 'LQA_TGT_LIQUIDATION_HORIZON'
			 	 , 'LQA_TGT_COST_CONF_LEVL'
			 	 , 'LQA_MODEL_AS_OF_DATE'
			 	 ]


	"""
	  [String] name (name of the lqa request list, such as 'master_clo')
	, [String] date (yyyymmdd)
	, [Dictionary] r (position)
		=> [Dictionary] LQA record

	LQA_SOURCE_TGT_LIQUIDATION_COST: price source, 'BA' (bid ask) for bond and 
		'PR' (public price) for equity

	"""
	lqaRecord = lambda name, date, r: \
		{ 'Identifier ID': r['Id']
		, 'Identifier ID Type': r['IdType']
		, 'LQA_POSITION_TAG_1': name
		, 'LQA_TGT_LIQUIDATION_VOLUME': str(r['Position'])
		, 'LQA_SOURCE_TGT_LIQUIDATION_COST': 'PR' if r['IdType'] == 'TICKER' else 'BA'
		, 'LQA_FACTOR_TGT_LIQUIDATION_COST': '20' if r['IdType'] == 'TICKER' else '1'
		, 'LQA_TGT_LIQUIDATION_HORIZON': '1'
		, 'LQA_TGT_COST_CONF_LEVL': '95'
		, 'LQA_MODEL_AS_OF_DATE': date
		}


	"""
		[Headers] headers, [Dictionary] r (LQA record) => [String] line
	"""
	outputLine = lambda headers, r: \
		'|'.join([r['Identifier ID'], r['Identifier ID Type'], str(len(headers))]) + '|' + \
		'|'.join(headers) + '|' + '|'.join(map(lambda h: r[h], headers)) + '|'


	lqaFile = 'LQA_'+ name + '_' + date + '.req'
	lqaLines = map( partial(outputLine, LQAHeaders)
				  , map(partial(lqaRecord, name, date), positions))


	outputString = \
		''.join(open('LQA_template_start.txt', 'r')) + \
		'\n'.join(lqaLines) + \
		''.join(open('LQA_template_end.txt', 'r'))


	with open(lqaFile, 'w') as outputFile:
		outputFile.write(outputString)


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




if __name__ == '__main__':
	import logging.config
	logging.config.fileConfig('logging.config', disable_existing_loggers=False)

	import argparse
	parser = argparse.ArgumentParser(description='Process Bloomberg and Geneva holding File ' \
										+ 'and Geneva holding file (DIF only), then produce '
										+ 'LQA request files.')
	parser.add_argument( 'blp_file', metavar='blp_file', type=str
					   , help='Bloomberg holding file')
	parser.add_argument( 'geneva_file', metavar='geneva_file', type=str
				   , help='Geneva holding file')
	args = parser.parse_args()

	buildLqaRequestFromFiles(args.blp_file, args.geneva_file)
