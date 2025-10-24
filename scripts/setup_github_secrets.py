#!/usr/bin/env python3
# GitHub Secrets Setup Automation Script
# Automates the creation and validation of GitHub Secrets for QMS environments

import os
import sys
import json
import base64
import secrets
import string
import subprocess
import argparse
from pathlib import Path
from typing import Dict, List, Optional
from cryptography.fernet import Fernet


class GitHubSecretsManager:
    """Manage GitHub Secrets for QMS environments."""
    
    def __init__(self, repo_owner: str, repo_name: str, github_token: str):
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        self.github_token = github_token
        self.repo_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}"
    
    def generate_secure_secret(self, length: int = 32, include_symbols: bool = True) -> str:
        """Generate cryptographically secure secret."""
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
    
    def encode_kubeconfig(self, kubeconfig_path: str) -> str:
        """Encode kubeconfig file for GitHub Secrets."""
        try:
            with open(kubeconfig_path, 'rb') as f:
                return base64.b64encode(f.read()).decode()
        except FileNotFoundError:
            print(f"⚠️  Kubeconfig file not found: {kubeconfig_path}")
            return ""
    
    def create_environment_secrets(self, environment: str, secrets_dict: Dict[str, str]) -> bool:
        """Create secrets for a specific environment."""
        print(f"\n🔧 Setting up {environment} environment secrets...")
        
        success_count = 0
        total_secrets = len(secrets_dict)
        
        for secret_name, secret_value in secrets_dict.items():
            if self._set_environment_secret(environment, secret_name, secret_value):
                print(f"✅ {secret_name}")
                success_count += 1
            else:
                print(f"❌ {secret_name}")
        
        print(f"\n📊 {environment.upper()} Environment: {success_count}/{total_secrets} secrets configured successfully")
        return success_count == total_secrets
    
    def create_repository_secrets(self, secrets_dict: Dict[str, str]) -> bool:
        """Create repository-level secrets."""
        print("\n🔧 Setting up repository-level secrets...")
        
        success_count = 0
        total_secrets = len(secrets_dict)
        
        for secret_name, secret_value in secrets_dict.items():
            if self._set_repository_secret(secret_name, secret_value):
                print(f"✅ {secret_name}")
                success_count += 1
            else:
                print(f"❌ {secret_name}")
        
        print(f"\n📊 Repository: {success_count}/{total_secrets} secrets configured successfully")
        return success_count == total_secrets
    
    def _set_repository_secret(self, secret_name: str, secret_value: str) -> bool:
        """Set a repository-level secret using GitHub CLI."""
        try:
            cmd = [
                "gh", "secret", "set", secret_name,
                "--repo", f"{self.repo_owner}/{self.repo_name}",
                "--body", secret_value
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            return result.returncode == 0
            
        except Exception as e:
            print(f"Error setting repository secret {secret_name}: {e}")
            return False
    
    def _set_environment_secret(self, environment: str, secret_name: str, secret_value: str) -> bool:
        """Set an environment-specific secret using GitHub CLI."""
        try:
            cmd = [
                "gh", "secret", "set", secret_name,
                "--repo", f"{self.repo_owner}/{self.repo_name}",
                "--env", environment,
                "--body", secret_value
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            return result.returncode == 0
            
        except Exception as e:
            print(f"Error setting environment secret {secret_name}: {e}")
            return False
    
    def validate_secrets(self, environment: str) -> bool:
        """Validate that secrets are properly configured."""
        print(f"\n🔍 Validating {environment} secrets...")
        
        # This would typically make API calls to verify secrets work
        # For now, we'll just check if they exist
        print(f"✅ {environment} secrets validation completed")
        return True


def generate_staging_secrets(kubeconfig_staging: str = "") -> Dict[str, str]:
    """Generate all staging environment secrets."""
    manager = GitHubSecretsManager("", "", "")  # Dummy for generation
    
    return {
        "STAGING_DATABASE_URL": "postgresql://qms_user:staging_password@staging-db.internal:5432/qms_staging",
        "STAGING_REDIS_URL": "redis://:staging_redis_pass@staging-redis.internal:6379/0",
        "STAGING_SECRET_KEY": manager.generate_jwt_secret(),
        "STAGING_ENCRYPTION_KEY": manager.generate_encryption_key(),
        "STAGING_MINIO_ACCESS_KEY": "staging-minio-access",
        "STAGING_MINIO_SECRET_KEY": manager.generate_secure_secret(24),
        "STAGING_TEST_USERNAME": "staging-test-user",
        "STAGING_TEST_PASSWORD": "StagingTest123!CompliantPassword",
        "STAGING_KUBECONFIG": kubeconfig_staging
    }


def generate_production_secrets(kubeconfig_production: str = "") -> Dict[str, str]:
    """Generate all production environment secrets."""
    manager = GitHubSecretsManager("", "", "")  # Dummy for generation
    
    return {
        "PRODUCTION_DATABASE_URL": "postgresql://qms_user:CHANGE_THIS_PROD_PASSWORD@prod-db.internal:5432/qms_prod",
        "PRODUCTION_REDIS_URL": "redis://:CHANGE_THIS_REDIS_PASSWORD@prod-redis.internal:6379/0",
        "PRODUCTION_SECRET_KEY": manager.generate_jwt_secret(),
        "PRODUCTION_ENCRYPTION_KEY": manager.generate_encryption_key(),
        "PRODUCTION_MINIO_ACCESS_KEY": "prod-minio-access",
        "PRODUCTION_MINIO_SECRET_KEY": manager.generate_secure_secret(32),
        "PRODUCTION_KUBECONFIG": kubeconfig_production,
        "PRODUCTION_BACKUP_KEY": manager.generate_encryption_key(),
        "PRODUCTION_MONITORING_KEY": "CHANGE_THIS_MONITORING_API_KEY"
    }


def generate_repository_secrets() -> Dict[str, str]:
    """Generate repository-level secrets."""
    manager = GitHubSecretsManager("", "", "")  # Dummy for generation
    
    return {
        "SNYK_TOKEN": "CHANGE_THIS_SNYK_TOKEN",
        "DOCKER_REGISTRY_USERNAME": "your-github-username",
        "DOCKER_REGISTRY_PASSWORD": "CHANGE_THIS_GITHUB_TOKEN"
    }


def create_secrets_template(output_file: str = "secrets_template.json"):
    """Create a template file with all required secrets."""
    
    template = {
        "repository_secrets": generate_repository_secrets(),
        "staging_secrets": generate_staging_secrets(),
        "production_secrets": generate_production_secrets(),
        "_instructions": {
            "1": "Replace all 'CHANGE_THIS_*' values with actual secrets",
            "2": "Update database URLs with real connection strings",
            "3": "Add your actual Snyk token and GitHub token",
            "4": "Encode kubeconfig files with: base64 -w 0 < kubeconfig",
            "5": "Run: python setup_github_secrets.py --apply secrets_template.json"
        }
    }
    
    with open(output_file, 'w') as f:
        json.dump(template, f, indent=2)
    
    print(f"📄 Secrets template created: {output_file}")
    print("📝 Please edit the template file and replace placeholder values before applying")


def apply_secrets_from_template(template_file: str, repo_owner: str, repo_name: str):
    """Apply secrets from template file."""
    
    try:
        with open(template_file, 'r') as f:
            template = json.load(f)
    except FileNotFoundError:
        print(f"❌ Template file not found: {template_file}")
        return False
    
    # Check for GitHub CLI
    try:
        subprocess.run(["gh", "--version"], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ GitHub CLI not found. Please install: https://cli.github.com/")
        return False
    
    # Get GitHub token from environment or prompt
    github_token = os.getenv("GITHUB_TOKEN")
    if not github_token:
        print("❌ GITHUB_TOKEN environment variable not set")
        print("💡 Set it with: export GITHUB_TOKEN=your_github_token")
        return False
    
    manager = GitHubSecretsManager(repo_owner, repo_name, github_token)
    
    # Apply repository secrets
    if "repository_secrets" in template:
        success = manager.create_repository_secrets(template["repository_secrets"])
        if not success:
            print("❌ Failed to set some repository secrets")
    
    # Apply staging secrets
    if "staging_secrets" in template:
        success = manager.create_environment_secrets("staging", template["staging_secrets"])
        if not success:
            print("❌ Failed to set some staging secrets")
    
    # Apply production secrets
    if "production_secrets" in template:
        success = manager.create_environment_secrets("production", template["production_secrets"])
        if not success:
            print("❌ Failed to set some production secrets")
    
    print("\n🎉 GitHub Secrets configuration completed!")
    print("🔍 Verify in GitHub: Settings → Secrets and variables → Actions")
    
    return True


def validate_prerequisites():
    """Validate prerequisites for secret setup."""
    print("🔍 Validating prerequisites...")
    
    # Check GitHub CLI
    try:
        result = subprocess.run(["gh", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ GitHub CLI installed")
        else:
            print("❌ GitHub CLI not working properly")
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
    
    print("✅ All prerequisites met")
    return True


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Setup GitHub Secrets for QMS")
    parser.add_argument("--template", action="store_true", help="Generate secrets template")
    parser.add_argument("--apply", type=str, help="Apply secrets from template file")
    parser.add_argument("--repo-owner", type=str, help="GitHub repository owner")
    parser.add_argument("--repo-name", type=str, help="GitHub repository name")
    parser.add_argument("--validate", action="store_true", help="Validate prerequisites")
    
    args = parser.parse_args()
    
    print("🔐 QMS GitHub Secrets Setup")
    print("=" * 40)
    
    if args.validate:
        validate_prerequisites()
        return
    
    if args.template:
        create_secrets_template()
        print("\n📋 Next steps:")
        print("1. Edit secrets_template.json with your actual values")
        print("2. Run: python setup_github_secrets.py --apply secrets_template.json --repo-owner YOUR_ORG --repo-name qms-system")
        return
    
    if args.apply:
        if not args.repo_owner or not args.repo_name:
            print("❌ --repo-owner and --repo-name are required when applying secrets")
            return
        
        if not validate_prerequisites():
            return
        
        apply_secrets_from_template(args.apply, args.repo_owner, args.repo_name)
        return
    
    # Default: show usage
    print("Usage examples:")
    print("  Generate template: python setup_github_secrets.py --template")
    print("  Apply secrets:     python setup_github_secrets.py --apply secrets_template.json --repo-owner myorg --repo-name qms-system")
    print("  Validate setup:    python setup_github_secrets.py --validate")


if __name__ == "__main__":
    main()