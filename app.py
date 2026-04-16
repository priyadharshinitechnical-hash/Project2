import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="M365 Security Dashboard — ChiEAC",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Sora:wght@400;500;600&display=swap');

html, body, [class*="css"] { font-family: 'Sora', sans-serif; }

/* Sidebar */
[data-testid="stSidebar"] {
    background: #0f1322 !important;
    border-right: 1px solid rgba(255,255,255,0.06);
}
[data-testid="stSidebar"] * { color: #e8eaf0 !important; }
[data-testid="stSidebar"] .stRadio label { font-family: 'DM Mono', monospace; font-size: 12px; }

/* Main background */
[data-testid="stAppViewContainer"] { background: #0a0d14; }
[data-testid="stHeader"] { background: transparent; }

/* Metric cards */
[data-testid="stMetric"] {
    background: #111520;
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 12px;
    padding: 1rem;
}
[data-testid="stMetricValue"] { color: #ffffff !important; font-weight: 600; }
[data-testid="stMetricLabel"] { color: #6b7280 !important; font-family: 'DM Mono', monospace; font-size: 11px; text-transform: uppercase; }
[data-testid="stMetricDelta"] { font-family: 'DM Mono', monospace; font-size: 12px; }

/* Headings */
h1, h2, h3 { color: #ffffff !important; font-family: 'Sora', sans-serif !important; }
p, li, .stMarkdown { color: #e8eaf0; }

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    background: #111520;
    border-radius: 8px;
    padding: 4px;
    gap: 4px;
    border: 1px solid rgba(255,255,255,0.06);
}
.stTabs [data-baseweb="tab"] {
    background: transparent;
    color: #6b7280;
    font-family: 'DM Mono', monospace;
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 0.07em;
    border-radius: 6px;
}
.stTabs [aria-selected="true"] {
    background: rgba(59,130,246,0.15) !important;
    color: #3b82f6 !important;
}

/* Dataframe / tables */
[data-testid="stDataFrame"] { background: #111520; border-radius: 10px; }
.stDataFrame { color: #e8eaf0; }

/* File uploader */
[data-testid="stFileUploader"] {
    background: #111520;
    border: 1px dashed rgba(255,255,255,0.15);
    border-radius: 12px;
    padding: 1rem;
}

/* Expander */
[data-testid="stExpander"] {
    background: #111520;
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 10px;
}

/* Divider */
hr { border-color: rgba(255,255,255,0.06); }

/* Scrollbar */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: #0a0d14; }
::-webkit-scrollbar-thumb { background: #2d3148; border-radius: 3px; }
</style>
""", unsafe_allow_html=True)

# ── Dummy data ────────────────────────────────────────────────────────────────
SCORE_HISTORY = pd.DataFrame({
    "Month": ["Nov 2025", "Dec 2025", "Jan 2026", "Feb 2026", "Mar 2026", "Apr 2026"],
    "Secure Score": [50, 52, 53, 56, 58, 62],
    "Nonprofit Avg": [51, 52, 52, 53, 53, 54],
})

MFA_BY_DEPT = pd.DataFrame({
    "Department": ["Finance", "IT", "HR", "Operations", "Leadership"],
    "MFA Coverage (%)": [95, 100, 60, 55, 80],
})

SIGNIN_RISK = pd.DataFrame({
    "Week": ["Week 1", "Week 2", "Week 3", "Week 4"],
    "Low Risk": [5, 8, 12, 6],
    "Medium Risk": [2, 3, 5, 2],
    "High Risk": [1, 1, 3, 1],
})

RISK_FINDINGS = [
    ("🔴", "3 global admins have no MFA enabled", "Critical"),
    ("🔴", "Legacy authentication protocols still active", "Critical"),
    ("🟡", "MFA not enforced for 47 standard users", "High"),
    ("🟡", "No Self-Service Password Reset (SSPR) policy configured", "High"),
    ("🔵", "12 Intune devices out of compliance", "Medium"),
    ("🔵", "2 unmanaged OAuth apps detected", "Medium"),
    ("🟢", "Anti-phishing policies active on all mailboxes", "Resolved"),
]

CATEGORY_SCORES = {
    "Identity & Access": 55,
    "Email Security": 78,
    "Device Management": 84,
    "Data Protection": 48,
    "Conditional Access": 57,
    "App Permissions": 62,
}

RECOMMENDATIONS = [
    ("01", "Enable MFA for all 3 global administrator accounts",
     "These accounts can access all data and represent the highest-risk surface in your tenant.",
     "+8 pts", "Low effort", "Critical"),
    ("02", "Block legacy authentication protocols via Conditional Access",
     "Legacy auth bypasses MFA and is responsible for the majority of credential spray attacks.",
     "+6 pts", "Low effort", "Critical"),
    ("03", "Enforce MFA for the 47 standard users without it",
     "Prioritize HR and Operations first given their low adoption rates (55–60%).",
     "+5 pts", "Medium effort", "High"),
    ("04", "Configure Self-Service Password Reset (SSPR)",
     "Reduces helpdesk burden and strengthens identity governance. Pair with MFA registration.",
     "+3 pts", "Low effort", "High"),
    ("05", "Remediate 12 Intune non-compliant devices",
     "Ensure compliance policies are enforced before granting access to M365 resources.",
     "+2 pts", "Medium effort", "Medium"),
]

CA_POLICIES = pd.DataFrame({
    "Policy": [
        "Require MFA for all users",
        "Block legacy authentication",
        "Require MFA for admins",
        "Require compliant device",
        "Block high-risk sign-ins",
        "Restrict access by location",
        "Session lifetime enforcement",
    ],
    "Status": ["Partial", "Missing", "Missing", "Active", "Active", "Partial", "Active"],
    "Coverage": ["71% users", "—", "—", "All users", "All users", "Admins only", "All users"],
    "Risk Level": ["High", "Critical", "Critical", "Low", "Low", "Medium", "Low"],
})

COMPLIANCE_CONTROLS = pd.DataFrame({
    "Control Area": [
        "Multi-factor authentication",
        "Privileged identity management",
        "Data loss prevention",
        "Endpoint security (Intune)",
        "Email protection (Defender)",
        "Information protection labels",
        "Audit logging",
        "Guest access governance",
    ],
    "Status": ["Partial", "Not configured", "Partial", "Active", "Active", "Partial", "Active", "Partial"],
    "Score": ["71%", "0%", "75%", "84%", "92%", "48%", "100%", "60%"],
    "Notes": [
        "Admins excluded",
        "No PIM roles active",
        "1 policy in draft",
        "12 non-compliant",
        "Anti-phishing on",
        "Manual labeling only",
        "90-day retention",
        "2 stale guest accounts",
    ],
})

BOARD_METRICS = pd.DataFrame({
    "Metric": ["Secure score", "MFA coverage", "Admin MFA coverage", "Device compliance",
                "Email protection", "Data classification", "Legacy auth blocked"],
    "Current": ["62%", "71%", "63%", "84%", "92%", "48%", "No"],
    "Target": ["80%", "100%", "100%", "95%", "95%", "80%", "Yes"],
    "Status": ["In progress", "In progress", "At risk", "In progress", "On track", "At risk", "At risk"],
})

# ── Plotly theme helper ───────────────────────────────────────────────────────
PLOT_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="DM Mono, monospace", color="#6b7280", size=11),
    margin=dict(l=10, r=10, t=30, b=10),
    xaxis=dict(gridcolor="rgba(255,255,255,0.04)", linecolor="rgba(255,255,255,0.06)"),
    yaxis=dict(gridcolor="rgba(255,255,255,0.04)", linecolor="rgba(255,255,255,0.06)"),
)

def badge(text, color):
    colors = {
        "Critical": ("#fca5a5", "rgba(239,68,68,0.15)"),
        "High":     ("#fcd34d", "rgba(245,158,11,0.15)"),
        "Medium":   ("#93c5fd", "rgba(59,130,246,0.15)"),
        "Resolved": ("#86efac", "rgba(34,197,94,0.15)"),
    }
    tc, bg = colors.get(text, ("#e8eaf0", "rgba(255,255,255,0.08)"))
    return f'<span style="background:{bg};color:{tc};font-family:DM Mono,monospace;font-size:10px;padding:2px 9px;border-radius:20px;font-weight:500;">{text}</span>'

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="padding:0.5rem 0 1rem;">
      <div style="font-family:'DM Mono',monospace;font-size:10px;color:#06b6d4;letter-spacing:0.12em;text-transform:uppercase;margin-bottom:4px;">● ChiEAC</div>
      <div style="font-size:16px;font-weight:600;color:#fff;letter-spacing:-0.02em;">M365 Security<br>Dashboard</div>
      <div style="font-family:'DM Mono',monospace;font-size:10px;color:#6b7280;margin-top:4px;">v1.0 · April 2026</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    st.markdown('<div style="font-family:\'DM Mono\',monospace;font-size:10px;color:#6b7280;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:8px;">Navigation</div>', unsafe_allow_html=True)
    page = st.radio("", ["📊 Overview", "🔐 Identity & Access", "✅ Compliance Posture", "📋 Executive Report"], label_visibility="collapsed")

    st.markdown("---")
    st.markdown('<div style="font-family:\'DM Mono\',monospace;font-size:10px;color:#6b7280;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:8px;">Upload Data</div>', unsafe_allow_html=True)
    uploaded = st.file_uploader("Upload M365 export (CSV/JSON)", type=["csv", "json"], label_visibility="collapsed")
    if uploaded:
        st.success(f"✓ Loaded: {uploaded.name}")
    else:
        st.caption("Using demo tenant data")

    st.markdown("---")
    st.markdown("""
    <div style="font-family:'DM Mono',monospace;font-size:10px;color:#6b7280;">
    Accepted formats:<br>
    · Secure Score CSV<br>
    · Entra ID Sign-in Logs<br>
    · MFA Status Export<br>
    · CA Policy JSON<br>
    · Intune Compliance
    </div>
    """, unsafe_allow_html=True)

# ── Shared score ring header ──────────────────────────────────────────────────
col_h1, col_h2 = st.columns([3, 1])
with col_h1:
    st.markdown("""
    <h1 style="font-size:26px;font-weight:600;letter-spacing:-0.02em;margin:0;">
        M365 <span style="color:#3b82f6;">Security</span> Posture Dashboard
    </h1>
    <div style="font-family:'DM Mono',monospace;font-size:11px;color:#6b7280;margin-top:4px;">
        microsoft-365 · entra-id · conditional-access · intune &nbsp;·&nbsp; 
        Report: April 16, 2026 09:41 UTC
    </div>
    """, unsafe_allow_html=True)
with col_h2:
    st.markdown("""
    <div style="text-align:right;">
      <div style="font-size:38px;font-weight:600;color:#f59e0b;line-height:1;">62<span style="font-size:18px;color:#6b7280;">/100</span></div>
      <div style="font-family:'DM Mono',monospace;font-size:11px;color:#22c55e;">↑ +4 pts from March</div>
      <div style="font-family:'DM Mono',monospace;font-size:10px;color:#6b7280;">Nonprofit avg: 54</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# ═══════════════════════════════════════════════════════════════════
# PAGE: OVERVIEW
# ═══════════════════════════════════════════════════════════════════
if page == "📊 Overview":

    # Metric cards
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("Secure Score", "62%", "+4 pts")
    c2.metric("MFA Coverage", "71%", "-29% gap", delta_color="inverse")
    c3.metric("Exposed Admins", "3", "No MFA", delta_color="inverse")
    c4.metric("CA Policies", "4 / 7", "3 gaps", delta_color="inverse")
    c5.metric("Device Compliance", "84%", "+0%")
    c6.metric("Risky Sign-ins", "17", "+3 this week", delta_color="inverse")

    st.markdown("<br>", unsafe_allow_html=True)

    col_l, col_r = st.columns(2)

    # Risk findings
    with col_l:
        st.markdown("#### Priority risk findings")
        for icon, text, sev in RISK_FINDINGS:
            st.markdown(
                f'<div style="display:flex;align-items:center;gap:10px;padding:8px 0;border-bottom:1px solid rgba(255,255,255,0.05);">'
                f'<span style="font-size:10px;">{icon}</span>'
                f'<span style="flex:1;font-size:13px;color:#e8eaf0;">{text}</span>'
                f'{badge(sev, sev)}'
                f'</div>',
                unsafe_allow_html=True
            )

    # Category scores
    with col_r:
        st.markdown("#### Security category scores")
        for cat, score in CATEGORY_SCORES.items():
            color = "#22c55e" if score >= 75 else "#f59e0b" if score >= 55 else "#ef4444"
            st.markdown(
                f'<div style="margin-bottom:10px;">'
                f'<div style="display:flex;justify-content:space-between;font-size:12px;color:#e8eaf0;margin-bottom:4px;">'
                f'<span>{cat}</span><span style="font-family:\'DM Mono\',monospace;color:{color}">{score}%</span></div>'
                f'<div style="background:rgba(255,255,255,0.06);border-radius:3px;height:6px;">'
                f'<div style="width:{score}%;background:{color};height:100%;border-radius:3px;"></div>'
                f'</div></div>',
                unsafe_allow_html=True
            )

    st.markdown("<br>", unsafe_allow_html=True)

    # Trend chart
    st.markdown("#### Secure score trend — 6 months")
    fig_trend = go.Figure()
    fig_trend.add_trace(go.Scatter(
        x=SCORE_HISTORY["Month"], y=SCORE_HISTORY["Secure Score"],
        name="Secure Score", mode="lines+markers",
        line=dict(color="#3b82f6", width=2.5),
        marker=dict(size=6, color="#3b82f6"),
        fill="tozeroy", fillcolor="rgba(59,130,246,0.07)"
    ))
    fig_trend.add_trace(go.Scatter(
        x=SCORE_HISTORY["Month"], y=SCORE_HISTORY["Nonprofit Avg"],
        name="Nonprofit avg", mode="lines",
        line=dict(color="#6b7280", width=1.5, dash="dot"),
    ))
    fig_trend.update_layout(
        **PLOT_LAYOUT,
        height=220,
        yaxis=dict(range=[40, 80], ticksuffix="%", **PLOT_LAYOUT["yaxis"]),
        legend=dict(font=dict(size=11, color="#6b7280"), bgcolor="rgba(0,0,0,0)", x=0.01, y=0.99),
        showlegend=True,
    )
    st.plotly_chart(fig_trend, use_container_width=True)

    col_b1, col_b2 = st.columns(2)

    # MFA by dept
    with col_b1:
        st.markdown("#### MFA adoption by department")
        colors = ["#22c55e" if v >= 80 else "#f59e0b" if v >= 70 else "#ef4444"
                  for v in MFA_BY_DEPT["MFA Coverage (%)"]]
        fig_mfa = go.Figure(go.Bar(
            x=MFA_BY_DEPT["Department"],
            y=MFA_BY_DEPT["MFA Coverage (%)"],
            marker=dict(color=colors, line=dict(width=0)),
            text=MFA_BY_DEPT["MFA Coverage (%)"].astype(str) + "%",
            textfont=dict(color="#e8eaf0", size=11),
            textposition="outside",
        ))
        fig_mfa.update_layout(**PLOT_LAYOUT, height=220,
                              yaxis=dict(range=[0, 115], ticksuffix="%", **PLOT_LAYOUT["yaxis"]))
        st.plotly_chart(fig_mfa, use_container_width=True)

    # Trend indicators
    with col_b2:
        st.markdown("#### Risk trend indicators")
        trends = [
            ("↑", "#22c55e", "Secure score improved +4 pts this period"),
            ("↑", "#22c55e", "MFA coverage up 64% → 71% (+7%)"),
            ("↑", "#22c55e", "Phishing emails blocked up +22%"),
            ("↓", "#ef4444", "3 new risky sign-ins detected this week"),
            ("↓", "#ef4444", "Legacy auth usage increased month-over-month"),
            ("↓", "#ef4444", "2 new unmanaged OAuth apps added"),
            ("→", "#6b7280", "Device compliance unchanged at 84%"),
        ]
        for arrow, color, text in trends:
            st.markdown(
                f'<div style="display:flex;gap:10px;align-items:center;padding:7px 0;border-bottom:1px solid rgba(255,255,255,0.05);">'
                f'<span style="color:{color};font-weight:600;font-family:\'DM Mono\',monospace;font-size:14px;min-width:16px;">{arrow}</span>'
                f'<span style="font-size:12.5px;color:#e8eaf0;">{text}</span>'
                f'</div>',
                unsafe_allow_html=True
            )

    st.markdown("<br>", unsafe_allow_html=True)

    # Recommendations
    st.markdown("#### Top actions to reduce risk")
    for num, title, detail, pts, effort, priority in RECOMMENDATIONS:
        color_map = {"Critical": "#fca5a5", "High": "#fcd34d", "Medium": "#93c5fd"}
        tc = color_map.get(priority, "#e8eaf0")
        with st.expander(f"**{num}** — {title}   `{pts}` · {priority}"):
            st.markdown(f'<p style="font-size:13px;color:#e8eaf0;">{detail}</p>', unsafe_allow_html=True)
            st.markdown(
                f'<span style="font-family:\'DM Mono\',monospace;font-size:11px;color:#22c55e;">{pts} estimated score impact</span> &nbsp;·&nbsp; '
                f'<span style="font-family:\'DM Mono\',monospace;font-size:11px;color:#06b6d4;">{effort}</span> &nbsp;·&nbsp; '
                f'<span style="font-family:\'DM Mono\',monospace;font-size:11px;color:{tc};">Priority: {priority}</span>',
                unsafe_allow_html=True
            )

# ═══════════════════════════════════════════════════════════════════
# PAGE: IDENTITY & ACCESS
# ═══════════════════════════════════════════════════════════════════
elif page == "🔐 Identity & Access":
    st.markdown("### Identity & Access Risk Analysis")

    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("Admins w/o MFA", "3", "Critical", delta_color="inverse")
    c2.metric("Users w/o MFA", "47", "of 163 total", delta_color="inverse")
    c3.metric("Risky Sign-ins", "17", "+3 this week", delta_color="inverse")
    c4.metric("Legacy Auth Events", "284", "Last 30 days", delta_color="inverse")
    c5.metric("SSPR Configured", "No", "Not set up", delta_color="inverse")
    c6.metric("Guest Accounts", "11", "2 stale >90d", delta_color="off")

    st.markdown("<br>", unsafe_allow_html=True)

    # Sign-in risk chart
    st.markdown("#### Sign-in risk breakdown — last 30 days")
    fig_si = go.Figure()
    for col, color, name in [
        ("Low Risk", "rgba(59,130,246,0.7)", "Low risk"),
        ("Medium Risk", "rgba(245,158,11,0.7)", "Medium risk"),
        ("High Risk", "rgba(239,68,68,0.7)", "High risk"),
    ]:
        fig_si.add_trace(go.Bar(
            x=SIGNIN_RISK["Week"], y=SIGNIN_RISK[col],
            name=name, marker_color=color,
        ))
    fig_si.update_layout(
        **PLOT_LAYOUT, barmode="stack", height=240,
        legend=dict(font=dict(size=11, color="#6b7280"), bgcolor="rgba(0,0,0,0)"),
    )
    st.plotly_chart(fig_si, use_container_width=True)

    st.markdown("#### Conditional access policy coverage")

    def style_status(val):
        styles = {
            "Active":   "background:rgba(34,197,94,0.12);color:#86efac",
            "Missing":  "background:rgba(239,68,68,0.12);color:#fca5a5",
            "Partial":  "background:rgba(245,158,11,0.12);color:#fcd34d",
        }
        return styles.get(val, "")

    def style_risk(val):
        styles = {
            "Critical": "color:#fca5a5;font-weight:500",
            "High":     "color:#fcd34d;font-weight:500",
            "Medium":   "color:#93c5fd",
            "Low":      "color:#86efac",
        }
        return styles.get(val, "")

    st.dataframe(
        CA_POLICIES.style
            .applymap(style_status, subset=["Status"])
            .applymap(style_risk, subset=["Risk Level"]),
        use_container_width=True,
        hide_index=True,
    )

# ═══════════════════════════════════════════════════════════════════
# PAGE: COMPLIANCE POSTURE
# ═══════════════════════════════════════════════════════════════════
elif page == "✅ Compliance Posture":
    st.markdown("### Compliance Posture Overview")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Devices Compliant", "84%", "67 of 79")
    c2.metric("Non-compliant", "12", "Pending fix", delta_color="inverse")
    c3.metric("DLP Policies Active", "3 / 4", "1 draft pending")
    c4.metric("Sensitivity Labels", "48%", "Data not fully labeled", delta_color="inverse")

    st.markdown("<br>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    # Radar / spider chart for categories
    with col1:
        st.markdown("#### Category posture radar")
        cats = list(CATEGORY_SCORES.keys())
        vals = list(CATEGORY_SCORES.values())
        fig_radar = go.Figure(go.Scatterpolar(
            r=vals + [vals[0]],
            theta=cats + [cats[0]],
            fill="toself",
            fillcolor="rgba(59,130,246,0.12)",
            line=dict(color="#3b82f6", width=2),
            marker=dict(color="#3b82f6", size=5),
        ))
        fig_radar.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(family="DM Mono, monospace", color="#6b7280", size=10),
            polar=dict(
                bgcolor="rgba(0,0,0,0)",
                radialaxis=dict(visible=True, range=[0, 100], ticksuffix="%",
                                gridcolor="rgba(255,255,255,0.06)", color="#6b7280"),
                angularaxis=dict(gridcolor="rgba(255,255,255,0.06)", color="#6b7280"),
            ),
            margin=dict(l=30, r=30, t=30, b=30),
            height=300,
            showlegend=False,
        )
        st.plotly_chart(fig_radar, use_container_width=True)

    with col2:
        st.markdown("#### Device compliance breakdown")
        fig_pie = go.Figure(go.Pie(
            labels=["Compliant", "Non-compliant"],
            values=[67, 12],
            hole=0.6,
            marker=dict(colors=["rgba(34,197,94,0.8)", "rgba(239,68,68,0.7)"],
                        line=dict(color="#0a0d14", width=2)),
            textfont=dict(family="DM Mono, monospace", color="#e8eaf0", size=11),
        ))
        fig_pie.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(family="DM Mono, monospace", color="#6b7280"),
            margin=dict(l=10, r=10, t=10, b=10),
            height=300,
            legend=dict(font=dict(size=11, color="#6b7280"), bgcolor="rgba(0,0,0,0)"),
            annotations=[dict(text="84%<br><span style='font-size:10px'>Compliant</span>",
                              x=0.5, y=0.5, showarrow=False,
                              font=dict(size=18, color="#fff", family="Sora, sans-serif"))],
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    st.markdown("#### Control framework status")

    def style_ctrl_status(val):
        styles = {
            "Active":          "background:rgba(34,197,94,0.12);color:#86efac",
            "Not configured":  "background:rgba(239,68,68,0.12);color:#fca5a5",
            "Partial":         "background:rgba(245,158,11,0.12);color:#fcd34d",
        }
        return styles.get(val, "")

    st.dataframe(
        COMPLIANCE_CONTROLS.style.applymap(style_ctrl_status, subset=["Status"]),
        use_container_width=True,
        hide_index=True,
    )

# ═══════════════════════════════════════════════════════════════════
# PAGE: EXECUTIVE REPORT
# ═══════════════════════════════════════════════════════════════════
elif page == "📋 Executive Report":
    st.markdown("### Executive Report — April 2026")

    # Narrative
    st.markdown("""
    <div style="background:linear-gradient(135deg,rgba(59,130,246,0.06),rgba(168,85,247,0.06));
                border:1px solid rgba(255,255,255,0.1);border-radius:12px;padding:1.25rem;margin-bottom:1.5rem;">
      <div style="font-family:'DM Mono',monospace;font-size:10px;color:#06b6d4;text-transform:uppercase;
                  letter-spacing:0.1em;margin-bottom:8px;">Security posture narrative</div>
      <p style="font-size:13px;color:#e8eaf0;line-height:1.8;">
        Your organization's Microsoft 365 environment shows <strong style="color:#fff;">moderate risk</strong> 
        with a current Secure Score of <strong style="color:#fff;">62 out of 100</strong>, above the 
        nonprofit sector average of 54. While meaningful progress has been made over six months — 
        the score rising from 50 in November — 
        <strong style="color:#fca5a5;">two critical gaps require immediate attention</strong>: 
        three global administrator accounts operate without multi-factor authentication, and legacy 
        authentication protocols remain enabled across the tenant.
        <br><br>
        These two issues represent the highest probability of a successful breach and should be 
        addressed within the next <strong style="color:#fff;">5 business days</strong>. 
        Resolving them alone would add an estimated +14 points to the Secure Score. 
        Email security remains strong (78%), and device compliance is solid at 84%. 
        The primary focus this quarter is <strong style="color:#3b82f6;">identity and access management</strong>.
      </p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Risk timeline for leadership")
        timeline = [
            ("🔴", "#fca5a5", "This week", "Enable MFA on 3 global admin accounts"),
            ("🔴", "#fca5a5", "This week", "Block legacy authentication protocols"),
            ("🟡", "#fcd34d", "This month", "Enforce MFA for all 47 remaining users"),
            ("🟡", "#fcd34d", "This month", "Enable Self-Service Password Reset"),
            ("🔵", "#93c5fd", "This quarter", "Remediate 12 non-compliant devices"),
            ("🔵", "#93c5fd", "This quarter", "Configure PIM for admin roles"),
        ]
        for icon, color, when, action in timeline:
            st.markdown(
                f'<div style="display:flex;gap:12px;align-items:flex-start;padding:9px 0;border-bottom:1px solid rgba(255,255,255,0.05);">'
                f'<span style="font-size:10px;margin-top:2px;">{icon}</span>'
                f'<div>'
                f'<div style="font-family:\'DM Mono\',monospace;font-size:10px;color:{color};margin-bottom:2px;">{when}</div>'
                f'<div style="font-size:12.5px;color:#e8eaf0;">{action}</div>'
                f'</div></div>',
                unsafe_allow_html=True
            )

    with col2:
        st.markdown("#### Projected score improvement")
        fig_proj = go.Figure(go.Bar(
            x=["Current\nscore", "After critical\nfixes", "After all\nactions"],
            y=[62, 76, 85],
            marker=dict(
                color=["rgba(245,158,11,0.75)", "rgba(59,130,246,0.75)", "rgba(34,197,94,0.75)"],
                line=dict(width=0),
            ),
            text=["62%", "76%", "85%"],
            textfont=dict(color="#e8eaf0", size=12),
            textposition="outside",
        ))
        fig_proj.update_layout(
            **PLOT_LAYOUT,
            height=280,
            yaxis=dict(range=[0, 100], ticksuffix="%", **PLOT_LAYOUT["yaxis"]),
        )
        st.plotly_chart(fig_proj, use_container_width=True)

    st.markdown("#### Board-ready metrics snapshot")

    def style_board(val):
        styles = {
            "On track":    "background:rgba(34,197,94,0.12);color:#86efac",
            "In progress": "background:rgba(245,158,11,0.12);color:#fcd34d",
            "At risk":     "background:rgba(239,68,68,0.12);color:#fca5a5",
        }
        return styles.get(val, "")

    st.dataframe(
        BOARD_METRICS.style.applymap(style_board, subset=["Status"]),
        use_container_width=True,
        hide_index=True,
    )

    st.markdown("<br>", unsafe_allow_html=True)
    st.info("💡 **To export this report**: Use your browser's Print function (Ctrl+P / Cmd+P) and select 'Save as PDF'.")

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("""
<div style="display:flex;justify-content:space-between;flex-wrap:wrap;gap:8px;">
  <span style="font-family:'DM Mono',monospace;font-size:11px;color:#6b7280;">
    ChiEAC · M365 Security Analytics Platform · v1.0
  </span>
  <span style="font-family:'DM Mono',monospace;font-size:11px;color:#6b7280;">
    Data: Microsoft 365 Security Center exports · Internal governance use
  </span>
</div>
""", unsafe_allow_html=True)
