from django.contrib import admin
from django.urls import path
from cemapp import views as baseviews
from cemapp.role_views import admin_views, service_client_views, gestionnaire_demande_views, analyste_demande_views, directeur_agence_views, agent_inspection_views

urlpatterns = [
    path('superuser/', admin.site.urls),
    path('', baseviews.user_login, name='login'),
    path('logout/', baseviews.user_logout, name='logout'),
    path('proposer-date/<uuid:token>/', baseviews.proposer_date, name='proposer_date'),
    path('proposer-date-finalisation/<uuid:token>/', baseviews.proposer_date_finalisation, name='proposer_date_finalisation'),
    #admin
    path('admin/', admin_views.admin_home, name='admin_home'),
    #directeur_agence
    path('directeuragence/', directeur_agence_views.directeur_home, name='directeur_home'),
    path('directeuragence/performancegenerale/', directeur_agence_views.performance_generale, name='performancegenerale'),
    path('api/get_performance_generale/', directeur_agence_views.get_performance_generale, name="getperformancegenerale"),
    path('directeuragence/performanceemploye/', directeur_agence_views.performance_employes, name='performanceemployes'),
    path('directeuragence/gestionemployes/', directeur_agence_views.gestion_employes, name='gestionemployes'),
    path('api/get_statut_demande/', directeur_agence_views.get_performance_employes, name="getperformanceemployes"),
    path('directeuragence/listeattente/',directeur_agence_views.liste_attente, name='listeattente'),
    path('directeuragence/creer-rendezvous/', directeur_agence_views.creer_rendezvous, name='creer_rendezvous_finalisation'),
    path('directeuragence/calendrier_finalisation', directeur_agence_views.calendrier_finalisation, name='calendrierfinalisation'),
    path('directeuragence/resumedemande/<int:demande_id>/', directeur_agence_views.resumedemande, name='resumedemande'),
    path('directeuragence/previewcontrat/<int:demande_id>/', directeur_agence_views.preview_contract, name='preview_contract'),
    path('directeuragence/demande/<int:demande_id>/generate-contract/', directeur_agence_views.generate_contract_pdf, name='generate_contract'),
    path('directeuragence/pdf-download-complete/', directeur_agence_views.pdf_download_complete, name='pdf_download_complete'),
    path('api/finalisation/', directeur_agence_views.api_finalisation, name='api_finalisation'),
    #analyste_demande
    path('analyste/', analyste_demande_views.analyste_home, name='analyste_home'),
    path('analyste/detailsscoringdemande/<int:demande_id>/', analyste_demande_views.details_demande, name='detailsscoringdemande'),
    path("feature-importance", analyste_demande_views.feature_importance_page, name="feature_importance_page"),
    path("get-feature-importances", analyste_demande_views.get_feature_importances, name="get_feature_importances"),
    path("update-feature-importances", analyste_demande_views.update_feature_importances, name="update_feature_importances"),
    path("analyste/refusdemande/<int:demande_id>/", analyste_demande_views.refus_demande, name="refus_demande"),
    path("analyste/transmettredemande/<int:demande_id>/", analyste_demande_views.transmettre_demande, name="transmettre_demande"),
    #agent_inspection
    path('agentinspection/', agent_inspection_views.agent_inspection_home, name='agent_inspection_home'),
    path('agentinspection/calendrier_inspection', agent_inspection_views.calendrier_inspections, name='calendrierinspection'),
    path('agentinspection/creer-rendezvous/', agent_inspection_views.creer_rendezvous, name='creer_rendezvous'),
    path('agentinspection/creer-inspection/', agent_inspection_views.creer_inspection, name='creer_inspection'),
    path('agentinspection/traiter-proposition/<uuid:token>/', agent_inspection_views.traiter_proposition, name='traiter_proposition'),    
    path('agentinspection/liste-proposition/', agent_inspection_views.propositions_rendezvous, name='liste_proposition'),    
    path('api/rendezvous/', agent_inspection_views.api_rendezvous, name='api_rendezvous'),
    #gestionnaire_demande
    path('gestionnairedemande/', gestionnaire_demande_views.gestionnaire_home, name='gestionnaire_home'),
    path('gestionnairedemande/gestionnaireclient/', gestionnaire_demande_views.gestionnaire_clients, name='gestionnaireclients'),
    path('gestionnairedemande/rechercheclients/', gestionnaire_demande_views.recherche_clients, name='rechercheclients'),
    path('gestionnairedemande/ajoutclient/', gestionnaire_demande_views.ajouter_client, name='ajoutclient'), 
    path('gestionnairedemande/modifie_client/<int:client_id>/', gestionnaire_demande_views.modifie_client, name='modifieclient'),
    path('gestionnairedemande/gestionnairedemande/', gestionnaire_demande_views.gestionnaire_demandes, name='gestionnairedemandes'),
    path('gestionnairedemande/nouvelledemande/', gestionnaire_demande_views.nouvelle_demande, name="nouvelledemande"),
    path('gestionnairedemande/modifier/<int:demande_id>/', gestionnaire_demande_views.modifier_demande, name='modifiedemande'),
    path('gestionnairedemande/payementdemande/<int:demande_id>/', gestionnaire_demande_views.paiement, name='payementdemande'),
    path('gestionnairedemande/telechargement/', gestionnaire_demande_views.page_telechargement, name='telechargement'),
    path('api/sous-types-credit/<int:type_credit_id>/', gestionnaire_demande_views.sous_types_credit_api, name='sous_types_credit_api'),
    # service_client
    path('serviceclient/offrescredit/', service_client_views.offres_credit, name='offre_credit'),
    path('serviceclient/simulation/<int:sous_type_id>/', service_client_views.simulation_view, name='simulation_offre'),    
]
