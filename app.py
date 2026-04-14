import streamlit as st
import os
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import random
from datetime import datetime
import json
import bcrypt
import base64
from io import BytesIO

# File‑based “database” paths (plain JSON files – easy to version on GitHub)
USERS_DB_PATH = "data/users.json"


# --- Page Config ---
st.set_page_config(
    page_title="CyberNova Intelligence Hub",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- Directory Setup ---
for p in ["data/sessions","data/analytics_cache","data/reports","data/audit_logs","data/config","data/geoip"]:
    os.makedirs(p, exist_ok=True)

# --- Product Map ---
URI_MAP = {
    "/api/ai_assistant":         "CyberNova AI Assistant",
    "/solutions/threat_monitor": "Threat Monitor Pro",
    "/demos/schedule_demo":      "Discovery Call",
    "/jobs/submit_placement":    "Digital Careers",
    "/events/promotional_event": "Events & Webinars",
    "/home":                     "Landing Page",
}

# Sample city coordinates per country (city, lat, lon)
CITY_MAP = {
    "Botswana": [
        ("Gaborone", -24.6282, 25.9231),
        ("Francistown", -21.1700, 27.5110),
        ("Maun", -19.9833, 23.4167)
    ],
    "South Africa": [
        ("Johannesburg", -26.2041, 28.0473),
        ("Cape Town", -33.9249, 18.4241),
        ("Durban", -29.8587, 31.0218)
    ],
    "Zimbabwe": [
        ("Harare", -17.8252, 31.0335),
        ("Bulawayo", -20.1490, 28.5867),
        ("Mutare", -18.9707, 32.6709)
    ],
    "Namibia": [
        ("Windhoek", -22.5609, 17.0658),
        ("Swakopmund", -22.6780, 14.5450),
        ("Walvis Bay", -22.9575, 14.5053)
    ]
}

# --- Data Enrichment ---
CAMPAIGNS   = ["Organic Search","Google Ads","LinkedIn","Partner Referral","Direct"]
DEVICES     = ["Mobile","Desktop","Tablet"]
INDUSTRIES  = ["Finance","Government","SME","Healthcare","Education"]
WEIGHTS_CAM = [0.35,0.20,0.20,0.15,0.10]
WEIGHTS_DEV = [0.45,0.40,0.15]

def enrich_data(df: pd.DataFrame) -> pd.DataFrame:
    rng = np.random.default_rng(42)
    n = len(df)
    df = df.copy()
    df['product_name']     = df['cs_uri_stem'].map(URI_MAP).fillna("Other")
    df['is_lead']          = df['cs_uri_stem'] == "/demos/schedule_demo"
    df['is_hire']          = df['cs_uri_stem'] == "/jobs/submit_placement"
    df['is_conversion']    = df['is_lead'] | df['is_hire']
    df['lead_score']       = df['product_name'].map({
        "Discovery Call":5,"CyberNova AI Assistant":4,"Threat Monitor Pro":3,
        "Events & Webinars":2,"Digital Careers":2,"Landing Page":1,"Other":1
    }).fillna(1)
    df['campaign_source']  = rng.choice(CAMPAIGNS,n,p=WEIGHTS_CAM)
    df['device_type']      = rng.choice(DEVICES,n,p=WEIGHTS_DEV)
    df['industry_sector']  = rng.choice(INDUSTRIES,n)
    df['session_quality']  = pd.cut(df['time_taken'].clip(lower=1),[0,500,1500,9999],labels=["Fast","Good","Slow"],include_lowest=True)
    df['deal_value_usd']   = np.where(df['is_lead'],
                                  rng.integers(1000,80001,n),0)
    # Add a random city per row based on country
    def pick_city(country):
        choices = CITY_MAP.get(country, [])
        if not choices:
            return None, None, None
        city, lat, lon = rng.choice(choices)
        return city, lat, lon
    df[['city','city_lat','city_lon']] = df.apply(
        lambda row: pd.Series(pick_city(row['actual_country'])), axis=1)
    return df

@st.cache_data
def load_data() -> pd.DataFrame:
    try:
        df = pd.read_csv("data/CyberNova_Web_Logs.csv")
        df['date_time'] = pd.to_datetime(df['date_time'])
        enriched = enrich_data(df)
        # Save enriched CSV for offline use
        enriched_path = "data/CyberNova_Web_Logs_enriched.csv"
        enriched.to_csv(enriched_path, index=False)
        return enriched
    except Exception:
        return pd.DataFrame()

# ---------------------------------------------------------------------------
# Simple JSON‑based user “database” helpers
def _ensure_user_db():
    """Create an empty JSON file if it does not exist yet."""
    if not os.path.isfile(USERS_DB_PATH):
        with open(USERS_DB_PATH, "w", encoding="utf-8") as f:
            json.dump([], f)

def load_users() -> list:
    """Return a list of user dicts from the JSON file."""
    _ensure_user_db()
    with open(USERS_DB_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def add_user(username: str, role: str, region: str, password: str) -> None:
    """Append a new user record with hashed password."""
    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    users = load_users()
    users.append({
        "Username": username,
        "Role": role,
        "Region": region,
        "Password": hashed,
        "Last Login": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })
    with open(USERS_DB_PATH, "w", encoding="utf-8") as f:
        json.dump(users, f, indent=2)
    log_audit("SYSTEM", f"Added user: {username} (Role: {role})")

def delete_user(username: str) -> bool:
    """Remove a user by their username."""
    users = load_users()
    filtered = [u for u in users if u["Username"] != username]
    if len(filtered) == len(users):
        return False
    with open(USERS_DB_PATH, "w", encoding="utf-8") as f:
        json.dump(filtered, f, indent=2)
    log_audit("SYSTEM", f"Deleted user: {username}")
    return True

def log_audit(username, action):
    """Write action to monthly audit log file."""
    now = datetime.now()
    log_path = f"data/audit_logs/audit_{now.strftime('%Y_%m')}.log"
    entry = f"[{now.strftime('%Y-%m-%d %H:%M:%S')}] USER: {username} | ACTION: {action}\n"
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(entry)

# --- Reporting Engine ---
def generate_csv_report(df):
    return df.to_csv(index=False).encode('utf-8')

def generate_excel_report(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Dashboard Report')
    return output.getvalue()


# --- CSS + Font ---
def inject_css():
    st.html("""
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
    html,body,[class*="css"]{font-family:'Inter',sans-serif!important;}
    #MainMenu,header,footer{visibility:hidden;}
    .block-container{padding-top:1.5rem!important;padding-bottom:1.5rem!important;max-width:1600px;}
    [data-testid="stSidebar"]{background:linear-gradient(160deg,#1e1b4b 0%,#0f172a 100%)!important;border-right:none;}
    [data-testid="stSidebar"] *{color:#e0e7ff!important;}
    .stRadio>div[role="radiogroup"]>label{padding:10px 14px;margin-bottom:5px;border-radius:10px;border:1px solid rgba(255,255,255,0.07);background:rgba(255,255,255,0.04);transition:all .2s;cursor:pointer;}
    .stRadio>div[role="radiogroup"]>label:hover{background:rgba(99,102,241,.3);border-color:#6366f1;}
    .kpi-card{background:#ffffff;border-radius:16px;padding:22px 24px;border:1px solid #f1f5f9;box-shadow:0 1px 3px rgba(0,0,0,.06);transition:transform .2s,box-shadow .2s;margin-bottom:16px;}
    .kpi-card:hover{transform:translateY(-4px);box-shadow:0 8px 24px rgba(99,102,241,.12);}
    .kpi-label{font-size:.72rem;font-weight:700;letter-spacing:.1em;text-transform:uppercase;color:#94a3b8;margin-bottom:8px;}
    .kpi-value{font-size:2.1rem;font-weight:800;color:#1e1b4b;line-height:1;}
    .kpi-sub{font-size:.8rem;font-weight:600;margin-top:8px;}
    .kpi-pos{color:#0d9488;} .kpi-neg{color:#dc2626;}
    .kanban-col{background:#f8fafc;border:1px solid #e2e8f0;border-radius:16px;padding:20px;min-height:280px;}
    .kanban-header{font-weight:700;font-size:1rem;color:#1e1b4b;margin-bottom:12px;padding-bottom:10px;border-bottom:2px solid #6366f1;}
    @keyframes livepulse{0%,100%{opacity:1;}50%{opacity:.3;}}
    .live-dot{display:inline-block;width:10px;height:10px;border-radius:50%;background:#dc2626;margin-right:8px;animation:livepulse 1.5s infinite;vertical-align:middle;}
    .alert-row{padding:8px 12px;border-radius:8px;margin-bottom:6px;font-size:.85rem;display:flex;justify-content:space-between;}
    .alert-danger{background:#fef2f2;border-left:3px solid #dc2626;color:#991b1b;}
    .alert-warn{background:#fffbeb;border-left:3px solid #f59e0b;color:#92400e;}
    .alert-ok{background:#f0fdf4;border-left:3px solid #16a34a;color:#14532d;}
    .section-title{font-size:1.3rem;font-weight:700;color:#1e1b4b;margin-bottom:12px;margin-top:4px;}
    /* Placeholder styling */
    /* Placeholder styling - made black for visibility */
    ::placeholder {color:#000000!important; opacity:1!important;}
    input::placeholder {color:#000000!important;}
    </style>
    """)

# --- Helpers ---
def trend_arrow(current: float, previous: float) -> str:
    """Return an up/down arrow indicating trend."""
    if current > previous: return "📈"
    if current < previous: return "📉"
    return "⏺"

def kpi(label, value, sub="", positive=True):
    cls = "kpi-pos" if positive else "kpi-neg"
    sub_html = f'<div class="kpi-sub {cls}">{sub}</div>' if sub else ""
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">{label}</div>
        <div class="kpi-value">{value}</div>
        {sub_html}
    </div>""", unsafe_allow_html=True)

def section(title):
    st.markdown(f'<div class="section-title">{title}</div>', unsafe_allow_html=True)

# ── PLOTLY THEME ─────────────────────────────────────────────
PLT_LAYOUT = dict(
    plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
    font=dict(family="Outfit",color="#334155"),
    margin=dict(t=10,b=10,l=10,r=10),
)
COLORS = ["#4f46e5","#0d9488","#f59e0b","#dc2626","#8b5cf6","#06b6d4"]

# ═══════════════════════════════════════
# AUTH
# ═══════════════════════════════════════
def login():
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        st.markdown("""
        <div style="text-align:center;margin-bottom:1.5rem;">
            <div style="font-size:2.8rem;font-weight:800;color:#1e1b4b;line-height:1.1;">CyberNova</div>
            <div style="font-size:1.1rem;color:#6366f1;font-weight:700;margin-bottom:8px;letter-spacing:1px;text-transform:uppercase;">Intelligence Hub</div>
            <div style="font-size:.9rem;color:#64748b;line-height:1.4;">Secure Operations & Analytics for Southern Africa</div>
        </div>
        """, unsafe_allow_html=True)
        
        with st.form("auth", border=True):
            st.markdown("<div style='text-align:center;font-size:1rem;color:#334155;font-weight:600;margin-bottom:16px;'>Sign In</div>", unsafe_allow_html=True)
            u = st.text_input("Username", placeholder="admin")
            p = st.text_input("Password", type="password", placeholder="••••••••")
            btn = st.form_submit_button("Access Dashboard", use_container_width=True)
            if btn:
                u_clean = u.strip()
                # 1. Hardcoded admin fallback (Highest Priority)
                if u_clean == "admin" and p == "admin":
                    st.session_state.update({"authenticated":True,"role":"Administrator","username":"admin"})
                    log_audit("admin", "Logged in (Root Access)")
                    st.rerun()

                # 2. Check Database
                users = load_users()
                valid_user = None
                for user in users:
                    if user.get("Username") == u_clean:
                        stored_pw = user.get("Password", "")
                        try:
                            if bcrypt.checkpw(p.encode('utf-8'), stored_pw.encode('utf-8')):
                                valid_user = user
                                break
                        except Exception:
                            if stored_pw == p:
                                valid_user = user
                                break

                if valid_user:
                    st.session_state.update({"authenticated":True,"role":valid_user.get("Role","Viewer"),"username":valid_user["Username"]})
                    log_audit(valid_user["Username"], "Logged in")
                    st.rerun()
                else:
                    log_audit(u_clean or "UNKNOWN", f"Failed login attempt")
                    st.error("Invalid credentials")

# ═══════════════════════════════════════
# PAGE 1 — LIVE OPERATIONS BOARD
# ═══════════════════════════════════════
@st.fragment(run_every="2s")
def live_board():
    if 'lb' not in st.session_state:
        st.session_state['lb'] = load_data().tail(800).copy()
    df = st.session_state['lb']

    # --- simulate incoming events ---
    new = []
    for _ in range(random.randint(3,10)):
        uri = random.choices(list(URI_MAP.keys()),weights=[25,20,15,15,15,10])[0]
        new.append({
            'date_time': pd.Timestamp.now(),
            'c_ip': f"{random.randint(10,200)}.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(0,255)}",
            'cs_method': random.choice(["GET","GET","GET","POST"]),
            'cs_uri_stem': uri,
            'sc_status': random.choices([200,200,200,200,302,404,500],[55,15,10,8,5,5,2])[0],
            'sc_bytes': random.randint(800,14000),
            'time_taken': random.randint(60,2000),
            'actual_country': random.choices(['Botswana','South Africa','Zimbabwe','Namibia'],[40,35,15,10])[0],
        })
    new_df = enrich_data(pd.DataFrame(new))
    df = pd.concat([df, new_df], ignore_index=True).iloc[-2000:]
    st.session_state['lb'] = df

    # ── KPIs ──
    prev_err = st.session_state.get("prev_err_rate", 0)
    
    c1,c2,c3,c4 = st.columns(4)
    active_users = df['c_ip'].nunique()
    leads_today  = df['is_lead'].sum()
    revenue      = df['deal_value_usd'].sum()
    err_rate     = (df['sc_status']>=400).mean()*100
    
    with c1: kpi("Active Users Now", f"{active_users:,}", "unique IPs in buffer")
    with c2: kpi("Demo Requests",    f"{int(leads_today):,}",  "discovery calls booked", True)
    with c3: kpi("Pipeline Value",   f"${revenue:,.0f}", "simulated deal value", True)
    with c4:
        arrow = trend_arrow(err_rate, prev_err)
        kpi("Disrupted Sessions", f"{err_rate:.1f}% {arrow}", "error rate", err_rate<5)

    st.session_state["prev_err_rate"] = err_rate

    # ── Row 2 ──
    c_left, c_right = st.columns([2,1])
    with c_left:
        section("Engagement Pulse (Live)")
        pulse = df.groupby(df['date_time'].dt.floor('2s')).size().tail(40).reset_index(name='Users')
        pulse.columns = ['Time','Users']
        fig = px.area(pulse,x='Time',y='Users',color_discrete_sequence=["#4f46e5"])
        fig.update_layout(**PLT_LAYOUT, height=220)
        fig.update_traces(fill='tozeroy',line_width=2)
        st.plotly_chart(fig, use_container_width=True)

    with c_right:
        section("Products Explored")
        prod = df['product_name'].value_counts().reset_index()
        prod.columns=['Product','Count']
        fig2 = px.pie(prod, values='Count', names='Product', hole=0.55,
                      color_discrete_sequence=COLORS)
        fig2.update_layout(**PLT_LAYOUT, height=220, showlegend=True,
                           legend=dict(font=dict(size=10)))
        st.plotly_chart(fig2, use_container_width=True)

    # ── Row 3: alerts + live feed ──
    c_feed, c_alerts = st.columns([3,2])
    with c_feed:
        section("Live Event Stream")
        feed = df.sort_values('date_time',ascending=False).head(8)[
            ['date_time','actual_country','product_name','sc_status','deal_value_usd']].copy()
        feed.columns = ['Time','Country','Product','Status','Deal $']
        feed['Time'] = feed['Time'].dt.strftime('%H:%M:%S')
        st.dataframe(feed, hide_index=True, use_container_width=True)
    with c_alerts:
        section("System Alerts")
        errs = df[df['sc_status']>=500]
        warns = df[df['sc_status']==404]
        if len(errs): st.markdown(f'<div class="alert-row alert-danger"><span>Server Errors (5xx)</span><b>{len(errs)}</b></div>', unsafe_allow_html=True)
        if len(warns): st.markdown(f'<div class="alert-row alert-warn"><span>Not Found (404)</span><b>{len(warns)}</b></div>', unsafe_allow_html=True)
        ok = df[df['sc_status']==200]
        st.markdown(f'<div class="alert-row alert-ok"><span>Successful (200)</span><b>{len(ok)}</b></div>', unsafe_allow_html=True)
        slowsess = (df['session_quality']=='Slow').sum()
        if slowsess: st.markdown(f'<div class="alert-row alert-warn"><span>Slow Sessions</span><b>{slowsess}</b></div>', unsafe_allow_html=True)

def page_live():
    now = datetime.now().strftime('%H:%M:%S')
    st.markdown(f'<h1 style="font-size:2rem;font-weight:800;color:#1e1b4b;margin-bottom:4px;">'
                f'<span class="live-dot"></span>Live Operations Board</h1>'
                f'<p style="color:#94a3b8;font-size:.85rem;margin-bottom:24px;">Last refresh: {now} — auto-updates every 2 seconds</p>', unsafe_allow_html=True)
    live_board()

# ═══════════════════════════════════════
# PAGE 2 — MARKETING INTELLIGENCE
# ═══════════════════════════════════════
def page_marketing(df):
    st.markdown('<h1 style="font-size:2rem;font-weight:800;color:#1e1b4b;margin-bottom:24px;">Audience Intelligence</h1>', unsafe_allow_html=True)
    if df.empty: st.error("No data"); return

    # KPIs
    prev_fast = st.session_state.get("prev_fast_pct", 0)
    
    c1,c2,c3,c4 = st.columns(4)
    top_campaign = df['campaign_source'].value_counts().idxmax()
    top_product  = df['product_name'].value_counts().idxmax()
    fast_pct     = (df['session_quality']=='Fast').mean()*100
    with c1: kpi("Total Visitors",    f"{df['c_ip'].nunique():,}",     "unique IPs")
    with c2: kpi("Best Channel",       top_campaign,                    "top campaign source")
    with c3: kpi("Most Visited",       top_product,                     "top CyberNova service")
    with c4:
        arrow_fast = trend_arrow(fast_pct, prev_fast)
        kpi("Fast Sessions", f"{fast_pct:.1f}% {arrow_fast}", "load < 500ms", fast_pct>50)

    st.session_state["prev_fast_pct"] = fast_pct

    # Row 2: campaign bar + device donut
    c_bar, c_pie = st.columns([3,2])
    with c_bar:
        section("Campaign Source vs Conversions")
        camp = df.groupby('campaign_source').agg(Visits=('c_ip','count'), Conversions=('is_conversion','sum')).reset_index()
        fig = px.bar(camp, x='campaign_source', y=['Visits','Conversions'],
                     barmode='group', color_discrete_sequence=["#4f46e5","#0d9488"])
        fig.update_layout(**PLT_LAYOUT, height=260)
        st.plotly_chart(fig, use_container_width=True)
    with c_pie:
        section("Device Breakdown")
        dev = df['device_type'].value_counts().reset_index()
        dev.columns=['Device','Count']
        fig2 = px.pie(dev, values='Count', names='Device', hole=0.55,
                      color_discrete_sequence=["#4f46e5","#0d9488","#f59e0b"])
        fig2.update_layout(**PLT_LAYOUT, height=260)
        st.plotly_chart(fig2, use_container_width=True)

    # Row 3: geo map + growth line
    c_map, c_line = st.columns([3,2])
    with c_map:
        section("Visitor Origins (OpenStreetMap)")
        coords = {'Botswana':(-22.33,24.68),'South Africa':(-30.56,22.94),'Zimbabwe':(-19.02,29.15),'Namibia':(-22.96,18.49)}
        geo = df.groupby('actual_country')['c_ip'].nunique().reset_index()
        geo.columns=['Country','Visitors']
        geo['lat'] = geo['Country'].map(lambda c: coords.get(c,(0,0))[0])
        geo['lon'] = geo['Country'].map(lambda c: coords.get(c,(0,0))[1])
        # Show cities as individual points
        city_df = df.dropna(subset=['city_lat','city_lon']).drop_duplicates(['city','city_lat','city_lon'])
        fig3 = px.scatter_mapbox(city_df,
                                 lat='city_lat', lon='city_lon',
                                 hover_name='city', 
                                 hover_data={'actual_country': True, 'city_lat': False, 'city_lon': False},
                                 color='actual_country', size_max=15,
                                 zoom=4.5,
                                 mapbox_style='open-street-map',
                                 color_continuous_scale=px.colors.sequential.Teal,
                                 center={'lat':-22.5,'lon':23.5})
        # Note: Reloading to ensure column name fix is applied.
        fig3.update_layout(margin=dict(r=0,t=0,l=0,b=0),height=300)
        st.plotly_chart(fig3, use_container_width=True)
    with c_line:
        section("Visitor Growth Over Time")
        growth = df.groupby(df['date_time'].dt.to_period('D'))['c_ip'].nunique().reset_index()
        growth.columns=['Date','Visitors']
        growth['Date'] = growth['Date'].astype(str)
        fig4 = px.line(growth, x='Date', y='Visitors', color_discrete_sequence=["#6366f1"])
        fig4.update_layout(**PLT_LAYOUT, height=300)
        st.plotly_chart(fig4, use_container_width=True)

# ═══════════════════════════════════════
# PAGE 3 — SALES & PIPELINE
# ═══════════════════════════════════════
def page_sales(df):
    st.markdown('<h1 style="font-size:2rem;font-weight:800;color:#1e1b4b;margin-bottom:24px;">Lead & Sales Pipeline</h1>', unsafe_allow_html=True)
    if df.empty: st.error("No data"); return

    leads_df = df[df['is_lead']]
    total_leads = len(leads_df)
    pipeline    = leads_df['deal_value_usd'].sum()
    conv_rate   = df['is_conversion'].mean()*100
    avg_score   = df['lead_score'].mean()

    c1,c2,c3,c4 = st.columns(4)
    prev_conv = st.session_state.get("prev_conv_rate", 0)
    
    with c1: kpi("Total Leads",      f"{total_leads:,}",     "demo requests")
    with c2: kpi("Pipeline Value",   f"${pipeline:,.0f}",    "est. deal value", True)
    with c3:
        arrow_conv = trend_arrow(conv_rate, prev_conv)
        kpi("Conversion Rate", f"{conv_rate:.1f}% {arrow_conv}", "visits → conversions", conv_rate>2)
    with c4: kpi("Avg Lead Score",   f"{avg_score:.1f}/5",   "intent score")
    
    st.session_state["prev_conv_rate"] = conv_rate

    # Row 2: funnel + revenue by country
    c_funnel, c_rev = st.columns([2,3])
    with c_funnel:
        section("CyberNova Sales Funnel")
        stages = ["Website Visits","Service Explored","Demo Requested","Est. Closed"]
        vals   = [
            len(df),
            len(df[df['product_name']!='Landing Page']),
            total_leads,
            max(1, int(total_leads * 0.3))
        ]
        fig = go.Figure(go.Funnel(
            y=stages, x=vals, textinfo="value+percent initial",
            marker=dict(color=["#4f46e5","#6366f1","#0d9488","#14b8a6"])
        ))
        fig.update_layout(**PLT_LAYOUT, height=280)
        st.plotly_chart(fig, use_container_width=True)

    with c_rev:
        section("Revenue Potential by Country")
        rev = leads_df.groupby('actual_country')['deal_value_usd'].sum().reset_index()
        rev.columns=['Country','Pipeline $']
        fig2 = px.bar(rev.sort_values('Pipeline $', ascending=True),
                      x='Pipeline $', y='Country', orientation='h',
                      color='Pipeline $', color_continuous_scale=["#c7d2fe","#4f46e5"])
        fig2.update_layout(**PLT_LAYOUT, height=280)
        st.plotly_chart(fig2, use_container_width=True)

    # Row 3: hot leads scatter + leads table
    c_scatter, c_table = st.columns([2,3])
    with c_scatter:
        section("Hot Lead Radar")
        scatter_df = df.copy()
        scatter_df['session_q_num'] = scatter_df['session_quality'].map({'Fast':3,'Good':2,'Slow':1}).fillna(1)
        scatter_df['bubble_size'] = scatter_df['deal_value_usd'].clip(lower=500)  # avoid 0-size bubbles
        fig3 = px.scatter(scatter_df.sample(min(400,len(scatter_df))),
                          x='session_q_num', y='lead_score',
                          color='product_name', size='bubble_size',
                          hover_name='actual_country',
                          labels={'session_q_num':'Session Speed (3=Fast)','lead_score':'Lead Score'},
                          color_discrete_sequence=COLORS)
        fig3.update_layout(**PLT_LAYOUT, height=260)
        st.plotly_chart(fig3, use_container_width=True)
    with c_table:
        section("Recent Discovery Call Requests")
        table = leads_df.sort_values('date_time',ascending=False).head(10)[
            ['date_time','actual_country','industry_sector','campaign_source','deal_value_usd','lead_score']].copy()
        table.columns=['Date','Country','Industry','Source','Est. Deal $','Score']
        table['Date'] = table['Date'].dt.strftime('%Y-%m-%d %H:%M')
        st.dataframe(table, hide_index=True, use_container_width=True)

# ═══════════════════════════════════════
# PAGE 4 — PRODUCT PERFORMANCE (KANBAN)
# ═══════════════════════════════════════
def page_products(df):
    st.markdown('<h1 style="font-size:2rem;font-weight:800;color:#1e1b4b;margin-bottom:24px;">Service Performance Board</h1>', unsafe_allow_html=True)
    if df.empty: st.error("No data"); return

    products = {
        "CyberNova AI Assistant":   {"icon":"🤖","color":"#4f46e5"},
        "Threat Monitor Pro":        {"icon":"🛡","color":"#dc2626"},
        "Discovery Call":            {"icon":"📞","color":"#0d9488"},
        "Events & Webinars":         {"icon":"📣","color":"#f59e0b"},
        "Digital Careers":           {"icon":"💼","color":"#8b5cf6"},
    }

    cols = st.columns(len(products))
    for col,(prod,meta) in zip(cols, products.items()):
        sub = df[df['product_name']==prod]
        visits   = len(sub)
        avg_ms   = sub['time_taken'].mean() if len(sub) else 0
        err_cnt  = (sub['sc_status']>=400).sum()
        fast_pct = (sub['session_quality']=='Fast').mean()*100 if len(sub) else 0
        with col:
            st.markdown(f"""
            <div class="kanban-col">
                <div class="kanban-header" style="border-color:{meta["color"]};">{prod}</div>
                <div style="font-size:1.6rem;font-weight:800;color:{meta["color"]};">{visits:,}</div>
                <div style="font-size:.75rem;color:#94a3b8;margin-bottom:12px;">Total Sessions</div>
                <div style="font-size:.8rem;color:#475569;"><b>Avg Response:</b> {avg_ms:.0f}ms</div>
                <div style="font-size:.8rem;color:#475569;"><b>Fast Sessions:</b> {fast_pct:.0f}%</div>
                <div style="font-size:.8rem;color:#dc2626;"><b>Errors:</b> {err_cnt}</div>
            </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    c_bar, c_line = st.columns(2)
    with c_bar:
        section("Avg Response Time by Service (ms)")
        rt = df.groupby('product_name')['time_taken'].mean().reset_index()
        rt.columns=['Service','Avg ms']
        rt = rt[rt['Service']!='Landing Page']
        fig = px.bar(rt.sort_values('Avg ms'), x='Service', y='Avg ms',
                     color='Avg ms', color_continuous_scale=["#0d9488","#f59e0b","#dc2626"])
        fig.update_layout(**PLT_LAYOUT, height=280)
        st.plotly_chart(fig, use_container_width=True)

    with c_line:
        section("Product Engagement Over Time")
        main_prods = ["CyberNova AI Assistant","Threat Monitor Pro","Discovery Call"]
        eng = df[df['product_name'].isin(main_prods)].groupby(
            [df['date_time'].dt.to_period('D'),'product_name']
        ).size().reset_index(name='Requests')
        eng['date_time'] = eng['date_time'].astype(str)
        fig2 = px.line(eng, x='date_time', y='Requests', color='product_name',
                       color_discrete_sequence=COLORS)
        fig2.update_layout(**PLT_LAYOUT, height=280)
        st.plotly_chart(fig2, use_container_width=True)

# ═══════════════════════════════════════
# PAGE 5 — ADMIN
# ═══════════════════════════════════════
def page_admin():
    st.markdown('<h1 style="font-size:2rem;font-weight:800;color:#1e1b4b;margin-bottom:24px;">System Administration</h1>', unsafe_allow_html=True)
    if st.session_state.get('role') != 'Administrator':
        st.error("Access Denied.")
        return

    t1,t2,t3 = st.tabs(["User Management","Audit Logs","System Health"])
    with t1:
        st.markdown("<br>", unsafe_allow_html=True)
        c_form, empty_space, c_table = st.columns([1.2, 0.2, 2])
        with c_form:
            section("Add New User")
            with st.form("add_user"):
                new_user = st.text_input("Username")
                new_role = st.selectbox("Role", ["Administrator","Analyst","Viewer"])
                new_region = st.text_input("Region")
                new_pass = st.text_input("Password", type="password")
                submitted = st.form_submit_button("Create User", use_container_width=True)
                if submitted and new_user and new_pass:
                    add_user(new_user, new_role, new_region, new_pass)
                    st.success(f"User {new_user} ({new_role}) added!")
                    
            st.markdown("<br>", unsafe_allow_html=True)
            section("Remove User")
            with st.form("delete_user"):
                del_user = st.text_input("Username to target:")
                del_btn = st.form_submit_button("Delete User", use_container_width=True)
                if del_btn and del_user:
                    if del_user == "admin":
                        st.error("Cannot delete the root admin.")
                    elif delete_user(del_user):
                        st.success(f"User {del_user} deleted!")
                    else:
                        st.warning("User not found.")
        with c_table:
            section("Current Users")
            # Load users from the JSON file – this will reflect any additions made during the session
            users = load_users()
            if users:
                df_users = pd.DataFrame(users)
                # Hide passwords from the display table
                if "Password" in df_users.columns:
                    df_users = df_users.drop(columns=["Password"])
                st.dataframe(df_users, hide_index=True, use_container_width=True)
            else:
                st.info("No users found. Use the form above to add one.")
    with t2:
        st.info("Audit logging to file is active. Logs stored in data/audit_logs/")
    with t3:
        sizes=[]
        for root,dirs,files in os.walk("data"):
            for f in files:
                fp=os.path.join(root,f)
                sizes.append({"File":fp,"Size (KB)":round(os.path.getsize(fp)/1024,2)})
        st.dataframe(sizes,hide_index=True,use_container_width=True)

# ═══════════════════════════════════════
# SIDEBAR + ROUTING
# ═══════════════════════════════════════
def main():
    inject_css()

    if 'authenticated' not in st.session_state:
        st.session_state['authenticated'] = False

    if not st.session_state['authenticated']:
        login()
        return

    df = load_data()

    with st.sidebar:
        st.markdown("""
        <div style="padding:8px 0 24px 0;">
            <div style="font-size:1.3rem;font-weight:800;letter-spacing:-.01em;">CyberNova</div>
            <div style="font-size:.72rem;color:#818cf8;font-weight:600;letter-spacing:.05em;">INTELLIGENCE HUB</div>
            <div style="font-size:.7rem;color:#64748b;margin-top:4px;">Southern Africa Cybersecurity Platform</div>
        </div>
        """, unsafe_allow_html=True)

        username = st.session_state.get('username','User').capitalize()
        role = st.session_state.get('role','Unknown')
        st.markdown(f"""
        <div style="background:rgba(99,102,241,.15);border-radius:12px;padding:12px 14px;margin-bottom:20px;">
            <div style="font-size:.65rem;color:#818cf8;font-weight:700;letter-spacing:.08em;text-transform:uppercase;">Signed in as</div>
            <div style="font-size:1rem;font-weight:700;">{username}</div>
            <div style="display:inline-block;background:#4f46e5;color:#fff;
                        font-size:.65rem;font-weight:700;border-radius:6px;
                        padding:2px 8px;margin-top:4px;">{role}</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown('<div style="font-size:.65rem;font-weight:700;letter-spacing:.1em;text-transform:uppercase;color:#64748b;margin-bottom:8px;padding-left:4px;">NAVIGATION</div>', unsafe_allow_html=True)

        nav = [
            "Live Operations Board",
            "Audience Intelligence",
            "Sales & Pipeline",
            "Service Performance",
            "Admin & Settings"
        ]
        selection = st.selectbox("Navigation", nav, index=0)

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown('<div style="font-size:.65rem;font-weight:700;letter-spacing:.1em;text-transform:uppercase;color:#64748b;margin-bottom:8px;padding-left:4px;">FILTERS</div>', unsafe_allow_html=True)
        st.date_input("Date Range", [])
        sel_countries = st.multiselect("Country", ['Botswana','South Africa','Zimbabwe','Namibia'])
        st.button("Apply", use_container_width=True)

        # Global Filtering
        if sel_countries:
            df = df[df['actual_country'].isin(sel_countries)]

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown('<div style="font-size:.65rem;font-weight:700;letter-spacing:.1em;text-transform:uppercase;color:#64748b;margin-bottom:8px;padding-left:4px;">REPORTS</div>', unsafe_allow_html=True)
        rep_type = st.selectbox("Format", ["CSV", "Excel"])
        if st.button("Generate & Download", use_container_width=True):
            if rep_type == "CSV":
                data = generate_csv_report(df)
                st.download_button("Download CSV", data, file_name=f"CyberNova_Report_{datetime.now().strftime('%Y%m%d')}.csv", mime='text/csv')
            else:
                data = generate_excel_report(df)
                st.download_button("Download Excel", data, file_name=f"CyberNova_Report_{datetime.now().strftime('%Y%m%d')}.xlsx", mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            log_audit(st.session_state.get('username','User'), f"Generated {rep_type} report")

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Sign Out", use_container_width=True):
            log_audit(st.session_state.get('username','User'), "Logged out")
            st.session_state['authenticated'] = False
            st.rerun()

    if   selection == "Live Operations Board":  page_live()
    elif selection == "Audience Intelligence":  page_marketing(df)
    elif selection == "Sales & Pipeline":       page_sales(df)
    elif selection == "Service Performance":    page_products(df)
    elif selection == "Admin & Settings":       page_admin()

if __name__ == "__main__":
    main()
