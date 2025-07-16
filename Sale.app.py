import streamlit as st
import pandas as pd

# --- CONFIGURATION ----------------------------------------------------------
CHLOE_RATE = 137.75             # hidden hourly cost for Chloe
CONTRACTOR_FIRST_FEE = 300       # $ per account month 1 (Premium)
CONTRACTOR_ONGOING_FEE = 200     # $ per account per subsequent month (Premium)

DEFAULT_PRICES = {
    "Plus": {"Monthly": 500, "6-Month": 3900, "Yearly": 5100},
    "Premium": {"Monthly": 1416, "6-Month": 6000, "Yearly": 11900},
}
CYCLE_MONTHS = {"Monthly": 1, "6-Month": 6, "Yearly": 12}

# --- PAGE SETUP -------------------------------------------------------------
st.set_page_config(page_title="Sales Margin & TCV Calculator", layout="wide")
st.title("📊 Sales Margin & TCV Calculator")

# --- SIDEBAR: SETTINGS ------------------------------------------------------
st.sidebar.header("Calculator Settings")

# 1. Plan & Billing
plan = st.sidebar.selectbox("Select Plan", ["Plus", "Premium"])
billing = st.sidebar.selectbox("Billing Cycle", ["Monthly", "6-Month", "Yearly"])

# 2. Pricing Override
default_lp = DEFAULT_PRICES[plan][billing]
list_price = st.sidebar.number_input(
    "List Price per Cycle ($)", min_value=0.0, value=float(default_lp), step=50.0
)

# 3. Discount
discount_type = st.sidebar.radio("Discount Type", ["% Off", "$ Off"])
if discount_type == "% Off":
    discount_pct = st.sidebar.slider("Discount %", 0, 100, 0) / 100
    net_price = list_price * (1 - discount_pct)
    discount_amount = list_price * discount_pct
else:
    discount_amount = st.sidebar.number_input("Discount Amount ($)", min_value=0.0, value=0.0)
    net_price = max(list_price - discount_amount, 0)

# 4. Accounts & Period
duration_months = st.sidebar.selectbox(
    "Analysis Period", [1, 6, 12, 24],
    format_func=lambda x: f"{x} {'month' if x==1 else 'months'}" if x<24 else "2 years"
)
accounts = st.sidebar.number_input("Number of Accounts", min_value=1, value=1)

# 5. Chloe Time per Account
st.sidebar.markdown("---")
st.sidebar.subheader("Chloe Time per Account")
chloe_hours_first = st.sidebar.number_input(
    "First Month Hours", min_value=0.0, value=2.0, step=0.25
)
chloe_hours_ongoing = st.sidebar.number_input(
    "Ongoing Monthly Hours", min_value=0.0, value=1.0, step=0.25
)

# 6. Premium-only: New vs. Ongoing Accounts
new_accounts = 0
if plan == "Premium":
    new_accounts = st.sidebar.number_input(
        "New Accounts in Month 1", min_value=0, max_value=accounts, value=accounts
    )
    # Show contractor cost estimate next to the input
    est_contractor = (
        CONTRACTOR_FIRST_FEE * new_accounts +
        CONTRACTOR_ONGOING_FEE * (accounts - new_accounts) * max(duration_months - 1, 0)
    )
    st.sidebar.metric("Contractor Cost (est.)", f"${est_contractor:,.2f}")

# 7. Minimum Margin Guard
min_margin = st.sidebar.slider("Minimum Margin %", 0, 100, 40)

# --- CALCULATIONS -----------------------------------------------------------
# Billing cycles in the analysis period
cycle_len = CYCLE_MONTHS[billing]
cycles = duration_months / cycle_len

# TCV & Revenue
tcv = list_price * accounts * cycles
revenue = net_price * accounts * cycles

# Discount amount for display
discount_amount = list_price - net_price

# Chloe Cost
total_chloe_cost = (
    CHLOE_RATE * chloe_hours_first * accounts +
    CHLOE_RATE * chloe_hours_ongoing * accounts * max(duration_months - 1, 0)
)

# Contractor Cost (Premium)
contractor_cost = 0
if plan == "Premium":
    ongoing_accounts = accounts - new_accounts
    contractor_cost = (
        CONTRACTOR_FIRST_FEE * new_accounts +
        CONTRACTOR_ONGOING_FEE * ongoing_accounts * max(duration_months - 1, 0)
    )

# Total Cost & Margin
total_cost = round(total_chloe_cost + contractor_cost, 2)
margin_pct = ((revenue - total_cost) / revenue * 100) if revenue else 0

# --- SIDEBAR DISPLAY: CONTRACTOR COST ---------------------------------------
# Show contractor cost estimate in sidebar for validation
st.sidebar.markdown("---")
st.sidebar.metric("Estimated Contractor Cost", f"${contractor_cost:,.2f}")

# --- MAIN OUTPUT ------------------------------------------------------------
st.subheader("Key Metrics")
cols = st.columns(8)
cols[0].metric("List Price/Cycle", f"${list_price:,.2f}")
cols[1].metric("Discount", f"${discount_amount:,.2f}")
cols[2].metric("Net Price/Cycle", f"${net_price:,.2f}")
cols[3].metric("Total Revenue", f"${revenue:,.2f}")
cols[4].metric("Chloe Cost", f"${total_chloe_cost:,.2f}")
cols[5].metric("Contractor Cost", f"${contractor_cost:,.2f}")
cols[6].metric("Total Cost", f"${total_cost:,.2f}")
cols[7].metric("Margin %", f"{margin_pct:.2f}%", delta=f"{margin_pct - min_margin:.2f}%")

st.subheader("Margin Threshold")
progress = margin_pct / min_margin if min_margin else 0
st.progress(min(max(progress, 0.0), 1.0))
if margin_pct < min_margin:
    st.error(f"❌ Margin below {min_margin}%! Adjust inputs.")
else:
    st.success(f"✅ Margin at or above {min_margin}%.")

st.subheader("Total Contract Value (TCV)")
st.write(f"**Pre‑discount TCV:** ${tcv:,.2f}")

st.subheader("Cost Breakdown")
costs = {"Chloe Support": f"${total_chloe_cost:,.2f}"}
if contractor_cost:
    costs["Contractor Fees"] = f"${contractor_cost:,.2f}"
costs["Total Cost"] = f"${total_cost:,.2f}"
cost_df = (
    pd.DataFrame.from_dict(costs, orient="index", columns=["Cost"])  
    .rename_axis("Item")  
    .reset_index()
)
st.table(cost_df)

st.caption("Built with ❤️ for your Sales & Finance teams.")
