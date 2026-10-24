إصلاح نسخة B2B Lead Builder — timeout في البحث العام

لماذا ظهر الخطأ؟
النسخة السابقة كانت تستخدم استعلام SPARQL واسعًا ومعقّدًا. خدمة Wikidata Query Service لديها حد تنفيذ ثابت، وقد تنتهي المهلة حتى عندما تكون المدخلات صحيحة. هذا الإصلاح يستخدم البحث النصي المفهرس في واجهة Wikidata API ثم يقرأ خصائص الكيانات، مع إعادة محاولة محدودة.

طريقة التثبيت (مع الاحتفاظ بالنسخ القديمة):
1) ارفع app_next_fixed.py إلى الصفحة الرئيسية في مستودع GitHub نفسه باستخدام Add file > Upload files.
2) لا تحذف app.py أو app_auto.py أو app_next.py.
3) تأكد أن requirements.txt يحتوي على streamlit وpandas وopenpyxl وrequests. إن كان موجودًا، حدّثه إلى المحتوى الموجود في هذا الملف.
4) افتح share.streamlit.io/deploy وأنشئ تطبيقًا جديدًا من المستودع نفسه.
5) Branch: main
6) Main file path: app_next_fixed.py
7) اضغط Deploy.

اختبار مقترح:
- Search source: Companies — free public source
- Country: Egypt
- Keyword: software
- Maximum results: 100

ملاحظات:
- البحث النصي المفهرس أفضل من استعلام SPARQL واسع للنصوص، لكنه لا يضمن نتائج كثيرة ولا يمثل كل شركات العالم.
- إذا كانت النتائج صفرًا، استخدم رابط البحث اليدوي أو جرّب كلمات مثل software company أو logistics أو marketing.
- البريد والهاتف لا يتم اختلاقهما؛ يحتاجان مصدرًا موثوقًا ومسموحًا به.
- احتفظ بالتطبيق القديم كنسخة احتياطية حتى تختبر الإصلاح.
