# risk_report
The purpose of this package to convert Daphne Keung's Excel application into a Python application.

Purpose of this application:

1. Generate SFC report for DIF.

2. Generate liquidity report for all other portfolios in the company.



## Considerations

1. What is the datasource for 19437? There are fees not included in the tax lot report such as "audit fees payable". Need to ask Kicoo.

2. Asset allocation: based on a list of filters.
	1. Location: China, Hong Kong, etc.
	2. Asset class: fixed income, equity, fund, commodity. There are sub categories of each asset class, e.g., equity has listed/unlisted/derivatives, and listed equity has financial and non-financial, derivatives has exchanged traded or over-the-counter.

3. When running end of month reports, back office team uses the last working day as the official reporting date, e.g., Apr 29th is the report day for 2020 April. However, risk team (Daphne) seems to use the last calendar day as the reporting day, shall we align them? Because bond prices are different on these two days.



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
