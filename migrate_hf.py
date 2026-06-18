import os
import shutil
from pathlib import Path

def run_migration():
    app_dir = Path("/home/user/app")
    backup_dir = app_dir / "hf_backup"
    backup_dir.mkdir(exist_ok=True)
    
    print("Starting Sovereign Alpha Data Migration Backup...")
    
    # 1. Identify all data assets
    data_paths = [
        app_dir / "billing",
        app_dir / "results",
        app_dir / "zkml" / "proofs",
        app_dir / "data"
    ]
    
    # 2. Copy data assets to backup
    for path in data_paths:
        if path.exists():
            dest = backup_dir / path.name
            if path.is_dir():
                if dest.exists():
                    shutil.rmtree(dest)
                shutil.copytree(path, dest)
            else:
                shutil.copy2(path, dest)
            print(f"Backed up: {path.name}")
    
    # 3. Create a downloadable zip
    zip_path = app_dir / "sovereign_alpha_backup"
    shutil.make_archive(str(zip_path), 'zip', str(backup_dir))
    
    print("================================================================")
    print("MIGRATION BACKUP COMPLETE")
    print(f"Backup archive created at: {zip_path}.zip")
    print("Please download this zip file from the Hugging Face Files UI.")
    print("After downloading, change your Persistent Storage mount to /data.")
    print("Then upload the extracted contents to /data.")
    print("================================================================")

if __name__ == "__main__":
    run_migration()
