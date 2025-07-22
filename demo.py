"""
PDF Content Extractor - Demo Script
Demonstrates the usage of the PDF extraction tool
"""

from pdf_extractor import PDFContentExtractor
import json
import os

def demo_extraction(pdf_file):
    """Demo function showing how to use the extractor"""
    print(f"Demo: Extracting content from {pdf_file}")
    print("=" * 50)

    # Check if file exists
    if not os.path.exists(pdf_file):
        print(f"Error: File {pdf_file} not found")
        return

    try:
        # Initialize extractor
        extractor = PDFContentExtractor(pdf_file, "demo_output")

        # Extract content
        print("Extracting content...")
        questions, summary = extractor.extract_all_content()

        # Save to JSON
        print("Saving to JSON...")
        json_path = extractor.save_to_json(questions, summary, "demo_questions.json")

        # Generate report
        report = extractor.generate_report(questions, summary)

        # Show summary
        print("\nEXTRACTION SUMMARY:")
        print(f"Questions found: {len(questions)}")
        print(f"Total images: {summary.get('total_images', 0)}")
        print(f"Pages processed: {summary.get('pages_processed', 0)}")

        # Show first question as example
        if questions:
            print(f"\nFIRST QUESTION EXAMPLE:")
            q = questions[0]
            print(f"Question: {q['question'][:100]}...")
            print(f"Options: {len(q.get('options', []))}")
            print(f"Answer: {q.get('answer', 'Not found')}")
            print(f"Images: {1 if q.get('images') else 0} main, {len(q.get('option_images', []))} options")

        # Save report
        with open("demo_output/demo_report.txt", 'w') as f:
            f.write(report)

        extractor.close()
        print(f"\nDemo completed! Check 'demo_output' directory for results.")

    except Exception as e:
        print(f"Error during extraction: {e}")

if __name__ == "__main__":
    # Run demo with the sample PDF
    pdf_file = "IMO-class-1-Maths-Olympiad-Sample-Paper-1-for-the-year-2024-25.pdf"
    demo_extraction(pdf_file)
