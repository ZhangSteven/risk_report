# coding=utf-8
# 

import unittest2
from risk_report.data import getPortfolioPositions, getPositionDate, getBookCurrency \
							, getIdnType, getMarketValue, getPortfolioId, getQuantity \
							, getLqaData
from risk_report.geneva import isGenevaPosition
from toolz.functoolz import compose
from functools import partial
from itertools import filterfalse



class TestGeneva(unittest2.TestCase):

	def __init__(self, *args, **kwargs):
		super(TestGeneva, self).__init__(*args, **kwargs)



	def testGetPortfolioPositions(self):
		# Test Geneva positions
		positions = list(getPortfolioPositions('19437', '20200429', 'test'))
		self.assertEqual(192, len(positions))
		self.verifyInvestmentPosition(positions[3])



	def testGetPortfolioPositions2(self):
		# Test Bloomberg positions
		positions = compose(
			list
		  , partial(filterfalse, isGenevaPosition)
		)(getPortfolioPositions('ALL', '20200131', 'test'))
		self.assertEqual(97, len(positions))
		self.verifyBlpPosition(positions[2])



	def testGetLqaData(self):
		d = getLqaData('20200529', 'test')
		self.assertEqual(171, len(d))
		self.verifyLQAdata(d['1299 HK Equity'])



	def verifyLQAdata(self, p):
		self.assertEqual(0, p['ERROR CODE'])
		self.assertEqual('1299 HK Equity', p['SECURITIES'])
		self.assertEqual('Developed APAC', p['LQA_LIQUIDITY_SECTOR'])
		self.assertEqual(0.2, p['LQA_LIQUIDATION_HORIZON'])
		self.assertAlmostEqual(0.003042, p['LQA_TGT_LIQUIDATION_COST'])
		self.assertEqual(177200, p['LQA_TGT_LIQUIDATION_VOLUME'])
		self.assertAlmostEqual(0.027887, p['LQA_LIQUIDATION_COST'])
		self.assertEqual(3, p['LQA_TIME_TO_CASH'])



	def verifyInvestmentPosition(self, p):
		self.assertEqual('20200429', getPositionDate(p))
		self.assertEqual('19437', getPortfolioId(p))
		self.assertEqual('HKD', getBookCurrency(p))
		self.assertEqual(('1299 HK Equity', 'TICKER'), getIdnType(p))
		self.assertEqual(12749540, getMarketValue(p))
		self.assertEqual(177200, getQuantity(p))



	def verifyBlpPosition(self, p):
		self.assertEqual('20200131', getPositionDate(p))
		self.assertEqual('12734', getPortfolioId(p))
		self.assertEqual('USD', getBookCurrency(p))
		self.assertEqual(('USF2R125CE38', 'ISIN'), getIdnType(p))
		self.assertEqual(11698622.22, getMarketValue(p))
		self.assertEqual(11000000, getQuantity(p))