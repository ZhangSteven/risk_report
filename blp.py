# coding=utf-8
#
# Read the Bloomberg input file (Excel) and output positions.
# 

from itertools import takewhile, dropwhile, filterfalse, chain
from functools import partial, reduce
from toolz.functoolz import compose
from toolz.itertoolz import groupby as groupbyToolz
from utils.iter import pop
from utils.excel import worksheetToLines
from risk_report.utility import getCurrentDirectory
from xlrd import open_workbook
from os.path import join
import logging
logger = logging.getLogger(__name__)



def fileToLines(file):
	"""
	[String] file => [Iterable] lines

	Read an Excel file, convert its first sheet into lines, each line is
	a list of the columns in the row.
	"""
	return worksheetToLines(open_workbook(file).sheet_by_index(0))



"""
	[String] file => [Iterable] positions

	Read all positions from the Bloomberg Excel file.
"""
getPositions = compose(
	  lambda t: map(lambda line: dict(zip(t[0], line)), t[1])
	, lambda lines: (pop(lines), lines)
	, partial(dropwhile, lambda line: line[0] != 'Name')
	, fileToLines
)



isEmptyPosition = lambda p: p['Position'] == ''
isShortPosition = lambda p: p['Position'] <= 0
unwantedPositionType = lambda p: p['Asset Type'] in \
	['Cash', 'Foreign Exchange Forward', 'Repo Liability', 'Money Market']
isDIFPosition = lambda p: p['Account Code'][:5] == '19437'



"""
	[String] file => [Iterable] long positions without cash and DIF
	
	Read positions, but exclude:

	1) Short positions;
	2) Cash, FX forward, repo, money market instruments;
	3) DIF positions (we will take DIF from Geneva)
"""
getLongHoldings = compose(
	partial(filterfalse, isDIFPosition)
  , partial(filterfalse, unwantedPositionType)
  , partial(filterfalse, isShortPosition)
  , partial(filterfalse, isEmptyPosition)
  , getPositions
)



# 12298 has only one equity holding and cash, no bo
isCLOPortfolio = lambda p: p['Account Code'] in \
					['12229', '12734', '12366', '12630', '12549', '12550', '13007']



"""
	(name, list of records under the name) => [Dictioanry] consolidated record

	Example:

	( '1 HK'
	, [ {'Name': '1 HK', 'Position': 100, ...}
	  , {'Name': '1 HK', 'Position': 200, ...}
	  ]
	)

	=>

	{'Name': '1 HK', 'Position': 300, ...}
"""
consolidateGroup = lambda t: \
	{ 'Name': t[0]
	, 'ISIN': t[1][0]['ISIN']
	, 'Asset Type': t[1][0]['Asset Type']
	, 'Currency': t[1][0]['Currency']
	, 'Position': sum(map(lambda x: x['Position'], t[1]))
	}



# [Iterable] positions => [Iterable] consolidated positions
consolidate = compose(
	  partial(map, consolidateGroup)
	, lambda d: d.items()
	, partial(groupbyToolz, lambda p: p['Name'])
)



"""
	[String] file => ( [Iterable] CLO positions consolidated
					 , [Iterable] non-CLO positions consolidated)

	This is the function exposed to others, it gets the long positions from 
	Bloomberg Excel, take out those that do not need liquidity measure (cash etc.), 
	split into CLO positions and non-CLO positions, the condolidate positions
	across all portofolios.

"""
getConsolidatedHoldings = compose(
	lambda t: (consolidate(t[0]), consolidate(t[1]))
  , lambda positions: \
		reduce( lambda acc, el: (chain(acc[0], [el]), acc[1]) if isCLOPortfolio(el) \
  		   							else (acc[0], chain(acc[1], [el])) 
  		   	  , positions
  		      , ([], [])
  		   	  )
  , getLongHoldings
)