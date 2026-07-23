i have made many sequenced screen shot for process using edge browser that show the ui and the network view i will give you those screen shots you job to map each page to the the called traffic names showed in the network tab i would like to have such structure page name: step: describtion: {what this page about with much details as possiable, max infromation} network-trafix: - xx - xx --- note that if the page or step has no traffic, you should show that are you ready?


---


This is a good format and level of detail for documenting the process. One observation: the screenshots correspond to roughly **16-17 logical pages**, because several screenshots show the same page before/after selecting an option. I merged those into single steps where appropriate.

---

# Step 1

**Page name:** Customer Selection

**Step:** 1

**Description:**

Entry page of the securities account opening (Investment Track: P-ALTERB).

The application identifies the customer for whom the product will be opened.

Displayed information:

* Customer number
* Customer name
* Current process: **Schritt 1 von 4 – Ihre persönlichen Angaben**
* Continue button
* Cancel button

No user input besides confirming the customer.

**Network traffic:**

* generate?name=Wertpapier Frontend&source=01-36-63
* customer-authorization
* info-welcome
* filialeKeepAlive

---

# Step 2

**Page name:** Online Banking Participant Assignment

**Step:** 2

**Description:**

The application asks which Online Banking participant should be linked to the newly created securities account.

Options:

* Existing participant (Felix Fuchs)
* Create depot without Online Banking participant

User selects the participant.

Continue button becomes enabled after a selection.

**Network traffic:**

* write-selected-customer-number
* basic-data
* checkResidency
* checkUSRelations
* regulatoryCheck
* cache-preload
* save-signing-persons
* parallel-process-with-status-processing
* participants
* filialeKeepAlive

---

# Step 3

**Page name:** Existing Process Confirmation

**Step:** 3

**Description:**

System detects an already existing depot opening process for this customer.

User must decide whether to:

* return to the existing process overview
* continue anyway

Warning explains that continuing invalidates the previously stored personal information.

**Network traffic:**

* confirm-selection
* has-completed-process-before

---

# Step 4

**Page name:** Investment Process Introduction

**Step:** 4

**Description:**

Overview page describing the complete workflow.

Shows the four major phases:

* Personal information
* Investment strategy
* Securities account opening
* Completion

Question:

"Is this process a follow-up of an already completed depot opening?"

Options:

* Yes
* No

**Network traffic:**

* securitiesAccountCheck

---

# Step 5

**Page name:** Beneficial Ownership Declaration

**Step:** 5

**Description:**

Legal declaration asking whether the customer acts in their own economic interest.

Question:

"Handeln Sie im eigenen Namen?"

Options:

* Yes
* No

Navigation:

* Continue without contact data
* Maintain contact data

Developer test options are visible at the bottom.

**Network traffic:**

* dcc
* suppress-documents

---

# Step 6

**Page name:** Contact Information

**Step:** 6

**Description:**

The contact data application is opened.

Instead of the expected contact maintenance page, a technical error occurs.

Displayed:

* Technical error
* Correlation ID
* Timestamp
* Backend service
* HTTP 400
* Continue without saving

This indicates a backend integration failure while loading the contact data micro frontend.

**Network traffic:**

* update
* reservation
* asset-manifest.json
* legacyAdapter.js
* remoteEntry.js
* preload-helper
* virtual modules
* api?bpkenn...
* api?bpkenn...

---

# Step 7

**Page name:** Existing Investor Profile

**Step:** 7

**Description:**

Application checks whether the existing investor profile can be reused.

Displays:

* Investment horizon
* Investment objective
* Risk profile (1–7)
* Existing strategy
* Loss capacity
* Experience
* Sustainability notice

Customer confirms the imported profile.

**Network traffic:**

* bundle-investor-profile-finances.js
* sustainability-keys
* summary-page-data
* translations
* keys
* selected-finances
* calculated-risk-acceptance
* calculated-risk-return-profile

---

# Step 8

**Page name:** Investment Strategy Introduction

**Step:** 8

**Description:**

Introductory information before the investment questionnaire.

Explains:

* why questions are asked
* recommendations are non-binding
* strategy will be generated automatically
* downloadable customer information PDF

No data entry.

**Network traffic:**

* None visible

---

# Step 9

**Page name:** Financial Situation Introduction

**Step:** 9

**Description:**

Introduction page explaining that the following pages concern the customer's financial situation.

No inputs.

Only navigation.

**Network traffic:**

* None visible

---

# Step 10

**Page name:** Income Information

**Step:** 10

**Description:**

Collects financial information.

Editable selections include:

