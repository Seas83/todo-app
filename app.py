import streamlit as st
from supabase import create_client, Client
from datetime import datetime, timedelta
from streamlit_autorun import autorun

# إعادة تحميل الصفحة تلقائياً كل 5000 ميلي ثانية (5 ثوانٍ)
autorun(interval=5000, key="auto_rerun")

# 1. Page Configuration
st.set_page_config(page_title="Task Management System", page_icon="📋", layout="wide")

# 2. Retrieve Connection Secrets
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

# 3. Users List
USERS = {
    "user1": "pass123",
    "user2": "pass123",
    "user3": "pass123"
}

# 4. Session State Management
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "username" not in st.session_state:
    st.session_state.username = ""
if "last_seen_task_id" not in st.session_state:
    st.session_state.last_seen_task_id = 0
if "view_mode" not in st.session_state:
    st.session_state.view_mode = "main"

# --- Login Screen ---
if not st.session_state.authenticated:
    st.title("🔐 Login - Team Workspace")
    
    with st.form("login_form"):
        username_input = st.text_input("Username")
        password_input = st.text_input("Password", type="password")
        submit = st.form_submit_button("Login")
        
        if submit:
            if username_input in USERS and USERS[username_input] == password_input:
                st.session_state.authenticated = True
                st.session_state.username = username_input
                st.rerun()
            else:
                st.error("Invalid username or password.")

# --- Main Dashboard / Archive View ---
else:
    col_user, col_nav, col_logout = st.columns([5, 3, 2])
    
    with col_user:
        st.title(f"📋 Task Board | Welcome, {st.session_state.username}")
    
    with col_nav:
        st.write("")
        if st.session_state.view_mode == "main":
            if st.button("🗄️ Database Archive"):
                st.session_state.view_mode = "archive"
                st.rerun()
        else:
            if st.button("🏠 Back to Main Board"):
                st.session_state.view_mode = "main"
                st.rerun()

    with col_logout:
        st.write("")
        if st.button("Logout"):
            st.session_state.authenticated = False
            st.session_state.username = ""
            st.session_state.view_mode = "main"
            st.rerun()

    st.divider()

    # === View 1: Main Active Tasks View ===
    if st.session_state.view_mode == "main":
        st.subheader("➕ Add New Task")
        with st.form("add_task_form", clear_on_submit=True):
            task_title = st.text_input("Task Title")
            assigned_user = st.selectbox("Assign To", list(USERS.keys()))
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
                
                # Check for new task notifications
                if st.session_state.last_seen_task_id != 0 and max_id > st.session_state.last_seen_task_id:
                    new_task = next(t for t in all_tasks if t['id'] == max_id)
                    st.toast(f"🔔 New task: '{new_task['title']}' assigned to {new_task['assigned_to']}", icon="🎉")
                
                st.session_state.last_seen_task_id = max_id

                # Filter for active tasks
                active_tasks = [t for t in all_tasks if t['status'] in ["قيد التنفيذ", "In Progress"]]

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
                        col_status.warning("In Progress")
                        
                        # --- التعديل الأساسي هنا ---
                        # التحقق هل المستخدم الحالي هو نفسه الشخص المخصصة له المهمة أم لا
                        if task['assigned_to'] == st.session_state.username:
                            if col_action.button("✅ Complete & Archive", key=f"btn_{task['id']}"):
                                supabase.table("tasks").update({"status": "Completed"}).eq("id", task['id']).execute()
                                st.success("Task moved to database archive.")
                                st.rerun()
                        else:
                            col_action.caption("🔒 Assigned to " + task['assigned_to'])
                else:
                    st.info("No active tasks at the moment. All tasks are completed and archived.")
            else:
                st.info("No tasks found.")
                
        except Exception as e:
            st.error(f"Error fetching tasks: {e}")

    # === View 2: Full Database Archive View ===
    else:
        st.subheader("🗄️ Full Database Archive (All Tasks)")
        
        try:
            response = supabase.table("tasks").select("*").order("id", desc=True).execute()
            all_tasks = response.data

            if all_tasks:
                col_search, col_filter = st.columns([3, 1])
                with col_search:
                    search_query = st.text_input("🔍 Search task title...", "")
                with col_filter:
                    status_filter = st.selectbox("Filter by Status", ["All", "In Progress", "Completed"])

                filtered_tasks = []
                for t in all_tasks:
                    matches_search = search_query.lower() in t['title'].lower()
                    
                    task_status = "Completed" if t['status'] in ["مكتملة", "Completed"] else "In Progress"
                    matches_status = (status_filter == "All") or (task_status == status_filter)
                    
                    if matches_search and matches_status:
                        t_copy = dict(t)
                        t_copy['normalized_status'] = task_status
                        filtered_tasks.append(t_copy)

                table_data = []
                for t in filtered_tasks:
                    utc_dt = datetime.fromisoformat(t['created_at'].replace('Z', '+00:00'))
                    gmt3_dt = utc_dt + timedelta(hours=3)
                    
                    table_data.append({
                        "Task ID": t['id'],
                        "Title": t['title'],
                        "Assigned To": t['assigned_to'],
                        "Created At (GMT+3)": gmt3_dt.strftime("%Y-%m-%d %H:%M:%S"),
                        "Status": t['normalized_status']
                    })

                st.dataframe(table_data, use_container_width=True)
                st.caption(f"Total tasks displayed: {len(table_data)}")
            else:
                st.info("Database is currently empty.")
                
        except Exception as e:
            st.error(f"Error loading database archive: {e}")
