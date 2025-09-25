"""
Test Tools for Large Data Optimization System

These tools generate large datasets to demonstrate the automatic
data reference and optimization system in action.
"""

import json
import random
import time
from typing import List, Dict, Any
from datetime import datetime, timedelta
from langchain_core.tools import tool

# Sample data for realistic test datasets
COMPANIES = ["TechCorp", "DataSys", "CloudInc", "AILabs", "DevCorp", "InnoTech", "SmartSys", "NextGen"]
PRODUCTS = ["Widget A", "Service B", "Platform C", "Tool D", "App E", "System F", "Module G"]
REGIONS = ["North America", "Europe", "Asia Pacific", "Latin America", "Middle East", "Africa"]
DEPARTMENTS = ["Engineering", "Sales", "Marketing", "Finance", "HR", "Operations", "Support"]

@tool
def fetch_sales_data(num_records: int = 50000, include_details: bool = True) -> List[Dict[str, Any]]:
    """
    Fetch comprehensive sales data records.
    
    Args:
        num_records: Number of records to generate (default: 50,000)
        include_details: Include detailed transaction information
    
    Returns:
        List of sales records with comprehensive details
    """
    
    print(f"🔄 Generating {num_records:,} sales records...")
    
    sales_data = []
    base_date = datetime(2023, 1, 1)
    
    for i in range(num_records):
        record_date = base_date + timedelta(days=random.randint(0, 365))
        
        record = {
            "transaction_id": f"TXN-{i+1:06d}",
            "date": record_date.strftime("%Y-%m-%d"),
            "customer_id": f"CUST-{random.randint(1000, 9999)}",
            "company": random.choice(COMPANIES),
            "product": random.choice(PRODUCTS),
            "region": random.choice(REGIONS),
            "quantity": random.randint(1, 100),
            "unit_price": round(random.uniform(10.0, 1000.0), 2),
            "discount": round(random.uniform(0.0, 0.25), 3),
            "sales_rep": f"Rep-{random.randint(100, 999)}",
            "department": random.choice(DEPARTMENTS)
        }
        
        # Calculate derived fields
        subtotal = record["quantity"] * record["unit_price"]
        discount_amount = subtotal * record["discount"]
        record["subtotal"] = round(subtotal, 2)
        record["discount_amount"] = round(discount_amount, 2)
        record["total"] = round(subtotal - discount_amount, 2)
        
        if include_details:
            record["details"] = {
                "shipping_address": {
                    "street": f"{random.randint(100, 9999)} Main St",
                    "city": f"City-{random.randint(1, 50)}",
                    "state": f"State-{random.randint(1, 20)}",
                    "zip": f"{random.randint(10000, 99999)}"
                },
                "payment_method": random.choice(["Credit Card", "Bank Transfer", "Check", "PayPal"]),
                "shipping_method": random.choice(["Standard", "Express", "Overnight", "Economy"]),
                "notes": f"Transaction note {i+1} with additional details and comments"
            }
        
        sales_data.append(record)
    
    print(f"✅ Generated {len(sales_data):,} sales records")
    return sales_data

@tool
def get_user_analytics(timeframe_days: int = 365, include_behavior: bool = True) -> Dict[str, Any]:
    """
    Get comprehensive user analytics data.
    
    Args:
        timeframe_days: Number of days of data to include
        include_behavior: Include detailed behavioral data
    
    Returns:
        Comprehensive user analytics dataset
    """
    
    print(f"🔄 Generating user analytics for {timeframe_days} days...")
    
    num_users = random.randint(10000, 50000)
    analytics_data = {
        "summary": {
            "total_users": num_users,
            "timeframe_days": timeframe_days,
            "generated_at": datetime.now().isoformat(),
            "data_version": "2.1"
        },
        "user_segments": [],
        "daily_metrics": [],
        "feature_usage": {},
        "conversion_funnel": {}
    }
    
    # Generate user segments
    segments = ["New Users", "Active Users", "Power Users", "Churned Users", "Inactive Users"]
    for segment in segments:
        analytics_data["user_segments"].append({
            "segment": segment,
            "count": random.randint(1000, 8000),
            "percentage": round(random.uniform(5.0, 25.0), 2),
            "growth_rate": round(random.uniform(-10.0, 15.0), 2),
            "avg_session_duration": random.randint(120, 1800),
            "avg_pages_per_session": round(random.uniform(2.0, 12.0), 1)
        })
    
    # Generate daily metrics
    base_date = datetime.now() - timedelta(days=timeframe_days)
    for day in range(timeframe_days):
        current_date = base_date + timedelta(days=day)
        
        daily_data = {
            "date": current_date.strftime("%Y-%m-%d"),
            "active_users": random.randint(5000, 15000),
            "new_signups": random.randint(100, 500),
            "sessions": random.randint(20000, 60000),
            "page_views": random.randint(100000, 300000),
            "bounce_rate": round(random.uniform(0.3, 0.7), 3),
            "avg_session_duration": random.randint(180, 900),
            "conversion_rate": round(random.uniform(0.02, 0.08), 4)
        }
        
        if include_behavior:
            daily_data["behavior_data"] = {
                "top_pages": [f"/page-{i}" for i in range(1, 11)],
                "user_flows": [
                    {"from": "home", "to": "product", "count": random.randint(100, 1000)},
                    {"from": "product", "to": "cart", "count": random.randint(50, 500)},
                    {"from": "cart", "to": "checkout", "count": random.randint(20, 200)}
                ],
                "device_breakdown": {
                    "desktop": random.randint(3000, 8000),
                    "mobile": random.randint(2000, 7000),
                    "tablet": random.randint(500, 2000)
                }
            }
        
        analytics_data["daily_metrics"].append(daily_data)
    
    # Generate feature usage data
    features = ["Search", "Filters", "Export", "Sharing", "Comments", "Notifications", "Dashboard"]
    for feature in features:
        analytics_data["feature_usage"][feature] = {
            "total_uses": random.randint(10000, 100000),
            "unique_users": random.randint(2000, 20000),
            "usage_trend": round(random.uniform(-20.0, 30.0), 2),
            "avg_uses_per_user": round(random.uniform(1.5, 15.0), 1)
        }
    
    print(f"✅ Generated comprehensive analytics for {num_users:,} users")
    return analytics_data

