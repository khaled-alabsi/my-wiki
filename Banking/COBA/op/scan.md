# Scan — ucc-offer-generator

| Field | Value |
|---|---|
| Repository | wpfe-am (Content Provider) |
| Shared repository | wpfe-shared |
| Profile chain | wpfe → wpfe-am |
| Chains traced | 31 of 31 |
| Analysed at | `main` @ checkpoint not recorded (clean) · shared `main` (clean) |
| Date | 2026-08-09 |

## Summary

The `ucc-offer-generator` module is the core investment-offer engine for the WPFE asset-management platform. It serves a single-page application and a React themenblock through **31 triggers** spanning REST endpoints, an MVC page load, and one scheduled job. The module orchestrates three primary business outcomes: (1) **configuring and validating** customer investment selections against CPMS-defined limits and regulatory rules; (2) **generating offer documents** as PDFs via DocuFamily with optional DDMS archival for compliance; and (3) **persisting** every stage of the advisory session to local database tables. It reaches five external systems — CPMS (Portfolio Operations, Portfolio Details, modules data, product catalogue, model-contracts, investment operations), Contentful CMS, MSL sustainability API, DocuFamily PDF rendering, and DDMS document archive — plus six local database tables. The most important finding is that the simulation endpoint (`compute-simulation`) is a stub throwing `NotImplementedException`; all other 30 triggers are fully operational.

## Chains

One row per trigger. Every chain reached its declared terminals; no chains were skipped or blocked.

