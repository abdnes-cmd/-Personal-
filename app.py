import streamlit as st
import pandas as pd
from datetime import datetime

# إعدادات الصفحة والهوية البصرية
st.set_page_config(page_title="الصندوق الشخصي", page_icon="💰", layout="wide")

# تصميم مخصص لتعديل اتجاه وتلوين الواجهة ليطابق نظام المسجد
st.markdown("""
    <style>
    .main { background-color: #f9fbf9; }
    h1, h2, h3, h4 { color: #004D40; font-family: 'Cairo', sans-serif; text-align: right; direction: rtl; }
    .stButton>button { background-color: #004D40; color: #D4AF37; border-radius: 5px; font-weight: bold; width: 100%; }
    .stButton>button:hover { background-color: #D4AF37; color: #004D40; }
    
    .custom-table {
        width: 100%;
        border-collapse: collapse;
        direction: rtl;
        text-align: right;
        margin-bottom: 20px;
        border: 1px solid #e0e0e0;
    }
    .custom-table th {
        padding: 12px;
        font-size: 16px;
        border: 1px solid #00332a;
    }
    .custom-table th:nth-child(odd) {
        background-color: #004D40 !important;
        color: #D4AF37 !important;
    }
    .custom-table th:nth-child(even) {
        background-color: #C5A059 !important;
        color: #FFFFFF !important;
    }
    .custom-table td {
        padding: 12px;
        border: 1px solid #e0e0e0;
        font-size: 15px;
    }
    .custom-table td:nth-child(odd) {
        background-color: #e8f5e9 !important;
        color: #004D40 !important;
        font-weight: bold;
    }
    .custom-table td:nth-child(even) {
        background-color: #fefde8 !important;
        color: #b45309 !important;
    }
    </style>
""", unsafe_allow_html=True)

# إدارة البيانات المحفوظة محلياً أو تخزين مؤقت لجلسة العمل
if 'personal_transactions' not in st.session_state:
    st.session_state['personal_transactions'] = pd.DataFrame(columns=[
        "id", "date", "description", "type", "amount_usd", "amount_lbp", "total_usd", "category"
    ])

if 'dollar_rate' not in st.session_state:
    st.session_state['dollar_rate'] = 89500.0

dollar_rate = st.session_state['dollar_rate']

DEFAULT_CATEGORIES = [
    "مصاريف شخصية",
    "عائلة",
    "طعام وشراب",
    "فواتير واشتراكات",
    "مدخول / راتب",
    "أخرى"
]

def safe_rerun():
    for rerun_func in ['rerun', 'experimental_rerun']:
        if hasattr(st, rerun_func):
            getattr(st, rerun_func)()
            break

def render_custom_html_table(headers, rows):
    html = "<table class='custom-table'><thead><tr>"
    for header in headers:
        html += f"<th>{header}</th>"
    html += "</tr></thead><tbody>"
    for row in rows:
        html += "<tr>"
        for cell in row:
            html += f"<td>{cell}</td>"
        html += "</tr>"
    html += "</tbody></table>"
    st.markdown(html, unsafe_allow_html=True)

# --- القائمة الجانبية ---
st.sidebar.markdown("<div style='text-align: center;'>", unsafe_allow_html=True)
st.sidebar.markdown("<h2 style='text-align: center; color: #D4AF37; margin-top: 0px;'>💰 الصندوق الشخصي</h2>", unsafe_allow_html=True)
st.sidebar.markdown("<p style='text-align: center; color: #004D40; font-weight: bold;'>إدارة المصاريف والدخل</p>", unsafe_allow_html=True)
st.sidebar.markdown("</div>", unsafe_allow_html=True)

page = st.sidebar.radio(
    "انتقل إلى:",
    [
        "🏠 الرئيسية (لوحة التحكم)",
        "📝 القيود اليومية",
        "📊 التقارير",
        "⚙️ الإعدادات"
    ],
    key="personal_side_nav"
)

df_trans = st.session_state['personal_transactions']

