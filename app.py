import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

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

# ── Page config (must be first Streamlit call) ──────────────────────────
st.set_page_config(
    page_title="Project Reporting Dashboard",
    page_icon="📊",
    layout="wide",
)
init_db()

# ── Constants ───────────────────────────────────────────────────────────
PROJECT_TYPES = ["AI", "RPA", "Software Development", "Innovation"]
FEATURE_STATUS = ["Pending", "In Progress", "Completed", "Blocked"]
UPDATE_STATUS = ["Not Started", "In Progress", "At Risk", "Completed", "Blocked"]

HEALTH_COLORS = {"On Track": "#2E7D32", "Watch": "#F9A825", "At Risk": "#C62828"}
STATUS_EMOJI = {"Completed": "✅", "In Progress": "🔄", "Pending": "⏳", "Blocked": "🚫"}


# ── Cached loaders ──────────────────────────────────────────────────────
@st.cache_data(ttl=30)
def load_projects() -> pd.DataFrame:
    return get_all_projects()


@st.cache_data(ttl=30)
def load_adoptions() -> pd.DataFrame:
    return get_all_adoptions()


@st.cache_data(ttl=30)
def load_updates() -> pd.DataFrame:
    return get_project_updates()


def bust_cache() -> None:
    load_projects.clear()
    load_adoptions.clear()
    load_updates.clear()


