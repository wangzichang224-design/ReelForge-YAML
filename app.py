from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parent
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from shortdrama_yaml.chapter_parser import split_chapters  # noqa: E402
from shortdrama_yaml.llm_client import LLMConfig  # noqa: E402
from shortdrama_yaml.pipeline import ConversionOptions, convert_novel_text  # noqa: E402
from shortdrama_yaml.yaml_io import yaml_to_document  # noqa: E402


def main() -> None:
    st.set_page_config(
        page_title="ReelForge YAML",
        page_icon="🎬",
        layout="wide",
    )
    _inject_css()
    _init_state()

    logo_path = PROJECT_ROOT / "assets" / "logo.svg"
    if logo_path.exists():
        st.image(str(logo_path), width=92)
    st.title("ReelForge YAML")
    st.caption("网文转竖屏短剧的结构化改编工作台｜章节 → 分集 → 镜头 → YAML → AI 视频友好提示词")

    settings = _render_sidebar()
    input_tab, generate_tab, eval_tab, editor_tab, export_tab = st.tabs(["输入区", "生成区", "测评与优化", "编辑区", "导出区"])

    with input_tab:
        _render_input_tab()

    with generate_tab:
        _render_generate_tab(settings)

    with eval_tab:
        _render_eval_tab()

    with editor_tab:
        _render_editor_tab()

    with export_tab:
        _render_export_tab()


def _init_state() -> None:
    if "novel_text" not in st.session_state:
        st.session_state["novel_text"] = _read_text(PROJECT_ROOT / "samples" / "sample_novel_three_chapters.txt")
    st.session_state.setdefault("yaml_text", "")
    st.session_state.setdefault("yaml_editor", "")
    st.session_state.setdefault("warnings", [])
    st.session_state.setdefault("document", None)


def _render_sidebar() -> dict:
    st.sidebar.header("生成配置")
    title = st.sidebar.text_input("作品名", value="隐婚风暴")
    genre = st.sidebar.text_input("题材", value="都市逆袭")
    tone = st.sidebar.text_input("短剧语气", value="强冲突、快节奏、爽感反转")
    target_style = st.sidebar.text_area(
        "目标风格",
        value="竖屏短剧，黄金三秒强冲突，人物关系强压迫，每集结尾留钩子。",
        height=90,
    )
    shots_per_episode = st.sidebar.slider("每集镜头数", min_value=10, max_value=15, value=10)

    st.sidebar.divider()
    st.sidebar.subheader("模型配置")
    use_offline_demo = st.sidebar.checkbox("使用离线 Demo 生成器", value=True)
    api_key = st.sidebar.text_input("API Key", value="", type="password", disabled=use_offline_demo)
    base_url = st.sidebar.text_input("Base URL", value="https://api.deepseek.com", disabled=use_offline_demo)
    model = st.sidebar.text_input("Model", value="deepseek-chat", disabled=use_offline_demo)
    temperature = st.sidebar.slider("Temperature", 0.0, 1.0, 0.2, 0.05, disabled=use_offline_demo)
    max_tokens = st.sidebar.number_input(
        "Max tokens",
        min_value=2000,
        max_value=32000,
        value=8000,
        step=1000,
        disabled=use_offline_demo,
    )
    st.sidebar.divider()
    st.sidebar.subheader("评测闭环")
    enable_scratchpad = st.sidebar.checkbox("启用全局视觉黑板", value=True)
    enable_critic_loop = st.sidebar.checkbox("启用 Critic 纠偏", value=False)
    max_critic_rounds = st.sidebar.slider("最多纠偏轮数", 1, 2, 2, disabled=not enable_critic_loop)
    use_llm_critic = st.sidebar.checkbox(
        "使用模型专家评审",
        value=False,
        disabled=use_offline_demo or not enable_critic_loop,
        help="关闭时使用本地硬规则评测；开启后会额外调用模型生成文字评审。",
    )

    return {
        "title": title,
        "genre": genre,
        "tone": tone,
        "target_style": target_style,
        "shots_per_episode": shots_per_episode,
        "llm_config": LLMConfig(
            api_key=api_key,
            base_url=base_url,
            model=model,
            temperature=temperature,
            max_tokens=int(max_tokens),
            use_offline_demo=use_offline_demo,
        ),
        "enable_scratchpad": enable_scratchpad,
        "enable_critic_loop": enable_critic_loop,
        "max_critic_rounds": max_critic_rounds,
        "use_llm_critic": use_llm_critic,
    }


def _render_input_tab() -> None:
    left, right = st.columns([0.68, 0.32], gap="large")
    with left:
        uploaded = st.file_uploader("上传小说 txt 文件", type=["txt", "md"])
        if uploaded is not None:
            st.session_state["novel_text"] = uploaded.read().decode("utf-8", errors="ignore")

        st.session_state["novel_text"] = st.text_area(
            "小说正文（至少 3 章）",
            value=st.session_state["novel_text"],
            height=460,
            help="支持“第1章/第一章/Chapter 1”等章节标题；标题不规范时会尝试按长段落切分。",
        )

    with right:
        st.subheader("章节解析预览")
        parse_result = split_chapters(st.session_state["novel_text"])
        st.metric("识别章节数", len(parse_result.chapters))
        if parse_result.warnings:
            for warning in parse_result.warnings:
                st.warning(warning)
        for chapter in parse_result.chapters[:5]:
            with st.expander(f"{chapter.chapter_id} · {chapter.title}", expanded=False):
                st.write(chapter.text[:360] + ("..." if len(chapter.text) > 360 else ""))


