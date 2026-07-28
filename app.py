import streamlit as st
from supabase import create_client, Client
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh

# 1. Page Configuration
st.set_page_config(page_title="Task Management System", page_icon="📋", layout="wide")

# 2. CSS لإخفاء الشريط العلوي وتوسيط العنوان والشعار
hide_and_center_style = """
    <style>
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    
    [data-testid="stDecoration"] {display: none !important; visibility: hidden !important;}
    div[class*="viewerBadge"] {display: none !important; visibility: hidden !important;}
    #stStatusWidget {display: none !important; visibility: hidden !important;}
    .stAppToolbar {display: none !important; visibility: hidden !important;}
    footer[data-testid="stFooter"] {display: none !important; visibility: hidden !important;}
    
    a[href*="streamlit.cloud"] {display: none !important;}
    .builtWith {display: none !important;}
    
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 0rem !important;
    }
    
    .centered-title {
        text-align: center;
        margin-bottom: 20px;
    }

    div[data-testid="column"] {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
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

ADMIN_USER = "Fadi"

# جلب المستخدمين من قاعدة البيانات مباشرة
def get_users_from_db():
    try:
        res = supabase.table("users").select("*").execute()
        users_dict = {}
        if res.data:
            for row in res.data:
                users_dict[row["username"]] = row["password"]
        return users_dict
    except:
        return {"Fadi": "Fadi@1983"}

# 5. Session State Management
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
if "show_add_user" not in st.session_state:
    st.session_state.show_add_user = False

current_users_db = get_users_from_db()
EMPLOYEES_ONLY = [u for u in current_users_db.keys() if u != ADMIN_USER]

# --- Login Screen ---
if not st.session_state.authenticated:
    col_l, col_m, col_r = st.columns([1, 2, 1])
    with col_m:
        try:
            st.image("logo.png", width=130)
        except:
            st.warning("⚠️ Logo image 'logo.png' not found.")

    st.markdown("<h1 class='centered-title'>Stan & Eval Division</h1>", unsafe_allow_html=True)
    
    with st.form("login_form"):
        username_input = st.text_input("Username")
        password_input = st.text_input("Password", type="password")
        submit = st.form_submit_button("Login")
        
        if submit:
            if username_input in current_users_db and current_users_db[username_input] == password_input:
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
    st.markdown(f"<h1 class='centered-title'>📋Welcome {current_user}{role_label}</h1>", unsafe_allow_html=True)

    if is_admin:
        col_pass, col_adduser, col_nav, col_logout = st.columns([1, 1, 1, 1])
    else:
        col_pass, col_nav, col_logout = st.columns([1, 1, 1])
    
    with col_pass:
        if st.button("🔑 Change Password", use_container_width=True):
            st.session_state.show_change_pass = not st.session_state.show_change_pass
            st.session_state.show_add_user = False

    if is_admin:
        with col_adduser:
            if st.button("👥 Manage Employees", use_container_width=True):
                st.session_state.show_add_user = not st.session_state.show_add_user
                st.session_state.show_change_pass = False

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
            st.session_state.show_add_user = False
            st.rerun()

    # --- نافذة إدارة الموظفين (إضافة وحذف موظف) ---
    if is_admin and st.session_state.show_add_user:
        with st.expander("👥 Employee Management (Add / Delete)", expanded=True):
            st.subheader("➕ Add New Employee")
            with st.form("add_user_form"):
                new_username = st.text_input("New Username")
                new_password = st.text_input("Password", type="password")
                add_user_submit = st.form_submit_button("Create User")
                
                if add_user_submit:
                    clean_name = new_username.strip()
                    if not clean_name:
                        st.warning("Username cannot be empty.")
                    elif clean_name in current_users_db:
                        st.error("User already exists.")
                    elif not new_password.strip():
                        st.warning("Password cannot be empty.")
                    else:
                        try:
                            supabase.table("users").insert({"username": clean_name, "password": new_password}).execute()
                            st.success(f"User '{clean_name}' added successfully to database!")
                            st.rerun()
                        except Exception as err:
                            st.error(f"Error adding user: {err}")

            st.divider()
            st.subheader("🗑️ Existing Employees List")
            for emp in EMPLOYEES_ONLY:
                c_name, c_btn = st.columns([3, 1])
                c_name.write(f"👤 **{emp}**")
                if c_btn.button(f"🗑️ Delete", key=f"del_user_{emp}"):
                    try:
                        supabase.table("users").delete().eq("username", emp).execute()
                        st.warning(f"Employee '{emp}' deleted successfully!")
                        st.rerun()
                    except Exception as err:
                        st.error(f"Error deleting user: {err}")

    # --- نافذة تغيير كلمة السر ---
    if st.session_state.show_change_pass:
        with st.expander("🔑 Change Your Password", expanded=True):
            with st.form("change_pass_form"):
                current_p = st.text_input("Current Password", type="password")
                new_p = st.text_input("New Password", type="password")
                confirm_p = st.text_input("Confirm New Password", type="password")
                pass_submit = st.form_submit_button("Update Password")
                
                if pass_submit:
                    actual_p = current_users_db.get(current_user, "")
                    if current_p != actual_p:
                        st.error("Current password is incorrect.")
                    elif not new_p.strip():
                        st.warning("New password cannot be empty.")
                    elif new_p != confirm_p:
                        st.error("New passwords do not match.")
                    else:
                        try:
                            supabase.table("users").update({"password": new_p}).eq("username", current_user).execute()
                            st.success("Password updated successfully in database!")
                            st.session_state.show_change_pass = False
                            st.rerun()
                        except Exception as err:
                            st.error(f"Error updating password: {err}")

    st.divider()

    # --- إدارة وعرض التعليمات الثابتة (من قاعدة البيانات) ---
    try:
        settings_res = supabase.table("settings").select("*").eq("key", "instructions").execute()
        current_instructions = ""
        if settings_res.data:
            current_instructions = settings_res.data[0]["value"]
        else:
            current_instructions = "- متابعة المهام بانتظام.\n- المهام العامة يمكن لأي موظف إنجازها على مرحلتين (بدء ثم إتمام).\n- يتم تحديث الصفحة تلقائياً كل 5 ثوانٍ."
    except:
        current_instructions = "- متابعة المهام بانتظام.\n- المهام العامة يمكن لأي موظف إنجازها."

    with st.expander("📌الأوامر والتعليمات ", expanded=False):
        if is_admin:
            with st.form("update_instructions_form"):
                updated_text = st.text_area("تعديل التعليمات :", value=current_instructions, height=120)
                update_btn = st.form_submit_button("حفظ وتحديث التعليمات")
                if update_btn:
                    try:
                        check_exist = supabase.table("settings").select("*").eq("key", "instructions").execute()
                        if check_exist.data:
                            supabase.table("settings").update({"value": updated_text}).eq("key", "instructions").execute()
                        else:
                            supabase.table("settings").insert({"key": "instructions", "value": updated_text}).execute()
                        st.success("تم تحديث التعليمات بنجاح!")
                        st.rerun()
                    except Exception as err:
                        st.error(f"خطأ في حفظ التعليمات (تأكد من إنشاء جدول settings في Supabase): {err}")
            st.divider()
        
        st.markdown(current_instructions)

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
                assigned_user = st.selectbox("Assign To", ["عام "] + EMPLOYEES_ONLY)
                add_submit = st.form_submit_button("Add Task")
                
                if add_submit:
                    if task_title.strip():
                        supabase.table("tasks").insert({
                            "title": task_title,
                            "assigned_to": assigned_user,
                            "status": "Pending"
                        }).execute()
                        st.success("Task added successfully!")
                        st.rerun()
                    else:
                        st.warning("Please enter a task title.")

            st.divider()

        st.subheader("📌 Active Tasks Board")
        
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
                    task_st = t.get('status', 'Pending')
                    if task_st not in ["Completed", "مكتملة"]:
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
                        
                        assignee_display = task['assigned_to']
                        if assignee_display == "عام ":
                            col_assignee.markdown("🌐 **مهمة عامة**")
                        else:
                            col_assignee.write(f"👤 {assignee_display}")
                            
                        col_date.write(f"🕒 {formatted_date}")
                        
                        current_status = task.get('status', 'Pending')
                        started_by = task.get('started_by')

                        if current_status in ["In Progress", "قيد التنفيذ"]:
                            col_status.warning(f"In Progress\n(By: {started_by})")
                            if col_action.button("✅ Complete Task", key=f"btn_comp_{task['id']}"):
                                now_utc = datetime.utcnow().isoformat()
                                supabase.table("tasks").update({
                                    "status": "Completed",
                                    "completed_by": current_user,
                                    "completed_at": now_utc
                                }).eq("id", task['id']).execute()
                                st.success(f"Task completed by {current_user} and archived.")
                                st.rerun()
                        else:
                            col_status.info("Pending")
                            if col_action.button("⏳ Start Task", key=f"btn_start_{task['id']}"):
                                supabase.table("tasks").update({
                                    "status": "In Progress",
                                    "started_by": current_user
                                }).eq("id", task['id']).execute()
                                st.success(f"Task started by {current_user}.")
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
                    status_filter = st.selectbox("Filter by Status", ["All", "Pending", "In Progress", "Completed"])
                with col_emp_f:
                    emp_filter = st.selectbox("Filter by Assigned Employee", ["All", "عام (بدون تخصيص)"] + EMPLOYEES_ONLY)

                filtered_tasks = []
                for t in all_tasks:
                    if emp_filter != "All" and t['assigned_to'] != emp_filter:
                        continue

                    matches_search = search_query.lower() in t['title'].lower()
                    t_status = t.get('status', 'Pending')
                    
                    matches_status = (status_filter == "All") or (t_status == status_filter)
                    
                    if matches_search and matches_status:
                        filtered_tasks.append(t)

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
                        elif t.get('started_by'):
                            col_completed_info.write(f"⏳ Started by: **{t['started_by']}**")
                        else:
                            col_completed_info.write("—")

                        t_status = t.get('status', 'Pending')
                        if t_status == "Completed":
                            col_status.success("Completed")
                            if col_act1.button("🔄 Reopen", key=f"btn_reopen_{t['id']}"):
                                supabase.table("tasks").update({
                                    "status": "Pending",
                                    "started_by": None,
                                    "completed_by": None,
                                    "completed_at": None
                                }).eq("id", t['id']).execute()
                                st.success("Task reopened.")
                                st.rerun()
                        elif t_status == "In Progress":
                            col_status.warning("In Progress")
                            col_act1.write("—")
                        else:
                            col_status.info("Pending")
                            col_act1.write("—")

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
