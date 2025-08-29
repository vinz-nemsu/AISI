
import os
import pandas as pd
import streamlit as st
import plotly.express as px

st.set_page_config(page_title="AI Survey — Local Dashboard", page_icon="📊", layout="wide")

st.title("📊 AI Survey — Local Dashboard (No DB Connection)")
st.caption("Upload your CSV or use the bundled sample. Filters apply to all visuals.")

# ---------------- Load CSV ----------------
def load_csv(file):
    return pd.read_csv(file, encoding="ISO-8859-1")

col_up1, col_up2 = st.columns([2,1])
with col_up1:
    uploaded = st.file_uploader("Upload the survey CSV", type=["csv"])
with col_up2:
    use_sample = st.checkbox("Use bundled sample", value=True)

if uploaded is not None:
    df_raw = load_csv(uploaded)
elif use_sample:
    sample_path = os.path.join("data", "ai_survey.csv")
    if os.path.exists(sample_path):
        df_raw = load_csv(sample_path)
    else:
        st.error("Sample file not found. Please upload a CSV.")
        st.stop()
else:
    st.info("Upload a CSV or tick 'Use bundled sample' to continue.")
    st.stop()

st.success(f"Loaded {len(df_raw):,} rows, {len(df_raw.columns)} columns.")
st.dataframe(df_raw.head(10), use_container_width=True)

# ---------------- Light cleaning into 'clean' DataFrame ----------------
def norm_yesno(x):
    if pd.isna(x): return "Not Answered"
    s = str(x).strip().lower()
    if s in {"yes","y","true","1"}: return "Yes"
    if s in {"no","n","false","0"}: return "No"
    return x

def clean(df):
    d = df.copy()
    # Rename columns to shorter friendly names
    ren = {
        "What is your age range?": "AGE_RANGE",
        "What is your gender?": "GENDER",
        "What is your education level?": "EDUCATION_LEVEL",
        "What is your employment status?": "EMPLOYMENT_STATUS",
        "What is your occupation? (optional)": "OCCUPATION",
        "How often do you use technological devices?": "DEVICE_USE_FREQUENCY",
        "How much knowledge do you have about artificial intelligence (AI) technologies?": "AI_KNOWLEDGE",
        "Do you generally trust artificial intelligence (AI)?": "TRUST_AI",
        "Do you think artificial intelligence (AI) will be generally beneficial or harmful to humanity?": "BENEFIT_OR_HARM",
        "Please rate how actively you use AI-powered products in your daily life on a scale from 1 to 5.": "AI_USAGE_RATING",
        "Would you like to use more AI products in the future?": "WANT_MORE_AI",
        "I think artificial intelligence (AI) could threaten individual freedoms.": "THREATEN_FREEDOMS",
        "Could artificial intelligence (AI) completely eliminate some professions?": "ELIMINATE_PROFESSIONS",
        "Do you think your own job could be affected by artificial intelligence (AI)?": "OWN_JOB_AFFECTED",
        "Do you believe that artificial intelligence (AI) should be limited by ethical rules?": "ETHICAL_LIMITS",
        "Could artificial intelligence (AI) one day become conscious like humans?": "CONSCIOUS_ONE_DAY",
        "Which of the following do you think is NOT an artificial intelligence (AI) application?": "NOT_AI_APPLICATION",
        "Which of the following is a machine learning algorithm used in the field of artificial intelligence?": "ML_ALGORITHM",
        "The artificial intelligence application called 'ChatGPT' is an example of which type of AI system?": "CHATGPT_TYPE",
    }
    d = d.rename(columns=ren)
    # Basic trims
    for c in d.columns:
        if d[c].dtype == "object":
            d[c] = d[c].astype(str).str.strip()
            d.loc[d[c].isin(["", "nan", "None"]), c] = None
    # Numeric rating
    if "AI_USAGE_RATING" in d.columns:
        d["AI_USAGE_RATING_NUM"] = pd.to_numeric(d["AI_USAGE_RATING"], errors="coerce")
    else:
        d["AI_USAGE_RATING_NUM"] = None
    # Normalize yes/no style columns
    for c in ["TRUST_AI", "WANT_MORE_AI"]:
        if c in d.columns:
            d[c] = d[c].apply(norm_yesno)
    # Title case select categoricals
    for c in ["GENDER","EDUCATION_LEVEL","EMPLOYMENT_STATUS","DEVICE_USE_FREQUENCY","AI_KNOWLEDGE",
              "BENEFIT_OR_HARM","THREATEN_FREEDOMS","ELIMINATE_PROFESSIONS","OWN_JOB_AFFECTED",
              "ETHICAL_LIMITS","CONSCIOUS_ONE_DAY","NOT_AI_APPLICATION","ML_ALGORITHM","CHATGPT_TYPE"]:
        if c in d.columns and d[c].dtype == "object":
            d[c] = d[c].apply(lambda x: x if pd.isna(x) else str(x).title())
    return d

df = clean(df_raw)

