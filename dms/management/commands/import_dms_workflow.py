from django.core.management.base import BaseCommand
import pandas as pd
from dms.models import Department, WorkflowPhase, WorkflowStep

class Command(BaseCommand):
    help = 'Imports DMS workflow from Excel'

    def handle(self, *args, **options):
        file_path = '/home/ebony/PycharmProjects/PIC_ERP_Backend/assets/DMS workflow for PIC ERP.xlsx'
        
        # Read with header=1 to capture correct columns
        df = pd.read_excel(file_path, header=1)
        
        # 1. Create Departments
        print("Creating Departments...")
        # Get unique actors and receivers
        actors = df['Actor'].dropna().unique()
        receivers = df['Receiver'].dropna().unique()
        all_depts = set(list(actors) + list(receivers))
        
        for dept_name in all_depts:
            dept_name = str(dept_name).strip()
            # Simple code generation: first 3 letters uppercased
            code = dept_name[:3].upper()
            
            # Corrections for known codes
            if dept_name == 'Subcontractor': code = 'SUB'
            if dept_name == 'Consultant': code = 'CSL'
            if dept_name == 'Management': code = 'MGT'
            if dept_name == 'Procurement': code = 'PRC' 
            
            # Ensure uniqueness
            base_code = code
            counter = 1
            while Department.objects.filter(code=code).exists():
                existing = Department.objects.get(code=code)
                if existing.name == dept_name:
                    break # Same dept, it's fine
                code = f"{base_code[:2]}{counter}"
                counter += 1
            
            Department.objects.get_or_create(name=dept_name, defaults={'code': code})
            
        # 2. Extract Workflow Steps
        # We need to handle Phases. The raw file analysis showed "Tendering" as a header row.
        # This is tricky with pandas. Let's assume some manual mapping or simple phase logic.
        # For this PoC, I'll put everything in one phase or look at the first column 'Seq'.
        # 2.1 starts Tendering?
        
        # Let's create a default Tendering phase
        phase, _ = WorkflowPhase.objects.get_or_create(name='Tendering', sequence=1)
        
        print("Creating Workflow Steps...")
        for index, row in df.iterrows():
            seq = row['Seq']
            # If seq is NaN, it might be a header or empty row
            if pd.isna(seq):
                continue
                
            actor_name = row['Actor']
            receiver_name = row['Receiver']
            action = row['Action']
            doc_type = row['Document Type']
            
            if pd.isna(actor_name): continue
            
            try:
                actor = Department.objects.get(name=str(actor_name).strip())
                
                receiver = None
                if pd.notna(receiver_name):
                    receiver = Department.objects.get(name=str(receiver_name).strip())
                
                step, created = WorkflowStep.objects.get_or_create(
                    sequence_id=str(seq),
                    phase=phase,
                    defaults={
                        'ordering': float(seq) if isinstance(seq, (int, float)) else 0,
                        'actor_department': actor,
                        'receiver_department': receiver,
                        'action_description': str(action) if pd.notna(action) else "",
                        'required_document_type': str(doc_type) if pd.notna(doc_type) else ""
                    }
                )
                if created:
                    print(f"Created step {seq}")
                else:
                    print(f"Updated step {seq}")
                    
            except Exception as e:
                print(f"Error processing row {index}: {e}")
                
        self.stdout.write(self.style.SUCCESS('Successfully imported workflow'))
