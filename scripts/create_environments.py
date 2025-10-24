#!/usr/bin/env python3
# GitHub Environments Setup Script
# Creates and configures GitHub environments with protection rules

import subprocess
import json
import sys
from typing import Dict, List, Optional


class GitHubEnvironmentManager:
    """Manage GitHub environments and protection rules."""
    
    def __init__(self, repo_owner: str, repo_name: str):
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        self.repo_full_name = f"{repo_owner}/{repo_name}"
    
    def validate_github_cli(self) -> bool:
        """Validate GitHub CLI is installed and authenticated."""
        try:
            # Check GitHub CLI is installed
            result = subprocess.run(["gh", "--version"], capture_output=True, text=True)
            if result.returncode != 0:
                print("❌ GitHub CLI not found")
                return False
            
            # Check authentication
            result = subprocess.run(["gh", "auth", "status"], capture_output=True, text=True)
            if result.returncode != 0:
                print("❌ GitHub CLI not authenticated. Run: gh auth login")
                return False
            
            print("✅ GitHub CLI ready")
            return True
            
        except FileNotFoundError:
            print("❌ GitHub CLI not installed. Install from: https://cli.github.com/")
            return False
    
    def create_staging_environment(self) -> bool:
        """Create staging environment with appropriate protection rules."""
        print("🔧 Creating staging environment...")
        
        environment_config = {
            "wait_timer": 0,
            "reviewers": [],
            "deployment_branch_policy": {
                "protected_branches": False,
                "custom_branch_policies": True
            }
        }
        
        # Create environment using GitHub API via gh CLI
        try:
            # Create environment
            cmd = [
                "gh", "api", 
                f"/repos/{self.repo_full_name}/environments/staging",
                "--method", "PUT",
                "--field", f"wait_timer={environment_config['wait_timer']}"
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                print("✅ Staging environment created")
                
                # Set deployment branch policy
                self._set_deployment_branches("staging", ["main", "develop"])
                return True
            else:
                print(f"❌ Failed to create staging environment: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"❌ Error creating staging environment: {e}")
            return False
    
    def create_production_environment(self, reviewers: List[str] = None) -> bool:
        """Create production environment with protection rules."""
        print("🔧 Creating production environment...")
        
        reviewers = reviewers or []
        
        environment_config = {
            "wait_timer": 0,
            "reviewers": [{"type": "User", "id": reviewer} for reviewer in reviewers],
            "deployment_branch_policy": {
                "protected_branches": True,
                "custom_branch_policies": False
            }
        }
        
        try:
            # Create environment
            cmd = [
                "gh", "api",
                f"/repos/{self.repo_full_name}/environments/production", 
                "--method", "PUT",
                "--field", f"wait_timer={environment_config['wait_timer']}"
            ]
            
            # Add reviewers if specified
            if reviewers:
                reviewers_json = json.dumps(environment_config['reviewers'])
                cmd.extend(["--field", f"reviewers={reviewers_json}"])
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                print("✅ Production environment created")
                
                # Set deployment branch policy (main and release branches only)
                self._set_deployment_branches("production", ["main"])
                
                if reviewers:
                    print(f"✅ Added reviewers: {', '.join(reviewers)}")
                else:
                    print("⚠️  No reviewers specified - consider adding reviewers for production")
                
                return True
            else:
                print(f"❌ Failed to create production environment: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"❌ Error creating production environment: {e}")
            return False
    
    def _set_deployment_branches(self, environment: str, allowed_branches: List[str]) -> bool:
        """Set deployment branch policy for environment."""
        try:
            branch_policy = {
                "protected_branches": False,
                "custom_branch_policies": True
            }
            
            cmd = [
                "gh", "api",
                f"/repos/{self.repo_full_name}/environments/{environment}/deployment-branch-policies",
                "--method", "POST",
                "--field", f"name={allowed_branches[0]}"  # Main branch
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"✅ {environment} deployment branches configured")
                return True
            else:
                print(f"⚠️  Could not configure deployment branches for {environment}")
                return False
                
        except Exception as e:
            print(f"⚠️  Error setting deployment branches: {e}")
            return False
    
    def list_environments(self) -> List[str]:
        """List existing environments."""
        try:
            cmd = ["gh", "api", f"/repos/{self.repo_full_name}/environments"]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                data = json.loads(result.stdout)
                environments = [env["name"] for env in data.get("environments", [])]
                return environments
            else:
                print(f"❌ Failed to list environments: {result.stderr}")
                return []
                
        except Exception as e:
            print(f"❌ Error listing environments: {e}")
            return []
    
    def validate_environments(self) -> Dict[str, bool]:
        """Validate that required environments exist."""
        environments = self.list_environments()
        
        required_environments = ["staging", "production"]
        validation_results = {}
        
        for env in required_environments:
            validation_results[env] = env in environments
        
        return validation_results
    
    def setup_branch_protection(self) -> bool:
        """Set up branch protection rules for main branch."""
        print("🔧 Setting up branch protection...")
        
        protection_config = {
            "required_status_checks": {
                "strict": True,
                "contexts": [
                    "Code Quality & Security",
                    "Backend Tests", 
                    "API Integration Tests",
                    "Compliance & Audit Tests"
                ]
            },
            "enforce_admins": True,
            "required_pull_request_reviews": {
                "required_approving_review_count": 2,
                "dismiss_stale_reviews": True,
                "require_code_owner_reviews": True,
                "require_last_push_approval": True
            },
            "restrictions": None,
            "allow_force_pushes": False,
            "allow_deletions": False
        }
        
        try:
            cmd = [
                "gh", "api",
                f"/repos/{self.repo_full_name}/branches/main/protection",
                "--method", "PUT",
                "--field", "required_status_checks[strict]=true",
                "--field", "enforce_admins=true",
                "--field", "required_pull_request_reviews[required_approving_review_count]=2",
                "--field", "required_pull_request_reviews[dismiss_stale_reviews]=true",
                "--field", "allow_force_pushes=false",
                "--field", "allow_deletions=false"
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                print("✅ Branch protection configured for main branch")
                return True
            else:
                print(f"⚠️  Could not configure branch protection: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"⚠️  Error setting up branch protection: {e}")
            return False


def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Setup GitHub environments for QMS")
    parser.add_argument("--repo-owner", required=True, help="GitHub repository owner")
    parser.add_argument("--repo-name", required=True, help="GitHub repository name")
    parser.add_argument("--reviewers", nargs="*", help="Production reviewers (GitHub usernames)")
    parser.add_argument("--branch-protection", action="store_true", help="Set up branch protection")
    parser.add_argument("--validate", action="store_true", help="Validate existing environments")
    
    args = parser.parse_args()
    
    print("🏗️  QMS GitHub Environments Setup")
    print("=" * 40)
    
    # Create manager
    manager = GitHubEnvironmentManager(args.repo_owner, args.repo_name)
    
    # Validate prerequisites
    if not manager.validate_github_cli():
        sys.exit(1)
    
    if args.validate:
        # Validate existing environments
        print("🔍 Validating environments...")
        validation_results = manager.validate_environments()
        
        for env, exists in validation_results.items():
            status = "✅" if exists else "❌"
            print(f"{status} {env} environment")
        
        all_exist = all(validation_results.values())
        if all_exist:
            print("\n✅ All required environments configured")
            sys.exit(0)
        else:
            print("\n❌ Some environments missing")
            sys.exit(1)
    
    # Create environments
    success_count = 0
    
    # Create staging environment
    if manager.create_staging_environment():
        success_count += 1
    
    # Create production environment
    if manager.create_production_environment(args.reviewers):
        success_count += 1
    
    # Set up branch protection if requested
    if args.branch_protection:
        if manager.setup_branch_protection():
            print("✅ Branch protection configured")
        else:
            print("⚠️  Branch protection setup failed")
    
    # Summary
    print(f"\n📊 SETUP SUMMARY")
    print("=" * 20)
    print(f"Environments created: {success_count}/2")
    
    if success_count == 2:
        print("✅ Environment setup completed successfully!")
        print("\n📋 Next steps:")
        print("1. Configure secrets for each environment")
        print("2. Test deployments to staging")
        print("3. Set up monitoring and alerting")
        sys.exit(0)
    else:
        print("❌ Some environments failed to create")
        print("Please check the errors above and retry")
        sys.exit(1)


if __name__ == "__main__":
    main()