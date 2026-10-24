import io
import json
from datetime import date
from urllib.parse import urlencode, quote_plus
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

import pandas as pd
import streamlit as st

st.set_page_config(page_title="B2B Lead Builder - Auto", page_icon="🎯", layout="wide")

st.markdown("""<style>
html, body, [class*="css"] { direction: rtl; }
[data-testid="stAppViewContainer"] { direction: rtl; }
[data-testid="stDataFrame"] { direction: ltr; }
</style>""", unsafe_allow_html=True)

APP_COLUMNS = [
    "Company Name", "Industry", "Official Website", "Country", "Headquarters / City",
    "Employees (if listed)", "Founded", "CEO / Executive (if listed)",
    "Contact Person", "Work Email", "Business Phone", "Completeness Score",
    "People Search Link", "Company Source", "Date Added", "Notes"
]

WIKIDATA_API = "https://www.wikidata.org/w/api.php"
WDQS_ENDPOINT = "https://query.wikidata.org/sparql"
USER_AGENT = "B2BLeadBuilder/1.0 (Streamlit public company research tool)"


def http_json(url, params=None, data=None, accept="application/json", timeout=50):
    if data is None and params:
        url = url + "?" + urlencode(params)
    body = urlencode(data).encode("utf-8") if data else None
    req = Request(url, data=body, headers={"User-Agent": USER_AGENT, "Accept": accept})
    with urlopen(req, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


@st.cache_data(ttl=86400, show_spinner=False)
def resolve_country(country_name):
    payload = http_json(
        WIKIDATA_API,
        params={"action": "wbsearchentities", "search": country_name, "language": "en",
                "format": "json", "type": "item", "limit": 10},
        timeout=20,
    )
    candidates = payload.get("search", [])
    target = " ".join(country_name.casefold().split())
    # Prefer an exact label describing a country/sovereign state.
    for item in candidates:
        label = " ".join(item.get("label", "").casefold().split())
        description = item.get("description", "").casefold()
        if label == target and ("country" in description or "sovereign state" in description):
            return item["id"], item.get("label", country_name)
    for item in candidates:
        description = item.get("description", "").casefold()
        if "country" in description or "sovereign state" in description:
            return item["id"], item.get("label", country_name)
    return None, None


def escape_sparql_literal(value):
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", " ").replace("\r", " ") + '"'


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_companies(country_qid, keyword, limit, only_with_website):
    filter_text = ""
    if keyword.strip():
        literal = escape_sparql_literal(keyword.strip())
        filter_text = f'''\n  FILTER(CONTAINS(LCASE(STR(?companyLabel)), LCASE({literal})) ||
         (BOUND(?industryLabel) && CONTAINS(LCASE(STR(?industryLabel)), LCASE({literal}))))'''

    website_filter = "\n  FILTER(BOUND(?website))" if only_with_website else ""
    query = f'''SELECT ?company ?companyLabel ?website ?industryLabel ?hqLabel ?employees ?inception ?executiveLabel WHERE {{
  ?company wdt:P17 wd:{country_qid}.
  VALUES ?companyClass {{ wd:Q4830453 wd:Q783794 }}
  ?company wdt:P31/wdt:P279* ?companyClass.
  OPTIONAL {{ ?company wdt:P856 ?website. }}
  OPTIONAL {{ ?company wdt:P452 ?industry. }}
  OPTIONAL {{ ?company wdt:P159 ?hq. }}
  OPTIONAL {{ ?company wdt:P1128 ?employees. }}
  OPTIONAL {{ ?company wdt:P571 ?inception. }}
  OPTIONAL {{ ?company wdt:P169 ?executive. }}
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en,ar". }}
  {website_filter}
  {filter_text}
}}
LIMIT {int(limit)}'''
    payload = http_json(
        WDQS_ENDPOINT,
        data={"query": query, "format": "json"},
        accept="application/sparql-results+json",
        timeout=58,
    )
    rows = payload.get("results", {}).get("bindings", [])
    records = []
    for row in rows:
        def val(key):
            return row.get(key, {}).get("value", "")

        company_uri = val("company")
        company_name = val("companyLabel") or company_uri.rsplit("/", 1)[-1]
        website = val("website")
        industry = val("industryLabel")
        hq = val("hqLabel")
        employees = val("employees")
        founded = val("inception")
        executive = val("executiveLabel")
        people_query = f'site:linkedin.com/in "{company_name}"'
        # The link helps the user research contacts manually; it does not scrape LinkedIn.
        people_url = "https://www.google.com/search?q=" + quote_plus(people_query)
        pieces = [bool(company_name), bool(website), bool(industry), bool(hq), bool(employees), bool(executive)]
        score = round(sum(pieces) / len(pieces) * 100)
        records.append({
            "Company Name": company_name,
            "Industry": industry,
            "Official Website": website,
            "Country": "",  # Filled with the user-selected country below.
            "Headquarters / City": hq,
            "Employees (if listed)": employees,
            "Founded": founded[:10] if founded else "",
            "CEO / Executive (if listed)": executive,
            "Contact Person": "",
            "Work Email": "",
            "Business Phone": "",
            "Completeness Score": score,
            "People Search Link": people_url,
            "Company Source": company_uri,
            "Date Added": date.today().isoformat(),
            "Notes": "Public company record; verify details before outreach."
        })
    df = pd.DataFrame(records, columns=APP_COLUMNS)
    if not df.empty:
        df = df.drop_duplicates(subset=["Company Source"], keep="first").reset_index(drop=True)
    return df


st.title("🎯 إنشاء ملف عملاء B2B تلقائيًا")
st.write("اكتب الدولة واضغط زر البحث؛ الأداة ستبحث في بيانات الشركات العامة في Wikidata وتجهّز جدولًا قابلًا للتنزيل Excel وCSV.")
st.info("مهم: هذه النسخة تُنشئ قائمة شركات تلقائيًا من مصدر بيانات عام. بيانات الأشخاص والبريد والهاتف ليست متاحة لكل شركة، لذلك لن نخترعها أو نعتبرها مؤكدة. رابط البحث عن جهات الاتصال يُنشأ للمساعدة في البحث اليدوي.")

with st.form("auto_search_form"):
    col1, col2 = st.columns(2)
    with col1:
        country = st.text_input("الدولة (اكتبها بالإنجليزية)", value="Egypt", help="مثال: Egypt, Saudi Arabia, United States")
        keyword = st.text_input("مجال أو كلمة تخص الشركة (اختياري)", placeholder="مثال: software, marketing, bank")
    with col2:
        target_role = st.text_input("المسمى الوظيفي الذي تريد البحث عنه لاحقًا (اختياري)", value="Marketing Manager", help="يُستخدم لتكوين رابط بحث عن الأشخاص، ولا يتم جمع ملفات LinkedIn آليًا.")
        max_results = st.selectbox("الحد الأقصى للنتائج", [50, 100, 250, 500], index=1)
    only_with_website = st.checkbox("اعرض الشركات التي لها موقع رسمي فقط", value=False)
    run_search = st.form_submit_button("🔎 ابحث وأنشئ ملف العملاء", type="primary", use_container_width=True)

if run_search:
    if not country.strip():
        st.error("اكتب اسم الدولة بالإنجليزية، مثل Egypt.")
    else:
        try:
            with st.spinner("جاري البحث في مصدر البيانات العامة..."):
                country_qid, country_label = resolve_country(country.strip())
                if not country_qid:
                    st.error("لم أتعرف على الدولة. اكتب اسمها بالإنجليزية، مثل Egypt أو Saudi Arabia.")
                else:
                    results = fetch_companies(country_qid, keyword.strip(), int(max_results), only_with_website)
                    if not results.empty:
                        results["Country"] = country_label or country.strip()
                        # Include target title in each generated people-search URL.
                        role = target_role.strip()
                        if role:
                            for idx, row in results.iterrows():
                                q = f'site:linkedin.com/in "{row["Company Name"]}" "{role}" {country_label or country.strip()}'
                                results.at[idx, "People Search Link"] = "https://www.google.com/search?q=" + quote_plus(q)
                    st.session_state["auto_results"] = results
                    st.session_state["auto_country"] = country_label or country.strip()
                    st.session_state["auto_keyword"] = keyword.strip()
                    st.session_state["auto_role"] = target_role.strip()
        except HTTPError as e:
            st.error(f"مصدر البيانات رفض الطلب (HTTP {e.code}). جرّب مرة أخرى بعد قليل أو قلّل عدد النتائج.")
        except URLError:
            st.error("تعذر الاتصال بمصدر البيانات. تأكد أن التطبيق متصل بالإنترنت ثم جرّب مرة أخرى.")
        except TimeoutError:
            st.error("البحث أخذ وقتًا أطول من المسموح. جرّب 50 أو 100 نتيجة بدلًا من 500.")
        except Exception as e:
            st.error(f"حدث خطأ أثناء البحث: {e}")

if "auto_results" in st.session_state:
    df = st.session_state["auto_results"].copy()
    st.divider()
    st.subheader("📄 الملف الذي تم إنشاؤه")
    st.write(f"عدد الشركات في النتائج: **{len(df)}**")
    if df.empty:
        st.warning("لم يعثر المصدر العام على نتائج بهذه الشروط. جرّب حذف كلمة المجال، أو ألغِ تحديد خيار الموقع الرسمي فقط، أو اختر دولة أخرى. بيانات Wikidata ليست دليلًا شاملًا لجميع الشركات.")
    else:
        st.dataframe(df, use_container_width=True, hide_index=True, column_config={
            "Official Website": st.column_config.LinkColumn("Official Website"),
            "People Search Link": st.column_config.LinkColumn("People Search Link"),
            "Company Source": st.column_config.LinkColumn("Company Source"),
            "Completeness Score": st.column_config.ProgressColumn("Completeness Score", min_value=0, max_value=100, format="%d%%"),
        })
        csv_bytes = df.to_csv(index=False).encode("utf-8-sig")
        xlsx_buffer = io.BytesIO()
        with pd.ExcelWriter(xlsx_buffer, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="B2B Leads")
            worksheet = writer.sheets["B2B Leads"]
            worksheet.freeze_panes = "A2"
            worksheet.auto_filter.ref = worksheet.dimensions
            for column_cells in worksheet.columns:
                max_len = max((len(str(cell.value or "")) for cell in column_cells[:100]), default=10)
                worksheet.column_dimensions[column_cells[0].column_letter].width = min(max(max_len + 2, 12), 38)
        d1, d2 = st.columns(2)
        with d1:
            st.download_button("⬇️ تنزيل ملف Excel", xlsx_buffer.getvalue(), file_name="b2b_leads_auto.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True, type="primary")
        with d2:
            st.download_button("⬇️ تنزيل ملف CSV", csv_bytes, file_name="b2b_leads_auto.csv", mime="text/csv", use_container_width=True)
    st.caption("المصدر: Wikidata Query Service. درجة الاكتمال تقيس عدد الحقول المتوفرة فقط، وليست تقييمًا لصحة الشركة أو جودة العميل المحتمل.")
    st.caption("مصدر البيانات: https://www.wikidata.org/ | خدمة الاستعلام الرسمية: https://query.wikidata.org/")

with st.expander("ماذا تعني الأداة بإنشاء الملف تلقائيًا؟"):
    st.write("بمجرد الضغط على زر البحث، تجلب الأداة بيانات الشركات المتاحة من المصدر العام، وترتبها في جدول، ثم تتيح تنزيل Excel أو CSV. لا تضمن هذه البيانات كل الشركات في الدولة، ولا تجمع البريد أو الهاتف تلقائيًا عندما لا يكونان متاحين في المصدر. استخدم بيانات التواصل وفق شروط المصدر والقوانين المعمول بها.")
