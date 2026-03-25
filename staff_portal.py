import streamlit as st
import pandas as pd
import plotly.express as px
import requests

def show_page(supabase):
    st.markdown("<h1 class='main-header'>Staff Administration Portal</h1>", unsafe_allow_html=True)
    
    tabs = st.tabs(["📢 Pending Approvals", "📊 Department Analytics", "🏆 Leaderboard", "💬 AI Assistant"])
    
    with tabs[0]:
        st.subheader("📋 Pending Certificate Reviews")
        
        # REMOVED JOIN QUERY: Fetch certificates and students separately to avoid APIError
        try:
            res = supabase.table("certificates").select("*").eq("status", "Pending").execute()
            pending_data = res.data
            
            # Enrich with student details manually
            for cert in pending_data:
                try:
                    std_res = supabase.table("students").select("*").eq("id", cert['student_id']).execute()
                    cert['students'] = std_res.data[0] if std_res.data else {"full_name": "Unknown", "gpa": 0.0, "department": "N/A"}
                except:
                    cert['students'] = {"full_name": "Unknown", "gpa": 0.0, "department": "N/A"}
        except Exception as e:
            st.error(f"Error loading pending reviews: {e}")
            pending_data = []
        
        if pending_data:
            for cert in pending_data:
                with st.expander(f"Review: {cert['event_name']} by {cert['students']['full_name']}"):
                    col1, col2 = st.columns([1, 2])
                    with col1:
                        st.write(f"**Student:** {cert['students'].get('full_name', 'N/A')}")
                        st.write(f"**Roll No:** {cert.get('roll_number', cert['students'].get('roll_number'))}")
                        st.write(f"**Email:** {cert.get('student_email', 'N/A')}")
                        st.write(f"**Department:** {cert.get('department', cert['students'].get('department'))}")
                        st.write(f"**GPA:** {cert['students'].get('gpa', 0.0)}")
                        st.write(f"**Event Type:** {cert['event_type']}")
                        st.write(f"**Achievement Level:** {cert.get('achievement_level', 'N/A')}")
                        
                        v_status = cert.get('verification_status', 'NOT VALID CERTIFICATE')
                        status_color = "#10b981" if "VALID" in v_status and "NOT" not in v_status else "#ef4444"
                        st.markdown(f"**AI Verification Status:** <span style='color:{status_color}; font-weight:bold;'>{v_status}</span>", unsafe_allow_html=True)
                        
                        st.markdown(f"[🔗 View Original]({cert['file_url']})")
                        
                        # Fetch and provide download
                        content = get_file_content(cert['file_url'])
                        if content:
                            ext = cert['file_url'].split('.')[-1].lower()
                            mime_type = "application/pdf" if ext == "pdf" else f"image/{ext}"
                            st.download_button(
                                label="📥 Download Certificate",
                                data=content,
                                file_name=f"{cert['students']['full_name']}_{cert['event_name']}.{ext}",
                                mime=mime_type,
                                key=f"dl_{cert['id']}"
                            )
                    
                    with col2:
                        awarded_points = st.number_input(
                            "Points to Award (0-10)", 
                            min_value=0, 
                            max_value=10, 
                            value=5, 
                            key=f"pts_{cert['id']}"
                        )
                        btn_col1, btn_col2 = st.columns(2)
                        if btn_col1.button("✅ Approve", key=f"app_{cert['id']}"):
                            approve_certificate(supabase, cert, awarded_points)
                        if btn_col2.button("❌ Reject", key=f"rej_{cert['id']}"):
                            reject_certificate(supabase, cert)
        else:
            st.info("No pending certifications for review.")

    with tabs[1]:
        st.subheader("Department Participation Analytics")
        # Fetch certificates with student_id to calculate unique participating students
        data = supabase.table("certificates").select("department, status, student_id").execute()
        
        if data.data:
            df = pd.DataFrame(data.data)
            
            # --- 1. Student Participation Overview ---
            st.markdown("### 📊 Overall Participation")
            total_students = df['student_id'].nunique() if 'student_id' in df.columns else 0
            total_certs = len(df)
            approved_certs = len(df[df['status'] == 'Approved'])
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
                st.metric("Total Students Participated", total_students)
                st.markdown("</div>", unsafe_allow_html=True)
            with col2:
                st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
                st.metric("Total Certificates Submitted", total_certs)
                st.markdown("</div>", unsafe_allow_html=True)
            with col3:
                st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
                st.metric("Total Approved Certificates", approved_certs)
                st.markdown("</div>", unsafe_allow_html=True)
                
            st.divider()

            # --- 2 & 3. Department Participation Analytics & Comparison Chart ---
            st.markdown("### 🏢 Department Comparison")
            
            # Group data by department
            if 'student_id' in df.columns:
                dept_stats = df.groupby('department').agg(
                    Total_Students_Participated=('student_id', 'nunique'),
                    Certificates_Submitted=('status', 'count'),
                    Certificates_Approved=('status', lambda x: (x == 'Approved').sum())
                ).reset_index()
            else:
                 dept_stats = df.groupby('department').agg(
                    Certificates_Submitted=('status', 'count'),
                    Certificates_Approved=('status', lambda x: (x == 'Approved').sum())
                ).reset_index()
                 dept_stats['Total_Students_Participated'] = 0 # Fallback
            
            # Rename columns for display
            dept_stats.rename(columns={
                'department': 'Department Name',
                'Total_Students_Participated': 'Total Students Participated',
                'Certificates_Submitted': 'Certificates Submitted',
                'Certificates_Approved': 'Certificates Approved'
            }, inplace=True)

            # Bar chart for department participation (students)
            fig = px.bar(
                dept_stats, 
                x='Department Name', 
                y='Total Students Participated', 
                color='Department Name',
                title="Student Participation by Department",
                template="plotly_white",
                text_auto=True
            )
            fig.update_layout(showlegend=False)
            st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
            st.plotly_chart(fig, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)
            
            # --- 4. Department Comparison Table ---
            st.markdown("### 📋 Detailed Analytics Data")
            st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
            st.dataframe(
                dept_stats,
                use_container_width=True,
                hide_index=True
            )
            st.markdown("</div>", unsafe_allow_html=True)
            
        else:
            st.info("No data available for analytics yet.")

    with tabs[2]:
        st.subheader("🏆 Student Leaderboard")
        # Top students based on points
        leaders = supabase.table("students").select("full_name, roll_number, department, points").order("points", desc=True).limit(10).execute()
        
        if leaders.data:
            st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
            df_leaders = pd.DataFrame(leaders.data)
            df_leaders.index += 1
            st.table(df_leaders)
            st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.info("Leaderboard is currently empty.")

    with tabs[3]:
        st.subheader("💬 Ask AI Assistant")
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        if "staff_chat_history" not in st.session_state:
            st.session_state.staff_chat_history = []
            
        for msg in st.session_state.staff_chat_history:
            st.chat_message(msg["role"]).write(msg["content"])
            
        if prompt := st.chat_input("How do I review pending certificates?"):
            st.session_state.staff_chat_history.append({"role": "user", "content": prompt})
            st.chat_message("user").write(prompt)
            
            with st.spinner("AI is thinking..."):
                from chatbot_utils import get_ai_response
                response = get_ai_response(prompt, st.session_state.staff_chat_history[:-1], role="Staff")
                st.session_state.staff_chat_history.append({"role": "assistant", "content": response})
                st.chat_message("assistant").write(response)
        st.markdown("</div>", unsafe_allow_html=True)

def approve_certificate(supabase, cert, awarded_points):
    # Update Certificate Status
    supabase.table("certificates").update({"status": "Approved"}).eq("id", cert['id']).execute()
    
    # Update Student Points
    current_points_res = supabase.table("students").select("points").eq("id", cert['student_id']).execute()
    current_points = current_points_res.data[0]['points'] if current_points_res.data and current_points_res.data[0]['points'] is not None else 0
    new_points = current_points + int(awarded_points)
    supabase.table("students").update({"points": new_points}).eq("id", cert['student_id']).execute()
    
    student_name = cert.get('students', {}).get('full_name', 'Student')
    st.success(f"Approved! {awarded_points} points awarded to {student_name}")
    st.rerun()

def reject_certificate(supabase, cert):
    supabase.table("certificates").update({"status": "Rejected"}).eq("id", cert['id']).execute()
    st.warning("Certificate Rejected.")
    st.rerun()

def get_file_content(url):
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return response.content
    except Exception as e:
        st.error(f"Error fetching file: {e}")
    return None