# ── Derived metrics ─────────────────────────────────────────────────────
def enrich_projects(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    m = df.copy()
    m["target"] = m.apply(
        lambda r: calculate_targeted_progress(r["start_date"], r["end_date"]), axis=1
    )
    m["variance"] = m["current_progress"] - m["target"]
    today = pd.Timestamp.today().normalize()
    m["end_dt"] = pd.to_datetime(m["end_date"])
    m["start_dt"] = pd.to_datetime(m["start_date"])
    m["days_left"] = (m["end_dt"] - today).dt.days
    m["total_days"] = (m["end_dt"] - m["start_dt"]).dt.days
    m["elapsed_days"] = (today - m["start_dt"]).dt.days.clip(lower=0)
    m["health"] = np.select(
        [m["variance"] >= 5, m["variance"] <= -5],
        ["On Track", "At Risk"],
        default="Watch",
    )
    m["needs_action"] = (m["health"] == "At Risk") | (m["days_left"] < 0)
    return m


def gather_all_features(metrics: pd.DataFrame) -> pd.DataFrame:
    frames = []
    for _, p in metrics.iterrows():
        feat = get_project_features(p["id"])
        if not feat.empty:
            feat = feat.copy()
            feat["project_name"] = p["name"]
            frames.append(feat)
    if not frames:
        return pd.DataFrame()
    all_f = pd.concat(frames, ignore_index=True)
    all_f["delivery_dt"] = pd.to_datetime(all_f["delivery_date"], errors="coerce")
    all_f["days_to_delivery"] = (all_f["delivery_dt"] - pd.Timestamp.today().normalize()).dt.days
    return all_f


# ═══════════════════════════════════════════════════════════════════════
#  PAGE: Executive Summary
# ═══════════════════════════════════════════════════════════════════════
def page_executive(metrics: pd.DataFrame) -> None:
    st.header("Executive Summary")

    if metrics.empty:
        st.info("No projects yet — add them via **Admin Center**.")
        return

    # ── KPI strip ───────────────────────────────────────────────────────
    total = len(metrics)
    on_track = int((metrics["health"] == "On Track").sum())
    watch = int((metrics["health"] == "Watch").sum())
    at_risk = int((metrics["health"] == "At Risk").sum())
    overdue = int((metrics["days_left"] < 0).sum())
    avg_progress = metrics["current_progress"].mean()
    avg_target = metrics["target"].mean()

    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("Total Projects", total)
    k2.metric("On Track", on_track)
    k3.metric("Watch", watch)
    k4.metric("At Risk", at_risk, delta=f"-{at_risk}" if at_risk else None, delta_color="inverse")
    k5.metric("Overdue", overdue)

    st.divider()

    # ── Portfolio health gauges ─────────────────────────────────────────
    st.subheader("Portfolio Progress Gauges")
    gauge_cols = st.columns(min(len(metrics), 5))
    for i, (_, p) in enumerate(metrics.head(10).iterrows()):
        col = gauge_cols[i % min(len(metrics), 5)]
        color = HEALTH_COLORS.get(p["health"], "#F9A825")
        fig = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=p["current_progress"],
            delta={"reference": p["target"], "relative": False, "valueformat": "+.0f"},
            title={"text": p["name"], "font": {"size": 14}},
            gauge={
                "axis": {"range": [0, 100], "tickwidth": 1},
                "bar": {"color": color},
                "bgcolor": "#f0f0f0",
                "steps": [
                    {"range": [0, p["target"]], "color": "#e8e8e8"},
                ],
                "threshold": {
                    "line": {"color": "#333", "width": 3},
                    "thickness": 0.8,
                    "value": p["target"],
                },
            },
        ))
        fig.update_layout(height=220, margin=dict(t=50, b=10, l=30, r=30))
        col.plotly_chart(fig, use_container_width=True)

    # ── second row if >5 projects ──
    if len(metrics) > 5:
        extra = metrics.iloc[5:10]
        gauge_cols2 = st.columns(len(extra))
        for i, (_, p) in enumerate(extra.iterrows()):
            color = HEALTH_COLORS.get(p["health"], "#F9A825")
            fig = go.Figure(go.Indicator(
                mode="gauge+number+delta",
                value=p["current_progress"],
                delta={"reference": p["target"], "relative": False, "valueformat": "+.0f"},
                title={"text": p["name"], "font": {"size": 14}},
                gauge={
                    "axis": {"range": [0, 100]},
                    "bar": {"color": color},
                    "bgcolor": "#f0f0f0",
                    "steps": [{"range": [0, p["target"]], "color": "#e8e8e8"}],
                    "threshold": {"line": {"color": "#333", "width": 3}, "thickness": 0.8, "value": p["target"]},
                },
            ))
            fig.update_layout(height=220, margin=dict(t=50, b=10, l=30, r=30))
            gauge_cols2[i].plotly_chart(fig, use_container_width=True)

    st.divider()

    # ── Portfolio timeline (Gantt) ──────────────────────────────────────
    st.subheader("Portfolio Timeline")
    gantt_df = metrics[["name", "start_dt", "end_dt", "health", "current_progress"]].copy()
    gantt_df.columns = ["Project", "Start", "End", "Health", "Progress"]
    fig = px.timeline(
        gantt_df,
        x_start="Start",
        x_end="End",
        y="Project",
        color="Health",
        color_discrete_map=HEALTH_COLORS,
        hover_data=["Progress"],
    )
    fig.update_yaxes(autorange="reversed")
    fig.update_layout(height=max(300, len(gantt_df) * 45), margin=dict(l=10, r=10))
    st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # ── Grouped analysis charts ─────────────────────────────────────────
    c1, c2 = st.columns(2)

    with c1:
        st.subheader("Progress by Project Type")
        by_type = (
            metrics.groupby("project_type", as_index=False)
            .agg(
                avg_current=("current_progress", "mean"),
                avg_target=("target", "mean"),
            )
        )
        fig = px.bar(
            by_type.melt(id_vars="project_type", var_name="Metric", value_name="Percent"),
            x="project_type",
            y="Percent",
            color="Metric",
            barmode="group",
            color_discrete_map={"avg_current": "#1976D2", "avg_target": "#90CAF9"},
            labels={"project_type": "Project Type", "Percent": "Avg %"},
        )
        fig.update_layout(height=350)
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        st.subheader("Health Distribution")
        health_counts = metrics["health"].value_counts().reset_index()
        health_counts.columns = ["Health", "Count"]
        fig = px.pie(
            health_counts,
            names="Health",
            values="Count",
            color="Health",
            color_discrete_map=HEALTH_COLORS,
            hole=0.45,
        )
        fig.update_layout(height=350)
        st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # ── Risk matrix ─────────────────────────────────────────────────────
    st.subheader("Risk Matrix — Variance vs Days Remaining")
    fig = px.scatter(
        metrics,
        x="days_left",
        y="variance",
        size=metrics["current_progress"].clip(lower=5),
        color="health",
        text="name",
        color_discrete_map=HEALTH_COLORS,
        labels={"days_left": "Days Remaining", "variance": "Variance (%)"},
    )
    fig.add_hline(y=0, line_dash="dash", line_color="grey")
    fig.add_vline(x=0, line_dash="dash", line_color="grey")
    fig.update_traces(textposition="top center", textfont_size=10)
    fig.update_layout(height=420)
    st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # ── Priority action register ────────────────────────────────────────
    st.subheader("⚠️ Priority Action Register")
    actions = metrics[metrics["needs_action"]].copy()
    if actions.empty:
        st.success("All projects are on track — no interventions required.")
    else:
        st.dataframe(
            actions[["name", "project_type", "current_progress", "target", "variance", "days_left", "health"]]
            .rename(columns={
                "name": "Project",
                "project_type": "Type",
                "current_progress": "Current %",
                "target": "Target %",
                "variance": "Variance",
                "days_left": "Days Left",
                "health": "Health",
            })
            .sort_values(["Health", "Days Left"]),
            use_container_width=True,
            hide_index=True,
        )

    st.divider()

    # ── Completion forecast table ───────────────────────────────────────
    st.subheader("Completion Forecast")
    forecast = metrics[["name", "current_progress", "elapsed_days", "total_days", "days_left"]].copy()
    forecast["daily_rate"] = np.where(
        forecast["elapsed_days"] > 0,
        forecast["current_progress"] / forecast["elapsed_days"],
        0,
    )
    forecast["est_days_to_100"] = np.where(
        forecast["daily_rate"] > 0,
        np.ceil((100 - forecast["current_progress"]) / forecast["daily_rate"]).astype(int),
        np.nan,
    )
    forecast["on_time"] = forecast.apply(
        lambda r: "✅ Yes" if pd.notna(r["est_days_to_100"]) and r["est_days_to_100"] <= max(r["days_left"], 0) else "❌ No",
        axis=1,
    )
    st.dataframe(
        forecast[["name", "current_progress", "daily_rate", "est_days_to_100", "days_left", "on_time"]]
        .rename(columns={
            "name": "Project",
            "current_progress": "Current %",
            "daily_rate": "Daily Rate (%/day)",
            "est_days_to_100": "Est. Days to 100%",
            "days_left": "Days Left",
            "on_time": "Forecast On-Time?",
        }),
        use_container_width=True,
        hide_index=True,
    )


