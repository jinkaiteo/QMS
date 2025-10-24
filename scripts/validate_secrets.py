#!/usr/bin/env python3
# GitHub Secrets Validation Script
# Validates that all required secrets are properly configured

import os
import sys
import json
import requests
import subprocess
from typing import Dict, List, Tuple, Optional
from pathlib import Path


class SecretsValidator:
    """Validate GitHub Secrets configuration."""
    
    def __init__(self, repo_owner: str, repo_name: str):
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        self.repo_full_name = f"{repo_owner}/{repo_name}"
    
    def validate_github_cli_auth(self) -> bool:
        """Validate GitHub CLI authentication."""
        try:
            result = subprocess.run(
                ["gh", "auth", "status"], 
                capture_output=True, 
                text=True
            )
            return result.returncode == 0
        except FileNotFoundError:
            print("❌ GitHub CLI not found")
            return False
    
    def get_repository_secrets(self) -> List[str]:
        """Get list of repository secrets."""
        try:
            result = subprocess.run(
                ["gh", "secret", "list", "--repo", self.repo_full_name],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                # Parse the output to extract secret names
                secrets = []
                for line in result.stdout.strip().split('\n'):
                    if line and '\t' in line:
                        secret_name = line.split('\t')[0]
                        secrets.append(secret_name)
                return secrets
            else:
                print(f"❌ Failed to list repository secrets: {result.stderr}")
                return []
                
        except Exception as e:
            print(f"❌ Error getting repository secrets: {e}")
            return []
    
    def get_environment_secrets(self, environment: str) -> List[str]:
        """Get list of environment secrets."""
        try:
            result = subprocess.run(
                ["gh", "secret", "list", "--repo", self.repo_full_name, "--env", environment],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                secrets = []
                for line in result.stdout.strip().split('\n'):
                    if line and '\t' in line:
                        secret_name = line.split('\t')[0]
                        secrets.append(secret_name)
                return secrets
            else:
                print(f"❌ Failed to list {environment} secrets: {result.stderr}")
                return []
                
        except Exception as e:
            print(f"❌ Error getting {environment} secrets: {e}")
            return []
    
    def validate_required_secrets(self) -> Dict[str, Dict[str, bool]]:
        """Validate all required secrets are present."""
        
        # Define required secrets for each scope
        required_repo_secrets = [
            "SNYK_TOKEN",
            "DOCKER_REGISTRY_USERNAME", 
            "DOCKER_REGISTRY_PASSWORD"
        ]
        
        required_staging_secrets = [
            "STAGING_DATABASE_URL",
            "STAGING_REDIS_URL",
            "STAGING_SECRET_KEY",
            "STAGING_ENCRYPTION_KEY",
            "STAGING_MINIO_ACCESS_KEY",
            "STAGING_MINIO_SECRET_KEY",
            "STAGING_TEST_USERNAME",
            "STAGING_TEST_PASSWORD",
            "STAGING_KUBECONFIG"
        ]
        
        required_production_secrets = [
            "PRODUCTION_DATABASE_URL",
            "PRODUCTION_REDIS_URL", 
            "PRODUCTION_SECRET_KEY",
            "PRODUCTION_ENCRYPTION_KEY",
            "PRODUCTION_MINIO_ACCESS_KEY",
            "PRODUCTION_MINIO_SECRET_KEY",
            "PRODUCTION_KUBECONFIG",
            "PRODUCTION_BACKUP_KEY",
            "PRODUCTION_MONITORING_KEY"
        ]
        
        # Get actual secrets
        repo_secrets = self.get_repository_secrets()
        staging_secrets = self.get_environment_secrets("staging")
        production_secrets = self.get_environment_secrets("production")
        
        # Validate each category
        validation_results = {
            "repository": {},
            "staging": {},
            "production": {}
        }
        
        # Check repository secrets
        for secret in required_repo_secrets:
            validation_results["repository"][secret] = secret in repo_secrets
        
        # Check staging secrets  
        for secret in required_staging_secrets:
            validation_results["staging"][secret] = secret in staging_secrets
        
        # Check production secrets
        for secret in required_production_secrets:
            validation_results["production"][secret] = secret in production_secrets
        
        return validation_results
    
    def test_api_connectivity(self, environment: str, api_url: str) -> bool:
        """Test API connectivity for an environment."""
        try:
            health_url = f"{api_url}/health"
            response = requests.get(health_url, timeout=10)
            
            if response.status_code == 200:
                health_data = response.json()
                return health_data.get("status") == "healthy"
            else:
                print(f"❌ {environment} API health check failed: {response.status_code}")
                return False
                
        except requests.RequestException as e:
            print(f"❌ {environment} API connectivity failed: {e}")
            return False
    
    def validate_secret_strength(self, secret_name: str, min_length: int = 16) -> bool:
        """Validate secret strength (placeholder - cannot actually read secrets)."""
        # Note: We cannot actually read the secret values from GitHub
        # This is a placeholder for validation logic that would run in the application
        print(f"ℹ️  {secret_name}: Strength validation requires application-level testing")
        return True
    
    def generate_validation_report(self) -> Dict:
        """Generate comprehensive validation report."""
        print("🔍 Starting GitHub Secrets validation...")
        
        # Check prerequisites
        if not self.validate_github_cli_auth():
            return {"error": "GitHub CLI authentication failed"}
        
        # Validate secrets presence
        secrets_validation = self.validate_required_secrets()
        
        # Calculate summary statistics
        total_secrets = 0
        configured_secrets = 0
        
        for scope, secrets in secrets_validation.items():
            scope_total = len(secrets)
            scope_configured = sum(1 for configured in secrets.values() if configured)
            
            total_secrets += scope_total
            configured_secrets += scope_configured
            
            print(f"\n📊 {scope.upper()} Secrets: {scope_configured}/{scope_total} configured")
            
            for secret_name, is_configured in secrets.items():
                status = "✅" if is_configured else "❌"
                print(f"  {status} {secret_name}")
        
        # Test environment connectivity (if URLs provided)
        environment_tests = {}
        
        staging_url = os.getenv("STAGING_API_URL", "https://qms-staging.company.com")
        production_url = os.getenv("PRODUCTION_API_URL", "https://qms.company.com")
        
        print(f"\n🌐 Testing environment connectivity...")
        environment_tests["staging"] = self.test_api_connectivity("staging", staging_url)
        environment_tests["production"] = self.test_api_connectivity("production", production_url)
        
        # Compile report
        report = {
            "timestamp": "2024-01-01T00:00:00Z",  # Would use actual timestamp
            "repository": self.repo_full_name,
            "summary": {
                "total_secrets_required": total_secrets,
                "secrets_configured": configured_secrets,
                "configuration_percentage": (configured_secrets / total_secrets) * 100 if total_secrets > 0 else 0
            },
            "secrets_validation": secrets_validation,
            "environment_tests": environment_tests,
            "recommendations": self._generate_recommendations(secrets_validation, environment_tests)
        }
        
        return report
    
    def _generate_recommendations(self, secrets_validation: Dict, environment_tests: Dict) -> List[str]:
        """Generate recommendations based on validation results."""
        recommendations = []
        
        # Check for missing secrets
        for scope, secrets in secrets_validation.items():
            missing_secrets = [name for name, configured in secrets.items() if not configured]
            if missing_secrets:
                recommendations.append(
                    f"Configure missing {scope} secrets: {', '.join(missing_secrets)}"
                )
        
        # Check environment connectivity
        for env, is_healthy in environment_tests.items():
            if not is_healthy:
                recommendations.append(
                    f"Fix {env} environment connectivity issues"
                )
        
        # General recommendations
        if not recommendations:
            recommendations.append("All secrets configured successfully - consider regular rotation schedule")
        else:
            recommendations.append("Review and update missing secrets before deployment")
            recommendations.append("Test environment connectivity after secret updates")
        
        return recommendations


def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Validate GitHub Secrets configuration")
    parser.add_argument("--repo-owner", required=True, help="GitHub repository owner")
    parser.add_argument("--repo-name", required=True, help="GitHub repository name")
    parser.add_argument("--output", help="Output file for validation report (JSON)")
    parser.add_argument("--staging-url", help="Staging API URL for connectivity test")
    parser.add_argument("--production-url", help="Production API URL for connectivity test")
    
    args = parser.parse_args()
    
    # Set environment URLs if provided
    if args.staging_url:
        os.environ["STAGING_API_URL"] = args.staging_url
    if args.production_url:
        os.environ["PRODUCTION_API_URL"] = args.production_url
    
    print("🔐 QMS GitHub Secrets Validation")
    print("=" * 40)
    
    # Create validator and run validation
    validator = SecretsValidator(args.repo_owner, args.repo_name)
    report = validator.generate_validation_report()
    
    # Handle errors
    if "error" in report:
        print(f"\n❌ Validation failed: {report['error']}")
        sys.exit(1)
    
    # Print summary
    print(f"\n📋 VALIDATION SUMMARY")
    print("=" * 40)
    print(f"Repository: {report['repository']}")
    print(f"Secrets configured: {report['summary']['secrets_configured']}/{report['summary']['total_secrets_required']}")
    print(f"Configuration: {report['summary']['configuration_percentage']:.1f}%")
    
    # Print recommendations
    print(f"\n💡 RECOMMENDATIONS")
    print("-" * 20)
    for i, recommendation in enumerate(report['recommendations'], 1):
        print(f"{i}. {recommendation}")
    
    # Save report if requested
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"\n📄 Validation report saved: {args.output}")
    
    # Exit with appropriate code
    if report['summary']['configuration_percentage'] == 100.0:
        print("\n✅ All secrets configured successfully!")
        sys.exit(0)
    else:
        print(f"\n⚠️  {report['summary']['total_secrets_required'] - report['summary']['secrets_configured']} secrets missing")
        sys.exit(1)


if __name__ == "__main__":
    main()