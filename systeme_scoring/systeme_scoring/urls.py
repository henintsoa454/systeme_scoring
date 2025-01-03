from django.contrib import admin
from django.urls import path
from cemapp import views as baseviews
from cemapp.role_views import admin_views, service_client_views, gestionnaire_demande_views, analyste_demande_views, directeur_agence_views, agent_inspection_views

urlpatterns = [
    path('superuser/', admin.site.urls),
    path('', baseviews.user_login, name='login'),
    path('logout/', baseviews.user_logout, name='logout'),
    #admin
    path('admin/', admin_views.admin_home, name='admin_home'),
    #directeur_agence
    path('directeuragence/', directeur_agence_views.directeur_home, name='directeur_home'),
    path('directeuragence/performancegenerale/', directeur_agence_views.performance_generale, name='performancegenerale'),
    path('api/get_performance_generale/', directeur_agence_views.get_performance_generale, name="getperformancegenerale"),
    path('directeuragence/performanceemploye/', directeur_agence_views.performance_employes, name='performanceemployes'),
    path('directeuragence/gestionemployes/', directeur_agence_views.gestion_employes, name='gestionemployes'),
    path('api/get_performance_employes/', directeur_agence_views.get_performance_employes, name="getperformanceemployes"),
    #analyste_demande
    path('analyste/', analyste_demande_views.analyste_home, name='analyste_home'),
    path('analyste/detailsscoringdemande/<int:demande_id>/', analyste_demande_views.details_demande, name='detailsscoringdemande'),
    path("feature-importance", analyste_demande_views.feature_importance_page, name="feature_importance_page"),
    path("get-feature-importances", analyste_demande_views.get_feature_importances, name="get_feature_importances"),
    path("update-feature-importances", analyste_demande_views.update_feature_importances, name="update_feature_importances"),
    path('analyste/listerendezvous/', analyste_demande_views.liste_rendez_vous, name='listerendezvous'),
    #agent_inspection
    path('agentinspection/', agent_inspection_views.agent_inspection_home, name='agent_inspection_home'),
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
