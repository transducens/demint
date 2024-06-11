import fitz  # PyMuPDF
import os


class ContentExtractor:
    @staticmethod
    def get_content(folder_path="../pdf_rag", part_count=1, overlap=0):
        paragraphs = []

        # Iterate through all files in the specified folder
        for filename in os.listdir(folder_path):
            if filename.endswith(".pdf"):
                pdf_path = os.path.join(folder_path, filename)
                doc = fitz.open(pdf_path)

                # Iterate through all pages in the document
                for page in doc:
                    text = page.get_text()

                    # Split text into 'part_count' parts with overlapping
                    part_length = len(text) // part_count
                    calculated_overlap = int(part_length * overlap)  # Overlap calculated as a percentage of the part length

                    parts_indexes = []
                    # Generate start and end indexes for each part considering the overlap
                    for i in range(part_count):
                        start = i * part_length - calculated_overlap if i > 0 else 0
                        end = (i + 1) * part_length + calculated_overlap if i < part_count - 1 else len(text)
                        parts_indexes.append((start, end))

                    # Extract parts based on calculated indexes
                    for start_index, end_index in parts_indexes:
                        paragraph = text[start_index:end_index].strip()
                        if paragraph:  # Check to avoid adding empty strings
                            paragraphs.append(paragraph)

        return paragraphs