def _render_generate_tab(settings: dict) -> None:
    st.subheader("生成结构化短剧 YAML")
    st.write("生成链路：章节解析 → 剧情抽取 → 短剧改编 → 镜头生成 → Schema 校验 → YAML 导出。")

    if st.button("开始生成 YAML 初稿", type="primary", use_container_width=True):
        progress_bar = st.progress(0.0)
        status_box = st.empty()

        def progress(label: str, value: float) -> None:
            progress_bar.progress(value)
            status_box.info(label)

        try:
            options = ConversionOptions(
                title=settings["title"],
                genre=settings["genre"],
                tone=settings["tone"],
                target_style=settings["target_style"],
                shots_per_episode=settings["shots_per_episode"],
                llm_config=settings["llm_config"],
                enable_scratchpad=settings["enable_scratchpad"],
                enable_critic_loop=settings["enable_critic_loop"],
                max_critic_rounds=settings["max_critic_rounds"],
                use_llm_critic=settings["use_llm_critic"],
            )
            result = convert_novel_text(
                st.session_state["novel_text"],
                options=options,
                progress_callback=progress,
            )
            st.session_state["yaml_text"] = result.yaml_text
            st.session_state["yaml_editor"] = result.yaml_text
            st.session_state["yaml_editor_widget"] = result.yaml_text
            st.session_state["warnings"] = result.warnings
            st.session_state["document"] = result.document
            st.success("生成完成，已通过 Pydantic Schema 校验。")
        except Exception as exc:  # noqa: BLE001 - Streamlit should show actionable error
            st.error(str(exc))

    if st.session_state.get("document"):
        _render_document_preview(st.session_state["document"])


def _render_eval_tab() -> None:
    st.subheader("测评与 Badcase 优化")
    document = st.session_state.get("document")
    if not document:
        st.info("请先生成 YAML；生成后这里会展示 hook、cliffhanger、power shift、视觉可执行性、连续性和来源追溯评分。")
        return
    report = document.quality_report
    if not report:
        st.warning("当前文档没有 quality_report，请重新生成或校验 YAML。")
        return

    score = report.overall_score if report.overall_score is not None else 0
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("综合分", f"{score:.2f}")
    c2.metric("Badcases", len(report.badcases))
    c3.metric("总镜头", report.total_shots)
    c4.metric("结构校验", "通过" if report.schema_valid else "失败")

    if report.episode_scores:
        st.markdown("**分集指标**")
        st.dataframe(
            [
                {
                    "EP": item.episode_number,
                    "Hook": item.hook_score,
                    "Cliffhanger": item.cliffhanger_score,
                    "Power Shift": item.power_shift_score,
                    "Visual": item.visual_executability_score,
                    "Continuity": item.continuity_score,
                    "Provenance": item.provenance_score,
                    "Overall": item.overall_score,
                    "Pass": item.passed,
                }
                for item in report.episode_scores
            ],
            use_container_width=True,
        )

    if report.badcases:
        st.markdown("**Badcase 列表**")
        for badcase in report.badcases:
            with st.expander(f"{badcase.metric} · {badcase.severity} · {badcase.target_path}", expanded=badcase.severity == "high"):
                st.write(f"原因：{badcase.reason}")
                st.write(f"根因：{badcase.root_cause}")
                st.write(f"建议：{badcase.repair_suggestion}")
                if badcase.source_excerpt:
                    st.caption(f"Source: {badcase.source_excerpt}")
    else:
        st.success("没有发现硬规则 badcase。")

    st.markdown("**Cliffhanger 备选方案**")
    for idx, score_item in enumerate(report.episode_scores):
        if idx >= len(document.episodes) or not score_item.cliffhanger_options:
            continue
        episode = document.episodes[idx]
        key = f"cliffhanger_option_{idx}"
        choice = st.radio(
            f"EP{episode.episode_number:02d} · {episode.episode_title}",
            score_item.cliffhanger_options,
            key=key,
        )
        if st.button(f"应用到 EP{episode.episode_number:02d}", key=f"apply_cliff_{idx}"):
            document = _apply_cliffhanger_choice(document, idx, choice)
            st.session_state["document"] = document
            from shortdrama_yaml.evaluator import evaluate_document
            from shortdrama_yaml.yaml_io import document_to_yaml

            report = evaluate_document(document, visual_bible=document.visual_bible)
            document = document.model_copy(update={"quality_report": report})
            st.session_state["document"] = document
            st.session_state["yaml_text"] = document_to_yaml(document)
            st.session_state["yaml_editor"] = st.session_state["yaml_text"]
            st.session_state["yaml_editor_widget"] = st.session_state["yaml_text"]
            st.success("已应用 cliffhanger 备选，并重新生成 YAML。")
            st.rerun()


