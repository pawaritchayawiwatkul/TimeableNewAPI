from django.urls import path , re_path
from teacher import views
from rest_framework.urlpatterns import format_suffix_patterns

app_name = 'teacher'

createLesson = views.LessonViewset.as_view({
    'post': 'create',
    # 'get': 'list'
})

studentAddView = views.StudentViewset.as_view({
    'post': 'add',
    # 'get': 'list'
})

profileView = views.ProfileViewSet.as_view({
    'get': 'retrieve',
    'put': 'update'
})

schoolView = views.SchoolViewSet.as_view({
    'put': 'update',
    'get': 'retrieve'
})

courseView = views.CourseViewset.as_view({
    'get': 'list',
    'post': 'create'
})

courseDetailView = views.CourseViewset.as_view({
    'get': 'retrieve',
})

courseFavView = views.CourseViewset.as_view({
    'put': 'favorite',
})

courseStudentView = views.CourseViewset.as_view({
    'get': 'retrieve_with_student',
})

courseATview = views.RegistrationViewset.as_view({
    'get': 'get_available_time',
})

lessonProgressView = views.LessonViewset.as_view({
    "get": "progress",
})

lessonDayView = views.LessonViewset.as_view({
    'get': 'day',
})

lessonWeekView = views.LessonViewset.as_view({
    'get': 'week',
})

LessonCancelView = views.LessonViewset.as_view({
    'put': 'cancel',
})

LessonConfirmView = views.LessonViewset.as_view({
    'put': 'confirm',
})

LessonMissedView = views.LessonViewset.as_view({
    'put': 'missed'
})

LessonAttendView = views.LessonViewset.as_view({
    'put': 'attended'
}) 

lessonRecentView = views.LessonViewset.as_view({
    'get': 'recent',
})

lessonStatusView = views.LessonViewset.as_view({
    'get': 'status',
})

studentListView = views.StudentViewset.as_view({
    'get': 'list'
})

studentFavView = views.StudentViewset.as_view({
    'put': 'favorite'
})

registrationView = views.RegistrationViewset.as_view({
    'get': 'list',
    'post': 'create'
})

registrationDetailView = views.RegistrationViewset.as_view({
    'get': 'retrieve'
})

registrationFavView = views.RegistrationViewset.as_view({
    'put': 'favorite'
})

oneTimeUnavailable = views.UnavailableTimeViewset.as_view({
    'post': 'one_time'
})

regularUnavailable = views.UnavailableTimeViewset.as_view({
    'post': 'regular'
})

blockTimeList = views.UnavailableTimeViewset.as_view({
    'get': 'retrieve'
})

blockTimeRemove = views.UnavailableTimeViewset.as_view({
    'delete': 'remove'
})
# Enter URL path below
urlpatterns = format_suffix_patterns([
    path('profile/', profileView, name='profile'),
    path('institute/', schoolView, name='profile'),

    path('course/', courseView, name='course'),
    path('course/<slug:code>', courseDetailView, name='course'),
    path('course/<slug:code>/favorite', courseFavView, name='course'),
    path('course/<slug:code>/student', courseStudentView, name='course'),

    path('registration/', registrationView, name='course'),
    path('registration/<slug:code>', registrationDetailView, name='course'),
    path('registration/<slug:code>/favorite', registrationFavView, name='regis-fav'),
    path('registration/<slug:code>/availabletime', courseATview, name='course-available-time'),

    path('lesson/', createLesson, name='lesson'),
    path('lesson/day', lessonDayView, name='lesson-day'),
    path('lesson/week', lessonWeekView, name='lesson-week'),
    path('lesson/status/<slug:status>', lessonStatusView, name='lesson'),
    path('lesson/recent', lessonRecentView, name='lesson-recent'),
    path('lesson/<slug:code>/cancel', LessonCancelView, name='lesson-cancel'),
    path('lesson/<slug:code>/confirm', LessonConfirmView, name='lesson-confirm'),
    path('lesson/<slug:code>/missed', LessonMissedView, name='lesson-missed'),
    path('lesson/<slug:code>/attended', LessonAttendView, name='lesson-attended'),

    path('unavailable/onetime', oneTimeUnavailable, name='unavailable-onetime'),
    path('unavailable/regular', regularUnavailable, name='unavailable-regular'),
    path('unavailable/', blockTimeList, name='block-time'),
    path('unavailable/<slug:code>/remove', blockTimeRemove, name='block-time'),

    path('student', studentListView, name='student-list'),
    path('student/<slug:code>/favorite', studentFavView, name='student-fav'),
    path('student/<slug:code>/add', studentAddView, name='student-add'),

    ])