# ═══════════════════════════════════════════════════════════════════════
#  PAGE: Project Portfolio
# ═══════════════════════════════════════════════════════════════════════
def page_projects(metrics: pd.DataFrame) -> None:
    st.header("Project Portfolio")

    if metrics.empty:
        st.info("No projects yet.")
        return

    fl, fr = st.columns([2, 1])
    with fl:
        sel_types = st.multiselect(
            "Filter by type",
            sorted(metrics["project_type"].unique()),
            default=sorted(metrics["project_type"].unique()),
        )
    with fr:
        sel_health = st.multiselect(
            "Filter by health",
            ["On Track", "Watch", "At Risk"],
            default=["On Track", "Watch", "At Risk"],
        )

    view = metrics[metrics["project_type"].isin(sel_types) & metrics["health"].isin(sel_health)]
    if view.empty:
        st.warning("No projects match filters.")
        return

    for ptype, grp in view.sort_values("name").groupby("project_type"):
        with st.expander(f"**{ptype}** ({len(grp)} projects)", expanded=True):
            for _, p in grp.iterrows():
                with st.container(border=True):
                    c1, c2, c3, c4 = st.columns([2.5, 1.5, 1, 1])
                    with c1:
                        st.markdown(f"**{p['name']}**")
                        st.progress(
                            max(min(p["current_progress"] / 100, 1.0), 0.0),
                            text=f"Current {p['current_progress']}%  ·  Target {p['target']}%",
                        )
                    with c2:
                        feat = get_project_features(p["id"])
                        done = int((feat["status"] == "Completed").sum()) if not feat.empty else 0
                        st.metric("Features", f"{done}/{len(feat)}")
                    with c3:
                        st.metric("Variance", f"{p['variance']:+.0f}%")
                    with c4:
                        days = int(p["days_left"]) if pd.notna(p["days_left"]) else 0
                        if days < 0:
                            st.error(f"{abs(days)}d overdue")
                        elif days == 0:
                            st.warning("Due today")
                        else:
                            st.caption(f"📅 {days}d left")
                        badge_color = HEALTH_COLORS.get(p["health"], "#F9A825")
                        st.markdown(
                            f"<span style='background:{badge_color};color:white;padding:2px 10px;border-radius:10px;font-size:12px'>{p['health']}</span>",
                            unsafe_allow_html=True,
                        )


