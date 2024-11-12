import random
import string
from django.utils import timezone
from datetime import datetime, timedelta
from student.models import Lesson, GuestLesson
from teacher.models import UnavailableTimeOneTime
from typing import List
from rest_framework.response import Response

def generate_unique_code(length=8):
    """Generate a unique random code."""
    characters = string.ascii_letters + string.digits
    code = ''.join(random.choice(characters) for _ in range(length))
    return code


def merge_schedule(validated_data, unavailables):
    new_start = validated_data['start']
    new_stop = validated_data['stop']
    overlap = []
    for interval in unavailables:
        start = interval.start
        stop = interval.stop
        _ = False
        if start > new_stop:
            # print('1')
            continue
        elif stop < new_start:
            # print('2')
            continue
        if start <= new_start:
            # print('3')
            new_start = start
            _ = True
        if stop >= new_stop:
            # print('4')
            new_stop = stop
            _ = True
        overlap.append(interval)
        # print('5')

    validated_data['start'] = new_start
    validated_data['stop'] = new_stop
    return validated_data, overlap

def compute_available_time(unavailables:List[UnavailableTimeOneTime], lessons:List[Lesson], guest_lessons:List[GuestLesson], date_time, start, stop, duration):
    interval = timedelta(minutes=30)
    duration = timedelta(minutes=duration)
    available_times = []
    current_time = timezone.make_aware(datetime.combine(date_time, start))
    stop_time = timezone.make_aware(datetime.combine(date_time, stop))
    while current_time + duration <= stop_time:
        end_time = current_time + duration
        
        _is_available = True
        for unavailable in unavailables:
            start_ = timezone.make_aware(datetime.combine(date_time, unavailable.start))
            stop_ = timezone.make_aware(datetime.combine(date_time, unavailable.stop))
            if (start_ <= current_time < stop_) or (start_ < end_time <= stop_):
                _is_available = False
                break
        for lesson in lessons:
            start_ = lesson.booked_datetime
            stop_ = start_ + timedelta(minutes=lesson.registration.course.duration)
            if (start_ <= current_time < stop_) or (start_ < end_time <= stop_):
                _is_available = False
                break
        for lesson in guest_lessons:
            start_ = lesson.datetime
            stop_ = start_ + timedelta(minutes=lesson.duration)
            if (start_ <= current_time < stop_) or (start_ < end_time <= stop_):
                _is_available = False
                break
        if _is_available:
            available_times.append({
                "start": current_time.strftime("%H:%M:%S"),
                "end": end_time.strftime("%H:%M:%S")
            })
        current_time += interval
    return available_times

def is_available(unavailables:List[UnavailableTimeOneTime], lessons:List[Lesson], guest_lessons:List[GuestLesson], date_time, start, stop, duration):
    start_time = timezone.make_aware(date_time)
    end_time = start_time + timedelta(minutes=duration)
    school_start = timezone.make_aware(datetime.combine(start_time, start))
    school_close = timezone.make_aware(datetime.combine(start_time, stop))
    if not (school_start <= start_time < school_close) or not (school_start <= end_time <= school_close):
        return False
    for unavailable in unavailables:
        start_ = timezone.make_aware(datetime.combine(start_time, unavailable.start))
        stop_ = timezone.make_aware(datetime.combine(start_time, unavailable.stop))
        if (start_ <= start_time < stop_) or (start_ < end_time <= stop_):
            return False
    for lesson in lessons:
        start_ = lesson.booked_datetime
        stop_ = start_ + timedelta(minutes=duration)
        if (start_ <= start_time < stop_) or (start_ < end_time <= stop_):
            return False
    for lesson in guest_lessons:
        start_ = lesson.datetime
        stop_ = start_ + timedelta(minutes=duration)
        if (start_ <= start_time < stop_) or (start_ < end_time <= stop_):
            return False
    return True


# start_time = timezone.make_aware(booked_date)
# end_time = start_time + timedelta(minutes=regis.course.duration)
# school_start = timezone.make_aware(datetime.combine(start_time, regis.course.school.start))
# school_close = timezone.make_aware(datetime.combine(start_time, regis.course.school.stop))
# if not (school_start <= start_time < school_close) or not (school_start <= end_time <= school_close):
#     return Response({"error": "Not in operating Time"}, status=400)
# for unavailable in unavailables:
#     start_ = timezone.make_aware(datetime.combine(start_time, unavailable.start))
#     stop_ = timezone.make_aware(datetime.combine(start_time, unavailable.stop))
#     if (start_ <= start_time < stop_) or (start_ < end_time <= stop_):
#         return Response({"error": "Invalid Time"}, status=400)
# for lesson in booked_lessons:
#     start_ = lesson.booked_datetime
#     stop_ = start_ + timedelta(minutes=regis.course.duration)
#     if (start_ <= start_time < stop_) or (start_ < end_time <= stop_):
#         return Response({"error": "Invalid Time s"}, status=400)