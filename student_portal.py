import streamlit as st
import time
import uuid

def show_page(supabase):
    if 'user_info' not in st.session_state or st.session_state.user_role != "Student":
        st.error("Access Denied")
        return

    student = st.session_state.user_info
    
    # --- Dashboard View ---
    st.markdown(f"<h1 class='main-header'>Student Dashboard</h1>", unsafe_allow_html=True)
    
    # Student Header Info
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"<div class='glass-card'><h3>Welcome, {student['full_name']}</h3><p>{student['roll_number']} | {student.get('email', 'N/A')}</p></div>", unsafe_allow_html=True)
    with col2:
        points = student.get('points') if student.get('points') is not None else 0
        st.markdown(f"<div class='glass-card'><h3>Total Points</h3><h2 style='color: #d97706;'>{points}</h2></div>", unsafe_allow_html=True)
    with col3:
        if points < 10:
            st.warning("⚠️ Low Participation Alert: Keep participating in events to earn more points!")
        else:
            st.success("✅ Great Participation! You are on the right track.")

    # --- Upload Certificate Section ---
    st.markdown("---")
    st.subheader("📤 Upload Certificate")
    
    with st.container():
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        col_up1, col_up2 = st.columns([2, 1])
        
        with col_up1:
            uploaded_file = st.file_uploader("Choose a certificate image or PDF", type=['pdf', 'jpg', 'jpeg', 'png'])
            event_name_input = st.text_input("Event Name", placeholder="e.g. National Level Codefest")
        
        with col_up2:
            event_type = st.selectbox("Event Type", [
                "Hackathon", 
                "Technical Event", 
                "Non-Technical Event", 
                "Workshop"
            ])
            achievement_level = st.selectbox("Achievement Level", [
                "1st Prize", 
                "2nd Prize", 
                "3rd Prize", 
                "Participation"
            ])

        if st.button("Upload Certificate"):
            if uploaded_file and event_name_input:
                # --- Robust Bucket Check ---
                bucket_exists = False
                try:
                    supabase.storage.get_bucket("certificates")
                    bucket_exists = True
                except Exception as e:
                    st.error(f"⚠️ Supabase Storage: {e}")
                    st.markdown("""
                    ### 🛠️ One-Time Setup Required
                    To enable uploads, please follow these steps in your Supabase Dashboard:
                    
                    1. **Create Bucket**: Go to **Storage** > **New Bucket** > Name it `certificates`.
                    2. **Make Public**: Toggle **'Public Bucket'** to **ON**.
                    3. **Add Policies**: This is crucial! 
                       - Go to **Storage** > **certificates** > **Policies**.
                       - Click **'New Policy'** > **'For full customization'**.
                       - Select **'ALLOWED OPERATIONS'**: `INSERT` and `SELECT`.
                       - Set **'Target Roles'**: `anon` and `authenticated`.
                       - For **'Policy Definition'**: `true` (allow all).
                    
                    *Without these steps, the "Bucket not found" or "Permission denied" error will persist.*
                    """, unsafe_allow_html=True)
                    st.stop()
                
                with st.spinner("Uploading to Supabase Storage..."):
                    file_extension = uploaded_file.name.split('.')[-1]
                    file_name = f"{uuid.uuid4()}.{file_extension}"
                    try:
                        # 1. Store in Supabase Storage "certificates" bucket
                        supabase.storage.from_("certificates").upload(
                            path=file_name,
                            file=uploaded_file.getvalue(),
                            file_options={"content-type": uploaded_file.type}
                        )
                        file_url = supabase.storage.from_("certificates").get_public_url(file_name)
                        
                        # 2. Run AI Verification
                        try:
                            from verification_utils import verify_certificate_with_ai
                            with st.spinner("AI is verifying your certificate..."):
                                ai_result = verify_certificate_with_ai(file_url, student['full_name'], event_name_input)
                                v_status = ai_result.get("verification_status", "NOT VALID CERTIFICATE")
                        except Exception as ai_err:
                            st.warning(f"AI Verification skipped: {ai_err}")
                            v_status = "NOT VALID CERTIFICATE"

                        # 3. Save Data to Database
                        cert_data = {
                            "student_id": student['id'],
                            "student_name": student['full_name'],
                            "student_email": student.get('email'),
                            "roll_number": student['roll_number'],
                            "department": student.get('department'),
                            "event_name": event_name_input,
                            "event_type": event_type,
                            "achievement_level": achievement_level,
                            "verification_status": v_status,
                            "file_url": file_url,
                            "status": "Pending"
                        }
                        supabase.table("certificates").insert(cert_data).execute()
                        
                        status_color = "#10b981" if "VALID" in v_status and "NOT" not in v_status else "#ef4444"
                        st.markdown(f"### AI Verification: <span style='color:{status_color};'>{v_status}</span>", unsafe_allow_html=True)
                        st.success("✅ Certificate uploaded successfully!")
                        st.balloons()
                        time.sleep(1)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error during upload: {e}")
            else:
                st.warning("Please provide both a file and the event name.")
        st.markdown("</div>", unsafe_allow_html=True)

    # --- Uploaded Certificates List ---
    st.markdown("---")
    st.subheader("📋 My Uploaded Certificates")
    
    try:
        # Fetch certificates for the current student
        certs_res = supabase.table("certificates").select("*").eq("student_id", student['id']).order("created_at", desc=True).execute()
        certs_data = certs_res.data
        
        if certs_data:
            # Prepare data for table
            table_data = []
            for cert in certs_data:
                # Extract file name from URL or metadata if possible, otherwise use a placeholder
                fname = cert['file_url'].split('/')[-1] if 'file_url' in cert else "N/A"
                table_data.append({
                    "Event Type": cert['event_type'],
                    "Achievement Level": cert.get('achievement_level', 'N/A'),
                    "AI Status": cert.get('verification_status', 'NOT VALID CERTIFICATE'),
                    "Status": cert['status']
                })
            
            # Show the table as requested
            st.table(table_data)
            
            # Optional: Add clear expanders for details/viewing
            st.markdown("#### 🔽 Detailed View")
            for cert in certs_data:
                status_color = {
                    "Pending": "#b45309",
                    "Approved": "#059669",
                    "Rejected": "#dc2626"
                }.get(cert['status'], "#1e293b")
                
                with st.expander(f"{cert['event_name']} - {cert['status']}"):
                    st.write(f"**Event Type:** {cert['event_type']}")
                    st.write(f"**Achievement Level:** {cert.get('achievement_level', 'N/A')}")
                    v_stat = cert.get('verification_status', 'NOT VALID CERTIFICATE')
                    v_color = "#10b981" if "VALID" in v_stat and "NOT" not in v_stat else "#ef4444"
                    st.markdown(f"**AI Verification Status:** <span style='color:{v_color}; font-weight:bold;'>{v_stat}</span>", unsafe_allow_html=True)
                    st.markdown(f"**Status:** <span style='color:{status_color}; font-weight:bold;'>{cert['status']}</span>", unsafe_allow_html=True)
                    st.markdown(f"[View Document]({cert['file_url']})")
        else:
            st.info("No certificates uploaded yet.")
    except Exception as e:
        st.error(f"Error fetching certificates: {e}")
        
    # --- AI Chatbot Section ---
    st.markdown("---")
    st.subheader("💬 AI Assistant")
    
    with st.expander("Ask me anything about the Student Portal", expanded=False):
        st.markdown("<div class='glass-card' style='padding: 1rem;'>", unsafe_allow_html=True)
        if "student_chat_history" not in st.session_state:
            st.session_state.student_chat_history = []
            
        for msg in st.session_state.student_chat_history:
            st.chat_message(msg["role"]).write(msg["content"])
            
        if prompt := st.chat_input("How do I check my certificate status?"):
            st.session_state.student_chat_history.append({"role": "user", "content": prompt})
            st.chat_message("user").write(prompt)
            
            with st.spinner("AI is thinking..."):
                from chatbot_utils import get_ai_response
                # Exclude the last message (the prompt itself) from the history passed to the function
                response = get_ai_response(prompt, st.session_state.student_chat_history[:-1], role="Student")
                st.session_state.student_chat_history.append({"role": "assistant", "content": response})
                st.chat_message("assistant").write(response)
        st.markdown("</div>", unsafe_allow_html=True)