# ---------------- Filters ----------------
st.subheader("🔎 Filters")
c1, c2, c3, c4 = st.columns(4)
ages = sorted([x for x in df["AGE_RANGE"].dropna().unique()]) if "AGE_RANGE" in df.columns else []
genders = sorted([x for x in df["GENDER"].dropna().unique()]) if "GENDER" in df.columns else []
edus = sorted([x for x in df["EDUCATION_LEVEL"].dropna().unique()]) if "EDUCATION_LEVEL" in df.columns else []
emps = sorted([x for x in df["EMPLOYMENT_STATUS"].dropna().unique()]) if "EMPLOYMENT_STATUS" in df.columns else []

f_age = c1.multiselect("Age Range", ages)
f_gender = c2.multiselect("Gender", genders)
f_edu = c3.multiselect("Education", edus)
f_emp = c4.multiselect("Employment", emps)

df_f = df.copy()
if f_age: df_f = df_f[df_f["AGE_RANGE"].isin(f_age)]
if f_gender: df_f = df_f[df_f["GENDER"].isin(f_gender)]
if f_edu: df_f = df_f[df_f["EDUCATION_LEVEL"].isin(f_edu)]
if f_emp: df_f = df_f[df_f["EMPLOYMENT_STATUS"].isin(f_emp)]

st.caption(f"Filtered rows: {len(df_f):,}")

# ---------------- KPIs ----------------
st.subheader("📈 KPIs")
k1, k2, k3 = st.columns(3)
k1.metric("Respondents", f"{len(df_f):,}")
if "AI_USAGE_RATING_NUM" in df_f.columns:
    k2.metric("Avg AI Usage Rating (1–5)", f"{df_f['AI_USAGE_RATING_NUM'].mean():.2f}")
else:
    k2.metric("Avg AI Usage Rating (1–5)", "-")
if "TRUST_AI" in df_f.columns:
    pct_trust = (df_f["TRUST_AI"].str.lower().eq("yes").mean() * 100) if len(df_f) else 0.0
    k3.metric("% Trust AI", f"{pct_trust:.1f}%")
else:
    k3.metric("% Trust AI", "-")

st.divider()

# ---------------- Usage ----------------
st.subheader("Usage & Adoption")
if "AI_USAGE_RATING_NUM" in df_f.columns:
    fig = px.histogram(df_f.dropna(subset=["AI_USAGE_RATING_NUM"]), x="AI_USAGE_RATING_NUM", nbins=5, title="AI Usage Rating (1–5)")
    st.plotly_chart(fig, use_container_width=True)

if "WANT_MORE_AI" in df_f.columns:
    want_counts = df_f["WANT_MORE_AI"].fillna("Not Answered").value_counts().reset_index()
    want_counts.columns = ["WANT_MORE_AI","COUNT"]
    fig = px.pie(want_counts, names="WANT_MORE_AI", values="COUNT", title="Would like to use more AI?")
    st.plotly_chart(fig, use_container_width=True)

st.divider()

# ---------------- Trust & Perception ----------------
st.subheader("Trust & Perception")
if "TRUST_AI" in df_f.columns:
    trust_counts = df_f["TRUST_AI"].fillna("Not Answered").value_counts().reset_index()
    trust_counts.columns = ["TRUST","COUNT"]
    fig = px.bar(trust_counts, x="TRUST", y="COUNT", title="General Trust in AI")
    st.plotly_chart(fig, use_container_width=True)

if "AI_USAGE_RATING_NUM" in df_f.columns and "TRUST_AI" in df_f.columns:
    heat = df_f.dropna(subset=["AI_USAGE_RATING_NUM", "TRUST_AI"]).groupby(["TRUST_AI","AI_USAGE_RATING_NUM"]).size().reset_index(name="COUNT")
    fig = px.density_heatmap(heat, x="AI_USAGE_RATING_NUM", y="TRUST_AI", z="COUNT", title="Trust × AI Usage Rating")
    st.plotly_chart(fig, use_container_width=True)

st.divider()

# ---------------- Job Impact & Ethics ----------------
st.subheader("Job Impact & Ethics")
for col, title in [
    ("ELIMINATE_PROFESSIONS", "Could AI eliminate some professions?"),
    ("OWN_JOB_AFFECTED", "Do you think your own job could be affected?"),
    ("ETHICAL_LIMITS", "Should AI be limited by ethical rules?"),
    ("CONSCIOUS_ONE_DAY", "Could AI become conscious like humans?"),
]:
    if col in df_f.columns:
        tmp = df_f[col].fillna("Not Answered").value_counts().reset_index()
        tmp.columns = ["ANSWER","COUNT"]
        fig = px.bar(tmp, x="ANSWER", y="COUNT", title=title)
        st.plotly_chart(fig, use_container_width=True)

st.divider()

# ---------------- Literacy ----------------
st.subheader("AI Literacy")
for col, title in [
    ("NOT_AI_APPLICATION", "Which is NOT an AI application?"),
    ("ML_ALGORITHM", "Which is a machine learning algorithm?"),
    ("CHATGPT_TYPE", "ChatGPT is an example of ..."),
]:
    if col in df_f.columns:
        tmp = df_f[col].fillna("Not Answered").value_counts().reset_index()
        tmp.columns = ["ANSWER","COUNT"]
        fig = px.bar(tmp, x="ANSWER", y="COUNT", title=title)
        st.plotly_chart(fig, use_container_width=True)

st.divider()

# ---------------- Preview ----------------
st.subheader("Preview Data (Filtered)")
st.dataframe(df_f.head(50), use_container_width=True)
