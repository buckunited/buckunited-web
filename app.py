import streamlit as st
import pandas as pd
import datetime
import io
import plotly.graph_objects as go

# --- CORE MATH ENGINE ---
def calculate_payoff(debts, monthly_budget, strategy="avalanche"):
    if not debts: return {"error": "No debts"}
    
    sorted_debts = sorted(debts, key=lambda x: x['apr'], reverse=True) if strategy == "avalanche" else sorted(debts, key=lambda x: x['balance'], reverse=False)
    months_elapsed = 0
    total_interest = 0
    timeline = []
    
    balances = {d['name']: d['balance'] for d in sorted_debts}
    aprs = {d['name']: d['apr'] for d in sorted_debts}

    while sum(balances.values()) > 0:
        months_elapsed += 1
        remaining_budget = monthly_budget
        
        for name in balances:
            if balances[name] > 0:
                interest = balances[name] * ((aprs[name] / 100) / 12)
                balances[name] += interest
                total_interest += interest

        for name in balances:
            if balances[name] <= 0: continue
            if remaining_budget >= balances[name]:
                remaining_budget -= balances[name]
                balances[name] = 0
            else:
                balances[name] -= remaining_budget
                remaining_budget = 0
                break

        if remaining_budget == monthly_budget and sum(balances.values()) > 0:
            return {"error": "Budget too low"}

        timeline.append({"month": months_elapsed, "remaining_total_debt": round(sum(balances.values()), 2)})

    return {"months_to_freedom": months_elapsed, "total_interest_paid": round(total_interest, 2), "timeline": timeline}

def find_required_budget(debts, target_months, strategy="avalanche"):
    if not debts: return 0
    
    low_guess = sum(d['balance'] for d in debts) / target_months 
    high_guess = sum(d['balance'] for d in debts) * 2 
    best_budget = high_guess
    
    for _ in range(50):
        mid_guess = (low_guess + high_guess) / 2
        res = calculate_payoff(debts, mid_guess, strategy)
        
        if "error" in res:
            low_guess = mid_guess 
            continue
            
        if res['months_to_freedom'] <= target_months:
            best_budget = mid_guess
            high_guess = mid_guess 
        else:
            low_guess = mid_guess 
            
    return best_budget

# --- EXCEL REPORT GENERATOR ---
def generate_excel_report(portfolio, result, strategy, view_mode, required_daily=0, required_monthly=0):
    output = io.BytesIO()
    
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        workbook = writer.book
        worksheet = workbook.add_worksheet('BuckUnited Plan')
        
        worksheet.hide_gridlines(2)
        worksheet.set_paper(9) 
        worksheet.center_horizontally() 
        worksheet.fit_to_pages(1, 0) 
        
        brand_format = workbook.add_format({'bold': True, 'font_size': 24, 'bg_color': '#0F172A', 'font_color': '#FFFFFF', 'align': 'center', 'valign': 'vcenter'})
        subtitle_format = workbook.add_format({'italic': True, 'font_size': 12, 'bg_color': '#0F172A', 'font_color': '#94A3B8', 'align': 'center', 'valign': 'vcenter'})
        header_format = workbook.add_format({'bold': True, 'font_size': 14, 'bottom': 2, 'bottom_color': '#333333', 'font_color': '#0F172A', 'align': 'center', 'valign': 'vcenter'})
        bold_label = workbook.add_format({'bold': True, 'font_size': 12, 'font_color': '#334155', 'align': 'center', 'valign': 'vcenter'})
        money_format = workbook.add_format({'num_format': '$#,##0.00', 'font_size': 12, 'font_color': '#0F172A', 'align': 'center', 'valign': 'vcenter'})
        text_format = workbook.add_format({'font_size': 12, 'font_color': '#0F172A', 'align': 'center', 'valign': 'vcenter'})
        center_box = workbook.add_format({'align': 'center', 'valign': 'vcenter', 'font_size': 16, 'font_color': '#64748B'})
        
        worksheet.set_column('A:A', 15)
        worksheet.set_column('B:B', 20)
        worksheet.set_column('C:C', 25)
        worksheet.set_column('D:D', 20)
        
        worksheet.merge_range('A1:D2', 'BUCKUNITED', brand_format)
        worksheet.merge_range('A3:D3', 'FINANCIAL ACTION PLAN', subtitle_format)
        worksheet.merge_range('A5:D5', 'STRATEGY SUMMARY', header_format)
        
        worksheet.write('A7', 'Methodology:', bold_label)
        worksheet.write('B7', strategy.title(), text_format)
        worksheet.write('A8', 'Timeline:', bold_label)
        worksheet.write('B8', f"{result['months_to_freedom']} Months", text_format)
        worksheet.write('A9', 'Total Interest:', bold_label)
        worksheet.write('B9', result['total_interest_paid'], money_format)
        
        if view_mode == "Target":
            worksheet.write('C8', 'Daily Target:', bold_label)
            worksheet.write('D8', required_daily, money_format)
            worksheet.write('C9', 'Monthly Target:', bold_label)
            worksheet.write('D9', required_monthly, money_format)
            
        worksheet.merge_range('A12:D12', 'MONTHLY EXECUTION CHECKLIST', header_format)
        worksheet.write('A14', 'Status', bold_label)
        worksheet.write('B14', 'Month', bold_label)
        worksheet.write('C14', 'Remaining Target', bold_label)
        worksheet.write('D14', 'Notes', bold_label) 
        
        row = 15
        for item in result['timeline']:
            worksheet.write(row, 0, '☐', center_box) 
            worksheet.write(row, 1, f"Month {item['month']}", text_format)
            worksheet.write(row, 2, item['remaining_total_debt'], money_format)
            worksheet.write(row, 3, '', text_format) 
            row += 1
            
    return output.getvalue()