# --- 1. الصفحة الرئيسية ---
if page == "🏠 الرئيسية (لوحة التحكم)":
    st.markdown("<h1 style='text-align: center;'>لوحة التحكم المالية الشخصية (بالدولار)</h1>", unsafe_allow_html=True)
    st.markdown(f"<p style='text-align: center; color: #C5A059;'>سعر الصرف المعتمد حالياً: {dollar_rate:,.0f} ل.ل للدولار</p>", unsafe_allow_html=True)
    st.write("---")

    if not df_trans.empty:
        total_in = df_trans[df_trans['type'] == 'قبض']['total_usd'].sum()
        total_out = df_trans[df_trans['type'] == 'صرف']['total_usd'].sum()
    else:
        total_in, total_out = 0.0, 0.0
    current_balance = total_in - total_out

    col1, col2, col3 = st.columns(3)
    col1.metric("💰 الصافي الحالي ($)", f"${current_balance:,.0f}")
    col2.metric("🟢 إجمالي المقبوضات ($)", f"${total_in:,.0f}")
    col3.metric("🔴 إجمالي المصروفات ($)", f"${total_out:,.0f}")

    st.write("---")
    st.subheader("🚰 ملخص المصروفات حسب التصنيف ($)")
    if df_trans.empty or df_trans[df_trans['type'] == 'صرف'].empty:
        st.info("💡 لا توجد مصروفات مسجلة بعد.")
    else:
        df_ops = df_trans[df_trans['type'] == 'صرف']
        df_ops_grouped = df_ops.groupby('category')['total_usd'].sum().reset_index()
        headers = ["التصنيف / البيان", "إجمالي المبلغ المصروف ($)"]
        rows = [[row['category'], f"${row['total_usd']:,.0f}"] for _, row in df_ops_grouped.iterrows()]
        render_custom_html_table(headers, rows)

# --- 2. القيود اليومية ---
elif page == "📝 القيود اليومية":
    st.title("📝 تسجيل القيود اليومية")
    
    max_id = df_trans["id"].max() if not df_trans.empty else 0
    if pd.isna(max_id):
        max_id = 0
    st.info(f"رقم السند التلقائي القادم: {int(max_id) + 1}")

    col1, col2 = st.columns(2)
    t_date = col1.date_input("التاريخ", datetime.now(), key="p_date")
    t_type = col2.selectbox("نوع العملية", ["قبض", "صرف"], key="p_type")

    usd_amount_raw = col1.number_input("المبلغ بالدولار ($)", min_value=0.0, step=1.0, value=None, placeholder="اكتب المبلغ بالدولار مباشرة...", key="p_usd")
    lbp_amount_raw = col2.number_input("المبلغ بالليرة (ل.ل)", min_value=0.0, step=1000.0, value=None, placeholder="اكتب المبلغ بالليرة مباشرة...", key="p_lbp")

    usd_amount = usd_amount_raw if usd_amount_raw is not None else 0.0
    lbp_amount = lbp_amount_raw if lbp_amount_raw is not None else 0.0

    converted_instant = round(lbp_amount / dollar_rate) if dollar_rate > 0 else 0
    total_calculated_usd = round(usd_amount + converted_instant)

    if lbp_amount > 0:
        st.warning(f"📊 قيمة الليرة تعادل: {converted_instant:,.0f}$")

    category = col1.selectbox("التصنيف", DEFAULT_CATEGORIES, key="p_cat")
    description = st.text_area("البيان / التفاصيل", key="p_desc")

    if st.button("حفظ السند المالي", key="p_save_btn"):
        if total_calculated_usd == 0:
            st.error("الرجاء إدخال قيمة مالية.")
        elif not description:
            st.error("الرجاء إدخال البيان.")
        else:
            new_id = int(max_id) + 1
            new_row = pd.DataFrame([{
                "id": new_id,
                "date": str(t_date),
                "description": description,
                "type": t_type,
                "amount_usd": usd_amount,
                "amount_lbp": lbp_amount,
                "total_usd": total_calculated_usd,
                "category": category
            }])
            st.session_state['personal_transactions'] = pd.concat([df_trans, new_row], ignore_index=True)
            st.success("تم حفظ السند المالي بنجاح!")
            safe_rerun()

    st.write("---")
    st.subheader("📋 حذف السندات المسجلة")
    
    if df_trans.empty:
        st.info("💡 لا توجد قيود مسجلة بعد.")
    else:
        for idx, row in df_trans.tail(15).iterrows():
            c1, c2, c3, c4 = st.columns([1, 2, 4, 1])
            c1.write(f"**🔢 سند:** {row['id']}")
            c2.write(f"**📅:** {row['date']}")

            usd_val = float(row['amount_usd']) if pd.notnull(row['amount_usd']) else 0.0
            lbp_val = float(row['amount_lbp']) if pd.notnull(row['amount_lbp']) else 0.0
            tot_val = float(row['total_usd']) if pd.notnull(row['total_usd']) else 0.0

            u_str = f"${usd_val:,.0f}" if usd_val > 0 else "-"
            l_str = f"{lbp_val:,.0f} ل.ل" if lbp_val > 0 else "-"

            details = f"【 {row['type']} 】  •  كاش: {u_str}  •  ليرة: {l_str}  •  الإجمالي: ${tot_val:,.0f}  •  {row['description']} ({row['category']})"

            c3.write(details)
            if c4.button("🗑️ حذف", key=f"del_personal_{row['id']}"):
                st.session_state['personal_transactions'] = df_trans[df_trans['id'] != row['id']].reset_index(drop=True)
                st.success("تم الحذف!")
                safe_rerun()

