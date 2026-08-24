from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st


BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "data" / "customer_data.csv"

st.set_page_config(
    page_title="Customer Analysis Dashboard",
    page_icon="CA",
    layout="wide",
)


st.markdown(
    """
    <style>
    .main .block-container {
        padding-top: 1.5rem;
        padding-bottom: 2rem;
        max-width: 1420px;
    }
    .dashboard-title {
        font-size: 2.15rem;
        font-weight: 800;
        color: #172033;
        margin-bottom: 0.2rem;
    }
    .dashboard-subtitle {
        color: #4b5563;
        font-size: 1rem;
        margin-bottom: 1.25rem;
    }
    .kpi-card {
        border: 1px solid #d9e2ec;
        border-radius: 8px;
        padding: 1rem;
        background: #ffffff;
        box-shadow: 0 1px 3px rgba(15, 23, 42, 0.06);
        min-height: 118px;
    }
    .kpi-label {
        color: #5b6472;
        font-size: 0.85rem;
        margin-bottom: 0.35rem;
    }
    .kpi-value {
        color: #111827;
        font-size: 1.55rem;
        font-weight: 800;
        line-height: 1.2;
    }
    .kpi-help {
        color: #6b7280;
        font-size: 0.78rem;
        margin-top: 0.35rem;
    }
    .rule-box {
        border: 1px solid #d9e2ec;
        border-radius: 8px;
        padding: 0.9rem 1rem;
        background: #fbfdff;
        color: #1f2937;
        margin-bottom: 0.75rem;
    }
    .insight-box {
        border-left: 4px solid #0f766e;
        background: #f8fafc;
        padding: 0.85rem 1rem;
        border-radius: 6px;
        margin-bottom: 0.65rem;
        color: #1f2937;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data
def load_customer_data() -> pd.DataFrame:
    """Load, clean, validate, and enrich the customer dataset."""
    df = pd.read_csv(DATA_FILE)
    df.columns = df.columns.str.strip()

    numeric_columns = [
        "Age",
        "Annual Income",
        "Total Purchases",
        "Total Spending",
        "Average Order Value",
        "Purchase Frequency",
        "Recency",
    ]
    for column in numeric_columns:
        df[column] = pd.to_numeric(df[column], errors="coerce")

    df["Last Purchase Date"] = pd.to_datetime(df["Last Purchase Date"], errors="coerce")

    text_columns = ["Gender", "City", "Region", "Preferred Category", "Customer Type"]
    for column in text_columns:
        df[column] = df[column].fillna("Unknown").astype(str).str.strip()
        df.loc[df[column] == "", column] = "Unknown"

    df = df.dropna(subset=["Customer ID", "Age", "Total Purchases", "Total Spending", "Purchase Frequency", "Recency"])
    df = df[
        (df["Age"].between(18, 90))
        & (df["Total Purchases"] > 0)
        & (df["Total Spending"] >= 0)
        & (df["Purchase Frequency"] > 0)
        & (df["Recency"] >= 0)
    ].copy()

    df["Annual Income"] = df.groupby("Region")["Annual Income"].transform(lambda s: s.fillna(s.median()))
    df["Annual Income"] = df["Annual Income"].fillna(df["Annual Income"].median())
    df["Average Order Value"] = df["Total Spending"] / df["Total Purchases"]
    df["Last Purchase Date"] = df["Last Purchase Date"].fillna(pd.Timestamp("2026-08-24") - pd.to_timedelta(df["Recency"], unit="D"))

    df = add_rule_based_segments(df)
    return df.sort_values("Customer ID")


def add_rule_based_segments(df: pd.DataFrame) -> pd.DataFrame:
    """Assign customer segments with transparent analytics rules, not machine learning."""
    segmented = df.copy()
    spending_q25 = segmented["Total Spending"].quantile(0.25)
    spending_q75 = segmented["Total Spending"].quantile(0.75)
    spending_median = segmented["Total Spending"].median()
    frequency_median = segmented["Purchase Frequency"].median()
    recency_q75 = segmented["Recency"].quantile(0.75)

    conditions = [
        (segmented["Recency"] >= recency_q75) & (segmented["Total Spending"] >= spending_median),
        (segmented["Total Spending"] >= spending_q75) & (segmented["Purchase Frequency"] >= frequency_median),
        (segmented["Purchase Frequency"] >= frequency_median) & (segmented["Total Spending"] >= spending_median),
        (segmented["Total Spending"] <= spending_q25),
    ]
    choices = ["At-Risk Customers", "High-Value Customers", "Regular Customers", "Low-Spending Customers"]
    segmented["Customer Segment"] = np.select(conditions, choices, default="Occasional Customers")
    segmented.attrs["segment_rules"] = {
        "spending_q25": spending_q25,
        "spending_q75": spending_q75,
        "spending_median": spending_median,
        "frequency_median": frequency_median,
        "recency_q75": recency_q75,
    }
    return segmented


def format_currency(value: float) -> str:
    return f"${value:,.2f}"


def format_number(value: float) -> str:
    return f"{value:,.1f}"


def format_int(value: float) -> str:
    return f"{value:,.0f}"


def multiselect_filter(label: str, values: pd.Series) -> list[str]:
    options = sorted(values.dropna().unique().tolist())
    return st.sidebar.multiselect(label, options=options, default=options)


def range_slider(label: str, values: pd.Series, step: float = 1.0, money: bool = False) -> tuple[float, float]:
    min_value = float(values.min())
    max_value = float(values.max())
    if min_value == max_value:
        st.sidebar.caption(f"{label}: only one value available")
        return min_value, max_value
    label_text = f"{label} ($)" if money else label
    return st.sidebar.slider(label_text, min_value=min_value, max_value=max_value, value=(min_value, max_value), step=step)


def apply_filters(df: pd.DataFrame) -> pd.DataFrame:
    st.sidebar.header("Filters")
    age_min, age_max = range_slider("Age Range", df["Age"], step=1.0)
    gender = multiselect_filter("Gender", df["Gender"])
    region = multiselect_filter("Region", df["Region"])
    city_source = df[df["Region"].isin(region)]["City"] if region else df["City"]
    city = multiselect_filter("City", city_source)
    income_min, income_max = range_slider("Income Range", df["Annual Income"], step=1000.0, money=True)
    preferred_category = multiselect_filter("Preferred Category", df["Preferred Category"])
    customer_type = multiselect_filter("Customer Type", df["Customer Type"])
    spending_min, spending_max = range_slider("Spending Range", df["Total Spending"], step=100.0, money=True)
    customer_segment = multiselect_filter("Customer Segment", df["Customer Segment"])

    return df[
        (df["Age"].between(age_min, age_max))
        & (df["Gender"].isin(gender))
        & (df["Region"].isin(region))
        & (df["City"].isin(city))
        & (df["Annual Income"].between(income_min, income_max))
        & (df["Preferred Category"].isin(preferred_category))
        & (df["Customer Type"].isin(customer_type))
        & (df["Total Spending"].between(spending_min, spending_max))
        & (df["Customer Segment"].isin(customer_segment))
    ].copy()


def render_kpi_cards(df: pd.DataFrame) -> None:
    total_customers = df["Customer ID"].nunique()
    avg_spending = df["Total Spending"].mean() if total_customers else 0
    avg_order_value = df["Average Order Value"].mean() if total_customers else 0
    avg_frequency = df["Purchase Frequency"].mean() if total_customers else 0
    avg_income = df["Annual Income"].mean() if total_customers else 0
    avg_recency = df["Recency"].mean() if total_customers else 0

    cards = [
        ("Total Customers", format_int(total_customers), "Filtered customer count"),
        ("Avg. Customer Spending", format_currency(avg_spending), "Mean total spending"),
        ("Avg. Order Value", format_currency(avg_order_value), "Mean order value"),
        ("Avg. Purchase Frequency", format_number(avg_frequency), "Purchases per period"),
        ("Avg. Annual Income", format_currency(avg_income), "Mean customer income"),
        ("Avg. Recency", f"{format_number(avg_recency)} days", "Days since last purchase"),
    ]
    cols = st.columns(6)
    for col, (label, value, help_text) in zip(cols, cards):
        col.markdown(
            f"""
            <div class="kpi-card">
                <div class="kpi-label">{label}</div>
                <div class="kpi-value">{value}</div>
                <div class="kpi-help">{help_text}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_segmentation_rules(df: pd.DataFrame) -> None:
    rules = df.attrs.get("segment_rules", {})
    if not rules:
        return
    st.subheader("Rule-Based Customer Segmentation")
    st.markdown(
        f"""
        <div class="rule-box">
        Segments are assigned with transparent business rules using dataset medians and percentiles, not machine learning.
        High-value customers have spending at or above the 75th percentile ({format_currency(rules['spending_q75'])}) and purchase frequency at or above the median ({rules['frequency_median']:.0f}).
        At-risk customers have recency at or above the 75th percentile ({rules['recency_q75']:.0f} days) and spending at or above the median ({format_currency(rules['spending_median'])}).
        Low-spending customers are at or below the 25th spending percentile ({format_currency(rules['spending_q25'])}).
        Other customers are classified as regular or occasional based on spending and purchase frequency.
        </div>
        """,
        unsafe_allow_html=True,
    )


def segment_summary(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()
    summary = (
        df.groupby("Customer Segment")
        .agg(
            Customers=("Customer ID", "nunique"),
            Average_Spending=("Total Spending", "mean"),
            Average_Order_Value=("Average Order Value", "mean"),
            Average_Purchase_Frequency=("Purchase Frequency", "mean"),
            Average_Income=("Annual Income", "mean"),
            Average_Recency=("Recency", "mean"),
        )
        .reset_index()
        .sort_values("Customers", ascending=False)
    )
    total = summary["Customers"].sum()
    summary["Customer Share (%)"] = (summary["Customers"] / total * 100) if total else 0
    return summary


def render_charts(df: pd.DataFrame) -> None:
    segment_counts = df.groupby("Customer Segment", as_index=False)["Customer ID"].nunique().rename(columns={"Customer ID": "Customers"})
    segment_metrics = df.groupby("Customer Segment", as_index=False).agg(
        Total_Spending=("Total Spending", "sum"),
        Purchase_Frequency=("Purchase Frequency", "mean"),
        Average_Order_Value=("Average Order Value", "mean"),
    )
    category_spending = df.groupby("Preferred Category", as_index=False)["Total Spending"].sum().sort_values("Total Spending", ascending=False)
    region_counts = df.groupby("Region", as_index=False)["Customer ID"].nunique().rename(columns={"Customer ID": "Customers"})

    st.subheader("Customer Segment Analysis")
    c1, c2 = st.columns(2)
    segment_bar = px.bar(segment_counts.sort_values("Customers", ascending=False), x="Customer Segment", y="Customers", color="Customer Segment", title="Customer Distribution by Segment", text_auto=True)
    segment_bar.update_layout(xaxis_title="Customer Segment", yaxis_title="Customers", showlegend=False)
    c1.plotly_chart(segment_bar, width="stretch")

    spend_bar = px.bar(segment_metrics.sort_values("Total_Spending", ascending=False), x="Customer Segment", y="Total_Spending", color="Customer Segment", title="Spending by Customer Segment", text_auto=".2s")
    spend_bar.update_layout(xaxis_title="Customer Segment", yaxis_title="Total Spending", yaxis_tickprefix="$", showlegend=False)
    c2.plotly_chart(spend_bar, width="stretch")

    c3, c4 = st.columns(2)
    freq_bar = px.bar(segment_metrics.sort_values("Purchase_Frequency", ascending=False), x="Customer Segment", y="Purchase_Frequency", color="Customer Segment", title="Purchase Frequency by Segment", text_auto=".2f")
    freq_bar.update_layout(xaxis_title="Customer Segment", yaxis_title="Average Purchase Frequency", showlegend=False)
    c3.plotly_chart(freq_bar, width="stretch")

    aov_bar = px.bar(segment_metrics.sort_values("Average_Order_Value", ascending=False), x="Customer Segment", y="Average_Order_Value", color="Customer Segment", title="Average Order Value by Segment", text_auto=".2s")
    aov_bar.update_layout(xaxis_title="Customer Segment", yaxis_title="Average Order Value", yaxis_tickprefix="$", showlegend=False)
    c4.plotly_chart(aov_bar, width="stretch")

    st.subheader("Demographic and Purchase Behavior")
    d1, d2 = st.columns(2)
    age_hist = px.histogram(df, x="Age", nbins=18, color="Gender", title="Age Distribution")
    age_hist.update_layout(xaxis_title="Age", yaxis_title="Customers", bargap=0.08)
    d1.plotly_chart(age_hist, width="stretch")

    income_hist = px.histogram(df, x="Annual Income", nbins=20, color="Customer Segment", title="Income Distribution")
    income_hist.update_layout(xaxis_title="Annual Income", yaxis_title="Customers", xaxis_tickprefix="$", bargap=0.08)
    d2.plotly_chart(income_hist, width="stretch")

    d3, d4 = st.columns(2)
    category_chart = px.bar(category_spending, x="Preferred Category", y="Total Spending", color="Preferred Category", title="Spending by Preferred Category", text_auto=".2s")
    category_chart.update_layout(xaxis_title="Preferred Category", yaxis_title="Total Spending", yaxis_tickprefix="$", showlegend=False)
    d3.plotly_chart(category_chart, width="stretch")

    region_chart = px.pie(region_counts, names="Region", values="Customers", title="Regional Customer Distribution", hole=0.38)
    region_chart.update_traces(textposition="inside", textinfo="percent+label", hovertemplate="%{label}<br>%{value:,} customers<extra></extra>")
    d4.plotly_chart(region_chart, width="stretch")

    recency_hist = px.histogram(df, x="Recency", nbins=20, color="Customer Segment", title="Recency Analysis")
    recency_hist.update_layout(xaxis_title="Days Since Last Purchase", yaxis_title="Customers", bargap=0.08)
    st.plotly_chart(recency_hist, width="stretch")


def generate_insights(df: pd.DataFrame) -> list[str]:
    if df.empty:
        return ["No insights are available because the selected filters returned no customer records."]

    segment_counts = df["Customer Segment"].value_counts()
    segment_spending = df.groupby("Customer Segment")["Total Spending"].mean().sort_values(ascending=False)
    segment_frequency = df.groupby("Customer Segment")["Purchase Frequency"].mean().sort_values(ascending=False)
    category_counts = df["Preferred Category"].value_counts()
    region_counts = df["Region"].value_counts()
    high_value_pct = (df["Customer Segment"].eq("High-Value Customers").mean()) if len(df) else 0
    at_risk_pct = (df["Customer Segment"].eq("At-Risk Customers").mean()) if len(df) else 0
    avg_age = df["Age"].mean()

    return [
        f"The largest customer segment is {segment_counts.index[0]} with {segment_counts.iloc[0]:,} customers.",
        f"{segment_spending.index[0]} has the highest average spending at {format_currency(segment_spending.iloc[0])}.",
        f"{segment_frequency.index[0]} purchases most frequently on average.",
        f"{category_counts.index[0]} is the most preferred category among filtered customers.",
        f"{region_counts.index[0]} has the largest customer base in the current selection.",
        f"Average customer spending is {format_currency(df['Total Spending'].mean())}.",
        f"High-value customers represent {high_value_pct:.1%} of the current customer base.",
        f"At-risk customers represent {at_risk_pct:.1%} of the current customer base.",
        f"The average customer age is {avg_age:.1f} years, which supports simple demographic profiling.",
    ]


def render_segment_table(df: pd.DataFrame) -> None:
    summary = segment_summary(df)
    if summary.empty:
        st.info("No segment summary is available for the current filters.")
        return
    st.dataframe(
        summary,
        width="stretch",
        hide_index=True,
        column_config={
            "Average_Spending": st.column_config.NumberColumn("Average Spending", format="$%.2f"),
            "Average_Order_Value": st.column_config.NumberColumn("Average Order Value", format="$%.2f"),
            "Average_Purchase_Frequency": st.column_config.NumberColumn("Average Purchase Frequency", format="%.2f"),
            "Average_Income": st.column_config.NumberColumn("Average Income", format="$%.2f"),
            "Average_Recency": st.column_config.NumberColumn("Average Recency", format="%.1f days"),
            "Customer Share (%)": st.column_config.NumberColumn("Customer Share", format="%.1f%%"),
        },
    )


def render_customer_table(df: pd.DataFrame) -> None:
    table = df[
        [
            "Customer ID",
            "Age",
            "Gender",
            "Region",
            "City",
            "Annual Income",
            "Total Spending",
            "Average Order Value",
            "Purchase Frequency",
            "Recency",
            "Preferred Category",
            "Customer Type",
            "Customer Segment",
        ]
    ].sort_values("Total Spending", ascending=False)
    st.dataframe(
        table,
        width="stretch",
        hide_index=True,
        column_config={
            "Annual Income": st.column_config.NumberColumn("Annual Income", format="$%.2f"),
            "Total Spending": st.column_config.NumberColumn("Total Spending", format="$%.2f"),
            "Average Order Value": st.column_config.NumberColumn("Average Order Value", format="$%.2f"),
            "Recency": st.column_config.NumberColumn("Recency", format="%.0f days"),
        },
    )


def main() -> None:
    st.markdown('<div class="dashboard-title">Customer Analysis Dashboard</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="dashboard-subtitle">A local Data Analytics dashboard for understanding customer demographics, spending behavior, purchase patterns, and rule-based customer segments.</div>',
        unsafe_allow_html=True,
    )

    df = load_customer_data()
    filtered_df = apply_filters(df)

    if filtered_df.empty:
        st.warning("No customer records match the selected filters. Please adjust the sidebar filters.")
        render_kpi_cards(filtered_df)
        st.subheader("Customer Insights")
        st.info("No insights are available for an empty selection.")
        return

    render_kpi_cards(filtered_df)

    with st.expander("Dataset and Cleaning Summary", expanded=False):
        st.write(
            f"Loaded {len(df):,} cleaned customer records from the local CSV. Dates and numeric columns are validated, missing income values are filled with regional medians, and average order value is recalculated from spending and purchases."
        )
        summary_columns = [
            "Age",
            "Annual Income",
            "Total Purchases",
            "Total Spending",
            "Average Order Value",
            "Purchase Frequency",
            "Recency",
        ]
        st.dataframe(filtered_df[summary_columns].describe(), width="stretch")
        st.write("Missing values after cleaning:")
        st.dataframe(filtered_df.isna().sum().rename("Missing Values").reset_index().rename(columns={"index": "Column"}), width="stretch", hide_index=True)

    render_segmentation_rules(df)

    st.subheader("Segment Summary Table")
    render_segment_table(filtered_df)

    render_charts(filtered_df)

    st.subheader("Customer Insights")
    for insight in generate_insights(filtered_df):
        st.markdown(f'<div class="insight-box">{insight}</div>', unsafe_allow_html=True)

    st.subheader("Filtered Customer Records")
    render_customer_table(filtered_df)


if __name__ == "__main__":
    main()
