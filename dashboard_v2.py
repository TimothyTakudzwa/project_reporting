import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

from database import (
    init_db,
    add_project,
    get_all_projects,
    update_project,
    delete_project,
    calculate_targeted_progress,
    add_feature,
    get_project_features,
    delete_feature,
    add_adoption,
    get_all_adoptions,
    delete_adoption,
    add_project_update,
    get_project_updates,
)

PROJECT_TYPES = ["AI", "RPA", "Software Development", "Innovation"]
FEATURE_STATUS = ["Pending", "In Progress", "Completed", "Blocked"]
UPDATE_STATUS = ["Not Started", "In Progress", "At Risk", "Completed", "Blocked"]


@st.cache_data(ttl=60)
def load_projects() -> pd.DataFrame:
    return get_all_projects()


@st.cache_data(ttl=60)
def load_adoptions() -> pd.DataFrame:
    return get_all_adoptions()


@st.cache_data(ttl=60)
def load_updates() -> pd.DataFrame:
    return get_project_updates()


def reset_cached_data() -> None:
    load_projects.clear()
    load_adoptions.clear()
    load_updates.clear()


def project_metrics(projects_df: pd.DataFrame) -> pd.DataFrame:
    if projects_df.empty:
        return projects_df

    metrics_df = projects_df.copy()
    metrics_df["target_progress"] = metrics_df.apply(
        lambda row: calculate_targeted_progress(row["start_date"], row["end_date"]),
        axis=1,
    )
    metrics_df["variance"] = metrics_df["current_progress"] - metrics_df["target_progress"]

    today = pd.Timestamp.today().normalize()
    metrics_df["end_date_dt"] = pd.to_datetime(metrics_df["end_date"], errors="coerce")
    metrics_df["days_remaining"] = (metrics_df["end_date_dt"] - today).dt.days

    conditions = [
        metrics_df["variance"] >= 5,
        (metrics_df["variance"] > -5) & (metrics_df["variance"] < 5),
        metrics_df["variance"] <= -5,
    ]
    labels = ["On Track", "Watch", "At Risk"]
    metrics_df["health"] = np.select(conditions, labels, default="Watch")

    metrics_df["attention_required"] = (
        (metrics_df["health"] == "At Risk") | (metrics_df["days_remaining"] < 0)
    )
    return metrics_df


def render_header() -> None:
    st.title("📊 Project Reporting Dashboard")
    st.caption(
        "Professional portfolio view with grouped data, governance-focused navigation, and action-oriented reporting."
    )


def render_overview(metrics_df: pd.DataFrame) -> None:
    st.subheader("Executive Overview")

    if metrics_df.empty:
        st.info("No projects available yet. Add projects in Admin Center.")
        return

    total_projects = len(metrics_df)
    on_track = int((metrics_df["health"] == "On Track").sum())
    at_risk = int((metrics_df["health"] == "At Risk").sum())
    overdue = int((metrics_df["days_remaining"] < 0).sum())

    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    kpi1.metric("Total Projects", total_projects)
    kpi2.metric("On Track", on_track)
    kpi3.metric("At Risk", at_risk)
    kpi4.metric("Overdue", overdue)

    c1, c2 = st.columns(2)

    with c1:
        by_type = (
            metrics_df.groupby("project_type", as_index=False)
            .agg(avg_current=("current_progress", "mean"), avg_target=("target_progress", "mean"))
            .sort_values("project_type")
        )
        fig = px.bar(
            by_type.melt(id_vars="project_type", var_name="metric", value_name="value"),
            x="project_type",
            y="value",
            color="metric",
            barmode="group",
            title="Current vs Target Progress by Project Type",
            labels={"value": "Progress (%)", "project_type": "Project Type"},
        )
        st.plotly_chart(fig, width="stretch")

    with c2:
        health_summary = (
            metrics_df.groupby(["project_type", "health"], as_index=False)
            .size()
            .rename(columns={"size": "count"})
        )
        fig = px.bar(
            health_summary,
            x="project_type",
            y="count",
            color="health",
            title="Portfolio Health Distribution",
            color_discrete_map={"On Track": "#2E7D32", "Watch": "#F9A825", "At Risk": "#C62828"},
        )
        st.plotly_chart(fig, width="stretch")

    st.markdown("#### Priority Action Register")
    action_df = metrics_df[metrics_df["attention_required"]].copy()
    if action_df.empty:
        st.success("No urgent interventions required.")
    else:
        st.dataframe(
            action_df[
                [
                    "name",
                    "project_type",
                    "current_progress",
                    "target_progress",
                    "variance",
                    "days_remaining",
                    "health",
                ]
            ]
            .sort_values(["health", "days_remaining"]),
            width="stretch",
            hide_index=True,
        )


