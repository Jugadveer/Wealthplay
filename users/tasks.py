"""
Celery tasks for users app
"""
from celery import shared_task
from django.core.management import call_command
import traceback


@shared_task
def update_ml_data_task():
    """
    Celery task to update ML data cache.
    Runs the update_ml_data management command.
    """
    try:
        call_command('update_ml_data')
        return {'status': 'success', 'message': 'ML data updated successfully'}
    except Exception as e:
        error_msg = f'Error updating ML data: {str(e)}'
        print(error_msg)
        traceback.print_exc()
        return {'status': 'error', 'message': error_msg}

