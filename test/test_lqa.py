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