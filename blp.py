# coding=utf-8
#
# Read the Bloomberg input file (Excel) and output positions.
# 

from itertools import takewhile, dropwhile, filterfalse, chain
from functools import partial, reduce
from toolz.functoolz import compose
from toolz.itertoolz import groupby as groupbyToolz
from utils.iter import pop, firstOf
from utils.excel import worksheetToLines
from utils.utility import mergeDict
from risk_report.utility import getCurrentDirectory
from xlrd import open_workbook
from datetime import datetime
from os.path import join
import logging, re
logger = logging.getLogger(__name__)



def lognContinue(msg, x):
	logger.debug(msg)
	return x


def lognRaise(msg):
	logger.error(msg)
	raise ValueError



def readBlpFile(file):
	"""
	[String] file => ( [String] date (yyyy-mm-dd)
					 , [Iterable] All positions consolidated
					 , [Iterable] CLO positions consolidated
				     , [Iterable] non-CLO positions consolidated)
					 )

	The function to expose to other modules. Tt gets the long positions from 
	Bloomberg Excel, take out those that do not need liquidity measure (cash etc.), 
	split into CLO positions and non-CLO positions, the condolidate positions
	across all portofolios.
	"""
	isCLOPortfolio = lambda p: p['Account Code'] in \
						['12229', '12734', '12366', '12630', '12549', '12550', '13007']


	"""
	[Iterable] positions => ( [Iterable] All positions
							, [Iterable] CLO positions
							, [Iterable] non CLO positions
							)

	Split the positions into All, CLO and non-CLO group
	"""
	splitCLO = lambda positions: \
		reduce( lambda acc, el: (chain(acc[0], [el]), chain(acc[1], [el]), acc[2]) \
								if isCLOPortfolio(el) else \
								(chain(acc[0], [el]), acc[1], chain(acc[2], [el]))
	  		  , positions
	  		  , ([], [], [])
	  		  )


	splitnConsolidate = compose(
	  	partial(map, consolidate)
	  , splitCLO
	)


	return \
	compose(
		lambda t: (t[0], *splitnConsolidate(t[1]))
	  , readBlpPositionsFromFile
	)(file)




def readBlpPositionsFromFile(file):
	"""
	[String] file => ( [String] date
					 , [Iterable] positions)

	Read positions from file, not consoldation.
	"""
	# [Iterable] lines => [List] line that contains the date
	findDateLine = partial(
		firstOf
	  , lambda line: len(line) > 1 and line[1].startswith('Risk Report LQA Master as of')
	)


	# [String] The string containing date => [String] date (yyyy-mm-dd)
	# it looks like: Risk Report LQA Master as of 20200429
	getDateFromString = compose(
		lambda s: datetime.strftime(datetime.strptime(s, '%Y%m%d'), '%Y-%m-%d')
	  , lambda s: s.split()[-1]
	)


	getDateFromLines = compose(
		getDateFromString
	  , lambda line: lognRaise('Failed to find date line') if line == None else line[1]
	  , findDateLine
	)


	updatePositionWithDate = lambda date, p: \
		mergeDict(p, {'Date': date})


	updatePositionId = lambda p: \
		mergeDict(p, {'Id': p['Name'] + ' Equity', 'IdType': 'TICKER'}) \
		if p['Asset Type'] == 'Equity' else \
		mergeDict(p, {'Id': p['ISIN'], 'IdType': 'ISIN'})


	updatePositions = lambda date, positions: \
		map( updatePositionId
		   , map(partial(updatePositionWithDate, date), positions))


	return \
	compose(
		lambda t: (t[0], updatePositions(t[0], t[1]))
	  , lambda lines: (getDateFromLines(lines), getLongHoldings(lines))
	  , fileToLines
	  , lambda file: lognContinue('readBlpPositionsFromFile(): {0}'.format(file), file)
	)(file)



def fileToLines(file):
	"""
	[String] file => [Iterable] lines

	Read an Excel file, convert its first sheet into lines, each line is
	a list of the columns in the row.
	"""
	return worksheetToLines(open_workbook(file).sheet_by_index(0))



"""
	[Iterable] lines => [Iterable] positions

	Read all positions from the Bloomberg Excel file.
"""
getPositions = compose(
	  lambda t: map(lambda line: dict(zip(t[0], line)), t[1])
	, lambda lines: (pop(lines), lines)
	, lambda lines: dropwhile(lambda line: line[0] != 'Name', lines)
)



emptyorShortPosition = lambda p: p['Position'] == '' or p['Position'] <= 0


unwantedPosition = lambda p: p['Asset Type'] in \
	['Cash', 'Foreign Exchange Forward', 'Repo Liability', 'Money Market'] or \
	p['Name'] in ['.FSFUND HK', 'CLFLDIF HK']	# open ended funds


difPosition = lambda p: p['Account Code'][:5] == '19437'



"""
	[Iterable] lines => [Iterable] long positions without cash and DIF
	
	Read positions, but exclude:

	1) Short positions;
	2) Cash, FX forward, repo, money market instruments;
	3) DIF positions (we will take DIF from Geneva)
"""
getLongHoldings = compose(
	partial(filterfalse, difPosition)
  , partial(filterfalse, unwantedPosition)
  , partial(filterfalse, emptyorShortPosition)
  , getPositions
)



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