# ═══════════════════════════════════════════════════════════════════════
#  PAGE: Feature Delivery
# ═══════════════════════════════════════════════════════════════════════
def page_features(metrics: pd.DataFrame) -> None:
    st.header("Feature Delivery")

    if metrics.empty:
        st.info("No projects yet.")
        return

    scope = st.selectbox("Project scope", ["All Projects"] + metrics["name"].tolist())

    if scope == "All Projects":
        all_f = gather_all_features(metrics)
    else:
        pid = int(metrics[metrics["name"] == scope].iloc[0]["id"])
        feat = get_project_features(pid)
        if feat.empty:
            st.info("No features for this project.")
            return
        feat = feat.copy()
        feat["project_name"] = scope
        feat["delivery_dt"] = pd.to_datetime(feat["delivery_date"], errors="coerce")
        feat["days_to_delivery"] = (feat["delivery_dt"] - pd.Timestamp.today().normalize()).dt.days
        all_f = feat

    if all_f.empty:
        st.info("No features found.")
        return

    # KPI strip
    total_f = len(all_f)
    done_f = int((all_f["status"] == "Completed").sum())
    overdue_f = int((all_f["days_to_delivery"] < 0).sum())
    blocked_f = int((all_f["status"] == "Blocked").sum())

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Total Features", total_f)
    k2.metric("Completed", done_f)
    k3.metric("Overdue", overdue_f)
    k4.metric("Blocked", blocked_f)

    st.divider()

    c1, c2 = st.columns(2)
    with c1:
        dist = all_f["status"].value_counts().reset_index()
        dist.columns = ["Status", "Count"]
        fig = px.pie(dist, names="Status", values="Count", title="Status Distribution", hole=0.4)
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        buckets = pd.cut(
            all_f["days_to_delivery"],
            bins=[-99999, -1, 7, 30, 99999],
            labels=["Overdue", "≤7 Days", "≤30 Days", "Future"],
        )
        bdf = buckets.value_counts().reset_index()
        bdf.columns = ["Urgency", "Count"]
        fig = px.bar(
            bdf, x="Urgency", y="Count", title="Delivery Urgency",
            color="Urgency",
            color_discrete_map={"Overdue": "#C62828", "≤7 Days": "#F9A825", "≤30 Days": "#1976D2", "Future": "#2E7D32"},
        )
        st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # Gantt of features
    if "project_name" in all_f.columns:
        gantt_data = all_f.copy()
        gantt_data["Start"] = gantt_data["delivery_dt"] - pd.Timedelta(days=14)  # approximate start
        gantt_data["End"] = gantt_data["delivery_dt"]
        fig = px.timeline(
            gantt_data,
            x_start="Start",
            x_end="End",
            y="feature_name",
            color="status",
            hover_data=["project_name", "days_to_delivery"],
            title="Feature Timeline",
            color_discrete_map={"Completed": "#2E7D32", "In Progress": "#1976D2", "Pending": "#F9A825", "Blocked": "#C62828"},
        )
        fig.update_yaxes(autorange="reversed")
        fig.update_layout(height=max(300, len(gantt_data) * 32))
        st.plotly_chart(fig, use_container_width=True)

    st.divider()
    st.subheader("Feature Register")
    st.dataframe(
        all_f[["project_name", "feature_name", "status", "delivery_date", "days_to_delivery"]]
        .sort_values(["days_to_delivery", "status"]),
        use_container_width=True,
        hide_index=True,
    )


