# coding=utf-8
#
# Read SFC template and generate output.
# 

from risk_report.utility import getCurrentDirectory
from utils.iter import pop, firstOf
from clamc_datafeed.feeder import fileToLines
from functools import partial
from itertools import takewhile, dropwhile, chain, repeat, zip_longest
from toolz.functoolz import compose
from os.path import join
import logging
logger = logging.getLogger(__name__)



def readSfcTemplate(file):
	"""
	[String] file => [List] filter string lines

	Each filter string line is a List, and each element of that line looks like:

	('China', 'Equity', 'Listed Equities') ...
	"""
	notHeaderLine = lambda line: \
		len(line) == 0 or not line[0].startswith('By asset class / by region')

	takeBetweenLines = compose(
		partial(takewhile, lambda line: len(line) > 0 and line[0] != 'Others')
	  , partial(dropwhile, notHeaderLine)
	)

	getHeaders = compose(
		list
	  , partial(map, lambda s: s.strip())
	  , partial(takewhile, lambda el: el != 'Total')
	  , partial(dropwhile, lambda el: el == '')
	  , lambda line: line[1:]
	)


	removeTrailingSpaces = compose(
		tuple
	  , reversed
	  , list
	  , partial(dropwhile, lambda el: el == '')
	  , reversed
	  , lambda line: line[:5]
	)

	lineToTuple = compose(
		lambda t: t[0:-1] if t[-1] == t[-2] else t
	  , removeTrailingSpaces
	)


	def fillupLeadingSpaces(lines):
		fillSpace = compose(
			tuple
		  , partial(map, lambda t: t[0] if t[1] == '' else t[1])
		)

		combine = lambda previous, line: \
			zip(previous, line) if len(previous) > len(line) else \
			zip_longest(previous, line)


		previous = tuple(repeat('', 5))
		for line in lines:
			if line[0] == '':
				previous = fillSpace(combine(previous, line))
			else:
				previous = line

			yield previous
	# End of fillupLeadingSpaces()


	getAssetTypes = compose(
		fillupLeadingSpaces
	  , partial(map, lineToTuple)
	)
	

	return \
	compose(
		lambda t: (getHeaders(t[0]), getAssetTypes(t[1]))
	  , lambda lines: (pop(lines), lines)
	  , takeBetweenLines
	  , fileToLines
	)(file)