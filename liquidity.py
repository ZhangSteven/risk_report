# coding=utf-8
#
# Build the .req file to generate Bloomberg liquidity report.
# 

from itertools import takewhile, dropwhile, filterfalse
from functools import partial
from toolz.functoolz import compose
from toolz.itertoolz import groupby as groupbyToolz
from utils.iter import pop
from nomura.main import fileToLines
from risk_report.utility import getCurrentDirectory
from os.path import join
import logging
logger = logging.getLogger(__name__)



"""
	[Dictionary] r, [String] date (yyyymmdd) => [Dictionary] LQA record
"""
lqaRecord = lambda date, r: \
	{ 'Identifier ID': r['Name'] + ' Equity' if r['Asset Type'] == 'Equity' \
						else r['ISIN']
	, 'Identifier ID Type': 'TICKER' if r['Asset Type'] == 'Equity' \
						else 'ISIN'
	, 'LQA_POSITION_TAG_1': 'MasterList'
	, 'LQA_TGT_LIQUIDATION_VOLUME': str(r['Position'])
	, 'LQA_SOURCE_TGT_LIQUIDATION_COST': 'PR' if r['Asset Type'] == 'Equity' \
						else 'BA'
	, 'LQA_FACTOR_TGT_LIQUIDATION_COST': '20' if r['Asset Type'] == 'Equity' \
						else '1'
	, 'LQA_TGT_LIQUIDATION_HORIZON': '1'
	, 'LQA_TGT_COST_CONF_LEVL': '95'
	, 'LQA_MODEL_AS_OF_DATE': date
	}



validPosition = compose(
	  partial(filter, lambda x: x['Position'] > 0)
	, partial(filterfalse, lambda x: x['Asset Type'] in \
							['Cash', 'Repo Liability', 'Foreign Exchange Forward'])
)



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
	, 'Position': sum(map(lambda x: x['Position'], t[1]))
	}



consolidate = compose(
	  partial(map, consolidateGroup)
	, lambda d: d.items()
	, partial(groupbyToolz, lambda x: x['Name'])
)



"""
	[String] file => [Iterable] positions

	position: [Dictionary] header -> value
"""
getPositions = compose(
	  lambda t: map(lambda line: dict(zip(t[0], line)), t[1])
	, lambda t: ( t[0]
				, filterfalse( lambda line: line[0] in ['Top Level', 'Long', 'Short']
							 , takewhile(lambda line: line[0] != '', t[1]))
				)
	, lambda lines: (pop(lines), lines)
	, partial(dropwhile, lambda line: line[0] != 'Name')
	, fileToLines
)



getLQARecords = lambda date, file: \
	compose( partial(map, partial(lqaRecord, date))
		   , validPosition
		   , consolidate
		   , getPositions
		   )(file)



"""
	[Headers] headers, [Dictionary] r (LQA record) => [String] line
"""
outputLine = lambda headers, r: \
	r['Identifier ID'] + '|' + r['Identifier ID Type'] + '|' + \
	'|'.join(headers) + '|' + '|'.join(map(lambda h: r[h], headers)) + '|'



LQAHeaders = [ 'LQA_POSITION_TAG_1'
			 , 'LQA_TGT_LIQUIDATION_VOLUME'
			 , 'LQA_SOURCE_TGT_LIQUIDATION_COST'
			 , 'LQA_FACTOR_TGT_LIQUIDATION_COST'
			 , 'LQA_TGT_LIQUIDATION_HORIZON'
			 , 'LQA_TGT_COST_CONF_LEVL'
			 , 'LQA_MODEL_AS_OF_DATE']



outputString = lambda records: \
	''.join(open('LQA_template_start.txt', 'r')) + \
	'\n'.join(map(partial(outputLine, LQAHeaders), records)) + \
	''.join(open('LQA_template_end.txt', 'r'))



def doOutput(date, inputFile):
	with open('LQA_'+date+'.req', 'w') as outputFile:
		outputFile.write(
			compose(outputString, partial(getLQARecords, date))(inputFile)
		)




if __name__ == '__main__':
	import logging.config
	logging.config.fileConfig('logging.config', disable_existing_loggers=False)

	inputFile = join('samples', 'risk_m2_20191209.xls')
	date = '20191209'
	doOutput(date, inputFile)