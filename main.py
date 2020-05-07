# coding=utf-8
#
# Read the Bloomberg input file (Excel) and output positions.
# 

from risk_report.utility import getCurrentDirectory
from risk_report.blp import readBlpFile
from functools import partial
from toolz.functoolz import compose
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



getLQARecordsFromFile = lambda file: compose( 
	lambda t: map(partial(lqaRecord, t[0]), t[1])
  , readBlpFile
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
			compose(outputString, getLQARecordsFromFile)(inputFile)
		)



if __name__ == '__main__':
	import logging.config
	logging.config.fileConfig('logging.config', disable_existing_loggers=False)

	import argparse
	parser = argparse.ArgumentParser(description='Process Bloomberg holding File and Geneva holding file (DIF only), then produce LQA request file for Bloomberg.')
	parser.add_argument( 'blp_file', metavar='blp_file', type=str
					   , help='Bloomberg holding file')
	args = parser.parse_args()
	doOutput('2020-05-06', args.blp_file)
