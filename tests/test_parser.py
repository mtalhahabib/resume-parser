"""
tests/test_parser.py

Run with:  pytest tests/ -v
Or:        python tests/test_parser.py  (no pytest needed)

Tests 3 resume scenarios:
  1. Clean resume  — basic extraction
  2. Messy resume  — abbreviations, bad formatting, acquired companies
  3. Senior resume — multi-role, normalization edge cases
"""

import sys
import os
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from parser_llm import parse_resume_text


# ── Test resumes ──────────────────────────────────────────────────────────────

CLEAN_RESUME = """
John Smith
john.smith@gmail.com | +1-555-0100 | New York, NY | linkedin.com/in/jsmith

EXPERIENCE

Senior Software Engineer — Google LLC
January 2021 – Present
- Built distributed ML serving infrastructure handling 1B+ QPS
- Led migration of legacy systems to Kubernetes
- Technologies: Python, Go, Kubernetes, TensorFlow, BigQuery

Software Engineer — Amazon Web Services
June 2018 – December 2020
- Developed S3 storage APIs used by 100,000+ customers
- Built internal tooling with Java and React
- Reduced deployment time by 60%

EDUCATION
B.S. Computer Science — MIT (Massachusetts Institute of Technology), 2018

SKILLS
Python, Go, Java, React, JavaScript, Kubernetes, TensorFlow, BigQuery, AWS, PostgreSQL, Redis
"""

MESSY_RESUME = """
sarah.chen@proton.me  Sarah Chen  SF CA

WORK

Principal ML Eng | Goog (Mountain View) | Mar 2020 – now
built recommendation systems 500M+ users, TF, BigQuery, K8s, GCP
team lead 8 ppl

SWE II, MSFT Azure | 2017 – 2020
C#, .NET, azure sdks, rest apis, perf optimization -40% latency

Junior Dev @ Nimbus Analytics (acquired by Salesforce 2019) | 2015-17
React, Node, PG, Redis. Agile

SKILLS:Python TF PyTorch JS TS React Node C# SQL NoSQL Docker K8s AWS GCP Azure Spark dbt

EDUCATION
MS CS Stanford Univ 2015  |  BS CS+Math MIT 2013
"""

SENIOR_RESUME = """
MICHAEL RODRIGUEZ
m.rodriguez@email.com  |  Austin, TX

VP of Engineering — Stripe, Inc.
2022 – Present
Scaled engineering org from 40 to 120 engineers. Owned payments infrastructure processing $500B/year. 
Led adoption of Rust for latency-critical systems.
Stack: Rust, Python, Java, Postgres, Kafka, AWS

Director of Engineering — Twitter (now X Corp)
2019 – 2022
Led Ads infrastructure team. 30% revenue increase via ML-driven bidding.
Python, Scala, Hadoop, Kafka, GCP

Senior Staff Engineer — Lyft
2016 – 2019
Core platform team. Microservices, gRPC, Go, Kubernetes.

Software Engineer — Small startup "RideFlow" (pre-acquisition, acquired by Lyft 2016)
2014 – 2016
Full-stack. Rails, React, Postgres, Heroku.

EDUCATION
M.B.A. — Harvard Business School, 2014
B.S. Electrical Engineering & CS — UC Berkeley, 2012

SKILLS
Python, Rust, Java, Scala, Go, Ruby on Rails, React, PostgreSQL, Kafka, Hadoop, 
Kubernetes, AWS, GCP, gRPC, Redis, Terraform, System Design, Engineering Management
"""


# ── Assertion helpers ─────────────────────────────────────────────────────────

def assert_field(result, path, description):
    """Assert a nested field exists and is not null/empty."""
    parts = path.split(".")
    val = result
    for part in parts:
        if isinstance(val, list):
            val = val[0] if val else None
        if val is None:
            break
        val = val.get(part) if isinstance(val, dict) else None
    assert val not in (None, "", []), f"FAIL: {description} (path={path}, got={val!r})"
    print(f"  ✓  {description}")
    return val


