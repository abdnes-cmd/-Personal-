import streamlit as st
import pandas as pd
import requests
import datetime
import urllib.parse

# إعدادات الصفحة وتصميمها
st.set_page_config(page_title="الصندوق الشخصي للمدخول والمصروف", page_icon="💰", layout="centered")

# تعديل اتجاه الصفحة ليدعم اللغة العربية وتنسيق العناصر بشكل أفضل
st.markdown("""
    <style>
    .reportview-container, .stApp {
        direction: RTL;
        text-align: right;
    }
    .stMarkdown, div[data-testid="stBlock"], div[data-baseweb="select"], .stTextInput, .stNumberInput, .stTextArea {
        direction: RTL;
        text-align: right;
    }
    .stSelectbox label, .stDateInput label, .stTextInput label, .stNumberInput label, .stTextArea label {
        direction: RTL;
        text-align: right;
        float: right;
    }
    </style>
    """, unsafe_allow_html=True)

# جلب الرموز السرية وتنظيفها مع معالجة الأخطاء
try:
    AIRTABLE_API_KEY = str(st.secrets["airtable"]["api_key"]).strip()
    AIRTABLE_BASE_ID = str(st.secrets["airtable"]["base_id"]).strip()
    AIRTABLE_TABLE_NAME = str(st.secrets["airtable"]["table_name"]).strip()
except Exception:
    st.error("⚠️ تنبيه: يرجى إعداد الـ Secrets الخاصة بـ Airtable (api_key, base_id, table_name) في إعدادات التطبيق.")
    st.stop()

# تشفير اسم الجدول آلياً
ENCODED_TABLE_NAME = urllib.parse.quote(AIRTABLE_TABLE_NAME)
AIRTABLE_URL = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{ENCODED_TABLE_NAME}"

# التعديل النهائي لضمان نجاح الاتصال وتجنب خطأ 401
HEADERS = {
    "Authorization": f"Bearer {AIRTABLE_API_KEY}",
    "Content-Type": "application/json"
}

# دالة جلب البيانات
def get_data():
    try:
        response = requests.get(AIRTABLE_URL, headers=HEADERS)
        response.encoding = 'utf-8' 
        
        if response.status_code == 200:
            records = response.json().get("records", [])
            data = []
            for r in records:
                fields = r.get("fields", {})
                data.append({
                    "التاريخ": fields.get("التاريخ", ""),
                    "البيان": fields.get("البيان", ""),
                    "النوع": fields.get("النوع", ""),
                    "الفئة": fields.get("الفئة", ""),
                    "المبلغ": fields.get("المبلغ", 0.0),
                    "ملاحظات": fields.get("ملاحظات", "")
                })
            return pd.DataFrame(data)
        else:
            st.error(f"تنبيه: فشل الاتصال بقاعدة Airtable (كود الخطأ: {response.status_code}). يرجى التأكد من صحة الرموز السرية واسم الجدول في الـ Secrets.")
            return pd.DataFrame()
    except Exception as e:
        st.error(f"حدث خطأ أثناء محاولة جلب البيانات: {str(e)}")
        return pd.DataFrame()

# دالة إضافة عملية جديدة
def add_record(date, desc, record_type, category, amount, notes):
    payload = {
        "records": [
            {
                "fields": {
                    "التاريخ": str(date),
                    "البيان": desc,
                    "النوع": record_type,
                    "الفئة": category,
                    "المبلغ": float(amount),
                    "ملاحظات": notes
                }
            }
        ]
    }
    try:
        response = requests.post(AIRTABLE_URL, headers=HEADERS, json=payload)
        return response.status_code == 200
    except Exception:
        return False

# عنوان البرنامج الرئيسي
st.title("💰 برنامج الصندوق الشخصي الشهري")
st.write("إدارة ومتابعة الراتب والمصروفات مقسمة ومستقلة حسب كل شهر بكل سهولة.")
st.markdown("---")

# جلب البيانات الحالية
df = get_data()

