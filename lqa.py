# coding=utf-8
#
# LQA related functions come here.
# 
# 1) Build LQA request
# 2) Read LQA response
# 

from risk_report.data import getPortfolioPositions, getIdnType, getQuantity
from risk_report.geneva import isGenevaPosition
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



def createLqaPositions(portfolio, date, mode='production'):
	"""
	[String] portfolio, [String] date (yyyymmdd), [Function] writer
		=> ( [Iterator] non-clo positions
		   , [Iterator] clo positions
		   )
	"""
	processGenevaPositions = compose(
		getGenevaLqaPositions
	  , partial(filter, isGenevaPosition)
	)


	processBlpPositions = compose(
		getBlpLqaPositions
	  , partial(filterfalse, isGenevaPosition)
	)


	return compose(
		lambda t: ( consolidate(chain(t[1], t[2]))
				  , consolidate(t[0])
				  )
	  , lambda positions: ( *processBlpPositions(positions)
						  , processGenevaPositions(positions)
						  )
	  , list
	  , getPortfolioPositions
	)(portfolio, date, mode)



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
	  , lambda p: (*getIdnType(p), p)
	)


	return compose(
		partial(map, addIdnType)
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
		partial( filterfalse
	  		   , lambda p: p['Asset Type'] in [ 'Cash', 'Foreign Exchange Forward'
	  		   								  , 'Repo Liability', 'Money Market'] \
					or p['Name'] in ['.FSFUND HK', 'CLFLDIF HK']	# open ended funds
			   )
	  
	  , partial(filterfalse, lambda p: p['Position'] == '' or p['Position'] <= 0)
	)


	# [Dictionary] position => [Dictioanry] position with id and idtype
	updatePositionId = compose(
		lambda t: mergeDict(t[2], {'Id': t[0], 'IdType': t[1]})
	  , lambda position: (*getIdnType(position), position)
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

	NOTE: consolidated position is hard to tell whether it is a blp position or
	a geneva position. Therefore we 'Position' field to store the total quantity.
"""
consolidateGroup = lambda group: \
	mergeDict(group[0].copy(), {'Position': sum(map(getQuantity, group))})



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

	"""
		Generate LQA requewst files. To generate LQA request for 19437 only, do

			$python lqa.py 19437 20200529

		To generate LQA request for all positions, do

			$python lqa.py all 20200529

		If you want to have the old in csv format for human inspection, do

			$python lqa.py 19437 202000529 --old

		If you want to build two output files with clo and non-clo separated,
		uncomment the code block blow and run the program.
	"""

	import argparse
	parser = argparse.ArgumentParser(description='produce LQA request files.')
	parser.add_argument( 'portfolio', metavar='portfolio', type=str
					   , help='for which portfolio')
	parser.add_argument( 'date', metavar='date', type=str
					   , help='date of the positions (yyyymmdd)')
	parser.add_argument( '--old', type=str, nargs='?', const=True, default=False
					   , help='use old style output for human inspection')
	args = parser.parse_args()

	writer = buildLqaRequestOldStyle if args.old else buildLqaRequest

	# Choice 1: Create CLO and non-CLO separately
	# compose(
	# 	lambda t: ( writer('masterlist_nonCLO', args.date, t[0])
	# 		  	  , writer('masterlist_CLO', args.date, t[1])
	# 		  	  )
	#   , createLqaPositions
	# )(args.portfolio, args.date)


	# Choice 2: Create one combined masterlist, use this if you want to generate
	# LQA request for just one portfolio, say 19437.
	compose(
		partial(writer, 'masterlist', args.date)
	  , consolidate
	  , lambda t: chain(t[0], t[1])
	  , createLqaPositions
	)(args.portfolio, args.date)
