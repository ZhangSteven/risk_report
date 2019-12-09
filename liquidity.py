# coding=utf-8
#
# Build the .req file to generate Bloomberg liquidity report.
# 


import logging
logger = logging.getLogger(__name__)




if __name__ == '__main__':
	import logging.config
	logging.config.fileConfig('logging.config', disable_existing_loggers=False)

	logger.debug('start')