#!/usr/bin/env python3
# Interactive GitHub Secrets Configuration
# Guided setup process for QMS GitHub Secrets

import os
import sys
import json
import getpass
import subprocess
import base64
import secrets
import string
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from cryptography.fernet import Fernet


class InteractiveSecretsSetup:
    """Interactive setup for GitHub Secrets."""
    
    def __init__(self):
        self.secrets_data = {
            "repository_secrets": {},
            "staging_secrets": {},
            "production_secrets": {}
        }
        self.repo_owner = ""
        self.repo_name = ""
    
    def welcome_message(self):
        """Display welcome message and overview."""
        print("🔐 QMS GitHub Secrets Interactive Setup")
        print("=" * 50)
        print("""
This interactive setup will guide you through configuring all required 
GitHub Secrets for the QMS pharmaceutical system.

We'll configure:
• Repository-level secrets (3 secrets)
• Staging environment secrets (9 secrets) 
• Production environment secrets (9 secrets)

Security Notes:
• All passwords will be generated securely
• Sensitive data will not be displayed
• Configuration will be validated before applying
        """)
        
        input("Press Enter to continue...")
    
    def get_repository_info(self):
        """Get repository information from user."""
        print("\n📁 Repository Configuration")
        print("-" * 30)
        
        self.repo_owner = input("GitHub repository owner/organization: ").strip()
        self.repo_name = input("GitHub repository name: ").strip()
        
        if not self.repo_owner or not self.repo_name:
            print("❌ Repository owner and name are required")
            sys.exit(1)
        
        print(f"✅ Repository: {self.repo_owner}/{self.repo_name}")
    
    def validate_prerequisites(self):
        """Validate prerequisites for setup."""
        print("\n🔍 Validating Prerequisites")
        print("-" * 30)
        
        # Check GitHub CLI
        try:
            result = subprocess.run(["gh", "--version"], capture_output=True, text=True)
            if result.returncode == 0:
                print("✅ GitHub CLI installed")
            else:
                print("❌ GitHub CLI not working")
                return False
        except FileNotFoundError:
            print("❌ GitHub CLI not found")
            print("💡 Install from: https://cli.github.com/")
            return False
        
        # Check authentication
        try:
            result = subprocess.run(["gh", "auth", "status"], capture_output=True, text=True)
            if result.returncode == 0:
                print("✅ GitHub CLI authenticated")
            else:
                print("❌ GitHub CLI not authenticated")
                print("💡 Run: gh auth login")
                return False
        except Exception:
            print("❌ Cannot verify GitHub authentication")
            return False
        
        # Check repository access
        try:
            result = subprocess.run(
                ["gh", "repo", "view", f"{self.repo_owner}/{self.repo_name}"],
                capture_output=True, text=True
            )
            if result.returncode == 0:
                print("✅ Repository access confirmed")
            else:
                print("❌ Cannot access repository")
                print(f"💡 Verify repository exists: {self.repo_owner}/{self.repo_name}")
                return False
        except Exception:
            print("❌ Repository access check failed")
            return False
        
        return True
    
    def generate_secure_password(self, length: int = 24, include_symbols: bool = True) -> str:
        """Generate cryptographically secure password."""
        chars = string.ascii_letters + string.digits
        if include_symbols:
            chars += "!@#$%^&*"
        return ''.join(secrets.choice(chars) for _ in range(length))
    
    def generate_jwt_secret(self) -> str:
        """Generate JWT secret key."""
        return secrets.token_urlsafe(32)
    
    def generate_encryption_key(self) -> str:
        """Generate Fernet encryption key."""
        return Fernet.generate_key().decode()
    
    def configure_repository_secrets(self):
        """Configure repository-level secrets."""
        print("\n🔧 Repository Secrets Configuration")
        print("-" * 40)
        
        # Snyk Token
        print("\n1. Snyk Security Scanning Token")
        print("   Get from: https://app.snyk.io/account")
        snyk_token = getpass.getpass("   Enter Snyk token (hidden): ").strip()
        if not snyk_token:
            print("⚠️  Using placeholder - update later in GitHub")
            snyk_token = "CHANGE_THIS_SNYK_TOKEN"
        self.secrets_data["repository_secrets"]["SNYK_TOKEN"] = snyk_token
        
        # Docker Registry
        print("\n2. Container Registry Credentials")
        docker_username = input("   Docker/GitHub registry username: ").strip() or "github-username"
        docker_password = getpass.getpass("   Registry password/token (hidden): ").strip()
        if not docker_password:
            print("⚠️  Using placeholder - update later in GitHub")
            docker_password = "CHANGE_THIS_GITHUB_TOKEN"
        
        self.secrets_data["repository_secrets"]["DOCKER_REGISTRY_USERNAME"] = docker_username
        self.secrets_data["repository_secrets"]["DOCKER_REGISTRY_PASSWORD"] = docker_password
        
        print("✅ Repository secrets configured")
    
    def configure_database_connection(self, environment: str) -> str:
        """Configure database connection for environment."""
        print(f"\n   Database Configuration ({environment})")
        
        # Database connection details
        db_host = input(f"     Database host (default: {environment}-db.internal): ").strip()
        if not db_host:
            db_host = f"{environment}-db.internal"
        
        db_port = input("     Database port (default: 5432): ").strip() or "5432"
        db_name = input(f"     Database name (default: qms_{environment}): ").strip()
        if not db_name:
            db_name = f"qms_{environment}"
        
        db_user = input("     Database user (default: qms_user): ").strip() or "qms_user"
        
        # Generate secure password
        use_generated = input("     Generate secure password? (Y/n): ").strip().lower()
        if use_generated != 'n':
            db_password = self.generate_secure_password(24)
            print("     ✅ Secure password generated")
        else:
            db_password = getpass.getpass("     Enter database password (hidden): ").strip()
            if not db_password:
                db_password = f"CHANGE_THIS_{environment.upper()}_DB_PASSWORD"
        
        # Build connection URL
        db_url = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
        return db_url
    
    def configure_redis_connection(self, environment: str) -> str:
        """Configure Redis connection for environment."""
        print(f"\n   Redis Configuration ({environment})")
        
        redis_host = input(f"     Redis host (default: {environment}-redis.internal): ").strip()
        if not redis_host:
            redis_host = f"{environment}-redis.internal"
        
        redis_port = input("     Redis port (default: 6379): ").strip() or "6379"
        
        # Generate secure password
        use_generated = input("     Generate secure Redis password? (Y/n): ").strip().lower()
        if use_generated != 'n':
            redis_password = self.generate_secure_password(20)
            print("     ✅ Secure Redis password generated")
        else:
            redis_password = getpass.getpass("     Enter Redis password (hidden): ").strip()
            if not redis_password:
                redis_password = f"CHANGE_THIS_{environment.upper()}_REDIS_PASSWORD"
        
        redis_url = f"redis://:{redis_password}@{redis_host}:{redis_port}/0"
        return redis_url
    
    def configure_object_storage(self, environment: str) -> Tuple[str, str]:
        """Configure object storage (MinIO) for environment."""
        print(f"\n   Object Storage Configuration ({environment})")
        
        access_key = input(f"     MinIO access key (default: {environment}-minio-access): ").strip()
        if not access_key:
            access_key = f"{environment}-minio-access"
        
        # Generate secure secret key
        use_generated = input("     Generate secure MinIO secret? (Y/n): ").strip().lower()
        if use_generated != 'n':
            secret_key = self.generate_secure_password(32)
            print("     ✅ Secure MinIO secret generated")
        else:
            secret_key = getpass.getpass("     Enter MinIO secret key (hidden): ").strip()
            if not secret_key:
                secret_key = f"CHANGE_THIS_{environment.upper()}_MINIO_SECRET"
        
        return access_key, secret_key
    
    def configure_kubeconfig(self, environment: str) -> str:
        """Configure Kubernetes configuration for environment."""
        print(f"\n   Kubernetes Configuration ({environment})")
        
        kubeconfig_path = input(f"     Path to {environment} kubeconfig file (optional): ").strip()
        
        if kubeconfig_path and os.path.exists(kubeconfig_path):
            try:
                with open(kubeconfig_path, 'rb') as f:
                    kubeconfig_b64 = base64.b64encode(f.read()).decode()
                print("     ✅ Kubeconfig encoded successfully")
                return kubeconfig_b64
            except Exception as e:
                print(f"     ❌ Error reading kubeconfig: {e}")
                return f"CHANGE_THIS_{environment.upper()}_KUBECONFIG"
        else:
            print("     ⚠️  Kubeconfig not provided - using placeholder")
            return f"CHANGE_THIS_{environment.upper()}_KUBECONFIG"
    
    def configure_staging_secrets(self):
        """Configure staging environment secrets."""
        print("\n🧪 Staging Environment Secrets")
        print("-" * 35)
        
        # Database
        db_url = self.configure_database_connection("staging")
        self.secrets_data["staging_secrets"]["STAGING_DATABASE_URL"] = db_url
        
        # Redis
        redis_url = self.configure_redis_connection("staging")
        self.secrets_data["staging_secrets"]["STAGING_REDIS_URL"] = redis_url
        
        # Security keys
        print("\n   Security Keys (staging)")
        jwt_secret = self.generate_jwt_secret()
        encryption_key = self.generate_encryption_key()
        self.secrets_data["staging_secrets"]["STAGING_SECRET_KEY"] = jwt_secret
        self.secrets_data["staging_secrets"]["STAGING_ENCRYPTION_KEY"] = encryption_key
        print("     ✅ JWT and encryption keys generated")
        
        # Object storage
        minio_access, minio_secret = self.configure_object_storage("staging")
        self.secrets_data["staging_secrets"]["STAGING_MINIO_ACCESS_KEY"] = minio_access
        self.secrets_data["staging_secrets"]["STAGING_MINIO_SECRET_KEY"] = minio_secret
        
        # Test credentials
        print("\n   Test Credentials (staging)")
        test_username = input("     Test username (default: staging-test-user): ").strip()
        if not test_username:
            test_username = "staging-test-user"
        
        use_generated_test_pass = input("     Generate secure test password? (Y/n): ").strip().lower()
        if use_generated_test_pass != 'n':
            test_password = "StagingTest123!" + self.generate_secure_password(8, False)
            print("     ✅ Secure test password generated")
        else:
            test_password = getpass.getpass("     Enter test password (hidden): ").strip()
            if not test_password:
                test_password = "StagingTest123!CompliantPassword"
        
        self.secrets_data["staging_secrets"]["STAGING_TEST_USERNAME"] = test_username
        self.secrets_data["staging_secrets"]["STAGING_TEST_PASSWORD"] = test_password
        
        # Kubernetes
        kubeconfig = self.configure_kubeconfig("staging")
        self.secrets_data["staging_secrets"]["STAGING_KUBECONFIG"] = kubeconfig
        
        print("✅ Staging secrets configured")
    
    def configure_production_secrets(self):
        """Configure production environment secrets."""
        print("\n🚀 Production Environment Secrets")
        print("-" * 38)
        
        # Database
        db_url = self.configure_database_connection("production")
        self.secrets_data["production_secrets"]["PRODUCTION_DATABASE_URL"] = db_url
        
        # Redis
        redis_url = self.configure_redis_connection("production")
        self.secrets_data["production_secrets"]["PRODUCTION_REDIS_URL"] = redis_url
        
        # Security keys (always generate for production)
        print("\n   Security Keys (production)")
        jwt_secret = self.generate_jwt_secret()
        encryption_key = self.generate_encryption_key()
        backup_key = self.generate_encryption_key()
        self.secrets_data["production_secrets"]["PRODUCTION_SECRET_KEY"] = jwt_secret
        self.secrets_data["production_secrets"]["PRODUCTION_ENCRYPTION_KEY"] = encryption_key
        self.secrets_data["production_secrets"]["PRODUCTION_BACKUP_KEY"] = backup_key
        print("     ✅ Production security keys generated")
        
        # Object storage
        minio_access, minio_secret = self.configure_object_storage("production")
        self.secrets_data["production_secrets"]["PRODUCTION_MINIO_ACCESS_KEY"] = minio_access
        self.secrets_data["production_secrets"]["PRODUCTION_MINIO_SECRET_KEY"] = minio_secret
        
        # Monitoring
        print("\n   Monitoring & APM")
        monitoring_key = input("     APM/Monitoring API key (optional): ").strip()
        if not monitoring_key:
            monitoring_key = "CHANGE_THIS_PRODUCTION_MONITORING_KEY"
        self.secrets_data["production_secrets"]["PRODUCTION_MONITORING_KEY"] = monitoring_key
        
        # Kubernetes
        kubeconfig = self.configure_kubeconfig("production")
        self.secrets_data["production_secrets"]["PRODUCTION_KUBECONFIG"] = kubeconfig
        
        print("✅ Production secrets configured")
    
    def display_configuration_summary(self):
        """Display configuration summary."""
        print("\n📊 Configuration Summary")
        print("-" * 30)
        
        repo_count = len(self.secrets_data["repository_secrets"])
        staging_count = len(self.secrets_data["staging_secrets"])
        production_count = len(self.secrets_data["production_secrets"])
        total_count = repo_count + staging_count + production_count
        
        print(f"Repository secrets: {repo_count}/3")
        print(f"Staging secrets: {staging_count}/9")
        print(f"Production secrets: {production_count}/9")
        print(f"Total secrets: {total_count}/21")
        
        # Check for placeholders
        placeholders = []
        for scope, secrets in self.secrets_data.items():
            for name, value in secrets.items():
                if "CHANGE_THIS" in value:
                    placeholders.append(f"{scope}: {name}")
        
        if placeholders:
            print(f"\n⚠️  {len(placeholders)} placeholders need manual update:")
            for placeholder in placeholders[:5]:  # Show first 5
                print(f"   • {placeholder}")
            if len(placeholders) > 5:
                print(f"   • ... and {len(placeholders) - 5} more")
    
    def save_configuration(self):
        """Save configuration to file."""
        config_file = "qms_secrets_config.json"
        
        with open(config_file, 'w') as f:
            json.dump(self.secrets_data, f, indent=2)
        
        print(f"\n💾 Configuration saved to: {config_file}")
        print("⚠️  Keep this file secure - it contains sensitive data")
        
        return config_file
    
    def apply_secrets_to_github(self) -> bool:
        """Apply secrets to GitHub using GitHub CLI."""
        print("\n🚀 Applying Secrets to GitHub")
        print("-" * 35)
        
        success_count = 0
        total_count = 0
        
        # Apply repository secrets
        print("\n📁 Repository secrets...")
        for name, value in self.secrets_data["repository_secrets"].items():
            total_count += 1
            if self._set_repository_secret(name, value):
                print(f"   ✅ {name}")
                success_count += 1
            else:
                print(f"   ❌ {name}")
        
        # Apply staging secrets
        print("\n🧪 Staging environment secrets...")
        for name, value in self.secrets_data["staging_secrets"].items():
            total_count += 1
            if self._set_environment_secret("staging", name, value):
                print(f"   ✅ {name}")
                success_count += 1
            else:
                print(f"   ❌ {name}")
        
        # Apply production secrets
        print("\n🚀 Production environment secrets...")
        for name, value in self.secrets_data["production_secrets"].items():
            total_count += 1
            if self._set_environment_secret("production", name, value):
                print(f"   ✅ {name}")
                success_count += 1
            else:
                print(f"   ❌ {name}")
        
        print(f"\n📊 Applied {success_count}/{total_count} secrets successfully")
        return success_count == total_count
    
    def _set_repository_secret(self, name: str, value: str) -> bool:
        """Set repository secret using GitHub CLI."""
        try:
            cmd = [
                "gh", "secret", "set", name,
                "--repo", f"{self.repo_owner}/{self.repo_name}",
                "--body", value
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            return result.returncode == 0
            
        except Exception:
            return False
    
    def _set_environment_secret(self, environment: str, name: str, value: str) -> bool:
        """Set environment secret using GitHub CLI."""
        try:
            cmd = [
                "gh", "secret", "set", name,
                "--repo", f"{self.repo_owner}/{self.repo_name}",
                "--env", environment,
                "--body", value
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            return result.returncode == 0
            
        except Exception:
            return False
    
    def run_setup(self):
        """Run the complete interactive setup."""
        self.welcome_message()
        self.get_repository_info()
        
        if not self.validate_prerequisites():
            print("\n❌ Prerequisites not met. Please resolve and try again.")
            sys.exit(1)
        
        # Configure all secrets
        self.configure_repository_secrets()
        self.configure_staging_secrets()
        self.configure_production_secrets()
        
        # Summary and confirmation
        self.display_configuration_summary()
        
        # Save configuration
        config_file = self.save_configuration()
        
        # Confirm application
        print("\n🔐 Ready to Apply Secrets")
        print("-" * 30)
        apply = input("Apply secrets to GitHub? (y/N): ").strip().lower()
        
        if apply == 'y':
            success = self.apply_secrets_to_github()
            
            if success:
                print("\n🎉 All secrets configured successfully!")
                print(f"✅ Repository: {self.repo_owner}/{self.repo_name}")
                print("✅ Staging environment ready")
                print("✅ Production environment ready")
                
                print("\n📋 Next Steps:")
                print("1. Test staging deployment")
                print("2. Configure production reviewers")
                print("3. Run validation: python validate_secrets.py")
                print("4. Trigger CI/CD pipeline")
                
                # Clean up config file
                cleanup = input("\nDelete local config file? (Y/n): ").strip().lower()
                if cleanup != 'n':
                    os.remove(config_file)
                    print("🗑️  Local config file deleted")
                
            else:
                print("\n❌ Some secrets failed to apply")
                print(f"💾 Configuration saved in: {config_file}")
                print("🔧 Review errors and re-run setup")
        else:
            print(f"\n💾 Configuration saved in: {config_file}")
            print("🔧 Apply later with: python setup_github_secrets.py --apply")


def main():
    """Main function."""
    try:
        setup = InteractiveSecretsSetup()
        setup.run_setup()
    except KeyboardInterrupt:
        print("\n\n⚠️  Setup cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Setup failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()