def render_projects(metrics_df: pd.DataFrame) -> None:
    st.subheader("Project Portfolio")

    if metrics_df.empty:
        st.info("No projects available yet.")
        return

    left, right = st.columns([2, 1])
    with left:
        selected_types = st.multiselect(
            "Filter by project type",
            options=sorted(metrics_df["project_type"].unique().tolist()),
            default=sorted(metrics_df["project_type"].unique().tolist()),
        )
    with right:
        selected_health = st.multiselect(
            "Filter by health",
            options=["On Track", "Watch", "At Risk"],
            default=["On Track", "Watch", "At Risk"],
        )

    filtered_df = metrics_df[
        metrics_df["project_type"].isin(selected_types) & metrics_df["health"].isin(selected_health)
    ]

    if filtered_df.empty:
        st.warning("No projects match current filters.")
        return

    for project_type, group in filtered_df.sort_values("name").groupby("project_type"):
        with st.expander(f"{project_type} ({len(group)})", expanded=True):
            for _, project in group.iterrows():
                pcol1, pcol2, pcol3 = st.columns([2, 2, 1])

                with pcol1:
                    st.markdown(f"**{project['name']}**")
                    st.caption(f"Health: {project['health']}")
                    st.progress(
                        max(min(project["current_progress"] / 100, 1.0), 0.0),
                        text=f"Current {project['current_progress']}% | Target {project['target_progress']}%",
                    )

                with pcol2:
                    feature_df = get_project_features(project["id"])
                    total_features = len(feature_df)
                    completed_features = (
                        int((feature_df["status"] == "Completed").sum()) if not feature_df.empty else 0
                    )
                    st.metric("Features Completed", f"{completed_features}/{total_features}")
                    st.caption(
                        f"Start {project['start_date']} • End {project['end_date']} • Days remaining: {int(project['days_remaining']) if pd.notna(project['days_remaining']) else 'N/A'}"
                    )

                with pcol3:
                    st.metric("Variance", f"{project['variance']:+.0f}%")
                    if project["attention_required"]:
                        st.error("Needs attention")
                    else:
                        st.success("Stable")