if not df.empty:
    # تحويل العمود لتاريخ لسهولة المعالجة
    df['التاريخ_تاريخ'] = pd.to_datetime(df['التاريخ'], errors='coerce')
    df = df.dropna(subset=['التاريخ_تاريخ']) # استبعاد أي تاريخ غير صالح
    df = df.sort_values(by="التاريخ_تاريخ", ascending=False)
    
    # استخراج الأشهر والسنوات المتوفرة في البيانات
    df['الشهر_والسنة'] = df['التاريخ_تاريخ'].dt.strftime('%Y-%m') # صيغة (YYYY-MM)
    
    available_months = sorted(df['الشهر_والسنة'].unique(), reverse=True)
    
    # 1. أولاً: اختيار الشهر للتقرير
    st.subheader("📅 اختيار الشهر للتقرير المستقل")
    current_month_str = datetime.date.today().strftime('%Y-%m')
    default_index = available_months.index(current_month_str) if current_month_str in available_months else 0
    
    selected_month = st.selectbox("اختر الشهر المراد عرضه ومتابعته:", available_months, index=default_index)
    
    # تصفية البيانات حسب الشهر المحدد
    filtered_df = df[df['الشهر_والسنة'] == selected_month]
    
    # حساب الإحصائيات للشهر المختار
    total_income = filtered_df[filtered_df["النوع"] == "المدخول"]["المبلغ"].sum()
    total_expense = filtered_df[filtered_df["النوع"] == "المصروف"]["المبلغ"].sum()
    monthly_balance = total_income - total_expense
    
    # 2. ثانياً: عرض اللوحة المالية (الملخص بترتيب عمودي مشابه لبرنامج المسجد)
    st.markdown(f"### 📊 لوحة التحطم المالية لشهر ({selected_month})")
    
    st.metric(label="🏦 رصيد الصندوق المتبقي الحالي ($)", value=f"${monthly_balance:,.2f}", delta=f"${monthly_balance:,.2f}")
    st.metric(label="🟢 إجمالي المدخول / الراتب ($)", value=f"${total_income:,.2f}")
    st.metric(label="🔴 إجمالي المصروفات ($)", value=f"${total_expense:,.2f}")

    st.markdown("---")
    
    # عرض جدول عمليات الشهر المختار فقط
    st.subheader(f"📋 عمليات وسجلات شهر ({selected_month}) المستقلة")
    display_df = filtered_df.drop(columns=['التاريخ_تاريخ', 'الشهر_والسنة'])
    st.dataframe(display_df, use_container_width=True)

else:
    st.info("لا توجد عمليات مسجلة حالياً لبدء الفلترة الشهرية. يمكنك البدء بإضافة أول عملية أدناه.")

st.markdown("---")

# 3. نموذج إدخال عملية جديدة في الأسفل
st.subheader("📝 تسجيل عملية جديدة (راتب / مصروف)")
with st.form("add_transaction_form", clear_on_submit=True):
    col_a, col_b = st.columns(2)
    
    with col_a:
        date_val = st.date_input("التاريخ (سيتم توجيه العملية لشهرها تلقائياً)", datetime.date.today())
        desc_val = st.text_input("البيان / الوصف (مثال: راتب، صيانة سيارة)")
        amount_val = st.number_input("المبلغ ($)", min_value=0.0, step=1.0, format="%.2f")
        
    with col_b:
        type_val = st.selectbox("النوع", ["المدخول", "المصروف"])
        category_val = st.selectbox("الفئة", ["راتب وعمل", "منزل", "سيارة", "طاقة شمسية", "أخرى"])
        notes_val = st.text_area("ملاحظات إضافية")
        
    submit_button = st.form_submit_button("حفظ العملية في السحابة")

if submit_button:
    if desc_val.strip() == "" or amount_val <= 0.0:
        st.warning("الرجاء تعبئة حقل البيان وإدخال قيمة صحيحة للمبلغ لإتمام الحفظ.")
    else:
        with st.spinner("جاري حفظ العملية في السحابة..."):
            success = add_record(date_val, desc_val, type_val, category_val, amount_val, notes_val)
            if success:
                st.success("تم تسجيل وحفظ العملية بنجاح!")
                st.rerun()
            else:
                st.error("حدث خطأ أثناء محاولة حفظ البيانات، يرجى مراجعة إعدادات الـ Secrets.")
