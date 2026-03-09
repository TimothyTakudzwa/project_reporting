import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import numpy as np
from database import (
    init_db, add_project, get_all_projects, 
    delete_project, calculate_targeted_progress, update_project,
    add_feature, get_project_features, update_feature, delete_feature, get_project_by_id,
    add_adoption, get_all_adoptions, update_adoption, delete_adoption, get_adoption_by_id,
    add_project_update, get_project_updates
)

from dashboard_v2 import run_dashboard

run_dashboard()
st.stop()

# Initialize the database
init_db()

# Set page config
st.set_page_config(
    page_title="Project Status Reports",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Project Status Reports Dashboard")

# Sidebar for adding/editing projects
with st.sidebar:
    st.header("Project Management")
    
    tab1, tab2, tab3 = st.tabs(["New Project", "Edit Project", "Manage Features"])
    
    with tab1:
        project_name = st.text_input("Project Name")
        project_type = st.selectbox(
            "Project Type",
            ["AI", "RPA", "Software Development", "Innovation"]
        )
        
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("Start Date")
        with col2:
            end_date = st.date_input("End Date")
        
        current_progress = st.slider("Current Progress (%)", 0, 100, 0)
        
        if st.button("Add Project", key="add_btn"):
            if project_name and start_date and end_date:
                if start_date >= end_date:
                    st.error("End date must be after start date!")
                else:
                    add_project(
                        project_name,
                        project_type,
                        start_date.strftime("%Y-%m-%d"),
                        end_date.strftime("%Y-%m-%d"),
                        current_progress
                    )
                    st.success("✅ Project added successfully!")
                    st.rerun()
            else:
                st.error("Please fill in all fields!")
    
    with tab2:
        st.subheader("Edit Existing Project")
        projects_df = get_all_projects()
        
        if len(projects_df) > 0:
            project_to_edit = st.selectbox(
                "Select Project to Edit",
                options=projects_df['name'].tolist(),
                key="edit_selector"
            )
            
            if project_to_edit:
                selected_project = projects_df[projects_df['name'] == project_to_edit].iloc[0]
                
                edit_name = st.text_input("Project Name", value=selected_project['name'], key="edit_name")
                edit_type = st.selectbox(
                    "Project Type",
                    ["AI", "RPA", "Software Development", "Innovation"],
                    index=["AI", "RPA", "Software Development", "Innovation"].index(selected_project['project_type']),
                    key="edit_type"
                )
                
                col1, col2 = st.columns(2)
                with col1:
                    edit_start = st.date_input(
                        "Start Date",
                        value=datetime.strptime(selected_project['start_date'], "%Y-%m-%d"),
                        key="edit_start"
                    )
                with col2:
                    edit_end = st.date_input(
                        "End Date",
                        value=datetime.strptime(selected_project['end_date'], "%Y-%m-%d"),
                        key="edit_end"
                    )
                
                col1, col2 = st.columns(2)
                with col1:
                    edit_progress = st.slider(
                        "Current Progress (%)",
                        0, 100,
                        int(selected_project['current_progress']),
                        key="edit_progress"
                    )
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("💾 Update Project", key="update_btn"):
                        if edit_start >= edit_end:
                            st.error("End date must be after start date!")
                        else:
                            update_project(
                                selected_project['id'],
                                edit_name,
                                edit_type,
                                edit_start.strftime("%Y-%m-%d"),
                                edit_end.strftime("%Y-%m-%d"),
                                edit_progress
                            )
                            st.success("✅ Project updated successfully!")
                            st.rerun()
                
                with col2:
                    if st.button("🗑️ Delete Project", key="delete_btn"):
                        delete_project(selected_project['id'])
                        st.success("✅ Project deleted!")
                        st.rerun()
        else:
            st.info("No projects available to edit.")
    
    with tab3:
        st.subheader("Manage Features")
        projects_df = get_all_projects()
        
        if len(projects_df) > 0:
            selected_project_feat = st.selectbox(
                "Select Project",
                options=projects_df['name'].tolist(),
                key="feat_project_selector"
            )
            
            if selected_project_feat:
                project_id = projects_df[projects_df['name'] == selected_project_feat].iloc[0]['id']
                
                st.markdown("**Add New Feature:**")
                feature_name = st.text_input("Feature Name", key="new_feat_name")
                feature_delivery = st.date_input("Delivery Date", key="new_feat_delivery")
                feature_status = st.selectbox(
                    "Status",
                    ["Pending", "In Progress", "Completed", "Blocked"],
                    key="new_feat_status"
                )
                
                if st.button("➕ Add Feature", key="add_feat_btn"):
                    if feature_name:
                        add_feature(
                            project_id,
                            feature_name,
                            feature_delivery.strftime("%Y-%m-%d"),
                            feature_status
                        )
                        st.success("✅ Feature added!")
                        st.rerun()
                    else:
                        st.error("Please enter a feature name!")
                
                st.divider()
                
                # Display existing features
                features_df = get_project_features(project_id)
                if len(features_df) > 0:
                    st.markdown("**Existing Features:**")
                    for idx, feature in features_df.iterrows():
                        with st.expander(f"📋 {feature['feature_name']} - {feature['status']}"):
                            st.write(f"**Delivery Date:** {feature['delivery_date']}")
                            
                            if st.button(f"🗑️ Delete", key=f"del_feat_{feature['id']}"):
                                delete_feature(feature['id'])
                                st.success("Feature deleted!")
                                st.rerun()
                else:
                    st.info("No features added yet.")
        else:
            st.info("Create a project first to add features.")

# Create main tabs for Projects, User Adoption, and Updates Timeline
tab_projects, tab_adoption, tab_updates = st.tabs(["📊 Projects", "👥 User Adoption", "🕒 Task Updates Timeline"])

# ========== PROJECTS TAB ==========
with tab_projects:

    # Main dashboard
    col1, col2 = st.columns([3, 1])
    
    with col2:
        st.metric("Total Projects", len(get_all_projects()))
    
    st.divider()
    
    # Get all projects
    projects_df = get_all_projects()
    
    if len(projects_df) == 0:
        st.info("📭 No projects yet. Add your first project using the sidebar!")
    else:
        # Display projects
        st.subheader("📋 Active Projects")

        # --- Circular Progress Rings for all projects ---
        num_projects = len(projects_df)
        ring_cols = st.columns(min(num_projects, 5))

        first_row_projects = projects_df.head(5)
        for i, (_, proj) in enumerate(first_row_projects.iterrows()):
            col_idx = i
            targeted = calculate_targeted_progress(proj['start_date'], proj['end_date'])
            progress = proj['current_progress']
            is_on_track = progress >= targeted

            fig_ring = go.Figure()

            # Background ring (remaining)
            fig_ring.add_trace(go.Pie(
                values=[progress, 100 - progress],
                hole=0.75,
                marker=dict(colors=[
                    '#2ecc71' if is_on_track else '#e74c3c',
                    '#f0f0f0'
                ]),
                textinfo='none',
                hoverinfo='skip',
                sort=False,
                direction='clockwise',
                rotation=90
            ))

            # Center text
            fig_ring.add_annotation(
                text=f"<b>{progress}%</b>",
                x=0.5, y=0.55, showarrow=False,
                font=dict(size=28, color='#2c3e50')
            )
            fig_ring.add_annotation(
                text=f"Target: {targeted}%",
                x=0.5, y=0.4, showarrow=False,
                font=dict(size=11, color='#7f8c8d')
            )

            fig_ring.update_layout(
                showlegend=False,
                height=180,
                margin=dict(t=30, b=10, l=10, r=10),
                title=dict(text=proj['name'], x=0.5, font=dict(size=13)),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)'
            )

            with ring_cols[col_idx]:
                st.plotly_chart(fig_ring, width='stretch', key=f"ring_primary_{proj['id']}")
                status_label = "✅ On Track" if is_on_track else "⚠️ Behind"
                st.caption(f"<div style='text-align:center'>{status_label}</div>", unsafe_allow_html=True)

        # Handle overflow if more than 5 projects
        if num_projects > 5:
            second_row_projects = projects_df.iloc[5:10]
            extra_cols = st.columns(len(second_row_projects))
            for i, (_, proj) in enumerate(second_row_projects.iterrows()):
                targeted = calculate_targeted_progress(proj['start_date'], proj['end_date'])
                progress = proj['current_progress']
                is_on_track = progress >= targeted

                fig_ring = go.Figure()
                fig_ring.add_trace(go.Pie(
                    values=[progress, 100 - progress],
                    hole=0.75,
                    marker=dict(colors=[
                        '#2ecc71' if is_on_track else '#e74c3c',
                        '#f0f0f0'
                    ]),
                    textinfo='none',
                    hoverinfo='skip',
                    sort=False,
                    direction='clockwise',
                    rotation=90
                ))
                fig_ring.add_annotation(
                    text=f"<b>{progress}%</b>",
                    x=0.5, y=0.55, showarrow=False,
                    font=dict(size=28, color='#2c3e50')
                )
                fig_ring.add_annotation(
                    text=f"Target: {targeted}%",
                    x=0.5, y=0.4, showarrow=False,
                    font=dict(size=11, color='#7f8c8d')
                )
                fig_ring.update_layout(
                    showlegend=False,
                    height=180,
                    margin=dict(t=30, b=10, l=10, r=10),
                    title=dict(text=proj['name'], x=0.5, font=dict(size=13)),
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)'
                )
                with extra_cols[i]:
                    st.plotly_chart(fig_ring, width='stretch', key=f"ring_overflow_{proj['id']}")
                    status_label = "✅ On Track" if is_on_track else "⚠️ Behind"
                    st.caption(f"<div style='text-align:center'>{status_label}</div>", unsafe_allow_html=True)

        st.divider()
    
    for idx, project in projects_df.iterrows():
        with st.container(border=True):
            col1, col2, col3 = st.columns([2, 2, 1])
            
            with col1:
                st.markdown(f"### {project['name']}")
                st.caption(f"Type: **{project['project_type']}**")
                
                # Show features count
                features = get_project_features(project['id'])
                if len(features) > 0:
                    completed = len(features[features['status'] == 'Completed'])
                    st.caption(f"📋 Features: {completed}/{len(features)} completed")
                    with st.expander("View Features"):
                        for _, feat in features.iterrows():
                            status_emoji = {
                                'Completed': '✅',
                                'In Progress': '🔄',
                                'Pending': '⏳',
                                'Blocked': '🚫'
                            }.get(feat['status'], '📌')
                            
                            days_to_delivery = (datetime.strptime(feat['delivery_date'], "%Y-%m-%d") - datetime.now()).days
                            delivery_status = f"({days_to_delivery} days)" if days_to_delivery > 0 else "⚠️ Overdue"
                            
                            st.write(f"{status_emoji} **{feat['feature_name']}**")
                            st.caption(f"Due: {feat['delivery_date']} {delivery_status}")
            
            with col2:
                # Calculate targeted progress
                targeted = calculate_targeted_progress(
                    project['start_date'], 
                    project['end_date']
                )
                variance = project['current_progress'] - targeted
                
                # Compact metrics row
                m1, m2, m3 = st.columns(3)
                with m1:
                    st.metric("Current", f"{project['current_progress']}%")
                with m2:
                    st.metric("Target", f"{targeted}%")
                with m3:
                    st.metric("Variance", f"{variance:+.0f}%", delta=f"{variance:+.0f}%")
                
                # Progress bar using Streamlit native
                st.progress(min(project['current_progress'] / 100, 1.0), text=f"Progress: {project['current_progress']}%")
            
            with col3:
                # Display dates
                st.caption("📅 **Timeline**")
                st.caption(f"Start: {project['start_date']}")
                st.caption(f"End: {project['end_date']}")
                
                # Calculate days remaining
                end_date = datetime.strptime(project['end_date'], "%Y-%m-%d")
                days_remaining = (end_date - datetime.now()).days
                
                if days_remaining > 0:
                    st.caption(f"⏱️ Days Left: **{days_remaining}**")
                elif days_remaining == 0:
                    st.caption("🏁 **Due Today**")
                else:
                    st.caption(f"⚠️ **{abs(days_remaining)} days overdue**")
            
            # Delete button
            if st.button(
                "🗑️ Delete",
                key=f"delete_{project['id']}",
                width='stretch'
            ):
                delete_project(project['id'])
                st.success("Project deleted!")
                st.rerun()

