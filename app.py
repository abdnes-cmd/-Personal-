from datetime import datetime
import os
import pandas as pd
import streamlit as st

# إعداد الصفحة
st.set_page_config(page_title="الصندوق الشخصي", page_icon="💰", layout="centered")

# ملف تخزين البيانات محلياً لتجنب مشاكل الاتصال
DATA_FILE = "personal_box_data.csv"


def load_data():
  if os.path.exists(DATA_FILE):
    return pd.read_csv(DATA_FILE)
  else:
    # إنشاء جدول فارغ بالعمود المطلوبة إذا لم يكن موجوداً
    return pd.DataFrame(
        columns=["date", "type", "amount", "category", "description", "notes"]
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
    new_row = {
        "date": str(t_date),
        "type": t_type,
        "amount": float(t_amount),
        "category": t_category,
        "description": t_description,
        "notes": t_notes,
    }
    # إضافة الصف الجديد للجدول
    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    save_data(df)
    st.sidebar.success("✅ تم حفظ المعاملة بنجاح!")
    st.rerun()

# عرض البيانات والإجماليات
st.subheader("📊 سجل المعاملات")

if not df.empty:
  # حساب الإجماليات
  total_income = df[df["type"] == "مدخول"]["amount"].sum()
  total_expense = df[df["type"] == "مصروف"]["amount"].sum()
  net_balance = total_income - total_expense

  col1, col2, col3 = st.columns(3)
  col1.metric("إجمالي المداخيل", f"{total_income:,.2f}")
  col2.metric("إجمالي المصاريف", f"{total_expense:,.2f}")
  col3.metric("الصافي الحالي", f"{net_balance:,.2f}")

  st.markdown("---")

  # عرض الجدول مع إضافة عمود الترقيم التلقائي (الرقم التسلسلي)
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
