import streamlit as st
import pandas as pd

# --- DEFAULT CONFIGURATION --------------------------------------------------
DEFAULT_PRICES = {
    "Plus": {"Monthly": 500, "6-Month": 500 * 6 * 0.9, "Yearly": 6000},
    "Premium": {"Monthly": 1416, "6-Month": 1416 * 6 * 0.95, "Yearly": 17000},
}
CYCLE_MONTHS = {"Monthly": 1, "6-Month": 6, "Yearly": 12}

# --- PAGE SETUP -------------------------------------------------------------
st.set_page_config(page_title="Sales Margin & TCV Calculator", layout="wide")
st.title("📊 Sales Margin & TCV Calculator")

# --- SIDEBAR: PRICING & DISCOUNT -------------------------------------------
st.sidebar.header("1. Pricing & Discount")
plan = st.sidebar.selectbox("Select Plan", ["Plus", "Premium"])
billing = st.sidebar.selectbox("Billing Cycle", ["Monthly", "6-Month", "Yearly"])

# Allow Bri to override default list price
default_lp = DEFAULT_PRICES[plan][billing]
list_price = st.sidebar.number_input(
    "List Price per Cycle ($)", min_value=0.0, value=float(default_lp), step=50.0
)

discount_type = st.sidebar.radio("Discount Type", ["% Off", "$ Off"])
if discount_type == "% Off":
    discount_pct = st.sidebar.slider("Discount %", 0, 100, 0) / 100
    net_price = list_price * (1 - discount_pct)
else:
    discount_amt = st.sidebar.number_input("Discount Amount ($)", min_value=0.0, value=0.0)
    net_price = max(list_price - discount_amt, 0)

min_margin = st.sidebar.slider("Minimum Margin %", 0, 100, 40)

st.sidebar.markdown("---")

# --- SIDEBAR: ACCOUNTS & PERIOD ---------------------------------------------
st.sidebar.header("2. Accounts & Period")
accounts = st.sidebar.number_input("Number of Accounts", min_value=1, value=1)
period_months = st.sidebar.selectbox(
    "Analysis Period", [1, 6, 12, 24],
    format_func=lambda m: f"{m} {'month' if m<12 else 'years' if m==24 else 'months'}"
)
new_accounts = 0
if plan == "Premium":
    new_accounts = st.sidebar.number_input(
        "New Accounts in Month 1", min_value=0, max_value=accounts, value=accounts
    )

st.sidebar.markdown("---")

# --- SIDEBAR: RESOURCE TIME & RATES -----------------------------------------
st.sidebar.header("3. Resource Time & Rates")
chloe_hours = st.sidebar.number_input(
    "Chloe hours per account/month", min_value=0.0, value=1.0, step=0.25
)
chloe_rate = st.sidebar.number_input(
    "Chloe hourly rate ($)", min_value=0.0, value=137.75, step=1.0
)

contractor_hours_first = contractor_hours_ongoing = contractor_rate = 0
if plan == "Premium":
    contractor_hours_first = st.sidebar.number_input(
        "Contractor hours per account (first month)", min_value=0.0, value=2.0, step=0.5
    )
    contractor_hours_ongoing = st.sidebar.number_input(
        "Contractor hours/account/month (ongoing)", min_value=0.0, value=1.0, step=0.5
    )
    contractor_rate = st.sidebar.number_input(
        "Contractor hourly rate ($)", min_value=0.0, value=100.0, step=1.0
    )

# --- CORE CALCULATIONS ------------------------------------------------------
# Billing cycles and TCV
duration = period_months
cycle_len = CYCLE_MONTHS[billing]
cycles = duration / cycle_len
tcv = list_price * accounts * cycles
revenue = net_price * accounts * cycles

# Chloe cost
chloe_cost = chloe_hours * chloe_rate * accounts * duration
# Contractor cost (Premium only)
contractor_cost = 0
if plan == "Premium":
    ongoing_accounts = accounts - new_accounts
    contractor_cost = (
        contractor_hours_first * contractor_rate * new_accounts +
        contractor_hours_ongoing * contractor_rate * ongoing_accounts * max(duration - 1, 0)
    )
# Total cost
total_cost = chloe_cost + contractor_cost

# Margin
margin_pct = ((revenue - total_cost) / revenue * 100) if revenue else 0

# --- MAIN: OUTPUT & VISUALS ---------------------------------------------
st.subheader("Key Metrics")
col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("List Price/Cycle", f"${list_price:,.2f}")
col2.metric("Net Price/Cycle", f"${net_price:,.2f}")
col3.metric("Total Revenue", f"${revenue:,.2f}")
col4.metric("Total Cost", f"${total_cost:,.2f}")
col5.metric("Margin %", f"{margin_pct:.2f}%", delta=f"{margin_pct - min_margin:.2f}%")

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
breakdown["Total Cost"] = f"${total_cost:,.2f}"

df = pd.DataFrame.from_dict(breakdown, orient="index", columns=["Cost"])\
    .rename_axis("Item")\
    .reset_index()
st.table(df)

st.caption("Built with ❤️ for your Sales & Finance teams.")
