import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import math
import json

# -------------------- PAGE CONFIG --------------------
st.set_page_config(
    page_title="AI Survey Dashboard",
    page_icon="🤖",
    layout="wide"
)

# -------------------- HEADER --------------------
st.markdown(
    """
    <div style="text-align:center;">
        <h1>🤖 AISIS: AI Survey Insights System</h1>
        <p style="color:gray; font-size:18px;">
            An Interactive Dashboard & AI Chatbot for Survey-Based Insights
        </p>
    </div>
    """,
    unsafe_allow_html=True
)

# -------------------- DB CONNECTION --------------------
session = st.connection("snowflake").session()

# Sidebar
st.sidebar.image("https://streamlit.io/images/brand/streamlit-logo-primary-colormark-darktext.png", width=180)
st.sidebar.markdown("## ⚙️ Settings")
source = st.sidebar.selectbox("Select Data Source", ["AI_SURVEY_CLEAN", "AI_SURVEY_RAW"], index=0)

# -------------------- LOAD DATA --------------------
query = f"SELECT * FROM {source}"
df = session.sql(query).to_pandas()

if source == "AI_SURVEY_RAW":
    rename_map = {
        "WHAT_IS_YOUR_AGE_RANGE": "AGE_RANGE",
        "WHAT_IS_YOUR_GENDER": "GENDER",
        "WHAT_IS_YOUR_EDUCATION_LEVEL": "EDUCATION_LEVEL",
        "WHAT_IS_YOUR_EMPLOYMENT_STATUS": "EMPLOYMENT_STATUS",
        "PLEASE_RATE_HOW_ACTIVELY_YOU_USE_AI_POWERED_PRODUCTS_IN_YOUR_DAILY_LIFE_ON_A_SCALE_FROM_1_TO_5": "AI_USAGE_RATING",
        "DO_YOU_GENERALLY_TRUST_ARTIFICIAL_INTELLIGENCE_AI": "TRUST_AI",
        "WOULD_YOU_LIKE_TO_USE_MORE_AI_PRODUCTS_IN_THE_FUTURE": "WANT_MORE_AI",
    }
    df = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns})

df["AI_USAGE_RATING_NUM"] = pd.to_numeric(df.get("AI_USAGE_RATING"), errors="coerce")

# -------------------- TABS --------------------
tab1, tab2, tab3 = st.tabs(["📊 Dashboard", "💬 AI Q&A", "ℹ️ About"])

# ==========================================================
# TAB 1: DASHBOARD
# ==========================================================
with tab1:
    st.markdown("### 📊 Explore the Survey Data")

    # Filter Panel
    with st.expander("🔎 Apply Filters", expanded=True):
        def pick_opts(series):
            try:
                return ["(All)"] + sorted([x for x in series.dropna().unique().tolist()])
            except:
                return ["(All)"]

        col1, col2, col3, col4 = st.columns(4)
        age_pick = col1.selectbox("Age Range", pick_opts(df.get("AGE_RANGE", pd.Series(dtype='object'))))
        gender_pick = col2.selectbox("Gender", pick_opts(df.get("GENDER", pd.Series(dtype='object'))))
        edu_pick = col3.selectbox("Education", pick_opts(df.get("EDUCATION_LEVEL", pd.Series(dtype='object'))))
        emp_pick = col4.selectbox("Employment", pick_opts(df.get("EMPLOYMENT_STATUS", pd.Series(dtype='object'))))

    # Apply Filters
    df_f = df.copy()
    if age_pick != "(All)": df_f = df_f[df_f["AGE_RANGE"] == age_pick]
    if gender_pick != "(All)": df_f = df_f[df_f["GENDER"] == gender_pick]
    if edu_pick != "(All)": df_f = df_f[df_f["EDUCATION_LEVEL"] == edu_pick]
    if emp_pick != "(All)": df_f = df_f[df_f["EMPLOYMENT_STATUS"] == emp_pick]

    st.success(f"🔍 Showing **{len(df_f):,}** filtered responses")

    # Table + Metrics Layout
    c1, c2 = st.columns([2.5, 1])

    with c1:
        st.markdown("#### 📑 Filtered Data")
        rows_per_page = 15
        total_pages = math.ceil(len(df_f) / rows_per_page)
        page = st.number_input("Page", min_value=1, max_value=max(total_pages, 1), step=1)
        start, end = (page - 1) * rows_per_page, (page - 1) * rows_per_page + rows_per_page
        st.dataframe(df_f.iloc[start:end], use_container_width=True, height=400)

    with c2:
        st.markdown("#### 📌 Quick Stats")
        st.metric("Total Records", f"{len(df):,}")
        st.metric("Filtered Records", f"{len(df_f):,}")
        if "AI_USAGE_RATING_NUM" in df_f.columns:
            avg_rating = df_f["AI_USAGE_RATING_NUM"].mean()
            st.metric("Avg Usage Rating", f"{avg_rating:.2f}")

    st.divider()

    # Visualization Layout
    col1, col2 = st.columns(2)
    with col1:
        if "AGE_RANGE" in df_f.columns and "AI_USAGE_RATING_NUM" in df_f.columns:
            st.markdown("#### 📈 Average AI Usage by Age Range")
            grp = df_f.groupby("AGE_RANGE")["AI_USAGE_RATING_NUM"].mean().sort_values()
            fig, ax = plt.subplots()
            grp.plot(kind="barh", ax=ax, color="skyblue")
            ax.set_xlabel("Average Rating (1–5)")
            st.pyplot(fig)

    with col2:
        if "WANT_MORE_AI" in df_f.columns:
            st.markdown("#### 🥧 Willingness to Use AI in Future")
            want_counts = df_f["WANT_MORE_AI"].fillna("Not Answered").value_counts()
            fig, ax = plt.subplots()
            ax.pie(
                want_counts.values,
                labels=want_counts.index,
                autopct="%1.1f%%",
                colors=["#4CAF50", "#FF9800", "#9E9E9E"]
            )
            ax.set_title("")
            st.pyplot(fig)

    col3, col4 = st.columns(2)
    with col3:
        if "TRUST_AI" in df_f.columns:
            st.markdown("#### 🤝 Trust in AI")
            trust_counts = df_f["TRUST_AI"].fillna("Not Answered").value_counts().sort_values()
            fig, ax = plt.subplots()
            trust_counts.plot(kind="barh", ax=ax, color="lightcoral")
            ax.set_xlabel("Respondents")
            st.pyplot(fig)

    with col4:
        if "TRUST_AI" in df_f.columns and "AI_USAGE_RATING_NUM" in df_f.columns:
            st.markdown("#### 🔥 Trust × Usage Rating")
            ct = pd.crosstab(df_f["TRUST_AI"], df_f["AI_USAGE_RATING_NUM"])
            fig, ax = plt.subplots()
            cax = ax.matshow(ct, aspect='auto', cmap="coolwarm")
            ax.set_xticks(range(len(ct.columns)))
            ax.set_xticklabels(ct.columns)
            ax.set_yticks(range(len(ct.index)))
            ax.set_yticklabels(ct.index)
            ax.set_xlabel("Usage Rating")
            ax.set_ylabel("Trust AI")
            fig.colorbar(cax)
            st.pyplot(fig)

