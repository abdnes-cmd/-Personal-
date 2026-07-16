import streamlit as st
import pandas as pd
import requests
import datetime
import urllib.parse

# إعدادات الصفحة وتصميمها
st.set_page_config(page_title="الصندوق الشخصي للمدخول والمصروف", page_icon="💰", layout="centered")

# تعديل اتجاه الصفحة ليدعم اللغة العربية
st.markdown("""
    <style>
    .reportview-container {
        direction: RTL;
        text-align: right;
    }
    .stMarkdown, div[data-testid="stBlock"] {
        direction: RTL;
        text-align: right;
    }
    div[data-baseweb="select"] {
        direction: RTL;
    }
    </style>
    """, unsafe_allow_html=True)

# جلب الرموز السرية وتنظيفها من أي مسافات زائدة
AIRTABLE_API_KEY = str(st.secrets["airtable"]["api_key"]).strip()
AIRTABLE_BASE_ID = str(st.secrets["airtable"]["base_id"]).strip()
AIRTABLE_TABLE_NAME = str(st.secrets["airtable"]["table_name"]).strip()

# تشفير اسم الجدول بشكل آمن تماماً للروابط
ENCODED_TABLE_NAME = urllib.parse.quote(AIRTABLE_TABLE_NAME)

# بناء الرابط بشكل آمن ليدعم كافة الحروف والرموز
AIRTABLE_URL = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{ENCODED_TABLE_NAME}"

# إعداد الهيدر بطريقة تمنع التعارض مع الأحرف غير اللاتينية في التوكن
# قمنا بتعديل طريقة كتابة التوكن للتأكد من خلوه من أي تشفير معقد قد يعيق المكتبة
HEADERS = {
    "Authorization": f"Bearer {AIRTABLE_API_KEY}".encode('utf-8').decode('latin-1'),
    "Content-Type": "application/json; charset=utf-8"
}

# دالة جلب البيانات مع معالجة الأخطاء والترميز
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
st.title("💰 برنامج الصندوق الشخصي")
st.write("إدارة ومتابعة المدخولات والمصروفات الشخصية بكل سهولة وأمان.")
st.markdown("---")

# جلب البيانات الحالية وعرضها
df = get_data()

# 1. قسم الإحصائيات وعرض الرصيد الحالي
if not df.empty:
    df['التاريخ'] = pd.to_datetime(df['التاريخ']).dt.date
    df = df.sort_values(by="التاريخ", ascending=False)
    
    total_income = df[df["النوع"] == "المدخول"]["المبلغ"].sum()
    total_expense = df[df["النوع"] == "المصروف"]["المبلغ"].sum()
    current_balance = total_income - total_expense
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(label="💵 إجمالي المدخول", value=f"{total_income:,.2f}")
    with col2:
        st.metric(label="💸 إجمالي المصروف", value=f"{total_expense:,.2f}")
    with col3:
        st.metric(label="🏦 الرصيد المتبقي الحالي", value=f"{current_balance:,.2f}", delta=f"{current_balance:,.2f}")
else:
    st.info("لا توجد عمليات مسجلة حالياً.")

st.markdown("---")

# 2. نموذج إدخال عملية جديدة
st.subheader("📝 تسجيل عملية جديدة")
with st.form("add_transaction_form", clear_on_submit=True):
    col_a, col_b = st.columns(2)
    
    with col_a:
        date_val = st.date_input("التاريخ", datetime.date.today())
        desc_val = st.text_input("البيان / الوصف (مثال: راتب، صيانة سيارة)")
        amount_val = st.number_input("المبلغ", min_value=0.0, step=1.0, format="%.2f")
        
    with col_b:
        type_val = st.selectbox("النوع", ["المدخول", "المصروف"])
        category_val = st.selectbox("الفئة", ["منزل", "سيارة", "طاقة شمسية", "راتب وعمل", "أخرى"])
        notes_val = st.text_area("ملاحظات إضافية")
        
    submit_button = st.form_submit_button("حفظ العملية")

if submit_button:
    if desc_val == "" or amount_val == 0.0:
        st.warning("الرجاء تعبئة حقل البيان وإدخال قيمة المبلغ لإتمام الحفظ.")
    else:
        with st.spinner("جاري حفظ العملية في Airtable..."):
            success = add_record(date_val, desc_val, type_val, category_val, amount_val, notes_val)
            if success:
                st.success("تم تسجيل وحفظ العملية بنجاح!")
                st.rerun()
            else:
                st.error("حدث خطأ أثناء محاولة حفظ البيانات، يرجى مراجعة إعدادات الـ Secrets.")

st.markdown("---")

# 3. جدول عرض آخر العمليات بالتفصيل
st.subheader("📋 سجل العمليات المدخلة (الأحدث أولاً)")
if not df.empty:
    st.dataframe(df, use_container_width=True)
else:
    st.write("الجدول فارغ، قم بإضافة أولى عملياتك من النموذج لتبدأ بالظهور هنا.")
