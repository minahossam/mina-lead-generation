B2B Lead Builder - Automatic company list version

This version automatically queries public company records from Wikidata and builds an Excel/CSV file.

Install/deploy:
1. Upload app_auto.py to the root of your existing GitHub repository.
2. Keep the existing requirements.txt (streamlit, pandas, openpyxl). requests is not required; the app uses Python's standard library for HTTP.
3. In Streamlit Community Cloud, open your app's settings or deploy a new app from the same repository.
4. Set Main file path to: app_auto.py
5. Deploy / Reboot the app.
6. Enter a country (English works best), optional industry keyword, then click "ابحث وأنشئ ملف العملاء".
7. Download the generated Excel or CSV file.

Important limitations:
- The app uses the public Wikidata Query Service and only finds records available there. It does not represent a complete business directory.
- Publicly listed work emails, phones, and contact-person details may be missing; the app intentionally leaves unknown fields blank.
- People Search Link is a link to open a manual search. The app does not scrape LinkedIn or Google search results.
- The Completeness Score shows how many fields are populated, not whether the lead is verified.
