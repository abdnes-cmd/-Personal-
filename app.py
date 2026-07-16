import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import base64

# إعدادات الصفحة
st.set_page_config(page_title="الصندوق الشخصي", page_icon="💰", layout="centered")

# فك تشفير الرمز السري
ENCODED_KEY = "cGF0bmtsZ05WT0xlWjJ1RGYuNTk2NjgzMDM5NmRmOGUxOGNhNzkwYzVmYWU1NDlhZDdjOTk3Y2YxZDFjYWFjMDI2MTE1OTFkNDIzM2ZjNzYyYg=="
AIRTABLE_API_KEY = base64.b64decode(ENCODED_KEY).decode("utf-8")

# الإعدادات
BASE_ID = "app8p8z76mWPa3fET"
TABLE_NAME = "Table 1"  

headers = {
    "Authorization": f"Bearer {AIRTABLE_API_KEY}",
    "Content-Type": "application/json"
}
url = f"https://api.airtable.com/v0/{BASE_ID}/{TABLE_NAME}"

# دالة جلب البيانات مع جلب المعرف الفريد (ID) للحذف
def fetch_data():
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            records = response.json().get("records", [])
            data = []
            for r in records:
                fields = r.get("fields", {})
                data.append({
                    "ID": r.get("id"),  # نحتفظ بالمعرف للحذف
                    "التاريخ": fields.get("التاريخ", ""),
                    "النوع": fields.get("النوع", ""),
                    "المبلغ": fields.get("المبلغ", 0),
                    "البيان": fields.get("البيان", "")
                })
            df = pd.DataFrame(data)
            return df
        else:
            st.error(f"فشل الاتصال بـ Airtable. رمز الخطأ: {response.status_code}")
            return pd.DataFrame()
    except Exception as e:
        st.error(f"حدث خطأ غير متوقع أثناء جلب البيانات: {e}")
        return pd.DataFrame()

# دالة إضافة معاملة
def add_record(date, trans_type, amount, description):
    payload = {
        "records": [
            {
                "fields": {
                    "Name": description,
                    "البيان": description,
                    "النوع": trans_type,
                    "المبلغ": float(amount),
                    "التاريخ": date.strftime("%Y-%m-%d")
                }
            }
        ]
    }
    try:
        response = requests.post(url, headers=headers, json=payload)
        return response.status_code == 200, response.text
    except Exception as e:
        return False, str(e)

# دالة حذف معاملة واحدة باستخدام الـ ID
def delete_record(record_id):
    try:
        delete_url = f"{url}/{record_id}"
        response = requests.delete(delete_url, headers=headers)
        return response.status_code == 200
    except Exception as e:
        st.error(f"خطأ أثناء الحذف: {e}")
        return False

# دالة تصفير الصندوق بالكامل
def clear_all_records(df):
    if df.empty:
        return True
    
    # Airtable يسمح بحذف حتى 10 سجلات في الطلب الواحد
    ids_to_delete = df["ID"].tolist()
    success = True
    
    # نقوم بحذف السجلات على دفعات
    for i in range(0, len(ids_to_delete), 10):
        batch = ids_to_delete[i:i+10]
        params = [("records[]", r_id) for r_id in batch]
        try:
            response = requests.delete(url, headers=headers, params=params)
            if response.status_code != 200:
                success = False
        except Exception:
            success = False
            
    return success

# عنوان التطبيق الرئيسي
st.title("💰 الصندوق الشخصي للمدخول والمصروفات")
st.write("سجل معاملاتك المالية، وراقب حركة صندوقك، وتحكم ببياناتك بالكامل.")

st.markdown("---")

# جلب البيانات الحالية وتخزينها في جلسة العمل
df = fetch_data()

# أزرار الإدارة العلوية (استعادة البيانات وتصفير الصندوق)
col_refresh, col_clear = st.columns([1, 1])

with col_refresh:
    if st.button("🔄 استعادة وتحديث البيانات", use_container_width=True):
        st.rerun()

with col_clear:
    # تصفير الصندوق مع نظام تأكيد لحماية البيانات من الحذف الخاطئ
    if "confirm_clear" not in st.session_state:
        st.session_state.confirm_clear = False
        
    if not st.session_state.confirm_clear:
        if st.button("🚨 تصفير الصندوق بالكامل", use_container_width=True, type="secondary"):
            st.session_state.confirm_clear = True
            st.rerun()
    else:
        st.warning("⚠️ هل أنت متأكد من رغبتك في حذف وتصفير جميع البيانات؟ لا يمكن التراجع!")
        col_yes, col_no = st.columns(2)
        with col_yes:
            if st.button("نعم، احذف الكل", use_container_width=True, type="primary"):
                if clear_all_records(df):
                    st.success("🧹 تم تصفير الصندوق بالكامل بنجاح!")
                else:
                    st.error("حدثت مشكلة أثناء محاولة مسح بعض البيانات.")
                st.session_state.confirm_clear = False
                st.rerun()
        with col_no:
            if st.button("إلغاء التصفير", use_container_width=True):
                st.session_state.confirm_clear = False
                st.rerun()

st.markdown("---")

# نموذج إضافة معاملة جديدة
st.subheader("📝 إضافة معاملة جديدة")
with st.form("transaction_form", clear_on_submit=True):
    col1, col2 = st.columns(2)
    with col1:
        amount = st.number_input("المبلغ", min_value=0.1, step=1.0, format="%.2f")
    with col2:
        trans_type = st.selectbox("النوع", ["المصروف", "المدخول"])
        date = st.date_input("التاريخ", datetime.today())
        
    description = st.text_input("البيان / الوصف")
    submit_button = st.form_submit_button("إضافة المعاملة")

if submit_button:
    success, message = add_record(date, trans_type, amount, description)
    if success:
        st.success("🎉 تم تسجيل المعاملة بنجاح!")
        st.rerun()
    else:
        st.error(f"❌ حدث خطأ أثناء الإرسال: {message}")

st.markdown("---")

# عرض المعاملات المسجلة وقسم الحذف المفرد
st.subheader("📊 حركة الصندوق الحالية")

if not df.empty:
    # إخفاء عمود الـ ID من الجدول المعروض للمستخدم لشكل أرتب
    display_df = df.drop(columns=["ID"]) if "ID" in df.columns else df
    st.dataframe(display_df, use_container_width=True)
    
    st.markdown("---")
    # قسم حذف معاملة معينة
    st.subheader("🗑️ حذف معاملة محددة")
    # ننشئ نصاً واضحاً لكل معاملة في القائمة المنسدلة لكي يسهل اختيارها
    df['display_name'] = df.apply(lambda row: f"{row['التاريخ']} | {row['النوع']} | {row['المبلغ']} | {row['البيان']}", axis=1)
    
    selected_option = st.selectbox("اختر المعاملة التي ترغب بحذفها:", df['display_name'].tolist())
    
    if st.button("حذف المعاملة المحددة", type="primary"):
        # جلب الـ ID المرتبط بالخيار المختار
        record_id_to_delete = df[df['display_name'] == selected_option]['ID'].values[0]
        if delete_record(record_id_to_delete):
            st.success("🗑️ تم حذف المعاملة المحددة بنجاح!")
            st.rerun()
        else:
            st.error("فشل حذف المعاملة.")
else:
    st.info("لا توجد معاملات مسجلة بعد في الجدول.")