st.divider()

# Summary Statistics
st.subheader("📈 Summary Statistics")

if len(projects_df) > 0:
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        avg_current = projects_df['current_progress'].mean()
        st.metric("Avg Current Progress", f"{avg_current:.1f}%")
    
    with col2:
        avg_targeted = projects_df.apply(
            lambda row: calculate_targeted_progress(row['start_date'], row['end_date']),
            axis=1
        ).mean()
        st.metric("Avg Targeted Progress", f"{avg_targeted:.1f}%")
    
    with col3:
        on_track = sum(
            projects_df.apply(
                lambda row: row['current_progress'] >= calculate_targeted_progress(row['start_date'], row['end_date']),
                axis=1
            )
        )
        st.metric("On Track", on_track)
    
    with col4:
        behind = len(projects_df) - on_track
        st.metric("Behind Schedule", behind)
    
    st.divider()

    # ========== EXECUTIVE REPORTING SECTION ==========
    st.subheader("📊 Executive Dashboard")

    # Prepare data for executive charts
    exec_data = projects_df.copy()
    exec_data['targeted_progress'] = exec_data.apply(
        lambda row: calculate_targeted_progress(row['start_date'], row['end_date']),
        axis=1
    )
    exec_data['variance'] = exec_data['current_progress'] - exec_data['targeted_progress']
    exec_data['status'] = exec_data['variance'].apply(lambda v: 'On Track' if v >= 0 else ('At Risk' if v >= -15 else 'Critical'))
    exec_data['start_dt'] = pd.to_datetime(exec_data['start_date'])
    exec_data['end_dt'] = pd.to_datetime(exec_data['end_date'])
    exec_data['days_total'] = (exec_data['end_dt'] - exec_data['start_dt']).dt.days
    exec_data['days_elapsed'] = (datetime.now() - exec_data['start_dt']).dt.days.clip(lower=0)
    exec_data['days_remaining'] = (exec_data['end_dt'] - datetime.now()).dt.days
    exec_data['time_consumed_pct'] = (exec_data['days_elapsed'] / exec_data['days_total'].clip(lower=1) * 100).clip(0, 100)

    # --- EXCO AI Portfolio Snapshot (single chart) ---
    st.markdown("### 🤖 AI Projects EXCO Snapshot")
    ai_exec_data = exec_data[exec_data['project_type'] == 'AI'].copy()

    if len(ai_exec_data) > 0:
        ai_exec_data['delivery_stage'] = np.where(
            ai_exec_data['current_progress'] >= 100,
            'Completed',
            'In Development'
        )
        ai_exec_data = ai_exec_data.sort_values('current_progress', ascending=True)

        ai_completed = len(ai_exec_data[ai_exec_data['delivery_stage'] == 'Completed'])
        ai_in_development = len(ai_exec_data[ai_exec_data['delivery_stage'] == 'In Development'])

        fig_ai_exco = go.Figure()

        for stage_name, color in [('Completed', '#27ae60'), ('In Development', '#f39c12')]:
            stage_data = ai_exec_data[ai_exec_data['delivery_stage'] == stage_name]
            if len(stage_data) > 0:
                fig_ai_exco.add_trace(go.Bar(
                    y=stage_data['name'],
                    x=stage_data['current_progress'],
                    orientation='h',
                    name=stage_name,
                    marker_color=color,
                    text=[f"{v:.0f}%" for v in stage_data['current_progress']],
                    textposition='inside',
                    customdata=stage_data[['delivery_stage']],
                    hovertemplate='<b>%{y}</b><br>Progress: %{x:.0f}%<br>Status: %{customdata[0]}<extra></extra>'
                ))

        fig_ai_exco.add_trace(go.Bar(
            y=ai_exec_data['name'],
            x=100 - ai_exec_data['current_progress'],
            orientation='h',
            name='Remaining',
            marker_color='#ecf0f1',
            hovertemplate='<b>%{y}</b><br>Remaining: %{x:.0f}%<extra></extra>'
        ))

        fig_ai_exco.update_layout(
            title='AI Projects Progress (Completed vs In Development)',
            barmode='stack',
            xaxis=dict(range=[0, 100], title='Progress (%)', ticksuffix='%'),
            yaxis=dict(title='', automargin=True, tickfont=dict(size=11)),
            height=max(320, len(ai_exec_data) * 48),
            margin=dict(l=190, r=20, t=55, b=40),
            legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='left', x=0)
        )

        st.plotly_chart(fig_ai_exco, width='stretch', key='ai_exco_snapshot_chart')
        st.caption(f"AI projects: {len(ai_exec_data)} | Completed: {ai_completed} | In development: {ai_in_development}")
    else:
        st.info("No AI projects available yet for the EXCO snapshot.")

    st.divider()

    # --- Row 1: Portfolio Health Overview ---
    col1, col2 = st.columns(2)

    with col1:
        # RAG Status Summary (Red/Amber/Green traffic light)
        status_counts = exec_data['status'].value_counts()
        rag_colors = {'On Track': '#27ae60', 'At Risk': '#f39c12', 'Critical': '#e74c3c'}
        
        fig_rag = go.Figure()
        for status_name in ['On Track', 'At Risk', 'Critical']:
            count = status_counts.get(status_name, 0)
            fig_rag.add_trace(go.Bar(
                x=[status_name],
                y=[count],
                marker_color=rag_colors[status_name],
                text=[count],
                textposition='outside',
                textfont=dict(size=18, family='Arial Black'),
                name=status_name,
                hovertemplate=f"<b>{status_name}</b><br>Projects: {count}<extra></extra>"
            ))
        
        fig_rag.update_layout(
            title="Portfolio RAG Status (Red / Amber / Green)",
            yaxis_title="Number of Projects",
            height=350,
            showlegend=False,
            yaxis=dict(dtick=1)
        )
        st.plotly_chart(fig_rag, width='stretch')

    with col2:
        # Progress vs Time Consumed (Efficiency Quadrant)
        fig_quad = go.Figure()

        fig_quad.add_trace(go.Scatter(
            x=exec_data['time_consumed_pct'],
            y=exec_data['current_progress'],
            mode='markers+text',
            marker=dict(
                size=18,
                color=[rag_colors[s] for s in exec_data['status']],
                line=dict(width=2, color='white')
            ),
            text=exec_data['name'],
            textposition='top center',
            textfont=dict(size=10),
            hovertemplate='<b>%{text}</b><br>Time Used: %{x:.0f}%<br>Progress: %{y:.0f}%<extra></extra>',
            name='Projects'
        ))

        # Diagonal line: ideal progress = time consumed
        fig_quad.add_shape(type="line", x0=0, y0=0, x1=100, y1=100,
                           line=dict(color="gray", dash="dash", width=1))
        fig_quad.add_annotation(x=85, y=90, text="Ideal Pace", showarrow=False,
                                font=dict(color="gray", size=10))

        # Quadrant shading
        fig_quad.add_shape(type="rect", x0=50, y0=0, x1=100, y1=50,
                           fillcolor="rgba(231,76,60,0.08)", line=dict(width=0))
        fig_quad.add_annotation(x=75, y=15, text="⚠️ Behind", showarrow=False,
                                font=dict(color="#e74c3c", size=11))
        fig_quad.add_shape(type="rect", x0=0, y0=50, x1=50, y1=100,
                           fillcolor="rgba(39,174,96,0.08)", line=dict(width=0))
        fig_quad.add_annotation(x=25, y=85, text="✅ Ahead", showarrow=False,
                                font=dict(color="#27ae60", size=11))

        fig_quad.update_layout(
            title="Progress vs Time Consumed (Efficiency Quadrant)",
            xaxis_title="Timeline Consumed (%)",
            yaxis_title="Current Progress (%)",
            height=350,
            xaxis=dict(range=[0, 105]),
            yaxis=dict(range=[0, 105]),
            showlegend=False
        )
        st.plotly_chart(fig_quad, width='stretch')

    # --- Row 2: Detailed Portfolio View ---
    col1, col2 = st.columns(2)

    with col1:
        # Stacked bar: Current vs Gap to Target for each project
        exec_sorted = exec_data.sort_values('current_progress', ascending=True)
        gap = (exec_sorted['targeted_progress'] - exec_sorted['current_progress']).clip(lower=0)
        ahead = (exec_sorted['current_progress'] - exec_sorted['targeted_progress']).clip(lower=0)

        fig_gap = go.Figure()
        fig_gap.add_trace(go.Bar(
            y=exec_sorted['name'],
            x=exec_sorted['current_progress'],
            orientation='h',
            name='Current Progress',
            marker_color='#3498db',
            text=[f"{v:.0f}%" for v in exec_sorted['current_progress']],
            textposition='inside',
            insidetextanchor='middle'
        ))
        fig_gap.add_trace(go.Bar(
            y=exec_sorted['name'],
            x=gap,
            orientation='h',
            name='Gap to Target',
            marker_color='#e74c3c',
            marker_opacity=0.6,
            text=[f"-{v:.0f}%" if v > 0 else "" for v in gap],
            textposition='inside'
        ))
        fig_gap.add_trace(go.Bar(
            y=exec_sorted['name'],
            x=ahead,
            orientation='h',
            name='Ahead of Target',
            marker_color='#27ae60',
            marker_opacity=0.6,
            text=[f"+{v:.0f}%" if v > 0 else "" for v in ahead],
            textposition='inside'
        ))

        fig_gap.update_layout(
            title="Progress vs Target Gap Analysis",
            xaxis_title="Percentage (%)",
            barmode='stack',
            height=350,
            legend=dict(orientation="h", yanchor="bottom", y=-0.25)
        )
        st.plotly_chart(fig_gap, width='stretch')

    with col2:
        # Budget of Time: how much timeline each project has used vs remaining
        time_sorted = exec_data.sort_values('time_consumed_pct', ascending=True)

        fig_time_budget = go.Figure()
        fig_time_budget.add_trace(go.Bar(
            y=time_sorted['name'],
            x=time_sorted['time_consumed_pct'],
            orientation='h',
            name='Time Used',
            marker_color='#2980b9',
            text=[f"{v:.0f}%" for v in time_sorted['time_consumed_pct']],
            textposition='inside',
            insidetextanchor='middle'
        ))
        fig_time_budget.add_trace(go.Bar(
            y=time_sorted['name'],
            x=100 - time_sorted['time_consumed_pct'],
            orientation='h',
            name='Time Remaining',
            marker_color='#ecf0f1',
            text=[f"{v:.0f}%" for v in (100 - time_sorted['time_consumed_pct'])],
            textposition='inside',
            insidetextanchor='middle',
            textfont=dict(color='#7f8c8d')
        ))

        fig_time_budget.update_layout(
            title="Timeline Budget (Time Consumed vs Remaining)",
            xaxis_title="Percentage (%)",
            barmode='stack',
            height=350,
            legend=dict(orientation="h", yanchor="bottom", y=-0.25)
        )
        st.plotly_chart(fig_time_budget, width='stretch')

    # --- Row 3: Executive Summary Table ---
    st.subheader("📋 Executive Summary Report")

    exec_table = exec_data[[
        'name', 'project_type', 'current_progress', 'targeted_progress',
        'variance', 'status', 'days_remaining'
    ]].copy()
    exec_table['variance'] = exec_table['variance'].apply(lambda v: f"{v:+.0f}%")
    exec_table['current_progress'] = exec_table['current_progress'].apply(lambda v: f"{v}%")
    exec_table['targeted_progress'] = exec_table['targeted_progress'].apply(lambda v: f"{v:.0f}%")
    exec_table['days_remaining'] = exec_table['days_remaining'].apply(lambda d: f"{d} days" if d >= 0 else f"⚠️ {abs(d)} days overdue")
    exec_table.columns = ['Project', 'Type', 'Current', 'Target', 'Variance', 'RAG Status', 'Time Left']

    st.dataframe(
        exec_table,
        width='stretch',
        hide_index=True
    )

    st.divider()

    # ========== ROADMAP INFOGRAPHICS BY PROJECT TYPE ==========
    st.subheader("🗺️ Project Roadmap by Type")

    project_types = ["AI", "RPA", "Software Development", "Innovation"]
    type_colors = {
        "AI": {"primary": "#8e44ad", "light": "rgba(142,68,173,0.15)", "phases": ["Research & Data", "Model Dev", "Training", "Testing", "Deployment", "Monitoring"]},
        "RPA": {"primary": "#e67e22", "light": "rgba(230,126,34,0.15)", "phases": ["Process Analysis", "Bot Design", "Development", "UAT", "Go-Live", "Optimization"]},
        "Software Development": {"primary": "#2980b9", "light": "rgba(41,128,185,0.15)", "phases": ["Requirements", "Design", "Development", "QA Testing", "Staging", "Production"]},
        "Innovation": {"primary": "#27ae60", "light": "rgba(39,174,96,0.15)", "phases": ["Ideation", "Prototyping", "Validation", "Pilot", "Scale", "Review"]}
    }

    # Filter to only types that have projects
    active_types = exec_data['project_type'].unique().tolist()

    for ptype in project_types:
        type_projects = exec_data[exec_data['project_type'] == ptype]
        if len(type_projects) == 0:
            continue

        tc = type_colors[ptype]
        phases = tc["phases"]
        num_phases = len(phases)

        st.markdown(f"#### {'🤖' if ptype == 'AI' else '⚙️' if ptype == 'RPA' else '💻' if ptype == 'Software Development' else '💡'} {ptype} Roadmap")

        fig_roadmap = go.Figure()

        # Draw phase columns (vertical bands)
        for pi, phase in enumerate(phases):
            x0 = pi / num_phases * 100
            x1 = (pi + 1) / num_phases * 100
            fig_roadmap.add_shape(
                type="rect", x0=x0, x1=x1, y0=-0.5, y1=len(type_projects) - 0.5,
                fillcolor=tc["light"] if pi % 2 == 0 else "rgba(255,255,255,0)",
                line=dict(color="rgba(0,0,0,0.05)", width=1)
            )
            fig_roadmap.add_annotation(
                x=(x0 + x1) / 2, y=len(type_projects) - 0.5,
                text=f"<b>{phase}</b>", showarrow=False,
                yshift=20, font=dict(size=10, color=tc["primary"])
            )

        # Draw each project as a lane
        for idx, (_, proj) in enumerate(type_projects.iterrows()):
            progress = proj['current_progress']
            targeted = proj['targeted_progress']
            status = proj['status']

            # Full track (background)
            fig_roadmap.add_trace(go.Scatter(
                x=[0, 100], y=[idx, idx],
                mode='lines',
                line=dict(color='#ecf0f1', width=22),
                showlegend=False, hoverinfo='skip'
            ))

            # Targeted progress marker
            fig_roadmap.add_trace(go.Scatter(
                x=[0, targeted], y=[idx, idx],
                mode='lines',
                line=dict(color='rgba(0,0,0,0.1)', width=22),
                showlegend=False, hoverinfo='skip'
            ))

            # Actual progress
            bar_color = '#27ae60' if status == 'On Track' else ('#f39c12' if status == 'At Risk' else '#e74c3c')
            fig_roadmap.add_trace(go.Scatter(
                x=[0, progress], y=[idx, idx],
                mode='lines',
                line=dict(color=bar_color, width=22),
                showlegend=False,
                hovertemplate=f"<b>{proj['name']}</b><br>Progress: {progress}%<br>Target: {targeted:.0f}%<br>Status: {status}<extra></extra>"
            ))

            # Progress label
            fig_roadmap.add_annotation(
                x=max(progress, 5), y=idx,
                text=f"<b>{progress}%</b>",
                showarrow=False, xanchor='left', xshift=5,
                font=dict(size=11, color='#2c3e50')
            )

            # Target marker (diamond)
            fig_roadmap.add_trace(go.Scatter(
                x=[targeted], y=[idx],
                mode='markers',
                marker=dict(symbol='diamond', size=10, color='#2c3e50',
                            line=dict(color='white', width=1)),
                showlegend=False,
                hovertemplate=f"Target: {targeted:.0f}%<extra></extra>"
            ))

            # Project name on left
            fig_roadmap.add_annotation(
                x=0, y=idx,
                text=f"<b>{proj['name']}</b>",
                showarrow=False, xanchor='right', xshift=-10,
                font=dict(size=12, color='#2c3e50')
            )

            # Days remaining badge
            days_left = proj['days_remaining']
            badge_text = f"{days_left}d left" if days_left >= 0 else f"{abs(days_left)}d over"
            badge_color = '#27ae60' if days_left > 30 else ('#f39c12' if days_left > 0 else '#e74c3c')
            fig_roadmap.add_annotation(
                x=100, y=idx,
                text=f"<b>{badge_text}</b>",
                showarrow=False, xanchor='left', xshift=10,
                font=dict(size=10, color=badge_color)
            )

        # Phase milestone markers along  bottom
        for pi in range(num_phases + 1):
            x_pos = pi / num_phases * 100
            fig_roadmap.add_shape(
                type="line", x0=x_pos, x1=x_pos, y0=-0.5, y1=len(type_projects) - 0.5,
                line=dict(color="rgba(0,0,0,0.08)", width=1, dash="dot")
            )

        fig_roadmap.update_layout(
            height=max(180, len(type_projects) * 70 + 80),
            xaxis=dict(
                range=[-2, 115], showticklabels=False, showgrid=False,
                zeroline=False, title=""
            ),
            yaxis=dict(
                showticklabels=False, showgrid=False, zeroline=False,
                range=[-0.8, len(type_projects) - 0.2], title=""
            ),
            margin=dict(l=120, r=80, t=50, b=10),
            plot_bgcolor='white',
            paper_bgcolor='white',
            showlegend=False
        )

        st.plotly_chart(fig_roadmap, width='stretch')

        # Compact stats row for this type
        type_cols = st.columns(4)
        avg_prog = type_projects['current_progress'].mean()
        avg_tgt = type_projects['targeted_progress'].mean()
        on_track_count = len(type_projects[type_projects['status'] == 'On Track'])
        at_risk_count = len(type_projects) - on_track_count

        with type_cols[0]:
            st.metric(f"{ptype} Projects", len(type_projects))
        with type_cols[1]:
            st.metric("Avg Progress", f"{avg_prog:.0f}%")
        with type_cols[2]:
            st.metric("Avg Target", f"{avg_tgt:.0f}%")
        with type_cols[3]:
            st.metric("On Track / At Risk", f"{on_track_count} / {at_risk_count}")

        st.divider()

    # ========== ANNUAL ROADMAP (JAN–DEC WITH QUARTERLY LANES) ==========
    st.subheader("📅 Annual Project Roadmap — " + str(datetime.now().year))

    current_year = datetime.now().year
    year_start = datetime(current_year, 1, 1)
    year_end = datetime(current_year, 12, 31)

    # Quarter boundaries
    quarters = [
        ("Q1", datetime(current_year, 1, 1), datetime(current_year, 3, 31)),
        ("Q2", datetime(current_year, 4, 1), datetime(current_year, 6, 30)),
        ("Q3", datetime(current_year, 7, 1), datetime(current_year, 9, 30)),
        ("Q4", datetime(current_year, 10, 1), datetime(current_year, 12, 31)),
    ]

    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

    type_colors = {
        "AI": "#8e44ad",
        "RPA": "#e67e22",
        "Software Development": "#2980b9",
        "Innovation": "#27ae60",
    }

    feature_status_icons = {
        "Completed": "✅",
        "In Progress": "🔄",
        "Pending": "⏳",
        "Blocked": "🚫",
    }
    feature_status_colors = {
        "Completed": "#27ae60",
        "In Progress": "#3498db",
        "Pending": "#7f8c8d",
        "Blocked": "#e74c3c",
    }

    fig_annual = go.Figure()

    # Sort projects by start date
    sorted_exec = exec_data.sort_values('start_date').reset_index(drop=True)
    num_proj = len(sorted_exec)

    # Use spacing of 2 per project to leave room for feature labels
    y_spacing = 2.0
    total_y = num_proj * y_spacing

    # Quarter shading bands
    q_colors = ["rgba(52,152,219,0.05)", "rgba(46,204,113,0.05)",
                "rgba(241,196,15,0.05)", "rgba(231,76,60,0.05)"]
    for qi, (q_label, q_start, q_end) in enumerate(quarters):
        fig_annual.add_shape(
            type="rect",
            x0=q_start, x1=q_end,
            y0=-1, y1=total_y,
            fillcolor=q_colors[qi],
            line=dict(width=0),
            layer='below'
        )
        q_mid = q_start + (q_end - q_start) / 2
        fig_annual.add_annotation(
            x=q_mid, y=total_y,
            text=f"<b>{q_label}</b>", showarrow=False,
            yshift=18, font=dict(size=13, color='#2c3e50')
        )

    # Month gridlines and labels
    for mi in range(12):
        m_start = datetime(current_year, mi + 1, 1)
        fig_annual.add_shape(
            type="line", x0=m_start, x1=m_start,
            y0=-1, y1=total_y,
            line=dict(color="rgba(0,0,0,0.07)", width=1, dash="dot"),
            layer='below'
        )
        fig_annual.add_annotation(
            x=m_start + timedelta(days=15), y=-1,
            text=months[mi], showarrow=False,
            yshift=-14, font=dict(size=9, color='#7f8c8d')
        )

    # Horizontal swim lane separators
    for idx in range(num_proj):
        lane_y = idx * y_spacing
        if idx > 0:
            fig_annual.add_shape(
                type="line",
                x0=year_start, x1=year_end,
                y0=lane_y - y_spacing / 2, y1=lane_y - y_spacing / 2,
                line=dict(color="rgba(0,0,0,0.04)", width=1),
                layer='below'
            )

    # Draw each project
    for idx, (_, proj) in enumerate(sorted_exec.iterrows()):
        lane_y = idx * y_spacing  # Center of this project's lane
        proj_start = max(proj['start_dt'], year_start)
        proj_end = min(proj['end_dt'], year_end)
        ptype = proj['project_type']
        tc = type_colors.get(ptype, "#95a5a6")

        # Progress calculation
        proj_days = (proj['end_dt'] - proj['start_dt']).days
        progress_days = int(proj_days * proj['current_progress'] / 100) if proj_days > 0 else 0
        progress_date = min(proj['start_dt'] + timedelta(days=progress_days), year_end)
        progress_date = max(progress_date, year_start)

        # Full project bar (background track)
        fig_annual.add_trace(go.Scatter(
            x=[proj_start, proj_end], y=[lane_y, lane_y],
            mode='lines',
            line=dict(color='#e8e8e8', width=22),
            showlegend=False, hoverinfo='skip'
        ))

        # Progress bar overlay
        status_color = '#27ae60' if proj['status'] == 'On Track' else ('#f39c12' if proj['status'] == 'At Risk' else '#e74c3c')
        fig_annual.add_trace(go.Scatter(
            x=[proj_start, progress_date], y=[lane_y, lane_y],
            mode='lines',
            line=dict(color=status_color, width=22),
            showlegend=False,
            hovertemplate=(
                f"<b>{proj['name']}</b><br>"
                f"Type: {ptype}<br>"
                f"Progress: {proj['current_progress']}%<br>"
                f"Target: {proj['targeted_progress']:.0f}%<br>"
                f"Status: {proj['status']}<br>"
                f"Timeline: {proj['start_date']} → {proj['end_date']}"
                "<extra></extra>"
            )
        ))

        # Project name label on left
        fig_annual.add_annotation(
            x=year_start, y=lane_y,
            text=f"<b>{proj['name']}</b>",
            showarrow=False, xanchor='right', xshift=-10,
            font=dict(size=11, color='#2c3e50')
        )

        # Progress % inside or beside bar
        fig_annual.add_annotation(
            x=progress_date, y=lane_y,
            text=f"<b>{proj['current_progress']}%</b>",
            showarrow=False, xanchor='left', xshift=6,
            font=dict(size=9, color='#2c3e50')
        )

        # Type badge on right side
        fig_annual.add_annotation(
            x=year_end, y=lane_y,
            text=f"<b>{ptype}</b>",
            showarrow=False, xanchor='left', xshift=10,
            font=dict(size=8, color=tc)
        )

        # --- Feature milestones as flags on this lane ---
        features_df = get_project_features(proj['id'])
        if not features_df.empty and 'delivery_date' in features_df.columns:
            year_features = []
            for _, feat in features_df.iterrows():
                try:
                    feat_date = pd.to_datetime(feat['delivery_date'])
                except Exception:
                    continue
                if year_start <= feat_date <= year_end:
                    year_features.append({
                        'name': feat['feature_name'],
                        'date': feat_date,
                        'status': feat.get('status', 'Pending'),
                        'delivery_str': feat['delivery_date'],
                    })

            # Sort features by date so we can alternate above/below
            year_features.sort(key=lambda f: f['date'])

            for fi, feat in enumerate(year_features):
                f_status = feat['status']
                f_color = feature_status_colors.get(f_status, '#7f8c8d')
                f_icon = feature_status_icons.get(f_status, '📌')

                # Alternate above/below the bar to avoid overlap
                is_above = (fi % 2 == 0)
                marker_y = lane_y + (0.35 if is_above else -0.35)
                label_y_offset = 20 if is_above else -20

                # Vertical connector line from bar to marker
                fig_annual.add_shape(
                    type="line",
                    x0=feat['date'], x1=feat['date'],
                    y0=lane_y, y1=marker_y,
                    line=dict(color=f_color, width=1.5, dash="dot"),
                )

                # Feature milestone marker
                fig_annual.add_trace(go.Scatter(
                    x=[feat['date']], y=[marker_y],
                    mode='markers+text',
                    marker=dict(symbol='diamond', size=12, color=f_color,
                                line=dict(color='white', width=1.5)),
                    text=[f_icon],
                    textposition='middle center',
                    textfont=dict(size=7),
                    showlegend=False,
                    hovertemplate=(
                        f"<b>🚩 {feat['name']}</b><br>"
                        f"Project: {proj['name']}<br>"
                        f"Delivery: {feat['delivery_str']}<br>"
                        f"Status: {f_icon} {f_status}"
                        "<extra></extra>"
                    )
                ))

                # Feature name label
                fig_annual.add_annotation(
                    x=feat['date'], y=marker_y,
                    text=f"<b>{feat['name']}</b>",
                    showarrow=True,
                    arrowhead=0, arrowwidth=0.8,
                    arrowcolor=f_color,
                    ax=0, ay=-label_y_offset,
                    font=dict(size=8, color=f_color),
                    bgcolor='rgba(255,255,255,0.85)',
                    bordercolor=f_color,
                    borderwidth=0.5,
                    borderpad=2,
                    xanchor='center'
                )

    # Today marker
    now = datetime.now()
    if year_start <= now <= year_end:
        fig_annual.add_shape(
            type="line", x0=now, x1=now,
            y0=-1, y1=total_y,
            line=dict(color="#e74c3c", width=2, dash="dash")
        )
        fig_annual.add_annotation(
            x=now, y=total_y,
            text="<b>Today</b>", showarrow=False,
            yshift=8, font=dict(size=10, color='#e74c3c')
        )

    # Legend entries — project types
    for ptype_name, ptype_color in type_colors.items():
        if ptype_name in exec_data['project_type'].values:
            fig_annual.add_trace(go.Scatter(
                x=[None], y=[None], mode='lines',
                line=dict(color=ptype_color, width=8),
                name=ptype_name
            ))

    # Legend entries — status
    fig_annual.add_trace(go.Scatter(x=[None], y=[None], mode='lines',
                                    line=dict(color='#27ae60', width=6), name='On Track'))
    fig_annual.add_trace(go.Scatter(x=[None], y=[None], mode='lines',
                                    line=dict(color='#f39c12', width=6), name='At Risk'))
    fig_annual.add_trace(go.Scatter(x=[None], y=[None], mode='lines',
                                    line=dict(color='#e74c3c', width=6), name='Critical'))

    # Legend entries — feature statuses
    for fs_label, fs_color in [("Feature: ✅ Done", "#27ae60"),
                                ("Feature: 🔄 In Progress", "#3498db"),
                                ("Feature: ⏳ Pending", "#7f8c8d"),
                                ("Feature: 🚫 Blocked", "#e74c3c")]:
        fig_annual.add_trace(go.Scatter(
            x=[None], y=[None], mode='markers',
            marker=dict(symbol='diamond', size=9, color=fs_color,
                        line=dict(color='white', width=1)),
            name=fs_label
        ))

    fig_annual.update_layout(
        height=max(400, int(num_proj * y_spacing * 55) + 140),
        xaxis=dict(
            range=[year_start - timedelta(days=5), year_end + timedelta(days=5)],
            type='date', showgrid=False, zeroline=False,
            title=""
        ),
        yaxis=dict(
            showticklabels=False, showgrid=False, zeroline=False,
            range=[-1.5, total_y + 0.8], title=""
        ),
        margin=dict(l=150, r=140, t=50, b=70),
        plot_bgcolor='white',
        paper_bgcolor='white',
        legend=dict(orientation="h", yanchor="bottom", y=-0.18, font=dict(size=9))
    )

    st.plotly_chart(fig_annual, width='stretch')

    st.divider()

    # Feature Analysis Section
    st.subheader("📊 Feature Analysis & Gantt Charts")
    
    selected_project_features = st.selectbox(
        "Select project to view feature timeline",
        options=projects_df['name'].tolist(),
        key="feature_gantt_selector"
    )
    
    if selected_project_features:
        project_id = projects_df[projects_df['name'] == selected_project_features].iloc[0]['id']
        project_features = get_project_features(project_id)
        
        if len(project_features) > 0:
            st.markdown(f"### 📅 Feature Gantt Chart - {selected_project_features}")
            
            # Get project start date
            project = projects_df[projects_df['name'] == selected_project_features].iloc[0]
            project_start = pd.to_datetime(project['start_date'])
            
            # Prepare Gantt chart data
            gantt_data = project_features.copy()
            gantt_data['delivery_dt'] = pd.to_datetime(gantt_data['delivery_date'])
            gantt_data['start_date'] = project_start  # Use project start date for all features
            gantt_data = gantt_data.sort_values('delivery_date')
            
            # Create Gantt chart
            fig_gantt_features = px.timeline(
                gantt_data,
                x_start='start_date',
                x_end='delivery_dt',
                y='feature_name',
                color='status',
                color_discrete_map={
                    'Completed': '#2ecc71',
                    'In Progress': '#3498db',
                    'Pending': '#f39c12',
                    'Blocked': '#e74c3c'
                },
                title=f"Feature Timeline - {selected_project_features}",
                labels={'feature_name': 'Feature', 'delivery_dt': 'Delivery Date'},
                height=400
            )
            fig_gantt_features.update_layout(
                xaxis_type='date',
                hovermode='y unified'
            )
            st.plotly_chart(fig_gantt_features, width='stretch')
            
            st.divider()
            
            # Feature Analytics Grid
            col1, col2, col3, col4 = st.columns(4)
            
            total_features = len(gantt_data)
            completed = len(gantt_data[gantt_data['status'] == 'Completed'])
            in_progress = len(gantt_data[gantt_data['status'] == 'In Progress'])
            blocked = len(gantt_data[gantt_data['status'] == 'Blocked'])
            
            with col1:
                st.metric("Total Features", total_features)
            with col2:
                st.metric("Completed", completed)
            with col3:
                st.metric("In Progress", in_progress)
            with col4:
                st.metric("Blocked", blocked)
            
            # Feature visualizations
            col1, col2 = st.columns(2)
            
            with col1:
                # Feature Status Distribution
                status_counts = gantt_data['status'].value_counts()
                fig_status = px.pie(
                    values=status_counts.values,
                    names=status_counts.index,
                    title="Feature Status Distribution",
                    color_discrete_map={
                        'Completed': '#00C851',
                        'In Progress': '#0099CC',
                        'Pending': '#FF8800',
                        'Blocked': '#FF4444'
                    }
                )
                st.plotly_chart(fig_status, width='stretch')
            
            with col2:
                # Feature Delivery Timeline
                gantt_data['days_to_delivery'] = (gantt_data['delivery_dt'] - datetime.now()).dt.days
                overdue = len(gantt_data[gantt_data['days_to_delivery'] < 0])
                due_soon = len(gantt_data[(gantt_data['days_to_delivery'] >= 0) & (gantt_data['days_to_delivery'] <= 7)])
                on_schedule = len(gantt_data[gantt_data['days_to_delivery'] > 7])
                
                fig_timeline_status = go.Figure(data=[
                    go.Bar(
                        x=['Overdue', 'Due This Week', 'Future'],
                        y=[overdue, due_soon, on_schedule],
                        marker_color=['#e74c3c', '#f39c12', '#2ecc71'],
                        text=[overdue, due_soon, on_schedule],
                        textposition='auto'
                    )
                ])
                fig_timeline_status.update_layout(
                    title="Features by Delivery Timeline",
                    showlegend=False,
                    height=300
                )
                st.plotly_chart(fig_timeline_status, width='stretch')
            
            # Feature Completion Timeline
            col1, col2 = st.columns(2)
            
            with col1:
                # Cumulative completion over time
                gantt_data_sorted = gantt_data[gantt_data['status'] == 'Completed'].copy()
                gantt_data_sorted = gantt_data_sorted.sort_values('delivery_date')
                
                if len(gantt_data_sorted) > 0:
                    gantt_data_sorted['cumulative_completed'] = range(1, len(gantt_data_sorted) + 1)
                    
                    fig_cumulative = px.line(
                        gantt_data_sorted,
                        x='delivery_date',
                        y='cumulative_completed',
                        markers=True,
                        title="Feature Completion Trend",
                        labels={'delivery_date': 'Date', 'cumulative_completed': 'Completed'},
                        line_shape='linear'
                    )
                    fig_cumulative.update_layout(height=300)
                    st.plotly_chart(fig_cumulative, width='stretch')
                else:
                    st.info("No completed features yet")
            
            with col2:
                # Feature velocity (completion rate)
                now = datetime.now()
                past_7_days = len(gantt_data[(gantt_data['status'] == 'Completed') & 
                                           (gantt_data['delivery_dt'] >= now - pd.Timedelta(days=7))])
                past_30_days = len(gantt_data[(gantt_data['status'] == 'Completed') & 
                                            (gantt_data['delivery_dt'] >= now - pd.Timedelta(days=30))])
                
                velocity_data = pd.DataFrame({
                    'Period': ['Last 7 Days', 'Last 30 Days'],
                    'Features': [past_7_days, past_30_days]
                })
                
                fig_velocity = px.bar(
                    velocity_data,
                    x='Period',
                    y='Features',
                    title="Feature Completion Velocity",
                    text='Features',
                    color='Features',
                    color_continuous_scale='Plasma'
                )
                fig_velocity.update_traces(textposition='auto')
                fig_velocity.update_layout(height=300, showlegend=False)
                st.plotly_chart(fig_velocity, width='stretch')
            
            st.divider()
            
            # Detailed Feature Table
            st.markdown("**Detailed Feature List:**")
            display_features = gantt_data[['feature_name', 'status', 'delivery_date']].copy()
            display_features['days_to_delivery'] = gantt_data['days_to_delivery']
            display_features.columns = ['Feature', 'Status', 'Delivery Date', 'Days Until Delivery']
            display_features = display_features.sort_values('Delivery Date')
            st.dataframe(display_features, width='stretch', hide_index=True)
        else:
            st.info(f"No features added yet for {selected_project_features}")
    
    st.divider()
    
    # Features Summary
    st.divider()
    st.subheader("📦 Features Overview")
    
    all_features = []
    for _, proj in projects_df.iterrows():
        features = get_project_features(proj['id'])
        if len(features) > 0:
            features['project_name'] = proj['name']
            all_features.append(features)
    
    if all_features:
        all_features_df = pd.concat(all_features, ignore_index=True)
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Features", len(all_features_df))
        with col2:
            completed = len(all_features_df[all_features_df['status'] == 'Completed'])
            st.metric("Completed", completed)
        with col3:
            in_progress = len(all_features_df[all_features_df['status'] == 'In Progress'])
            st.metric("In Progress", in_progress)
        with col4:
            blocked = len(all_features_df[all_features_df['status'] == 'Blocked'])
            st.metric("Blocked", blocked)
        
        # Features by status
        col1, col2 = st.columns(2)
        
        with col1:
            status_counts = all_features_df['status'].value_counts()
            fig_status = px.pie(
                values=status_counts.values,
                names=status_counts.index,
                title="Features by Status",
                color_discrete_map={
                    'Completed': '#00C851',
                    'In Progress': '#0099CC',
                    'Pending': '#FF8800',
                    'Blocked': '#FF4444'
                }
            )
            st.plotly_chart(fig_status, width='stretch')
        
        with col2:
            # Features timeline
            all_features_df['delivery_dt'] = pd.to_datetime(all_features_df['delivery_date'])
            all_features_df['days_to_delivery'] = (all_features_df['delivery_dt'] - datetime.now()).dt.days
            all_features_df['overdue'] = all_features_df['days_to_delivery'] < 0
            
            overdue_count = all_features_df['overdue'].sum()
            upcoming_count = ((all_features_df['days_to_delivery'] >= 0) & (all_features_df['days_to_delivery'] <= 7)).sum()
            
            fig_timeline = go.Figure(data=[
                go.Bar(
                    x=['Overdue', 'Due This Week', 'Future'],
                    y=[overdue_count, upcoming_count, len(all_features_df) - overdue_count - upcoming_count],
                    marker_color=['#e74c3c', '#f39c12', '#2ecc71']
                )
            ])
            fig_timeline.update_layout(title="Features Delivery Timeline", showlegend=False)
            st.plotly_chart(fig_timeline, width='stretch')

