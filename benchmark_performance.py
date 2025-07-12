#!/usr/bin/env python3
"""
Comprehensive performance benchmarking script for before/after caching comparison
"""

import requests
import time
import json
import statistics
from typing import Dict, List

class PerformanceBenchmark:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.results = []
    
    def test_endpoint_performance(self, endpoint: str, method: str = "GET", data: Dict = None, iterations: int = 3) -> Dict:
        """Test an endpoint multiple times and record performance metrics"""
        times = []
        responses = []
        
        print(f"\n🧪 Testing {method} {endpoint} ({iterations} iterations)...")
        
        for i in range(iterations):
            print(f"   Iteration {i+1}/{iterations}...", end=" ")
            
            start_time = time.time()
            
            try:
                if method.upper() == "POST":
                    response = requests.post(f"{self.base_url}{endpoint}", json=data, timeout=120)
                else:
                    response = requests.get(f"{self.base_url}{endpoint}", timeout=120)
                
                end_time = time.time()
                duration = end_time - start_time
                
                times.append(duration)
                responses.append({
                    "status_code": response.status_code,
                    "response_size": len(response.content),
                    "duration": duration
                })
                
                print(f"{duration:.2f}s (Status: {response.status_code})")
                
                # Small delay between requests to avoid overwhelming the server
                if i < iterations - 1:
                    time.sleep(1)
                    
            except Exception as e:
                print(f"❌ Error: {e}")
                times.append(float('inf'))
                responses.append({"error": str(e), "duration": float('inf')})
        
        # Calculate statistics
        valid_times = [t for t in times if t != float('inf')]
        
        if valid_times:
            avg_time = statistics.mean(valid_times)
            min_time = min(valid_times)
            max_time = max(valid_times)
            std_dev = statistics.stdev(valid_times) if len(valid_times) > 1 else 0
        else:
            avg_time = min_time = max_time = std_dev = float('inf')
        
        result = {
            "endpoint": endpoint,
            "method": method,
            "iterations": iterations,
            "avg_time": avg_time,
            "min_time": min_time,
            "max_time": max_time,
            "std_dev": std_dev,
            "success_rate": len(valid_times) / iterations * 100,
            "responses": responses
        }
        
        self.results.append(result)
        return result
    
    def benchmark_full_workflow(self, scholar_id: str) -> Dict:
        """Benchmark the complete workflow for a Google Scholar profile"""
        
        print(f"\n🚀 Benchmarking Full Workflow for Scholar ID: {scholar_id}")
        print("=" * 60)
        
        # Step 1: Profile Import (includes scraping)
        import_result = self.test_endpoint_performance(
            f"/api/scholar/import/{scholar_id}", 
            method="POST",
            iterations=2  # Fewer iterations for expensive operations
        )
        
        if import_result["success_rate"] == 0:
            print("❌ Profile import failed, cannot continue with workflow test")
            return {"error": "Profile import failed"}
        
        # Extract profile ID from successful response
        try:
            # Get a successful response to extract profile ID
            for response in import_result["responses"]:
                if response.get("status_code") == 200:
                    # Make a fresh request to get the profile ID
                    fresh_response = requests.post(f"{self.base_url}/api/scholar/import/{scholar_id}")
                    if fresh_response.status_code == 200:
                        profile_data = fresh_response.json()
                        profile_id = profile_data["id"]
                        break
            else:
                raise Exception("No successful responses found")
                
        except Exception as e:
            print(f"❌ Could not extract profile ID: {e}")
            return {"error": "Could not extract profile ID"}
        
        print(f"✅ Profile ID extracted: {profile_id}")
        
        # Step 2: Publications fetch
        publications_result = self.test_endpoint_performance(
            f"/api/publications/{profile_id}",
            iterations=3
        )
        
        # Step 3: Overview Analysis
        overview_result = self.test_endpoint_performance(
            f"/api/analysis/{profile_id}/overview",
            iterations=3
        )
        
        # Step 4: Authorship Analysis
        authorship_result = self.test_endpoint_performance(
            f"/api/analysis/{profile_id}/authorship",
            iterations=3
        )
        
        # Step 5: Complete Analysis
        complete_result = self.test_endpoint_performance(
            f"/api/analysis/{profile_id}/complete",
            iterations=3
        )
        
        # Calculate total workflow time
        total_avg_time = (
            import_result["avg_time"] +
            publications_result["avg_time"] +
            overview_result["avg_time"] +
            authorship_result["avg_time"] +
            complete_result["avg_time"]
        )
        
        workflow_summary = {
            "scholar_id": scholar_id,
            "profile_id": profile_id,
            "steps": {
                "import": import_result,
                "publications": publications_result,
                "overview": overview_result,
                "authorship": authorship_result,
                "complete": complete_result
            },
            "total_avg_time": total_avg_time,
            "bottlenecks": self._identify_bottlenecks({
                "import": import_result["avg_time"],
                "publications": publications_result["avg_time"],
                "overview": overview_result["avg_time"],
                "authorship": authorship_result["avg_time"],
                "complete": complete_result["avg_time"]
            })
        }
        
        return workflow_summary
    
    def _identify_bottlenecks(self, times: Dict[str, float]) -> List[str]:
        """Identify the slowest operations"""
        sorted_times = sorted(times.items(), key=lambda x: x[1], reverse=True)
        bottlenecks = []
        
        # Mark operations that take more than 25% of total time as bottlenecks
        total_time = sum(times.values())
        threshold = total_time * 0.25
        
        for operation, time_taken in sorted_times:
            if time_taken > threshold:
                percentage = (time_taken / total_time) * 100
                bottlenecks.append(f"{operation}: {time_taken:.2f}s ({percentage:.1f}%)")
        
        return bottlenecks
    
    def print_summary(self, workflow_result: Dict):
        """Print a comprehensive performance summary"""
        
        print(f"\n📊 PERFORMANCE BENCHMARK SUMMARY")
        print("=" * 50)
        
        if "error" in workflow_result:
            print(f"❌ Benchmark failed: {workflow_result['error']}")
            return
        
        print(f"Scholar ID: {workflow_result['scholar_id']}")
        print(f"Profile ID: {workflow_result['profile_id']}")
        print(f"\n⏱️  Step-by-Step Performance:")
        
        for step_name, step_data in workflow_result["steps"].items():
            status = "✅" if step_data["success_rate"] == 100 else "⚠️ "
            print(f"  {status} {step_name.capitalize():12} {step_data['avg_time']:6.2f}s (±{step_data['std_dev']:.2f}s)")
        
        print(f"\n🎯 Total Workflow Time: {workflow_result['total_avg_time']:.2f}s")
        
        if workflow_result["bottlenecks"]:
            print(f"\n🐌 Performance Bottlenecks:")
            for bottleneck in workflow_result["bottlenecks"]:
                print(f"  • {bottleneck}")
        
        print(f"\n💡 Caching Potential:")
        cacheable_time = (
            workflow_result["steps"]["publications"]["avg_time"] +
            workflow_result["steps"]["overview"]["avg_time"] +
            workflow_result["steps"]["authorship"]["avg_time"] +
            workflow_result["steps"]["complete"]["avg_time"]
        )
        
        cache_savings_percentage = (cacheable_time / workflow_result["total_avg_time"]) * 100
        
        print(f"  • Cacheable operations: {cacheable_time:.2f}s ({cache_savings_percentage:.1f}% of total)")
        print(f"  • Estimated speedup with caching: {workflow_result['total_avg_time'] / (workflow_result['total_avg_time'] - cacheable_time + 0.1):.1f}x")
        print(f"  • Projected time with cache hits: ~{workflow_result['total_avg_time'] - cacheable_time + 0.1:.2f}s")

def main():
    benchmark = PerformanceBenchmark()
    
    print("🧪 Google Scholar Profile Analyzer - Performance Benchmark")
    print("=" * 60)
    
    # Get test subject
    scholar_id = input("Enter a Google Scholar user ID to benchmark: ").strip()
    
    if not scholar_id:
        print("Please provide a valid Google Scholar user ID")
        return
    
    # Run comprehensive benchmark
    workflow_result = benchmark.benchmark_full_workflow(scholar_id)
    
    # Print results
    benchmark.print_summary(workflow_result)
    
    # Save results to file
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    filename = f"benchmark_results_{timestamp}.json"
    
    with open(filename, 'w') as f:
        json.dump({
            "timestamp": timestamp,
            "workflow_result": workflow_result,
            "all_results": benchmark.results
        }, f, indent=2)
    
    print(f"\n💾 Results saved to: {filename}")
    print(f"\nNext: Implement caching and run again to see the improvement!")

if __name__ == "__main__":
    main()