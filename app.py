import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import base64
import io

st.set_page_config(page_title="الصندوق الشخصي", page_icon="💰", layout="wide")

# إعدادات Airtable
ENCODED_KEY = "cGF0bmtsZ05WT0xlWjJ1RGYuNTk2NjgzMDM5NmRmOGUxOGNhNzkwYzVmYWU1NDlhZDdjOTk3Y2YxZDFjYWFjMDI2MTE1OTFkNDIzM2ZjNzYyYg=="
AIRTABLE_API_KEY = base64.b64decode(ENCODED_KEY).decode("utf-8")
BASE_ID = "app8p8z76mWPa3fET"
TABLE_NAME = "Table 1"
headers = {"Authorization": f"Bearer {AIRTABLE_API_KEY}", "Content-Type": "application/json"}
url = f"https://api.airtable.com/v0/{BASE_ID}/{TABLE_NAME}"

# دالة جلب البيانات
def fetch_data():
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            records = response.json().get("records", [])
            data = []
            for r in records:
                fields = r.get("fields", {})
                data.append({
                    "ID": r.get("id"),
                    "التاريخ": fields.get("التاريخ", ""),
                    "النوع": fields.get("النوع", ""),
                    "المبلغ": fields.get("المبلغ", 0),
                    "البيان": fields.get("البيان", "")
                })
            return pd.DataFrame(data)
        return pd.DataFrame()
    except: 
        return pd.DataFrame()

# --- واجهة التطبيق ---
st.title("💰 الصندوق الشخصي")

df = fetch_data()

# 1. لوحة التحكم (الخلاصة)
if not df.empty:
    income = df[df['النوع'] == 'المدخول']['المبلغ'].sum()
    expense = df[df['النوع'] == 'المصروف']['المبلغ'].sum()
    balance = income - expense
else:
    income, expense, balance = 0, 0, 0

# عرض الأرقام في الأعلى
col1, col2, col3 = st.columns(3)
col1.metric("إجمالي المدخول", f"{income:,.2f}")
col2.metric("إجمالي المصروف", f"{expense:,.2f}")
col3.metric("الرصيد المتبقي (الصندوق)", f"{balance:,.2f}", delta_color="normal")

st.markdown("---")

# 2. أزرار الإدارة
tab1, tab2 = st.tabs(["➕ إضافة معاملة", "⚙️ إدارة الصندوق"])

with tab1:
    with st.form("add_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        amount = c1.number_input("المبلغ", min_value=0.1, step=1.0)
        trans_type = c2.selectbox("النوع", ["المصروف", "المدخول"])
        date = st.date_input("التاريخ", datetime.today())
        desc = st.text_input("البيان")
        
        submitted = st.form_submit_button("إضافة")
        
        if submitted:
            payload = {
                "records": [{
                    "fields": {
                        "Name": desc,
                        "البيان": desc,
                        "النوع": trans_type,
                        "المبلغ": float(amount),
                        "التاريخ": date.strftime("%Y-%m-%d")
                    }
                }]
            }
            response = requests.post(url, headers=headers, json=payload)
            if response.status_code == 200:
                st.rerun()

with tab2:
    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button("🔄 تحديث البيانات", use_container_width=True): 
            st.rerun()
    with col_btn2:
        if st.button("🚨 تصفير الصندوق بالكامل", type="primary", use_container_width=True):
            if not df.empty:
                for r_id in df["ID"]: 
                    requests.delete(f"{url}/{r_id}", headers=headers)
                st.rerun()
    
    st.markdown("---")
    
    # قسم النسخ الاحتياطي والاستعادة
    st.markdown("### 💾 النسخ الاحتياطي والاستعادة (Backup & Restore)")
    col_back1, col_back2 = st.columns(2)
    
    with col_back1:
        st.write("**1. تحميل نسخة احتياطية:**")
        if not df.empty:
            # تحويل البيانات إلى ملف Excel في الذاكرة لتنزيله مباشرة
            buffer = io.BytesIO()
            # استبعاد عمود الـ ID الخاص بـ Airtable عند الحفظ لجعل الملف نظيفاً
            backup_df = df.drop(columns=["ID"]) if "ID" in df.columns else df
            
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                backup_df.to_excel(writer, index=False, sheet_name='البيانات')
            
            st.download_button(
                label="📥 تحميل ملف النسخة الاحتياطية (Excel)",
                data=buffer.getvalue(),
                file_name=f"صندوق_شخصي_نسخة_{datetime.today().strftime('%Y-%m-%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
        else:
            st.warning("لا توجد بيانات حالياً لتصديرها كنسخة احتياطية.")
            
    with col_back2:
        st.write("**2. استعادة من نسخة سابقة:**")
        uploaded_file = st.file_uploader("ارفع ملف الـ Excel لاستعادة البيانات:", type=["xlsx"])
        if uploaded_file is not None:
            if st.button("⏪ بدء عملية الاستعادة الآن", type="primary", use_container_width=True):
                try:
                    # قراءة الملف المرفوع
                    restore_df = pd.read_excel(uploaded_file)
                    
                    # التأكد من أن الأعمدة المطلوبة موجودة
                    required_columns = ["التاريخ", "النوع", "المبلغ", "البيان"]
                    if all(col in restore_df.columns for col in required_columns):
                        
                        progress_bar = st.progress(0)
                        total_rows = len(restore_df)
                        
                        # رفع الأسطر واحداً تلو الآخر إلى Airtable
                        for idx, row in restore_df.iterrows():
                            payload = {
                                "records": [{
                                    "fields": {
                                        "Name": str(row["البيان"]) if pd.notna(row["البيان"]) else "",
                                        "البيان": str(row["البيان"]) if pd.notna(row["البيان"]) else "",
                                        "النوع": str(row["النوع"]),
                                        "المبلغ": float(row["المبلغ"]),
                                        "التاريخ": str(row["التاريخ"])
                                    }
                                }]
                            }
                            requests.post(url, headers=headers, json=payload)
                            progress_bar.progress((idx + 1) / total_rows)
                        
                        st.success("🎉 تم استيراد واستعادة جميع البيانات بنجاح!")
                        st.rerun()
                    else:
                        st.error("تنبيه: أعمدة ملف الـ Excel المرفوع غير مطابقة لملفات الصندوق الأصلية.")
                except Exception as e:
                    st.error(f"حدث خطأ أثناء قراءة الملف: {e}")

    st.markdown("---")
    st.markdown("### 🗑️ حذف معاملات محددة")
    if not df.empty:
        st.write("اختر المعاملة (أو المعاملات) التي تريد حذفها:")
        options = {f"{row['التاريخ']} - {row['النوع']} - {row['المبلغ']} ({row['البيان']})": row['ID'] for _, row in df.iterrows()}
        selected_to_delete = st.multiselect("اختر المعاملات المراد حذفها:", options=list(options.keys()))
        
        if st.button("❌ حذف المعاملات المحددة", type="secondary"):
            if selected_to_delete:
                for item in selected_to_delete:
                    record_id = options[item]
                    requests.delete(f"{url}/{record_id}", headers=headers)
                st.success("تم الحذف!")
                st.rerun()
            else:
                st.warning("الرجاء اختيار معاملة.")

st.markdown("---")

# 3. عرض الجدول
st.subheader("📊 تفاصيل المعاملات")
if not df.empty:
    display_df = df.drop(columns=["ID"])
    st.dataframe(display_df, use_container_width=True)
else:
    st.info("لا توجد بيانات.")