def render_features(metrics_df: pd.DataFrame) -> None:
    st.subheader("Feature Delivery")

    if metrics_df.empty:
        st.info("No projects available yet.")
        return

    project_options = ["All Projects"] + metrics_df["name"].tolist()
    selected_project = st.selectbox("Project scope", project_options)

    feature_frames = []
    if selected_project == "All Projects":
        for _, project in metrics_df.iterrows():
            feature_df = get_project_features(project["id"])
            if not feature_df.empty:
                feature_df = feature_df.copy()
                feature_df["project_name"] = project["name"]
                feature_frames.append(feature_df)
    else:
        project_row = metrics_df[metrics_df["name"] == selected_project].iloc[0]
        feature_df = get_project_features(int(project_row["id"]))
        if not feature_df.empty:
            feature_df = feature_df.copy()
            feature_df["project_name"] = selected_project
            feature_frames.append(feature_df)

    if not feature_frames:
        st.info("No features found for the selected scope.")
        return

    all_features = pd.concat(feature_frames, ignore_index=True)
    all_features["delivery_date_dt"] = pd.to_datetime(all_features["delivery_date"], errors="coerce")
    all_features["days_to_delivery"] = (
        all_features["delivery_date_dt"] - pd.Timestamp.today().normalize()
    ).dt.days

    c1, c2 = st.columns(2)
    with c1:
        status_dist = all_features.groupby("status", as_index=False).size().rename(columns={"size": "count"})
        fig = px.pie(status_dist, names="status", values="count", title="Feature Status Distribution")
        st.plotly_chart(fig, width="stretch")

    with c2:
        delivery_bucket = pd.cut(
            all_features["days_to_delivery"],
            bins=[-99999, -1, 7, 99999],
            labels=["Overdue", "Due in 7 Days", "Future"],
        )
        bucket_df = delivery_bucket.value_counts(dropna=False).rename_axis("bucket").reset_index(name="count")
        fig = px.bar(bucket_df, x="bucket", y="count", title="Delivery Urgency")
        st.plotly_chart(fig, width="stretch")

    st.dataframe(
        all_features[
            ["project_name", "feature_name", "status", "delivery_date", "days_to_delivery"]
        ].sort_values(["days_to_delivery", "status"]),
        width="stretch",
        hide_index=True,
    )


def render_adoption() -> None:
    st.subheader("User Adoption")

    adoption_df = load_adoptions()
    if adoption_df.empty:
        st.info("No adoption records available.")
        return

    adoption_df = adoption_df.copy()
    adoption_df["adoption_date"] = pd.to_datetime(adoption_df["adoption_date"], errors="coerce")

    latest_date = adoption_df["adoption_date"].max()
    latest_total_users = int(adoption_df[adoption_df["adoption_date"] == latest_date]["num_users"].sum())

    k1, k2 = st.columns(2)
    k1.metric("Tracked Apps", adoption_df["app_name"].nunique())
    k2.metric("Users (Latest Snapshot)", latest_total_users)

    trend_df = adoption_df.sort_values("adoption_date")
    fig = px.line(
        trend_df,
        x="adoption_date",
        y="num_users",
        color="app_name",
        markers=True,
        title="Adoption Trend by Application",
    )
    st.plotly_chart(fig, width="stretch")

    st.dataframe(
        trend_df.sort_values(["adoption_date", "app_name"], ascending=[False, True]),
        width="stretch",
        hide_index=True,
    )


def render_updates() -> None:
    st.subheader("Task Updates Timeline")

    updates_df = load_updates()
    if updates_df.empty:
        st.info("No status updates available.")
        return

    updates_df = updates_df.copy()
    updates_df["update_date"] = pd.to_datetime(updates_df["update_date"], errors="coerce")

    project_filter = st.multiselect(
        "Filter by project",
        options=sorted(updates_df["project_name"].unique().tolist()),
        default=sorted(updates_df["project_name"].unique().tolist()),
    )

    status_filter = st.multiselect(
        "Filter by status",
        options=sorted(updates_df["status"].unique().tolist()),
        default=sorted(updates_df["status"].unique().tolist()),
    )

    filtered = updates_df[
        updates_df["project_name"].isin(project_filter) & updates_df["status"].isin(status_filter)
    ]

    if filtered.empty:
        st.warning("No updates match the current filters.")
        return

    fig = px.scatter(
        filtered,
        x="update_date",
        y="project_name",
        color="status",
        size="progress_percent",
        hover_data=["task_name", "update_text"],
        title="Update Timeline",
    )
    st.plotly_chart(fig, width="stretch")

    st.dataframe(
        filtered[
            ["update_date", "project_name", "task_name", "status", "progress_percent", "update_text"]
        ].sort_values("update_date", ascending=False),
        width="stretch",
        hide_index=True,
    )


