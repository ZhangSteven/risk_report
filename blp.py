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
					 , [Iterable] CLO positions consolidated
				     , [Iterable] non-CLO positions consolidated)
					 )

	The function to expose to other modules. Tt gets the long positions from 
	Bloomberg Excel, take out those that do not need liquidity measure (cash etc.), 
	split into CLO positions and non-CLO positions, the condolidate positions
	across all portofolios.
	"""

	# [Iterable] lines => [List] line that contains the date
	findDateLine = partial(
		firstOf
	  , lambda line: len(line) > 0 and line[0].lower().startswith('mav: mav')
	)


	# [String] header containing date => [String] date (yyyy-mm-dd)
	# The header looks like: MAV: MAV (12/09/2019 01:17:01)
	getDateFromString = compose(
		lambda s: datetime.strftime(datetime.strptime(s, '%m/%d/%Y'), '%Y-%m-%d')
	  , lambda s: s[1:].split()[0]
	  , lambda m: lognRaise('Failed to get date from line') if m == None else m.group(1)
	  , lambda s: re.match('.*(\(.*\))', s)
	)


	getDateFromLines = compose(
		getDateFromString
	  , lambda line: lognRaise('Failed to find date line') if line == None else line[0]
	  , findDateLine
	)


	updatePositionWithDate = lambda date, p: \
		mergeDict(p, {'Date': date})


	isCLOPortfolio = lambda p: p['Account Code'] in \
						['12229', '12734', '12366', '12630', '12549', '12550', '13007']


	"""
	[Iterable] positions => ( [Iterable] consolidated CLO positions
							, [Iterable] consolidated non CLO positions
							)

	Split the positions into CLO and non-CLO group, then consolidate them
	"""
	splitCLO = lambda positions: \
		reduce( lambda acc, el: (chain(acc[0], [el]), acc[1]) if isCLOPortfolio(el) else \
								(acc[0], chain(acc[1], [el])) 
	  		  , positions
	  		  , ([], [])
	  		  )


	updateSplitConsolidate = compose(
	  	lambda t: ( consolidate(t[0])
				  , consolidate(t[1])
				  )
	  , splitCLO
	  , lambda date, positions: map(partial(updatePositionWithDate, date), positions)
	)


	return \
	compose(
		lambda t: (t[0], *updateSplitConsolidate(t[0], t[1]))
	  , lambda lines: (getDateFromLines(lines), getLongHoldings(lines))
	  , fileToLines
	  , lambda file: lognContinue('readBlpFile(): {0}'.format(file), file)
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
unwantedPositionType = lambda p: p['Asset Type'] in \
	['Cash', 'Foreign Exchange Forward', 'Repo Liability', 'Money Market']
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
  , partial(filterfalse, unwantedPositionType)
  , partial(filterfalse, emptyorShortPosition)
  , getPositions
)



"""
	[List] group (positions of the same security) 
		=> [Dictioanry] consolidated record

	Example:

	[ {'Name': '1 HK', 'Position': 100, ...}
	  , {'Name': '1 HK', 'Position': 200, ...}
	]

	=>

	{'Name': '1 HK', 'Position': 300, ...}
"""
consolidateGroup = lambda group: \
	mergeDict(group[0].copy(), {'Position': sum(map(lambda p: p['Position'], group))})



# [Iterable] positions => [Iterable] consolidated positions
consolidate = compose(
	  partial(map, consolidateGroup)
	, lambda d: d.values()
	, partial(groupbyToolz, lambda p: p['Name'])
)
