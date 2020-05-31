# coding=utf-8
# 

import unittest2
from risk_report.asset import byCountryFilter, byAssetTypeFilter
from risk_report.geneva import readGenevaInvestmentPositionFile \
							, getGenevaMarketValue
from risk_report.main import loadBlpDataFromFile
from risk_report.utility import getCurrentDirectory
from toolz.functoolz import compose
from functools import partial
from itertools import filterfalse
from os.path import join



class TestGenevaAll(unittest2.TestCase):

	def __init__(self, *args, **kwargs):
		super(TestGenevaAll, self).__init__(*args, **kwargs)



	def testSum(self):
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


		
		# Now we test by different country groups
		self.assertAlmostEqual( 394165723.69
							  , compose(
							  		lambda x: x * FX
							  	  , sum
							  	  , partial(map, getGenevaMarketValue)
							  	  , byCountryFilter(blpData, 'China')
							  	)(positions)
							  , 2
							  )


		self.assertAlmostEqual( 46753980.08
							  , compose(
							  		lambda x: x * FX
							  	  , sum
							  	  , partial(map, getGenevaMarketValue)
							  	  , byCountryFilter(blpData, 'Hong Kong')
							  	)(positions)
							  , 2
							  )


		self.assertAlmostEqual( 10019205.48
							  , compose(
							  		lambda x: x * FX
							  	  , sum
							  	  , partial(map, getGenevaMarketValue)
							  	  , byCountryFilter(blpData, 'Macau')
							  	)(positions)
							  , 2
							  )


		self.assertAlmostEqual( 15742145.41
							  , compose(
							  		lambda x: x * FX
							  	  , sum
							  	  , partial(map, getGenevaMarketValue)
							  	  , byCountryFilter(blpData, 'Singapore')
							  	)(positions)
							  , 2
							  )


		self.assertAlmostEqual( 1419901.34
							  , compose(
							  		lambda x: x * FX
							  	  , sum
							  	  , partial(map, getGenevaMarketValue)
							  	  , byCountryFilter(blpData, 'America - others (1)')
							  	)(positions)
							  , 2
							  )


		# Purposedly made wrong, since there are no "XXX" country.
		self.assertAlmostEqual( 0
							  , compose(
							  		lambda x: x * FX
							  	  , sum
							  	  , partial(map, getGenevaMarketValue)
							  	  , byCountryFilter(blpData, 'XXX')
							  	)(positions)
							  , 2
							  )


		# Now test different asset types
		"""
		The sum of Equity and Fund is 25,175,114.16, which is the same as the
		Hong Kong equity sum. But Daphne's report has 8,350,682.52 China equity.
		Why?
		"""
		self.assertAlmostEqual( 23396037.80
							  , compose(
							  		lambda x: x * FX
							  	  , sum
							  	  , partial(map, getGenevaMarketValue)
							  	  , byAssetTypeFilter(blpData, 'Equity')
							  	)(positions)
							  , 2
							  )

		# 823 HK and 2823 HK
		self.assertAlmostEqual( 1779076.37
							  , compose(
							  		lambda x: x * FX
							  	  , sum
							  	  , partial(map, getGenevaMarketValue)
							  	  , byAssetTypeFilter(blpData, 'Fund')
							  	)(positions)
							  , 2
							  )


		"""
		For China, 'Fixed Income', 'Additional Tier 1, Contingent Convertibles'
		Daphne's number is 12,513,933.62 , the delta is 8,350,682.53, which is
		China Equity in the above. So that means some convertible bonds are
		considered as Equity by Daphne.
		"""
		self.assertAlmostEqual( 20864616.15
							  , compose(
							  		lambda x: x * FX
							  	  , sum
							  	  , partial(map, getGenevaMarketValue)
							  	  , byAssetTypeFilter(blpData, 'Fixed Income', 'Additional Tier 1, Contingent Convertibles')
							  	  , byCountryFilter(blpData, 'China')
							  	)(positions)
							  , 2
							  )


		self.assertAlmostEqual( 17208645.91
							  , compose(
							  		lambda x: x * FX
							  	  , sum
							  	  , partial(map, getGenevaMarketValue)
							  	  , byAssetTypeFilter(blpData, 'Fixed Income', 'Corporate', 'Investment Grade')
							  	  , byCountryFilter(blpData, 'Hong Kong')
							  	)(positions)
							  , 2
							  )


		self.assertAlmostEqual( 5020919.30
							  , compose(
							  		lambda x: x * FX
							  	  , sum
							  	  , partial(map, getGenevaMarketValue)
							  	  , byAssetTypeFilter(blpData, 'Fixed Income', 'Corporate', 'Non-Investment Grade', 'Non-Financial')
							  	  , byCountryFilter(blpData, 'Macau')
							  	)(positions)
							  , 2
							  )


		self.assertAlmostEqual( 2029888.56
							  , compose(
							  		lambda x: x * FX
							  	  , sum
							  	  , partial(map, getGenevaMarketValue)
							  	  , byAssetTypeFilter(blpData, 'Fixed Income', 'Government / Municipal')
							  	  , byCountryFilter(blpData, 'Asia - others (1)')
							  	)(positions)
							  , 2
							  )


		self.assertAlmostEqual( 13607814.13 
							  , compose(
							  		lambda x: x * FX
							  	  , sum
							  	  , partial(map, getGenevaMarketValue)
							  	  , byAssetTypeFilter(blpData, 'Fixed Income', 'Corporate', 'Non-Investment Grade', 'Financial')
							  	  , byCountryFilter(blpData, 'Asia - others (1)')
							  	)(positions)
							  , 2
							  )


		# Purposely made wrong, since there are no such thing as 
		# 'Fixed Income', 'Government', 'Financial'
		self.assertAlmostEqual( 0
							  , compose(
							  		lambda x: x * FX
							  	  , sum
							  	  , partial(map, getGenevaMarketValue)
							  	  , byAssetTypeFilter(blpData, 'Fixed Income', 'Government / Municipal', 'Financial')
							  	  , byCountryFilter(blpData, 'Asia - others (1)')
							  	)(positions)
							  , 2
							  )