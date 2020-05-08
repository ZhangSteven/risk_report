# coding=utf-8
#
# Read the Bloomberg input file (Excel) and Geneva input file, then produce
# master list files and LQA request files.
# 

from risk_report.utility import getCurrentDirectory
from risk_report.blp import getBlpLqaPositions
from risk_report.geneva import readGenevaFile, getGenevaLqaPositions
from functools import partial
from itertools import chain
from toolz.functoolz import compose
from toolz.itertoolz import groupby as groupbyToolz
from utils.utility import mergeDict
from os.path import join
import logging
logger = logging.getLogger(__name__)



def lognContinue(msg, x):
	logger.debug(msg)
	return x


def lognRaise(msg):
	logger.error(msg)
	raise ValueError



def buildLqaRequestFromFiles(blpFile, genevaFile):
	"""
	[String] blpFile, [String] genevaFile
		=> ( [String] master list CLO csv file
		   , [STring] master list non-CLO csv file
		   )

	Side effect: create 2 LQA request files
	"""
	date1, clo, nonClo = compose(
		lambda t: (t[0], *getBlpLqaPositions(t[1]))
	  , readBlpFile
	)(blpFile)

	date2, dif = readGenevaFile(genevaFile)

	if date1 != date2:
		lognRaise('inconsistent dates: {0}, {1}'.format(date1, date2))

	return buildLqaRequest('masterlist_nonCLO', date1, consolidate(chain(nonClo, dif))) \
		 , buildLqaRequest('masterlist_CLO', date1, consolidate(clo))



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
		, 'LQA_TGT_LIQUIDATION_VOLUME': str(int(r['Position']))
		, 'LQA_SOURCE_TGT_LIQUIDATION_COST': 'PR' if r['Asset Type'] == 'Equity' \
							else 'BA'
		, 'LQA_FACTOR_TGT_LIQUIDATION_COST': '20' if r['Asset Type'] == 'Equity' \
							else '1'
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
