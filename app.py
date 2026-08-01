from datetime import datetime
import os
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="الصندوق الشخصي", page_icon="💰", layout="wide"
)

DATA_FILE = "personal_box_data.csv"


def load_data():
  if os.path.exists(DATA_FILE):
    try:
      df = pd.read_csv(DATA_FILE)
      if "amount_usd" in df.columns:
        df["amount_usd"] = pd.to_numeric(
            df["amount_usd"], errors="coerce"
        ).fillna(0)
      return df
    except:
      return pd.DataFrame()
  return pd.DataFrame()


def save_data(df):
  df.to_csv(DATA_FILE, index=False)


df = load_data()

st.title("💰 إدارة الصندوق الشخصي")
st.markdown("---")

# --- شريط إدارة البيانات، النسخ الاحتياطي، والتصفير ---
with st.expander("⚙️ إدارة البيانات والنسخ الاحتياطي والتصفير"):
  col_up, col_down = st.columns(2)

  with col_up:
    st.subheader("📤 تحميل نسخة احتياطية")
    if not df.empty:
      csv_data = df.to_csv(index=False).encode("utf-8")
      st.download_button(
          label="📥 تحميل ملف البيانات (CSV)",
          data=csv_data,
          file_name=f"my_box_backup_{datetime.today().strftime('%Y-%m-%d')}.csv",
          mime="text/csv",
      )
    else:
      st.info("لا توجد بيانات لتحميلها بعد.")

  with col_down:
    st.subheader("📥 استعادة البيانات")
    uploaded_file = st.file_uploader(
        "ارفع ملفك السابق:", type=["csv", "xlsx"]
    )
    if uploaded_file is not None:
      try:
        if uploaded_file.name.endswith(".csv"):
          imported_df = pd.read_csv(uploaded_file)
        else:
          imported_df = pd.read_excel(uploaded_file)
        df = pd.concat([df, imported_df], ignore_index=True).drop_duplicates()
        save_data(df)
        st.success("✅ تمت الاستعادة بنجاح!")
        st.rerun()
      except Exception as e:
        st.error(f"خطأ: {e}")

  st.markdown("---")
  st.subheader("⚠️ تصفير البيانات")
  confirm_reset = st.checkbox("أنا متأكد من رغبتي في حذف جميع البيانات")
  if st.button("🗑️ تصفير كل البيانات نهائياً", type="primary"):
    if confirm_reset:
      if os.path.exists(DATA_FILE):
        os.remove(DATA_FILE)
      st.success("🧹 تم التصفير بنجاح!")
      st.rerun()
    else:
      st.error("⚠️ يجب تحديد مربع التأكيد أولاً.")

st.markdown("---")

# --- 1. حالة الصندوق والإجماليات ---
st.subheader("📊 حالة الصندوق والإجماليات")

if not df.empty and "amount_usd" in df.columns:
  df["amount_usd"] = pd.to_numeric(df["amount_usd"], errors="coerce").fillna(0)
  total_income = df[df["type"].astype(str).str.contains("مدخول", na=False)][
      "amount_usd"
  ].sum()
  total_expense = df[df["type"].astype(str).str.contains("مصروف", na=False)][
      "amount_usd"
  ].sum()
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
st.subheader("➕ إضافة معاملة جديدة")

with st.form("transaction_form", clear_on_submit=True):
  c1, c2, c3, c4 = st.columns(4)

  with c1:
    t_date = st.date_input("التاريخ", value=datetime.today())
    # جعل "مصروف" هو الخيار الافتراضي الأول
    t_type = st.selectbox("النوع", ["مصروف", "مدخول"])

  with c2:
    currency = st.selectbox("عملة الدفع", ["دولار ($)", "ليرة لبنانية (ل.ل)"])
    # جعل قيمة المبلغ فارغة لتجنب الاضطرار لمسح الأصفار
    t_amount = st.number_input(
        "المبلغ المدفوع", min_value=0.0, value=None, step=1.0, placeholder="أدخل المبلغ..."
    )

  with c3:
    exchange_rate = st.number_input(
        "سعر الصرف (ليرة/$)", min_value=1.0, value=89500.0, step=100.0
    )
    t_category = st.selectbox(
        "الفئة",
        [
            "أكل وشرب",
            "فواتير",
            "مواصلات",
            "ترفيه",
            "راتب",
            "تجارة",
            "متفرقات",
        ],
    )

  with c4:
    t_description = st.text_input("البيان / الوصف")
    t_notes = st.text_input("ملاحظات")

  submit_button = st.form_submit_button(label="حفظ المعاملة")

  if submit_button:
    if t_amount is None:
      t_amount = 0.0

    if "ليرة" in currency:
      amount_usd = t_amount / exchange_rate if exchange_rate > 0 else 0
    else:
      amount_usd = t_amount

    new_row = {
        "date": str(t_date),
        "type": t_type,
        "amount_usd": round(amount_usd, 2),
        "original_amount": t_amount,
        "currency": currency,
        "category": t_category,
        "description": t_description,
        "notes": t_notes,
    }
    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    save_data(df)
    st.success(f"✅ تم الحفظ بنجاح! ($ {amount_usd:,.2f})")
    st.rerun()

st.markdown("---")

# --- 3. سجل المعاملات وخيارات الحذف ---
st.subheader("📋 جدول تنظيم المعاملات")

if not df.empty:
  display_df = df.reset_index().rename(columns={"index": "ID"})
  display_df["ID"] = display_df["ID"] + 1
  st.dataframe(display_df, use_container_width=True)

  st.markdown("### 🗑️ حذف معاملة مفردة")
  d_col1, d_col2 = st.columns([2, 1])
  with d_col1:
    delete_id = st.number_input(
        "أدخل رقم (ID) المعاملة المراد حذفها",
        min_value=1,
        max_value=len(df),
        step=1,
    )
  with d_col2:
    st.write("")
    st.write("")
    if st.button("حذف المعاملة"):
      df = df.drop(index=delete_id - 1).reset_index(drop=True)
      save_data(df)
      st.success(f"تم حذف المعاملة رقم {delete_id} بنجاح!")
      st.rerun()
else:
  st.info("ℹ️ لا توجد معاملات مسجلة حتى الآن.")
