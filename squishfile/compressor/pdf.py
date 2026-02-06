import fitz  # PyMuPDF
from squishfile.compressor.image import compress_image


def compress_pdf(data: bytes, target_size: int) -> dict:
    original_size = len(data)

    if original_size <= target_size:
        return {"data": data, "size": original_size, "skipped": True}

    ratio = target_size / original_size
    doc = fitz.open(stream=data, filetype="pdf")

    # Extract and compress embedded images
    for page_num in range(len(doc)):
        page = doc[page_num]
        image_list = page.get_images(full=True)

        for img_info in image_list:
            xref = img_info[0]
            try:
                base_image = doc.extract_image(xref)
                img_data = base_image["image"]
                img_ext = base_image["ext"]
                img_mime = f"image/{img_ext}"

                img_target = max(1024, int(len(img_data) * ratio))
                compressed = compress_image(img_data, img_mime, img_target)

                if not compressed["skipped"]:
                    # Replace image in PDF using page.replace_image
                    page.replace_image(xref, stream=compressed["data"])
            except Exception:
                continue  # Skip images that can't be processed

    result_bytes = doc.tobytes(deflate=True, garbage=4)
    doc.close()

    return {
        "data": result_bytes,
        "size": len(result_bytes),
        "skipped": False,
    }
