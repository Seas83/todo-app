import streamlit as st
from supabase import create_client, Client

# إعداد الصفحة
st.set_page_config(page_title="نظام إدارة المهام", page_icon="📋", layout="wide")

# جلب البيانات من Secrets
SUPABASE_URL = st.secrets.get("SUPABASE_URL", "")
SUPABASE_KEY = st.secrets.get("SUPABASE_KEY", "")

# التحقق من وجود البيانات
if not SUPABASE_URL or not SUPABASE_KEY:
    st.error("⚠️ يرجى التأكد من إضافة SUPABASE_URL و SUPABASE_KEY في إعدادات Secrets.")
    st.stop()

@st.cache_resource
def init_supabase() -> Client:
    return create_client(SUPABASE_URL, SUPABASE_KEY)

try:
    supabase = init_supabase()
except Exception as e:
    st.error(f"خطأ في الاتصال بقاعدة البيانات: {e}")
    st.stop()

# قائمة المستخدمين
USERS = {
    "user1": "pass123",
    "user2": "pass123",
    "user3": "pass123"
}

# إدارة الجلسة
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "username" not in st.session_state:
    st.session_state.username = ""

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

# --- الشاشة الرئيسية ---
else:
    col_user, col_logout = st.columns([8, 2])
    with col_user:
        st.title(f"📋 لوحة المهام | أهلاً {st.session_state.username}")
    with col_logout:
        if st.button("تسجيل الخروج"):
            st.session_state.authenticated = False
            st.session_state.username = ""
            st.rerun()

    st.divider()

    # إضافة مهمة
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

    # عرض المهام
    st.subheader("📌 قائمة المهام الحالية")
    
    try:
        response = supabase.table("tasks").select("*").order("id", desc=True).execute()
        tasks = response.data

        if not tasks:
            st.info("لا توجد مهام حالية.")
        else:
            for task in tasks:
                col_id, col_title, col_assignee, col_status, col_action = st.columns([1, 4, 2, 2, 2])
                
                col_id.write(f"#{task['id']}")
                col_title.write(task['title'])
                col_assignee.write(f"👤 {task['assigned_to']}")
                
                if task['status'] == "مكتملة":
                    col_status.success(task['status'])
                else:
                    col_status.warning(task['status'])
                    
                new_status = "مكتملة" if task['status'] == "قيد التنفيذ" else "قيد التنفيذ"
                btn_label = "تعليم كمكتملة" if task['status'] == "قيد التنفيذ" else "إعادة فتح"
                
                if col_action.button(btn_label, key=f"btn_{task['id']}"):
                    supabase.table("tasks").update({"status": new_status}).eq("id", task['id']).execute()
                    st.rerun()
    except Exception as e:
        st.error(f"حدث خطأ أثناء جلب المهام: {e}")
