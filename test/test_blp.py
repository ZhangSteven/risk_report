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



class TestBlp(unittest2.TestCase):

	def __init__(self, *args, **kwargs):
		super(TestBlp, self).__init__(*args, **kwargs)



	def testGetLongHoldings(self):
		inputFile = join(getCurrentDirectory(), 'samples', 'risk_m2_sample.xls')
		holdings = list(getLongHoldings(fileToLines(inputFile)))
		self.assertEqual(25, len(holdings))



	def testReadBlpFile(self):
		inputFile = join(getCurrentDirectory(), 'samples', 'risk_m2_sample.xls')
		date, clo, nonCLO = readBlpFile(inputFile)
		self.assertEqual('2019-12-09', date)
		
		clo, nonCLO = list(clo), list(nonCLO)
		self.assertEqual(2, len(clo))
		self.assertEqual(12, len(nonCLO))
		self.verifyCLOPosition(findByName('MQGAU 6 ¼ 01/14/21 REGS', clo))
		self.verifyNonCLOPosition(findByName('YUZHOU 8 ⅝ 01/23/22', nonCLO))



	def testReadBlpFile2(self):
		inputFile = join(getCurrentDirectory(), 'samples', 'risk_m2_20200429.xlsx')
		date, _, nonCLO = readBlpFile(inputFile)
		self.assertEqual('2020-04-29', date)
		self.verifyEquityPosition(findByName('2 HK', nonCLO))



	def verifyCLOPosition(self, p):
		self.assertEqual('US55608KAD72', p['ISIN'])
		self.assertEqual('Corporate Bond', p['Asset Type'])
		self.assertEqual(15846, p['Position'])
		self.assertEqual('USD', p['Currency'])
		self.assertEqual('2019-12-09', p['Date'])
		self.assertFalse('TICKER' in p)



	def verifyNonCLOPosition(self, p):
		self.assertEqual('XS1938265474', p['ISIN'])
		self.assertEqual('Corporate Bond', p['Asset Type'])
		self.assertEqual(4000, p['Position'])
		self.assertEqual('USD', p['Currency'])
		self.assertEqual('2019-12-09', p['Date'])
		self.assertFalse('TICKER' in p)



	def verifyEquityPosition(self, p):
		self.assertEqual('HK0002007356', p['ISIN'])
		self.assertEqual('Equity', p['Asset Type'])
		self.assertEqual(384500, p['Position'])
		self.assertEqual('HKD', p['Currency'])
		self.assertEqual('2020-04-29', p['Date'])
		self.assertEqual('2 HK Equity', p['TICKER'])