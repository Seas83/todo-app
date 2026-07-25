import streamlit as st
from supabase import create_client, Client
from datetime import datetime, timedelta

# 1. إعداد الصفحة
st.set_page_config(page_title="نظام إدارة المهام", page_icon="📋", layout="wide")

# 2. جلب معلومات الاتصال
SUPABASE_URL = st.secrets.get("SUPABASE_URL", "")
SUPABASE_KEY = st.secrets.get("SUPABASE_KEY", "")

if not SUPABASE_URL or not SUPABASE_KEY:
    st.error("⚠️ يرجى التأكد من إضافة SUPABASE_URL و SUPABASE_KEY في Secrets.")
    st.stop()

@st.cache_resource
def init_supabase() -> Client:
    return create_client(SUPABASE_URL, SUPABASE_KEY)

try:
    supabase = init_supabase()
except Exception as e:
    st.error(f"خطأ في الاتصال بقاعدة البيانات: {e}")
    st.stop()

# 3. قائمة المستخدمين
USERS = {
    "user1": "pass123",
    "user2": "pass123",
    "user3": "pass123"
}

# 4. إدارة الجلسة
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "username" not in st.session_state:
    st.session_state.username = ""
if "last_seen_task_id" not in st.session_state:
    st.session_state.last_seen_task_id = 0
if "view_mode" not in st.session_state:
    st.session_state.view_mode = "main"

# --- شاشة تسجيل الدخول ---
if not st.session_state.authenticated:
    st.title("🔐 تسجيل الدخول - فريق العمل")
    
    with st.form("login_form"):
        username_input = st.text_input("اسم المستخدم")
        password_input = st.text_input("كلمة السر", type="password")
        submit = st.form_submit_button("دخول")
        
        if submit:
            if username_input in USERS and USERS[username_input] == password_input:
                st.session_state.authenticated = True
                st.session_state.username = username_input
                st.rerun()
            else:
                st.error("اسم المستخدم أو كلمة السر غير صحيحة")

