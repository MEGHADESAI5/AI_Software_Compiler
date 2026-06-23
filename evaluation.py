import time
import json
from datetime import datetime
from typing import Dict, List  
from stage1_intent import extract_intent
from stage2_design import design_system
from stage3_generate import generate_all_schemas
from repair_engine import validate_and_repair
from runtime import validate_config

# ============================================================
# Test Dataset: 10 Product Prompts + 10 Edge Cases
# ============================================================

PRODUCT_PROMPTS = [
    "Build a CRM with login, contacts, dashboard, role-based access, and premium plan with payments",
    "Build an e-commerce store with products, shopping cart, checkout, and payment processing",
    "Build a task management app with teams, assignments, deadlines, and progress tracking",
    "Build a social media dashboard with analytics, post scheduling, and engagement metrics",
    "Build a project management tool with Gantt charts, resource allocation, and reporting",
    "Build a healthcare patient portal with appointments, medical records, and prescription management",
    "Build a learning management system with courses, quizzes, student progress, and certificates",
    "Build a real estate listing platform with property search, favorites, and agent contact",
    "Build a food delivery app with restaurants, menu browsing, ordering, and delivery tracking",
    "Build a financial dashboard with transaction history, budgeting, and spending analytics"
]

EDGE_CASE_PROMPTS = [
    # Vague
    "Build an app",
    "Make a tool",
    "Build something for users",
    
    # Conflicting
    "Build a free app with premium payments and subscriptions",
    "Make a public social network that requires login",
    "Build a completely secure system that anyone can access",
    "Build an app with no database but store all user data",
    
    # Incomplete
    "Build a blog",
    "Build a social network",
    "Build an analytics dashboard",
]

ALL_PROMPTS = PRODUCT_PROMPTS + EDGE_CASE_PROMPTS

# ============================================================
# Evaluation Function with Rate Limiting
# ============================================================

def evaluate_prompt(prompt: str, delay: float = 3.0) -> Dict:
    """
    Runs the full pipeline on a single prompt and returns metrics.
    Includes a delay to avoid rate limits.
    """
    start_time = time.time()
    retry_count = 0
    repair_count = 0
    error = None
    
    try:
        # Stage 1: Intent
        intent = extract_intent(prompt)
        time.sleep(delay)
        
        # Stage 2: Design
        design = design_system(intent)
        time.sleep(delay)
        
        # Stage 3: Generate schemas (now sequential)
        schemas = generate_all_schemas(design)
        
        db = schemas['db']
        api = schemas['api']
        ui = schemas['ui']
        auth = schemas['auth']
        
        # Stage 4: Repair (no API calls)
        repaired_db, repaired_api, repaired_ui, repaired_auth, repairs = validate_and_repair(
            db, api, ui, auth
        )
        repair_count = len(repairs)
        
        # Stage 5: Runtime validation (no API calls)
        result = validate_config(repaired_db, repaired_api, repaired_ui, repaired_auth)
        
        success = result['passed']
        passed_checks = result['passed_checks']
        total_checks = result['total_checks']
        
    except Exception as e:
        success = False
        error = str(e)
        passed_checks = 0
        total_checks = 0
    
    elapsed_time = time.time() - start_time
    
    return {
        "prompt": prompt,
        "success": success,
        "latency": elapsed_time,
        "retries": retry_count,
        "repairs": repair_count,
        "passed_checks": passed_checks,
        "total_checks": total_checks,
        "error": error
    }


