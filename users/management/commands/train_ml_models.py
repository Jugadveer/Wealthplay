"""
Django management command to train ML models from scratch.
This prepares data and trains the direction, volatility, and regime models.
"""

from django.core.management.base import BaseCommand
from pathlib import Path
import sys
import subprocess
import os

# Add ml directory to path
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
ML_DIR = BASE_DIR / "ml"

class Command(BaseCommand):
    help = 'Train ML models (data prep + training)'

    def handle(self, *args, **options):
        self.stdout.write('='*70)
        self.stdout.write('ML MODEL TRAINING')
        self.stdout.write('='*70)
        
        # Step 1: Data Preparation
        self.stdout.write('\n[1/2] Preparing dataset...')
        try:
            # Import and run data prep
            sys.path.insert(0, str(BASE_DIR))
            from ml.data_prep import build_dataset
            
            df, features = build_dataset()
            if df is None:
                self.stdout.write(self.style.ERROR('Data preparation failed!'))
                return
                
            self.stdout.write(self.style.SUCCESS(f'✓ Dataset prepared: {len(df)} samples'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error in data preparation: {e}'))
            import traceback
            traceback.print_exc()
            return
        
        # Step 2: Model Training
        self.stdout.write('\n[2/2] Training models...')
        try:
            # Execute train.py as a separate Python process
            train_script = ML_DIR / "train.py"
            if not train_script.exists():
                self.stdout.write(self.style.ERROR(f'Train script not found: {train_script}'))
                return
            
            # Run the training script
            result = subprocess.run(
                [sys.executable, str(train_script)],
                cwd=str(BASE_DIR),
                capture_output=True,
                text=True,
                encoding='utf-8'
            )
            
            # Print output
            if result.stdout:
                self.stdout.write(result.stdout)
            if result.stderr:
                self.stdout.write(self.style.WARNING(result.stderr))
            
            if result.returncode != 0:
                self.stdout.write(self.style.ERROR(f'Training failed with exit code {result.returncode}'))
                return
            
            self.stdout.write(self.style.SUCCESS('✓ Models trained successfully!'))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error in model training: {e}'))
            import traceback
            traceback.print_exc()
            return
        
        self.stdout.write('\n' + '='*70)
        self.stdout.write(self.style.SUCCESS('TRAINING COMPLETE!'))
        self.stdout.write('='*70)
        self.stdout.write('\nModels are now available for predictions.')

