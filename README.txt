B2B Lead Builder Pro - Version 2

Files:
- app_pro.py: upgraded Streamlit app. Upload this file to the root of your current GitHub repository.
- requirements.txt: Python dependencies used by the app.

Recommended safe upgrade path (keeps the current app available):
1. Open your GitHub repository.
2. Click Add file -> Upload files.
3. Upload app_pro.py to the repository root. Do not upload the ZIP file itself.
4. If requirements.txt already exists, open it and make sure it contains these three lines:
   streamlit
   pandas
   openpyxl
   Save changes (Commit changes). If it does not exist, upload/create the supplied requirements.txt.
5. In Streamlit Community Cloud, deploy a NEW app from the same repository and branch main, with Main file path app_pro.py.
6. Keep the existing app_auto.py deployment until you test the new app.

Current capabilities:
- Arabic/English user interface.
- Automatic search of public company records available through Wikidata.
- Optional worldwide query or a specific country; industry/keyword search; target job title used for Google X-Ray research links.
- Optional website and company employee-size filters; requested result caps 100-2000 (not guaranteed).
- Import CSV/Excel and combine imported rows with public-source records.
- Duplicate detection and merging, completeness score, source/date fields.
- Formatted Excel with Leads and Summary sheets, plus CSV export.

Important boundaries:
- This version does not scrape Google or LinkedIn results and does not automatically collect private contact data.
- Contact information is filled only when present in an uploaded file or public record; missing values remain blank.
- Wikidata is not a complete global company directory. Large queries can time out or be limited by the public query service.
