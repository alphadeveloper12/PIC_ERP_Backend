import os
import django
import sys

sys.path.append('/home/ebony/PycharmProjects/PIC_ERP_Backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from django.contrib.auth import get_user_model
from projects.models import Project, Company
from contracts.models import ConstructionContract
from contracts.logic import process_contract_file, search_contract

User = get_user_model()

def test_ai_contracts():
    print("--- Starting AI Contract Intelligence Test ---")
    
    # 1. Setup Data
    user = User.objects.first()
    if not user:
        user = User.objects.create(username='ai_tester')
        
    company, _ = Company.objects.get_or_create(name="AI Test Co", code="ATC", address="Test")
    project = Project.objects.filter(code="AI-PRJ-001").first()
    if not project:
        project = Project.objects.create(name="AI Test Project", code="AI-PRJ-001", company=company)
        
    # 2. Create Dummy Contract
    contract, created = ConstructionContract.objects.get_or_create(
        project=project,
        title="Main Construction Agreement",
        defaults={'uploaded_by': user}
    )
    
    # 3. Process (Simulate Ingestion)
    print("Processing Contract (Embedding Clauses)...")
    process_contract_file(contract.id)
    
    # 4. Test Semantic Search
    query = "When should the invoice be paid?"
    print(f"\nQuery: '{query}'")
    
    results = search_contract(contract.id, query)
    
    if results:
        print(f"Top Result: {results[0]['text']}")
        print(f"Score: {results[0]['score']:.4f}")
        print("SUCCESS: Semantic search found relevant clause.")
    else:
        print("FAILURE: No results found.")

if __name__ == "__main__":
    test_ai_contracts()
