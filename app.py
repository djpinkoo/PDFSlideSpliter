import streamlit as st
import tempfile
import os
from pdf_processor import process_pdf

# Page configuration
st.set_page_config(
    page_title="PDF Slide Splitter | PDFスライド分割ツール",
    page_icon="📄",
    layout="centered"
)

# Load custom CSS
def load_css():
    with open("style.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

load_css()

# Title and description
st.title("PDF Slide Splitter | PDFスライド分割ツール")
st.markdown("""
### English
This application splits PDF pages containing multiple slides into individual pages.
Upload a PDF file where each page contains two slides, and get back a new PDF with each slide on its own page.

### 日本語
このアプリケーションは、複数のスライドが含まれているPDFページを個別のページに分割します。
1ページに2つのスライドが含まれているPDFファイルをアップロードすると、各スライドが独立したページとなった新しいPDFファイルを作成します。
""")

# File upload section
st.subheader("Upload PDF | PDFをアップロード")
uploaded_file = st.file_uploader(
    "Drag and drop your PDF file here | PDFファイルをここにドラッグ＆ドロップしてください",
    type=["pdf"],
    help="Upload a PDF file containing multiple slides per page | 1ページに複数のスライドが含まれているPDFファイルをアップロードしてください"
)

if uploaded_file is not None:
    try:
        # Create progress bar
        progress_bar = st.progress(0)
        status_text = st.empty()

        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            input_path = tmp_file.name

        # Process the PDF
        status_text.text("Processing PDF... PDFを処理中です...")

        def update_progress(progress):
            progress_bar.progress(progress)
            status_text.text(f"Processing... 処理中... {int(progress * 100)}%")

        # Process the PDF and get the output path
        output_path = process_pdf(input_path, progress_callback=update_progress)

        # Read the processed file
        with open(output_path, "rb") as file:
            processed_pdf = file.read()

        # Update status and show download button
        status_text.text("Processing complete! | 処理が完了しました！")
        st.success("PDF has been successfully processed! | PDFの処理が正常に完了しました！")

        # Create download button
        st.download_button(
            label="Download Processed PDF | 処理済みPDFをダウンロード",
            data=processed_pdf,
            file_name="processed_slides.pdf",
            mime="application/pdf"
        )

        # Cleanup temporary files
        os.unlink(input_path)
        os.unlink(output_path)

    except Exception as e:
        st.error(f"An error occurred while processing the PDF | PDFの処理中にエラーが発生しました: {str(e)}")
        if 'input_path' in locals():
            os.unlink(input_path)
        if 'output_path' in locals():
            os.unlink(output_path)

# Footer
st.markdown("---")
st.markdown("""
### Instructions | 使用方法
#### English
1. Upload a PDF file containing two slides per page
2. Wait for the processing to complete
3. Download the processed PDF with each slide on its own page

**Note**: The application works best with PDFs that have clear slide boundaries.

#### 日本語
1. 1ページに2つのスライドが含まれているPDFファイルをアップロードします
2. 処理が完了するまでお待ちください
3. 各スライドが個別のページとなった処理済みPDFをダウンロードします

**注意**: スライドの境界が明確なPDFファイルで最も良い結果が得られます。
""")