# ═══════════════════════════════════════════════════════════════════════
#  PAGE: User Adoption
# ═══════════════════════════════════════════════════════════════════════
def page_adoption() -> None:
    st.header("User Adoption")

    adoption = load_adoptions()
    if adoption.empty:
        st.info("No adoption records. Add them in **Admin Center → Adoption Registry**.")
        return

    adoption = adoption.copy()
    adoption["adoption_date"] = pd.to_datetime(adoption["adoption_date"], errors="coerce")

    latest = adoption["adoption_date"].max()
    latest_users = int(adoption[adoption["adoption_date"] == latest]["num_users"].sum())
    apps = adoption["app_name"].nunique()
    total_records = len(adoption)

    k1, k2, k3 = st.columns(3)
    k1.metric("Tracked Apps", apps)
    k2.metric("Users (Latest Snapshot)", latest_users)
    k3.metric("Total Records", total_records)

    st.divider()

    fig = px.line(
        adoption.sort_values("adoption_date"),
        x="adoption_date",
        y="num_users",
        color="app_name",
        markers=True,
        title="Adoption Trend",
    )
    fig.update_layout(height=400)
    st.plotly_chart(fig, use_container_width=True)

    # per-app summary
    app_latest = (
        adoption.sort_values("adoption_date")
        .groupby("app_name", as_index=False)
        .last()
        [["app_name", "num_users", "adoption_date"]]
    )
    app_latest.columns = ["Application", "Latest Users", "As Of"]
    st.dataframe(app_latest, use_container_width=True, hide_index=True)


# ═══════════════════════════════════════════════════════════════════════
#  PAGE: Task Updates
# ═══════════════════════════════════════════════════════════════════════
def page_updates() -> None:
    st.header("Task Updates Timeline")

    updates = load_updates()
    if updates.empty:
        st.info("No updates logged yet.")
        return

    updates = updates.copy()
    updates["update_date"] = pd.to_datetime(updates["update_date"], errors="coerce")

    pf = st.multiselect(
        "Filter by project",
        sorted(updates["project_name"].unique()),
        default=sorted(updates["project_name"].unique()),
    )
    sf = st.multiselect(
        "Filter by status",
        sorted(updates["status"].unique()),
        default=sorted(updates["status"].unique()),
    )

    view = updates[updates["project_name"].isin(pf) & updates["status"].isin(sf)]
    if view.empty:
        st.warning("No updates match filters.")
        return

    # timeline scatter
    fig = px.scatter(
        view,
        x="update_date",
        y="project_name",
        color="status",
        size="progress_percent",
        hover_data=["task_name", "update_text"],
        title="Update Timeline",
    )
    fig.update_layout(height=400)
    st.plotly_chart(fig, use_container_width=True)

    # progress-over-time line
    if len(view) > 1:
        fig2 = px.line(
            view.sort_values("update_date"),
            x="update_date",
            y="progress_percent",
            color="task_name",
            markers=True,
            title="Progress Over Time by Task",
        )
        fig2.update_layout(height=350, yaxis_range=[0, 105])
        st.plotly_chart(fig2, use_container_width=True)

    st.dataframe(
        view[["update_date", "project_name", "task_name", "status", "progress_percent", "update_text"]]
        .sort_values("update_date", ascending=False),
        use_container_width=True,
        hide_index=True,
    )