# --- الشاشة الرئيسية / الأرشيف ---
else:
    col_user, col_nav, col_logout = st.columns([5, 3, 2])
    
    with col_user:
        st.title(f"📋 لوحة المهام | أهلاً {st.session_state.username}")
    
    with col_nav:
        st.write("")
        if st.session_state.view_mode == "main":
            if st.button("🗄️ أرشيف قاعدة البيانات"):
                st.session_state.view_mode = "archive"
                st.rerun()
        else:
            if st.button("🏠 العودة للوحة الرئيسية"):
                st.session_state.view_mode = "main"
                st.rerun()

    with col_logout:
        st.write("")
        if st.button("تسجيل الخروج"):
            st.session_state.authenticated = False
            st.session_state.username = ""
            st.session_state.view_mode = "main"
            st.rerun()

    st.divider()

    # === العرض 1: الشاشة الرئيسية (تقتصر على المهام قيد التنفيذ) ===
    if st.session_state.view_mode == "main":
        st.subheader("➕ إضافة مهمة جديدة")
        with st.form("add_task_form", clear_on_submit=True):
            task_title = st.text_input("عنوان المهمة")
            assigned_user = st.selectbox("تعيين إلى", list(USERS.keys()))
            add_submit = st.form_submit_button("إضافة المهمة")
            
            if add_submit:
                if task_title.strip():
                    supabase.table("tasks").insert({
                        "title": task_title,
                        "assigned_to": assigned_user,
                        "status": "قيد التنفيذ"
                    }).execute()
                    st.success("تمت إضافة المهمة بنجاح!")
                    st.rerun()
                else:
                    st.warning("يرجى كتابة عنوان للمهمة.")

        st.divider()
        st.subheader("📌 المهام النشطة (قيد التنفيذ)")
        
        try:
            # جلب المهام المخزنة
            response = supabase.table("tasks").select("*").order("id", desc=True).execute()
            all_tasks = response.data

            if all_tasks:
                max_id = max(task['id'] for task in all_tasks)
                
                # فحص التنبيهات للمهام الجديدة
                if st.session_state.last_seen_task_id != 0 and max_id > st.session_state.last_seen_task_id:
                    new_task = next(t for t in all_tasks if t['id'] == max_id)
                    st.toast(f"🔔 مهمة جديدة: '{new_task['title']}' موجهة إلى {new_task['assigned_to']}", icon="🎉")
                
                st.session_state.last_seen_task_id = max_id

                # تصفية المهام لعرض "قيد التنفيذ" فقط في الواجهة الرئيسية
                active_tasks = [t for t in all_tasks if t['status'] == "قيد التنفيذ"]

                if active_tasks:
                    for task in active_tasks:
                        col_id, col_title, col_assignee, col_date, col_status, col_action = st.columns([1, 3, 2, 2, 2, 2])
                        
                        utc_dt = datetime.fromisoformat(task['created_at'].replace('Z', '+00:00'))
                        gmt3_dt = utc_dt + timedelta(hours=3)
                        formatted_date = gmt3_dt.strftime("%Y-%m-%d %H:%M")

                        col_id.write(f"#{task['id']}")
                        col_title.write(task['title'])
                        col_assignee.write(f"👤 {task['assigned_to']}")
                        col_date.write(f"🕒 {formatted_date}")
                        col_status.warning(task['status'])
                        
                        # زر تحويل المهمة لمكتملة وأرشفتها فوراً
                        if col_action.button("✅ إكمال وأرشفة", key=f"btn_{task['id']}"):
                            supabase.table("tasks").update({"status": "مكتملة"}).eq("id", task['id']).execute()
                            st.success("تم نقل المهمة إلى أرشيف قاعدة البيانات.")
                            st.rerun()
                else:
                    st.info("لا توجد مهام نشطة حالياً. جميع المهام مكتملة ومؤرشفة.")
            else:
                st.info("لا توجد مهام حالية.")
                
        except Exception as e:
            st.error(f"حدث خطأ أثناء جلب المهام: {e}")

    # === العرض 2: أرشيف قاعدة البيانات (يعرض الجميع مع إمكانية إلغاء الأرشفة) ===
    else:
        st.subheader("🗄️ قاعدة البيانات الكاملة (جميع المهمات)")
        
        try:
            response = supabase.table("tasks").select("*").order("id", desc=True).execute()
            all_tasks = response.data

            if all_tasks:
                col_search, col_filter = st.columns([3, 1])
                with col_search:
                    search_query = st.text_input("🔍 بحث في عنوان المهمة...", "")
                with col_filter:
                    status_filter = st.selectbox("تصفية حسب الحالة", ["الكل", "قيد التنفيذ", "مكتملة"])

                filtered_tasks = []
                for t in all_tasks:
                    matches_search = search_query.lower() in t['title'].lower()
                    matches_status = (status_filter == "الكل") or (t['status'] == status_filter)
                    if matches_search and matches_status:
                        filtered_tasks.append(t)

                table_data = []
                for t in filtered_tasks:
                    utc_dt = datetime.fromisoformat(t['created_at'].replace('Z', '+00:00'))
                    gmt3_dt = utc_dt + timedelta(hours=3)
                    
                    table_data.append({
                        "رقم المهمة": t['id'],
                        "العنوان": t['title'],
                        "المسؤول": t['assigned_to'],
                        "تاريخ ووقت الإنشاء (GMT+3)": gmt3_dt.strftime("%Y-%m-%d %H:%M:%S"),
                        "الحالة": t['status']
                    })

                st.dataframe(table_data, use_container_width=True)
                st.caption(f"إجمالي المهام المعروضة: {len(table_data)}")
            else:
                st.info("قاعدة البيانات فارغة حالياً.")
                
        except Exception as e:
            st.error(f"حدث خطأ أثناء تحميل أرشيف قاعدة البيانات: {e}")