st.divider()

# Individual Project Deep Dive
if len(projects_df) > 0:
    st.subheader("🔍 Individual Project Analysis")
    
    selected_project = st.selectbox(
        "Select a project to analyze",
        options=projects_df['name'].tolist(),
        key="project_selector"
    )
    
    if selected_project:
        project = projects_df[projects_df['name'] == selected_project].iloc[0]
        targeted = calculate_targeted_progress(project['start_date'], project['end_date'])
        
        st.markdown(f"### {project['name']}")
        st.caption(f"Type: **{project['project_type']}**")
        
        # Detailed metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Current Progress", f"{project['current_progress']}%")
        with col2:
            st.metric("Targeted Progress", f"{targeted}%")
        with col3:
            variance = project['current_progress'] - targeted
            st.metric("Variance", f"{variance:+.0f}%")
        with col4:
            start = datetime.strptime(project['start_date'], "%Y-%m-%d")
            end = datetime.strptime(project['end_date'], "%Y-%m-%d")
            days_remaining = max(0, (end - datetime.now()).days)
            st.metric("Days Remaining", days_remaining)
        
        st.divider()
        
        # Graph 1: Progress Gauge
        col1, col2 = st.columns(2)
        
        with col1:
            fig_gauge = go.Figure(data=[go.Indicator(
                mode = "gauge+number+delta",
                value = project['current_progress'],
                delta = {'reference': targeted, 'relative': False},
                title = {'text': "Current vs Targeted Progress"},
                domain = {'x': [0, 1], 'y': [0, 1]},
                gauge = {
                    'axis': {'range': [None, 100]},
                    'bar': {'color': "darkblue"},
                    'steps': [
                        {'range': [0, 25], 'color': "lightgray"},
                        {'range': [25, 50], 'color': "gray"},
                        {'range': [50, 75], 'color': "lightgreen"},
                        {'range': [75, 100], 'color': "green"}],
                    'threshold': {
                        'line': {'color': "red", 'width': 4},
                        'thickness': 0.75,
                        'value': targeted}}
            )])
            fig_gauge.update_layout(height=300)
            st.plotly_chart(fig_gauge, width='stretch')
        
        with col2:
            # Graph 2: Timeline Progress
            progress_data = pd.DataFrame({
                "Milestone": ["Start", "Today", "End"],
                "Progress": [0, targeted, 100],
                "Status": ["Start", "On Track", "Complete"]
            })
            
            fig_timeline = px.line(
                progress_data,
                x="Milestone",
                y="Progress",
                markers=True,
                title="Expected Progress Timeline",
                line_shape="linear"
            )
            fig_timeline.add_scatter(
                x=["Start", "Today", "End"],
                y=[0, project['current_progress'], 100],
                mode='markers+lines',
                name='Actual Progress',
                marker=dict(size=10, color='red')
            )
            fig_timeline.update_layout(height=300)
            st.plotly_chart(fig_timeline, width='stretch')
        
        st.divider()
        
        # Graph 3: Pie Chart - Progress Distribution
        col1, col2 = st.columns(2)
        
        with col1:
            remaining = 100 - project['current_progress']
            fig_pie = go.Figure(data=[go.Pie(
                labels=['Completed', 'Remaining'],
                values=[project['current_progress'], remaining],
                hole=0.4,
                marker=dict(colors=['#2ecc71', '#e74c3c'])
            )])
            fig_pie.update_layout(title_text="Project Completion", height=350)
            st.plotly_chart(fig_pie, width='stretch')
        
        with col2:
            # Graph 4: Comparison Bar Chart
            comparison_data = pd.DataFrame({
                "Type": ["Current", "Targeted"],
                "Progress": [project['current_progress'], targeted]
            })
            
            fig_bar = px.bar(
                comparison_data,
                x="Type",
                y="Progress",
                color="Type",
                color_discrete_map={"Current": "#0099CC", "Targeted": "#DD33FF"},
                title="Current vs Targeted Progress",
                text="Progress"
            )
            fig_bar.update_traces(textposition='auto')
            fig_bar.update_layout(height=350, showlegend=False)
            st.plotly_chart(fig_bar, width='stretch')