# --- PREMIUM INTERACTIVE GRAPH ---
def draw_pro_chart(timeline):
    months = [t['month'] for t in timeline]
    balances = [t['remaining_total_debt'] for t in timeline]
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=months, y=balances,
        fill='tozeroy',
        mode='lines+markers',
        line=dict(color='#10B981', width=3), 
        fillcolor='rgba(16, 185, 129, 0.15)', 
        marker=dict(size=8, color='#0F172A', line=dict(width=2, color='#10B981')),
        hovertemplate="Month: %{x}<br>Balance: $%{y:,.2f}<extra></extra>"
    ))
    
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=0, r=0, t=10, b=0),
        xaxis=dict(showgrid=True, gridcolor='#1E293B', title="Timeline (Months)", color='#94A3B8'),
        yaxis=dict(showgrid=True, gridcolor='#1E293B', tickprefix="$", color='#94A3B8'),
        hovermode="x unified",
        font=dict(color='#94A3B8')
    )
    # Renders perfectly on mobile devices
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False}) 

# --- UI SETUP ---
st.set_page_config(page_title="BuckUnited Intake", layout="wide")
st.title("BuckUnited Financial Optimizer")
st.caption("Maximize every dollar. Reverse-engineer your financial freedom.")

if 'portfolio' not in st.session_state:
    st.session_state.portfolio = []

if 'view_mode' not in st.session_state:
    st.session_state.view_mode = "Standard"

# --- SIDEBAR: INTAKE FORM ---
st.sidebar.header("Intake: Add Debt")
with st.sidebar.form("add_debt_form", clear_on_submit=True):
    new_name = st.text_input("Debt Name")
    new_balance = st.number_input("Total Balance ($)", min_value=0.0, step=100.0)
    new_apr = st.number_input("APR (%)", min_value=0.0, step=0.1)
    
    if st.form_submit_button("Add to Portfolio") and new_name:
        st.session_state.portfolio.append({"name": new_name, "balance": new_balance, "apr": new_apr})
        st.rerun()

# --- MAIN DASHBOARD: PORTFOLIO MANAGEMENT ---
st.subheader("Your Current Portfolio")
if len(st.session_state.portfolio) > 0:
    hcol1, hcol2, hcol3, hcol4 = st.columns([3, 2, 2, 1])
    hcol1.markdown("**Debt Name**")
    hcol2.markdown("**Balance**")
    hcol3.markdown("**APR**")
    hcol4.markdown("**Action**")
    st.markdown("---") 
    for i, debt in enumerate(st.session_state.portfolio):
        col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
        col1.write(debt['name'])
        col2.write(f"${debt['balance']:,.2f}")
        col3.write(f"{debt['apr']}%")
        if col4.button("❌", key=f"delete_btn_{i}"):
            st.session_state.portfolio.pop(i) 
            st.rerun() 
    st.write("") 
    if st.button("🗑️ Clear All Debts"):
        st.session_state.portfolio = []
        st.rerun()