def check_experience(exp_list, expected_count, check_normalization=True):
    assert len(exp_list) >= expected_count, (
        f"FAIL: Expected ≥{expected_count} experience entries, got {len(exp_list)}"
    )
    print(f"  ✓  Found {len(exp_list)} experience entries (expected ≥{expected_count})")

    for exp in exp_list:
        assert exp.get("title"), f"FAIL: Missing title in {exp}"
        assert exp.get("company_normalized"), f"FAIL: Missing company_normalized in {exp}"
        conf = exp.get("confidence", 0)
        assert conf >= 0.5, f"FAIL: Low confidence {conf} for {exp.get('company_raw')}"

    if check_normalization:
        normalized = [e["company_normalized"].lower() for e in exp_list]
        print(f"  ✓  Normalized companies: {normalized}")


def check_skills(skills_list, min_count=5):
    assert len(skills_list) >= min_count, (
        f"FAIL: Expected ≥{min_count} skills, got {len(skills_list)}"
    )
    print(f"  ✓  Found {len(skills_list)} skills")

    clusters = set(s.get("cluster") for s in skills_list)
    valid_clusters = {"Frontend", "Backend", "AI/ML", "DevOps", "Data", "Mobile", "Other"}
    for c in clusters:
        assert c in valid_clusters, f"FAIL: Unknown cluster '{c}'"
    print(f"  ✓  Clusters: {clusters}")


def check_education(edu_list, min_count=1):
    assert len(edu_list) >= min_count, (
        f"FAIL: Expected ≥{min_count} education entries, got {len(edu_list)}"
    )
    print(f"  ✓  Found {len(edu_list)} education entries")

    for e in edu_list:
        assert e.get("school_normalized"), f"FAIL: Missing school_normalized in {e}"
        assert e.get("tier") in ("Elite", "Target", "Standard"), (
            f"FAIL: Invalid tier '{e.get('tier')}'"
        )
    print(f"  ✓  Education tiers: {[e['tier'] for e in edu_list]}")


# ── Tests ─────────────────────────────────────────────────────────────────────

def test_clean_resume():
    print("\n" + "="*60)
    print("TEST 1: Clean Resume (Google + AWS + MIT)")
    print("="*60)

    result = parse_resume_text(CLEAN_RESUME)

    assert_field(result, "candidate.name", "Candidate name extracted")
    assert_field(result, "candidate.email", "Email extracted")

    exp = result.get("experience", [])
    check_experience(exp, expected_count=2)

    # Google should be normalized
    companies = [e["company_normalized"].lower() for e in exp]
    assert any("google" in c for c in companies), f"FAIL: Google not found in {companies}"
    assert any("amazon" in c for c in companies), f"FAIL: Amazon not found in {companies}"
    print("  ✓  Google and Amazon normalized correctly")

    check_skills(result.get("skills", []), min_count=5)
    check_education(result.get("education", []), min_count=1)

    edu = result.get("education", [])
    mit = next((e for e in edu if "mit" in e.get("school_normalized","").lower() or 
                "massachusetts" in e.get("school_normalized","").lower()), None)
    assert mit, "FAIL: MIT not found in education"
    assert mit.get("tier") == "Elite", f"FAIL: MIT should be Elite, got {mit.get('tier')}"
    print("  ✓  MIT correctly tiered as Elite")

    meta = result.get("extraction_meta", {})
    assert meta.get("total_years_experience", 0) > 0, "FAIL: years_experience is 0"
    print(f"  ✓  Years experience: {meta.get('total_years_experience')}")
    print(f"  ✓  Overall confidence: {meta.get('confidence_overall')}")

    print("\n  PASS ✓")
    return result