st.divider()

# All Projects Comparison Charts
if len(projects_df) > 0:
    st.subheader("📊 All Projects Comparison")
    
    # Prepare data with targeted progress for all projects
    all_projects_data = projects_df.copy()
    all_projects_data['targeted_progress'] = all_projects_data.apply(
        lambda row: calculate_targeted_progress(row['start_date'], row['end_date']),
        axis=1
    )
    all_projects_data['variance'] = all_projects_data['current_progress'] - all_projects_data['targeted_progress']
    all_projects_data['status'] = all_projects_data.apply(
        lambda row: 'On Track' if row['current_progress'] >= row['targeted_progress'] else 'Behind',
        axis=1
    )
    
    # Graph 1: Multi-project Progress Comparison
    col1, col2 = st.columns(2)
    
    with col1:
        fig_all_bar = go.Figure(data=[
            go.Bar(x=all_projects_data['name'], y=all_projects_data['current_progress'], name='Current'),
            go.Bar(x=all_projects_data['name'], y=all_projects_data['targeted_progress'], name='Targeted')
        ])
        fig_all_bar.update_layout(
            title="All Projects: Current vs Targeted",
            barmode='group',
            height=400,
            xaxis_title="Projects",
            yaxis_title="Progress (%)"
        )
        st.plotly_chart(fig_all_bar, width='stretch')
    
    with col2:
        # Graph 2: Project Status Overview (Scatter)
        fig_scatter = go.Figure()
        
        fig_scatter.add_trace(go.Scatter(
            x=all_projects_data['targeted_progress'],
            y=all_projects_data['current_progress'],
            mode='markers+text',
            marker=dict(
                size=all_projects_data['current_progress'] * 0.5 + 10,
                color=[1 if s == "On Track" else 0 for s in all_projects_data['status']],
                colorscale=[[0, '#e74c3c'], [1, '#2ecc71']],
                showscale=False,
                line=dict(width=2, color='white')
            ),
            text=all_projects_data['name'],
            textposition='top center',
            textfont=dict(size=10, color='black'),
            hovertemplate='<b>%{text}</b><br>Targeted: %{x}%<br>Current: %{y}%<extra></extra>',
            name='Projects'
        ))
        
        # Add diagonal line (perfect progress)
        fig_scatter.add_scatter(
            x=[0, 100],
            y=[0, 100],
            mode='lines',
            name='Perfect Progress',
            line=dict(color='gray', dash='dash'),
            hoverinfo='skip'
        )
        
        fig_scatter.update_layout(
            title="Progress Status Overview",
            xaxis_title="Targeted Progress (%)",
            yaxis_title="Current Progress (%)",
            height=400,
            showlegend=False
        )
        st.plotly_chart(fig_scatter, width='stretch')
    
    st.divider()
    
    # Graph 3: Project Type Distribution with Progress
    col1, col2 = st.columns(2)
    
    with col1:
        type_data = all_projects_data.groupby('project_type').agg({
            'current_progress': 'mean',
            'name': 'count'
        }).reset_index()
        type_data.columns = ['Project Type', 'Avg Progress', 'Count']
        
        fig_type_progress = px.bar(
            type_data,
            x='Project Type',
            y='Avg Progress',
            color='Avg Progress',
            text='Count',
            title="Average Progress by Project Type",
            color_continuous_scale='Plasma'
        )
        fig_type_progress.update_traces(texttemplate='Count: %{text}', textposition='outside')
        fig_type_progress.update_layout(height=400)
        st.plotly_chart(fig_type_progress, width='stretch')
    
    with col2:
        # Graph 4: Variance Analysis
        variance_data = all_projects_data[['name', 'variance']].sort_values('variance')
        colors = ['green' if v >= 0 else 'red' for v in variance_data['variance']]
        
        fig_variance = go.Figure(data=[
            go.Bar(
                y=variance_data['name'],
                x=variance_data['variance'],
                orientation='h',
                marker=dict(color=colors),
                text=variance_data['name'],
                textposition='auto',
                hovertemplate='<b>%{y}</b><br>Variance: %{x:+.0f}%<extra></extra>'
            )
        ])
        fig_variance.update_layout(
            title="Progress Variance (Current - Targeted)",
            xaxis_title="Variance (%)",
            height=400
        )
        st.plotly_chart(fig_variance, width='stretch')
    
    st.divider()
    
    # Graph 5: Timeline View - Projects Gantt-style
    st.subheader("📅 Projects Timeline View")
    
    timeline_data = all_projects_data[['name', 'start_date', 'end_date', 'current_progress']].copy()
    timeline_data['start'] = pd.to_datetime(timeline_data['start_date'])
    timeline_data['end'] = pd.to_datetime(timeline_data['end_date'])
    
    fig_gantt = px.timeline(
        timeline_data,
        x_start='start',
        x_end='end',
        y='name',
        color='current_progress',
        color_continuous_scale='RdYlGn',
        title="Project Timeline",
        labels={'name': 'Project', 'current_progress': 'Progress (%)'},
        height=300
    )
    fig_gantt.update_layout(xaxis_type='date')
    st.plotly_chart(fig_gantt, width='stretch')
    
    st.divider()
    
    # Graph 6: Type Distribution Pie Chart
    col1, col2 = st.columns(2)
    
    with col1:
        type_counts = all_projects_data['project_type'].value_counts()
        fig_type_pie = px.pie(
            values=type_counts.values,
            names=type_counts.index,
            title="Distribution by Project Type",
            color_discrete_sequence=['#0099CC', '#00C851', '#FF8800', '#DD33FF']
        )
        fig_type_pie.update_layout(height=350)
        st.plotly_chart(fig_type_pie, width='stretch')
    
    with col2:
        # Graph 7: Status Distribution
        status_counts = all_projects_data['status'].value_counts()
        fig_status_pie = px.pie(
            values=status_counts.values,
            names=status_counts.index,
            color_discrete_map={"On Track": "#00C851", "Behind": "#FF4444"},
            title="On Track vs Behind"
        )
        fig_status_pie.update_layout(height=350)
        st.plotly_chart(fig_status_pie, width='stretch')
    
    st.divider()
    
    # Data Table: Detailed Project Metrics
    st.subheader("📋 Detailed Project Metrics")
    
    display_data = all_projects_data[[
        'name', 'project_type', 'current_progress', 'targeted_progress', 
        'variance', 'status', 'start_date', 'end_date'
    ]].copy()
    display_data.columns = [
        'Project', 'Type', 'Current (%)', 'Targeted (%)', 
        'Variance (%)', 'Status', 'Start Date', 'End Date'
    ]
    
    st.dataframe(
        display_data,
        width='stretch',
        hide_index=True
    )

    st.divider()

    # ========== NEW: Additional Project Progress Charts ==========
    st.subheader("📈 Project Progress Deep Dive")

    # --- Chart A: Burndown Chart (work remaining per project) ---
    col1, col2 = st.columns(2)

    with col1:
        burndown_data = all_projects_data.copy()
        burndown_data['work_remaining'] = 100 - burndown_data['current_progress']
        burndown_data['start_dt'] = pd.to_datetime(burndown_data['start_date'])
        burndown_data['end_dt'] = pd.to_datetime(burndown_data['end_date'])
        burndown_data['days_total'] = (burndown_data['end_dt'] - burndown_data['start_dt']).dt.days
        burndown_data['days_elapsed'] = (datetime.now() - burndown_data['start_dt']).dt.days.clip(lower=0)

        fig_burndown = go.Figure()

        for _, row in burndown_data.iterrows():
            total_days = max(row['days_total'], 1)
            elapsed = min(row['days_elapsed'], total_days)
            dates = pd.date_range(row['start_dt'], periods=3, freq=f'{int(total_days / 2)}D').tolist()
            if len(dates) < 3:
                dates = [row['start_dt'], datetime.now(), row['end_dt']]

            # Ideal burndown line
            fig_burndown.add_trace(go.Scatter(
                x=[row['start_dt'], row['end_dt']],
                y=[100, 0],
                mode='lines',
                line=dict(dash='dot', width=1, color='gray'),
                showlegend=False,
                hoverinfo='skip'
            ))

            # Actual burndown point
            fig_burndown.add_trace(go.Scatter(
                x=[row['start_dt'], datetime.now()],
                y=[100, row['work_remaining']],
                mode='lines+markers',
                name=row['name'],
                line=dict(width=3),
                marker=dict(size=10),
                hovertemplate=f"<b>{row['name']}</b><br>Date: %{{x|%Y-%m-%d}}<br>Remaining: %{{y:.0f}}%<extra></extra>"
            ))

        now_ts = datetime.now()
        fig_burndown.add_shape(
            type="line", x0=now_ts, x1=now_ts, y0=0, y1=105,
            line=dict(color="blue", dash="dash", width=1)
        )
        fig_burndown.add_annotation(
            x=now_ts, y=105, text="Today", showarrow=False,
            xanchor="left", font=dict(color="blue", size=11)
        )

        fig_burndown.update_layout(
            title="Project Burndown Chart (Work Remaining)",
            xaxis_title="Timeline",
            yaxis_title="Work Remaining (%)",
            height=450,
            yaxis=dict(range=[0, 105]),
            legend=dict(orientation="h", yanchor="bottom", y=-0.3)
        )
        st.plotly_chart(fig_burndown, width='stretch')

    # --- Chart B: Waterfall Chart (progress breakdown) ---
    with col2:
        waterfall_data = all_projects_data.sort_values('current_progress', ascending=False).copy()

        fig_waterfall = go.Figure(go.Waterfall(
            name="Progress",
            orientation="v",
            x=waterfall_data['name'],
            y=waterfall_data['current_progress'],
            connector={"line": {"color": "rgb(63, 63, 63)", "width": 1}},
            text=[f"{v:.0f}%" for v in waterfall_data['current_progress']],
            textposition="outside",
            increasing={"marker": {"color": "#2ecc71"}},
            decreasing={"marker": {"color": "#e74c3c"}},
            totals={"marker": {"color": "#3498db"}},
            measure=["relative"] * len(waterfall_data)
        ))
        fig_waterfall.update_layout(
            title="Project Progress Waterfall",
            yaxis_title="Progress (%)",
            height=450,
            showlegend=False
        )
        st.plotly_chart(fig_waterfall, width='stretch')

    # --- Chart C: Milestone Gantt Chart with progress overlay ---
    st.subheader("🏁 Project Milestone Tracker")

    milestone_data = all_projects_data.copy()
    milestone_data['start_dt'] = pd.to_datetime(milestone_data['start_date'])
    milestone_data['end_dt'] = pd.to_datetime(milestone_data['end_date'])
    milestone_data['days_total'] = (milestone_data['end_dt'] - milestone_data['start_dt']).dt.days
    # Calculate the date up to which progress covers
    milestone_data['progress_end'] = milestone_data.apply(
        lambda r: r['start_dt'] + timedelta(days=int(r['days_total'] * r['current_progress'] / 100)),
        axis=1
    )

    fig_milestone = go.Figure()

    colors_track = {'On Track': '#2ecc71', 'Behind': '#e74c3c'}
    y_positions = list(range(len(milestone_data)))

    for i, (_, row) in enumerate(milestone_data.iterrows()):
        # Full project bar (background)
        fig_milestone.add_trace(go.Bar(
            x=[(row['end_dt'] - row['start_dt']).days],
            y=[row['name']],
            base=[row['start_dt'].timestamp() * 1000],
            orientation='h',
            marker=dict(color='#ecf0f1', line=dict(color='#bdc3c7', width=1)),
            showlegend=False,
            hoverinfo='skip',
            width=0.5
        ))

        # Progress bar (overlay)
        progress_days = (row['progress_end'] - row['start_dt']).days
        bar_color = colors_track.get(row['status'], '#3498db')
        fig_milestone.add_trace(go.Bar(
            x=[progress_days],
            y=[row['name']],
            base=[row['start_dt'].timestamp() * 1000],
            orientation='h',
            marker=dict(color=bar_color),
            showlegend=False,
            hoverinfo='skip',
            width=0.5
        ))

    # Use timeline approach instead for cleaner rendering
    fig_milestone = go.Figure()

    for _, row in milestone_data.iterrows():
        # Full duration (gray background)
        fig_milestone.add_trace(go.Scatter(
            x=[row['start_dt'], row['end_dt']],
            y=[row['name'], row['name']],
            mode='lines',
            line=dict(color='#dfe6e9', width=20),
            showlegend=False,
            hoverinfo='skip'
        ))

        # Progress (colored overlay)
        bar_color = colors_track.get(row['status'], '#3498db')
        fig_milestone.add_trace(go.Scatter(
            x=[row['start_dt'], row['progress_end']],
            y=[row['name'], row['name']],
            mode='lines',
            line=dict(color=bar_color, width=20),
            showlegend=False,
            hovertemplate=f"<b>{row['name']}</b><br>Progress: {row['current_progress']:.0f}%<br>"
                          f"Target: {row['targeted_progress']:.0f}%<br>Status: {row['status']}<extra></extra>"
        ))

        # Milestone markers: start, today-marker, end
        fig_milestone.add_trace(go.Scatter(
            x=[row['start_dt']],
            y=[row['name']],
            mode='markers',
            marker=dict(symbol='diamond', size=10, color='#2c3e50'),
            showlegend=False,
            hovertemplate=f"<b>{row['name']}</b> Start<br>{row['start_date']}<extra></extra>"
        ))
        fig_milestone.add_trace(go.Scatter(
            x=[row['end_dt']],
            y=[row['name']],
            mode='markers',
            marker=dict(symbol='star', size=12, color='#f39c12'),
            showlegend=False,
            hovertemplate=f"<b>{row['name']}</b> Deadline<br>{row['end_date']}<extra></extra>"
        ))

        # Progress percentage label
        fig_milestone.add_annotation(
            x=row['progress_end'],
            y=row['name'],
            text=f" {row['current_progress']:.0f}%",
            showarrow=False,
            xanchor='left',
            font=dict(size=11, color='black', family='Arial Black')
        )

    # Today line
    now_ts = datetime.now()
    fig_milestone.add_shape(
        type="line", x0=now_ts, x1=now_ts, y0=-0.5, y1=len(milestone_data) - 0.5,
        line=dict(color="blue", dash="dash", width=1)
    )
    fig_milestone.add_annotation(
        x=now_ts, y=len(milestone_data) - 0.5, text="Today", showarrow=False,
        xanchor="left", font=dict(color="blue", size=11)
    )

    # Legend entries
    fig_milestone.add_trace(go.Scatter(
        x=[None], y=[None], mode='markers',
        marker=dict(size=10, color='#2ecc71'), name='On Track'
    ))
    fig_milestone.add_trace(go.Scatter(
        x=[None], y=[None], mode='markers',
        marker=dict(size=10, color='#e74c3c'), name='Behind'
    ))
    fig_milestone.add_trace(go.Scatter(
        x=[None], y=[None], mode='markers',
        marker=dict(size=10, color='#dfe6e9'), name='Remaining'
    ))
    fig_milestone.add_trace(go.Scatter(
        x=[None], y=[None], mode='markers',
        marker=dict(symbol='diamond', size=10, color='#2c3e50'), name='Start'
    ))
    fig_milestone.add_trace(go.Scatter(
        x=[None], y=[None], mode='markers',
        marker=dict(symbol='star', size=12, color='#f39c12'), name='Deadline'
    ))

    fig_milestone.update_layout(
        title="Project Milestone Tracker (Progress vs Timeline)",
        xaxis_title="Timeline",
        height=max(350, len(milestone_data) * 80),
        xaxis=dict(type='date'),
        legend=dict(orientation="h", yanchor="bottom", y=-0.2),
        margin=dict(l=10, r=10)
    )
    st.plotly_chart(fig_milestone, width='stretch')

