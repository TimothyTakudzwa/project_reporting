import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import numpy as np
from database import (
    init_db, add_project, get_all_projects, 
    delete_project, calculate_targeted_progress, update_project,
    add_feature, get_project_features, update_feature, delete_feature, get_project_by_id
)

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
    
    for idx, project in projects_df.iterrows():
        with st.container(border=True):
            col1, col2, col3 = st.columns([2, 3, 1])
            
            with col1:
                st.markdown(f"### {project['name']}")
                st.caption(f"Type: **{project['project_type']}**")
                
                # Show features count
                features = get_project_features(project['id'])
                if len(features) > 0:
                    st.caption(f"📋 Features: {len(features)}")
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
                
                # Display progress comparison
                col2a, col2b = st.columns(2)
                with col2a:
                    st.metric(
                        "Current Progress",
                        f"{project['current_progress']}%"
                    )
                with col2b:
                    st.metric(
                        "Targeted Progress",
                        f"{targeted}%"
                    )
                
                # Progress visualization
                st.write("**Progress Comparison:**")
                progress_data = pd.DataFrame({
                    "Type": ["Current", "Targeted"],
                    "Progress": [project['current_progress'], targeted]
                })
                st.bar_chart(
                    progress_data.set_index("Type"),
                    height=200
                )
            
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
                use_container_width=True
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
    
    # Type breakdown
    st.subheader("Projects by Type")
    type_counts = projects_df['project_type'].value_counts()
    st.bar_chart(type_counts)
    
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
                    'Completed': '#2ecc71',
                    'In Progress': '#3498db',
                    'Pending': '#f39c12',
                    'Blocked': '#e74c3c'
                }
            )
            st.plotly_chart(fig_status, use_container_width=True)
        
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
            st.plotly_chart(fig_timeline, use_container_width=True)

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
            st.plotly_chart(fig_gauge, use_container_width=True)
        
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
            st.plotly_chart(fig_timeline, use_container_width=True)
        
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
            st.plotly_chart(fig_pie, use_container_width=True)
        
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
                color_discrete_map={"Current": "#3498db", "Targeted": "#9b59b6"},
                title="Current vs Targeted Progress",
                text="Progress"
            )
            fig_bar.update_traces(textposition='auto')
            fig_bar.update_layout(height=350, showlegend=False)
            st.plotly_chart(fig_bar, use_container_width=True)

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
        st.plotly_chart(fig_all_bar, use_container_width=True)
    
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
        st.plotly_chart(fig_scatter, use_container_width=True)
    
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
            color_continuous_scale='Viridis'
        )
        fig_type_progress.update_traces(texttemplate='Count: %{text}', textposition='outside')
        fig_type_progress.update_layout(height=400)
        st.plotly_chart(fig_type_progress, use_container_width=True)
    
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
        st.plotly_chart(fig_variance, use_container_width=True)
    
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
    st.plotly_chart(fig_gantt, use_container_width=True)
    
    st.divider()
    
    # Graph 6: Type Distribution Pie Chart
    col1, col2 = st.columns(2)
    
    with col1:
        type_counts = all_projects_data['project_type'].value_counts()
        fig_type_pie = px.pie(
            values=type_counts.values,
            names=type_counts.index,
            title="Distribution by Project Type"
        )
        fig_type_pie.update_layout(height=350)
        st.plotly_chart(fig_type_pie, use_container_width=True)
    
    with col2:
        # Graph 7: Status Distribution
        status_counts = all_projects_data['status'].value_counts()
        fig_status_pie = px.pie(
            values=status_counts.values,
            names=status_counts.index,
            color_discrete_map={"On Track": "#2ecc71", "Behind": "#e74c3c"},
            title="On Track vs Behind"
        )
        fig_status_pie.update_layout(height=350)
        st.plotly_chart(fig_status_pie, use_container_width=True)
    
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
        use_container_width=True,
        hide_index=True
    )

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
            st.plotly_chart(fig_risk, use_container_width=True)
        
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
            st.plotly_chart(fig_health, use_container_width=True)
        
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
                color_continuous_scale='Viridis',
                title="Daily Completion Rate (% per day)",
                labels={'completion_rate': 'Rate (% per day)'}
            )
            fig_perf.update_layout(height=350, showlegend=False)
            st.plotly_chart(fig_perf, use_container_width=True)
        
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
            st.plotly_chart(fig_eff, use_container_width=True)
        
        # Performance metrics table
        st.markdown("**Detailed Performance Metrics:**")
        perf_table = analytics_data[[
            'name', 'completion_rate', 'days_elapsed', 'days_remaining', 'current_progress'
        ]].copy()
        perf_table.columns = ['Project', 'Daily Rate (%)', 'Days Elapsed', 'Days Remaining', 'Progress (%)']
        perf_table['Daily Rate (%)'] = perf_table['Daily Rate (%)'].round(2)
        st.dataframe(perf_table, use_container_width=True, hide_index=True)
    
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
            st.plotly_chart(fig_timeline, use_container_width=True)
        
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
            st.plotly_chart(fig_util, use_container_width=True)
    
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
            st.plotly_chart(fig_pred, use_container_width=True)
        
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
                color_discrete_map={'Over Target': '#e74c3c', 'On Target': '#2ecc71', 'Complete': '#95a5a6'},
                title="Days Until Completion",
                labels={'days_to_completion': 'Days Remaining'}
            )
            fig_time.update_layout(height=350, showlegend=True)
            st.plotly_chart(fig_time, use_container_width=True)
        
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
