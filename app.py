import streamlit as st
from supabase import create_client, Client
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh
import bcrypt

# 1. Page Configuration
st.set_page_config(page_title="Task Management System", page_icon="📋", layout="wide")

# 2. CSS لإخفاء الشريط العلوي وتوسيط العنوان وجعل واجهة النظام من اليمين لليسار (RTL)
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
        direction: rtl;
        text-align: right;
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

    input, textarea, div[data-baseweb="select"] {
        direction: rtl !important;
        text-align: right !important;
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

# دالة التحقق من كلمة المرور المشفرة أو النصية (لضمان التوافق المؤقت)
def verify_password(stored_password, provided_password):
    if stored_password.startswith("$2b$") or stored_password.startswith("$2a$"):
        try:
            return bcrypt.checkpw(provided_password.encode('utf-8'), stored_password.encode('utf-8'))
        except:
            return False
    return stored_password == provided_password

# جلب المستخدمين من قاعدة البيانات وترتيبهم أبجدياً
def get_users_from_db():
    try:
        res = supabase.table("users").select("*").execute()
        users_dict = {}
        if res.data:
            sorted_rows = sorted(res.data, key=lambda x: x["username"].strip().lower())
            for row in sorted_rows:
                users_dict[row["username"].strip()] = row["password"]
        return users_dict
    except:
        return {"Fadi": "Fadi@1983"}

# 5. Session State Management
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "username" not in st.session_state:
    st.session_state.username = ""

# التحقق الأمني من الوجود في قاعدة البيانات لمنع التلاعب برابط الوجود
current_users_db = get_users_from_db()
query_params = st.query_params
if "logged_user" in query_params and not st.session_state.authenticated:
    param_user = query_params["logged_user"]
    if param_user in current_users_db:
        st.session_state.authenticated = True
        st.session_state.username = param_user

if "last_seen_task_id" not in st.session_state:
    st.session_state.last_seen_task_id = 0
if "view_mode" not in st.session_state:
    st.session_state.view_mode = "main"
if "show_change_pass" not in st.session_state:
    st.session_state.show_change_pass = False
if "show_add_user" not in st.session_state:
    st.session_state.show_add_user = False
if "editing_task_id" not in st.session_state:
    st.session_state.editing_task_id = None

EMPLOYEES_ONLY = [u for u in current_users_db.keys() if u != ADMIN_USER]

# --- Login Screen ---
if not st.session_state.get("authenticated", False):
    col_l, col_m, col_r = st.columns([1, 2, 1])
    with col_m:
        try:
            st.image("logo.png", width=130)
        except:
            st.warning("⚠️ Logo image 'logo.png' not found.")

    st.markdown("<h1 class='centered-title'>Stan & Eval Division</h1>", unsafe_allow_html=True)
    
    with st.form("login_form"):
        username_input = st.text_input("اسم المستخدم (Username)")
        password_input = st.text_input("كلمة المرور (Password)", type="password")
        submit = st.form_submit_button("تسجيل الدخول (Login)")
        
        if submit:
            clean_user = username_input.strip()
            if clean_user in current_users_db and verify_password(current_users_db[clean_user], password_input):
                st.session_state.authenticated = True
                st.session_state.username = clean_user
                st.query_params["logged_user"] = clean_user
                st.rerun()
            else:
                st.error("اسم المستخدم أو كلمة المرور غير صحيحة.")

# --- Main Dashboard / Archive View ---
else:
    is_admin = st.session_state.username == ADMIN_USER
    current_user = st.session_state.username

    role_label = " (مشرف - Admin)" if is_admin else ""
    st.markdown(f"<h1 class='centered-title'>📋 مرحباً {current_user}{role_label}</h1>", unsafe_allow_html=True)

    if is_admin:
        col_pass, col_adduser, col_nav, col_logout = st.columns([1, 1, 1, 1])
    else:
        col_pass, col_nav, col_logout = st.columns([1, 1, 1])
    
    with col_pass:
        if st.button("🔑 تغيير كلمة المرور", use_container_width=True):
            st.session_state.show_change_pass = not st.session_state.show_change_pass
            st.session_state.show_add_user = False

    if is_admin:
        with col_adduser:
            if st.button("👥 إدارة الموظفين", use_container_width=True):
                st.session_state.show_add_user = not st.session_state.show_add_user
                st.session_state.show_change_pass = False

    with col_nav:
        if is_admin:
            if st.session_state.view_mode == "main":
                if st.button("🗄️ أرشيف قاعدة البيانات", use_container_width=True):
                    st.session_state.view_mode = "archive"
                    st.rerun()
            else:
                if st.button("🏠 العودة للوحة الرئيسية", use_container_width=True):
                    st.session_state.view_mode = "main"
                    st.rerun()

    with col_logout:
        if st.button("تسجيل الخروج", use_container_width=True):
            st.session_state.authenticated = False
            st.session_state.username = ""
            if "logged_user" in st.query_params:
                del st.query_params["logged_user"]
            st.session_state.view_mode = "main"
            st.session_state.show_change_pass = False
            st.session_state.show_add_user = False
            st.rerun()

    # --- نافذة إدارة الموظفين (مع تشفير كلمات المرور أمنياً) ---
    if is_admin and st.session_state.show_add_user:
        with st.expander("👥 إدارة الموظفين (إضافة / حذف / عرض كلمات السر)", expanded=True):
            st.subheader("➕ إضافة موظف جديد")
            with st.form("add_user_form"):
                new_username = st.text_input("اسم المستخدم الجديد")
                new_password = st.text_input("كلمة المرور", type="password")
                add_user_submit = st.form_submit_button("إنشاء المستخدم")
                
                if add_user_submit:
                    clean_name = new_username.strip()
                    if not clean_name:
                        st.warning("اسم المستخدم لا يمكن أن يكون فارغاً.")
                    elif clean_name in current_users_db:
                        st.error("المستخدم موجود مسبقاً.")
                    elif not new_password.strip():
                        st.warning("كلمة المرور لا يمكن أن تكون فارغة.")
                    else:
                        try:
                            # تشفير كلمة المرور بأمان تام باستخدام bcrypt
                            hashed_pw = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                            supabase.table("users").insert({"username": clean_name, "password": hashed_pw}).execute()
                            st.success(f"تم إضافة المستخدم '{clean_name}' بنجاح!")
                            st.rerun()
                        except Exception as err:
                            st.error(f"خطأ في إضافة المستخدم: {err}")

            st.divider()
            st.subheader("🔑 عرض المستخدمين المسجلين")
            for uname in current_users_db.keys():
                st.text(f"المستخدم: {uname}")

            st.divider()
            st.subheader("🗑️ قائمة الموظفين الحاليين")
            for emp in EMPLOYEES_ONLY:
                c_name, c_btn = st.columns([3, 1])
                c_name.write(f"👤 **{emp}**")
                if c_btn.button(f"🗑️ حذف", key=f"del_user_{emp}"):
                    try:
                        supabase.table("users").delete().eq("username", emp).execute()
                        st.warning(f"تم حذف الموظف '{emp}' بنجاح!")
                        st.rerun()
                    except Exception as err:
                        st.error(f"خطأ في حذف المستخدم: {err}")

    # --- نافذة تغيير كلمة السر ---
    if st.session_state.show_change_pass:
        with st.expander("🔑 تغيير كلمة المرور الخاصة بك", expanded=True):
            with st.form("change_pass_form"):
                current_p = st.text_input("كلمة المرور الحالية", type="password")
                new_p = st.text_input("كلمة المرور الجديدة", type="password")
                confirm_p = st.text_input("تأكيد كلمة المرور الجديدة", type="password")
                pass_submit = st.form_submit_button("تحديث كلمة المرور")
                
                if pass_submit:
                    actual_p = current_users_db.get(current_user, "")
                    if not verify_password(actual_p, current_p):
                        st.error("كلمة المرور الحالية غير صحيحة.")
                    elif not new_p.strip():
                        st.warning("كلمة المرور الجديدة لا يمكن أن تكون فارغة.")
                    elif new_p != confirm_p:
                        st.error("كلمتا المرور غير متطابقتين.")
                    else:
                        try:
                            hashed_new_pw = bcrypt.hashpw(new_p.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                            supabase.table("users").update({"password": hashed_new_pw}).eq("username", current_user).execute()
                            st.success("تم تحديث كلمة المرور بنجاح!")
                            st.session_state.show_change_pass = False
                            st.rerun()
                        except Exception as err:
                            st.error(f"خطأ في تحديث كلمة المرور: {err}")

    st.divider()

    # --- لوحة الأوامر والتعليمات الثابتة ---
    try:
        settings_res = supabase.table("settings").select("*").eq("key", "instructions").execute()
        current_instructions = ""
        if settings_res.data:
            current_instructions = settings_res.data[0]["value"]
        else:
            current_instructions = "- متابعة المهام بانتظام.\n- يمكن لأي مستخدم إضافة أو إنجاز المهام على مرحلتين.\n- يتم تحديث الصفحة تلقائياً كل 5 ثوانٍ."
    except:
        current_instructions = "- متابعة المهام بانتظام."

    st.markdown("### 📌 الأوامر والتعليمات")
    
    if is_admin:
        with st.form("update_instructions_form"):
            updated_text = st.text_area("تعديل التعليمات:", value=current_instructions, height=100)
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
                    st.error(f"خطأ في حفظ التعليمات: {err}")
    else:
        st.info(current_instructions)

    st.divider()

    if not is_admin and st.session_state.view_mode == "archive":
        st.session_state.view_mode = "main"
        st.rerun()

    # === View 1: Main Active Tasks View ===
    if st.session_state.view_mode == "main":
        st.subheader("➕ إضافة مهمة جديدة")
        with st.form("add_task_form", clear_on_submit=True):
            task_title = st.text_input("عنوان المهمة")
            assigned_user = st.selectbox("إسناد إلى", ["عام "] + EMPLOYEES_ONLY)
            add_submit = st.form_submit_button("إضافة المهمة")
            
            if add_submit:
                if task_title.strip():
                    supabase.table("tasks").insert({
                        "title": task_title.strip(),
                        "assigned_to": assigned_user,
                        "created_by": current_user,
                        "status": "Pending"
                    }).execute()
                    st.success("تم إضافة المهمة بنجاح!")
                    st.rerun()
                else:
                    st.warning("الرجاء إدخال عنوان المهمة.")

        st.divider()

        st.subheader("📌 لوحة المهام النشطة")
        
        try:
            response = supabase.table("tasks").select("*").order("id", desc=True).execute()
            all_tasks = response.data

            if all_tasks:
                max_id = max(task['id'] for task in all_tasks)
                
                if st.session_state.last_seen_task_id != 0 and max_id > st.session_state.last_seen_task_id:
                    new_task = next(t for t in all_tasks if t['id'] == max_id)
                    st.toast(f"🔔 مهمة جديدة: '{new_task['title']}' مسندة إلى {new_task['assigned_to']}", icon="🎉")
                
                st.session_state.last_seen_task_id = max_id

                emp_filter = st.selectbox("تصفية المهام حسب الموظف", ["All", "عام "] + EMPLOYEES_ONLY)

                active_tasks = []
                for t in all_tasks:
                    task_st = t.get('status', 'Pending')
                    if task_st not in ["Completed", "مكتملة"]:
                        if emp_filter == "All" or t['assigned_to'] == emp_filter:
                            active_tasks.append(t)

                if active_tasks:
                    for task in active_tasks:
                        if is_admin:
                            col_id, col_title, col_assignee, col_date, col_status, col_edit, col_action = st.columns([1, 2.5, 1.5, 1.5, 1.5, 1, 1.5])
                        else:
                            col_id, col_title, col_assignee, col_date, col_status, col_action = st.columns([1, 3, 2, 2, 2, 2])
                        
                        utc_dt = datetime.fromisoformat(task['created_at'].replace('Z', '+00:00'))
                        gmt3_dt = utc_dt + timedelta(hours=3)
                        formatted_date = gmt3_dt.strftime("%Y-%m-%d %H:%M")

                        col_id.write(f"#{task['id']}")
                        
                        if is_admin:
                            if st.session_state.editing_task_id == task['id']:
                                with st.form(key=f"edit_form_{task['id']}"):
                                    new_title_input = st.text_input("تعديل العنوان", value=task['title'], label_visibility="collapsed")
                                    c_save, c_cancel = st.columns(2)
                                    if c_save.form_submit_button("💾 حفظ"):
                                        if new_title_input.strip():
                                            supabase.table("tasks").update({"title": new_title_input.strip()}).eq("id", task['id']).execute()
                                            st.session_state.editing_task_id = None
                                            st.success("تم التحديث!")
                                            st.rerun()
                                    if c_cancel.form_submit_button("❌ إلغاء"):
                                        st.session_state.editing_task_id = None
                                        st.rerun()
                            else:
                                col_title.write(task['title'])
                                if col_edit.button("✏️ تعديل", key=f"btn_edit_{task['id']}"):
                                    st.session_state.editing_task_id = task['id']
                                    st.rerun()
                        else:
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
                            col_status.warning(f"قيد التنفيذ\n(بواسطة: {started_by})")
                            if col_action.button("✅ إتمام المهمة", key=f"btn_comp_{task['id']}"):
                                now_utc = datetime.utcnow().isoformat()
                                supabase.table("tasks").update({
                                    "status": "Completed",
                                    "completed_by": current_user,
                                    "completed_at": now_utc
                                }).eq("id", task['id']).execute()
                                st.success(f"تم إتمام المهمة بواسطة {current_user}.")
                                st.rerun()
                        else:
                            col_status.info("معلقة")
                            if col_action.button("⏳ البدء بالمهمة", key=f"btn_start_{task['id']}"):
                                supabase.table("tasks").update({
                                    "status": "In Progress",
                                    "started_by": current_user
                                }).eq("id", task['id']).execute()
                                st.success(f"تم بدء المهمة بواسطة {current_user}.")
                                st.rerun()
                else:
                    st.info("لا توجد مهام نشطة.")
            else:
                st.info("لا توجد مهام مسجلة.")
                
        except Exception as e:
            st.error(f"خطأ في جلب المهام: {e}")

    # === View 2: Full Database Archive View (Admin Only) ===
    elif is_admin and st.session_state.view_mode == "archive":
        st.subheader("🗄️ أرشيف قاعدة البيانات (عرض المشرف)")
        
        try:
            response = supabase.table("tasks").select("*").order("id", desc=True).execute()
            all_tasks = response.data

            if all_tasks:
                col_search, col_status_f, col_emp_f = st.columns([2, 1, 1])
                with col_search:
                    search_query = st.text_input("🔍 بحث في عنوان المهمة...", "")
                with col_status_f:
                    status_filter = st.selectbox("تصفية حسب الحالة", ["All", "Pending", "In Progress", "Completed"])
                with col_emp_f:
                    emp_filter = st.selectbox("تصفية حسب الموظف المسند إليه", ["All", "عام "] + EMPLOYEES_ONLY)

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
                        
                        creator = t.get('created_by', 'غير معروف')
                        col_assignee.write(f"👤 المسند إليه: {t['assigned_to']}\n✍️ أضيفت بواسطة: **{creator}**\n🕒 وقت الإنشاء: {created_date}")
                        
                        info_text = "—"
                        started_user = t.get('started_by')
                        completed_user = t.get('completed_by')
                        completed_at_raw = t.get('completed_at')

                        details_list = []
                        if started_user:
                            details_list.append(f"⏳ بدأت بواسطة: **{started_user}**")
                        
                        if completed_user and completed_at_raw:
                            comp_utc = datetime.fromisoformat(completed_at_raw.replace('Z', '+00:00'))
                            comp_gmt3 = comp_utc + timedelta(hours=3)
                            completed_date_str = comp_gmt3.strftime("%Y-%m-%d %H:%M")
                            details_list.append(f"✅ انتهت بواسطة: **{completed_user}**\n🕒 وقت الانتهاء: {completed_date_str}")
                        
                        if details_list:
                            info_text = "\n".join(details_list)

                        col_completed_info.markdown(info_text)

                        t_status = t.get('status', 'Pending')
                        if t_status == "Completed":
                            col_status.success("مكتملة")
                            if col_act1.button("🔄 إعادة فتح", key=f"btn_reopen_{t['id']}"):
                                supabase.table("tasks").update({
                                    "status": "Pending",
                                    "started_by": None,
                                    "completed_by": None,
                                    "completed_at": None
                                }).eq("id", t['id']).execute()
                                st.success("تم إعادة فتح المهمة.")
                                st.rerun()
                        elif t_status == "In Progress":
                            col_status.warning("قيد التنفيذ")
                            col_act1.write("—")
                        else:
                            col_status.info("معلقة")
                            col_act1.write("—")

                        if col_act2.button("🗑️ حذف", key=f"btn_del_{t['id']}"):
                            supabase.table("tasks").delete().eq("id", t['id']).execute()
                            st.warning(f"تم حذف المهمة #{t['id']} نهائياً.")
                            st.rerun()

                    st.caption(f"إجمالي المهام المعروضة: {len(filtered_tasks)}")
                else:
                    st.info("لا توجد مهام مطابقة في الأرشيف.")
            else:
                st.info("قاعدة البيانات فارغة حالياً.")
                
        except Exception as e:
            st.error(f"خطأ في تحميل أرشيف قاعدة البيانات: {e}")
