# coding=utf-8
#
# Build LQA request file from Daphne's Excel file.
# 

from toolz.functoolz import compose
from utils.excel import getRawPositionsFromFile
from os.path import join
import logging
logger = logging.getLogger(__name__)



def buildLqaRequest(positions):
	"""
	[Iterable] positions => [Int] 0 if successful

	Side effect: create a lqa request file

	This version builds a txt file that is ready to be submitted as a universe
	file to the Bloomberg service center.
	"""
	lqaLine = lambda position: \
		', '.join([ position['Identifier ID']
				  , position['Identifier ID Type']
				  , 'LQA_POSITION_TAG_1={0}'.format(position['LQA_POSITION_TAG_1'])
				  , 'LQA_TGT_LIQUIDATION_VOLUME={0}'.format(position['LQA_TGT_LIQUIDATION_VOLUME'])
				  , 'LQA_SOURCE_TGT_LIQUIDATION_COST={0}'.format(position['LQA_SOURCE_TGT_LIQUIDATION_COST'])
				  , 'LQA_FACTOR_TGT_LIQUIDATION_COST={0}'.format(position['LQA_FACTOR_TGT_LIQUIDATION_COST'])
				  , 'LQA_TGT_LIQUIDATION_HORIZON={0}'.format(position['LQA_TGT_LIQUIDATION_HORIZON'])
				  , 'LQA_TGT_COST_CONF_LEVL={0}'.format(position['LQA_TGT_COST_CONF_LEVL'])
				  , 'LQA_MODEL_AS_OF_DATE={0}'.format(int(position['LQA_MODEL_AS_OF_DATE']))
				  ])


	with open('LQA_request.txt', 'w') as outputFile:
		outputFile.write('\n'.join(map(lqaLine, positions)))


	return 0



def buildLqaRequestStress(positions):
	"""
	[Iterable] positions => [Int] 0 if successful

	Side effect: create a lqa request file

	This version builds a txt file that is ready to be submitted as a universe
	file to the Bloomberg service center.
	"""
	lqaLine = lambda position: \
		', '.join([ position['Identifier ID']
				  , position['Identifier ID Type']
				  , 'LQA_POSITION_TAG_1={0}'.format(position['LQA_POSITION_TAG_1'])
				  , 'LQA_TGT_LIQUIDATION_VOLUME={0}'.format(position['LQA_TGT_LIQUIDATION_VOLUME'])
				  , 'LQA_SOURCE_TGT_LIQUIDATION_COST={0}'.format(position['LQA_SOURCE_TGT_LIQUIDATION_COST'])
				  , 'LQA_FACTOR_TGT_LIQUIDATION_COST={0}'.format(position['LQA_FACTOR_TGT_LIQUIDATION_COST'])
				  , 'LQA_TGT_LIQUIDATION_HORIZON={0}'.format(position['LQA_TGT_LIQUIDATION_HORIZON'])
				  , 'LQA_TGT_COST_CONF_LEVL={0}'.format(position['LQA_TGT_COST_CONF_LEVL'])
				  , 'LQA_MODEL_AS_OF_DATE={0}'.format(int(position['LQA_MODEL_AS_OF_DATE']))
				  , 'LQA_FACTOR_EXPECTED_DAILY_VOLUME={0}'.format(position['LQA_FACTOR_EXPECTED_DAILY_VOLUME'])
				  , 'LQA_FACTOR_PRICE_VOLATILITY={0}'.format(position['LQA_FACTOR_PRICE_VOLATILITY'])
				  , 'LQA_FACTOR_BID_ASK_SPREAD={0}'.format(position['LQA_FACTOR_BID_ASK_SPREAD'])
				  ])


	with open('LQA_request.txt', 'w') as outputFile:
		outputFile.write('\n'.join(map(lqaLine, positions)))


	return 0



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
		Generate LQA request file from Daphne's excel file.

			$python lqa_daphne.py excel_file.xlsx

		If the file is for stress scenario, then it contains 3 more columns,
		we need to specify the --stress flag:

			$python lqa_daphne.py excel_file.xlsx --stress

		For sample file, please check out the below files in 'samples' folder:

		LQA request_GB_20200331.xlsx
		LQA request_GB_20200331 (Stress).xlsx
	"""

	import argparse
	parser = argparse.ArgumentParser(description='produce LQA request files.')
	parser.add_argument( 'file', metavar='excel file', type=str
					   , help='daphne\'s excel file format')
	parser.add_argument( '--stress', type=str, nargs='?', const=True, default=False
					   , help='use old style output for human inspection')
	args = parser.parse_args()

	writer = buildLqaRequestStress if args.stress else buildLqaRequest

	compose(
		writer
	  , getRawPositionsFromFile
	)(args.file)