| Trigger | Kind | Action point | What it does | Terminals | ACs | Trace |
|---|---|---|---|---|---|---|
| `GET /offer-generator` | mvc-view | `OfferGeneratorPage` | Renders the offer generator SPA entry page, checking VV Flex feature flag and generating a technical process ID for React hydration | db (SETTINGS_SWITCHES), none | 1 | [trace](chain-traces/page-initial-page-load-offer-generator-page.md) |
| `GET /offer-generator/v1/initial-configuration` | rest | `ConfigurationController` | Returns startup configuration — module selection limits, VV Flex flag, online-participant status; syncs module icons from CMS if the icon table is empty | db (MODULE_ICON, SETTINGS_SWITCHES), external (Contentful CMS) | 3 | [trace](chain-traces/get-initial-configuration-configuration-controller.md) |
| `GET /offer-generator/v1/configuration-summary` | rest | `ConfigurationController` | Assembles the configuration summary document data — module hierarchy from CPMS filtered to selected modules, investment volume, risk profile, sustainability text, and localized labels | db (OFFER_GENERATOR_PROCESS), external (CPMS modules API) | 3 | [trace](chain-traces/get-configuration-summary-data-configuration-controller.md) |
| `GET /offer-generator/v1/user-preferences` | rest | `OfferGeneratorController` | Retrieves the customer's saved investment volume and portfolio influence setting from the latest offer data record | db (OFFER_DATA, OFFER_GENERATOR_PROCESS) | 2 | [trace](chain-traces/get-user-preferences-data-offer-generator-controller.md) |
| `GET /offer-generator/v1/offer-generator-process` | rest | `OfferGeneratorController` | Returns all historical offers for a process with their module proportions and configuration, used to render the current screen state | db (OFFER_DATA, MODULE_PROPORTION, OFFER_GENERATOR_DOCUMENT) | 2 | [trace](chain-traces/get-offer-generator-process-offer-generator-controller.md) |
| `GET /offer-generator/v1/offer-data` | rest | `OfferGeneratorController` | Retrieves a complete snapshot of a specific saved offer — investment selections, module proportions, risk profiles, document availability | db (OFFER_DATA, MODULE_PROPORTION, OFFER_GENERATOR_DOCUMENT) | 2 | [trace](chain-traces/get-offer-data-by-offer-id-offer-generator-controller.md) |
| `GET /offer-generator/v1/latest-offer` | rest | `OfferGeneratorController` | Returns the most recent offer for a session with all module allocation weights, risk profiles, quotas, and document presence flag | db (OFFER_DATA, MODULE_PROPORTION, OFFER_GENERATOR_DOCUMENT) | 2 | [trace](chain-traces/get-latest-offer-offer-generator-controller.md) |
| `GET /offer-generator/v1/sustainability-preferences` | rest | `OfferGeneratorController` | Fetches the customer's seven ESG and climate-related sustainability preference flags from MSL external system as boolean toggles | external (MSL sustainability API) | 2 | [trace](chain-traces/get-custom-sustainability-preferences-offer-generator-controller.md) |
| `GET /offer-generator/v1/modules` | rest | `ModulesController` | Retrieves the complete investment module hierarchy from CPMS, enriched with CMS icons and localized translations for de-DE and en-GB | external (CPMS modules API), db (MODULE_ICON), external (Contentful CMS) | 3 | [trace](chain-traces/get-modules-modules-controller.md) |
| `GET /offer-generator/v1/module-details` | rest | `ModulesController` | Returns details for a single module — performance data, allocation groups, and localized CMS content; performance is optional | external (CPMS value series, portfolio growth, modules API), db (MODULE_ICON) | 2 | [trace](chain-traces/get-module-details-modules-controller.md) |
| `GET /offer-generator/v1/global-stocks-distribution` | rest | `ModulesController` | Retrieves global stocks distribution data (market cap weighted, GDP weighted, equally weighted) from Contentful CMS for portfolio allocation display | external (Contentful CMS) | 2 | [trace](chain-traces/get-global-stocks-distribution-modules-controller.md) |
| `GET /offer-generator/v1/product-line` | rest | `ProductLineController` | Retrieves structured product line content (descriptions, cards, modalities, investment strategies) from Contentful CMS for the selected product line and mandate | external (Contentful CMS), none | 2 | [trace](chain-traces/get-details-product-line-controller.md) |
| `GET /offer-generator/v1/model-contracts` | rest | `ModelContractsController` | Retrieves all model contracts for a product line from CPMS; marks one as default based on stocks-and-commodities quota when risk-return profile is provided | external (CPMS model-contracts API), db (STOCKS_COMMODITIES_QUOTA) | 3 | [trace](chain-traces/get-model-contracts-model-contracts-controller.md) |
| `GET /offer-generator/v1/model-contract-by-account` | rest | `ModelContractsController` | Resolves a technical securities account number to its investment guideline and returns the full model contract details from CPMS | external (CPMS Portfolio Operations API, CPMS Portfolio Details API) | 2 | [trace](chain-traces/get-model-contract-by-account-model-contracts-controller.md) |
| `GET /offer-generator/v1/model-contract-performance` | rest | `ModelContractsController` | Retrieves historical performance data — value series chart, yearly returns, total return and annual volatility — from CPMS Portfolio Details API v2 | external (CPMS Portfolio Details API v2), none | 3 | [trace](chain-traces/get-model-contract-performance-model-contracts-controller.md) |
| `GET /offer-generator/v1/validate/allowed-stocks-commodities-quotas` | rest | `ValidateController` | Retrieves all permitted stocks/commodities quota values from the configuration table for a given product line, mandate, and risk profile | db (CUSTOMER_RISK_RETURN_PROFILE_PERMISSIONS) | 2 | [trace](chain-traces/get-allowed-stocks-commodities-quotas-validate-controller.md) |
| `POST /offer-generator/v1/user-preferences` | rest | `OfferGeneratorController` | Captures investment volume and portfolio influence choice; validates minimum 100,000 EUR and persists to two database tables in one transaction | db (OFFER_GENERATOR_PROCESS, OFFER_DATA) | 2 | [trace](chain-traces/post-save-user-preferences-data-offer-generator-controller.md) |
| `POST /offer-generator/v1/product-config` | rest | `OfferGeneratorController` | Persists complete product configuration — module proportions, risk profile, sustainability preference, scenario type — across four database tables in one transaction | db (OFFER_GENERATOR_PROCESS, OFFER_DATA, MODULE_PROPORTION, OFFER_DATA_KPI) | 3 | [trace](chain-traces/post-save-user-product-config-data-offer-generator-controller.md) |
| `POST /offer-generator/v1/productdata` | rest | `OfferGeneratorProductDataController` | Retrieves the full CPMS product catalogue, filters to new-customer-allowed products sorted by risk level, and verifies each against seven suitability rules | external (CPMS product data API) | 3 | [trace](chain-traces/post-retrieve-product-data-offer-generator-product-data-controller.md) |
| `POST /offer-generator/v1/calculate-aggregates` | rest | `CalculateAggregatesController` | Computes portfolio composition from module proportions — retrieves CPMS hierarchy, filters to requested modules, calculates absolute values and enforceable slider limits at every hierarchy level | external (CPMS modules API), none | 3 | [trace](chain-traces/post-calculate-aggregates-calculate-aggregates-controller.md) |
| `POST /offer-generator/v1/compute-simulation` | rest | `SimulationController` | Computes projected financial simulation data for portfolio module configurations; currently a stub throwing NotImplementedException — CPMS integration not wired | none (stub) | 0 | [trace](chain-traces/post-compute-simulations-simulation-controller.md) |
| `POST /offer-generator/v1/generate-document` | rest | `DocumentsController` | Generates customer-facing offer overview PDF via DocuFamily, persists it to the database, and optionally archives in DDMS with compliance metadata | db (OFFER_DATA, OFFER_GENERATOR_PROCESS, OFFER_GENERATOR_DOCUMENT), external (DocuFamily, DDMS, CPMS customer agreement API) | 5 | [trace](chain-traces/post-generate-offer-generator-document-documents-controller.md) |
| `POST /offer-generator/v1/model-contract` | rest | `ModelContractsController` | Persists the user's chosen model contract to CPMS and links it back to the local offer record; idempotent — skips if already saved for this offer | external (CPMS model-contracts API), db (OFFER_DATA) | 2 | [trace](chain-traces/post-save-model-contract-model-contracts-controller.md) |
| `POST /offer-generator/v1/temporary-contract` | rest | `TemporaryContractController` | Creates a temporary contract in CPMS for historical performance lookup; returns the contract ID, cached via Redis on repeated identical calls | external (CPMS Portfolio Investment Operations API) | 2 | [trace](chain-traces/post-save-temporary-contract-temporary-contract-controller.md) |
| `POST /offer-generator/v1/reallocate-modules-weights` | rest | `ModelContractsController` | Computes valid module weight proportions using the WRL algorithm after a user changes selection or adjusts sliders; returns proportions or validation violations | external (CPMS modules API), db (4 WRL weight tables) | 3 | [trace](chain-traces/post-reallocate-modules-weights-model-contracts-controller.md) |
| `POST /offer-generator/v1/validate/model-contract` | rest | `ValidateController` | Validates proposed module weightings against CPMS-defined slider limits and structural rules — checks every module weighting, group constraints, offensive share match, alternative investment minimums | external (CPMS modules API), none | 5 | [trace](chain-traces/post-validate-model-contract-validate-controller.md) |
| `POST /offer-generator/v1/validate/modules-selection` | rest | `ValidateController` | Validates that selected modules can collectively meet model contract target quotas within upper/lower limits; proactively suggests module swaps (individual securities → fund wrappers) for lower-limit violations | external (CPMS modules API), none | 4 | [trace](chain-traces/post-validate-selection-validate-controller.md) |
| `POST /offer-generator/v1/validate/customer-risk-return` | rest | `ValidateController` | Validates stocks-commodities quota allocation and calculated risk-return profile against fixed configuration in CUSTOMER_RISK_RETURN_PROFILE_PERMISSIONS; throws technical exception if config row is missing | db (CUSTOMER_RISK_RETURN_PROFILE_PERMISSIONS) | 3 | [trace](chain-traces/post-validate-customer-risk-return-validate-controller.md) |
| `POST /offer-generator/v1/validate/customer-funds-transfer` | rest | `ValidateController` | Confirms the customer has an active model contract on file in CPMS by resolving account → investment guideline → contract; actual funds transfer validation not yet implemented | external (CPMS Portfolio Operations API, CPMS Portfolio Details API) | 2 | [trace](chain-traces/post-validate-customer-funds-transfer-validate-controller.md) |
| `GET /offer-generator/v1/validate/allowed-stocks-commodities-quotas` | rest | `ValidateController` | Retrieves all permitted stocks/commodities quota values from the configuration table for a given product line, mandate, and risk profile so the UI can present valid options without guessing | db (CUSTOMER_RISK_RETURN_PROFILE_PERMISSIONS) | 2 | [trace](chain-traces/get-allowed-stocks-commodities-quotas-validate-controller.md) |
| `cron = ${application.offer-generator.module-icon-sync.cronExpression:-}` | scheduler | `ModuleIconSyncJob` | Periodically syncs module icons and multi-language translations from Contentful CMS to the local MODULE_ICON table — full diff: create, update, delete orphans | external (Contentful CMS), db (MODULE_ICON) | 3 | [trace](chain-traces/module-icon-sync-job-sync-module-icons.md) |

