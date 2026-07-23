from asyncio.log import logger

from .BaseController import BaseController
from .ProjectController import ProjectController
import os
from helpers.config import get_settings, Settings
from langchain_community.document_loaders import TextLoader , CSVLoader ,PyMuPDFLoader

from models import ProcessingEnum
from typing import List
from dataclasses import dataclass
from langchain_text_splitters import RecursiveCharacterTextSplitter
import pandas as pd
from langchain_core.documents import Document
            
@dataclass
class Document:
    page_content: str
    metadata: dict

class ProcessController(BaseController):

    def __init__(self, project_id: str):
        super().__init__()
        self.app_settings = get_settings()
        self.project_id = project_id
        self.project_path = ProjectController().get_project_path(project_id=project_id)
        self.chunking_method = self.app_settings.CHUNKING_METHOD

    def get_file_extension(self, file_id: str):
        return os.path.splitext(file_id)[-1]


    def get_file_content(self, file_id: str):
            file_ext = self.get_file_extension(file_id=file_id)
            file_path = os.path.join(self.project_path, file_id)

            if not os.path.exists(file_path):
                return None

            if file_ext == ProcessingEnum.TXT.value:
                return TextLoader(file_path, encoding="utf-8").load()

            if file_ext == ProcessingEnum.PDF.value:
                return PyMuPDFLoader(file_path).load()
            
            # Handle CSV files
            if file_ext == ProcessingEnum.CSV.value:
                return CSVLoader(file_path, encoding="utf-8").load()

            return None


    # chunking is here
    def process_file_content(self, file_content: list, file_id: str,
                            chunk_size: int=100, overlap_size: int=20):

        file_content_texts = [
            rec.page_content
            for rec in file_content
        ]

        file_content_metadata = [
            rec.metadata
            for rec in file_content
        ]
        if self.chunking_method == "recursive":
            chunks = self.process_recursive_medical_splitter(
                texts=file_content_texts,
                metadatas=file_content_metadata,
                chunk_size=chunk_size,
                overlap_size=overlap_size
            )

        # elif self.chunking_method == "csv":
        #     chunks = self.process_csv_reports(
        #         text=file_content
        #     )

        else :
            chunks = self.process_simpler_splitter(
                texts=file_content_texts,
                metadatas=file_content_metadata,
                chunk_size=chunk_size,
            )
        logger.info(f"Processed {len(chunks)} chunks for file_id: {file_id} , chunking_method: {self.chunking_method}")
        return chunks
    
    # simple chunking by splitter tag (e.g., newline) 
    def process_simpler_splitter(self, texts: List[str], metadatas: List[dict], chunk_size: int, splitter_tag: str="\n"):
        
        full_text = " ".join(texts)

        # split by splitter_tag
        lines = [ doc.strip() for doc in full_text.split(splitter_tag) if len(doc.strip()) > 1 ]

        chunks = []
        current_chunk = ""

        for line in lines:
            current_chunk += line + splitter_tag
            if len(current_chunk) >= chunk_size:
                chunks.append(Document(
                    page_content=current_chunk.strip(),
                    metadata={}
                ))

                current_chunk = ""

        if len(current_chunk) >= 0:
            chunks.append(Document(
                page_content=current_chunk.strip(),
                metadata={}
            ))

        return chunks


    # recursive chunking by splitter tag (e.g., newline)
    # adapt according to report format and structure
    def process_recursive_medical_splitter(self, texts: List[str], metadatas: List[dict], chunk_size: int, overlap_size: int):

            splitter = RecursiveCharacterTextSplitter(
                chunk_size=chunk_size,
                chunk_overlap=overlap_size,
                separators=["\n\n", "\n", " ", ""]
            )

            chunks = []

            for i, text in enumerate(texts):
                base_metadata = metadatas[i] if i < len(metadatas) else {}
                
                # 1. Create a contextual summary header from metadata or document header
                # (e.g., Patient/Report context injection)
                context_prefix = f"[Source: {base_metadata.get('source', 'Medical Report')} | Age: {base_metadata.get('age', 'Unknown')} | Findings Summary]\n"
                
                # 2. Split the body text recursively
                langchain_docs = splitter.create_documents(
                    texts=[text],
                    metadatas=[base_metadata]
                )

                # 3. Prepend the context prefix to every chunk so it never loses its identity
                for doc in langchain_docs:
                    enriched_content = context_prefix + doc.page_content
                    
                    chunks.append(
                        Document(
                            page_content=enriched_content,
                            metadata=base_metadata
                        )
                    )

            return chunks
    



    # # Inside your get_file_loader or a new CSV handler:
    # def process_csv_reports(self, text: str) -> List[Document]:

    #     chunks = []

    #     for _, row in df.iterrows():
    #         # The free text report content to be chunked/embedded
    #         report_text = str(row['report'])
            
    #         # Structured metadata directly from the CSV columns
    #         row_metadata = {
    #             "patient_id": row['ID'],
    #             "age": row['age'],
    #             "breast_density": row['breast_density'],
    #             "laterality": row['laterality'],
    #             "source": "CSV Report"
    #         }
            
    #         chunks.append(Document(page_content=report_text, metadata=row_metadata))

    #     return chunks