@tool
def export_financial_report(quarters: int = 8, detailed: bool = True) -> Dict[str, Any]:
    """
    Export detailed financial report data.
    
    Args:
        quarters: Number of quarters to include in the report
        detailed: Include detailed breakdowns and line items
    
    Returns:
        Comprehensive financial report dataset
    """
    
    print(f"🔄 Generating financial report for {quarters} quarters...")
    
    report_data = {
        "report_metadata": {
            "report_type": "Comprehensive Financial Report",
            "quarters_included": quarters,
            "generated_at": datetime.now().isoformat(),
            "currency": "USD",
            "report_version": "3.2"
        },
        "quarterly_summary": [],
        "revenue_breakdown": {},
        "expense_categories": {},
        "balance_sheet": {},
        "cash_flow": {}
    }
    
    # Generate quarterly data
    base_year = 2022
    base_quarter = 1
    
    for q in range(quarters):
        year = base_year + ((base_quarter + q - 1) // 4)
        quarter = ((base_quarter + q - 1) % 4) + 1
        
        revenue = random.randint(5000000, 15000000)  # $5M - $15M
        expenses = int(revenue * random.uniform(0.6, 0.9))  # 60-90% of revenue
        
        quarter_data = {
            "year": year,
            "quarter": quarter,
            "period": f"Q{quarter} {year}",
            "revenue": revenue,
            "gross_profit": revenue - int(revenue * random.uniform(0.3, 0.5)),
            "operating_expenses": expenses,
            "net_income": revenue - expenses,
            "ebitda": revenue - int(expenses * random.uniform(0.7, 0.9)),
            "growth_rate": round(random.uniform(-5.0, 25.0), 2)
        }
        
        if detailed:
            quarter_data["detailed_breakdown"] = {
                "revenue_streams": {
                    "Product Sales": int(revenue * random.uniform(0.4, 0.7)),
                    "Services": int(revenue * random.uniform(0.2, 0.4)),
                    "Subscriptions": int(revenue * random.uniform(0.1, 0.3)),
                    "Other": int(revenue * random.uniform(0.0, 0.1))
                },
                "expense_breakdown": {
                    "Cost of Goods Sold": int(expenses * random.uniform(0.3, 0.5)),
                    "Sales & Marketing": int(expenses * random.uniform(0.2, 0.3)),
                    "Research & Development": int(expenses * random.uniform(0.15, 0.25)),
                    "General & Administrative": int(expenses * random.uniform(0.1, 0.2)),
                    "Other Operating Expenses": int(expenses * random.uniform(0.05, 0.15))
                },
                "key_metrics": {
                    "customer_acquisition_cost": random.randint(50, 200),
                    "customer_lifetime_value": random.randint(500, 2000),
                    "monthly_recurring_revenue": random.randint(100000, 500000),
                    "churn_rate": round(random.uniform(0.02, 0.08), 4)
                }
            }
        
        report_data["quarterly_summary"].append(quarter_data)
    
    # Generate additional detailed sections if requested
    if detailed:
        # Revenue breakdown by region
        report_data["revenue_breakdown"] = {
            "by_region": {
                region: {
                    "total_revenue": random.randint(1000000, 5000000),
                    "growth_rate": round(random.uniform(-10.0, 30.0), 2),
                    "market_share": round(random.uniform(5.0, 25.0), 2)
                }
                for region in REGIONS
            },
            "by_product": {
                product: {
                    "revenue": random.randint(500000, 3000000),
                    "units_sold": random.randint(1000, 10000),
                    "avg_selling_price": round(random.uniform(100.0, 500.0), 2)
                }
                for product in PRODUCTS
            }
        }
        
        # Generate balance sheet data
        total_assets = random.randint(50000000, 200000000)
        report_data["balance_sheet"] = {
            "assets": {
                "current_assets": {
                    "cash": int(total_assets * random.uniform(0.1, 0.3)),
                    "accounts_receivable": int(total_assets * random.uniform(0.1, 0.2)),
                    "inventory": int(total_assets * random.uniform(0.05, 0.15)),
                    "other_current": int(total_assets * random.uniform(0.02, 0.08))
                },
                "fixed_assets": {
                    "property_plant_equipment": int(total_assets * random.uniform(0.2, 0.4)),
                    "intangible_assets": int(total_assets * random.uniform(0.1, 0.2)),
                    "other_fixed": int(total_assets * random.uniform(0.05, 0.15))
                },
                "total_assets": total_assets
            },
            "liabilities_equity": {
                "current_liabilities": int(total_assets * random.uniform(0.1, 0.25)),
                "long_term_debt": int(total_assets * random.uniform(0.15, 0.35)),
                "other_liabilities": int(total_assets * random.uniform(0.05, 0.15)),
                "shareholders_equity": int(total_assets * random.uniform(0.25, 0.55))
            }
        }
    
    print(f"✅ Generated comprehensive financial report with {quarters} quarters of data")
    return report_data

@tool  
def search_documents(query: str, max_results: int = 1000) -> List[Dict[str, Any]]:
    """
    Search through a large document collection.
    
    Args:
        query: Search query to find relevant documents
        max_results: Maximum number of results to return
    
    Returns:
        List of matching documents with metadata
    """
    
    print(f"🔍 Searching documents for '{query}' (max {max_results} results)...")
    
    # Generate realistic document results
    document_types = ["Report", "Memo", "Policy", "Manual", "Guide", "Specification", "Analysis"]
    authors = ["Smith, J.", "Johnson, M.", "Williams, K.", "Brown, S.", "Davis, R.", "Miller, T."]
    departments = DEPARTMENTS
    
    results = []
    for i in range(max_results):
        doc_date = datetime.now() - timedelta(days=random.randint(1, 1000))
        
        document = {
            "document_id": f"DOC-{i+1:06d}",
            "title": f"Document about {query} - Part {i+1}",
            "type": random.choice(document_types),
            "author": random.choice(authors),
            "department": random.choice(departments),
            "created_date": doc_date.strftime("%Y-%m-%d"),
            "last_modified": (doc_date + timedelta(days=random.randint(0, 30))).strftime("%Y-%m-%d"),
            "file_size_kb": random.randint(50, 5000),
            "page_count": random.randint(5, 200),
            "relevance_score": round(random.uniform(0.3, 1.0), 3),
            "summary": f"This document covers aspects of {query} including detailed analysis, recommendations, and implementation guidelines. Created by {random.choice(authors)} for {random.choice(departments)} department.",
            "tags": random.sample(["important", "confidential", "archived", "current", "draft", "final", "review"], k=random.randint(2, 4)),
            "content_preview": f"This document discusses {query} in the context of {random.choice(departments)} operations. Key findings include significant improvements in efficiency and cost reduction measures that have been implemented across multiple divisions..."
        }
        
        results.append(document)
    
    # Sort by relevance score (descending)
    results.sort(key=lambda x: x["relevance_score"], reverse=True)
    
    print(f"✅ Found {len(results):,} documents matching '{query}'")
    return results

@tool
def fetch_research_data(topic: str, num_studies: int = 5000) -> Dict[str, Any]:
    """
    Fetch comprehensive research data on a specific topic.
    
    Args:
        topic: Research topic to fetch data for
        num_studies: Number of research studies to include
    
    Returns:
        Comprehensive research dataset
    """
    
    print(f"🔄 Generating research data on '{topic}' with {num_studies} studies...")
    
    research_types = ["Experimental", "Observational", "Meta-Analysis", "Case Study", "Survey", "Review"]
    institutions = ["MIT", "Stanford", "Harvard", "Oxford", "Cambridge", "Berkeley", "Caltech", "Yale"]
    journals = ["Nature", "Science", "Cell", "JAMA", "Lancet", "PNAS", "IEEE", "ACM"]
    
    research_data = {
        "metadata": {
            "topic": topic,
            "total_studies": num_studies,
            "date_range": "2020-2024",
            "generated_at": datetime.now().isoformat(),
            "data_version": "4.1"
        },
        "studies": [],
        "summary_statistics": {},
        "trending_keywords": [],
        "collaboration_network": {},
        "citation_analysis": {}
    }
    
    # Generate individual studies
    for i in range(num_studies):
        study_date = datetime(2020, 1, 1) + timedelta(days=random.randint(0, 1460))  # 4 years
        
        study = {
            "study_id": f"STUDY-{i+1:06d}",
            "title": f"Research Study on {topic}: Investigation {i+1}",
            "authors": [f"Author{j}" for j in range(random.randint(2, 8))],
            "institution": random.choice(institutions),
            "journal": random.choice(journals),
            "publication_date": study_date.strftime("%Y-%m-%d"),
            "study_type": random.choice(research_types),
            "sample_size": random.randint(50, 10000),
            "duration_months": random.randint(6, 60),
            "citation_count": random.randint(0, 500),
            "impact_factor": round(random.uniform(1.0, 15.0), 2),
            "abstract": f"This {random.choice(research_types).lower()} study investigates {topic} across {random.randint(50, 10000)} participants over {random.randint(6, 60)} months. The research demonstrates significant findings in the field and contributes to our understanding of the underlying mechanisms.",
            "keywords": random.sample([f"{topic}_keyword_{k}" for k in range(1, 21)], k=random.randint(5, 10)),
            "methodology": f"The study employed a {random.choice(research_types).lower()} approach with rigorous controls and statistical analysis.",
            "key_findings": [
                f"Finding {j+1}: Significant correlation discovered in {topic} research"
                for j in range(random.randint(3, 8))
            ],
            "funding_sources": random.sample(["NSF", "NIH", "Private Foundation", "University Grant", "Industry"], k=random.randint(1, 3))
        }
        
        research_data["studies"].append(study)
    
    # Generate summary statistics
    research_data["summary_statistics"] = {
        "total_participants": sum(study["sample_size"] for study in research_data["studies"]),
        "avg_citation_count": round(sum(study["citation_count"] for study in research_data["studies"]) / num_studies, 1),
        "avg_impact_factor": round(sum(study["impact_factor"] for study in research_data["studies"]) / num_studies, 2),
        "studies_by_type": {
            research_type: len([s for s in research_data["studies"] if s["study_type"] == research_type])
            for research_type in research_types
        },
        "studies_by_institution": {
            institution: len([s for s in research_data["studies"] if s["institution"] == institution])
            for institution in institutions
        }
    }
    
    # Generate trending keywords
    all_keywords = []
    for study in research_data["studies"]:
        all_keywords.extend(study["keywords"])
    
    keyword_counts = {}
    for keyword in all_keywords:
        keyword_counts[keyword] = keyword_counts.get(keyword, 0) + 1
    
    research_data["trending_keywords"] = sorted(
        keyword_counts.items(), 
        key=lambda x: x[1], 
        reverse=True
    )[:50]  # Top 50 keywords
    
    print(f"✅ Generated comprehensive research data on '{topic}' with {num_studies} studies")
    return research_data

# Additional utility functions for testing

def generate_sample_large_json(size_mb: float = 10.0) -> Dict[str, Any]:
    """Generate a large JSON object of approximately the specified size"""
    target_size = int(size_mb * 1024 * 1024)  # Convert MB to bytes
    data = {"records": []}
    
    current_size = 0
    counter = 0
    
    while current_size < target_size:
        record = {
            "id": counter,
            "data": f"Large data record {counter} with substantial content " * 20,  # ~1KB per record
            "timestamp": datetime.now().isoformat(),
            "metadata": {
                "source": f"generator_{counter % 100}",
                "category": f"category_{counter % 50}",
                "details": f"Detailed information for record {counter}" * 5
            }
        }
        data["records"].append(record)
        
        # Estimate current size (rough approximation)
        current_size = len(json.dumps(data))
        counter += 1
    
    return data

if __name__ == "__main__":
    # Test the tools
    print("🧪 Testing Large Data Tools")
    print("=" * 50)
    
    # Test small dataset (should return directly)
    small_data = fetch_sales_data.invoke({"num_records": 50, "include_details": False})
    print(f"Small dataset: {len(small_data)} records")
    
    # Test large dataset (should create reference)
    large_data = fetch_sales_data.invoke({"num_records": 10000, "include_details": True})
    print(f"Large dataset: {len(large_data)} records")
    
    print("\n✅ Test tools ready for large data optimization system")
