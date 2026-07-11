# /app/test_task.py

from workers.tasks import process_case_task

# Replace 1 with a real Case ID from your database
task = process_case_task.delay(1)  
print("Task ID:", task.id)
