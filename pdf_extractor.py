"""
PDF Content Analysis and Question Generation Tool
=================================================

Author - Parth Sharma
This tool extracts text and images from educational PDF documents and structures
them into a JSON format suitable for AI-based question generation.

Requirements:
- PyMuPDF (fitz)
- pdfplumber  
- Pillow

Usage:
    python pdf_extractor.py <pdf_file_path>

"""

import os
import sys
import json
import re
import argparse
from datetime import datetime
from typing import List, Dict, Tuple, Optional

try:
    import fitz  # PyMuPDF
except ImportError:
    print("Error: PyMuPDF not found. Install with: pip install PyMuPDF")
    sys.exit(1)

try:
    import pdfplumber
except ImportError:
    print("Error: pdfplumber not found. Install with: pip install pdfplumber")
    sys.exit(1)

try:
    from PIL import Image
except ImportError:
    print("Error: Pillow not found. Install with: pip install Pillow")
    sys.exit(1)


class PDFContentExtractor:


    def __init__(self, pdf_path: str, output_dir: str = "extracted_content"):
        """
        Initialize the PDF extractor
        """
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")

        self.pdf_path = pdf_path
        self.doc = fitz.open(pdf_path)
        self.output_dir = output_dir
        self.images_dir = os.path.join(output_dir, "images")

        # Create output directories
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.images_dir, exist_ok=True)

        print(f"Initialized extractor for: {pdf_path}")
        print(f"Total pages: {self.doc.page_count}")
        print(f"Output directory: {self.output_dir}")

    def extract_text_from_page(self, page_num: int) -> str:
        """Extract text using PyMuPDF"""
        page = self.doc[page_num]
        text = page.get_text()
        return text

    def extract_text_with_pdfplumber(self, page_num: int) -> str:
        """Extract text using pdfplumber (often more accurate)"""
        try:
            with pdfplumber.open(self.pdf_path) as pdf:
                if page_num < len(pdf.pages):
                    page = pdf.pages[page_num]
                    return page.extract_text() or ""
        except Exception as e:
            print(f"pdfplumber extraction failed for page {page_num + 1}: {e}")
            return self.extract_text_from_page(page_num)
        return ""

    def extract_images_from_page(self, page_num: int) -> List[str]:
       
        page = self.doc[page_num]
        image_list = page.get_images()
        extracted_images = []

        for img_index, img in enumerate(image_list):
            try:
                xref = img[0]
                pix = fitz.Pixmap(self.doc, xref)

                # Filter out very small images (likely decorative)
                if pix.width < 20 or pix.height < 20:
                    pix = None
                    continue

                img_filename = f"page{page_num + 1}_image{img_index + 1}.png"
                img_path = os.path.join(self.images_dir, img_filename)

                if pix.n - pix.alpha < 4:  # GRAY or RGB
                    pix.save(img_path)
                else:  # CMYK: convert to RGB first
                    pix1 = fitz.Pixmap(fitz.csRGB, pix)
                    pix1.save(img_path)
                    pix1 = None

                extracted_images.append(img_path)
                pix = None

            except Exception as e:
                print(f"Error extracting image {img_index} from page {page_num + 1}: {e}")

        return extracted_images

    def clean_text_line(self, line: str) -> str:
       
        line = ' '.join(line.split())
        line = line.replace('', '').replace('', '').strip()
        return line

    def parse_questions_from_text(self, text: str, page_images: List[str], page_num: int) -> List[Dict]:
       
        questions = []
        lines = [self.clean_text_line(line) for line in text.split('\n') if line.strip()]

        current_question = None
        current_options = []
        current_answer = None
        question_number = None

        i = 0
        while i < len(lines):
            line = lines[i].strip()

           
            if not line or line in ['Vedantu', 'LIVE ONLINE TUTORING', 'www.vedantu.com']:
                i += 1
                continue

            
            question_match = re.match(r'^(\d+)\.\s*(.+)', line)
            if question_match:
                
                if current_question is not None:
                    questions.append({
                        "question_number": question_number,
                        "question": current_question,
                        "options": current_options,
                        "answer": current_answer,
                        "page": page_num + 1,
                        "images": "",
                        "option_images": []
                    })

                
                question_number = int(question_match.group(1))
                current_question = question_match.group(2).strip()
                current_options = []
                current_answer = None

                
                j = i + 1
                while j < len(lines):
                    next_line = lines[j].strip()

                    # Stop if we hit options, answers, or next question
                    if (re.match(r'^\[?[A-D]\]', next_line) or 
                        next_line.startswith('Ans') or 
                        re.match(r'^\d+\.', next_line) or
                        next_line in ['??', '?'] or
                        not next_line):
                        break

                    current_question += " " + next_line
                    j += 1

                i = j - 1

            
            elif re.match(r'^\[?([A-D])\]?\s*(.+)?', line):
                option_match = re.match(r'^\[?([A-D])\]?\s*(.+)?', line)
                if option_match:
                    option_letter = option_match.group(1)
                    option_text = option_match.group(2) or ""
                    current_options.append(f"[{option_letter}] {option_text}".strip())

            
            elif line.startswith('Ans'):
                answer_match = re.search(r'Ans\.?\s*\[?([A-D])\]?', line)
                if answer_match:
                    current_answer = answer_match.group(1)

            i += 1

        # Add the last question
        if current_question is not None:
            questions.append({
                "question_number": question_number,
                "question": current_question,
                "options": current_options,
                "answer": current_answer,
                "page": page_num + 1,
                "images": "",
                "option_images": []
            })

        
        if questions and page_images:
            self._associate_images_with_questions(questions, page_images)

        return questions

    def _associate_images_with_questions(self, questions: List[Dict], page_images: List[str]):
       
        if not questions or not page_images:
            return

        images_per_question = max(1, len(page_images) // len(questions))

        for i, question in enumerate(questions):
            start_idx = i * images_per_question
            end_idx = min(start_idx + images_per_question, len(page_images))

            if start_idx < len(page_images):
                
                question["images"] = page_images[start_idx]

                
                if end_idx > start_idx + 1:
                    question["option_images"] = page_images[start_idx + 1:end_idx]
                else:
                    question["option_images"] = []

    def extract_page_content(self, page_num: int) -> Tuple[str, List[str], List[Dict]]:
        """Extract all content from a single page"""
        print(f"Processing page {page_num + 1}...")

        
        page_text = self.extract_text_with_pdfplumber(page_num)
        if not page_text.strip():
            page_text = self.extract_text_from_page(page_num)

        # Extract images
        page_images = self.extract_images_from_page(page_num)

        # Parse questions
        page_questions = self.parse_questions_from_text(page_text, page_images, page_num)

        print(f"  Found {len(page_questions)} questions and {len(page_images)} images")

        return page_text, page_images, page_questions

    def extract_all_content(self) -> Tuple[List[Dict], Dict]:
        """
        Extract all content from the PDF

        
        """
        all_questions = []
        extraction_summary = {
            "total_pages": self.doc.page_count,
            "total_questions": 0,
            "total_images": 0,
            "pages_processed": 0,
            "extraction_errors": []
        }

        for page_num in range(self.doc.page_count):
            try:
                page_text, page_images, page_questions = self.extract_page_content(page_num)
                all_questions.extend(page_questions)

                extraction_summary["total_images"] += len(page_images)
                extraction_summary["pages_processed"] += 1

            except Exception as e:
                error_msg = f"Error processing page {page_num + 1}: {str(e)}"
                print(error_msg)
                extraction_summary["extraction_errors"].append(error_msg)

        extraction_summary["total_questions"] = len(all_questions)

        return all_questions, extraction_summary

    def save_to_json(self, questions: List[Dict], summary: Dict, output_file: str = "extracted_content.json") -> str:
        """
        Save extracted content to JSON file

        """
        # Convert to the required format
        formatted_questions = []
        for q in questions:
            formatted_q = {
                "question": q["question"],
                "images": q["images"],
                "option_images": q["option_images"]
            }
            
            if q.get("options"):
                formatted_q["options"] = q["options"]
            if q.get("answer"):
                formatted_q["answer"] = q["answer"]
            if q.get("question_number"):
                formatted_q["question_number"] = q["question_number"]
            if q.get("page"):
                formatted_q["page"] = q["page"]

            formatted_questions.append(formatted_q)

        
        detailed_output = {
            "metadata": {
                "source_file": self.pdf_path,
                "extraction_date": datetime.now().isoformat(),
                "extractor_version": "2.0",
                "total_questions": len(questions),
                "total_images": summary.get("total_images", 0)
            },
            "summary": summary,
            "questions": formatted_questions
        }

        
        output_path = os.path.join(self.output_dir, output_file)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(formatted_questions, f, indent=2, ensure_ascii=False)

        # Save detailed format
        detailed_path = os.path.join(self.output_dir, "detailed_" + output_file)
        with open(detailed_path, 'w', encoding='utf-8') as f:
            json.dump(detailed_output, f, indent=2, ensure_ascii=False)

        print(f"Simple format saved to: {output_path}")
        print(f"Detailed format saved to: {detailed_path}")

        return output_path

    def generate_report(self, questions: List[Dict], summary: Dict) -> str:
        """Generate extraction statistics report"""
        report = []
        report.append("=" * 60)
        report.append("PDF CONTENT EXTRACTION REPORT")
        report.append("=" * 60)
        report.append(f"Source File: {self.pdf_path}")
        report.append(f"Extraction Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")

        # Basic statistics
        report.append("EXTRACTION SUMMARY:")
        report.append(f"  Total Pages: {summary['total_pages']}")
        report.append(f"  Pages Processed: {summary['pages_processed']}")
        report.append(f"  Total Questions: {summary['total_questions']}")
        report.append(f"  Total Images: {summary['total_images']}")

        if summary.get('extraction_errors'):
            report.append(f"  Extraction Errors: {len(summary['extraction_errors'])}")

        report.append("")

        
        if questions:
            report.append("QUESTION ANALYSIS:")

            
            pages_with_questions = {}
            for q in questions:
                page = q.get('page', 'Unknown')
                pages_with_questions[page] = pages_with_questions.get(page, 0) + 1

            report.append(f"  Pages with Questions: {len(pages_with_questions)}")
            for page in sorted(pages_with_questions.keys()):
                if page != 'Unknown':
                    report.append(f"    Page {page}: {pages_with_questions[page]} questions")

           
            questions_with_images = sum(1 for q in questions if q.get('images') or q.get('option_images'))
            report.append(f"  Questions with Images: {questions_with_images}")

            
            answer_counts = {}
            for q in questions:
                answer = q.get('answer')
                if answer:
                    answer_counts[answer] = answer_counts.get(answer, 0) + 1

            if answer_counts:
                report.append("  Answer Distribution:")
                for answer in sorted(answer_counts.keys()):
                    report.append(f"    {answer}: {answer_counts[answer]} questions")

        # File outputs
        report.append("")
        report.append("OUTPUT FILES:")
        report.append(f"  Images Directory: {self.images_dir}")
        report.append(f"  JSON Output: {os.path.join(self.output_dir, 'extracted_content.json')}")
        report.append(f"  Detailed JSON: {os.path.join(self.output_dir, 'detailed_extracted_content.json')}")

        if summary.get('extraction_errors'):
            report.append("")
            report.append("EXTRACTION ERRORS:")
            for error in summary['extraction_errors']:
                report.append(f"  - {error}")

        report.append("")
        report.append("=" * 60)

        return "\n".join(report)

    def close(self):
        """Close the PDF document"""
        self.doc.close()


def main():
    """Main function to run the PDF extractor"""
    parser = argparse.ArgumentParser(
        description="Extract content from educational PDF documents",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python pdf_extractor.py sample.pdf
  python pdf_extractor.py sample.pdf --output-dir my_output
        """
    )
    parser.add_argument("pdf_file", help="Path to the PDF file to process")
    parser.add_argument("--output-dir", default="extracted_content", 
                       help="Output directory (default: extracted_content)")

    args = parser.parse_args()

    try:
        
        extractor = PDFContentExtractor(args.pdf_file, args.output_dir)

        print("\nStarting content extraction...")

        
        questions, summary = extractor.extract_all_content()

        print("\nExtraction completed!")
        print(f"Found {summary['total_questions']} questions and {summary['total_images']} images")

        # Save to JSON
        json_path = extractor.save_to_json(questions, summary)

        
        report = extractor.generate_report(questions, summary)
        print("\n" + report)

        report_path = os.path.join(args.output_dir, "extraction_report.txt")
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"\nReport saved to: {report_path}")

        # Show sample questions
        if questions:
            print("\nSample Questions:")
            for i, q in enumerate(questions[:3]):
                print(f"\n{i+1}. {q['question'][:100]}...")
                if q.get('images'):
                    print(f"   Main image: {q['images']}")
                if q.get('option_images'):
                    print(f"   Option images: {len(q['option_images'])} images")

        extractor.close()
        print("\nExtraction process completed successfully!")

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