# ═══════════════════════════════════════════════════════════════════════
#  PAGE: Admin Center
# ═══════════════════════════════════════════════════════════════════════
def page_admin(projects_df: pd.DataFrame) -> None:
    st.header("Admin Center")
    st.caption("All create / edit / delete operations in one place.")

    tab_proj, tab_feat, tab_adopt, tab_upd = st.tabs(
        ["📁 Project Registry", "📋 Feature Registry", "👥 Adoption Registry", "📝 Update Log"]
    )

    # ── Project Registry ────────────────────────────────────────────────
    with tab_proj:
        with st.form("add_project", clear_on_submit=True):
            st.markdown("**Create Project**")
            name = st.text_input("Project Name")
            ptype = st.selectbox("Type", PROJECT_TYPES)
            c1, c2 = st.columns(2)
            with c1:
                sd = st.date_input("Start Date")
            with c2:
                ed = st.date_input("End Date")
            prog = st.slider("Current Progress (%)", 0, 100, 0)
            if st.form_submit_button("Add Project"):
                if not name.strip():
                    st.error("Name required.")
                elif sd >= ed:
                    st.error("End must be after start.")
                else:
                    add_project(name.strip(), ptype, sd.strftime("%Y-%m-%d"), ed.strftime("%Y-%m-%d"), prog)
                    bust_cache()
                    st.success("Project added.")
                    st.rerun()

        if not projects_df.empty:
            st.divider()
            st.markdown("**Edit / Remove**")
            sel_name = st.selectbox("Select project", projects_df["name"].tolist())
            sel = projects_df[projects_df["name"] == sel_name].iloc[0]
            with st.form("edit_project"):
                en = st.text_input("Name", value=sel["name"])
                et = st.selectbox("Type", PROJECT_TYPES, index=PROJECT_TYPES.index(sel["project_type"]))
                c1, c2 = st.columns(2)
                with c1:
                    es = st.date_input("Start", value=pd.to_datetime(sel["start_date"]).date(), key="es")
                with c2:
                    ee = st.date_input("End", value=pd.to_datetime(sel["end_date"]).date(), key="ee")
                ep = st.slider("Progress (%)", 0, 100, int(sel["current_progress"]), key="ep")
                sc, dc = st.columns(2)
                save = sc.form_submit_button("💾 Save")
                delete = dc.form_submit_button("🗑️ Delete")
                if save:
                    if es >= ee:
                        st.error("End must be after start.")
                    else:
                        update_project(int(sel["id"]), en.strip(), et, es.strftime("%Y-%m-%d"), ee.strftime("%Y-%m-%d"), ep)
                        bust_cache()
                        st.success("Updated.")
                        st.rerun()
                if delete:
                    delete_project(int(sel["id"]))
                    bust_cache()
                    st.success("Deleted.")
                    st.rerun()

    # ── Feature Registry ────────────────────────────────────────────────
    with tab_feat:
        if projects_df.empty:
            st.info("Create a project first.")
        else:
            fp = st.selectbox("Project", projects_df["name"].tolist(), key="fp")
            fpid = int(projects_df[projects_df["name"] == fp].iloc[0]["id"])
            with st.form("add_feat", clear_on_submit=True):
                fn = st.text_input("Feature Name")
                fd = st.date_input("Delivery Date")
                fs = st.selectbox("Status", FEATURE_STATUS)
                if st.form_submit_button("Add Feature"):
                    if not fn.strip():
                        st.error("Name required.")
                    else:
                        add_feature(fpid, fn.strip(), fd.strftime("%Y-%m-%d"), fs)
                        bust_cache()
                        st.success("Added.")
                        st.rerun()

            feats = get_project_features(fpid)
            if not feats.empty:
                st.markdown("**Existing Features**")
                for _, f in feats.iterrows():
                    with st.container(border=True):
                        fc1, fc2 = st.columns([4, 1])
                        fc1.write(f"{STATUS_EMOJI.get(f['status'], '📌')} **{f['feature_name']}** · {f['status']} · Due {f['delivery_date']}")
                        if fc2.button("🗑️", key=f"df_{f['id']}"):
                            delete_feature(int(f["id"]))
                            bust_cache()
                            st.rerun()

    # ── Adoption Registry ───────────────────────────────────────────────
    with tab_adopt:
        with st.form("add_adopt", clear_on_submit=True):
            an = st.text_input("Application Name")
            au = st.number_input("Number of Users", min_value=0, value=0)
            ad = st.date_input("Adoption Date")
            anotes = st.text_area("Notes")
            if st.form_submit_button("Save Record"):
                if not an.strip():
                    st.error("App name required.")
                else:
                    add_adoption(an.strip(), int(au), ad.strftime("%Y-%m-%d"), anotes.strip())
                    bust_cache()
                    st.success("Saved.")
                    st.rerun()

        adopt_df = load_adoptions()
        if not adopt_df.empty:
            st.divider()
            del_id = st.selectbox(
                "Delete record",
                adopt_df["id"].tolist(),
                format_func=lambda rid: f"{adopt_df[adopt_df['id']==rid].iloc[0]['app_name']} · {adopt_df[adopt_df['id']==rid].iloc[0]['adoption_date']}",
            )
            if st.button("Delete Adoption Record"):
                delete_adoption(int(del_id))
                bust_cache()
                st.success("Deleted.")
                st.rerun()

    # ── Update Log ──────────────────────────────────────────────────────
    with tab_upd:
        if projects_df.empty:
            st.info("Create a project first.")
        else:
            with st.form("add_upd", clear_on_submit=True):
                up = st.selectbox("Project", projects_df["name"].tolist(), key="up")
                upid = int(projects_df[projects_df["name"] == up].iloc[0]["id"])
                tn = st.text_input("Task Name")
                ut = st.text_area("Update")
                us = st.selectbox("Status", UPDATE_STATUS)
                upr = st.slider("Progress (%)", 0, 100, 0)
                ud = st.date_input("Update Date")
                if st.form_submit_button("Log Update"):
                    if not tn.strip() or not ut.strip():
                        st.error("Task name and update text required.")
                    else:
                        add_project_update(upid, tn.strip(), ut.strip(), us, upr, ud.strftime("%Y-%m-%d"))
                        bust_cache()
                        st.success("Logged.")
                        st.rerun()