def test_messy_resume():
    print("\n" + "="*60)
    print("TEST 2: Messy Resume (abbreviations, bad formatting)")
    print("="*60)

    result = parse_resume_text(MESSY_RESUME)

    assert_field(result, "candidate.name", "Candidate name extracted from messy format")
    assert_field(result, "candidate.email", "Email extracted")

    exp = result.get("experience", [])
    check_experience(exp, expected_count=3)

    # Check abbreviation normalization
    companies = [e["company_normalized"].lower() for e in exp]
    google_found = any("google" in c for c in companies)
    ms_found = any("microsoft" in c for c in companies)
    assert google_found, f"FAIL: 'Goog' not normalized to Google. Got: {companies}"
    assert ms_found, f"FAIL: 'MSFT' not normalized to Microsoft. Got: {companies}"
    print("  ✓  'Goog' → Google, 'MSFT' → Microsoft")

    # Check acquired company detection
    nimbus = next((e for e in exp if "nimbus" in e.get("company_raw","").lower()), None)
    if nimbus:
        assert nimbus.get("is_acquired") == True, "FAIL: Nimbus should be marked acquired"
        print(f"  ✓  Nimbus Analytics marked as acquired by: {nimbus.get('acquired_by')}")

    # Skills: K8s → Kubernetes, PG → PostgreSQL, TF → TensorFlow
    skills = result.get("skills", [])
    skill_names = [s["name"].lower() for s in skills]
    assert any("kubernetes" in s for s in skill_names), \
        f"FAIL: K8s not normalized to Kubernetes. Skills: {skill_names}"
    print("  ✓  'K8s' → Kubernetes normalized")

    edu = result.get("education", [])
    check_education(edu, min_count=2)
    tiers = [e.get("tier") for e in edu]
    assert tiers.count("Elite") >= 2, f"FAIL: Stanford+MIT should both be Elite. Got: {tiers}"
    print("  ✓  Stanford + MIT both tiered as Elite")

    print("\n  PASS ✓")
    return result


def test_senior_resume():
    print("\n" + "="*60)
    print("TEST 3: Senior Resume (multi-role, VP/Director level)")
    print("="*60)

    result = parse_resume_text(SENIOR_RESUME)

    assert_field(result, "candidate.name", "Name extracted")

    exp = result.get("experience", [])
    check_experience(exp, expected_count=4)

    meta = result.get("extraction_meta", {})
    career_level = meta.get("career_level", "")
    assert career_level in ("Principal", "Staff", "Executive", "Senior"), \
        f"FAIL: Expected senior career level, got '{career_level}'"
    print(f"  ✓  Career level: {career_level}")

    years = meta.get("total_years_experience", 0)
    assert years >= 8, f"FAIL: Expected ≥8 years experience, got {years}"
    print(f"  ✓  Years experience: {years}")

    # Check Twitter/X Corp normalization
    companies = [e["company_normalized"] for e in exp]
    twitter = next((e for e in exp if "twitter" in e.get("company_raw","").lower() or
                    "twitter" in e.get("company_normalized","").lower()), None)
    assert twitter, f"FAIL: Twitter not found in: {companies}"
    print(f"  ✓  Twitter found: '{twitter.get('company_normalized')}'")

    # Check acquired company (RideFlow → Lyft)
    rideflow = next((e for e in exp if "rideflow" in e.get("company_raw","").lower()), None)
    if rideflow:
        assert rideflow.get("is_acquired"), "FAIL: RideFlow should be marked acquired"
        print(f"  ✓  RideFlow marked acquired by: {rideflow.get('acquired_by')}")

    edu = result.get("education", [])
    check_education(edu, min_count=2)
    harvard = next((e for e in edu if "harvard" in e.get("school_normalized","").lower()), None)
    assert harvard, "FAIL: Harvard not found"
    assert harvard.get("tier") == "Elite", f"FAIL: Harvard should be Elite"
    print("  ✓  Harvard correctly tiered as Elite")

    skills = result.get("skills", [])
    check_skills(skills, min_count=10)

    print("\n  PASS ✓")
    return result


# ── Runner ────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("\nResumeIQ Parser — Test Suite")
    print("Using Claude claude-sonnet-4-20250514\n")

    results = {}
    failures = []

    for test_fn in [test_clean_resume, test_messy_resume, test_senior_resume]:
        try:
            res = test_fn()
            results[test_fn.__name__] = "PASS"
        except AssertionError as e:
            print(f"\n  ✗ ASSERTION: {e}")
            results[test_fn.__name__] = f"FAIL: {e}"
            failures.append(test_fn.__name__)
        except Exception as e:
            print(f"\n  ✗ ERROR: {e}")
            results[test_fn.__name__] = f"ERROR: {e}"
            failures.append(test_fn.__name__)

    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    for name, status in results.items():
        icon = "✓" if status == "PASS" else "✗"
        print(f"  {icon}  {name}: {status}")

    if failures:
        print(f"\n  {len(failures)} test(s) failed.")
        sys.exit(1)
    else:
        print(f"\n  All {len(results)} tests passed.")
        sys.exit(0)
