# coding=utf-8
# 

import unittest2
from risk_report.lqa import createLqaPositions, readLqaDataFromFile
from risk_report.data import getPositionDate
from risk_report.utility import getCurrentDirectory
from functools import partial
from utils.iter import firstOf
from toolz.functoolz import compose
from os.path import join



findById = lambda id, positions: \
	firstOf(lambda p: p['Id'] == id, positions)



findByName = lambda name, positions: \
	firstOf(lambda p: p['Name'] == name, positions)



class TestLqa(unittest2.TestCase):

	def __init__(self, *args, **kwargs):
		super(TestLqa, self).__init__(*args, **kwargs)



	def testLqaPositions(self):
		nonCLO, clo = compose(
			lambda t: (list(t[0]), list(t[1]))
		  , createLqaPositions
		)('all', '20200429', 'test')

		# ADROIJ 4.25 10/31/24 REGS, only in 19437
		self.verifyBondPosition(findById('USY70902AB04', nonCLO))

		# in 19437 and other other non-clo portfolios
		self.verifyEquityPosition(findById('2318 HK Equity', nonCLO))
		


	def testLqaPositions2(self):
		nonCLO, clo = compose(
			lambda t: (list(t[0]), list(t[1]))
		  , createLqaPositions
		)('all', '20200131', 'test')
		
		"""
			19437 Geneva has 146 positions (excluding cash)
			BLP has 18 positions (8 clo, 10 non-clo)
			They have 5 overlapping positions in the non-clo section.

			Therefore CLO = 8, ono-CLO = 151
		"""
		self.assertEqual(8, len(clo))
		self.assertEqual(151, len(nonCLO))
		self.verifyCLOPosition(findByName('AEGON 5 ½ 04/11/48', clo))
		self.verifyNonCLOPosition(findByName('CHINSC 8 ¾ 01/15/21', nonCLO))
		self.verifyEquityPosition3(findByName('1038 HK', nonCLO))



	def testReadLqaDataFromFile(self):
		inputFile = join(getCurrentDirectory(), 'samples', 'difLqa20200529.bbg')
		positions = list(readLqaDataFromFile(inputFile))
		self.assertEqual(171, len(positions))
		self.verifyLQAdata(positions[0])



	def verifyLQAdata(self, p):
		self.assertEqual(0, p['ERROR CODE'])
		self.assertEqual('1299 HK Equity', p['SECURITIES'])
		self.assertEqual('Developed APAC', p['LQA_LIQUIDITY_SECTOR'])
		self.assertEqual(0.2, p['LQA_LIQUIDATION_HORIZON'])
		self.assertAlmostEqual(0.003042, p['LQA_TGT_LIQUIDATION_COST'])
		self.assertEqual(177200, p['LQA_TGT_LIQUIDATION_VOLUME'])
		self.assertAlmostEqual(0.027887, p['LQA_LIQUIDATION_COST'])
		self.assertEqual(3, p['LQA_TIME_TO_CASH'])



	def verifyCLOPosition(self, p):
		self.assertEqual('US007924AJ23', p['Id'])
		self.assertEqual('ISIN', p['IdType'])
		self.assertEqual('Corporate Bond', p['Asset Type'])
		self.assertEqual(290400000, p['Position'])
		self.assertEqual('USD', p['Currency'])



	def verifyNonCLOPosition(self, p):
		self.assertEqual('XS1893648904', p['Id'])
		self.assertEqual('ISIN', p['IdType'])
		self.assertEqual('Corporate Bond', p['Asset Type'])
		self.assertEqual(12000000, p['Position'])
		self.assertEqual('USD', p['Currency'])



	def verifyEquityPosition3(self, p):
		self.assertEqual('1038 HK Equity', p['Id'])
		self.assertEqual('TICKER', p['IdType'])
		self.assertEqual('Equity', p['Asset Type'])
		self.assertEqual(256500, p['Position'])
		self.assertEqual('HKD', p['Currency'])



	def verifyBondPosition(self, p):
		self.assertEqual('USY70902AB04', p['Id'])
		self.assertEqual('ISIN', p['IdType'])
		self.assertEqual('Corporate Bond', p['SortKey'])
		self.assertEqual(3000000, p['Position'])
		self.assertEqual('United States Dollar', p['LocalCurrency'])
		self.assertEqual('20200429', getPositionDate(p))
		self.assertEqual('19437', p['Portfolio'])
		self.assertEqual('HKD', p['BookCurrency'])
		self.assertEqual('Geneva', p['Remarks1'][0:6])



	def verifyEquityPosition(self, p):
		self.assertEqual('2318 HK Equity', p['Id'])
		self.assertEqual('TICKER', p['IdType'])
		self.assertEqual(1037000, p['Position'])
		self.assertEqual('20200429', getPositionDate(p))