st.divider()

# Advanced Analytics Section
if len(projects_df) > 0:
    st.subheader("🔬 Advanced Analytics & Risk Assessment")
    
    # Prepare extended data for analytics
    analytics_data = all_projects_data.copy()
    
    # Calculate additional metrics
    analytics_data['start_dt'] = pd.to_datetime(analytics_data['start_date'])
    analytics_data['end_dt'] = pd.to_datetime(analytics_data['end_date'])
    analytics_data['days_elapsed'] = (datetime.now() - analytics_data['start_dt']).dt.days
    analytics_data['days_total'] = (analytics_data['end_dt'] - analytics_data['start_dt']).dt.days
    analytics_data['days_remaining'] = (analytics_data['end_dt'] - datetime.now()).dt.days
    
    # Risk scoring (0-100, higher = more risk)
    analytics_data['risk_score'] = analytics_data.apply(
        lambda row: min(100, max(0, abs(row['variance']) * 2 + (50 if row['variance'] < 0 else 0))),
        axis=1
    )
    
    # Completion rate (progress per day)
    analytics_data['completion_rate'] = analytics_data.apply(
        lambda row: row['current_progress'] / max(1, row['days_elapsed']) if row['days_elapsed'] > 0 else 0,
        axis=1
    )
    
    # Projected completion date
    analytics_data['days_to_completion'] = analytics_data.apply(
        lambda row: (100 - row['current_progress']) / max(0.1, row['completion_rate']) if row['completion_rate'] > 0 else 999,
        axis=1
    )
    
    analytics_data['projected_completion'] = analytics_data.apply(
        lambda row: (datetime.now() + timedelta(days=int(row['days_to_completion']))).strftime('%Y-%m-%d'),
        axis=1
    )
    
    # Health status
    analytics_data['health'] = analytics_data.apply(
        lambda row: 'Critical' if row['risk_score'] >= 75 else ('Warning' if row['risk_score'] >= 50 else 'Healthy'),
        axis=1
    )
    
    tab1, tab2, tab3, tab4 = st.tabs(["Risk & Health", "Performance", "Timeline", "Predictive"])
    
    with tab1:
        st.subheader("Risk Assessment & Health Status")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Risk Heatmap
            risk_matrix = analytics_data[['name', 'risk_score', 'health']].sort_values('risk_score', ascending=False)
            
            fig_risk = go.Figure(data=[
                go.Bar(
                    y=risk_matrix['name'],
                    x=risk_matrix['risk_score'],
                    orientation='h',
                    marker=dict(
                        color=risk_matrix['risk_score'],
                        colorscale='Reds',
                        showscale=True,
                        colorbar=dict(title="Risk Score")
                    ),
                    text=risk_matrix['health'],
                    textposition='auto'
                )
            ])
            fig_risk.update_layout(
                title="Project Risk Scores",
                xaxis_title="Risk Level (0-100)",
                height=400
            )
            st.plotly_chart(fig_risk, width='stretch')
        
        with col2:
            # Health Status Distribution
            health_counts = analytics_data['health'].value_counts()
            colors_map = {'Healthy': '#2ecc71', 'Warning': '#f39c12', 'Critical': '#e74c3c'}
            
            fig_health = go.Figure(data=[
                go.Pie(
                    labels=health_counts.index,
                    values=health_counts.values,
                    marker=dict(colors=[colors_map.get(h, '#95a5a6') for h in health_counts.index]),
                    textposition='inside',
                    textinfo='label+percent'
                )
            ])
            fig_health.update_layout(
                title="Projects by Health Status",
                height=400
            )
            st.plotly_chart(fig_health, width='stretch')
        
        # Risk factors breakdown
        st.markdown("**Risk Factors:**")
        risk_details = analytics_data[['name', 'variance', 'risk_score', 'health']].sort_values('risk_score', ascending=False)
        
        for idx, row in risk_details.iterrows():
            health_emoji = '🟢' if row['health'] == 'Healthy' else ('🟡' if row['health'] == 'Warning' else '🔴')
            st.write(f"{health_emoji} **{row['name']}** - Risk: {row['risk_score']:.0f}/100, Variance: {row['variance']:+.0f}%")
    
    with tab2:
        st.subheader("Performance Metrics")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Completion Rate Analysis
            perf_data = analytics_data[['name', 'completion_rate']].sort_values('completion_rate', ascending=False)
            
            fig_perf = px.bar(
                perf_data,
                x='name',
                y='completion_rate',
                color='completion_rate',
                color_continuous_scale='Plasma',
                title="Daily Completion Rate (% per day)",
                labels={'completion_rate': 'Rate (% per day)'}
            )
            fig_perf.update_layout(height=350, showlegend=False)
            st.plotly_chart(fig_perf, width='stretch')
        
        with col2:
            # Efficiency vs Progress
            fig_eff = go.Figure()
            
            fig_eff.add_trace(go.Scatter(
                x=analytics_data['completion_rate'],
                y=analytics_data['current_progress'],
                mode='markers+text',
                marker=dict(
                    size=analytics_data['risk_score'] * 0.5 + 8,
                    color=['#2ecc71' if h == 'Healthy' else ('#f39c12' if h == 'Warning' else '#e74c3c') 
                           for h in analytics_data['health']],
                    line=dict(width=2, color='white')
                ),
                text=analytics_data['name'],
                textposition='top center',
                textfont=dict(size=9),
                hovertemplate='<b>%{text}</b><br>Daily Rate: %{x:.2f}%<br>Progress: %{y:.0f}%<extra></extra>',
                name='Projects'
            ))
            
            fig_eff.update_layout(
                title="Efficiency vs Current Progress",
                xaxis_title="Daily Rate (% per day)",
                yaxis_title="Current Progress (%)",
                height=350,
                showlegend=False
            )
            st.plotly_chart(fig_eff, width='stretch')
        
        # Performance metrics table
        st.markdown("**Detailed Performance Metrics:**")
        perf_table = analytics_data[[
            'name', 'completion_rate', 'days_elapsed', 'days_remaining', 'current_progress'
        ]].copy()
        perf_table.columns = ['Project', 'Daily Rate (%)', 'Days Elapsed', 'Days Remaining', 'Progress (%)']
        perf_table['Daily Rate (%)'] = perf_table['Daily Rate (%)'].round(2)
        st.dataframe(perf_table, width='stretch', hide_index=True)
    
    with tab3:
        st.subheader("Timeline Analysis")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Days remaining vs progress
            timeline_data = analytics_data[['name', 'days_remaining', 'current_progress']].sort_values('days_remaining')
            
            fig_timeline = go.Figure()
            fig_timeline.add_trace(go.Scatter(
                x=timeline_data['days_remaining'],
                y=timeline_data['current_progress'],
                mode='markers+text',
                marker=dict(size=15, color=analytics_data.loc[timeline_data.index, 'risk_score'], 
                           colorscale='Reds', showscale=True),
                text=timeline_data['name'],
                textposition='top center'
            ))
            fig_timeline.update_layout(
                title="Days Remaining vs Current Progress",
                xaxis_title="Days Left",
                yaxis_title="Progress (%)",
                height=350
            )
            st.plotly_chart(fig_timeline, width='stretch')
        
        with col2:
            # Timeline utilization
            util_data = analytics_data[['name', 'days_elapsed', 'days_total']].copy()
            util_data['elapsed_pct'] = (util_data['days_elapsed'] / util_data['days_total'] * 100).clip(0, 100)
            util_data = util_data.sort_values('elapsed_pct', ascending=False)
            
            fig_util = go.Figure()
            fig_util.add_trace(go.Bar(
                y=util_data['name'],
                x=util_data['elapsed_pct'],
                orientation='h',
                name='Time Used',
                marker_color='#3498db'
            ))
            fig_util.add_trace(go.Bar(
                y=util_data['name'],
                x=100 - util_data['elapsed_pct'],
                orientation='h',
                name='Time Remaining',
                marker_color='#ecf0f1'
            ))
            fig_util.update_layout(
                title="Project Timeline Utilization",
                xaxis_title="Timeline %",
                barmode='stack',
                height=350
            )
            st.plotly_chart(fig_util, width='stretch')
    
    with tab4:
        st.subheader("Predictive Analytics")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Projected completion
            pred_data = analytics_data[['name', 'projected_completion', 'end_date']].copy()
            pred_data['on_time'] = pd.to_datetime(pred_data['projected_completion']) <= pd.to_datetime(pred_data['end_date'])
            pred_data = pred_data.sort_values('projected_completion')
            
            fig_pred = go.Figure()
            
            # Scheduled end dates
            fig_pred.add_trace(go.Scatter(
                x=pd.to_datetime(pred_data['end_date']),
                y=pred_data['name'],
                mode='markers',
                name='Scheduled End',
                marker=dict(size=12, color='#3498db', symbol='circle')
            ))
            
            # Projected completion
            fig_pred.add_trace(go.Scatter(
                x=pd.to_datetime(pred_data['projected_completion']),
                y=pred_data['name'],
                mode='markers',
                name='Projected End',
                marker=dict(
                    size=12,
                    color=['#2ecc71' if x else '#e74c3c' for x in pred_data['on_time']],
                    symbol='diamond'
                )
            ))
            
            fig_pred.update_layout(
                title="Scheduled vs Projected Completion",
                xaxis_title="Date",
                height=350
            )
            st.plotly_chart(fig_pred, width='stretch')
        
        with col2:
            # Completion time remaining
            time_data = analytics_data[['name', 'days_to_completion']].sort_values('days_to_completion', ascending=False)
            time_data['status'] = time_data['days_to_completion'].apply(
                lambda x: 'Over Target' if x > 365 else ('On Target' if x > 0 else 'Complete')
            )
            
            fig_time = px.bar(
                time_data,
                x='name',
                y='days_to_completion',
                color='status',
                color_discrete_map={'Over Target': '#FF4444', 'On Target': '#00C851', 'Complete': '#FF6B6B'},
                title="Days Until Completion",
                labels={'days_to_completion': 'Days Remaining'}
            )
            fig_time.update_layout(height=350, showlegend=True)
            st.plotly_chart(fig_time, width='stretch')
        
        # Predictive insights
        st.markdown("**Predictive Insights:**")
        
        on_time_count = (pd.to_datetime(analytics_data['projected_completion']) <= pd.to_datetime(analytics_data['end_date'])).sum()
        at_risk_count = len(analytics_data) - on_time_count
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("On Track (Predicted)", on_time_count)
        with col2:
            st.metric("At Risk (Predicted)", at_risk_count)
        with col3:
            avg_variance = analytics_data['variance'].mean()
            st.metric("Avg Variance", f"{avg_variance:+.1f}%")
        
        # Individual predictions
        for idx, row in analytics_data.iterrows():
            status_emoji = '✅' if pd.to_datetime(row['projected_completion']) <= pd.to_datetime(row['end_date']) else '⚠️'
            days_diff = (pd.to_datetime(row['projected_completion']) - pd.to_datetime(row['end_date'])).days
            st.write(
                f"{status_emoji} **{row['name']}**: Projected finish {abs(days_diff)} days "
                f"{'before' if days_diff <= 0 else 'after'} target ({row['projected_completion']})"
            )
