# coding=utf-8
# 

import unittest2
from risk_report.lqa import readLqaDataFromFile
from risk_report.utility import getCurrentDirectory
from os.path import join



class TestLQA(unittest2.TestCase):

	def __init__(self, *args, **kwargs):
		super(TestLQA, self).__init__(*args, **kwargs)



	def testReadLqaDataFromFile(self):
		inputFile = join(getCurrentDirectory(), 'samples', 'LQA_response_20200430.xlsx')
		d = readLqaDataFromFile(inputFile)
		self.assertEqual(176, len(d))
		self.verifyLQAdata(d['XS2114413565'])



	def verifyLQAdata(self, p):
		"""
		AT&T INC Bond
		"""
		self.assertEqual(0, p['ERROR CODE'])
		self.assertEqual('BBG00RPJBQ56', p['ID_BB_GLOBAL'])
		self.assertEqual('Corp', p['MARKET_SECTOR_DES'])
		self.assertEqual('EUR', p['CRNCY'])
		self.assertAlmostEqual(92.064, p['LQA_MARKET_PRICE_UNC_PRICE'])
		self.assertEqual(10000000, p['LQA_TGT_LIQUIDATION_VOLUME'])
		self.assertAlmostEqual(0.016903, p['LQA_LIQUIDATION_COST'])
		self.assertEqual(3, p['LQA_TIME_TO_CASH'])
