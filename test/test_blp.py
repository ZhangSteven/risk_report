# coding=utf-8
# 

import unittest2
from risk_report.blp import getBlpLqaPositions, readBlpFile
from risk_report.main import consolidate
from risk_report.utility import getCurrentDirectory
from functools import partial
from utils.iter import firstOf
from toolz.functoolz import compose
from os.path import join



findByName = lambda name, positions: \
	firstOf(lambda p: p['Name'] == name, positions)



class TestBlp(unittest2.TestCase):

	def __init__(self, *args, **kwargs):
		super(TestBlp, self).__init__(*args, **kwargs)



	def testReadBlpFile(self):
		inputFile = join(getCurrentDirectory(), 'samples', 'risk_m2_sample.xlsx')
		date, positions = readBlpFile(inputFile)
		positions = list(positions)
		self.assertEqual('20200429', date)
		self.assertEqual(107, len(positions))



	def testReadLqaPositionsFromFile(self):
		inputFile = join(getCurrentDirectory(), 'samples', 'risk_m2_sample.xlsx')
		readLqaPositionsFromFile = compose(
			lambda t: (t[0], *getBlpLqaPositions(t[1]))
		  , readBlpFile
		)

		date, clo, nonCLO = readLqaPositionsFromFile(inputFile)
		self.assertEqual('20200429', date)
		
		clo, nonCLO = list(consolidate(clo)), list(consolidate(nonCLO))
		self.assertEqual(8, len(clo))
		self.assertEqual(10, len(nonCLO))
		self.verifyCLOPosition(findByName('AEGON 5 ½ 04/11/48', clo))
		self.verifyNonCLOPosition(findByName('CHINSC 8 ¾ 01/15/21', nonCLO))
		self.verifyEquityPosition(findByName('1038 HK', nonCLO))


	def verifyCLOPosition(self, p):
		self.assertEqual('US007924AJ23', p['Id'])
		self.assertEqual('ISIN', p['IdType'])
		self.assertEqual('Corporate Bond', p['Asset Type'])
		self.assertEqual(290400, p['Position'])
		self.assertEqual('USD', p['Currency'])
		self.assertEqual('20200429', p['AsOfDate'])
		self.assertEqual('position', p['RecordType'])
		self.assertEqual('aim', p['DataSource'])



	def verifyNonCLOPosition(self, p):
		self.assertEqual('XS1893648904', p['Id'])
		self.assertEqual('ISIN', p['IdType'])
		self.assertEqual('Corporate Bond', p['Asset Type'])
		self.assertEqual(6000, p['Position'])
		self.assertEqual('USD', p['Currency'])
		self.assertEqual('20200429', p['AsOfDate'])
		self.assertEqual('position', p['RecordType'])
		self.assertEqual('aim', p['DataSource'])



	def verifyEquityPosition(self, p):
		self.assertEqual('1038 HK Equity', p['Id'])
		self.assertEqual('TICKER', p['IdType'])
		self.assertEqual('Equity', p['Asset Type'])
		self.assertEqual(256500, p['Position'])
		self.assertEqual('HKD', p['Currency'])
		self.assertEqual('20200429', p['AsOfDate'])
		self.assertEqual('position', p['RecordType'])
		self.assertEqual('aim', p['DataSource'])