* employment status
* household size
* household income
* dependency on investment income

Implemented as inline dropdown selections.

**Network traffic:**

* None visible

---

# Step 11

**Page name:** Assets

**Step:** 11

**Description:**

Captures current wealth.

Fields include:

* monthly disposable income
* financial assets
* additional assets

Values selected from predefined ranges.

**Network traffic:**

* None visible

---

# Step 12

**Page name:** Financial Capacity Result

**Step:** 12

**Description:**

System evaluates financial capacity based on previous answers.

Displays a positive assessment that the customer can tolerate even a complete loss based solely on financial circumstances.

Prepares the transition to personal risk preference.

**Network traffic:**

* None visible

---

# Step 13

**Page name:** Initial Risk Tolerance

**Step:** 13

**Description:**

Collects acceptable temporary loss.

Scenario:

Investment of €10,000.

Customer specifies the maximum acceptable temporary loss after one year.

Current value:

* up to €500

**Network traffic:**

* None visible

---

# Step 14

**Page name:** Risk Preference Scenario

**Step:** 14

**Description:**

More advanced behavioural risk assessment.

Four investment scenarios (A–D) combine potential gains and losses.

Customer selects the scenario matching their comfort level.

Example:

* +10% / −5%
* +20% / −10%
* +30% / −20%
* +40% / −30%

**Network traffic:**

* None visible

---

# Step 15

**Page name:** Investment Knowledge and Experience

**Step:** 15

**Description:**

Determines which investment products the customer is allowed to purchase.

Knowledge levels:

* Basic
* Advanced
* Extensive

Each level unlocks additional product categories.

Visible products include:

* Bonds
* Mixed funds
* Stocks
* Equity funds
* Real estate funds
* Certificates
* Warrants
* Leveraged certificates

**Network traffic:**

* knowledge-and-experience
* save-investorprofile-finances
* bundle-ke-person.js
* product-groups?marketCategory=EQUITY
* pseudonymize-values
* calculated-loss-capacity
* calculated-risk-acceptance

---

# Step 16

**Page name:** Sustainability Introduction

**Step:** 16

**Description:**

Introduction to ESG preferences.

Explains:

* sustainable investing
* future sustainability questions
* investment advice based on sustainability preferences

No input yet.

**Network traffic:**

* sustainability-keys
* save-knowledge-and-experience
* bundle-sustainability.js
* translations

---

# Step 17

**Page name:** Sustainability Preferences per Portfolio

**Step:** 17

**Description:**

Assigns ESG preferences individually to each existing portfolio.

Displayed:

* Newly created retirement portfolio
* Existing advisory portfolios
* Existing direct portfolio

Each portfolio has an edit action for configuring ESG preferences.

Validation indicates that the new portfolio still requires a sustainability preference.

**Network traffic:**

* save-investorprofile-finances
* save-knowledge-and-experience
* sustainability-keys
* translations
* asset-manifest.json
* bundle-sustainability.js

---

Continuation from the previous documentation.

---

# Step 18

**Page name:** Sustainability Preference Selection

**Step:** 18

**Description:**

Configuration page for the sustainability preference of the newly created retirement portfolio.

The customer chooses one of three regulatory sustainability options:

* At least one sustainability standard must be fulfilled.
* Explicitly configure sustainability standards and preferences.
* No sustainability preference (selected).

The selected preference applies only to the current portfolio.

After confirmation the preference is stored.

**Network traffic:**

* save-knowledge-and-experience
* save-investorprofile-finances
* save-sustainability
* sustainability-keys
* translations

---

# Step 19

**Page name:** Sustainability Overview

**Step:** 19

**Description:**

Overview showing the sustainability configuration for every existing portfolio.

Current state:

* New retirement portfolio → No sustainability preference.
* Retirement Base Portfolio → ESG objectives.
* Classic Portfolio → ESG business activities.
* Direct Portfolio → No configuration required.

A success notification confirms the preference has been saved.

**Network traffic:**

* None visible (save already completed)

---

# Step 20

**Page name:** Investment Strategy Recommendation

**Step:** 20

**Description:**

Beginning of **Step 2 of 4 – Investment Strategy**.

The application presents the recommended investment strategy for the newly created retirement portfolio.

Displayed:

* Risk-return profile (Level 5)
* Explanation of risk classes
* Future investment strategy
* Suggested investment horizon
* Suggested investment objective
* Detailed description of the proposed strategy

User may either accept or modify the proposal.

**Network traffic:**

