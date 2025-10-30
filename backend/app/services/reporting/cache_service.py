# Cache Service - Phase B Sprint 2 Day 2
# Intelligent caching for report generation performance optimization

import redis
import json
import hashlib
import asyncio
from typing import Any, Optional, Union, Dict, List
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import pickle
import gzip

@dataclass
class CacheStats:
    """Cache statistics for monitoring"""
    hits: int = 0
    misses: int = 0
    sets: int = 0
    deletes: int = 0
    hit_rate: float = 0.0
    total_requests: int = 0

class ReportCacheService:
    """
    Intelligent caching service for report generation
    Supports multiple cache layers with automatic invalidation
    """
    
    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        self.redis_client = redis.from_url(redis_url, decode_responses=False)
        self.stats = CacheStats()
        self.default_ttl = 3600  # 1 hour
        self.compression_threshold = 1024  # Compress data larger than 1KB
        
    async def get(self, key: str) -> Optional[Any]:
        """
        Get data from cache with automatic decompression
        
        Args:
            key: Cache key
            
        Returns:
            Cached data or None if not found
        """
        try:
            # Get from Redis
            cached_data = self.redis_client.get(key)
            
            if cached_data is None:
                self.stats.misses += 1
                self.stats.total_requests += 1
                self._update_hit_rate()
                return None
            
            # Decompress if needed
            if cached_data.startswith(b'GZIP:'):
                cached_data = gzip.decompress(cached_data[5:])
            
            # Deserialize
            data = pickle.loads(cached_data)
            
            self.stats.hits += 1
            self.stats.total_requests += 1
            self._update_hit_rate()
            
            return data
            
        except Exception as e:
            print(f"Cache get error for key {key}: {e}")
            self.stats.misses += 1
            self.stats.total_requests += 1
            self._update_hit_rate()
            return None
    
    async def set(self, key: str, data: Any, ttl: Optional[int] = None) -> bool:
        """
        Set data in cache with automatic compression
        
        Args:
            key: Cache key
            data: Data to cache
            ttl: Time to live in seconds
            
        Returns:
            Success status
        """
        try:
            # Serialize data
            serialized_data = pickle.dumps(data)
            
            # Compress if data is large
            if len(serialized_data) > self.compression_threshold:
                compressed_data = gzip.compress(serialized_data)
                final_data = b'GZIP:' + compressed_data
            else:
                final_data = serialized_data
            
            # Set with TTL
            cache_ttl = ttl or self.default_ttl
            result = self.redis_client.setex(key, cache_ttl, final_data)
            
            if result:
                self.stats.sets += 1
            
            return bool(result)
            
        except Exception as e:
            print(f"Cache set error for key {key}: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete data from cache"""
        try:
            result = self.redis_client.delete(key)
            if result:
                self.stats.deletes += 1
            return bool(result)
        except Exception as e:
            print(f"Cache delete error for key {key}: {e}")
            return False
    
    async def invalidate_pattern(self, pattern: str) -> int:
        """
        Invalidate cache entries matching a pattern
        
        Args:
            pattern: Redis key pattern (supports wildcards)
            
        Returns:
            Number of keys deleted
        """
        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                deleted = self.redis_client.delete(*keys)
                self.stats.deletes += deleted
                return deleted
            return 0
        except Exception as e:
            print(f"Cache invalidate pattern error for {pattern}: {e}")
            return 0
    
    def generate_template_cache_key(self, template_id: int, parameters: Dict[str, Any]) -> str:
        """Generate cache key for template data"""
        param_string = json.dumps(parameters, sort_keys=True, default=str)
        param_hash = hashlib.md5(param_string.encode()).hexdigest()
        return f"template_data:{template_id}:{param_hash}"
    
    def generate_chart_cache_key(self, chart_type: str, data_hash: str) -> str:
        """Generate cache key for chart data"""
        return f"chart_data:{chart_type}:{data_hash}"
    
    def generate_report_cache_key(self, template_id: int, parameters: Dict[str, Any], format_type: str) -> str:
        """Generate cache key for generated reports"""
        param_string = json.dumps(parameters, sort_keys=True, default=str)
        param_hash = hashlib.md5(param_string.encode()).hexdigest()
        return f"report_file:{template_id}:{format_type}:{param_hash}"
    
    async def cache_template_data(self, template_id: int, parameters: Dict[str, Any], 
                                 data: Dict[str, Any], ttl: int = 1800) -> bool:
        """Cache processed template data (30 min default TTL)"""
        cache_key = self.generate_template_cache_key(template_id, parameters)
        return await self.set(cache_key, data, ttl)
    
    async def get_template_data(self, template_id: int, parameters: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Get cached template data"""
        cache_key = self.generate_template_cache_key(template_id, parameters)
        return await self.get(cache_key)
    
    async def cache_chart_data(self, chart_type: str, data: Dict[str, Any], 
                              processed_data: Any, ttl: int = 3600) -> bool:
        """Cache processed chart data (1 hour default TTL)"""
        data_string = json.dumps(data, sort_keys=True, default=str)
        data_hash = hashlib.md5(data_string.encode()).hexdigest()
        cache_key = self.generate_chart_cache_key(chart_type, data_hash)
        return await self.set(cache_key, processed_data, ttl)
    
    async def get_chart_data(self, chart_type: str, data: Dict[str, Any]) -> Optional[Any]:
        """Get cached chart data"""
        data_string = json.dumps(data, sort_keys=True, default=str)
        data_hash = hashlib.md5(data_string.encode()).hexdigest()
        cache_key = self.generate_chart_cache_key(chart_type, data_hash)
        return await self.get(cache_key)
    
    async def invalidate_template_cache(self, template_id: int) -> int:
        """Invalidate all cache entries for a specific template"""
        pattern = f"template_data:{template_id}:*"
        return await self.invalidate_pattern(pattern)
    
    async def invalidate_report_cache(self, template_id: int) -> int:
        """Invalidate all cached reports for a specific template"""
        pattern = f"report_file:{template_id}:*"
        return await self.invalidate_pattern(pattern)
    
    def get_stats(self) -> CacheStats:
        """Get cache statistics"""
        return self.stats
    
    def _update_hit_rate(self):
        """Update hit rate calculation"""
        if self.stats.total_requests > 0:
            self.stats.hit_rate = self.stats.hits / self.stats.total_requests
    
    async def health_check(self) -> Dict[str, Any]:
        """Check cache service health"""
        try:
            # Test basic operations
            test_key = "health_check_test"
            test_data = {"timestamp": datetime.now().isoformat()}
            
            # Test set
            set_result = await self.set(test_key, test_data, 60)
            
            # Test get
            get_result = await self.get(test_key)
            
            # Test delete
            delete_result = await self.delete(test_key)
            
            # Get Redis info
            info = self.redis_client.info()
            
            return {
                "status": "healthy",
                "operations": {
                    "set": set_result,
                    "get": get_result is not None,
                    "delete": delete_result
                },
                "stats": asdict(self.stats),
                "redis_info": {
                    "connected_clients": info.get("connected_clients"),
                    "used_memory_human": info.get("used_memory_human"),
                    "keyspace_hits": info.get("keyspace_hits"),
                    "keyspace_misses": info.get("keyspace_misses")
                }
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "stats": asdict(self.stats)
            }

class CacheWarmer:
    """Cache warming service for preloading frequently used data"""
    
    def __init__(self, cache_service: ReportCacheService, data_aggregator):
        self.cache_service = cache_service
        self.data_aggregator = data_aggregator
    
    async def warm_template_cache(self, template_id: int, 
                                 common_parameters: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Warm cache for a template with common parameter combinations
        
        Args:
            template_id: Template to warm cache for
            common_parameters: List of common parameter combinations
            
        Returns:
            Warming results
        """
        results = {
            "template_id": template_id,
            "total_combinations": len(common_parameters),
            "successful_warming": 0,
            "failed_warming": 0,
            "warming_time_ms": 0
        }
        
        start_time = datetime.now()
        
        for params in common_parameters:
            try:
                # Check if already cached
                cached_data = await self.cache_service.get_template_data(template_id, params)
                
                if cached_data is None:
                    # Generate and cache data
                    # This would integrate with the data aggregation service
                    # For now, we'll create a placeholder
                    warming_data = {
                        "template_id": template_id,
                        "parameters": params,
                        "warmed_at": datetime.now().isoformat(),
                        "data": "placeholder_warm_data"
                    }
                    
                    success = await self.cache_service.cache_template_data(
                        template_id, params, warming_data
                    )
                    
                    if success:
                        results["successful_warming"] += 1
                    else:
                        results["failed_warming"] += 1
                else:
                    results["successful_warming"] += 1
                    
            except Exception as e:
                print(f"Cache warming error for template {template_id}: {e}")
                results["failed_warming"] += 1
        
        results["warming_time_ms"] = int((datetime.now() - start_time).total_seconds() * 1000)
        return results
    
    async def warm_dashboard_caches(self) -> Dict[str, Any]:
        """Warm caches for common dashboard data"""
        # Define common dashboard parameter combinations
        common_periods = [7, 30, 90]  # days
        common_departments = [None, 1, 2, 3]  # None = all departments
        
        warming_tasks = []
        
        # Warm common analytics queries
        for period in common_periods:
            for dept_id in common_departments:
                params = {"period_days": period}
                if dept_id:
                    params["department_id"] = dept_id
                
                # Create cache keys for common analytics endpoints
                cache_keys = [
                    f"analytics_quality_{period}_{dept_id}",
                    f"analytics_training_{period}_{dept_id}",
                    f"analytics_documents_{period}_{dept_id}"
                ]
                
                for cache_key in cache_keys:
                    # Cache placeholder data (in production, this would call real APIs)
                    warming_data = {
                        "cache_key": cache_key,
                        "period": period,
                        "department_id": dept_id,
                        "warmed_at": datetime.now().isoformat(),
                        "data": f"warm_data_for_{cache_key}"
                    }
                    
                    warming_tasks.append(
                        self.cache_service.set(cache_key, warming_data, 1800)  # 30 min TTL
                    )
        
        # Execute all warming tasks
        results = await asyncio.gather(*warming_tasks, return_exceptions=True)
        
        successful = sum(1 for r in results if r is True)
        failed = len(results) - successful
        
        return {
            "cache_type": "dashboard_data",
            "total_items": len(results),
            "successful": successful,
            "failed": failed,
            "success_rate": (successful / len(results)) * 100 if results else 0
        }

# Global cache service instance
_cache_service = None

def get_cache_service() -> ReportCacheService:
    """Get or create global cache service instance"""
    global _cache_service
    if _cache_service is None:
        _cache_service = ReportCacheService()
    return _cache_service