def render_admin_center(projects_df: pd.DataFrame) -> None:
    st.subheader("Admin Center")
    st.caption("Centralized maintenance for projects, features, adoption records, and status updates.")

    tab1, tab2, tab3, tab4 = st.tabs(
        ["Project Registry", "Feature Registry", "Adoption Registry", "Update Log"]
    )

    with tab1:
        with st.form("add_project_form", clear_on_submit=True):
            st.markdown("**Create Project**")
            name = st.text_input("Project Name")
            project_type = st.selectbox("Project Type", PROJECT_TYPES)
            col1, col2 = st.columns(2)
            with col1:
                start_date = st.date_input("Start Date")
            with col2:
                end_date = st.date_input("End Date")
            progress = st.slider("Current Progress (%)", 0, 100, 0)
            submit = st.form_submit_button("Add Project")

            if submit:
                if not name.strip():
                    st.error("Project name is required.")
                elif start_date >= end_date:
                    st.error("End date must be after start date.")
                else:
                    add_project(
                        name.strip(),
                        project_type,
                        start_date.strftime("%Y-%m-%d"),
                        end_date.strftime("%Y-%m-%d"),
                        progress,
                    )
                    reset_cached_data()
                    st.success("Project added.")
                    st.rerun()

        if not projects_df.empty:
            st.markdown("**Edit / Remove Project**")
            project_name = st.selectbox("Select Project", projects_df["name"].tolist())
            selected = projects_df[projects_df["name"] == project_name].iloc[0]

            with st.form("edit_project_form"):
                edited_name = st.text_input("Project Name", value=selected["name"])
                edited_type = st.selectbox(
                    "Project Type",
                    PROJECT_TYPES,
                    index=PROJECT_TYPES.index(selected["project_type"]),
                )
                c1, c2 = st.columns(2)
                with c1:
                    edited_start = st.date_input(
                        "Start Date",
                        value=pd.to_datetime(selected["start_date"]).date(),
                        key="edited_start",
                    )
                with c2:
                    edited_end = st.date_input(
                        "End Date",
                        value=pd.to_datetime(selected["end_date"]).date(),
                        key="edited_end",
                    )
                edited_progress = st.slider(
                    "Current Progress (%)",
                    0,
                    100,
                    int(selected["current_progress"]),
                    key="edited_progress",
                )

                save_col, del_col = st.columns(2)
                save = save_col.form_submit_button("Save Changes")
                delete = del_col.form_submit_button("Delete Project")

                if save:
                    if edited_start >= edited_end:
                        st.error("End date must be after start date.")
                    else:
                        update_project(
                            int(selected["id"]),
                            edited_name.strip(),
                            edited_type,
                            edited_start.strftime("%Y-%m-%d"),
                            edited_end.strftime("%Y-%m-%d"),
                            edited_progress,
                        )
                        reset_cached_data()
                        st.success("Project updated.")
                        st.rerun()

                if delete:
                    delete_project(int(selected["id"]))
                    reset_cached_data()
                    st.success("Project removed.")
                    st.rerun()

    with tab2:
        if projects_df.empty:
            st.info("Create at least one project before adding features.")
        else:
            project_name = st.selectbox("Project", projects_df["name"].tolist(), key="feature_project")
            project_id = int(projects_df[projects_df["name"] == project_name].iloc[0]["id"])

            with st.form("add_feature_form", clear_on_submit=True):
                feature_name = st.text_input("Feature Name")
                delivery_date = st.date_input("Delivery Date")
                status = st.selectbox("Status", FEATURE_STATUS)
                submit_feature = st.form_submit_button("Add Feature")

                if submit_feature:
                    if not feature_name.strip():
                        st.error("Feature name is required.")
                    else:
                        add_feature(
                            project_id,
                            feature_name.strip(),
                            delivery_date.strftime("%Y-%m-%d"),
                            status,
                        )
                        reset_cached_data()
                        st.success("Feature added.")
                        st.rerun()

            features_df = get_project_features(project_id)
            if not features_df.empty:
                st.markdown("**Existing Features**")
                for _, feature in features_df.iterrows():
                    with st.container(border=True):
                        st.write(f"{feature['feature_name']} • {feature['status']} • Due {feature['delivery_date']}")
                        if st.button("Delete", key=f"del_feature_{feature['id']}"):
                            delete_feature(int(feature["id"]))
                            reset_cached_data()
                            st.success("Feature removed.")
                            st.rerun()

    with tab3:
        with st.form("adoption_form", clear_on_submit=True):
            app_name = st.text_input("Application Name")
            num_users = st.number_input("Number of Users", min_value=0, value=0)
            adoption_date = st.date_input("Adoption Date")
            notes = st.text_area("Notes")
            submit_adoption = st.form_submit_button("Save Adoption Record")

            if submit_adoption:
                if not app_name.strip():
                    st.error("Application name is required.")
                else:
                    add_adoption(
                        app_name.strip(),
                        int(num_users),
                        adoption_date.strftime("%Y-%m-%d"),
                        notes.strip(),
                    )
                    reset_cached_data()
                    st.success("Adoption record saved.")
                    st.rerun()

        adoption_df = load_adoptions()
        if not adoption_df.empty:
            to_delete = st.selectbox(
                "Delete Record",
                options=adoption_df["id"].tolist(),
                format_func=lambda record_id: (
                    f"{adoption_df[adoption_df['id'] == record_id].iloc[0]['app_name']}"
                    f" • {adoption_df[adoption_df['id'] == record_id].iloc[0]['adoption_date']}"
                ),
            )
            if st.button("Delete Adoption Record"):
                delete_adoption(int(to_delete))
                reset_cached_data()
                st.success("Adoption record deleted.")
                st.rerun()

    with tab4:
        if projects_df.empty:
            st.info("Create a project before logging updates.")
        else:
            with st.form("update_form", clear_on_submit=True):
                project_name = st.selectbox("Project", projects_df["name"].tolist(), key="update_project")
                project_id = int(projects_df[projects_df["name"] == project_name].iloc[0]["id"])
                task_name = st.text_input("Task Name")
                update_text = st.text_area("Update")
                status = st.selectbox("Status", UPDATE_STATUS)
                progress_percent = st.slider("Progress (%)", 0, 100, 0)
                update_date = st.date_input("Update Date")
                submit_update = st.form_submit_button("Log Update")

                if submit_update:
                    if not task_name.strip() or not update_text.strip():
                        st.error("Task name and update details are required.")
                    else:
                        add_project_update(
                            project_id,
                            task_name.strip(),
                            update_text.strip(),
                            status,
                            progress_percent,
                            update_date.strftime("%Y-%m-%d"),
                        )
                        reset_cached_data()
                        st.success("Update logged.")
                        st.rerun()


def run_dashboard() -> None:
    st.set_page_config(
        page_title="Project Reporting Dashboard",
        page_icon="📊",
        layout="wide",
    )
    init_db()

    render_header()

    projects_df = load_projects()
    metrics_df = project_metrics(projects_df)

    with st.sidebar:
        st.header("Navigation")
        page = st.radio(
            "Go to",
            [
                "Overview",
                "Projects",
                "Features",
                "Adoption",
                "Updates",
                "Admin Center",
            ],
        )
        st.divider()
        st.caption("Data grouped by business domain for faster reporting and cleaner governance.")

    if page == "Overview":
        render_overview(metrics_df)
    elif page == "Projects":
        render_projects(metrics_df)
    elif page == "Features":
        render_features(metrics_df)
    elif page == "Adoption":
        render_adoption()
    elif page == "Updates":
        render_updates()
    else:
        render_admin_center(projects_df)
