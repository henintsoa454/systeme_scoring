from django.shortcuts import render,get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from ..models_classes.type_credit import TypeCredit
from ..models_classes.document_credit import DocumentCredit 
from ..models_classes.sous_types_credit import SousTypeCredit
from ..utils.role_checker import role_required

def is_service_client(user):
    return user.role == 'service_client'


@login_required
@user_passes_test(is_service_client)
def offres_credit(request):
    type_credits = TypeCredit.objects.prefetch_related('soustypecredit_set').all()
    documents = DocumentCredit.objects.all()

    return render(request, 'service_client/offres_credit.html', {
        'type_credits': type_credits,
        'documents': documents,
    })
    
@login_required
@user_passes_test(is_service_client)
def simulation_view(request, sous_type_id):
    sous_type = get_object_or_404(SousTypeCredit, id=sous_type_id)
    return render(request, 'service_client/simulation_offre.html', {'sous_type': sous_type})