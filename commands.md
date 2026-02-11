# Check if items are actually in the tables

aws dynamodb scan --table-name rti_fairness --limit 10

aws dynamodb scan --table-name rti_query_history --limit 10

# Also check item counts

aws dynamodb describe-table --table-name rti_fairness --query 'Table.ItemCount'
aws dynamodb describe-table --table-name rti_query_history --query 'Table.ItemCount'
