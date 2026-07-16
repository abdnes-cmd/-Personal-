import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import base64

# إعدادات الصفحة
st.set_page_config(page_title="الصندوق الشخصي", page_icon="💰", layout="centered")

# فك تشفير الرمز السري الجديد تلقائياً بأمان
ENCODED_KEY = "cGF0SzhhWkU2eUozTWt6THUuN2ZlZTE0NDJkOTdmZTYwNDg3YWZiNjZjNzg2YTc5MzUwZDk4NGNmMjY1YTcyYjc2Y2UxZWQ2Y2YzMWRhNTFjMw=="
AIRTABLE_API_KEY = base64.b64decode(ENCODED_KEY).decode("utf-8")

# إعدادات جدولك الفعلي الجديد
BASE_ID = "app8p8z76mWPa3fET"
TABLE_NAME = "tbl4VJzkXSFfZpvOd"

# إعداد رأس الطلب للاتصال بـ Airtable
headers = {
    "Authorization": f"Bearer {AIRTABLE_API_KEY}",
    "Content-Type": "application/json"
}
url = f"https://api.airtable.com/v0/{BASE_ID}/{TABLE_NAME}"

# دالة لجلب البيانات وعرضها
def fetch_data():
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            records = response.json().get("records", [])
            data = []
            for r in records:
                fields = r.get("fields", {})
                data.append({
                    "التاريخ": fields.get("التاريخ", ""),
                    "النوع": fields.get("النوع", ""),
                    "الفئة": fields.get("الفئة", ""),
                    "المبلغ": fields.get("المبلغ", 0),
                    "البيان": fields.get("البيان", "")
                })
            return pd.DataFrame(data)
        else:
            st.error(f"فشل الاتصال بـ Airtable. رمز الخطأ: {response.status_code}")
            return pd.DataFrame()
    except Exception as e:
        st.error(f"حدث خطأ أثناء الاتصال: {e}")
        return pd.DataFrame()

# دالة لإضافة معاملة جديدة
def add_record(date, trans_type, category, amount, description):
    payload = {
        "records": [
            {
                "fields": {
                    "التاريخ": date.strftime("%Y-%m-%d"),
                    "النوع": trans_type,
                    "الفئة": category,
                    "المبلغ": float(amount),
                    "البيان": description
                }
            }
        ]
    }
    try:
        response = requests.post(url, headers=headers, json=payload)
        return response.status_code == 200
    except Exception as e:
        st.error(f"حدث خطأ أثناء الإضافة: {e}")
        return False

# عنوان التطبيق
st.title("💰 الصندوق الشخصي للمدخول والمصروفات")
st.write("سجل معاملاتك المالية وراقب حركة صندوقك بسهولة.")

st.markdown("---")

# نموذج إضافة معاملة جديدة
st.subheader("📝 إضافة معاملة جديدة")
with st.form("transaction_form", clear_on_submit=True):
    col1, col2 = st.columns(2)
    with col1:
        amount = st.number_input("المبلغ", min_value=0.1, step=1.0, format="%.2f")
        category = st.text_input("الفئة (مثال: طعام، وقود، راتب...)")
    with col2:
        trans_type = st.selectbox("النوع", ["مصروف", "مدخول"])
        date = st.date_input("التاريخ", datetime.today())
        
    description = st.text_input("البيان / الوصف")
    
    submit_button = st.form_submit_button("إضافة المعاملة")

if submit_button:
    if not category:
         st.warning("الرجاء كتابة الفئة أولاً!")
    else:
        success = add_record(date, trans_type, category, amount, description)
        if success:
            st.success("🎉 تم تسجيل المعاملة بنجاح وإرسالها إلى Airtable!")
            st.rerun() # تحديث الصفحة فوراً لرؤية النتيجة
        else:
            st.error("❌ حدث خطأ أثناء محاولة إرسال البيانات. تأكد من مطابقة أسماء الحقول في جدول Airtable.")

st.markdown("---")

# عرض المعاملات المسجلة
st.subheader("📊 حركة الصندوق الحالية")
df = fetch_data()
if not df.empty:
    st.dataframe(df, use_container_width=True)
else:
    st.info("لا توجد معاملات مسجلة بعد في الجدول.")
