import os
import streamlit as st
import pandas as pd
from typing import Optional

from application.model.services.summarization_service import (
    SummarizationService,
    StudentFilter,
)
from application.model.services.file_system import FileSystemService


def _get_emotion_column(df: pd.DataFrame) -> Optional[str]:
    for col in df.columns:
        if isinstance(col, str) and col.strip().lower().startswith("how do you feel about the course so far?"):
            return col
    return None


def run_summarization_tab():
    base_path = os.path.join("application", "model", "reflections")
    fs = FileSystemService(base_path)
    svc = SummarizationService(base_path)

    course_name = st.session_state.get("current_course_folder")
    reflection_folder = st.session_state.get("current_reflection_folder")

    if not course_name or not reflection_folder:
        st.warning("Please select a course and reflection first in the Workflow tab.")
        return

    st.subheader(f"Summarization for {course_name} - {reflection_folder}")

    reflection_df, grades_df, exploded_df = svc.load_available_data(course_name, reflection_folder)

    # Global toggle to disable AI for testing
    testing_mode = st.checkbox(
        "Testing mode: disable AI generation",
        value=False,
        help="When enabled, AI-based generation buttons are disabled so you can test filters and UI without triggering slow LLM calls.",
        key="summ_testing_mode",
    )

    with st.expander("Preview Available Data", expanded=False):
        if reflection_df is not None:
            st.caption("Reflections (head)")
            st.dataframe(reflection_df.head())
        if grades_df is not None:
            st.caption("Grades (head)")
            st.dataframe(grades_df.head())
        if exploded_df is not None:
            st.caption("Topic Analysis (exploded head)")
            st.dataframe(exploded_df.head())

    tabs = st.tabs(["Complete Summary", "Topic Summaries", "Student Summaries"]) 

    # -------------------------- Complete Summary --------------------------
    with tabs[0]:
        st.markdown("Create an executive, actionable summary across reflections, topics, and grades.")
        if testing_mode:
            st.info("Testing mode is ON. AI-based complete summary is disabled.")
        else:
            if st.button("Generate Complete Summary", key="btn_complete_summary"):
                with st.spinner("Generating complete summary..."):
                    html = svc.build_complete_summary_html(course_name, reflection_folder)
                    st.components.v1.html(html, height=600, scrolling=True)

    # -------------------------- Topic Summaries ----------------------------
    with tabs[1]:
        st.markdown("Summarize by specific topics from prior Topic Analysis.")
        available_topics = []
        if exploded_df is not None and not exploded_df.empty and "primary_labels_selected" in exploded_df.columns:
            available_topics = sorted(exploded_df["primary_labels_selected"].astype(str).unique().tolist())
        selected_topics = st.multiselect("Topics", options=available_topics, default=available_topics[:5])
        if testing_mode:
            st.info("Testing mode is ON. AI-based topic summaries are disabled.")
        else:
            if st.button("Generate Topic Summaries", key="btn_topic_summaries"):
                with st.spinner("Generating topic summaries..."):
                    html = svc.build_topic_summaries_html(course_name, reflection_folder, selected_topics=selected_topics or None)
                    st.components.v1.html(html, height=700, scrolling=True)

    # -------------------------- Student Summaries --------------------------
    with tabs[2]:
        st.markdown("Generate per-student action briefs using filters.")
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            min_grade = st.number_input("Min grade", min_value=0.0, max_value=100.0, value=0.0, step=1.0)
        with c2:
            max_grade = st.number_input("Max grade", min_value=0.0, max_value=100.0, value=100.0, step=1.0)
        with c3:
            unresolved_only = st.checkbox("Unresolved only", value=False)
        with c4:
            urgency_levels = []
        if exploded_df is not None and "urgency" in exploded_df.columns:
            urgency_levels = sorted(exploded_df["urgency"].astype(str).dropna().unique().tolist())
        selected_urgencies = st.multiselect("Urgency levels", options=urgency_levels, default=[])

        if not testing_mode:
            if st.button("Generate Student Summaries", key="btn_student_summaries"):
                filt = StudentFilter(
                    min_grade=min_grade,
                    max_grade=max_grade,
                    unresolved_only=unresolved_only,
                    urgency_levels=selected_urgencies or None,
                )
                with st.spinner("Generating student summaries..."):
                    html = svc.build_student_summaries_html(course_name, reflection_folder, student_filter=filt)
                    st.components.v1.html(html, height=800, scrolling=True)
        else:
            st.info("Testing mode is ON. Use the V2 generator below to test filters without AI.")

        # -------------------------- V2: Performance-based filters + AI toggle --------------------------
        st.markdown("---")
        st.markdown("**V2: Performance-based filters and optional AI emails**")
        col_v2_1, col_v2_2 = st.columns([2, 1])
        with col_v2_1:
            perf_choice = st.radio(
                "Performance filter (V2):",
                [
                    "None",
                    "Good in quizzes, weak in assignments (<80)",
                    "Weak in quizzes, good in assignments (<80)",
                ],
                index=0,
                key="perf_filter_v2",
                help="Filters students based on cohort-normalized quiz/assignment percentages (max-per-column = total)."
            )
        with col_v2_2:
            ai_emails = st.checkbox(
                "Generate AI emails (slow)",
                value=False,
                key="ai_emails_v2",
                help="Turn off for faster testing. When on, drafts are generated per student."
            )

        # Map UI string to internal mode
        if perf_choice == "Good in quizzes, weak in assignments (<80)":
            perf_mode_internal = "good_quiz_weak_assignment"
        elif perf_choice == "Weak in quizzes, good in assignments (<80)":
            perf_mode_internal = "weak_quiz_good_assignment"
        else:
            perf_mode_internal = None

        if st.button("Generate Student Summaries (V2)", key="btn_student_summaries_v2"):
            with st.spinner("Generating V2 student summaries..."):
                html_v2 = svc.build_student_summaries_html_v2(
                    course_name,
                    reflection_folder,
                    performance_mode=perf_mode_internal,
                    generate_ai_emails=ai_emails
                )
                st.components.v1.html(html_v2, height=900, scrolling=True)


