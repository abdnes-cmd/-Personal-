from datetime import datetime
import pandas as pd
from supabase import create_client
import streamlit as st

# إعداد الصفحة
st.set_page_config(
    page_title="الصندوق الشخصي", page_icon="💰", layout="wide"
)

# جلب الإعدادات السرية من Streamlit Secrets
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


# الاتصال السحابي بـ Supabase
@st.cache_resource
def init_connection():
  return create_client(SUPABASE_URL, SUPABASE_KEY)


supabase = init_connection()

# عنوان التطبيق
st.title("💰 إدارة الصندوق الشخصي (سحابي 100%)")
st.markdown("---")

# جلب البيانات الحية من السحابة
try:
  response = supabase.table(TABLE_NAME).select("*").execute()
  data = response.data
  df = pd.DataFrame(data) if data else pd.DataFrame()
except Exception as e:
  st.error(f"❌ تعذر الاتصال بقاعدة البيانات السحابية: {e}")
  df = pd.DataFrame()

# --- 1. حالة الصندوق والإجماليات في الأعلى ---
st.subheader("📊 حالة الصندوق والإجماليات")

if not df.empty and "amount_usd" in df.columns:
  total_income = df[df["type"] == "مدخول"]["amount_usd"].sum()
  total_expense = df[df["type"] == "مصروف"]["amount_usd"].sum()
  net_balance = total_income - total_expense
else:
  total_income = 0.0
  total_expense = 0.0
  net_balance = 0.0

col1, col2, col3 = st.columns(3)
col1.metric("إجمالي المداخيل ($)", f"${total_income:,.2f}")
col2.metric("إجمالي المصاريف ($)", f"${total_expense:,.2f}")
col3.metric("الصافي الحالي ($)", f"${net_balance:,.2f}")

st.markdown("---")

# --- 2. إضافة معاملة جديدة ---
st.subheader("➕ إضافة معاملة جديدة للسحابة")

with st.form("transaction_form", clear_on_submit=True):
  c1, c2, c3, c4 = st.columns(4)

  with c1:
    t_date = st.date_input("التاريخ", value=datetime.today())
    t_type = st.selectbox("النوع", ["مدخول", "مصروف"])

  with c2:
    currency = st.selectbox("عملة الدفع", ["دولار ($)", "ليرة لبنانية (ل.ل)"])
    t_amount = st.number_input("المبلغ المدفوع", min_value=0.0, step=1.0)

  with c3:
    exchange_rate = st.number_input(
        "سعر الصرف (ليرة/$)", min_value=1.0, value=89500.0, step=100.0
    )
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

  with c4:
    t_description = st.text_input("البيان / الوصف")
    t_notes = st.text_input("ملاحظات")

  submit_button = st.form_submit_button(label="حفظ المعاملة بالسحابة")

  if submit_button:
    if "ليرة" in currency:
      amount_usd = t_amount / exchange_rate if exchange_rate > 0 else 0
    else:
      amount_usd = t_amount

    new_row = {
        "date": str(t_date),
        "type": t_type,
        "amount_usd": round(float(amount_usd), 2),
        "original_amount": float(t_amount),
        "currency": currency,
        "category": t_category,
        "description": t_description,
        "notes": t_notes,
    }

    try:
      supabase.table(TABLE_NAME).insert(new_row).execute()
      st.success(
          f"✅ تم الحفظ في السحابة بنجاح! (المبلغ بالدولار: ${amount_usd:,.2f})"
      )
      st.rerun()
    except Exception as e:
      st.error(f"❌ خطأ أثناء الحفظ في قاعدة البيانات: {e}")

st.markdown("---")

# --- 3. سجل المعاملات وخيارات الحذف ---
st.subheader("📋 جدول تنظيم المعاملات السحابية")

if not df.empty:
  st.dataframe(df, use_container_width=True)

  st.markdown("### 🗑️ حذف معاملة")
  d_col1, d_col2 = st.columns([2, 1])
  with d_col1:
    delete_id = st.number_input(
        "أدخل معرف (ID) المعاملة المراد حذفها", min_value=1, step=1
    )
  with d_col2:
    st.write("")
    st.write("")
    if st.button("حذف المعاملة من السحابة"):
      try:
        supabase.table(TABLE_NAME).delete().eq("id", delete_id).execute()
        st.success(f"تم حذف المعاملة رقم {delete_id} بنجاح من السحابة!")
        st.rerun()
      except Exception as e:
        st.error(f"خطأ في الحذف: {e}")
else:
  st.info("ℹ️ لا توجد معاملات مسجلة في السحابة حتى الآن.")
