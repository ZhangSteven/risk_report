# coding=utf-8
# 

import unittest2
from risk_report.geneva import readGenevaFile
from risk_report.lqa import getGenevaLqaPositions
from risk_report.utility import getCurrentDirectory
from utils.iter import firstOf
from toolz.functoolz import compose
from os.path import join



findByName = lambda name, positions: \
	firstOf(lambda p: p['TaxLotDescription'] == name, positions)


readGenevaLqaPositions = compose(
	lambda t: (t[0], getGenevaLqaPositions(t[1]))
  , readGenevaFile
)



class TestGeneva(unittest2.TestCase):

	def __init__(self, *args, **kwargs):
		super(TestGeneva, self).__init__(*args, **kwargs)



	def testReadGenevaFile(self):
		inputFile = join(getCurrentDirectory(), 'samples', '19437 tax lot 20200429.xlsx')
		date, positions = readGenevaLqaPositions(inputFile)
		self.assertEqual('20200429', date)
		positions = list(positions)
		self.assertEqual(175, len(positions))
		self.verifyBondPosition(findByName('ADROIJ 4.25 10/31/24 REGS', positions))
		self.verifyEquityPosition(findByName('ISHARES FTSE A50 CHINA INDEX', positions))
		


	def testReadGenevaFile2(self):	# Tests a HTM bond
		inputFile = join(getCurrentDirectory(), 'samples', '19437 tax lot 20200131.xlsx')
		date, positions = readGenevaLqaPositions(inputFile)
		self.assertEqual('20200131', date)
		positions = list(positions)
		self.assertEqual(145, len(positions))
		self.verifyBondPosition2(findByName('COGARD 7.5 03/09/20', positions))



	def verifyBondPosition(self, p):
		self.assertEqual('USY70902AB04', p['Id'])
		self.assertEqual('ISIN', p['IdType'])
		self.assertEqual('Corporate Bond', p['ThenByDescription'])
		self.assertEqual(3000000, p['Position'])
		self.assertEqual('USD', p['Currency'])
		self.assertEqual('2020-04-29', p['PeriodEndDate'])



	def verifyEquityPosition(self, p):
		self.assertEqual('2823 HK Equity', p['Id'])
		self.assertEqual('TICKER', p['IdType'])
		self.assertEqual('Exchange Trade Fund', p['ThenByDescription'])
		self.assertEqual(530000, p['Position'])
		self.assertEqual('HKD', p['Currency'])
		self.assertEqual('2020-04-29', p['PeriodEndDate'])



	def verifyBondPosition2(self, p):
		self.assertEqual('XS1164776020', p['Id'])
		self.assertEqual('ISIN', p['IdType'])
		self.assertEqual('Corporate Bond', p['ThenByDescription'])
		self.assertEqual(2000000, p['Position'])
		self.assertEqual('USD', p['Currency'])
		self.assertEqual('2020-01-31', p['PeriodEndDate'])
