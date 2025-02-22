from django.conf import settings
from rest_framework.routers import DefaultRouter
from rest_framework.routers import SimpleRouter

from dialer.users.api.views import UserViewSet
from dialer.pbx.api.views import QueueViewSet, CallViewSet
from dialer.crm.api.views import CRMViewSet  

router = DefaultRouter() if settings.DEBUG else SimpleRouter()

# router.register("users", UserViewSet)
router.register("queue", QueueViewSet, basename="queue")
router.register("call", CallViewSet, basename="call")
router.register("crm", CRMViewSet, basename="crm")


app_name = "api"
urlpatterns = router.urls
