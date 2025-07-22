@echo off
echo ===========================================
echo  PDF Content Extractor - Setup Script
echo ===========================================
echo.

echo Installing required Python packages...
pip install PyMuPDF==1.23.14
pip install pdfplumber==0.10.3  
pip install Pillow==10.1.0

echo.
echo ===========================================
echo  Setup Complete!
echo ===========================================
echo.
echo To run the extractor:
echo   python pdf_extractor.py "your-pdf-file.pdf"
echo.
echo Or run the demo:
echo   python demo.py
echo.
pause
