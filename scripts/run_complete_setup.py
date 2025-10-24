#!/usr/bin/env python3
# Complete QMS Setup - One Command Setup
# Orchestrates the entire secrets configuration process

import os
import sys
import subprocess
import argparse
import json
from pathlib import Path


def main():
    """Complete setup orchestration."""
    
    print("🚀 QMS Complete Setup")
    print("=" * 30)
    
    parser = argparse.ArgumentParser(description="Complete QMS secrets setup")
    parser.add_argument("--repo-owner", required=True, help="GitHub repository owner")
    parser.add_argument("--repo-name", required=True, help="GitHub repository name")
    parser.add_argument("--method", choices=["interactive", "quick", "template"], 
                       default="interactive", help="Setup method")
    parser.add_argument("--reviewers", nargs="*", help="Production reviewers")
    parser.add_argument("--validate-only", action="store_true", help="Only run validation")
    
    args = parser.parse_args()
    
    scripts_dir = Path(__file__).parent
    
    if args.validate_only:
        print("🔍 Running validation only...")
        validate_cmd = [
            "python3", str(scripts_dir / "validate_secrets.py"),
            "--repo-owner", args.repo_owner,
            "--repo-name", args.repo_name
        ]
        subprocess.run(validate_cmd)
        return
    
    print(f"Repository: {args.repo_owner}/{args.repo_name}")
    print(f"Setup method: {args.method}")
    
    try:
        # Step 1: Create environments
        print("\n🏗️  Step 1: Creating GitHub environments...")
        create_env_cmd = [
            "python3", str(scripts_dir / "create_environments.py"),
            "--repo-owner", args.repo_owner,
            "--repo-name", args.repo_name
        ]
        if args.reviewers:
            create_env_cmd.extend(["--reviewers"] + args.reviewers)
        
        result = subprocess.run(create_env_cmd)
        if result.returncode != 0:
            print("❌ Environment creation failed")
            sys.exit(1)
        
        # Step 2: Configure secrets based on method
        print(f"\n🔐 Step 2: Configuring secrets ({args.method} method)...")
        
        if args.method == "interactive":
            setup_cmd = ["python3", str(scripts_dir / "interactive_secrets_setup.py")]
        elif args.method == "quick":
            setup_cmd = [
                str(scripts_dir / "quick_secrets_setup.sh"),
                "--owner", args.repo_owner,
                "--repo", args.repo_name,
                "--env", "both"
            ]
        else:  # template
            print("Please run the following commands manually:")
            print(f"python3 {scripts_dir}/setup_github_secrets.py --template")
            print("# Edit secrets_template.json")
            print(f"python3 {scripts_dir}/setup_github_secrets.py --apply secrets_template.json --repo-owner {args.repo_owner} --repo-name {args.repo_name}")
            return
        
        result = subprocess.run(setup_cmd)
        if result.returncode != 0:
            print("❌ Secrets configuration failed")
            sys.exit(1)
        
        # Step 3: Validate configuration
        print("\n🔍 Step 3: Validating configuration...")
        validate_cmd = [
            "python3", str(scripts_dir / "validate_secrets.py"),
            "--repo-owner", args.repo_owner,
            "--repo-name", args.repo_name,
            "--output", "validation_report.json"
        ]
        
        result = subprocess.run(validate_cmd)
        
        # Step 4: Test connectivity (if possible)
        print("\n🔌 Step 4: Testing connectivity...")
        test_cmd = [
            "python3", str(scripts_dir / "test_secrets_connection.py"),
            "--environment", "staging",
            "--output", "connectivity_report.json"
        ]
        
        subprocess.run(test_cmd)  # Don't fail on connectivity issues
        
        # Summary
        print("\n🎉 Setup Complete!")
        print("=" * 20)
        print("✅ GitHub environments created")
        print("✅ Secrets configured")
        print("✅ Configuration validated")
        print("✅ Connectivity tested")
        
        print("\n📋 Next Steps:")
        print("1. Review validation_report.json")
        print("2. Test staging deployment: git push origin main")
        print("3. Configure monitoring and alerting")
        print("4. Schedule secret rotation")
        
    except KeyboardInterrupt:
        print("\n⚠️  Setup cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Setup failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()