from rest_framework.routers import DefaultRouter

from .api import ApplicationViewSet, JobViewSet

router = DefaultRouter()
router.register("jobs", JobViewSet, basename="api-jobs")
router.register("applications", ApplicationViewSet, basename="api-applications")

urlpatterns = router.urls
