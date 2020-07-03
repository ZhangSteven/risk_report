# coding=utf-8
#
# Build the .req file to generate Bloomberg liquidity report.
# 
import configparser
from os.path import dirname, abspath, join
from functools import lru_cache



"""
	Get the absolute path to the directory where this module is in.

	This piece of code comes from:

	http://stackoverflow.com/questions/3430372/how-to-get-full-path-of-current-files-directory-in-python
"""
getCurrentDirectory = lambda: \
	dirname(abspath(__file__))



@lru_cache(maxsize=3)
def loadConfigFile(file):
	"""
	Read the config file, convert it to a config object.
	"""
	cfg = configparser.ConfigParser()
	cfg.read(join(getCurrentDirectory(), file))
	return cfg



def getInputDirectory(mode):
	if mode == 'test':
		return loadConfigFile('risk_report.config')['Test']['inputDirectory']
	else:
		return loadConfigFile('risk_report.config')['Production']['inputDirectory']



def getDataDirectory():
	return loadConfigFile('risk_report.config')['Data']['directory']