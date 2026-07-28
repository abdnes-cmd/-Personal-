from datetime import datetime
import pandas as pd
from supabase import create_client
import streamlit as st

# إعداد الصفحة
st.set_page_config(page_title="الصندوق الشخصي", page_icon="💰", layout="centered")

# جلب الإعدادات من Secrets
try:
  SUPABASE_URL = st.secrets["SUPABASE_URL"]
  SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
  TABLE_NAME = st.secrets["table_name"]
except Exception as e:
  st.error(
      "⚠️ يرجى التأكد من إضافة إعدادات الـ Secrets بشكل صحيح في لوحة تحكم"
      " Streamlit."
  )
  st.stop()


# الاتصال بـ Supabase
@st.cache_resource
def init_connection():
  return create_client(SUPABASE_URL, SUPABASE_KEY)


supabase = init_connection()

# عنوان التطبيق
st.title("💰 إدارة الصندوق الشخصي")
st.markdown("---")

# الشريط الجانبي لإضافة معاملة جديدة
st.sidebar.header("➕ إضافة معاملة جديدة")

with st.sidebar.form("transaction_form", clear_on_submit=True):
  t_date = st.date_input("التاريخ", value=datetime.today())
  t_type = st.selectbox("النوع", ["مدخول", "مصروف"])
  t_amount = st.number_input("المبلغ", min_value=0.0, step=0.5)
  t_category = st.selectbox(
      "الفئة",
      [
          "راتب",
          "تجارة",
          "أكل وشرب",
          "فواتير",
          "مواصلات",
          "ترفيه",
          "متفرقات",
      ],
  )
  t_description = st.text_input("البيان / الوصف")
  t_notes = st.text_area("ملاحظات")

  submit_button = st.form_submit_button(label="حفظ المعاملة")

  if submit_button:
    try:
      data = {
          "date": str(t_date),
          "type": t_type,
          "amount": float(t_amount),
          "category": t_category,
          "description": t_description,
          "notes": t_notes,
      }
      response = supabase.table(TABLE_NAME).insert(data).execute()
      st.sidebar.success("✅ تم حفظ المعاملة بنجاح!")
      st.rerun()
    except Exception as e:
      st.sidebar.error(f"❌ حدث خطأ أثناء الحفظ: {e}")

# جلب البيانات وعرضها
try:
  response = supabase.table(TABLE_NAME).select("*").execute()
  data = response.data

  if data:
    df = pd.DataFrame(data)

    st.subheader("📊 سجل المعاملات")

    # حساب الإجماليات
    total_income = df[df["type"] == "مدخول"]["amount"].sum()
    total_expense = df[df["type"] == "مصروف"]["amount"].sum()
    net_balance = total_income - total_expense

    col1, col2, col3 = st.columns(3)
    col1.metric("إجمالي المداخيل", f"{total_income:,.2f}")
    col2.metric("إجمالي المصاريف", f"{total_expense:,.2f}")
    col3.metric("الصافي الحالي", f"{net_balance:,.2f}")

    st.markdown("---")

    # عرض الجدول
    st.dataframe(df, use_container_width=True)

    # زر لحذف معاملة عبر الـ ID
    st.markdown("### 🗑️ حذف معاملة")
    delete_id = st.number_input(
        "أدخل معرف (ID) المعاملة المراد حذفها", min_value=1, step=1
    )
    if st.button("حذف المعاملة"):
      try:
        supabase.table(TABLE_NAME).delete().eq("id", delete_id).execute()
        st.success(f"تم حذف المعاملة رقم {delete_id} بنجاح!")
        st.rerun()
      except Exception as e:
        st.error(f"خطأ في الحذف: {e}")

  else:
    st.info("ℹ️ لا توجد معاملات مسجلة حتى الآن. ابدأ بإضافة معاملة جديدة من القائمة الجانبية.")

except Exception as e:
    st.error(f"❌ تعذر جلب البيانات من قاعدة البيانات: {e}")
