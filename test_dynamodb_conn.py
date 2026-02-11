import boto3
import argparse
from botocore.exceptions import ClientError

def test_connectivity(region, fairness_table, query_table_name):
    print(f"Testing connectivity in region: {region}")
    dynamodb = boto3.resource("dynamodb", region_name=region)
    
    # Test Fairness Table
    print(f"--- Checking Fairness Table: {fairness_table} ---")
    try:
        table = dynamodb.Table(fairness_table)
        response = table.scan(Limit=1)
        print(f"Successfully scanned {fairness_table}. Item count: {response.get('Count', 0)}")
    except ClientError as e:
        print(f"Error accessing {fairness_table}: {e.response['Error']['Message']}")
    except Exception as e:
        print(f"Unexpected error: {e}")

    # Test Query History Table
    # NOTE: If query table represents a different region, this test might fail if run with wrong region.
    # The user screenshot showed rti_query_history in us-east-1 and rti_fairness in eu-north-1.
    print(f"--- Checking Query History Table: {query_table_name} ---")
    try:
        table = dynamodb.Table(query_table_name)
        response = table.scan(Limit=1)
        print(f"Successfully scanned {query_table_name}. Item count: {response.get('Count', 0)}")
    except ClientError as e:
        print(f"Error accessing {query_table_name}: {e.response['Error']['Message']}")
    except Exception as e:
        print(f"Unexpected error: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--region", default="eu-north-1", help="DynamoDB Region")
    parser.add_argument("--fairness", default="rti_fairness", help="Fairness Table Name")
    parser.add_argument("--query", default="rti_query_history", help="Query History Table Name")
    args = parser.parse_args()
    
    test_connectivity(args.region, args.fairness, args.query)
