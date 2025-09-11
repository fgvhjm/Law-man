from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions, TesseractCliOcrOptions
from docling.document_converter import DocumentConverter, PdfFormatOption
import io

pipeline = PdfPipelineOptions(
    do_ocr=True,
    ocr_options=TesseractCliOcrOptions(lang=["auto"]),   # auto-detect language
    do_table_structure=True                              # keep tables in MD
)

converter = DocumentConverter(
    format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline)}
)
source="/home/suraj-kumar-nayak/law-man/contract.pdf"
doc = converter.convert(source).document
print(doc.export_to_markdown())
print(type(doc.export_to_markdown()))
