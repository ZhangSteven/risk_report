# coding=utf-8
# 

import unittest2
from risk_report.blp import readBlpFile, getLongHoldings, fileToLines
from risk_report.utility import getCurrentDirectory
from functools import partial
from utils.iter import firstOf
from os.path import join



findByName = lambda name, positions: \
	firstOf(lambda p: p['Name'] == name, positions)



class TestALL(unittest2.TestCase):

	def __init__(self, *args, **kwargs):
		super(TestALL, self).__init__(*args, **kwargs)



	def testGetLongHoldings(self):
		inputFile = join(getCurrentDirectory(), 'samples', 'risk_m2_sample.xls')
		holdings = list(getLongHoldings(fileToLines(inputFile)))
		self.assertEqual(25, len(holdings))



	def testGetConsolidatedHoldings(self):
		inputFile = join(getCurrentDirectory(), 'samples', 'risk_m2_sample.xls')
		date, clo, nonCLO = readBlpFile(inputFile)
		self.assertEqual('2019-12-09', date)
		
		clo, nonCLO = list(clo), list(nonCLO)
		self.assertEqual(2, len(clo))
		self.assertEqual(12, len(nonCLO))
		self.verifyCLOPosition(findByName('MQGAU 6 ¼ 01/14/21 REGS', clo))
		self.verifyNonCLOPosition(findByName('YUZHOU 8 ⅝ 01/23/22', nonCLO))



	def verifyCLOPosition(self, p):
		self.assertEqual('US55608KAD72', p['ISIN'])
		self.assertEqual('Corporate Bond', p['Asset Type'])
		self.assertEqual(15846, p['Position'])
		self.assertEqual('USD', p['Currency'])
		self.assertEqual('2019-12-09', p['Date'])



	def verifyNonCLOPosition(self, p):
		self.assertEqual('XS1938265474', p['ISIN'])
		self.assertEqual('Corporate Bond', p['Asset Type'])
		self.assertEqual(4000, p['Position'])
		self.assertEqual('USD', p['Currency'])
		self.assertEqual('2019-12-09', p['Date'])