else:
    st.info("Add a debt in the sidebar to begin.")

st.divider()

# --- OPTIMIZATION ENGINE ---
if len(st.session_state.portfolio) > 0:
    st.subheader("Optimization Engine")
    
    strat_key = st.radio("Choose Priority Rule", ("Avalanche (Math Focused)", "Snowball (Psychology Focused)"), horizontal=True)
    active_strat = "avalanche" if "Avalanche" in strat_key else "snowball"
    
    if active_strat == "avalanche":
        st.info("🏔️ **The Avalanche Method:** Targets your highest interest rate first. This is mathematically the fastest and cheapest way out of debt, but it might take longer to see your first account hit zero.")
    else:
        st.info("⛄ **The Snowball Method:** Targets your smallest balance first, regardless of interest. This gives you quick psychological victories by closing accounts faster, keeping you motivated.")
    
    st.write("") 
    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button("📊 Standard: I have a set budget", type="primary" if st.session_state.view_mode == "Standard" else "secondary", use_container_width=True):
            st.session_state.view_mode = "Standard"
            st.rerun()
    with col_btn2:
        if st.button("🎯 Target: I have a deadline", type="primary" if st.session_state.view_mode == "Target" else "secondary", use_container_width=True):
            st.session_state.view_mode = "Target"
            st.rerun()
    st.divider()

    # --- STANDARD VIEW ---
    if st.session_state.view_mode == "Standard":
        user_budget = st.slider("Target Monthly Payoff Budget ($)", 100, 5000, 500, 50)
        result = calculate_payoff(st.session_state.portfolio, user_budget, active_strat)
        
        if "error" in result:
            st.error("Budget too low to cover accruing interest.")
        else:
            c1, c2 = st.columns(2)
            c1.metric("Months to Debt-Free", result['months_to_freedom'])
            c2.metric("Total Interest Paid", f"${result['total_interest_paid']}")
            
            # ---> THE NEW GRAPH <---
            draw_pro_chart(result['timeline'])
            
            st.divider()
            st.markdown("### 🖨️ Your Action Plan")
            excel_data = generate_excel_report(st.session_state.portfolio, result, active_strat, "Standard")
            st.download_button("📊 Download Pro Action Plan (Excel)", data=excel_data, file_name='BuckUnited_Action_Plan.xlsx', mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', type="primary")

    # --- TARGET VIEW ---
    elif st.session_state.view_mode == "Target":
        st.markdown("### Reverse Engineer Your Freedom")
        dropdown_options = ["All Debts (Combined Portfolio)"] + [d['name'] for d in st.session_state.portfolio]
        selected_view = st.selectbox("Select Target Scope:", dropdown_options)
        
        target_portfolio = st.session_state.portfolio if selected_view == "All Debts (Combined Portfolio)" else [d for d in st.session_state.portfolio if d['name'] == selected_view]
        target_months = st.slider("I want this completely paid off in (Months):", 1, 120, 24, 1)
        
        required_monthly = find_required_budget(target_portfolio, target_months, active_strat)
        required_daily = required_monthly / 30.4 
        future_date = datetime.date.today() + datetime.timedelta(days=target_months * 30.4)
        
        st.success(f"To pay off **{selected_view}** by **{future_date.strftime('%B %Y')}**, you need to hit this target:")
        c1, c2 = st.columns(2)
        c1.metric("Your Daily Micro-Target", f"${required_daily:.2f} / day")
        c2.metric("Required Monthly Equivalent", f"${required_monthly:.2f} / mo")
        
        target_result = calculate_payoff(target_portfolio, required_monthly, active_strat)
        
        # ---> THE NEW GRAPH <---
        draw_pro_chart(target_result['timeline'])

        st.divider()
        st.markdown("### 🖨️ Your Action Plan")
        excel_data = generate_excel_report(target_portfolio, target_result, active_strat, "Target", required_daily, required_monthly)
        st.download_button("📊 Download Pro Action Plan (Excel)", data=excel_data, file_name='BuckUnited_Action_Plan.xlsx', mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', type="primary", key="target_dl")
