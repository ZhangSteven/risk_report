# coding=utf-8
#
# Asset allocation logic for SFC
# 

import logging
logger = logging.getLogger(__name__)



def country(investment):
	"""
	The logic is:

	1) For equity asset class, use Bloomberg "CNTRY_ISSUE_ISO" field
	2) For other asset class other than cash, use Bloomberg "CNTRY_OF_RISK" field
	3) For cash, it will throw an exception because country does not make sense
		in this case.
	"""
	return 0



def assetClass(investment):
	"""
	The logic is:

	If it's cash on hand, payables and receivables, money market instrucments 
	(say fixed deposit), asset class = "Cash Equivalents"

	If it's not cash, then use LQA "MARKET_SECTOR_DES" field to lookup:

	If LQA market sector = "Equity", then asset class = "Equity", sub category
	"Listed Equity" if Bloomberg field "EXCH_MARKET_STATUS" = "ACTV", else
	sub category "Unlisted Equity".

	If it's not equity and its Bloomberg field "CAPITAL_CONTINGENT_SECURITY" 
	= "Y", then asset class is "Additional Tier 1, Contingent Convertibles 
	and similar instrucments"

	Else use the below mapping

	Corp -> Fixed Income, sub catetory "Corporate Bond"
	Govt -> Fixed Income, sub catetory "Government Bond"
	Comdty -> Derivatives, sub category "Derivatives"
	"""
	return 0



def isFinancial(investment):
	"""
	The logic:

	1) If asset class is cash equivalent, then throw exception because it does
		not make sense.
	2) Otherwise use Bloomberg "INDUSTRY_SECTOR", if return result is "Financial",
		then YES, othereise NO.

	What about derivatives? Cannot see the logic in Excel
	"""
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