# ========== USER ADOPTION TAB ==========
with tab_adoption:
    st.header("👥 App User Adoption Tracking")
    st.write("Track and compare user adoption metrics across HealthSync, WhatsApp Chatbot, and USSD")
    
    # Define available apps
    available_apps = [
        "HealthSync (Android)",
        "HealthSync (iOS)", 
        "HealthSync (Total)",
        "WhatsApp Chatbot",
        "USSD"
    ]
    
    st.divider()
    
    # Add/Update adoption record
    col1, col2 = st.columns([2, 1])
    with col1:
        st.subheader("📋 Record User Adoption Data")
    
    col1, col2 = st.columns(2)
    with col1:
        selected_app = st.selectbox(
            "Select App",
            [app for app in available_apps if app != "HealthSync (Total)"],
            key="adoption_app_select"
        )
        adoption_date = st.date_input("Date", key="adoption_date")
    with col2:
        num_users = st.number_input("Current Users", min_value=0, value=0, step=100, key="adoption_users")
    
    adoption_notes = st.text_area("Notes (optional)", placeholder="e.g., Weekly active users, significant milestone, etc.", key="adoption_notes", height=60)
    
    if st.button("➕ Record Data", width='stretch', key="add_adoption_btn"):
        if selected_app and adoption_date and num_users >= 0:
            add_adoption(
                selected_app,
                num_users,
                adoption_date.strftime("%Y-%m-%d"),
                adoption_notes
            )
            st.success(f"✅ Recorded {num_users:,} users for {selected_app}")
            st.rerun()
        else:
            st.error("Please fill in the required fields!")
    
    st.divider()
    
    # Get all adoptions
    adoptions_df = get_all_adoptions()
    
    if len(adoptions_df) > 0:
        # Latest adoption date
        latest_date = adoptions_df['adoption_date'].max()
        
        # Overview metrics - latest data
        st.subheader(f"📊 Adoption Overview (as of {latest_date})")
        
        latest_data = adoptions_df[adoptions_df['adoption_date'] == latest_date]
        
        col1, col2, col3, col4, col5 = st.columns(5)
        
        # Calculate HealthSync metrics (with safety checks)
        android_users = 0
        ios_users = 0
        wp_users = 0
        ussd_users = 0
        total_hs = 0
        
        if len(latest_data) > 0 and 'app_name' in latest_data.columns:
            android_filtered = latest_data[latest_data['app_name'] == "HealthSync (Android)"]
            if len(android_filtered) > 0 and 'num_users' in android_filtered.columns:
                android_users = int(android_filtered.iloc[0]['num_users'])
            
            ios_filtered = latest_data[latest_data['app_name'] == "HealthSync (iOS)"]
            if len(ios_filtered) > 0 and 'num_users' in ios_filtered.columns:
                ios_users = int(ios_filtered.iloc[0]['num_users'])
            
            total_hs = android_users + ios_users
            
            wp_filtered = latest_data[latest_data['app_name'] == "WhatsApp Chatbot"]
            if len(wp_filtered) > 0 and 'num_users' in wp_filtered.columns:
                wp_users = int(wp_filtered.iloc[0]['num_users'])
            
            ussd_filtered = latest_data[latest_data['app_name'] == "USSD"]
            if len(ussd_filtered) > 0 and 'num_users' in ussd_filtered.columns:
                ussd_users = int(ussd_filtered.iloc[0]['num_users'])
        
        with col1:
            st.metric("HealthSync Android", f"{android_users:,}")
        with col2:
            st.metric("HealthSync iOS", f"{ios_users:,}")
        with col3:
            st.metric("HealthSync Total", f"{total_hs:,}")
        with col4:
            st.metric("WhatsApp Chatbot", f"{wp_users:,}")
        with col5:
            st.metric("USSD", f"{ussd_users:,}")
        
        st.divider()
        
        # Adoption visualizations
        st.subheader("📈 App Comparison & Analytics")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Latest user count comparison (including calculated HealthSync Total)
            if len(latest_data) > 0 and 'app_name' in latest_data.columns:
                comparison_data = latest_data[['app_name', 'num_users']].copy()
                # Add calculated HealthSync Total
                total_row = pd.DataFrame({
                    'app_name': ['HealthSync (Total)'],
                    'num_users': [total_hs]
                })
                comparison_data = pd.concat([comparison_data, total_row], ignore_index=True)
                comparison_data = comparison_data.sort_values('num_users', ascending=True)
                
                fig_comparison = px.bar(
                    comparison_data,
                    x='num_users',
                    y='app_name',
                    title=f"Current User Count by App ({latest_date})",
                    labels={'app_name': 'App', 'num_users': 'Users'},
                    color='num_users',
                    color_continuous_scale='Plasma',
                    orientation='h'
                )
                fig_comparison.update_layout(height=350, showlegend=False)
                st.plotly_chart(fig_comparison, width='stretch')
            else:
                st.info("No data available yet for comparison chart")
        
        with col2:
            # Growth trend over time
            if len(adoptions_df) > 0 and 'app_name' in adoptions_df.columns:
                adoptions_by_app = []
                for app in available_apps:
                    app_data = adoptions_df[adoptions_df['app_name'] == app].sort_values('adoption_date')
                    if len(app_data) > 0:
                        adoptions_by_app.append(app_data)
                
                if adoptions_by_app:
                    combined_data = pd.concat(adoptions_by_app)
                    
                    fig_trend = px.line(
                        combined_data,
                        x='adoption_date',
                        y='num_users',
                        color='app_name',
                        markers=True,
                        title="User Growth Trend Over Time",
                        labels={'adoption_date': 'Date', 'num_users': 'Users', 'app_name': 'App'},
                        color_discrete_sequence=['#0099CC', '#00C851', '#FF8800', '#FF4444']
                    )
                    fig_trend.update_layout(height=350)
                    st.plotly_chart(fig_trend, width='stretch')
                else:
                    st.info("No historical data yet for trend chart")
            else:
                st.info("No data available yet for trend chart")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Pie chart of current distribution
            if len(latest_data) > 0 and 'app_name' in latest_data.columns:
                pie_data = latest_data.copy()
                
                fig_pie = px.pie(
                    pie_data,
                    values='num_users',
                    names='app_name',
                    title=f"User Distribution by App ({latest_date})",
                    color_discrete_sequence=['#0099CC', '#00C851', '#FF8800', '#FF4444', '#DD33FF']
                )
                fig_pie.update_layout(height=400)
                st.plotly_chart(fig_pie, width='stretch')
            else:
                st.info("No data available yet for distribution chart")
        
        with col2:
            # Historical summary stats
          
            if len(adoptions_df) > 0 and 'app_name' in adoptions_df.columns:
                for app in ["HealthSync (Android)", "HealthSync (iOS)", "WhatsApp Chatbot", "USSD"]:
                    app_data = adoptions_df[adoptions_df['app_name'] == app].sort_values('adoption_date')
                    if len(app_data) > 0:
                        current = int(app_data.iloc[-1]['num_users'])
                        if len(app_data) > 1:
                            previous = int(app_data.iloc[-2]['num_users'])
                            change = current - previous
                            st.metric(app, f"{current:,}", delta=f"{change:+,}")
                        else:
                            st.metric(app, f"{current:,}")
            else:
                st.info("No adoption records yet")
        
        st.divider()
        
        # App-specific history
        st.subheader("📅 App Adoption History")
        
        # Only show apps that have data in the database (exclude HealthSync Total which is calculated)
        editable_apps = [app for app in available_apps if app != "HealthSync (Total)"]
        
        if len(adoptions_df) > 0 and 'app_name' in adoptions_df.columns:
            selected_app_history = st.selectbox(
                "Select App to View History",
                editable_apps,
                key="history_app_select"
            )
            
            app_history = adoptions_df[adoptions_df['app_name'] == selected_app_history].sort_values('adoption_date', ascending=False)
            
            if len(app_history) > 0:
                # Stats for this app
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    current_users = int(app_history.iloc[0]['num_users'])
                    st.metric("Current Users", f"{current_users:,}")
                
                with col2:
                    if len(app_history) > 1:
                        prev_users = int(app_history.iloc[1]['num_users'])
                        change = current_users - prev_users
                        st.metric("Change from Previous", f"{change:+,}", delta=change)
                    else:
                        st.metric("Change from Previous", "N/A")
                
                with col3:
                    first_users = int(app_history.iloc[-1]['num_users'])
                    total_growth = current_users - first_users
                    st.metric("Total Growth", f"{total_growth:+,}")
                
                st.divider()
                
                # History table
                history_display = app_history[['adoption_date', 'num_users', 'notes']].copy()
                history_display.columns = ['Date', 'Users', 'Notes']
                
                st.dataframe(
                    history_display,
                    width='stretch',
                    hide_index=True
                )
                
                # Edit/Delete for this app
                st.subheader("✏️ Manage Records")
                
                record_to_modify = st.selectbox(
                    "Select a record to edit or delete",
                    options=range(len(app_history)),
                    format_func=lambda i: f"{app_history.iloc[i]['adoption_date']} - {int(app_history.iloc[i]['num_users']):,} users"
                )
                
                if record_to_modify is not None:
                    record = app_history.iloc[record_to_modify]
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**Date:** {record['adoption_date']}")
                        st.write(f"**Users:** {int(record['num_users']):,}")
                        st.write(f"**Notes:** {record['notes']}" if record['notes'] else "**Notes:** None")
                    
                    with col2:
                        edit_users = st.number_input(
                            "Edit Users",
                            value=int(record['num_users']),
                            step=100
                        )
                        edit_notes = st.text_area("Edit Notes", value=record['notes'] if record['notes'] else "")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("💾 Update Record", width='stretch'):
                            update_adoption(
                                record['id'],
                                selected_app_history,
                                edit_users,
                                record['adoption_date'],
                                edit_notes
                            )
                            st.success("✅ Record updated!")
                            st.rerun()
                    
                    with col2:
                        if st.button("🗑️ Delete Record", width='stretch'):
                            delete_adoption(record['id'])
                            st.success("✅ Record deleted!")
                            st.rerun()
            else:
                st.info(f"No adoption records for {selected_app_history} yet")
        else:
            st.info("👉 No adoption records yet. Add your first records using the form above!")