def _render_editor_tab() -> None:
    st.subheader("YAML 编辑器")
    if not st.session_state.get("yaml_editor"):
        st.info("请先在生成区生成 YAML。")
        return

    edited = st.text_area(
        "可编辑 YAML",
        value=st.session_state["yaml_editor"],
        height=520,
        key="yaml_editor_widget",
    )
    st.session_state["yaml_editor"] = edited

    col1, col2 = st.columns([0.25, 0.75])
    with col1:
        if st.button("校验编辑后的 YAML", use_container_width=True):
            try:
                document = yaml_to_document(st.session_state["yaml_editor"])
                st.session_state["document"] = document
                st.session_state["yaml_text"] = st.session_state["yaml_editor"]
                st.success("编辑后的 YAML 仍然符合 Schema。")
            except Exception as exc:  # noqa: BLE001
                st.error(str(exc))
    with col2:
        if st.session_state.get("warnings"):
            st.caption("质量提醒")
            for warning in st.session_state["warnings"]:
                st.warning(warning)


def _render_export_tab() -> None:
    st.subheader("导出")
    yaml_text = st.session_state.get("yaml_text") or _build_default_sample_yaml()
    schema_doc = _read_text(PROJECT_ROOT / "docs" / "YAML_SCHEMA.md")
    sample_novel = _read_text(PROJECT_ROOT / "samples" / "sample_novel_three_chapters.txt")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.download_button(
            "下载剧本 YAML",
            data=yaml_text,
            file_name="short_drama_script.yaml",
            mime="text/yaml",
            use_container_width=True,
        )
    with col2:
        st.download_button(
            "下载 Schema 文档",
            data=schema_doc,
            file_name="YAML_SCHEMA.md",
            mime="text/markdown",
            use_container_width=True,
        )
    with col3:
        st.download_button(
            "下载示例小说输入",
            data=sample_novel,
            file_name="sample_novel_three_chapters.txt",
            mime="text/plain",
            use_container_width=True,
        )

    st.divider()
    st.code(yaml_text[:6000], language="yaml")


def _render_document_preview(document) -> None:
    st.divider()
    total_shots = sum(len(episode.shots) for episode in document.episodes)
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("角色数", len(document.characters))
    col2.metric("集数", len(document.episodes))
    col3.metric("镜头数", total_shots)
    col4.metric("Source Map", len(document.source_map))

    for episode in document.episodes:
        with st.expander(f"EP{episode.episode_number:02d} · {episode.episode_title}", expanded=episode.episode_number == 1):
            st.markdown(f"**开场钩子**：{episode.hook_summary}")
            st.markdown(f"**情绪曲线**：{' → '.join(episode.emotional_curve)}")
            st.markdown(f"**结尾悬念**：{episode.cliffhanger}")
            for shot in episode.shots:
                st.markdown(
                    f"""
                    <div class="shot-card">
                    <b>{shot.shot_id}</b> · {shot.purpose} · {shot.duration_seconds:.0f}s · {shot.visual_track.framing}<br>
                    <span>{shot.visual_track.visual_notes_zh}</span><br>
                    <code>{shot.visual_track.video_prompt}</code>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )


def _apply_cliffhanger_choice(document, episode_index: int, choice: str):
    from shortdrama_yaml.yaml_io import document_to_yaml, yaml_to_document

    data = document.model_dump(mode="json", exclude_none=True)
    episode = data["episodes"][episode_index]
    episode["cliffhanger"] = choice
    last_shot = episode["shots"][-1]
    last_shot["purpose"] = "cliffhanger"
    last_shot["visual_track"]["visual_notes_zh"] = f"用户选择的结尾钩子：{choice}"
    last_shot["visual_track"]["video_prompt"] = (
        "Close-up shot, sudden cliffhanger reveal, the protagonist freezes while a shocking message or document appears, "
        "dramatic lighting, fast push-in camera, vertical 9:16. "
        f"Cliffhanger concept: {choice}"
    )
    yaml_text = document_to_yaml(document.__class__.model_validate(data))
    return yaml_to_document(yaml_text)


def _read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def _build_default_sample_yaml() -> str:
    try:
        result = convert_novel_text(
            _read_text(PROJECT_ROOT / "samples" / "sample_novel_three_chapters.txt"),
            options=ConversionOptions(
                title="隐婚风暴",
                genre="都市逆袭",
                tone="强冲突、快节奏、爽感反转",
                llm_config=LLMConfig(use_offline_demo=True),
                enable_scratchpad=True,
                enable_critic_loop=True,
            ),
        )
        return result.yaml_text
    except Exception as exc:  # noqa: BLE001
        return f"# 示例 YAML 生成失败：{exc}\n"


def _inject_css() -> None:
    st.markdown(
        """
        <style>
        .stApp { background: #f7f8fb; }
        .shot-card {
            border: 1px solid #d9dee8;
            background: #ffffff;
            border-radius: 8px;
            padding: 12px 14px;
            margin: 10px 0;
            line-height: 1.55;
        }
        .shot-card code {
            white-space: normal;
            color: #334155;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
