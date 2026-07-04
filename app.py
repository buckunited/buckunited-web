import streamlit as st
import datetime
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

# --- PREMIUM HYBRID HTML REPORT GENERATOR ---
def generate_html_report(portfolio, result, strategy, view_mode, required_daily=0, required_monthly=0):
    # 1. Build the dynamic rows (Using Design 1's structured table layout)
    table_rows = ""
    for item in result['timeline']:
        table_rows += f"""
        <tr class="blank-row">
            <td class="text-center text-gray-400 text-lg">☐</td>
            <td class="text-center text-sm">Month {item['month']}</td>
            <td class="text-center font-mono text-sm">${item['remaining_total_debt']:,.2f}</td>
            <td></td>
        </tr>
        """

    # 2. Handle the Target vs Standard view numbers
    daily_str = f"${required_daily:,.2f}" if view_mode == "Target" else "N/A"
    monthly_str = f"${required_monthly:,.2f}" if view_mode == "Target" else "N/A"

    # 3. Inject into the Hybrid Template
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>BuckUnited Master Plan</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <style>
            /* Base styling */
            body {{ background-color: #e5e7eb; display: flex; justify-content: center; padding: 2rem; font-family: 'Helvetica Neue', sans-serif; color: #1f2937; }}
            .a4-sheet {{ width: 210mm; min-height: 297mm; background: white; box-shadow: 0 20px 25px -5px rgba(0,0,0,0.1); padding: 15mm 20mm; position: relative; margin-bottom: 2rem; }}
            
            /* Print rules to handle 30+ months perfectly */
            @media print {{
                body {{ background: white; padding: 0; }}
                .a4-sheet {{ width: 210mm; height: 297mm; box-shadow: none; margin: 0; padding: 15mm; page-break-after: always; }}
                @page {{ size: A4 portrait; margin: 0; }}
                .no-print {{ display: none !important; }}
                tr {{ page-break-inside: avoid; }} 
            }}
            
            /* Strict Table Styling */
            table {{ width: 100%; border-collapse: collapse; margin-top: 5px; }}
            th, td {{ border: 1px solid #9ca3af; padding: 6px 8px; text-align: left; font-size: 0.875rem; }}
            th {{ background-color: #f3f4f6; font-weight: bold; color: #374151; text-transform: uppercase; font-size: 0.75rem; letter-spacing: 0.05em; }}
            .blank-row td {{ height: 31px; }}
            .fill-line {{ border-bottom: 1px solid #6b7280; flex-grow: 1; margin-left: 8px; }}
            
            /* The Watermark */
            .watermark-container {{ position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%) rotate(-30deg); width: 80%; text-align: center; opacity: 0.05; pointer-events: none; z-index: 0; display: flex; flex-direction: column; align-items: center; justify-content: center; }}
            .watermark-main {{ font-size: 8rem; font-weight: 900; color: #111827; letter-spacing: -0.05em; line-height: 1; white-space: nowrap; }}
            .watermark-sub {{ font-size: 2rem; font-weight: 700; color: #374151; letter-spacing: 0.3em; text-transform: uppercase; margin-top: -10px; }}
            .content-layer {{ position: relative; z-index: 10; }}
        </style>
    </head>
    <body>
        <div class="fixed top-6 right-6 no-print z-50">
            <button onclick="window.print()" class="bg-indigo-600 text-white px-6 py-2.5 rounded-lg shadow-lg hover:bg-indigo-700 transition font-semibold">
                🖨️ Print Master Plan
            </button>
        </div>

        <div class="a4-sheet">
            <div class="watermark-container">
                <div class="watermark-main">BUCKUNITED</div>
                <div class="watermark-sub">FINANCIAL</div>
            </div>
            
            <div class="content-layer">
                <div class="border-b-2 border-gray-800 pb-2 mb-4 flex justify-between items-end">
                    <div>
                        <p class="text-xs font-bold text-indigo-600 tracking-widest mb-1">BUCKUNITED</p> 
                        <h1 class="text-2xl font-black uppercase tracking-wider text-gray-900">Master Financial Action Plan</h1>
                    </div>
                    <div class="text-right no-print">
                        <span class="text-xs bg-gray-200 text-gray-600 px-2 py-1 rounded">A4 Standard Format</span>
                    </div>
                </div>

                <h2 class="text-xs font-bold uppercase tracking-wider text-gray-500 mb-2">Strategy Overview</h2>
                <div class="grid grid-cols-2 gap-x-12 gap-y-4 mb-6 bg-gray-50 p-4 border border-gray-200 rounded-sm">
                    <div class="flex items-end">
                        <span class="font-bold text-sm whitespace-nowrap w-28">Methodology:</span>
                        <span class="text-sm ml-2 font-medium text-gray-800">{strategy.title()}</span>
                    </div>
                    <div class="flex items-end">
                        <span class="font-bold text-sm whitespace-nowrap w-28">Daily Target:</span>
                        <span class="text-sm ml-2 font-medium text-gray-800">{daily_str}</span>
                    </div>
                    <div class="flex items-end">
                        <span class="font-bold text-sm whitespace-nowrap w-28">Timeline:</span>
                        <span class="text-sm ml-2 font-medium text-gray-800">{result['months_to_freedom']} Months</span>
                    </div>
                    <div class="flex items-end">
                        <span class="font-bold text-sm whitespace-nowrap w-28">Monthly Target:</span>
                        <span class="text-sm ml-2 font-medium text-gray-800">{monthly_str}</span>
                    </div>
                    <div class="flex items-end">
                        <span class="font-bold text-sm whitespace-nowrap w-28">Total Interest:</span>
                        <span class="text-sm ml-2 font-medium text-gray-800">${result['total_interest_paid']:,.2f}</span>
                    </div>
                </div>

                <h2 class="text-xs font-bold uppercase tracking-wider text-gray-500 mb-1">Execution Checklist</h2>
                <table>
                    <thead>
                        <tr>
                            <th class="w-12 text-center">Status</th>
                            <th class="w-24 text-center">Timeline</th>
                            <th class="w-32 text-center">Remaining Debt</th>
                            <th class="w-auto text-left">Notes / Actual Paid</th>
                        </tr>
                    </thead>
                    <tbody>
                        {table_rows}
                    </tbody>
                </table>
                
                <div class="mt-8 pt-4 border-t border-gray-200 text-center text-xs text-gray-500">
                    <p>Track your live progress and visualize your trajectory at <b>buckunited-web-km98v3cnxqxunrp4nj7ylr.streamlit.app</b></p>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    return html_content.encode('utf-8')

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
            
            draw_pro_chart(result['timeline'])
            
            st.divider()
            st.markdown("### 🖨️ Your Action Plan")
            html_data = generate_html_report(st.session_state.portfolio, result, active_strat, "Standard")
            st.download_button("🖨️ Download Master Plan (HTML)", data=html_data, file_name='BuckUnited_Master_Plan.html', mime='text/html', type="primary")

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
        
        draw_pro_chart(target_result['timeline'])

        st.divider()
        st.markdown("### 🖨️ Your Action Plan")
        html_data = generate_html_report(target_portfolio, target_result, active_strat, "Target", required_daily, required_monthly)
        st.download_button("🖨️ Download Master Plan (HTML)", data=html_data, file_name='BuckUnited_Master_Plan.html', mime='text/html', type="primary", key="target_dl")
