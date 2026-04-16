# M365 Security Posture Dashboard
**Chicago Education Advocacy Cooperative (ChiEAC)**

A public-facing Microsoft 365 security analytics dashboard built with Streamlit.
Translates Secure Score, identity, and access data into actionable posture insights
for nonprofits and small organizations — no dedicated security team required.

---

## 🚀 Deploy to Streamlit Cloud (Get a public link in 2 minutes)

### Step 1 — Push to GitHub
```bash
git init
git add .
git commit -m "Initial M365 security dashboard"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/m365-security-dashboard.git
git push -u origin main
```

### Step 2 — Deploy on Streamlit Cloud
1. Go to **https://share.streamlit.io**
2. Sign in with GitHub
3. Click **"New app"**
4. Select your repo → Branch: `main` → File: `app.py`
5. Click **"Deploy"**

✅ You'll get a public URL like:
`https://YOUR_USERNAME-m365-security-dashboard-app-xxxx.streamlit.app`

---

## 🖥️ Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```
Opens at: http://localhost:8501

---

## 📁 Project structure

```
m365_dashboard/
├── app.py                  # Main Streamlit application
├── requirements.txt        # Python dependencies
├── .streamlit/
│   └── config.toml         # Dark theme configuration
└── README.md
```

---

## 📊 Dashboard sections

| Tab | Contents |
|-----|----------|
| Overview | Metric cards, risk findings, category scores, trend chart, MFA by dept, recommendations |
| Identity & Access | Admin/user MFA gaps, sign-in risk chart, Conditional Access policy table |
| Compliance Posture | Device compliance, radar chart, control framework status |
| Executive Report | Narrative summary, risk timeline, projected score chart, board metrics |

---

## 📥 Accepted data uploads (MVP)
- Secure Score CSV exports
- Entra ID sign-in logs (sanitized)
- MFA status exports
- Conditional Access policy summaries (JSON)
- Intune device compliance reports

---

## 🏢 Ownership
Built and maintained by ChiEAC as a public security analytics product.
Primary builder responsible for ongoing updates, metrics, and support.
