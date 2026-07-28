import streamlit as st
from supabase import create_client, Client
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh

# 1. Page Configuration
st.set_page_config(page_title="Task Management System", page_icon="📋", layout="wide")

# 2. CSS لإخفاء الشريط العلوي، وتوسيط العنوان، وإخفاء أداة Streamlit
hide_and_center_style = """
    <style>
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    
    [data-testid="stDecoration"] {visibility: hidden;}
    div[class*="viewerBadge"] {visibility: hidden;}
    
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 0rem !important;
    }
    
    .centered-title {
        text-align: center;
        margin-bottom: 20px;
    }
    </style>
"""
st.markdown(hide_and_center_style, unsafe_allow_html=True)

# 3. Auto Refresh (Every 5 seconds)
st_autorefresh(interval=5000, key="datarefresh")

# 4. Retrieve Connection Secrets
SUPABASE_URL = st.secrets.get("SUPABASE_URL", "")
SUPABASE_KEY = st.secrets.get("SUPABASE_KEY", "")

if not SUPABASE_URL or not SUPABASE_KEY:
    st.error("⚠️ Please make sure to add SUPABASE_URL and SUPABASE_KEY in Secrets.")
    st.stop()

@st.cache_resource
def init_supabase() -> Client:
    return create_client(SUPABASE_URL, SUPABASE_KEY)

try:
    supabase = init_supabase()
except Exception as e:
    st.error(f"Database connection error: {e}")
    st.stop()

# 5. Initial Users List
INITIAL_USERS = {
    "Fadi": "Fadi@1983",  # Admin
    "Hamza": "pass123", # Employee 1
    "Edwan": "pass123", # Employee 2
    "Talal": "pass123", # Employee 3
    "Momen": "pass123",  # Employee 4
    "Omar": "pass123" , # Employee 5
}

ADMIN_USER = "Fadi"

# 6. Session State Management
if "user_passwords" not in st.session_state:
    st.session_state.user_passwords = INITIAL_USERS.copy()
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "username" not in st.session_state:
    st.session_state.username = ""
if "last_seen_task_id" not in st.session_state:
    st.session_state.last_seen_task_id = 0
if "view_mode" not in st.session_state:
    st.session_state.view_mode = "main"
if "show_change_pass" not in st.session_state:
    st.session_state.show_change_pass = False

EMPLOYEES_ONLY = [u for u in st.session_state.user_passwords.keys() if u != ADMIN_USER]

# --- Login Screen ---
if not st.session_state.authenticated:
    col_img1, col_img2, col_img3 = st.columns([1, 1, 1])
    with col_img2:
        try:
            st.image("logo.png", width=120)
        except:
            pass

    st.markdown("<h1 class='centered-title'>Standardization & Evaluation Division</h1>", unsafe_allow_html=True)
    
    with st.form("login_form"):
        username_input = st.text_input("Username")
        password_input = st.text_input("Password", type="password")
        submit = st.form_submit_button("Login")
        
        if submit:
            users_db = st.session_state.user_passwords
            if username_input in users_db and users_db[username_input] == password_input:
                st.session_state.authenticated = True
                st.session_state.username = username_input
                st.rerun()
            else:
                st.error("Invalid username or password.")

