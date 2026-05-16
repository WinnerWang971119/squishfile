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


def _make_test_pdf_with_background_and_text() -> bytes:
    """Create a PDF with page text layered over a full-page image."""
    doc = fitz.open()
    page = doc.new_page(width=600, height=800)

    img = Image.new("RGB", (600, 800), color="white")
    for y in range(800):
        for x in range(600):
            img.putpixel((x, y), ((x * 5) % 256, (y * 3) % 256, 128))
    img_buf = io.BytesIO()
    img.save(img_buf, format="JPEG", quality=95)
    img_buf.seek(0)

    page.insert_image(fitz.Rect(0, 0, 600, 800), stream=img_buf.getvalue())
    page.insert_text((72, 110), "Layered page text", fontsize=36, fill=(0, 0, 0))

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


def test_compress_pdf_preserves_background_image_size_for_text_overlay():
    original = _make_test_pdf_with_background_and_text()
    result = compress_pdf(original, len(original) // 2)

    original_doc = fitz.open(stream=original, filetype="pdf")
    compressed_doc = fitz.open(stream=result["data"], filetype="pdf")

    original_image = original_doc[0].get_images(full=True)[0]
    compressed_image = compressed_doc[0].get_images(full=True)[0]

    assert compressed_doc[0].get_text("text").strip() == "Layered page text"
    assert compressed_image[2:4] == original_image[2:4]

    original_doc.close()
    compressed_doc.close()
