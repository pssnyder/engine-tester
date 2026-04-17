#!/usr/bin/env python3
"""
GCP Lichess Bot Deployment Script
Automates deployment of new V7P3R engine versions to production Lichess bot
"""

import subprocess
import sys
import time
from pathlib import Path
from datetime import datetime


class GCPDeployer:
    """Manages GCP VM deployments for Lichess bot"""
    
    def __init__(self, version: str, source_dir: str):
        self.version = version
        self.source_dir = Path(source_dir)
        self.vm_name = "v7p3r-production-bot"
        self.zone = "us-central1-a"
        self.container_name = "v7p3r-production"
        
    def execute_command(self, command: str, description: str):
        """Execute a shell command with error handling"""
        print(f"\n{'='*60}")
        print(f"{description}")
        print(f"{'='*60}")
        print(f"Command: {command}\n")
        
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(f"STDERR: {result.stderr}")
        
        if result.returncode != 0:
            print(f"❌ Command failed with exit code {result.returncode}")
            return False
        
        print("✅ Success")
        return True
    
    def create_tarball(self):
        """Create tarball of source files"""
        print("\n📦 STEP 1: Creating deployment tarball...")
        
        tarball_name = f"v{self.version}-src.tar.gz"
        tarball_path = self.source_dir.parent / tarball_name
        
        # Create tarball
        cmd = f'tar -czf "{tarball_path}" -C "{self.source_dir}" .'
        if not self.execute_command(cmd, "Creating tarball"):
            return None
        
        print(f"Tarball created: {tarball_path}")
        return tarball_path
    
    def upload_to_vm(self, tarball_path: Path):
        """Upload tarball to GCP VM"""
        print("\n☁️  STEP 2: Uploading to GCP VM...")
        
        cmd = f'gcloud compute scp "{tarball_path}" {self.vm_name}:/home/patss/ --zone={self.zone}'
        if not self.execute_command(cmd, "Uploading tarball to VM"):
            return False
        
        # Verify upload
        verify_cmd = f'gcloud compute ssh {self.vm_name} --zone={self.zone} --command="ls -lh /home/patss/{tarball_path.name}"'
        return self.execute_command(verify_cmd, "Verifying upload")
    
    def backup_current_version(self):
        """Backup current production version"""
        print("\n💾 STEP 3: Backing up current version...")
        
        backup_cmd = f'''gcloud compute ssh {self.vm_name} --zone={self.zone} --command="
BACKUP_DATE=$(date +%Y%m%d_%H%M%S)
sudo docker exec {self.container_name} bash -c 'tar -czf /tmp/v7p3r_backup_'\\$BACKUP_DATE'.tar.gz /lichess-bot/engines/v7p3r'
sudo docker cp {self.container_name}:/tmp/v7p3r_backup_\\$BACKUP_DATE.tar.gz /home/patss/backups/
ls -lh /home/patss/backups/v7p3r_backup_\\$BACKUP_DATE.tar.gz
"'''
        
        return self.execute_command(backup_cmd, "Creating backup")
    
    def deploy_new_version(self, tarball_name: str):
        """Deploy new version to container"""
        print("\n🚀 STEP 4: Deploying new version...")
        
        deploy_cmd = f'''gcloud compute ssh {self.vm_name} --zone={self.zone} --command="
# Copy tarball into container
sudo docker cp {tarball_name} {self.container_name}:/tmp/

# Move current version to backup
sudo docker exec {self.container_name} bash -c 'mv /lichess-bot/engines/v7p3r /lichess-bot/engines/v7p3r.backup'

# Create new directory
sudo docker exec {self.container_name} mkdir -p /lichess-bot/engines/v7p3r

# Extract new version
sudo docker exec {self.container_name} bash -c 'cd /lichess-bot/engines/v7p3r && tar -xzf /tmp/{tarball_name}'

# Verify extraction
sudo docker exec {self.container_name} ls -la /lichess-bot/engines/v7p3r/
"'''
        
        return self.execute_command(deploy_cmd, "Deploying to container")
    
    def restart_bot(self):
        """Restart the bot container"""
        print("\n🔄 STEP 5: Restarting bot...")
        
        restart_cmd = f'gcloud compute ssh {self.vm_name} --zone={self.zone} --command="sudo docker restart {self.container_name}"'
        if not self.execute_command(restart_cmd, "Restarting container"):
            return False
        
        print("Waiting 10 seconds for startup...")
        time.sleep(10)
        
        return True
    
    def verify_deployment(self):
        """Verify successful deployment"""
        print("\n✅ STEP 6: Verifying deployment...")
        
        # Check logs
        log_cmd = f'gcloud compute ssh {self.vm_name} --zone={self.zone} --command="sudo docker logs {self.container_name} --tail 50"'
        if not self.execute_command(log_cmd, "Checking logs"):
            return False
        
        # Verify UCI version
        version_cmd = f'''gcloud compute ssh {self.vm_name} --zone={self.zone} --command="
sudo docker exec {self.container_name} bash -c 'echo uci | python /lichess-bot/engines/v7p3r/v7p3r_uci.py | grep \"id name\"'
"'''
        
        return self.execute_command(version_cmd, "Verifying engine version")
    
    def rollback(self):
        """Rollback to backup version"""
        print("\n⏮️  ROLLBACK: Restoring backup...")
        
        rollback_cmd = f'''gcloud compute ssh {self.vm_name} --zone={self.zone} --command="
sudo docker exec {self.container_name} bash -c 'rm -rf /lichess-bot/engines/v7p3r'
sudo docker exec {self.container_name} bash -c 'mv /lichess-bot/engines/v7p3r.backup /lichess-bot/engines/v7p3r'
sudo docker restart {self.container_name}
"'''
        
        self.execute_command(rollback_cmd, "Rolling back to previous version")
    
    def deploy(self):
        """Execute full deployment workflow"""
        print(f"\n{'#'*70}")
        print(f"# GCP LICHESS BOT DEPLOYMENT")
        print(f"# Version: {self.version}")
        print(f"# Source: {self.source_dir}")
        print(f"# VM: {self.vm_name}")
        print(f"# Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'#'*70}")
        
        # Create tarball
        tarball_path = self.create_tarball()
        if not tarball_path:
            print("\n❌ DEPLOYMENT FAILED: Could not create tarball")
            return False
        
        # Upload
        if not self.upload_to_vm(tarball_path):
            print("\n❌ DEPLOYMENT FAILED: Could not upload to VM")
            return False
        
        # Backup
        if not self.backup_current_version():
            print("\n❌ DEPLOYMENT FAILED: Could not backup current version")
            return False
        
        # Deploy
        if not self.deploy_new_version(tarball_path.name):
            print("\n❌ DEPLOYMENT FAILED: Could not deploy new version")
            print("Would you like to rollback? (y/n): ", end="")
            if input().lower() == 'y':
                self.rollback()
            return False
        
        # Restart
        if not self.restart_bot():
            print("\n❌ DEPLOYMENT FAILED: Could not restart bot")
            print("Would you like to rollback? (y/n): ", end="")
            if input().lower() == 'y':
                self.rollback()
            return False
        
        # Verify
        if not self.verify_deployment():
            print("\n⚠️  WARNING: Deployment verification incomplete")
            print("Bot may be running but verification failed")
            print("Would you like to rollback? (y/n): ", end="")
            if input().lower() == 'y':
                self.rollback()
                return False
        
        print(f"\n{'#'*70}")
        print("# ✅ DEPLOYMENT SUCCESSFUL!")
        print(f"# Version {self.version} is now live on Lichess")
        print(f"# Monitor first 5-10 games carefully")
        print(f"# Lichess: https://lichess.org/@/v7p3r_bot")
        print(f"{'#'*70}")
        
        return True


def main():
    """Main deployment entry point"""
    if len(sys.argv) < 3:
        print("Usage: python gcp_deploy.py <version> <source_directory>")
        print("Example: python gcp_deploy.py 18.4 \"e:\\v7p3r-chess-engine\\lichess\\engines\\V7P3R_v18.4_20260415\\src\"")
        sys.exit(1)
    
    version = sys.argv[1]
    source_dir = sys.argv[2]
    
    deployer = GCPDeployer(version, source_dir)
    success = deployer.deploy()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
