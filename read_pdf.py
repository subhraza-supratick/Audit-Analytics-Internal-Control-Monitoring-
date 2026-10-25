import sys
sys.stdout.reconfigure(encoding='utf-8')
from pypdf import PdfReader
reader = PdfReader('Audit_Analytics_Internal_Control_Monitoring_Project_Plan.pdf')
for i, page in enumerate(reader.pages):
    text = page.extract_text() or ''
    print(f'--- PAGE {i+1} ---')
    print(text.encode('ascii', errors='replace').decode('ascii'))
    print()