# ========== TASK UPDATES TIMELINE TAB ==========
with tab_updates:
    st.header("🕒 Project Task Updates & Timeline")
    st.write("Capture task/project updates and monitor progress over time.")

    projects_df = get_all_projects()

    if len(projects_df) == 0:
        st.info("Create at least one project first, then you can start recording updates.")
    else:
        st.subheader("📝 Add Update")

        selected_project_name = st.selectbox(
            "Project",
            options=projects_df['name'].tolist(),
            key="timeline_project_select"
        )

        selected_project_id = int(
            projects_df[projects_df['name'] == selected_project_name].iloc[0]['id']
        )

        col1, col2 = st.columns(2)
        with col1:
            task_name = st.text_input(
                "Task / Workstream",
                placeholder="e.g., API integration, QA testing",
                key="timeline_task_name"
            )
            update_status = st.selectbox(
                "Status",
                ["Not Started", "In Progress", "Blocked", "Completed"],
                index=1,
                key="timeline_status"
            )
        with col2:
            update_date = st.date_input(
                "Update Date",
                value=datetime.now().date(),
                key="timeline_update_date"
            )
            progress_percent = st.slider(
                "Progress (%)",
                0,
                100,
                0,
                key="timeline_progress"
            )

        update_text = st.text_area(
            "Update Details",
            placeholder="Describe what changed, what was completed, blockers, and next step.",
            height=100,
            key="timeline_update_text"
        )

        if st.button("➕ Save Update", key="timeline_save_update"):
            if task_name and update_text:
                add_project_update(
                    selected_project_id,
                    task_name,
                    update_text,
                    update_status,
                    progress_percent,
                    update_date.strftime("%Y-%m-%d")
                )
                st.success("✅ Update saved successfully!")
                st.rerun()
            else:
                st.error("Please provide both task/workstream and update details.")

        st.divider()

        st.subheader("📈 Update Timeline")

        updates_df = get_project_updates()

        if len(updates_df) == 0:
            st.info("No updates captured yet. Add your first update above.")
        else:
            col1, col2 = st.columns(2)
            with col1:
                view_project = st.selectbox(
                    "View Project",
                    options=["All Projects"] + projects_df['name'].tolist(),
                    key="timeline_view_project"
                )
            with col2:
                all_tasks = sorted(updates_df['task_name'].dropna().unique().tolist())
                view_task = st.selectbox(
                    "View Task / Workstream",
                    options=["All Tasks"] + all_tasks,
                    key="timeline_view_task"
                )

            filtered_updates = updates_df.copy()

            if view_project != "All Projects":
                filtered_updates = filtered_updates[filtered_updates['project_name'] == view_project]

            if view_task != "All Tasks":
                filtered_updates = filtered_updates[filtered_updates['task_name'] == view_task]

            if len(filtered_updates) == 0:
                st.warning("No updates found for the selected filters.")
            else:
                filtered_updates['update_date'] = pd.to_datetime(filtered_updates['update_date'])
                filtered_updates = filtered_updates.sort_values('update_date')

                latest_update = filtered_updates.iloc[-1]
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Latest Progress", f"{int(latest_update['progress_percent'])}%")
                with col2:
                    st.metric("Latest Status", latest_update['status'])
                with col3:
                    st.metric("Total Updates", len(filtered_updates))

                timeline_title = "Progress Over Time"
                if view_project != "All Projects":
                    timeline_title += f" - {view_project}"
                if view_task != "All Tasks":
                    timeline_title += f" ({view_task})"

                fig_timeline = px.line(
                    filtered_updates,
                    x='update_date',
                    y='progress_percent',
                    color='task_name' if view_task == "All Tasks" else None,
                    markers=True,
                    title=timeline_title,
                    labels={
                        'update_date': 'Update Date',
                        'progress_percent': 'Progress (%)',
                        'task_name': 'Task / Workstream'
                    }
                )
                fig_timeline.update_layout(height=380, yaxis_range=[0, 100])
                st.plotly_chart(fig_timeline, width='stretch')

                timeline_display = filtered_updates.sort_values('update_date', ascending=False)[
                    ['update_date', 'project_name', 'task_name', 'status', 'progress_percent', 'update_text']
                ].copy()
                timeline_display.columns = ['Date', 'Project', 'Task / Workstream', 'Status', 'Progress (%)', 'Update']
                timeline_display['Date'] = timeline_display['Date'].dt.strftime("%Y-%m-%d")

                st.dataframe(timeline_display, width='stretch', hide_index=True)