# --- 3. التقارير ---
elif page == "📊 التقارير":
    st.title("📊 التقارير المالية والطباعة")
    rep_type = st.selectbox("نوع التقرير المراد عرضه", ["يومي", "شهري", "سنوي"], key="personal_rep_t")

    if df_trans.empty:
        st.info("💡 لا توجد قيود مسجلة تماماً.")
    else:
        df_trans['parsed_date'] = pd.to_datetime(df_trans['date'])
        if rep_type == "يومي":
            sel_date = st.date_input("اختر اليوم", datetime.now(), key="personal_rep_d")
            df_filtered = df_trans[df_trans['parsed_date'].dt.date == sel_date]
        elif rep_type == "شهري":
            sel_month = st.slider("اختر الشهر", 1, 12, int(datetime.now().month), key="personal_rep_m")
            df_filtered = df_trans[df_trans['parsed_date'].dt.month == sel_month]
        else:
            sel_year = st.number_input("حدد السنة", min_value=2020, value=int(datetime.now().year), key="personal_rep_y")
            df_filtered = df_trans[df_trans['parsed_date'].dt.year == sel_year]

        if df_filtered.empty:
            st.warning("⚠️ لا توجد معاملات مالية مسجلة لهذه الفترة.")
        else:
            headers = ["رقم السند", "التاريخ", "الحركة", "البيان والتفاصيل", "التصنيف", "المبلغ كاش ($)", "المبلغ بالليرة (ل.ل)", "الإجمالي الموحد ($)"]
            rows = []

            for _, r in df_filtered.iterrows():
                val_usd = float(r['amount_usd']) if pd.notnull(r['amount_usd']) else 0.0
                val_lbp = float(r['amount_lbp']) if pd.notnull(r['amount_lbp']) else 0.0
                val_total = float(r['total_usd']) if pd.notnull(r['total_usd']) else 0.0

                usd_cash_str = f"${val_usd:,.0f}" if val_usd > 0 else "-"
                lbp_str = f"{val_lbp:,.0f} ل.ل" if val_lbp > 0 else "-"
                total_usd_str = f"${val_total:,.0f}"

                rows.append([r['id'], r['date'], r['type'], r['description'], r['category'], usd_cash_str, lbp_str, total_usd_str])

            render_custom_html_table(headers, rows)

            st.write("---")
            total_in_rep = df_filtered[df_filtered['type'] == 'قبض']['total_usd'].sum()
            total_out_rep = df_filtered[df_filtered['type'] == 'صرف']['total_usd'].sum()
            net_rep = total_in_rep - total_out_rep

            # مطابقة لنظام المسجد تماماً (بدون مجموع الليرة وبنفس المقاييس)
            mc1, mc2, mc3 = st.columns(3)
            mc1.metric("🟢 إجمالي المقبوضات", f"${total_in_rep:,.0f}")
            mc2.metric("🔴 إجمالي المصروفات", f"${total_out_rep:,.0f}")
            mc3.metric("💰 الصافي للفترة", f"${net_rep:,.0f}")

            df_export = df_filtered.drop(columns=['parsed_date'])
            csv_data = df_export.to_csv(index=False).encode('utf-8-sig')

            st.download_button(
                label="📥 تحميل التقرير المعروض (CSV / Excel)",
                data=csv_data,
                file_name=f"personal_report_{rep_type}_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                key="personal_export_csv"
            )

# --- 4. الإعدادات ---
elif page == "⚙️ الإعدادات":
    st.title("⚙️ الإعدادات العامة")

    new_rate = st.number_input("تحديث سعر صرف الدولار مقابل الليرة اللبنانية", value=dollar_rate, step=500.0, key="personal_set_r")
    if st.button("تحديث سعر الصرف الآن", key="personal_set_save_r"):
        st.session_state['dollar_rate'] = new_rate
        st.success("تم تحديث سعر الصرف بنجاح!")
        safe_rerun()

    st.write("---")
    st.subheader("⚠️ منطقة خطر: تصفير العمليات والقيود")
    confirm_reset = st.checkbox("أوافق على حذف وتصفير جميع السندات والعمليات الحسابية نهائياً", key="personal_confirm_reset")
    if st.button("🔴 تصفير كافة العمليات الحسابية الآن", key="personal_reset_btn"):
        if confirm_reset:
            st.session_state['personal_transactions'] = pd.DataFrame(columns=[
                "id", "date", "description", "type", "amount_usd", "amount_lbp", "total_usd", "category"
            ])
            st.success("✅ تم تصفير كافة العمليات بنجاح والبدء من جديد!")
            safe_rerun()
        else:
            st.error("⚠️ يرجى تحديد مربع الموافقة أولاً لتأكيد رغبتك بالتصفير.")
