# coding=utf-8
# 

import unittest2
from risk_report.geneva import readGenevaInvestmentPositionFile, getGenevaPositionDate
from risk_report.lqa import getGenevaLqaPositions
from risk_report.utility import getCurrentDirectory
from utils.iter import firstOf
from toolz.functoolz import compose
from os.path import join



findByName = lambda name, positions: \
	firstOf(lambda p: p['Description'] == name, positions)


readGenevaLqaPositions = compose(
	lambda t: (t[0], getGenevaLqaPositions(t[1]))
  , readGenevaInvestmentPositionFile
)



class TestGeneva(unittest2.TestCase):

	def __init__(self, *args, **kwargs):
		super(TestGeneva, self).__init__(*args, **kwargs)



	def testLqaFromGenevaInvestmentPositions(self):
		inputFile = join(getCurrentDirectory(), 'samples', 'DIF_20200429_investment_position.xlsx')
		date, positions = readGenevaLqaPositions(inputFile)
		self.assertEqual('20200429', date)
		positions = list(positions)
		self.assertEqual(175, len(positions))
		self.verifyBondPosition(findByName('ADROIJ 4.25 10/31/24 REGS', positions))
		self.verifyEquityPosition(findByName('ISHARES FTSE A50 CHINA INDEX', positions))
		


	def testLqaFromGenevaInvestmentPositions2(self):	# Tests a HTM bond
		inputFile = join(getCurrentDirectory(), 'samples', 'DIF_20200131_investment_position.xlsx')
		date, positions = readGenevaLqaPositions(inputFile)
		self.assertEqual('20200131', date)
		positions = list(positions)
		self.assertEqual(145, len(positions))
		self.verifyBondPosition2(findByName('COGARD 7.5 03/09/20', positions))



	def testReadGenevaInvestmentPositionFile(self):
		inputFile = join( getCurrentDirectory(), 'samples'
						, 'DIF_20200429_investment_position.xlsx')
		date, positions = readGenevaInvestmentPositionFile(inputFile)
		self.assertEqual('20200429', date)
		positions = list(positions)
		self.assertEqual(192, len(positions))
		self.verifyInvestmentPosition(positions[3])



	def verifyBondPosition(self, p):
		self.assertEqual('USY70902AB04', p['Id'])
		self.assertEqual('ISIN', p['IdType'])
		self.assertEqual('Corporate Bond', p['SortKey'])
		self.assertEqual(3000000, p['Position'])
		self.assertEqual('United States Dollar', p['LocalCurrency'])
		self.assertEqual('20200429', getGenevaPositionDate(p))
		self.assertEqual('19437', p['Portfolio'])
		self.assertEqual('HKD', p['BookCurrency'])
		self.assertEqual('Geneva', p['Remarks1'][0:6])



	def verifyEquityPosition(self, p):
		self.assertEqual('2823 HK Equity', p['Id'])
		self.assertEqual('TICKER', p['IdType'])
		self.assertEqual('Exchange Trade Fund', p['SortKey'])
		self.assertEqual(530000, p['Position'])
		self.assertEqual('Hong Kong Dollar', p['LocalCurrency'])
		self.assertEqual('20200429', getGenevaPositionDate(p))
		self.assertEqual('19437', p['Portfolio'])
		self.assertEqual('HKD', p['BookCurrency'])
		self.assertEqual('Geneva', p['Remarks1'][0:6])



	def verifyBondPosition2(self, p):
		self.assertEqual('XS1164776020', p['Id'])
		self.assertEqual('ISIN', p['IdType'])
		self.assertEqual('Corporate Bond', p['SortKey'])
		self.assertEqual(2000000, p['Position'])
		self.assertEqual('United States Dollar', p['LocalCurrency'])
		self.assertEqual('20200131', getGenevaPositionDate(p))
		self.assertEqual('19437', p['Portfolio'])
		self.assertEqual('HKD', p['BookCurrency'])
		self.assertEqual('Geneva', p['Remarks1'][0:6])



	def verifyInvestmentPosition(self, p):
		self.assertEqual('20200429', getGenevaPositionDate(p))
		self.assertEqual('19437', p['Portfolio'])
		self.assertEqual('HKD', p['BookCurrency'])
		self.assertEqual('Geneva', p['Remarks1'].split()[0])
		self.assertEqual('Hong Kong Dollar', p['LocalCurrency'])
		self.assertEqual('1299 HK', p['InvestID'])
		self.assertAlmostEqual(71.95, p['LocalPrice'])
		self.assertEqual(12749540, p['MarketValueBook'])