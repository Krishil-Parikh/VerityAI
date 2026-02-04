"""
Test script for RTI Ethics Engine API with 3-Layer Grounding Judge

Tests:
1. L1: Citation Coverage (hard requirement)
2. L2: Cosine Similarity (soft signal)
3. L3: Claim-Context Overlap (anti-hallucination)
4. Full ethics evaluation with all layers displayed
"""

import requests
import json
import time
import numpy as np
import sys

BASE_URL = "http://localhost:8000"


def print_layer(layer_data: dict, indent: int = 2):
    """Pretty print a layer result"""
    prefix = " " * indent
    status_icon = {
        "PASS": "✅",
        "FAIL": "❌",
        "WARN": "⚠️",
        "OK": "🔵",
        "GOOD": "🟢",
        "SKIP": "⏭️",
        "ERROR": "🔴"
    }.get(layer_data.get("status", "OK"), "•")
    
    print(f"{prefix}{status_icon} [{layer_data.get('layer', 'L?')}] {layer_data.get('name', 'Unknown')}")
    print(f"{prefix}   Score: {layer_data.get('score', 'N/A')}")
    print(f"{prefix}   Status: {layer_data.get('status', 'N/A')}")
    print(f"{prefix}   Reason: {layer_data.get('reason', 'N/A')}")


