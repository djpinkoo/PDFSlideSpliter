import fitz  # PyMuPDF
import cv2
import numpy as np
import tempfile
from pathlib import Path

def detect_slides_in_page(page, zoom_x=4.0, zoom_y=4.0):
    """
    PDFページを画像に変換し、OpenCVで黒枠のスライドを検出する関数。
    戻り値は[(x, y, w, h), ...]という矩形のリスト(PDF座標系)。
    """
    # 1) PDFをPixmapに変換
    mat = fitz.Matrix(zoom_x, zoom_y)
    pix = page.get_pixmap(matrix=mat, alpha=False)

    # 2) PixmapをOpenCV形式に変換
    img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, 3)

    # 3) グレースケール化
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # 4) 二値化
    _, thresh = cv2.threshold(gray, 50, 255, cv2.THRESH_BINARY_INV)

    # 5) 輪郭抽出
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # 6) 大きめの四角形の輪郭のみ抽出
    candidate_boxes = []
    for cnt in contours:
        x, y, w, h = cv2.boundingRect(cnt)
        area = w * h
        if area < 80000:  # 小さすぎるものは除外
            continue
        candidate_boxes.append((x, y, w, h))

    # 7) y座標順にソート
    candidate_boxes.sort(key=lambda box: box[1])

    # 8) 画像座標をPDF座標に変換
    page_w = page.rect.width
    page_h = page.rect.height
    img_w = pix.width
    img_h = pix.height

    pdf_boxes = []
    for (x, y, w, h) in candidate_boxes:
        pdf_x = (x / img_w) * page_w
        pdf_y = (y / img_h) * page_h
        pdf_w = (w / img_w) * page_w
        pdf_h = (h / img_h) * page_h
        pdf_boxes.append((pdf_x, pdf_y, pdf_w, pdf_h))

    return pdf_boxes

def process_pdf(input_file, progress_callback=None):
    """
    PDFを処理し、分割されたPDFを返す
    """
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
        output_path = tmp_file.name
        
        original_doc = fitz.open(input_file)
        new_doc = fitz.open()
        
        total_pages = len(original_doc)
        
        for page_index, page in enumerate(original_doc):
            if progress_callback:
                progress_callback((page_index + 1) / total_pages)
                
            boxes = detect_slides_in_page(page, zoom_x=4.0, zoom_y=4.0)
            
            if len(boxes) >= 2:
                top_box = boxes[0]
                bottom_box = boxes[1]
                
                # 上部スライド用の矩形
                top_rect = fitz.Rect(
                    top_box[0],
                    top_box[1],
                    top_box[0] + top_box[2],
                    top_box[1] + top_box[3]
                )
                
                # 下部スライド用の矩形
                bottom_rect = fitz.Rect(
                    bottom_box[0],
                    bottom_box[1],
                    bottom_box[0] + bottom_box[2],
                    bottom_box[1] + bottom_box[3]
                )
                
                # 上部スライドの処理
                top_page = new_doc.new_page(width=top_rect.width, height=top_rect.height)
                top_page.show_pdf_page(
                    top_page.rect,
                    original_doc,
                    page_index,
                    clip=top_rect
                )
                
                # 下部スライドの処理
                bottom_page = new_doc.new_page(width=bottom_rect.width, height=bottom_rect.height)
                bottom_page.show_pdf_page(
                    bottom_page.rect,
                    original_doc,
                    page_index,
                    clip=bottom_rect
                )
        
        new_doc.save(output_path)
        new_doc.close()
        original_doc.close()
        
        return output_path

