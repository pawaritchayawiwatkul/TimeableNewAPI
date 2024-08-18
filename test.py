from datetime import timedelta, datetime
from pprint import pprint
unavailable_periods = [
    (datetime.strptime("10:00:00", "%H:%M:%S"), datetime.strptime("11:00:00", "%H:%M:%S")),
    (datetime.strptime("14:00:00", "%H:%M:%S"), datetime.strptime("16:00:00", "%H:%M:%S"))
]

start_time = datetime.strptime("7:00:00", "%H:%M:%S")
stop_time = datetime.strptime("18:00:00", "%H:%M:%S")
# Define the duration and interval
duration = timedelta(minutes=60)
interval = timedelta(minutes=30)

available_times = []

# Generate time slots
current_time = start_time
while current_time + duration <= stop_time:
    end_time = current_time + duration
    
    # Check if the current time slot is within any unavailable periods
    is_available = True
    for unavailable_start, unavailable_stop in unavailable_periods:
        if (unavailable_start <= current_time < unavailable_stop) or (unavailable_start < end_time <= unavailable_stop):
            is_available = False
            break
    
    if is_available:
        available_times.append({
            "start": current_time.strftime("%H:%M:%S"),
            "end": end_time.strftime("%H:%M:%S")
        })
    
    # Move to the next time slot
    current_time += interval

# Output the available times
pprint(available_times)