# ==========================================================
# TAB 2: CHATBOT
# ==========================================================
with tab2:
    st.markdown("### 💬 AI Chatbot with Data + Chat History")
    st.info("Ask natural questions about the dataset. Example: *Which age group trusts AI the most?*")

    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Sidebar Chat Settings
    st.sidebar.markdown("### 🗂 Chat Settings")
    st.sidebar.button("🧹 Clear Chat", on_click=lambda: st.session_state.update({"messages": []}))
    st.sidebar.slider("History Length", 1, 25, 5, key="num_chat_messages")

    # Show Chat History
    icons = {"assistant": "🤖", "user": "👤"}
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"], avatar=icons.get(msg["role"])):
            st.markdown(msg["content"])

    # Handle Input
    if user_input := st.chat_input("Type your question here..."):
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user", avatar="👤"):
            st.markdown(user_input)

        with st.chat_message("assistant", avatar="🤖"):
            msg_container = st.empty()
            with st.spinner("Analyzing..."):
                valid_keywords = ["age", "gender", "education", "employment", "ai usage", "trust", "adoption"]
                if not any(kw in user_input.lower() for kw in valid_keywords):
                    answer = "⚠️ Sorry, your question seems outside the scope of the survey dataset."
                else:
                    context_str = df_f.head(20).to_string(index=False)
                    history = st.session_state.messages[-st.session_state.num_chat_messages:-1]
                    history_str = "\n".join(f"{m['role']}: {m['content']}" for m in history) or "No history."

                    prompt = f"""
You are a helpful assistant. Use the chat history and the table data below to answer the question.

Chat History:
{history_str}

Data Preview:
{context_str}

Question:
{user_input}
Answer:
""".strip()

                    escaped_prompt = json.dumps({"prompt": prompt})
                    escaped_prompt_sql = escaped_prompt.replace("'", "''")
                    sql = f"SELECT SNOWFLAKE.CORTEX.COMPLETE('claude-3-5-sonnet', '{escaped_prompt_sql}');"

                    try:
                        result = session.sql(sql).collect()
                        answer = result[0][0]
                    except Exception as e:
                        answer = f"⚠️ Error: {e}"

                msg_container.markdown(answer)

        st.session_state.messages.append({"role": "assistant", "content": answer})

# ==========================================================
# TAB 3: ABOUT
# ==========================================================
with tab3:
    st.markdown("### ℹ️ About This Project")
    st.markdown("""
    **AISIS: AI Survey Insights System**  
    This project analyzes public perceptions of Artificial Intelligence (AI) using survey data.  
    It provides both **interactive visual analytics** and an **AI-powered Q&A chatbot**.
    """)

    st.markdown("#### 📊 Dataset Source")
    st.markdown("""
    - **Title**: The Impact of Artificial Intelligence on Society  
    - **Author**: Arda Yavuz Keskin  
    - **Platform**: [Kaggle](https://www.kaggle.com/datasets/ardayavuzkeskin/the-impact-of-artificial-intelligence-on-society)  
    - **Size**: 205 responses, 20 variables  
    - **Focus**: Demographics, AI usage, trust in AI, and adoption
    """)

    st.markdown("#### 🛠️ Tools & Technologies")
    st.markdown("""
    - Snowflake (Data Warehouse & Cortex AI)  
    - Streamlit (Interactive Dashboard)  
    - Matplotlib / Altair (Visualizations)  
    - Python (Pandas, JSON, Math)
    """)

    st.markdown("#### 🎯 Objectives")
    st.markdown("""
    - Provide an **interactive way** to explore AI survey data  
    - Enable **natural language Q&A** using Cortex  
    - Support **researchers, educators, and policymakers**
    """)

    st.success("✅ This app demonstrates how AI can enhance survey data analysis and accessibility.")
