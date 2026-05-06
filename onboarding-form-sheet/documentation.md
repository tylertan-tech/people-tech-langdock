Workflow Documentation: Onboarding Request → Google Sheets
Overview
This workflow automatically captures IT onboarding requests received via webhook and logs them into a specific tab on a Google Sheet.

Trigger — Webhook
The workflow starts when an HTTP POST request is received at the webhook URL. The request is authenticated via a header secret. It expects a JSON body containing all the onboarding request fields.

Step 1 — Build Row (Code)
A JavaScript code node extracts 21 fields from the webhook payload in the exact column order matching the spreadsheet headers. Any fields missing from the payload are defaulted to null so no columns are skipped.

The fields extracted, in order, are:

Table


#	Field
1	submittedAt
2	requestedAt
3	requestRef
4	department
5	market
6	contractType
7	employeeName
8	privateEmail
9	shippingAddress
10	shippingAddressLine1
11	shippingAddressLine2
12	shippingCity
13	shippingState
14	shippingPostcode
15	shippingCountry
16	officeLocation
17	needsMonitor
18	operatingSystem
19	keyboardLayout
20	osLanguage
21	ipadKeyboard
Step 2 — Append Row to Spreadsheet (Google Sheets)
The row array is appended to the onboarding-automated tab of the target Google Sheet (ID: 1RVc9ScyMliPBeljmssA7fFTDYC3Qk9y7X72G6xRgVRQ). It always writes after the last existing row, so no data is overwritten.

Flow
Webhook → Build Row → Append to Google Sheet