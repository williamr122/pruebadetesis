import sys
import os

try:
    import win32com.client
except ImportError:
    print("win32com not installed.")
    sys.exit(1)

script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
base_path = os.path.join(project_root, "frontend", "public", "resources", "RECOMENDACION_DE_RECURSOS_YELIA4AP")

print("Starting PowerPoint application COM server...")
try:
    # Use DispatchEx to start a fresh instance
    ppt_app = win32com.client.DispatchEx("PowerPoint.Application")
except Exception as e:
    print(f"Error starting PowerPoint: {e}")
    sys.exit(1)

for u in (3, 4):
    pptx_path = os.path.join(base_path, f"u{u}", "presentation.pptx")
    pdf_path = os.path.join(base_path, f"u{u}", "presentation.pdf")
    
    if os.path.exists(pptx_path):
        print(f"Opening u{u} presentation: {pptx_path}")
        try:
            # Open(FileName, ReadOnly, Untitled, WithWindow)
            # ReadOnly=True (True/1), Untitled=True (True/1), WithWindow=False (False/0)
            pres = ppt_app.Presentations.Open(pptx_path, 1, 1, 0)
            print(f"Saving as PDF: {pdf_path}")
            # 32 is ppSaveAsPDF
            pres.SaveAs(pdf_path, 32)
            pres.Close()
            print(f"Success for Unit {u}")
        except Exception as e:
            print(f"Error for Unit {u}: {e}")
    else:
        print(f"File not found: {pptx_path}")

try:
    ppt_app.Quit()
except Exception:
    pass
print("Finished.")