# ═══════════════════════════════════════════════════════════════════════
#  MAIN — sidebar navigation & routing
# ═══════════════════════════════════════════════════════════════════════
def main() -> None:
    # Title
    st.title("📊 Project Reporting Dashboard")

    projects_df = load_projects()
    metrics = enrich_projects(projects_df)

    with st.sidebar:
        st.header("📊 Navigation")
        page = st.radio(
            "Go to",
            [
                "🏠 Executive Summary",
                "📁 Projects",
                "📋 Features",
                "👥 Adoption",
                "📝 Updates",
                "⚙️ Admin Center",
            ],
            label_visibility="collapsed",
        )
        st.divider()
        if not metrics.empty:
            on = int((metrics["health"] == "On Track").sum())
            risk = int((metrics["health"] == "At Risk").sum())
            st.caption(f"✅ {on} on track · ⚠️ {risk} at risk")
        st.caption(f"Last refreshed: {datetime.now().strftime('%H:%M:%S')}")

    if page.startswith("🏠"):
        page_executive(metrics)
    elif page.startswith("📁"):
        page_projects(metrics)
    elif page.startswith("📋"):
        page_features(metrics)
    elif page.startswith("👥"):
        page_adoption()
    elif page.startswith("📝"):
        page_updates()
    else:
        page_admin(projects_df)


if __name__ == "__main__":
    main()
