# PDF Content Analysis and Question Generation 
## Assignment by Parth Sharma
### mail: parthsharma2300@gmail.com , Contact: 8087384306


## 📋 Requirements

- Required libraries (You can also see requirements.txt):
  - PyMuPDF (fitz)
  - pdfplumber  
  - Pillow

## 🛠️ Installation

 **Install Python packages:**
   ```bash
   pip install -r requirements.txt
   ```

## 🚀 How to use - ( There are 3 menthods we can use)

### Method 1: Command Line
```bash
python pdf_extractor.py "your-pdf-filename.pdf"
```

### Method 2: Demo Script
```bash
python demo.py
```

### Method 3: Python Code
```python
from pdf_extractor import PDFContentExtractor

# Create extractor
extractor = PDFContentExtractor("your-pdf-file.pdf")

# Extract content
questions, summary = extractor.extract_all_content()

# Save to JSON
extractor.save_to_json(questions, summary)

# Close extractor
extractor.close()
```

## 📤 Output Files

The tool creates several output files in the `extracted_content/` folder:

1. **extracted_content.json** 
2. **detailed_extracted_content.json** 
3. **extraction_report.txt** 
4. **images/** folder 

## 📊 Example Output Format

```json
[
  {
    "question": "What is the next figure?",
    "images": "extracted_content/images/page1_image1.png",
    "option_images": [
      "extracted_content/images/page1_image2.png",
      "extracted_content/images/page1_image3.png"
    ]
  }
]
```




