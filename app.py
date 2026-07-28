from datetime import datetime
import os
import pandas as pd
import streamlit as st

# إعداد الصفحة بعرض كامل لتناسب التصميم العلوي
st.set_page_config(
    page_title="الصندوق الشخصي", page_icon="💰", layout="wide"
)

DATA_FILE = "personal_box_data.csv"


def load_data():
  if os.path.exists(DATA_FILE):
    try:
      df = pd.read_csv(DATA_FILE)
      required_columns = [
          "date",
          "type",
          "amount_usd",
          "original_amount",
          "currency",
          "category",
          "description",
          "notes",
      ]
      for col in required_columns:
        if col not in df.columns:
          return pd.DataFrame(columns=required_columns)
      return df
    except:
      return pd.DataFrame(
          columns=[
              "date",
              "type",
              "amount_usd",
              "original_amount",
              "currency",
              "category",
              "description",
              "notes",
          ]
      )
  else:
    return pd.DataFrame(
        columns=[
            "date",
            "type",
            "amount_usd",
            "original_amount",
            "currency",
            "category",
            "description",
            "notes",
        ]
    )


def save_data(df):
  df.to_csv(DATA_FILE, index=False)


df = load_data()

# عنوان التطبيق
st.title("💰 إدارة الصندوق الشخصي")
st.markdown("---")

# --- 1. القائمة الرئيسية في الأعلى (نموذج الإدخال) ---
st.subheader("➕ إضافة معاملة جديدة")

with st.form("transaction_form", clear_on_submit=True):
  # نضع المدخلات مقسمة على أعمدة في الأعلى لترتيب أنيق
  col_a1, col_a2, col_a3, col_a4 = st.columns(4)

  with col_a1:
    t_date = st.date_input("التاريخ", value=datetime.today())
    t_type = st.selectbox("النوع", ["مدخول", "مصروف"])

  with col_a2:
    currency = st.selectbox("عملة الدفع", ["دولار ($)", "ليرة لبنانية (ل.ل)"])
    t_amount = st.number_input("المبلغ المدفوع", min_value=0.0, step=1.0)

  with col_a3:
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

  with col_a4:
    t_description = st.text_input("البيان / الوصف")
    t_notes = st.text_input("ملاحظات")

  submit_button = st.form_submit_button(label="حفظ المعاملة في الصندوق")

  if submit_button:
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
    st.success(f"✅ تم الحفظ بنجاح! (المبالغ محسوبة بالدولار: ${amount_usd:,.2f})")
    st.rerun()

st.markdown("---")

# --- 2. قسم المعلومات والإجماليات والجدول في الأسفل ---
st.subheader("📊 سجل المعاملات والمعلومات العامة")

if not df.empty:
  # حساب الإجماليات
  total_income = df[df["type"] == "مدخول"]["amount_usd"].sum()
  total_expense = df[df["type"] == "مصروف"]["amount_usd"].sum()
  net_balance = total_income - total_expense

  # عرض الإجماليات في كروت واضحة بالأسفل
  m_col1, m_col2, m_col3 = st.columns(3)
  m_col1.metric("إجمالي المداخيل ($)", f"${total_income:,.2f}")
  m_col2.metric("إجمالي المصاريف ($)", f"${total_expense:,.2f}")
  m_col3.metric("الصافي الحالي ($)", f"${net_balance:,.2f}")

  st.markdown("")

  # عرض جدول البيانات
  display_df = df.reset_index().rename(columns={"index": "ID"})
  display_df["ID"] = display_df["ID"] + 1
  st.dataframe(display_df, use_container_width=True)

  # قسم الحذف
  st.markdown("### 🗑️ حذف معاملة")
  d_col1, d_col2 = st.columns([2, 1])
  with d_col1:
    delete_id = st.number_input(
        "أدخل رقم (ID) المعاملة المراد حذفها",
        min_value=1,
        max_value=len(df),
        step=1,
    )
  with d_col2:
    st.write("")  # مسافة محاذاة
    st.write("")
    if st.button("حذف المعاملة المحددة"):
      df = df.drop(index=delete_id - 1).reset_index(drop=True)
      save_data(df)
      st.success(f"تم حذف المعاملة رقم {delete_id} بنجاح!")
      st.rerun()

else:
  st.info(
      "ℹ️ لا توجد معاملات مسجلة حتى الآن. استخدم نموذج الإدخال في الأعلى لإضافة"
      " أول معاملة."
  )
