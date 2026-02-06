import io
import fitz  # PyMuPDF
from PIL import Image
from squishfile.compressor.pdf import compress_pdf


def _make_test_pdf_with_image() -> bytes:
    """Create a PDF with an embedded large image."""
    doc = fitz.open()
    page = doc.new_page(width=612, height=792)

    # Create a large image and embed it
    img = Image.new("RGB", (800, 600), color="blue")
    for y in range(600):
        for x in range(800):
            img.putpixel((x, y), ((x * 7) % 256, (y * 3) % 256, 128))
    img_buf = io.BytesIO()
    img.save(img_buf, format="JPEG", quality=95)
    img_buf.seek(0)

    rect = fitz.Rect(50, 50, 550, 450)
    page.insert_image(rect, stream=img_buf.getvalue())

    pdf_bytes = doc.tobytes(deflate=True)
    doc.close()
    return pdf_bytes


def test_compress_pdf():
    original = _make_test_pdf_with_image()
    target_size = len(original) // 2
    result = compress_pdf(original, target_size)
    assert len(result["data"]) <= target_size * 1.10  # 10% tolerance for PDFs
    assert result["data"][:5] == b"%PDF-"


def test_skip_small_pdf():
    doc = fitz.open()
    doc.new_page()
    pdf_bytes = doc.tobytes()
    doc.close()
    result = compress_pdf(pdf_bytes, len(pdf_bytes) * 2)
    assert result["skipped"] is True
