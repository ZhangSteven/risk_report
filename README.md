# risk_report
The purpose of this package to convert Daphne Keung's Excel application into a Python application.

Purpose of this application:

1. Generate SFC report for DIF.

2. Generate liquidity report for all other portfolios in the company.



## Know Issues

1. A bond has an invest id "XS1684793018 Perfshs" in DIF 2020-04-29 tax file. We need to convert that to ISIN before consolidating the tax lot report.

2. HTM bond not processed yet, i.e., all bonds will remain 

2. Add test case for consolicated positions after merging BLP and Geneva positions.



## Bloomberg Positions

To get position data from Bloomberg,

1. Go to MAV >> Views >> Open Position Views >> choose "Risk-Mon Steven" as the view.

2. Go to Settings >> MAV settings >> Accounts >> choose "RISK_M2" account group, then press "update".

3. On the date field, choose "As of" and input the desired date. Because the default is "Live", then in the output file there will be no date on the 4th line, causing the program to fail.

4. Go to Actions >> Export >> Export to Excel (formatted) to download the output Excel file.
