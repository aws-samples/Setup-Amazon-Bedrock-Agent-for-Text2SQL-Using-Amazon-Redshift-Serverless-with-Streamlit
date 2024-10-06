import boto3
import json
import os

redshift_data = boto3.client('redshift-data')
workgroup_name = os.environ['REDSHIFT_WORKGROUP_NAME']

def get_schema(db):
    """
    Retrieve the schema for tables in the specified database.
    
    :param db: The name of the database
    :return: A list of dictionaries containing table names and their schemas
    """
    table_schema_list = []
    
    try:
        # Get list of schemas
        schema_query = "SELECT DISTINCT schemaname FROM pg_tables WHERE schemaname NOT IN ('pg_catalog', 'information_schema');"
        schema_result = execute_query(schema_query, db, None, None)
        
        for schema in schema_result:
            schema_name = schema['schemaname']
            # Get list of tables for each schema
            table_query = f"SELECT tablename FROM pg_tables WHERE schemaname = '{schema_name}';"
            table_result = execute_query(table_query, db, None, None)
            
            for table in table_result:
                table_name = table['tablename']
                # Get column information for each table
                column_query = f"SELECT column_name, data_type FROM information_schema.columns WHERE table_schema = '{schema_name}' AND table_name = '{table_name}';"
                column_result = execute_query(column_query, db, None, None)
                
                schema = {col['column_name']: col['data_type'] for col in column_result}
                table_schema_list.append({"Table": f"{schema_name}.{table_name}", "Schema": json.dumps(schema)})
    
    except Exception as e:
        print(f"Error in get_schema: {str(e)}")
        return [{"Error": str(e)}]
    
    return table_schema_list

def get_user_acl(user_id):
    """
    Retrieve the list of data sources a given user has access to.
    
    :param user_id: The ID of the user to get data source access for
    :return: A list of accessible data sources
    """
    # This is a mock implementation. In a real scenario, you'd query your ACL system.
    acl_data = {
        "sudipta": [
            {"db": "sample_data_dev", "schema": "tpcds"},
            {"db": "sample_data_prod", "schema": "public"}
        ],
        "syed": [
            {"db": "sample_data_dev", "schema": "tpcds"},
            {"db": "analytics", "schema": "reports"}
        ]
    }
    
    return acl_data.get(user_id, [])

def execute_query(query, db, schema, table, user_id=None):
    """
    Execute a query using Amazon Redshift Serverless after checking user access if applicable.
    Allows DESCRIBE queries without specific user permissions.
    
    :param query: The SQL query to execute
    :param db: The database name
    :param schema: the schema in which table exist
    :param table: the table name
    :param user_id: The ID of the user executing the query (optional)
    :return: Query results or error message
    """
    # Check if the query is a DESCRIBE query
    is_describe_query = query.strip().upper().startswith("DESCRIBE")

    # If it's not a DESCRIBE query and user_id is provided, check if user has access to the schema
    if not is_describe_query and user_id and db and schema:
        user_acl = get_user_acl(user_id)
        if not any(acl['db'] == db and acl['schema'] == schema for acl in user_acl):
            return f"Error: User {user_id} does not have access to database {db} and schema {schema}"

    response = redshift_data.execute_statement(
        WorkgroupName=workgroup_name,
        Database=db,
        Sql=query,
        WithEvent=True
    )
    try:
        query_id = response['Id']
        
        # Wait for query to complete
        while True:
            status = redshift_data.describe_statement(Id=query_id)
            if status['Status'] == 'FINISHED':
                break
            elif status['Status'] in ['FAILED', 'ABORTED']:
                return f"Query failed: {status.get('Error', 'Unknown error')}"

        # Get results
        result = redshift_data.get_statement_result(Id=query_id)
        return extract_result_data(result)

    except Exception as e:
        return f"Error in execute_query: {str(e)}"

def extract_result_data(query_results):
    """
    Extract and format the result data from Redshift Serverless query results.
    
    :param query_results: Raw query results from Redshift Serverless
    :return: Formatted list of dictionaries containing the query results
    """
    result_data = []

    # Extract column names
    column_metadata = query_results['ColumnMetadata']
    column_names = [col['name'] for col in column_metadata]

    # Process each row of data
    for row in query_results['Records']:
        row_data = []
        for item in row:
            # Check for different value types
            if 'stringValue' in item:
                row_data.append(item['stringValue'])
            elif 'longValue' in item:
                row_data.append(item['longValue'])
            elif 'doubleValue' in item:
                row_data.append(item['doubleValue'])
            elif 'booleanValue' in item:
                row_data.append(item['booleanValue'])
            else:
                row_data.append(None)  # For null values or unhandled types
        result_data.append(dict(zip(column_names, row_data)))

    return result_data