import fitz  # PyMuPDF
import os


class ContentExtractor:
    @staticmethod
    def get_content(folder_path="./pdf_rag", part_count=400, overlap=0.25):
        paragraphs = []

        # Iterate through all files in the specified folder
        for filename in os.listdir(folder_path):
            if filename.endswith(".pdf"):
                pdf_path = os.path.join(folder_path, filename)
                doc = fitz.open(pdf_path)
                content = str()

                for page in doc:
                    text = page.get_text()
                    content += text

                # Iterate through all pages in the document
                idx = 0
                part_length = part_count
                calculated_overlap = int(part_length * overlap)  # Overlap calculated as a percentage of the part length
                start = end = idx
                while idx < len(content):

                    start = end - calculated_overlap if end > 0 else 0
                    end = start + part_length + calculated_overlap

                    if end > len(content):
                        end = len(content)

                    paragraph = content[start:end].strip()
                    if paragraph:  # Check to avoid adding empty strings
                            paragraphs.append(paragraph)

                    idx = end
        
        return paragraphs
    

if __name__ == '__main__':
    extractor = ContentExtractor()
    paragraphs = extractor.get_content("pdf_rag", 400, 0.25)
    print(paragraphs)


