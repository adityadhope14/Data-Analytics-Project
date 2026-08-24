# Customer Analysis Dashboard

## Problem Statement

Customer data contains useful information about demographics, spending, purchasing frequency, and recent activity. This project converts a local customer dataset into a clear dashboard that helps explain who the customers are and which groups are most valuable.

## Objective

The objective is to perform traditional customer Data Analytics using descriptive statistics, filtering, aggregation, visual analysis, and transparent rule-based customer segmentation.

## Data Analytics Concepts Used

- Data loading and inspection
- Missing-value handling
- Numeric validation
- Date conversion
- Derived field calculation
- Filtering
- Grouping and aggregation
- Descriptive statistics
- Customer behavior analysis
- Rule-based customer segmentation
- Segment comparison
- Business insight generation

## Technology Stack

- Python
- Pandas
- NumPy
- Streamlit
- Plotly

No machine learning libraries or algorithms are used.

## Dataset Description

The dataset is generated locally and saved at:

`data/customer_data.csv`

Main fields include:

- Customer ID
- Age
- Gender
- City
- Region
- Annual Income
- Total Purchases
- Total Spending
- Average Order Value
- Purchase Frequency
- Last Purchase Date
- Recency
- Preferred Category
- Customer Type

## Data Preprocessing

The app performs simple preprocessing:

- Converts numeric columns into valid numeric values
- Converts `Last Purchase Date` into a date type
- Fills missing text values with `Unknown`
- Fills missing income values using regional medians
- Removes obvious invalid records
- Recalculates average order value from spending and purchases
- Adds a customer segment using transparent business rules

## Rule-Based Segmentation Method

Customer segmentation in this project is NOT machine learning.

The app uses clear analytical rules based on medians and percentiles:

- High-Value Customers: high spending and high purchase frequency
- Regular Customers: above-median spending and purchase frequency
- Occasional Customers: customers who do not meet stronger segment rules
- Low-Spending Customers: customers at or below the lower spending percentile
- At-Risk Customers: customers with high recency and meaningful historical spending

These are deterministic business rules. The project does not use clustering, K-Means, Scikit-learn, classification, regression, or predictive modeling.

## Analysis Methodology

The dashboard filters the customer dataset and calculates KPIs, segment summaries, spending patterns, demographic distributions, category preferences, regional distribution, and recency behavior from the selected data.

## Dashboard Features

- Dynamic customer KPI cards
- Age, gender, region, city, income, category, customer type, spending, and segment filters
- Rule-based segmentation explanation
- Segment summary table with customer share
- Customer distribution by segment
- Spending by customer segment
- Purchase frequency by segment
- Average order value by segment
- Age and income distributions
- Spending by preferred category
- Regional customer distribution
- Recency analysis
- Interactive customer table
- Automatically generated customer insights

## How to Install

From this project folder, run:

```bash
python3 -m pip install -r requirements.txt
```

## How to Run

```bash
streamlit run app.py
```

If `streamlit` is not on your PATH, use:

```bash
python3 -m streamlit run app.py
```

## Expected Output

A local browser window opens with a professional customer analytics dashboard. Filters update the KPIs, visualizations, segment table, insights, and customer records dynamically.

## Key Insights You Can Present

- Largest customer segment
- Highest-spending segment
- Most frequent customer group
- Most preferred product category
- Region with the most customers
- Percentage of high-value customers
- Percentage of at-risk customers
- Basic demographic observations

## Future Improvements

- Add customer lifetime purchase history
- Add product-level customer preferences
- Add exportable filtered reports
- Add more business-defined customer rules