def run_evaluation() -> Dict:
    """
    Runs evaluation on all prompts and generates metrics.
    """
    print("=" * 70)
    print("🧪 EVALUATION FRAMEWORK")
    print("=" * 70)
    print(f"Total prompts: {len(ALL_PROMPTS)}")
    print(f"  - Product prompts: {len(PRODUCT_PROMPTS)}")
    print(f"  - Edge cases: {len(EDGE_CASE_PROMPTS)}")
    print("=" * 70)
    print("\n⚠️  Rate limit protection: 3-second delay between API calls")
    print("⏳ This will take approximately 8-10 minutes to complete...\n")
    
    results = []
    total_api_calls = 0
    failed_api_calls = 0
    
    for idx, prompt in enumerate(ALL_PROMPTS, 1):
        print(f"\n[{idx}/{len(ALL_PROMPTS)}] Testing: {prompt[:60]}...")
        result = evaluate_prompt(prompt, delay=3.0)
        results.append(result)
        
        status = "✅" if result['success'] else "❌"
        print(f"  {status} Success: {result['success']}, "
              f"Latency: {result['latency']:.2f}s, "
              f"Repairs: {result['repairs']}, "
              f"Checks: {result['passed_checks']}/{result['total_checks']}")
        
        if result['error']:
            print(f"  ⚠️ Error: {result['error'][:100]}")
            if "429" in result['error'] or "Rate limit" in result['error']:
                failed_api_calls += 1
    
    # ============================================================
    # Generate Summary Metrics
    # ============================================================
    
    total = len(results)
    successful = sum(1 for r in results if r['success'])
    failed = total - successful
    
    total_latency = sum(r['latency'] for r in results)
    avg_latency = total_latency / total if total > 0 else 0
    
    total_repairs = sum(r['repairs'] for r in results)
    avg_repairs = total_repairs / total if total > 0 else 0
    
    total_checks_passed = sum(r['passed_checks'] for r in results)
    total_checks = sum(r['total_checks'] for r in results)
    check_pass_rate = (total_checks_passed / total_checks * 100) if total_checks > 0 else 0
    
    # Separate product vs edge case metrics
    product_results = results[:len(PRODUCT_PROMPTS)]
    edge_results = results[len(PRODUCT_PROMPTS):]
    
    product_success = sum(1 for r in product_results if r['success'])
    edge_success = sum(1 for r in edge_results if r['success'])
    
    # ============================================================
    # Print Final Report
    # ============================================================
    
    print("\n" + "=" * 70)
    print("📊 EVALUATION SUMMARY REPORT")
    print("=" * 70)
    print(f"\n📈 SUCCESS RATE:")
    print(f"   Overall: {successful}/{total} ({successful/total*100:.1f}%)")
    print(f"   Product Prompts: {product_success}/{len(PRODUCT_PROMPTS)} ({product_success/len(PRODUCT_PROMPTS)*100:.1f}%)")
    print(f"   Edge Cases: {edge_success}/{len(EDGE_CASE_PROMPTS)} ({edge_success/len(EDGE_CASE_PROMPTS)*100:.1f}%)")
    
    print(f"\n⏱️  LATENCY:")
    print(f"   Average: {avg_latency:.2f} seconds")
    print(f"   Total: {total_latency:.2f} seconds")
    
    print(f"\n🔧 REPAIRS:")
    print(f"   Total repairs made: {total_repairs}")
    print(f"   Average repairs per request: {avg_repairs:.2f}")
    
    print(f"\n✅ VALIDATION:")
    print(f"   Check pass rate: {check_pass_rate:.1f}% ({total_checks_passed}/{total_checks})")
    
    print(f"\n❌ FAILURES:")
    failed_results = [r for r in results if not r['success']]
    if failed_results:
        for r in failed_results:
            error_msg = r['error'] if r['error'] else "Unknown error"
            print(f"   - {r['prompt'][:50]}... → {error_msg[:80]}")
    else:
        print("   ✅ No failures!")
    
    print("\n" + "=" * 70)
    
    return {
        "total_prompts": total,
        "success_count": successful,
        "success_rate": successful / total * 100,
        "product_success_rate": product_success / len(PRODUCT_PROMPTS) * 100,
        "edge_success_rate": edge_success / len(EDGE_CASE_PROMPTS) * 100,
        "avg_latency": avg_latency,
        "total_latency": total_latency,
        "total_repairs": total_repairs,
        "avg_repairs": avg_repairs,
        "check_pass_rate": check_pass_rate,
        "failures": [{"prompt": r['prompt'], "error": r['error']} for r in failed_results]
    }


# ============================================================
# Run the evaluation
# ============================================================

if __name__ == "__main__":
    metrics = run_evaluation()
    
    # Save results to file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"evaluation_results_{timestamp}.json"
    
    with open(filename, 'w') as f:
        json.dump(metrics, f, indent=2)
    
    print(f"\n📁 Results saved to: {filename}")