* sustainability-data
* bundle-investorprofile-selection.js
* existing-investorprofile
* deviation-check
* new-investorprofile
* calculate-risk-return-profile
* check-account-profile

---

# Step 21

**Page name:** Strategy Configuration

**Step:** 21

**Description:**

Detailed configuration of the recommended investment strategy.

Editable parameters:

* Investment strategy
* Investment horizon
* Investment objective

Current recommendation:

* Retirement strategy
* Long-term (>5 years)
* Specific retirement provision

After accepting, the strategy is stored.

**Network traffic:**

* save-new-investorprofile
* save-data
* new-customer-info

---

# Step 22

**Page name:** Strategy Proposal Overview

**Step:** 22

**Description:**

Intermediate overview before configuring all portfolios.

Explains that recommendations were generated from previous answers.

Continue proceeds to the depot overview.

**Network traffic:**

* None visible

---

# Step 23

**Page name:** Portfolio Strategy Overview

**Step:** 23

**Description:**

Lists every investment portfolio together with its proposed strategy.

Displays:

* Retirement Base Portfolio
* Classic Portfolio
* Direct Portfolio

Each portfolio may still be modified.

Green indicators show all recommendations are valid.

No changes required.

**Network traffic:**

* existing-investorprofile
* deviation-check

---

# Step 24

**Page name:** Generated Documents

**Step:** 24

**Description:**

Documents generated from the investment profile.

User selects:

* Meeting channel
* Document language

Documents will later appear in the electronic mailbox.

**Network traffic:**

* bundle-wphg-finalization.js
* finalization-page-content
* translations

---

# Step 25

**Page name:** Investment Profile Documents

**Step:** 25

**Description:**

Document download page.

Generated document:

* Investor Profile

Functions:

* Download individual document
* Download all documents
* Confirm documents have been discussed
* Save and continue

**Network traffic:**

* investor-profile-document-opening-bg-creation

---

# Step 26

**Page name:** Retirement Savings Configuration

**Step:** 26

**Description:**

Beginning of the retirement investment recommendation.

Customer enters:

* Monthly savings rate
* First execution date
* Payment interval
* Optional one-time contribution

Developer test panel is visible at the bottom.

**Network traffic:**

* bundle-privatepensionrecommendator.js
* new-customer-info
* save-data

---

# Step 27

**Page name:** Retirement Savings Amount Entered

**Step:** 27

**Description:**

Same page after entering the monthly contribution.

Savings amount has been entered.

The application is ready to calculate a recommendation.

No visible page transition.

**Network traffic:**

* None visible

---

# Step 28

**Page name:** Order Capture

**Step:** 28

**Description:**

Captures consultation metadata.

Fields include:

* Conversation initiator
* Order type
* Meeting location
* Additional participants
* Internal notes

These values document regulatory consultation information.

**Network traffic:**

* save-data
* expected-subsidy
* filialeKeepAlive

---

# Step 29

**Page name:** Fund Recommendation

**Step:** 29

**Description:**

System calculates the recommended retirement investment.

Recommended product:

Future Fund

Displays:

* Monthly investment
* Expected subsidy
* Weighting recommendation
* Product profile
* Detailed investment explanation

Portfolio allocation:

* Defensive fund
* Offensive fund

**Network traffic:**

* expected-subsidy
* save-data

---

# Step 30

**Page name:** Product Documentation

**Step:** 30

**Description:**

Continuation of the recommendation page.

Contains:

Product profile

Available documents:

* Prospectus
* Semi-annual report
* Ex-ante cost information

Customer confirms whether documents were handed out or waived.

Investment recommendation documents can also be downloaded.

**Network traffic:**

* None visible

---

# Step 31

**Page name:** Retirement Configuration Summary

**Step:** 31

**Description:**

Summary of the selected retirement investment.

Shows:

* Selected fund
* Monthly savings rate
* Fund allocation
* Expected subsidy

Customer can still edit the recommendation.

**Network traffic:**

* private-pension-recommendation
* set-reg-passed
* conversation
* save-investment-data
* bundle-private-pension.js
* model-contracts

**Observed response:**

* `private-pension-recommendation` returned **404** (visible in Network).

---

# Step 32

**Page name:** Settlement Account Selection

**Step:** 32

**Description:**

Beginning of **Step 3 of 4 – Depot Opening**.

Customer chooses which current account should be linked to the new securities account.

Options:

* Commerzbank account
* External bank account

Selection is mandatory before continuing.

**Network traffic:**

* save-investment-data
* save-with-special-conditions
* check
* sepa
* cash-accounts

---

# Step 33

**Page name:** Tax Residency

**Step:** 33

