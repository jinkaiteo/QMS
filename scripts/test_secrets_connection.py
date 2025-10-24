#!/usr/bin/env python3
# Test GitHub Secrets Connectivity
# Validates that configured secrets work correctly

import os
import sys
import json
import requests
import subprocess
import psycopg2
import redis
from typing import Dict, List, Tuple, Optional
import argparse
from datetime import datetime


class SecretsConnectivityTester:
    """Test connectivity using configured secrets."""
    
    def __init__(self, environment: str = "staging"):
        self.environment = environment
        self.test_results = {}
    
    def test_database_connection(self, database_url: str) -> Dict[str, any]:
        """Test PostgreSQL database connectivity."""
        print(f"🔍 Testing {self.environment} database connection...")
        
        try:
            # Parse connection string
            conn = psycopg2.connect(database_url)
            cursor = conn.cursor()
            
            # Test basic query
            cursor.execute("SELECT version();")
            version = cursor.fetchone()[0]
            
            # Test QMS specific tables (if they exist)
            cursor.execute("""
                SELECT COUNT(*) FROM information_schema.tables 
                WHERE table_schema = 'public' AND table_name = 'users';
            """)
            users_table_exists = cursor.fetchone()[0] > 0
            
            cursor.close()
            conn.close()
            
            return {
                "status": "success",
                "version": version,
                "qms_tables": users_table_exists,
                "message": "Database connection successful"
            }
            
        except psycopg2.Error as e:
            return {
                "status": "error",
                "error": str(e),
                "message": "Database connection failed"
            }
        except Exception as e:
            return {
                "status": "error", 
                "error": str(e),
                "message": "Unexpected database error"
            }
    
    def test_redis_connection(self, redis_url: str) -> Dict[str, any]:
        """Test Redis connectivity."""
        print(f"🔍 Testing {self.environment} Redis connection...")
        
        try:
            r = redis.from_url(redis_url)
            
            # Test basic operations
            test_key = f"qms_test_{self.environment}"
            test_value = f"test_value_{datetime.now().timestamp()}"
            
            # Set and get test value
            r.set(test_key, test_value, ex=30)  # Expire in 30 seconds
            retrieved_value = r.get(test_key)
            
            # Get Redis info
            info = r.info()
            
            # Cleanup
            r.delete(test_key)
            
            if retrieved_value and retrieved_value.decode() == test_value:
                return {
                    "status": "success",
                    "version": info.get("redis_version"),
                    "memory_used": info.get("used_memory_human"),
                    "message": "Redis connection successful"
                }
            else:
                return {
                    "status": "error",
                    "message": "Redis read/write test failed"
                }
                
        except redis.RedisError as e:
            return {
                "status": "error",
                "error": str(e),
                "message": "Redis connection failed"
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "message": "Unexpected Redis error"
            }
    
    def test_api_connectivity(self, api_url: str) -> Dict[str, any]:
        """Test API endpoint connectivity."""
        print(f"🔍 Testing {self.environment} API connectivity...")
        
        try:
            # Test health endpoint
            health_url = f"{api_url}/health"
            response = requests.get(health_url, timeout=10)
            
            if response.status_code == 200:
                health_data = response.json()
                
                # Test system info endpoint
                info_url = f"{api_url}/api/v1/system/info"
                info_response = requests.get(info_url, timeout=10)
                
                return {
                    "status": "success",
                    "health_status": health_data.get("status"),
                    "api_version": health_data.get("version"),
                    "environment": health_data.get("environment"),
                    "info_endpoint": info_response.status_code == 200,
                    "message": "API connectivity successful"
                }
            else:
                return {
                    "status": "error",
                    "status_code": response.status_code,
                    "message": f"API health check failed: {response.status_code}"
                }
                
        except requests.RequestException as e:
            return {
                "status": "error",
                "error": str(e),
                "message": "API connectivity failed"
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "message": "Unexpected API error"
            }
    
    def test_kubernetes_access(self, kubeconfig_b64: str) -> Dict[str, any]:
        """Test Kubernetes cluster access."""
        print(f"🔍 Testing {self.environment} Kubernetes access...")
        
        if not kubeconfig_b64 or "CHANGE_THIS" in kubeconfig_b64:
            return {
                "status": "skipped",
                "message": "Kubeconfig not configured"
            }
        
        try:
            import base64
            import tempfile
            
            # Decode kubeconfig
            kubeconfig_data = base64.b64decode(kubeconfig_b64)
            
            # Write to temporary file
            with tempfile.NamedTemporaryFile(mode='wb', delete=False) as f:
                f.write(kubeconfig_data)
                kubeconfig_path = f.name
            
            # Test kubectl access
            env = os.environ.copy()
            env['KUBECONFIG'] = kubeconfig_path
            
            result = subprocess.run(
                ["kubectl", "cluster-info"],
                capture_output=True,
                text=True,
                env=env,
                timeout=30
            )
            
            # Cleanup
            os.unlink(kubeconfig_path)
            
            if result.returncode == 0:
                # Get namespace info
                result_ns = subprocess.run(
                    ["kubectl", "get", "namespaces"],
                    capture_output=True,
                    text=True,
                    env=env,
                    timeout=10
                )
                
                return {
                    "status": "success",
                    "cluster_info": result.stdout.strip(),
                    "namespaces_accessible": result_ns.returncode == 0,
                    "message": "Kubernetes access successful"
                }
            else:
                return {
                    "status": "error",
                    "error": result.stderr,
                    "message": "Kubernetes access failed"
                }
                
        except subprocess.TimeoutExpired:
            return {
                "status": "error",
                "message": "Kubernetes access timeout"
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "message": "Kubernetes test error"
            }
    
    def test_environment_secrets(self, api_url: str = None) -> Dict[str, Dict]:
        """Test all secrets for an environment."""
        print(f"\n🧪 Testing {self.environment.upper()} Environment Secrets")
        print("-" * 50)
        
        results = {}
        
        # Determine URLs based on environment
        if not api_url:
            if self.environment == "staging":
                api_url = "https://qms-staging.company.com"
            else:
                api_url = "https://qms.company.com"
        
        # Get secrets from environment (these would come from CI/CD context)
        database_url = os.getenv(f"{self.environment.upper()}_DATABASE_URL")
        redis_url = os.getenv(f"{self.environment.upper()}_REDIS_URL")
        kubeconfig = os.getenv(f"{self.environment.upper()}_KUBECONFIG")
        
        # Test database if URL provided
        if database_url and "CHANGE_THIS" not in database_url:
            results["database"] = self.test_database_connection(database_url)
        else:
            results["database"] = {
                "status": "skipped",
                "message": "Database URL not configured"
            }
        
        # Test Redis if URL provided
        if redis_url and "CHANGE_THIS" not in redis_url:
            results["redis"] = self.test_redis_connection(redis_url)
        else:
            results["redis"] = {
                "status": "skipped",
                "message": "Redis URL not configured"
            }
        
        # Test API connectivity
        results["api"] = self.test_api_connectivity(api_url)
        
        # Test Kubernetes if configured
        if kubeconfig:
            results["kubernetes"] = self.test_kubernetes_access(kubeconfig)
        else:
            results["kubernetes"] = {
                "status": "skipped",
                "message": "Kubeconfig not provided"
            }
        
        return results
    
    def print_test_results(self, results: Dict[str, Dict]):
        """Print formatted test results."""
        print(f"\n📊 {self.environment.upper()} Test Results")
        print("-" * 30)
        
        for service, result in results.items():
            status = result.get("status", "unknown")
            message = result.get("message", "No message")
            
            if status == "success":
                icon = "✅"
            elif status == "error":
                icon = "❌"
            elif status == "skipped":
                icon = "⏭️"
            else:
                icon = "❓"
            
            print(f"{icon} {service.title()}: {message}")
            
            # Show additional details for successful connections
            if status == "success":
                if service == "database" and "version" in result:
                    print(f"   📊 Version: {result['version'][:50]}...")
                elif service == "redis" and "version" in result:
                    print(f"   📊 Version: {result['version']}")
                    print(f"   💾 Memory: {result.get('memory_used', 'Unknown')}")
                elif service == "api" and "api_version" in result:
                    print(f"   📊 Version: {result['api_version']}")
                    print(f"   🌍 Environment: {result.get('environment', 'Unknown')}")
            
            # Show errors
            if status == "error" and "error" in result:
                error_msg = str(result["error"])
                if len(error_msg) > 100:
                    error_msg = error_msg[:100] + "..."
                print(f"   ⚠️  Error: {error_msg}")
    
    def generate_test_report(self, results: Dict[str, Dict]) -> Dict:
        """Generate comprehensive test report."""
        successful_tests = sum(1 for r in results.values() if r.get("status") == "success")
        total_tests = len([r for r in results.values() if r.get("status") != "skipped"])
        
        report = {
            "timestamp": datetime.utcnow().isoformat(),
            "environment": self.environment,
            "summary": {
                "total_tests": total_tests,
                "successful_tests": successful_tests,
                "success_rate": (successful_tests / total_tests * 100) if total_tests > 0 else 0
            },
            "results": results,
            "status": "pass" if successful_tests == total_tests else "fail"
        }
        
        return report


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Test QMS secrets connectivity")
    parser.add_argument("--environment", choices=["staging", "production"], 
                       default="staging", help="Environment to test")
    parser.add_argument("--api-url", help="API base URL override")
    parser.add_argument("--output", help="Output file for test report")
    parser.add_argument("--database-url", help="Database URL override")
    parser.add_argument("--redis-url", help="Redis URL override")
    
    args = parser.parse_args()
    
    print("🔌 QMS Secrets Connectivity Test")
    print("=" * 40)
    
    # Override environment variables if provided
    if args.database_url:
        os.environ[f"{args.environment.upper()}_DATABASE_URL"] = args.database_url
    if args.redis_url:
        os.environ[f"{args.environment.upper()}_REDIS_URL"] = args.redis_url
    
    # Create tester and run tests
    tester = SecretsConnectivityTester(args.environment)
    results = tester.test_environment_secrets(args.api_url)
    
    # Print results
    tester.print_test_results(results)
    
    # Generate report
    report = tester.generate_test_report(results)
    
    # Save report if requested
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"\n📄 Test report saved: {args.output}")
    
    # Print summary
    print(f"\n📋 Test Summary")
    print(f"Environment: {args.environment}")
    print(f"Success rate: {report['summary']['success_rate']:.1f}%")
    print(f"Tests passed: {report['summary']['successful_tests']}/{report['summary']['total_tests']}")
    
    # Exit with appropriate code
    if report["status"] == "pass":
        print("\n✅ All connectivity tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Some connectivity tests failed")
        sys.exit(1)


if __name__ == "__main__":
    main()