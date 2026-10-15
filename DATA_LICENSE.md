# Data and derived artifacts

The dataset is **Brazilian E-Commerce Public Dataset by Olist**, published by Olist on Kaggle:

- Source: https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce
- Pinned version: 2
- Provider-reported license: **Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International**
- License: https://creativecommons.org/licenses/by-nc-sa/4.0/

Credit Olist and its dataset contributors. The source CSV files are not bundled in this repository. `data/source_manifest.json` records their checksums. Transformations include order aggregation, stated cohort filters, feature generation, fitting, calibration and aggregate evaluation.

The original project source code is licensed under MIT in `LICENSE`. That code license does not replace the dataset's terms. For this educational project, the trained model under `artifacts/` and data-derived outputs under `reports/` are distributed with the Olist attribution and CC BY-NC-SA 4.0 terms. No commercial-use permission is claimed.

The example orders in `examples/` were invented for the demo. They are not copies of real customer records.
