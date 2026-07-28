from datetime import datetime
import os
import pandas as pd
import streamlit as st

# إعداد الصفحة
st.set_page_config(page_title="الصندوق الشخصي", page_icon="💰", layout="centered")

DATA_FILE = "personal_box_data.csv"


def load_data():
  if os.path.exists(DATA_FILE):
    try:
      df = pd.read_csv(DATA_FILE)
      # التأكد من وجود الأعمدة المطلوبة لتجنب أخطاء الملفات القديمة
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
          # إذا كان الملف قديماً، نقوم بإعادة تهيئته نظيفاً
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


# تحميل البيانات
df = load_data()

# عنوان التطبيق
st.title("💰 إدارة الصندوق الشخصي")
st.markdown("---")

# الشريط الجانبي لإضافة معاملة جديدة
st.sidebar.header("➕ إضافة معاملة جديدة")

# تحديد سعر الصرف الحالي لليرة مقابل الدولار
exchange_rate = st.sidebar.number_input(
    "سعر الصرف (ليرة لكل 1 دولار)", min_value=1.0, value=89500.0, step=100.0
)

with st.sidebar.form("transaction_form", clear_on_submit=True):
  t_date = st.date_input("التاريخ", value=datetime.today())
  t_type = st.selectbox("النوع", ["مدخول", "مصروف"])

  # اختيار العملة والمبلغ
  currency = st.selectbox("عملة الدفع", ["دولار ($)", "ليرة لبنانية (ل.ل)"])
  t_amount = st.number_input("المبلغ المدفوع", min_value=0.0, step=1.0)

  # حساب المبلغ بالدولار تلقائياً
  if "ليرة" in currency:
    amount_usd = t_amount / exchange_rate if exchange_rate > 0 else 0
  else:
    amount_usd = t_amount

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
    st.sidebar.success(
        f"✅ تم الحفظ! (المبلغ بالدولار: ${amount_usd:,.2f})"
    )
    st.rerun()

# عرض البيانات والإجماليات
st.subheader("📊 سجل المعاملات (بالدولار)")

if not df.empty:
  # حساب الإجماليات بالدولار
  total_income = df[df["type"] == "مدخول"]["amount_usd"].sum()
  total_expense = df[df["type"] == "مصروف"]["amount_usd"].sum()
  net_balance = total_income - total_expense

  col1, col2, col3 = st.columns(3)
  col1.metric("إجمالي المداخيل ($)", f"${total_income:,.2f}")
  col2.metric("إجمالي المصاريف ($)", f"${total_expense:,.2f}")
  col3.metric("الصافي الحالي ($)", f"${net_balance:,.2f}")

  st.markdown("---")

  # عرض الجدول مع ترقيم تلقائي
  display_df = df.reset_index().rename(columns={"index": "ID"})
  display_df["ID"] = display_df["ID"] + 1
  st.dataframe(display_df, use_container_width=True)

  # زر لحذف معاملة عبر الـ ID
  st.markdown("### 🗑️ حذف معاملة")
  delete_id = st.number_input(
      "أدخل رقم (ID) المعاملة المراد حذفها",
      min_value=1,
      max_value=len(df),
      step=1,
  )
  if st.button("حذف المعاملة"):
    df = df.drop(index=delete_id - 1).reset_index(drop=True)
    save_data(df)
    st.success(f"تم حذف المعاملة رقم {delete_id} بنجاح!")
    st.rerun()

else:
  st.info("ℹ️ لا توجد معاملات مسجلة حتى الآن. ابدأ بإضافة معاملة جديدة من القائمة الجانبية.")