## Processes

| Process | Repository / module | Reached by | Described in |
|---|---|---|---|
| `OfferGeneratorProcessImpl` | wpfe-am / ucc-offer-generator | 6 chains | [initial-configuration](chain-traces/get-initial-configuration-configuration-controller.md#journey), [user-preferences](chain-traces/get-user-preferences-data-offer-generator-controller.md#journey), [offer-generator-process](chain-traces/get-offer-generator-process-offer-generator-controller.md#journey), [offer-data-by-id](chain-traces/get-offer-data-by-offer-id-offer-generator-controller.md#journey), [latest-offer](chain-traces/get-latest-offer-offer-generator-controller.md#journey), [configuration-summary](chain-traces/get-configuration-summary-data-configuration-controller.md#journey) |
| `OfferGeneratorProductDataProcessImpl` | wpfe-am / ucc-offer-generator | 1 chain | [retrieve-product-data](chain-traces/post-retrieve-product-data-offer-generator-product-data-controller.md#journey) |
| `AggregatesCalculationProcessImpl` | wpfe-am / ucc-offer-generator | 1 chain | [calculate-aggregates](chain-traces/post-calculate-aggregates-calculate-aggregates-controller.md#journey) |
| `SimulationProcessImpl` | wpfe-am / ucc-offer-generator | 1 chain | [compute-simulations](chain-traces/post-compute-simulations-simulation-controller.md#journey) |
| `DocumentsProcessImpl` | wpfe-am / ucc-offer-generator | 1 chain | [generate-document](chain-traces/post-generate-offer-generator-document-documents-controller.md#journey) |
| `ModelContractProcessImpl` | wpfe-am / ucc-offer-generator | 5 chains | [model-contracts](chain-traces/get-model-contracts-model-contracts-controller.md#journey), [model-contract-by-account](chain-traces/get-model-contract-by-account-model-contracts-controller.md#journey), [model-contract-performance](chain-traces/get-model-contract-performance-model-contracts-controller.md#journey), [save-model-contract](chain-traces/post-save-model-contract-model-contracts-controller.md#journey), [reallocate-modules-weights](chain-traces/post-reallocate-modules-weights-model-contracts-controller.md#journey) |
| `ModulesProcessImpl` | wpfe-am / ucc-offer-generator | 3 chains | [modules](chain-traces/get-modules-modules-controller.md#journey), [module-details](chain-traces/get-module-details-modules-controller.md#journey), [global-stocks-distribution](chain-traces/get-global-stocks-distribution-modules-controller.md#journey) |
| `ProductLineProcessImpl` | wpfe-am / ucc-offer-generator | 1 chain | [product-line-details](chain-traces/get-details-product-line-controller.md#journey) |
| `TemporaryContractProcessImpl` | wpfe-am / ucc-offer-generator | 1 chain | [temporary-contract](chain-traces/post-save-temporary-contract-temporary-contract-controller.md#journey) |
| `ValidateModelContractProcessImpl` | wpfe-am / ucc-offer-generator | 2 chains | [validate-model-contract](chain-traces/post-validate-model-contract-validate-controller.md#journey), [allowed-stocks-commodities-quotas](chain-traces/get-allowed-stocks-commodities-quotas-validate-controller.md#journey) |
| `ValidateCustomerRiskReturnProcessImpl` | wpfe-am / ucc-offer-generator | 1 chain | [customer-risk-return](chain-traces/post-validate-customer-risk-return-validate-controller.md#journey) |
| `ValidateModuleSelectionProcessImpl` | wpfe-am / ucc-offer-generator | 1 chain | [modules-selection](chain-traces/post-validate-selection-validate-controller.md#journey) |
| `ValidateCustomerFundsTransferProcessImpl` | wpfe-am / ucc-offer-generator | 1 chain | [customer-funds-transfer](chain-traces/post-validate-customer-funds-transfer-validate-controller.md#journey) |
| `SustainabilityPreferencesProcessImpl` | wpfe-am / ucc-offer-generator | 1 chain | [sustainability-preferences](chain-traces/get-custom-sustainability-preferences-offer-generator-controller.md#journey) |

## Services

| Service | Repository / module | Reached by | Described in |
|---|---|---|---|
| `OfferGeneratorServiceImpl` | wpfe-am / ucc-offer-generator | 6 chains | [initial-configuration](chain-traces/get-initial-configuration-configuration-controller.md#journey), [user-preferences](chain-traces/get-user-preferences-data-offer-generator-controller.md#journey), [offer-generator-process](chain-traces/get-offer-generator-process-offer-generator-controller.md#journey), [offer-data-by-id](chain-traces/get-offer-data-by-offer-id-offer-generator-controller.md#journey), [latest-offer](chain-traces/get-latest-offer-offer-generator-controller.md#journey), [configuration-summary](chain-traces/get-configuration-summary-data-configuration-controller.md#journey) |
| `OfferGeneratorProductDataServiceImpl` | wpfe-am / ucc-offer-generator | 1 chain | [retrieve-product-data](chain-traces/post-retrieve-product-data-offer-generator-product-data-controller.md#journey) |
| `AggregatesCalculationServiceImpl` | wpfe-am / ucc-offer-generator | 2 chains | [calculate-aggregates](chain-traces/post-calculate-aggregates-calculate-aggregates-controller.md#journey), [validate-model-contract](chain-traces/post-validate-model-contract-validate-controller.md#journey) |
| `SimulationServiceImpl` | wpfe-am / ucc-offer-generator | 1 chain | [compute-simulations](chain-traces/post-compute-simulations-simulation-controller.md#journey) |
| `OfferDocumentServiceImpl` | wpfe-am / ucc-offer-generator | 1 chain | [generate-document](chain-traces/post-generate-offer-generator-document-documents-controller.md#journey) |
| `ModelContractServiceImpl` | wpfe-am / ucc-offer-generator | 5 chains | [model-contracts](chain-traces/get-model-contracts-model-contracts-controller.md#journey), [model-contract-by-account](chain-traces/get-model-contract-by-account-model-contracts-controller.md#journey), [model-contract-performance](chain-traces/get-model-contract-performance-model-contracts-controller.md#journey), [save-model-contract](chain-traces/post-save-model-contract-model-contracts-controller.md#journey), [reallocate-modules-weights](chain-traces/post-reallocate-modules-weights-model-contracts-controller.md#journey) |
| `ModulesServiceImpl` | wpfe-am / ucc-offer-generator | 3 chains | [modules](chain-traces/get-modules-modules-controller.md#journey), [module-details](chain-traces/get-module-details-modules-controller.md#journey), [global-stocks-distribution](chain-traces/get-global-stocks-distribution-modules-controller.md#journey) |
| `TemporaryContractServiceImpl` | wpfe-am / ucc-offer-generator | 1 chain | [temporary-contract](chain-traces/post-save-temporary-contract-temporary-contract-controller.md#journey) |
| `ValidateModelContractServiceImpl` | wpfe-am / ucc-offer-generator | 2 chains | [validate-model-contract](chain-traces/post-validate-model-contract-validate-controller.md#journey), [allowed-stocks-commodities-quotas](chain-traces/get-allowed-stocks-commodities-quotas-validate-controller.md#journey) |
| `ValidateCustomerRiskReturnProfileServiceImpl` | wpfe-am / ucc-offer-generator | 2 chains | [customer-risk-return](chain-traces/post-validate-customer-risk-return-validate-controller.md#journey), [allowed-stocks-commodities-quotas](chain-traces/get-allowed-stocks-commodities-quotas-validate-controller.md#journey) |
| `ValidateModulesSelectionServiceImpl` | wpfe-am / ucc-offer-generator | 1 chain | [modules-selection](chain-traces/post-validate-selection-validate-controller.md#journey) |
| `SustainabilityPreferencesServiceImpl` | wpfe-am / ucc-offer-generator | 1 chain | [sustainability-preferences](chain-traces/get-custom-sustainability-preferences-offer-generator-controller.md#journey) |

## MnCs

| MnC | Repository / module | Reached by | Described in |
|---|---|---|---|
| `ContentManagementSystemMnCImpl` | wpfe-am / ucc-offer-generator | 4 chains | [modules](chain-traces/get-modules-modules-controller.md#journey), [module-details](chain-traces/get-module-details-modules-controller.md#journey), [product-line-details](chain-traces/get-details-product-line-controller.md#journey), [global-stocks-distribution](chain-traces/get-global-stocks-distribution-modules-controller.md#journey) |
| `AssetManagementProductMnCImpl` | wpfe-am / ucc-offer-generator | 1 chain | [retrieve-product-data](chain-traces/post-retrieve-product-data-offer-generator-product-data-controller.md#journey) |
| `CalculateValueSeriesV2MnCImpl` | wpfe-am / ucc-offer-generator | 1 chain | [model-contract-performance](chain-traces/get-model-contract-performance-model-contracts-controller.md#journey) |
| `PortfolioGrowthV2MnCImpl` | wpfe-am / ucc-offer-generator | 1 chain | [model-contract-performance](chain-traces/get-model-contract-performance-model-contracts-controller.md#journey), [module-details](chain-traces/get-module-details-modules-controller.md#journey) |
| `DocumentRenderMnCImpl` | wpfe-am / ucc-offer-generator | 1 chain | [generate-document](chain-traces/post-generate-offer-generator-document-documents-controller.md#journey) |
| `ModelContractsMnCImpl` | wpfe-am / ucc-offer-generator | 3 chains | [model-contracts](chain-traces/get-model-contracts-model-contracts-controller.md#journey), [save-model-contract](chain-traces/post-save-model-contract-model-contracts-controller.md#journey), [temporary-contract](chain-traces/post-save-temporary-contract-temporary-contract-controller.md#journey) |
| `ModulesDataMnCImpl` | wpfe-am / ucc-offer-generator | 4 chains | [modules](chain-traces/get-modules-modules-controller.md#journey), [calculate-aggregates](chain-traces/post-calculate-aggregates-calculate-aggregates-controller.md#journey), [reallocate-modules-weights](chain-traces/post-reallocate-modules-weights-model-contracts-controller.md#journey), [validate-selection](chain-traces/post-validate-selection-validate-controller.md#journey) |
| `InvestmentGuidelinesMnCImpl` | wpfe-am / ucc-offer-generator | 2 chains | [model-contract-by-account](chain-traces/get-model-contract-by-account-model-contracts-controller.md#journey), [customer-funds-transfer](chain-traces/post-validate-customer-funds-transfer-validate-controller.md#journey) |
| `CustomerAgreementMnCImplV3` | wpfe-am / ucc-offer-generator | 1 chain | [generate-document](chain-traces/post-generate-offer-generator-document-documents-controller.md#journey) |

## API clients

| API client | Repository / module | Target | Reached by | Described in |
|---|---|---|---|---|
| `ModulesApiClient` | wpfe-shared / cpms | CPMS modules data API | 5 chains | [modules](chain-traces/get-modules-modules-controller.md#journey), [calculate-aggregates](chain-traces/post-calculate-aggregates-calculate-aggregates-controller.md#journey), [reallocate-modules-weights](chain-traces/post-reallocate-modules-weights-model-contracts-controller.md#journey), [validate-selection](chain-traces/post-validate-selection-validate-controller.md#journey), [module-details](chain-traces/get-module-details-modules-controller.md#journey) |
| `ProductDataApiClient` | wpfe-shared / cpms | CPMS product data API | 1 chain | [retrieve-product-data](chain-traces/post-retrieve-product-data-offer-generator-product-data-controller.md#journey) |
| `ModelContractsApi` | wpfe-shared / cpms | CPMS model-contracts API | 3 chains | [model-contracts](chain-traces/get-model-contracts-model-contracts-controller.md#journey), [save-model-contract](chain-traces/post-save-model-contract-model-contracts-controller.md#journey), [temporary-contract](chain-traces/post-save-temporary-contract-temporary-contract-controller.md#journey) |
| `InvestmentGuidelineApiClient` | wpfe-shared / cpms | CPMS Portfolio Operations API | 2 chains | [model-contract-by-account](chain-traces/get-model-contract-by-account-model-contracts-controller.md#journey), [customer-funds-transfer](chain-traces/post-validate-customer-funds-transfer-validate-controller.md#journey) |
| `ModelContractsApiClient` | wpfe-shared / cpms | CPMS Portfolio Details API | 3 chains | [model-contract-by-account](chain-traces/get-model-contract-by-account-model-contracts-controller.md#journey), [customer-funds-transfer](chain-traces/post-validate-customer-funds-transfer-validate-controller.md#journey), [model-contract-performance](chain-traces/get-model-contract-performance-model-contracts-controller.md#journey) |
| `CalculateValueSeriesV2ApiClient` | wpfe-shared / cpms | CPMS Portfolio Details API v2 value series | 1 chain | [model-contract-performance](chain-traces/get-model-contract-performance-model-contracts-controller.md#journey) |
| `PortfolioGrowthV2ApiClient` | wpfe-shared / cpms | CPMS Portfolio Details API v2 portfolio growth | 2 chains | [model-contract-performance](chain-traces/get-model-contract-performance-model-contracts-controller.md#journey), [module-details](chain-traces/get-module-details-modules-controller.md#journey) |
| `TemporaryContractApiClient` | wpfe-shared / cpms | CPMS Portfolio Investment Operations API | 1 chain | [temporary-contract](chain-traces/post-save-temporary-contract-temporary-contract-controller.md#journey) |
| `SustainabilityApiClient` | wpfe-shared / wpfe-shared-regulations | MSL sustainability preferences API | 1 chain | [sustainability-preferences](chain-traces/get-custom-sustainability-preferences-offer-generator-controller.md#journey) |

## Repositories

| Repository | Table | Reached by | Described in |
|---|---|---|---|
| `OfferDataRepository` | OFFER_DATA | 5 chains | [user-preferences](chain-traces/get-user-preferences-data-offer-generator-controller.md#journey), [offer-generator-process](chain-traces/get-offer-generator-process-offer-generator-controller.md#journey), [offer-data-by-id](chain-traces/get-offer-data-by-offer-id-offer-generator-controller.md#journey), [latest-offer](chain-traces/get-latest-offer-offer-generator-controller.md#journey), [save-user-preferences](chain-traces/post-save-user-preferences-data-offer-generator-controller.md#journey) |
| `OfferGeneratorProcessRepository` | OFFER_GENERATOR_PROCESS | 4 chains | [user-preferences](chain-traces/get-user-preferences-data-offer-generator-controller.md#journey), [offer-generator-process](chain-traces/get-offer-generator-process-offer-generator-controller.md#journey), [save-user-preferences](chain-traces/post-save-user-preferences-data-offer-generator-controller.md#journey), [product-config](chain-traces/post-save-user-product-config-data-offer-generator-controller.md#journey) |
| `ModuleProportionRepository` | MODULE_PROPORTION | 3 chains | [offer-generator-process](chain-traces/get-offer-generator-process-offer-generator-controller.md#journey), [offer-data-by-id](chain-traces/get-offer-data-by-offer-id-offer-generator-controller.md#journey), [product-config](chain-traces/post-save-user-product-config-data-offer-generator-controller.md#journey) |
| `OfferGeneratorDocumentRepository` | OFFER_GENERATOR_DOCUMENT | 3 chains | [offer-generator-process](chain-traces/get-offer-generator-process-offer-generator-controller.md#journey), [offer-data-by-id](chain-traces/get-offer-data-by-offer-id-offer-generator-controller.md#journey), [latest-offer](chain-traces/get-latest-offer-offer-generator-controller.md#journey) |
| `CustomerRiskReturnProfilePermissionsRepository` | CUSTOMER_RISK_RETURN_PROFILE_PERMISSIONS | 2 chains | [allowed-stocks-commodities-quotas](chain-traces/get-allowed-stocks-commodities-quotas-validate-controller.md#journey), [customer-risk-return](chain-traces/post-validate-customer-risk-return-validate-controller.md#journey) |
| `ModuleIconRepository` | MODULE_ICON | 2 chains | [initial-configuration](chain-traces/get-initial-configuration-configuration-controller.md#journey), [modules](chain-traces/get-modules-modules-controller.md#journey) |

## Terminals

Where the traced chains actually end.

| Terminal | Kind | Reached by |
|---|---|---|
| CPMS (wpfe-shared / cpms) — modules data API | external | 8 chains |
| CPMS (wpfe-shared / cpms) — product data API | external | 1 chain |
| CPMS (wpfe-shared / cpms) — model-contracts API | external | 3 chains |
| CPMS (wpfe-shared / cpms) — Portfolio Operations API | external | 2 chains |
| CPMS (wpfe-shared / cpms) — Portfolio Details API | external | 3 chains |
| CPMS (wpfe-shared / cpms) — Portfolio Details API v2 value series | external | 1 chain |
| CPMS (wpfe-shared / cpms) — Portfolio Details API v2 portfolio growth | external | 2 chains |
| CPMS (wpfe-shared / cpms) — Portfolio Investment Operations API | external | 1 chain |
| Contentful CMS (wpfe-shared / cms) | external | 5 chains |
| MSL sustainability preferences API (wpfe-shared / wpfe-shared-regulations) | external | 1 chain |
| DocuFamily PDF rendering service | external | 1 chain |
| DDMS documents archive API | external | 1 chain |
| CPMS customer agreement API | external | 1 chain |
| OFFER_DATA (db) | db | 5 chains |
| OFFER_GENERATOR_PROCESS (db) | db | 4 chains |
| MODULE_PROPORTION (db) | db | 3 chains |
| OFFER_GENERATOR_DOCUMENT (db) | db | 3 chains |
| CUSTOMER_RISK_RETURN_PROFILE_PERMISSIONS (db) | db | 2 chains |
| MODULE_ICON (db) | db | 2 chains |
| STOCKS_COMMODITIES_QUOTA (db) | db | 1 chain |
| WRL weight tables (4 tables, db) | db | 1 chain |
| OFFER_DATA_KPI (db) | db | 1 chain |
| SETTINGS_SWITCHES (db) | db | 2 chains |
| — | none | 8 chains (pure computation: aggregates, limits, response assembly, CMS content mapping, UUID generation) |

## Themenblocks

**Provided**

| Name | Port | Index file |
|---|---|
| `offer-generator` | `/wpfe/am/offer-generator` | [tb-offer-generator](chain-traces/tb-offer-generator.md) |

**Consumed**

| Name | contextPath | Used in |
|---|---|---|
| *(none observed)* | — | — |

## Architecture findings

No forbidden dependencies observed. The module follows a clean controller → process → service → MnC / repository layering with no cross-layer violations detected across any of the 31 traced chains.

One uncertain edge: `SimulationServiceImpl` is wired to call CPMS integration classes (`CalculateValueSeriesV2MnC`, `PortfolioGrowthV2MnC`) but currently throws `NotImplementedException` — the wiring exists in the graph but no actual external calls are made at runtime. This is a planned dependency, not a violation.

## Orphans

No processes or services were found that are unreachable from any traced chain. All 14 process classes, 38 service classes, and 9 MnC classes listed above are reached by at least one chain trace.

The `SimulationServiceImpl` is reachable (by the `compute-simulation` chain) but functionally inert — it does not call CPMS despite having the integration classes wired. This is a functional gap rather than an orphan.

## Open questions

- What happens when the MSL sustainability API returns partial data for some of the seven preference flags? — [sustainability-preferences chain](chain-traces/get-custom-sustainability-preferences-offer-generator-controller.md#journey)
- The `compute-simulation` endpoint is a stub; what CPMS integration was planned but not yet wired? — [compute-simulations chain](chain-traces/post-compute-simulations-simulation-controller.md#journey)
- When no configuration row exists in `CUSTOMER_RISK_RETURN_PROFILE_PERMISSIONS`, the system throws a technical exception rather than returning a validation error. Is this intentional operational behavior or should it return a user-facing message? — [customer-risk-return chain](chain-traces/post-validate-customer-risk-return-validate-controller.md#journey)
- The `customer-funds-transfer` validation returns success as soon as a contract is found; actual funds transfer logic (amount checks, balance verification) is not yet implemented. What is the expected scope? — [customer-funds-transfer chain](chain-traces/post-validate-customer-funds-transfer-validate-controller.md#journey)

## Coverage

| Area | Status |
|---|---|
| Chains | 31 of 31 traced |
| Skipped | 0 (none by ignore list) |
| Blocked | 0 |
| Components reached | 14 processes, 38 services, 9 MnCs, 9 API clients, 6 repositories — **observed, not a denominator** |
| wpfe-am, module `ucc-offer-generator` | searched |
| wpfe-am-app | swept for schedulers, jobs and listeners (found: ModuleIconSyncJob) |
| wpfe-shared | entered by pom and import; not swept |
| Other modules | not searched — out of scope |
| React data setters behind the page controller | not traced — by design |
| Host/mainframe behavior | not reachable from a Content Provider |

**Chain coverage is arithmetic**: 31 triggers identified in phase 1, all 31 successfully traced. No chains were skipped or blocked.

**Component counts are observations, not coverage.** Phase 1 deliberately never enumerates the layers, so there is no `M` to report them against — and an untraced chain may reach components no row above mentions.
