# coding=utf-8
# 

import unittest2
from risk_report.utility import getCurrentDirectory
from utils.iter import firstOf
from os.path import join



findByName = lambda name, positions: \
	firstOf(lambda p: p['Name'] == name, positions)



class TestMain(unittest2.TestCase):

	def __init__(self, *args, **kwargs):
		super(TestMain, self).__init__(*args, **kwargs)



	# def testReadGenevaFile(self):
	# 	inputFile = join(getCurrentDirectory(), 'samples', '19437 tax lot 20200429.xlsx')
	# 	date, positions = readGenevaFile(inputFile)
	# 	self.assertEqual('20200429', date)
	# 	self.assertEqual(175, len(positions))
	# 	self.verifyBondPosition(findByName('ADROIJ 4.25 10/31/24 REGS', positions))
	# 	self.verifyEquityPosition(findByName('ISHARES FTSE A50 CHINA INDEX', positions))



	# def verifyEquityPosition(self, p):
	# 	self.assertEqual('2823 HK Equity', p['Id'])
	# 	self.assertEqual('Equity', p['Asset Type'])
	# 	self.assertEqual(530000, p['Position'])
	# 	self.assertEqual('HKD', p['Currency'])
	# 	self.assertEqual('20200429', p['Date'])
	# 	self.assertEqual('TICKER', p['IdType'])



	# def verifyBondPosition2(self, p):
	# 	self.assertEqual('XS1164776020', p['Id'])
	# 	self.assertEqual('Corporate Bond', p['Asset Type'])
	# 	self.assertEqual(2000000, p['Position'])
	# 	self.assertEqual('USD', p['Currency'])
	# 	self.assertEqual('20200131', p['Date'])
	# 	self.assertEqual('ISIN', p['IdType'])