import streamlit as st
import pandas as pd

# --- CONFIGURATION ----------------------------------------------------------
CHLOE_RATE = 137.75  # fixed hourly cost for Chloe
CONTRACTOR_FIRST_MONTH = 300
CONTRACTOR_ONGOING_MONTH = 200

PRICES = {
    "Plus": {"Monthly": 500, "6-Month": 500 * 6 * 0.9, "Yearly": 6000},
    "Premium": {"Monthly": 1416, "6-Month": 1416 * 6 * 0.95, "Yearly": 17000},
}
PERIOD_LENGTH = {"Monthly": 1, "6-Month": 6, "Yearly": 12}

# --- PAGE SETUP -------------------------------------------------------------
st.set_page_config(page_title="Sales Margin & TCV Calculator", layout="wide")
st.title("📊 Sales Margin & TCV Calculator")

# --- SIDEBAR INPUTS ---------------------------------------------------------
st.sidebar.header("Calculator Settings")
plan = st.sidebar.selectbox("Select Plan", ["Plus", "Premium"])
billing = st.sidebar.selectbox("Billing Option", ["Monthly", "6-Month", "Yearly"])

discount_type = st.sidebar.radio("Discount Type", ["% Off", "$ Off"])
if discount_type == "% Off":
    discount_pct = st.sidebar.slider("Discount %", 0, 100, 0) / 100
    discount_val = discount_pct
else:
    discount_val_amount = st.sidebar.number_input("Discount Amount ($)", min_value=0.0, value=0.0)
    discount_val = discount_val_amount

min_margin = st.sidebar.slider("Minimum Margin %", 0, 100, 40)
accounts = st.sidebar.number_input("Number of Accounts", min_value=1, value=1)
hours_per_account = st.sidebar.number_input("Hours per Account / Month", min_value=0.0, value=1.0)
period = st.sidebar.selectbox(
    "Analysis Period (months)", [1, 6, 12, 24],
    format_func=lambda m: f"{m} {'month' if m<12 else 'years' if m==24 else 'months'}"
)
new_accounts = 0
if plan == "Premium":
    new_accounts = st.sidebar.number_input(
        "New Accounts in Month 1", min_value=0, max_value=accounts, value=accounts
    )

# --- CORE CALCULATIONS ------------------------------------------------------
list_price_base = PRICES[plan][billing]
if discount_type == "% Off":
    net_price_cycle = list_price_base * (1 - discount_val)
else:
    net_price_cycle = max(list_price_base - discount_val, 0)

cycles = period / PERIOD_LENGTH[billing]
tcv = list_price_base * accounts * cycles
revenue = net_price_cycle * accounts * cycles

chloe_cost = CHLOE_RATE * hours_per_account * accounts * period
contractor_cost = 0
if plan == "Premium":
    ongoing_accounts = accounts - new_accounts
    contractor_cost = (
        CONTRACTOR_FIRST_MONTH * new_accounts +
        CONTRACTOR_ONGOING_MONTH * ongoing_accounts * max(period - 1, 0)
    )
total_cost = chloe_cost + contractor_cost

def safe_margin(rev, cost):
    return ((rev - cost) / rev * 100) if rev else 0
margin_pct = safe_margin(revenue, total_cost)

# --- OUTPUT METRICS ---------------------------------------------------------
st.subheader("Key Metrics")
col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("List Price/Cycle", f"${list_price_base:,.2f}")
col2.metric("Net Price/Cycle", f"${net_price_cycle:,.2f}")
col3.metric("Total Revenue", f"${revenue:,.2f}")
col4.metric("Total Cost", f"${total_cost:,.2f}")
col5.metric(
    "Margin %", f"{margin_pct:.2f}%", delta=f"{margin_pct - min_margin:.2f}%"
)

st.subheader("Margin Threshold")
progress = margin_pct / min_margin if min_margin else 0
st.progress(min(max(progress, 0.0), 1.0))
if margin_pct < min_margin:
    st.error(f"❌ Margin below {min_margin}%! Adjust discount or inputs.")
else:
    st.success(f"✅ Margin meets or exceeds {min_margin}%.")

st.subheader("Total Contract Value (TCV)")
st.write(f"**Pre‑discount TCV:** ${tcv:,.2f}")

st.subheader("Cost Breakdown")
breakdown = {"Chloe Support": f"${chloe_cost:,.2f}"}
if contractor_cost:
    breakdown["Contractor"] = f"${contractor_cost:,.2f}"
breakdown["Total"] = f"${total_cost:,.2f}"

df = pd.DataFrame.from_dict(breakdown, orient="index", columns=["Cost"]).
      rename_axis("Item").reset_index()
st.table(df)

st.caption("Built with ❤️ for your Sales & Finance teams.")
