import logging
from typing import List, Dict, Any, Optional
from django.db.models import QuerySet
from sentence_transformers import util
import torch

from .models import ConstructionContract, ContractClause
from ai_core.services import embedding_service

# Placeholder import for OCR
# import pytesseract
# from pdf2image import convert_from_path

logger = logging.getLogger(__name__)

def process_contract_file(contract_id: int) -> None:
    """
    Orchestrates the processing of a contract file.
    1. Reads PDF (Stubbed).
    2. Splits into clauses (Stubbed regex/heuristic).
    3. Embeds each clause using local SBERT.
    4. Saves to DB.
    """
    try:
        contract = ConstructionContract.objects.get(id=contract_id)
        
        # TODO: Implement actual OCRService to get text from contract.file.path
        # text = ocr_service.extract_text(contract.file.path)
        
        # For prototype, we use simulated clauses typical of construction contracts
        simulated_clauses = [
            ("PAYMENT", "The Employer shall pay the Contractor the Contract Price in accordance with the Payment Schedule. Payment shall be made within 30 days of receipt of a valid Invoice."),
            ("RETENTION", "Ten percent (10%) of each interim payment shall be retained by the Employer as Retention Money."),
            ("TERMINATION", "The Employer may terminate this Contract by giving 14 days written notice if the Contractor fails to remedy a breach."),
            ("DISPUTE", "Any dispute arising out of this Contract shall be settled by arbitration in Dubai, UAE."),
        ]
        
        for category, text in simulated_clauses:
            # Generate Embedding
            vector = embedding_service.encode(text)
            
            ContractClause.objects.create(
                contract=contract,
                category=category,
                original_text=text,
                embedding=vector,
                interpreted_value={"raw": text}  # Placeholder for structured extraction
            )
            
        contract.is_processed = True
        contract.save()
        logger.info(f"Contract '{contract.title}' (ID: {contract.id}) processed successfully.")
        
    except ConstructionContract.DoesNotExist:
        logger.error(f"Contract ID {contract_id} not found.")
    except Exception as e:
        logger.error(f"Error processing contract {contract_id}: {e}", exc_info=True)

def search_contract(contract_id: int, query: str) -> List[Dict[str, Any]]:
    """
    Performs semantic search against constraints of a specific contract.
    Returns a list of relevant clauses with similarity scores.
    """
    if not query:
        return []

    # Encode query
    query_vec = embedding_service.encode(query)
    if not query_vec:
        return []
        
    # Fetch all clauses for this contract
    clauses: QuerySet[ContractClause] = ContractClause.objects.filter(contract_id=contract_id)
    results = []
    
    # Extract embeddings (filtering out any None values)
    corpus_embeddings = [c.embedding for c in clauses if c.embedding]
    if not corpus_embeddings:
        return []

    # Convert to tensor for PyTorch operations
    corpus_t = torch.tensor(corpus_embeddings)
    query_t = torch.tensor(query_vec)
    
    # Perform semantic search (cosine similarity)
    # Returns a list of results for each query
    hits = util.semantic_search(query_t, corpus_t, top_k=3)
    
    # Map back to objects
    # hits[0] is the list of hits for the first (and only) query
    for hit in hits[0]:
        clause_idx = hit['corpus_id']
        clause = clauses[clause_idx]
        results.append({
            'id': clause.id,
            'category': clause.category,
            'text': clause.original_text,
            'score': float(hit['score'])
        })
        
    return results
