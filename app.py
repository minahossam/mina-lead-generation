import io
from datetime import date
from urllib.parse import quote_plus

import pandas as pd
import streamlit as st

st.set_page_config(page_title="B2B Lead Builder", page_icon="🎯", layout="wide")

COLUMNS = [
    "Full Name", "Job Title", "Company", "LinkedIn URL", "Work Email",
    "Email Status", "Business Phone", "Company Website", "Country", "City",
    "Industry", "Company Size", "Source", "Date Added", "Notes"
]

st.markdown("""<style>
html, body, [class*="css"] { direction: rtl; }
[data-testid="stAppViewContainer"] { direction: rtl; }
[data-testid="stDataFrame"] { direction: ltr; }
</style>""", unsafe_allow_html=True)

st.title("🎯 أداة تجهيز قوائم عملاء B2B")
st.write("ابحث يدويًا في المصادر المسموح بها، ثم سجّل العملاء المحتملين ونزّل ملف Excel أو CSV. الأداة لا تسحب بيانات LinkedIn تلقائيًا ولا تتحقق من البريد تلقائيًا.")

with st.expander("1) إنشاء بحث عن العملاء المحتملين", expanded=True):
    c1, c2 = st.columns(2)
    with c1:
        job = st.text_input("المسمى الوظيفي", placeholder="مثال: Marketing Manager")
        country = st.text_input("الدولة", placeholder="مثال: Egypt")
    with c2:
        company = st.text_input("الشركة (اختياري)", placeholder="مثال: شركة معينة")
        keywords = st.text_input("كلمات إضافية (اختياري)", placeholder="مثال: SaaS, agency")
    search_type = st.radio("نوع البحث", ["أشخاص على LinkedIn", "شركات ومواقعها"], horizontal=True)
    parts = []
    if job.strip(): parts.append(job.strip())
    if country.strip(): parts.append(country.strip())
    if company.strip(): parts.append(company.strip())
    if keywords.strip(): parts.append(keywords.strip())
    if search_type == "أشخاص على LinkedIn":
        query = "site:linkedin.com/in " + " ".join(parts)
    else:
        query = "company website " + " ".join(parts)
    if parts:
        url = "https://www.google.com/search?q=" + quote_plus(query)
        st.link_button("افتح نتائج البحث في Google", url, type="primary")
        st.caption("افتح النتائج بنفسك، وسجّل فقط البيانات المهنية المتاحة علنًا والتي تسمح شروط المصدر باستخدامها.")
    else:
        st.info("اكتب على الأقل المسمى الوظيفي أو الدولة أو كلمة بحث.")

st.divider()
st.subheader("2) أضف البيانات أو ارفع ملفًا موجودًا")
if "leads" not in st.session_state:
    st.session_state.leads = pd.DataFrame(columns=COLUMNS)

uploaded = st.file_uploader("رفع ملف CSV أو Excel (اختياري)", type=["csv", "xlsx"])
if uploaded is not None:
    try:
        if uploaded.name.lower().endswith(".csv"):
            imported = pd.read_csv(uploaded, dtype=str).fillna("")
        else:
            imported = pd.read_excel(uploaded, dtype=str).fillna("")
        for col in COLUMNS:
            if col not in imported.columns:
                imported[col] = ""
        st.session_state.leads = imported[COLUMNS].copy()
        st.success(f"تم تحميل {len(imported)} صف. يمكنك مراجعة الجدول أدناه.")
    except Exception as e:
        st.error(f"تعذر قراءة الملف. تأكد أنه ملف CSV أو Excel سليم. التفاصيل: {e}")

st.caption("يمكنك الكتابة في الصفوف الفارغة مباشرة. احفظ نسخة من ملفك عند الانتهاء لأن هذه النسخة البسيطة لا تحتفظ بالبيانات بشكل دائم عند إغلاق الجلسة.")
edited = st.data_editor(
    st.session_state.leads,
    num_rows="dynamic",
    use_container_width=True,
    hide_index=True,
    key="lead_editor",
    column_config={
        "LinkedIn URL": st.column_config.LinkColumn("LinkedIn URL"),
        "Company Website": st.column_config.LinkColumn("Company Website"),
        "Email Status": st.column_config.SelectboxColumn("Email Status", options=["", "Not checked", "Verified", "Invalid", "Unknown"]),
        "Date Added": st.column_config.TextColumn("Date Added", help="مثال: 2026-10-24"),
    },
)
st.session_state.leads = edited

b1, b2, b3 = st.columns(3)
with b1:
    if st.button("تنظيف التكرارات", use_container_width=True):
        df = st.session_state.leads.copy().fillna("")
        for c in COLUMNS:
            df[c] = df[c].astype(str).str.strip()
        url_mask = df["LinkedIn URL"].ne("")
        email_mask = df["Work Email"].ne("")
        keep = pd.Series(True, index=df.index)
        # Keep the first record for each non-empty LinkedIn URL and work email.
        keep &= ~(url_mask & df["LinkedIn URL"].duplicated(keep="first"))
        df = df.loc[keep].copy()
        email_mask = df["Work Email"].ne("")
        df = df.loc[~(email_mask & df["Work Email"].duplicated(keep="first"))].copy()
        st.session_state.leads = df.reset_index(drop=True)
        st.success("تم حذف التكرارات حسب رابط LinkedIn والبريد المهني.")
        st.rerun()
with b2:
    csv_bytes = st.session_state.leads.to_csv(index=False).encode("utf-8-sig")
    st.download_button("تنزيل CSV", csv_bytes, file_name="b2b_leads.csv", mime="text/csv", use_container_width=True)
with b3:
    xlsx_buffer = io.BytesIO()
    with pd.ExcelWriter(xlsx_buffer, engine="openpyxl") as writer:
        st.session_state.leads.to_excel(writer, index=False, sheet_name="B2B Leads")
    st.download_button("تنزيل Excel", xlsx_buffer.getvalue(), file_name="b2b_leads.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)

st.caption(f"عدد الصفوف الحالية: {len(st.session_state.leads)} | تاريخ اليوم: {date.today().isoformat()}")
with st.expander("مهم قبل استخدام البيانات تجاريًا"):
    st.write("لا تستخدم بوتات أو طرقًا تتجاوز قيود المواقع. لا تعتبر البريد صحيحًا لمجرد وجوده؛ احتفظ بحالة التحقق ومصدر البيانات وتاريخ جمعها. راجع شروط المصدر والقوانين المحلية وقواعد التواصل التسويقي قبل جمع البيانات أو بيعها أو استخدامها.")
