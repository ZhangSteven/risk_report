# coding=utf-8
#
# Read the Bloomberg input file (Excel) and Geneva input file, then produce
# master list files and LQA request files.
# 

from risk_report.utility import getCurrentDirectory
from risk_report.lqa import investIdToLqaId, noNeedLiquidityGeneva
from utils.utility import mergeDict
from itertools import chain
from functools import reduce, partial
from os.path import join
import logging
logger = logging.getLogger(__name__)




def enrichGenevaPositions(blpDataFile, positions):
	"""
	[String] blpDataFile, [Iterator] positions
		=> [Iterator] enriched positions
	"""

	needsBlpDataEnrichment = lambda position: True

	"""
		[Iterator] positions => ( [List] positions no need to enrich
								, [List] positions that need to enrch)
	"""
	splitPositions = lambda positions: \
		reduce( lambda acc, el: \
					(acc[0] + [el], acc[1]) \
					if needsBlpDataEnrichment(el) else \
					(acc[0], acc[1] + [el])
			  , positions
			  , ([], [])
			  )


	"""
		[Dictionary] blpData (investid, investidType) -> [Dictionary] blp info)
		[Dictionary] geneva position
			=> [Dictionary] enriched position with data fields from Bloomberg
	"""
	addBlpData = lambda blpData, position : \
		mergeDict(position, blpData[(position['Id'], position['IdType'])])


	return compose(
		lambda t: chain( map(partial(addBlpData, t[0]), t[1])
					   , t[2])
	  , lambda blpDataFile, positions: (getBlpDataFromFile(blpDataFile), *splitPositions(positions))
	)(blpDataFile, positions)




def lognContinue(msg, x):
	logger.debug(msg)
	return x


def lognRaise(msg):
	logger.error(msg)
	raise ValueError




if __name__ == '__main__':
	import logging.config
	logging.config.fileConfig('logging.config', disable_existing_loggers=False)

