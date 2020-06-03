# coding=utf-8
# 

import unittest2
from risk_report.asset import byCountryFilter, byAssetTypeFilter
from risk_report.geneva import readGenevaInvestmentPositionFile \
							, getGenevaMarketValue
from risk_report.main import loadBlpDataFromFile, getTotalMarketValueFromAssetType \
							, getTotalMarketValueFromCountrynAssetType
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
							  	  , byCountryFilter(blpData, 'China - Mainland')
							  	)(positions)
							  , 2
							  )


		self.assertAlmostEqual( 46753980.08
							  , compose(
							  		lambda x: x * FX
							  	  , sum
							  	  , partial(map, getGenevaMarketValue)
							  	  , byCountryFilter(blpData, 'China - Hong Kong')
							  	)(positions)
							  , 2
							  )


		self.assertAlmostEqual( 10019205.48
							  , compose(
							  		lambda x: x * FX
							  	  , sum
							  	  , partial(map, getGenevaMarketValue)
							  	  , byCountryFilter(blpData, 'China - Macau')
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
		Note that "XS1684793018	POSABK V4.5 PERP" is treated as a special case 
		in 19437, as Equity
		"""
		self.assertAlmostEqual( 31746720.32
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
		self.assertAlmostEqual( 12513933.62
							  , getTotalMarketValueFromCountrynAssetType(
									'20200429'
								  , positions
								  , blpData
								  , 'USD'
								  , 'China - Mainland'
								  , 'Fixed Income'
								  , 'Additional Tier 1, Contingent Convertibles'
								)
							  , 2
							  )


		self.assertAlmostEqual( 17208645.91
							  , getTotalMarketValueFromCountrynAssetType(
									'20200429'
								  , positions
								  , blpData
								  , 'USD'
								  , 'China - Hong Kong'
								  , 'Fixed Income'
								  , 'Corporate'
								  , 'Investment Grade'
								  , 'Financial Institution'
								)
							  , 2
							  )


		self.assertAlmostEqual( 5020919.30
							  , getTotalMarketValueFromCountrynAssetType(
									'20200429'
								  , positions
								  , blpData
								  , 'USD'
								  , 'China - Macau'
								  , 'Fixed Income'
								  , 'Corporate'
								  , 'Non-Investment Grade'
								  , 'Non-Financial Institution'
								)
							  , 2
							  )


		self.assertAlmostEqual( 2029888.56
							  , getTotalMarketValueFromCountrynAssetType(
									'20200429'
								  , positions
								  , blpData
								  , 'USD'
								  , 'Asia - others (1)'
								  , 'Fixed Income'
								  , 'Government / Municipal'
								)
							  , 2
							  )


		self.assertAlmostEqual( 26308960.40
							  , getTotalMarketValueFromCountrynAssetType(
									'20200429'
								  , positions
								  , blpData
								  , 'USD'
								  , 'Asia - others (1)'
								  , 'Fixed Income'
								  , 'Corporate'
								)
							  , 2
							  )


		# Purposely made wrong, since there are no such thing as 
		# 'Fixed Income', 'Government', 'Financial'
		self.assertAlmostEqual( 0
							  , getTotalMarketValueFromCountrynAssetType(
									'20200429'
								  , positions
								  , blpData
								  , 'USD'
								  , 'Asia - others (1)'
								  , 'Fixed Income'
								  , 'Government / Municipal'
								  , 'Financial'
								)
							  , 2
							  )