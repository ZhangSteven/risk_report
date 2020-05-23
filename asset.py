# coding=utf-8
#
# Asset allocation logic
# 

import logging
logger = logging.getLogger(__name__)



def sfcCountry(investment):
	"""
	The logic is:

	1) For cash equivalents, leave it, no country is assigned.
	2) For equity asset class, use Bloomberg "CNTRY_ISSUE_ISO" field
	3) For other asset class, use Bloomberg "CNTRY_OF_RISK" field
	"""

	return 0



def assetClass(investment):
	"""
	The logic is:

	
	"""



def lognContinue(msg, x):
	logger.debug(msg)
	return x



def lognRaise(msg):
	logger.error(msg)
	raise ValueError




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
