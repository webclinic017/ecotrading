from django.urls import include, path
from .views import *
import debug_toolbar
from rest_framework.routers import DefaultRouter

app_name = 'portfolio'
router = DefaultRouter()
router.register('test', TransactionViewSet)


urlpatterns = [
    path('account/<int:pk>/', account, name='account'),  
    path('get-port/', get_port, name='get_port'),
    # path('',include(router.urls)), 
    path('', redirect_view),
   
]