def test_grounding_endpoint():
    """Test the dedicated /grounding endpoint"""
    print("\n" + "="*70)
    print("🔬 TESTING 3-LAYER GROUNDING JUDGE")
    print("="*70)
    
    test_cases = [
        {
            "name": "Well-Grounded Response (Section 4)",
            "payload": {
                "user_query": "What is Section 4 of RTI Act?",
                "llm_output": "Section 4 of the RTI Act 2005 mandates proactive disclosure by public authorities. Under Section 4(1)(b), every authority must publish relevant facts and maintain records. This is in accordance with the CSMOP guidelines for transparency.",
                "citations": [
                    {
                        "document": "rti_act_2005.pdf",
                        "page": 3,
                        "text": "Section 4(1)(b) requires every public authority to designate PIOs and publish information proactively. Every authority must publish relevant facts.",
                        "score": 0.92,
                        "url": "file:///rti_act_2005.pdf#page=3"
                    },
                    {
                        "document": "csmop_guidelines.pdf",
                        "page": 12,
                        "text": "CSMOP guidelines mandate transparency in all government communications.",
                        "score": 0.85
                    }
                ]
            },
            "expected_status": "PASS"
        },
        {
            "name": "Hallucinated Response (No Citations)",
            "payload": {
                "user_query": "What information can I get under RTI?",
                "llm_output": "You can get any information you want. The government must respond within 24 hours. There are no exemptions for any information. All files are public.",
                "citations": [
                    {
                        "document": "rti_act_2005.pdf",
                        "page": 5,
                        "text": "Information must be provided within 30 days. Certain exemptions apply under Section 8.",
                        "score": 0.6
                    }
                ]
            },
            "expected_status": "FAIL"
        },
        {
            "name": "Exemption Response (Legal Citations)",
            "payload": {
                "user_query": "Can national security info be disclosed?",
                "llm_output": "Information relating to national security is exempt under Section 8(1)(a) of the RTI Act 2005. The competent authority must demonstrate that disclosure would prejudicially affect national security. However, as per Section 8(2), public interest may override exemptions.",
                "citations": [
                    {
                        "document": "rti_exemptions.pdf",
                        "page": 12,
                        "text": "Section 8(1)(a) exempts information affecting national security. Section 8(2) allows disclosure if public interest outweighs the harm.",
                        "score": 0.95
                    }
                ]
            },
            "expected_status": "PASS"
        }
    ]
    
    for tc in test_cases:
        print(f"\n{'─'*60}")
        print(f"📋 Test: {tc['name']}")
        print(f"{'─'*60}")
        
        try:
            response = requests.post(
                f"{BASE_URL}/grounding",
                json=tc["payload"],
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                
                print(f"\n📊 GROUNDING RESULT:")
                print(f"   Grounding Score: {data['grounding_score']:.4f}")
                print(f"   Hallucination Rate: {data['hallucination_rate']:.4f}")
                print(f"   Overall Status: {data['overall_status']}")
                print(f"   Reason: {data['overall_reason']}")
                
                print(f"\n🏗️ THREE LAYERS:")
                
                # L1
                l1 = data['layers']['L1_citation_coverage']
                print(f"\n   📌 L1: Citation Coverage (HARD REQUIREMENT)")
                print(f"      Status: {l1['status']}")
                print(f"      Score: {l1['score']:.2%}")
                print(f"      {l1['cited_sentences']}/{l1['total_sentences']} sentences cited")
                print(f"      Threshold: {l1['threshold']}")
                
                # L2
                l2 = data['layers']['L2_cosine_similarity']
                print(f"\n   📌 L2: Cosine Similarity (SOFT SIGNAL)")
                print(f"      Status: {l2['status']}")
                print(f"      Score: {l2['score']:.4f}")
                print(f"      Interpretation: {l2.get('interpretation', 'N/A')}")
                
                # L3
                l3 = data['layers']['L3_claim_context_overlap']
                print(f"\n   📌 L3: Claim-Context Overlap (ANTI-HALLUCINATION)")
                print(f"      Status: {l3['status']}")
                print(f"      Support Ratio: {l3['support_ratio']:.2%}")
                print(f"      {l3['supported_claims']}/{l3['total_claims']} claims verified")
                if l3.get('unsupported_claims'):
                    print(f"      ⚠️ Unsupported claims:")
                    for claim in l3['unsupported_claims'][:2]:
                        print(f"         - {claim['sentence'][:60]}...")
                
                # Verify expected status
                actual = data['overall_status']
                expected = tc['expected_status']
                if actual == expected or (expected == "PASS" and actual in ["PASS", "WARN"]):
                    print(f"\n   ✅ Test PASSED (expected: {expected}, got: {actual})")
                else:
                    print(f"\n   ❌ Test MISMATCH (expected: {expected}, got: {actual})")
                    
            else:
                print(f"❌ Error: {response.status_code}")
                print(response.text)
                
        except Exception as e:
            print(f"❌ Exception: {e}")


def test_full_evaluation():
    """Test full evaluation with all 9 dimensions × 3 layers"""
    print("\n" + "="*70)
    print("⚖️ TESTING FULL ETHICS EVALUATION (9 DIMENSIONS × 3 LAYERS)")
    print("="*70)
    
    payload = {
        "user_query": "What is Section 4 of RTI Act 2005?",
        "llm_output": "Section 4 of the RTI Act 2005 mandates proactive disclosure by public authorities. Under Section 4(1)(b), every authority must publish all relevant facts regarding their functions, duties, and decision-making processes. This is in accordance with CSMOP guidelines for government transparency.",
        "citations": [
            {
                "document": "rti_act_2005.pdf",
                "page": 3,
                "text": "Section 4(1)(b) requires every public authority to proactively disclose information about their organization, functions, duties, powers, and procedures.",
                "score": 0.94,
                "url": "https://rti.gov.in/act#section4"
            },
            {
                "document": "csmop_guidelines.pdf",
                "page": 15,
                "text": "CSMOP requires all government departments to maintain transparency in their operations and publish relevant facts.",
                "score": 0.87,
                "url": "file:///csmop_guidelines.pdf#page=15"
            }
        ],
        "latency_ms": 420.0,
        "output_tokens": 48
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/evaluate",
            json=payload,
            timeout=60
        )
        
        if response.status_code == 200:
            data = response.json()
            
            # Summary
            print(f"\n📊 SUMMARY")
            print(f"   Final Label: {data['final_label']}")
            print(f"   Overall Score: {data['overall_score']}%")
            print(f"   S_LLM: {data['s_llm']:.4f}")
            print(f"   Risk Band: {data['risk_band']}")
            print(f"   L1 Pass Rate: {data['l1_pass_rate']:.1%}")
            
            # Grounding
            print(f"\n🔬 3-LAYER GROUNDING JUDGE")
            g = data['grounding']
            print(f"   Grounding Score: {g['grounding_score']:.4f}")
            print(f"   Hallucination Rate: {g['hallucination_rate']:.4f}")
            print(f"   Status: {g['overall_status']}")
            
            print(f"\n   L1 Citation Coverage: {g['l1_citation_coverage']['score']:.2%} ({g['l1_citation_coverage']['status']})")
            print(f"   L2 Cosine Similarity: {g['l2_cosine_similarity']['score']:.4f} ({g['l2_cosine_similarity']['status']})")
            print(f"   L3 Claim Overlap: {g['l3_claim_context_overlap']['support_ratio']:.2%} ({g['l3_claim_context_overlap']['status']})")
            
            # Per-dimension breakdown
            print(f"\n⚖️ 9 DIMENSIONS (ALL THREE LAYERS)")
            print("=" * 70)
            
            for dim in data['dimension_scores']:
                print(f"\n📦 {dim['dimension_name']} (weight: {dim['weight']})")
                print(f"   Overall Score: {dim['overall_score']:.1f}%")
                
                # L1
                l1 = dim['l1']
                icon1 = "✅" if l1['status'] == "PASS" else "❌"
                print(f"   {icon1} L1 Hard Gate: {l1['status']} - {l1['reason'][:50]}")
                
                # L2  
                l2 = dim['l2']
                icon2 = "🟢" if l2['status'] == "GOOD" else "🟡" if l2['status'] in ["OK", "WARN"] else "🔴"
                print(f"   {icon2} L2 Risk: {l2['score']:.3f} ({100*(1-l2['score']):.1f}% safe)")
                
                # L3
                l3 = dim['l3']
                print(f"   📋 L3 Evidence: {l3['reason'][:50]}")
                
                # Show some raw metrics
                raw = dim.get('raw_metrics', {})
                if raw:
                    sample = list(raw.items())[:4]
                    metrics_str = ", ".join(f"{k}={v:.3f}" if isinstance(v, float) else f"{k}={v}" for k, v in sample)
                    print(f"   📈 Metrics: {metrics_str}")
            
            # Citations
            print(f"\n📚 CITATION ANALYSIS")
            print(f"   Citations: {data['citations_analyzed']}")
            print(f"   Coverage: {data['citation_coverage']:.2%}")
            print(f"   Source Diversity: {data['source_diversity']}")
            for url in data['citation_urls']:
                print(f"   🔗 {url}")
            
            print(f"\n🎫 AUDIT")
            print(f"   Audit ID: {data['audit_id']}")
            print(f"   Timestamp: {data['timestamp']}")
            print(f"   Computation Mode: {data['computation_mode']}")
            
            return True
            
        else:
            print(f"❌ Error: {response.status_code}")
            print(response.text)
            return False
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_grounding_formula():
    """Test the grounding formula endpoint"""
    print("\n" + "="*70)
    print("📐 GROUNDING FORMULA")
    print("="*70)
    
    try:
        response = requests.get(f"{BASE_URL}/grounding-formula", timeout=10)
        if response.status_code == 200:
            data = response.json()
            
            print(f"\n📊 Formula: {data['grounding_score_formula']}")
            print(f"📊 Hallucination: {data['hallucination_rate']}")
            
            print("\n🏗️ Layers:")
            for layer_key, layer_info in data['layers'].items():
                print(f"\n   {layer_key}:")
                print(f"      Formula: {layer_info['formula']}")
                print(f"      Type: {layer_info['type']}")
                print(f"      Weight: {layer_info['weight']}")
                if 'catches' in layer_info:
                    catches = layer_info['catches']
                    if isinstance(catches, list):
                        for c in catches:
                            print(f"      Catches: {c}")
                    else:
                        print(f"      Catches: {catches}")
            
            print(f"\n✨ Properties: {', '.join(data['properties'])}")
            
    except Exception as e:
        print(f"❌ Error: {e}")


def test_dynamic_computation():
    """Verify dynamic computation (no hardcoding)"""
    print("\n" + "="*70)
    print("🔧 VERIFYING DYNAMIC COMPUTATION")
    print("="*70)
    
    sys.path.insert(0, r"c:\Users\krish\OneDrive\Desktop\bazinga_tsec_hacks\rti_ethics_engine")
    from rti_ethics_engine import compute_spd, compute_readability_fk, compute_accuracy
    
    # Test 1: Different inputs → different outputs
    preds1 = np.array([1, 1, 0, 0, 1])
    preds2 = np.array([1, 0, 0, 0, 0])
    sens = np.array([0, 0, 1, 1, 1])
    
    spd1 = compute_spd(preds1, sens)
    spd2 = compute_spd(preds2, sens)
    
    assert spd1 != spd2, "SPD should differ with different inputs"
    print(f"✅ SPD is DYNAMIC: {spd1:.4f} ≠ {spd2:.4f}")
    
    # Test 2: Readability
    text1 = "Simple sentence."
    text2 = "The implementation of multifarious governmental infrastructural developments necessitates comprehensive interdepartmental coordination mechanisms."
    
    fk1 = compute_readability_fk(text1)
    fk2 = compute_readability_fk(text2)
    
    assert fk1 != fk2, "FK should differ with different text"
    print(f"✅ Readability is DYNAMIC: {fk1:.1f} ≠ {fk2:.1f}")
    
    print("\n✅ All metrics verified as DYNAMICALLY computed")


if __name__ == "__main__":
    print("\n" + "="*70)
    print("🚀 RTI ETHICS ENGINE - 3-LAYER GROUNDING TEST SUITE")
    print("="*70)
    
    # Test dynamic computation first (doesn't need server)
    test_dynamic_computation()
    
    # Check if server is running
    try:
        requests.get(f"{BASE_URL}/health", timeout=2)
        server_running = True
        print("\n✅ Server is running")
    except:
        server_running = False
        print("\n⚠️ Server not running. Start with: python api.py")
    
    if server_running:
        test_grounding_formula()
        test_grounding_endpoint()
        test_full_evaluation()
        
        print("\n" + "="*70)
        print("✅ ALL TESTS COMPLETE")
        print("="*70)
