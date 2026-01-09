from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import ConstructionContract
from .serializers import ConstructionContractSerializer, ContractClauseSerializer
from .logic import process_contract_file, search_contract

class ConstructionContractViewSet(viewsets.ModelViewSet):
    queryset = ConstructionContract.objects.all()
    serializer_class = ConstructionContractSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(uploaded_by=self.request.user)

    @action(detail=True, methods=['post'])
    def process(self, request, pk=None):
        """
        Triggers the AI processing of the contract.
        """
        contract = self.get_object()
        # In production, this should be a Celery task
        process_contract_file(contract.id)
        
        contract.refresh_from_db()
        return Response(self.get_serializer(contract).data)

    @action(detail=True, methods=['get'])
    def search(self, request, pk=None):
        """
        Semantic search within the contract.
        Query param: ?q=query_string
        """
        query = request.query_params.get('q')
        if not query:
            return Response({'error': 'Query parameter "q" is required'}, status=400)
            
        results = search_contract(pk, query)
        return Response(results)