**Description:**

Collection of tax residency information.

Displays:

* Existing tax self-certification
* Country list
* Tax identification number
* Signature method
* Ability to add additional countries

Integrated with the fiscal processing system (FAS).

**Network traffic:**

* verify
* settlement-and-reference
* check
* read
* index.BeGDeLe.js
* api?bpkenn...&partyType=PERSON
* info

---

# Step 34

**Page name:** Tax Residency Confirmation

**Step:** 34

**Description:**

Continuation of the tax residency page.

Customer confirms:

* Signature type
* No additional tax residency

Option to generate the tax certificate PDF.

Continue proceeds to finalization.

**Network traffic:**

* log-event

---

# Step 35

**Page name:** Final Review

**Step:** 35

**Description:**

Beginning of **Step 4 of 4 – Completion**.

Complete summary before submission.

Sections include:

* Depot information
* Settlement account
* Generated opening documents
* Customer consent
* Download all documents

Final validation before contract completion.

**Network traffic:**

* initialize-summary-page
* complete
* reserve
* save-involved-bpkenns
* finish-signing-persons
* update
* log-event


Continuation of the process mapping.

---

# Step 36

**Page name:** Customer Consent

**Step:** 36

**Description:**

Final consent page before releasing the depot opening process.

The advisor confirms:

* Opening documents have been provided.
* Signature method is selected.

Available signature methods:

* eSignature (DocuSign)
* photoTAN push
* Paper signature (selected)

The page explains that the advisor may only continue after obtaining the customer's approval.

**Network traffic:**

* find-signing-persons
* titles
* all

---

# Step 37

**Page name:** Documents Download Confirmation

**Step:** 37

**Description:**

Modal dialog shown after downloading the required documents.

Purpose:

* Verify that all required opening documents have been downloaded.
* Display customers whose signatures are available.

Current state:

* Felix Fuchs ✓

Advisor confirms and continues.

**Network traffic:**

* method-update

---

# Step 38

**Page name:** Release Confirmation

**Step:** 38

**Description:**

Final approval screen.

The advisor officially releases the depot opening request.

The page contains:

* Final confirmation icon
* "Freigeben" (Release) button
* Option to cancel the release

This is the final user action before backend processing starts.

**Network traffic:**

* start
* prepare

---

# Step 39

**Page name:** Depot Opening Processing

**Step:** 39

**Description:**

Processing page shown immediately after the release.

The frontend waits while backend systems execute the depot opening workflow.

Displayed:

* Loading animation
* "Ihr Depot wird derzeit eröffnet."

No user interaction.

**Network traffic:**

* approve
* validate-and-save
* add-confirmation
* confirm
* client-identifier-status
* shadow-process-status (repeated polling)

---

# Step 40

**Page name:** Depot Opening Result

**Step:** 40

**Description:**

Final completion page.

The customer data has been fully submitted.

The backend indicates that depot creation has started successfully, but completion is asynchronous.

Message shown:

* If the product cannot be created within the next 24 hours, the bank will contact the customer.

Available actions:

* Go to order overview (Zur Finanzübersicht)

Additional follow-up tasks are displayed:

* Adjustment of exemption orders
* Reduction of US withholding tax
* Online Banking display
* Depot transfer
* DBA authorization

This represents the end of the customer-facing workflow.

**Network traffic:**

* shadow-process-status (multiple polling requests)
* read

---

## Final Process Summary

| Phase                         | Steps |
| ----------------------------- | ----: |
| Step 1 – Personal Information |  1–19 |
| Step 2 – Investment Strategy  | 20–31 |
| Step 3 – Depot Opening        | 32–34 |
| Step 4 – Completion           | 35–40 |

### Main backend APIs observed throughout the complete process

* customer-authorization
* info-welcome
* participants
* write-selected-customer-number
* basic-data
* checkResidency
* checkUSRelations
* regulatoryCheck
* securitiesAccountCheck
* save-signing-persons
* save-investorprofile-finances
* save-new-investorprofile
* save-knowledge-and-experience
* save-sustainability
* save-investment-data
* existing-investorprofile
* deviation-check
* calculate-risk-acceptance
* calculate-risk-return-profile
* calculated-loss-capacity
* calculated-risk-return-profile
* sustainability-keys
* finalization-page-content
* initialize-summary-page
* complete
* approve
* validate-and-save
* confirm
* shadow-process-status
* reserve
* read
* update
* log-event
* filialeKeepAlive

This completes the end-to-end mapping of the depot opening workflow from the initial customer selection through asynchronous backend processing after final approval.

---