# --- Main Dashboard / Archive View ---
else:
    is_admin = st.session_state.username == ADMIN_USER
    current_user = st.session_state.username

    role_label = " (Admin)" if is_admin else ""
    st.markdown(f"<h1 class='centered-title'>📋 Task Board | Welcome, {current_user}{role_label}</h1>", unsafe_allow_html=True)

    col_pass, col_nav, col_logout = st.columns([1, 1, 1])
    
    with col_pass:
        if st.button("🔑 Change Password", use_container_width=True):
            st.session_state.show_change_pass = not st.session_state.show_change_pass

    with col_nav:
        if is_admin:
            if st.session_state.view_mode == "main":
                if st.button("🗄️ Database Archive", use_container_width=True):
                    st.session_state.view_mode = "archive"
                    st.rerun()
            else:
                if st.button("🏠 Back to Main Board", use_container_width=True):
                    st.session_state.view_mode = "main"
                    st.rerun()

    with col_logout:
        if st.button("Logout", use_container_width=True):
            st.session_state.authenticated = False
            st.session_state.username = ""
            st.session_state.view_mode = "main"
            st.session_state.show_change_pass = False
            st.rerun()

    # --- نافذة تغيير كلمة السر ---
    if st.session_state.show_change_pass:
        with st.expander("🔑 Change Your Password", expanded=True):
            with st.form("change_pass_form"):
                current_p = st.text_input("Current Password", type="password")
                new_p = st.text_input("New Password", type="password")
                confirm_p = st.text_input("Confirm New Password", type="password")
                pass_submit = st.form_submit_button("Update Password")
                
                if pass_submit:
                    actual_p = st.session_state.user_passwords.get(current_user, "")
                    if current_p != actual_p:
                        st.error("Current password is incorrect.")
                    elif not new_p.strip():
                        st.warning("New password cannot be empty.")
                    elif new_p != confirm_p:
                        st.error("New passwords do not match.")
                    else:
                        st.session_state.user_passwords[current_user] = new_p
                        st.success("Password updated successfully!")
                        st.session_state.show_change_pass = False

    st.divider()

    # --- لوحة التعليمات الثابتة (تظهر لجميع المستخدمين بشكل نقاط تحت بعض) ---
    with st.expander("📌 التعليمات والتوجهـــــات الثابتة (اضغط للعرض/الإخفاء)", expanded=False):
        st.markdown("""
        * **متابعة المهام:** يجب على جميع الموظفين مراجعة المهام النشطة بانتظام وإنجازها بالسرعة الممكنة.
        * **المهام العامة:** المهام غير المخصصة لموظف معين تعتبر عامة، ويمكن لأي زميل المبادرة بإنجازها.
        * **التحديث التلقائي:** يتم تحديث الصفحة وعرض المهام الجديدة تلقائياً كل 5 ثوانٍ.
        * **السرية والأمان:** يرجى عدم مشاركة بيانات الدخول وتغيير كلمة السر الشخصية بشكل دوري.
        """)

    st.divider()

    if not is_admin and st.session_state.view_mode == "archive":
        st.session_state.view_mode = "main"
        st.rerun()

    # === View 1: Main Active Tasks View ===
    if st.session_state.view_mode == "main":
        if is_admin:
            st.subheader("➕ Add New Task")
            with st.form("add_task_form", clear_on_submit=True):
                task_title = st.text_input("Task Title")
                # إضافة خيار "عام (بدون تخصيص)" بجانب أسماء الموظفين
                assigned_user = st.selectbox("Assign To", ["عام (بدون تخصيص)"] + EMPLOYEES_ONLY)
                add_submit = st.form_submit_button("Add Task")
                
                if add_submit:
                    if task_title.strip():
                        supabase.table("tasks").insert({
                            "title": task_title,
                            "assigned_to": assigned_user,
                            "status": "In Progress"
                        }).execute()
                        st.success("Task added successfully!")
                        st.rerun()
                    else:
                        st.warning("Please enter a task title.")

            st.divider()

        st.subheader("📌 Active Tasks (In Progress)")
        
        try:
            response = supabase.table("tasks").select("*").order("id", desc=True).execute()
            all_tasks = response.data

            if all_tasks:
                max_id = max(task['id'] for task in all_tasks)
                
                if st.session_state.last_seen_task_id != 0 and max_id > st.session_state.last_seen_task_id:
                    new_task = next(t for t in all_tasks if t['id'] == max_id)
                    st.toast(f"🔔 New task: '{new_task['title']}' assigned to {new_task['assigned_to']}", icon="🎉")
                
                st.session_state.last_seen_task_id = max_id

                emp_filter = st.selectbox("Filter Active Tasks by Assigned Employee", ["All", "عام (بدون تخصيص)"] + EMPLOYEES_ONLY)

                active_tasks = []
                for t in all_tasks:
                    if t['status'] in ["قيد التنفيذ", "In Progress"]:
                        if emp_filter == "All" or t['assigned_to'] == emp_filter:
                            active_tasks.append(t)

                if active_tasks:
                    for task in active_tasks:
                        col_id, col_title, col_assignee, col_date, col_status, col_action = st.columns([1, 3, 2, 2, 2, 2])
                        
                        utc_dt = datetime.fromisoformat(task['created_at'].replace('Z', '+00:00'))
                        gmt3_dt = utc_dt + timedelta(hours=3)
                        formatted_date = gmt3_dt.strftime("%Y-%m-%d %H:%M")

                        col_id.write(f"#{task['id']}")
                        col_title.write(task['title'])
                        
                        # تمييز شكل العرض للمهام العامة غير المخصصة
                        assignee_display = task['assigned_to']
                        if assignee_display == "عام (بدون تخصيص)":
                            col_assignee.markdown("🌐 **مهمة عامة**")
                        else:
                            col_assignee.write(f"👤 {assignee_display}")
                            
                        col_date.write(f"🕒 {formatted_date}")
                        col_status.warning("In Progress")
                        
                        if col_action.button("✅ Complete & Archive", key=f"btn_comp_{task['id']}"):
                            now_utc = datetime.utcnow().isoformat()
                            supabase.table("tasks").update({
                                "status": "Completed",
                                "completed_by": current_user,
                                "completed_at": now_utc
                            }).eq("id", task['id']).execute()
                            st.success(f"Task completed by {current_user} and archived.")
                            st.rerun()
                else:
                    st.info("No active tasks found.")
            else:
                st.info("No tasks found.")
                
        except Exception as e:
            st.error(f"Error fetching tasks: {e}")

    # === View 2: Full Database Archive View (Admin Only) ===
    elif is_admin and st.session_state.view_mode == "archive":
        st.subheader("🗄️ Database Archive (Admin View)")
        
        try:
            response = supabase.table("tasks").select("*").order("id", desc=True).execute()
            all_tasks = response.data

            if all_tasks:
                col_search, col_status_f, col_emp_f = st.columns([2, 1, 1])
                with col_search:
                    search_query = st.text_input("🔍 Search task title...", "")
                with col_status_f:
                    status_filter = st.selectbox("Filter by Status", ["All", "In Progress", "Completed"])
                with col_emp_f:
                    emp_filter = st.selectbox("Filter by Assigned Employee", ["All", "عام (بدون تخصيص)"] + EMPLOYEES_ONLY)

                filtered_tasks = []
                for t in all_tasks:
                    if emp_filter != "All" and t['assigned_to'] != emp_filter:
                        continue

                    matches_search = search_query.lower() in t['title'].lower()
                    task_status = "Completed" if t['status'] in ["مكتملة", "Completed"] else "In Progress"
                    matches_status = (status_filter == "All") or (task_status == status_filter)
                    
                    if matches_search and matches_status:
                        t_copy = dict(t)
                        t_copy['normalized_status'] = task_status
                        filtered_tasks.append(t_copy)

                if filtered_tasks:
                    for t in filtered_tasks:
                        col_id, col_title, col_assignee, col_completed_info, col_status, col_act1, col_act2 = st.columns([1, 3, 2, 3, 2, 2, 2])

                        utc_dt = datetime.fromisoformat(t['created_at'].replace('Z', '+00:00'))
                        gmt3_dt = utc_dt + timedelta(hours=3)
                        created_date = gmt3_dt.strftime("%Y-%m-%d %H:%M")

                        col_id.write(f"#{t['id']}")
                        col_title.write(t['title'])
                        col_assignee.write(f"👤 Assigned: {t['assigned_to']}\n🕒 {created_date}")
                        
                        if t.get('completed_by'):
                            comp_utc = datetime.fromisoformat(t['completed_at'].replace('Z', '+00:00'))
                            comp_gmt3 = comp_utc + timedelta(hours=3)
                            completed_date_str = comp_gmt3.strftime("%Y-%m-%d %H:%M")
                            col_completed_info.write(f"✅ By: **{t['completed_by']}**\n🕒 {completed_date_str}")
                        else:
                            col_completed_info.write("—")

                        if t['normalized_status'] == "Completed":
                            col_status.success("Completed")
                            if col_act1.button("🔄 Reopen", key=f"btn_reopen_{t['id']}"):
                                supabase.table("tasks").update({
                                    "status": "In Progress",
                                    "completed_by": None,
                                    "completed_at": None
                                }).eq("id", t['id']).execute()
                                st.success("Task reopened.")
                                st.rerun()
                        else:
                            col_status.warning("In Progress")

                        if col_act2.button("🗑️ Delete", key=f"btn_del_{t['id']}"):
                            supabase.table("tasks").delete().eq("id", t['id']).execute()
                            st.warning(f"Task #{t['id']} deleted permanently.")
                            st.rerun()

                    st.caption(f"Total tasks displayed: {len(filtered_tasks)}")
                else:
                    st.info("No tasks found in archive.")
            else:
                st.info("Database is currently empty.")
                
        except Exception as e:
            st.error(f"Error loading database archive: {e}")
