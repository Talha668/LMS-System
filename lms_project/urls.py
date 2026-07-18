from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from users import views as user_views
from django.conf import settings
from django.conf.urls.static import static
from courses.views import home_view



urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('courses.urls')),
    path('', home_view, name='home'),    
    path('register/', user_views.register, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('profile/', user_views.profile_view, name='profile'),
    path('profile/edit/', user_views.profile_edit, name='profile_edit'),
    path('api/', include('courses.api.urls')),
]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)