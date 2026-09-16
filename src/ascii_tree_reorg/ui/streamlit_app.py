import shutil
import tempfile
from pathlib import Path
import streamlit as st

from ascii_tree_reorg.core.auditor import StructureAuditor
from ascii_tree_reorg.core.parser import AsciiTreeParser
from ascii_tree_reorg.engine.reorganizer import DirectoryReorganizer


def run_ui():
    # Resolve project root relative to this UI file: src/ascii_tree_reorg/ui -> root
    project_root = Path(__file__).resolve().parent.parent.parent.parent

    st.set_page_config(page_title="ASCII Tree Reorganizer", layout="wide", page_icon="📁")

    st.title("📁 ASCII Directory Restructurer")
    st.caption("Reorganize flat data and code archives into hierarchical project structures.")

    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("1. Source Files")
        input_method = st.radio(
            "Provide files via:",
            ["Select Existing Folder on Disk", "Upload Loose Files directly"]
        )

        source_dir = None
        if input_method == "Select Existing Folder on Disk":
            default_folder = str((project_root / "data" / "inputs" / "raw_archive").resolve())
            folder_str = st.text_input("Source Directory Path:", value=default_folder)
            if folder_str and Path(folder_str).is_dir():
                source_dir = Path(folder_str)
                item_count = len([f for f in source_dir.rglob("*") if f.is_file()])
                st.success(f"Located folder with {item_count} files.")
            else:
                st.warning("Enter a valid local directory path containing files.")
        else:
            uploaded_files = st.file_uploader(
                "Upload your loose files (.csv, .json, .parquet, .pkl, .py, etc.)",
                accept_multiple_files=True
            )
            if uploaded_files:
                temp_staging = Path(tempfile.mkdtemp(prefix="st_upload_"))
                for uf in uploaded_files:
                    target_file = temp_staging / uf.name
                    target_file.write_bytes(uf.getbuffer())
                source_dir = temp_staging
                st.success(f"Staged {len(uploaded_files)} files for restructuring.")

        st.subheader("2. Destination")
        default_out = str((project_root / "data" / "outputs").resolve())
        dest_str = st.text_input("Where should output root be built?", value=default_out)
        task_name = st.text_input("Task/Run Name:", value="reconstructed_project")
        move_mode = st.checkbox(
            "Move files instead of copying (destructively saves disk space)",
            value=False
        )

    with col2:
        st.subheader("3. ASCII Tree Specification")
        tree_input_mode = st.radio("Tree input format:", ["Paste ASCII Text", "Upload structure.txt"])

        ascii_content = ""
        if tree_input_mode == "Paste ASCII Text":
            ascii_content = st.text_area(
                "Paste ASCII Tree here:",
                height=320,
                value="""my_project/
├── configs/
│   ├── config.yaml
│   └── params.json
├── data/
│   ├── dataset.csv
│   └── records.parquet
├── models/
│   └── model.pkl
└── src/
    └── main.py"""
            )
        else:
            tree_file = st.file_uploader("Upload ASCII text file", type=["txt"])
            if tree_file:
                ascii_content = tree_file.read().decode("utf-8")
                st.text_area("File Preview:", value=ascii_content, height=200, disabled=True)

        indent_width = st.number_input("Indentation pitch (default: 4):", min_value=2, max_value=8, value=4)

    st.divider()

    if st.button("🚀 Reconstruct Directory Structure", type="primary", use_container_width=True):
        if not source_dir or not source_dir.exists():
            st.error("Please provide valid source files first.")
        elif not ascii_content.strip():
            st.error("Please provide the ASCII tree structure.")
        else:
            with tempfile.NamedTemporaryFile("w+", encoding="utf-8", delete=False) as tf:
                tf.write(ascii_content)
                temp_tree_path = Path(tf.name)

            target_root = Path(dest_str) / task_name
            target_root.mkdir(parents=True, exist_ok=True)

            try:
                parser = AsciiTreeParser(temp_tree_path, fallback_width=indent_width)
                nodes = parser.parse()

                reorganizer = DirectoryReorganizer(
                    source_dir=source_dir,
                    target_dir=target_root,
                    move_files=move_mode
                )

                with st.expander("Pre-flight Structural Audit", expanded=False):
                    auditor = StructureAuditor(nodes, reorganizer.source_index)
                    auditor.run_audit()
                    st.info("Structure verification complete.")

                with st.spinner("Building hierarchy and transferring files..."):
                    reorganizer.execute(nodes)

                st.balloons()
                st.success(f"Successfully generated structure at: `{target_root}`")

                st.write("### Resulting Structure on Disk:")
                created_files = [str(p.relative_to(target_root)) for p in target_root.rglob("*")]
                st.code("\n".join(created_files) if created_files else "(Empty)")

            except Exception as e:
                st.error(f"Execution Error: {e}")


if __name__ == "__main__":
    run_ui()