# coding=utf-8
#
# Build the .req file to generate Bloomberg liquidity report.
# 

from os.path import dirname, abspath



"""
	Get the absolute path to the directory where this module is in.

	This piece of code comes from:

	http://stackoverflow.com/questions/3430372/how-to-get-full-path-of-current-files-directory-in-python
"""
getCurrentDirectory = lambda: \
	dirname(abspath(__file__))
