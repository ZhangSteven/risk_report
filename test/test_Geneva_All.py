# coding=utf-8
# 

import unittest2
from risk_report.asset import byCountryGroup, getAssetType
from risk_report.geneva import readGenevaInvestmentPositionFile
from risk_report.main import loadBlpDataFromFile, countryNotApplicable
from risk_report.utility import getCurrentDirectory
from toolz.functoolz import compose
from functools import partial
from itertools import filterfalse
from os.path import join



"""
	[Dictionary] Blp Data
	[String] country group
	[Iterator] positions grom Geneva investment positions
		=> [Float] sum of market value of positions from that country in the
			portfolio's local currency
"""
getGenevaTotalCountryGroup = compose(
	sum
  , partial(map, lambda p: p['AccruedInterest'] + p['MarketValueBook'])
  , lambda blpData, countryGroup, positions: \
  		byCountryGroup( blpData
  					  , countryGroup
  					  , filterfalse(partial(countryNotApplicable, blpData), positions)
  					  )
)



class TestGenevaAll(unittest2.TestCase):

	def __init__(self, *args, **kwargs):
		super(TestGenevaAll, self).__init__(*args, **kwargs)



	def testbyCountryGroup(self):
		inputFile = join( getCurrentDirectory()
						, 'samples'
						, 'DIF_20200429_investment_position.xlsx'
						)

		blpDataFile = join( getCurrentDirectory()
						  , 'samples'
						  , 'DIF_20200429_BlpData.xlsx'
						  )
		
		FX = 1/7.7520	# USD FX as of 2020-04-30
		blpData = loadBlpDataFromFile(blpDataFile)
		positions = compose(
			lambda t: list(t[1])
		  , readGenevaInvestmentPositionFile
		)(inputFile)


		self.assertAlmostEqual( 394165723.69
							  , getGenevaTotalCountryGroup(blpData, 'China', positions) * FX
							  , 2
							  )

		self.assertAlmostEqual( 46753980.08
							  , getGenevaTotalCountryGroup(blpData, 'Hong Kong', positions) * FX
							  , 2
							  )

		self.assertAlmostEqual( 10019205.48
							  , getGenevaTotalCountryGroup(blpData, 'Macau', positions) * FX
							  , 2
							  )

		self.assertAlmostEqual( 15742145.41
							  , getGenevaTotalCountryGroup(blpData, 'Singapore', positions) * FX
							  , 2
							  )

		self.assertAlmostEqual( 1419901.34
							  , getGenevaTotalCountryGroup(blpData, 'America - others (1)', positions) * FX
							  , 2
							  )