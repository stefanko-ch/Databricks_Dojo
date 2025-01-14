# Databricks notebook source
# MAGIC %md
# MAGIC # Follow Job

# COMMAND ----------

import requests
import json

# COMMAND ----------

dbutils.widgets.text("subscription_id", "")
dbutils.widgets.text("resource_group", "")
dbutils.widgets.text("factory_name", "")
dbutils.widgets.text("adf_run_id", "")
dbutils.widgets.text("job_run_table", "demo.demo.job_run")
dbutils.widgets.text("adf_run_id", "adf-test")
dbutils.widgets.text("dbx_run_id", "dbx-test")

subscription_id = dbutils.widgets.get("subscription_id")
resource_group = dbutils.widgets.get("resource_group")
factory_name = dbutils.widgets.get("factory_name")
adf_run_id = dbutils.widgets.get("adf_run_id")
dbx_run_id = dbutils.widgets.get("dbx_run_id")
job_run_table = dbutils.widgets.get("job_run_table")


print(f'adf_run_id: {adf_run_id}')
print(f'dbx_run_id: {dbx_run_id}')

# COMMAND ----------

def create_access_token():
    """
    This function creates an access token using client credentials.
    
    Returns:
        str: Access token if successful, None otherwise.
    """
    
    client_id = dbutils.secrets.get(scope="kv", key="app-reg-adf-job-client-id")
    client_secret = dbutils.secrets.get(scope="kv", key="app-reg-adf-job-client-secret")
    tenant_id = dbutils.secrets.get(scope="kv", key="app-reg-adf-job-tenant-id")

    token_url = f'https://login.microsoftonline.com/{tenant_id}/oauth2/token'
    resource = 'https://management.core.windows.net/'

    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }

    data = {
        'grant_type': 'client_credentials',
        'client_id': client_id,
        'client_secret': client_secret,
        'resource': resource
    }
    try:
        response = requests.post(token_url, headers=headers, data=data)
        if response.status_code == 200:
            access_token = response.json()['access_token']
            return access_token
        else:
            error_message = response.json().get('error', {}).get('message', 'No additional error message provided.')
            print(f'Failed to obtain access token with status code {response.status_code}. Error: {error_message}')

    except requests.exceptions.RequestException as e:
        print(f"An error occurred while obtaining the access token: {e}")

# COMMAND ----------

def check_adf_pipeline_run(subscription_id, resource_group, factory_name, adf_run_id):
    """
    Check status of an Azure Data Factory pipeline run.

    Args:
        subscription_id (str): The subscription ID for the Azure account.
        resource_group (str): The resource group name where the Data Factory is located.
        factory_name (str): The name of the Data Factory.
        adf_run_id (str): The id of the adf pipeline run to check.

    Returns:
        str: The status of a pipeline run.
    """
    
    access_token = create_access_token()

    api_url = f"https://management.azure.com/subscriptions/{subscription_id}/resourceGroups/{resource_group}/providers/Microsoft.DataFactory/factories/{factory_name}/pipelineruns/{adf_run_id}?api-version=2018-06-01"

    # Define headers with Authorization
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {access_token}'
    }

    try:
        # Make the GET request
        response = requests.get(api_url, headers=headers)

        # Check response
        if response.status_code == 200:
            adf_pipe_status = response.json()['status']
            adf_pipe_full_status = response.json()
            print(f'Got pipeline run status:')
            return adf_pipe_status, adf_pipe_full_status
        else:
            # Output specific error message for better debugging
            error_message = response.json().get('error', {}).get('message', 'No additional error message provided.')
            print(f'Something went wrong with status code {response.status_code}. Error: {error_message}')
            
    except requests.exceptions.RequestException as e:
        print(f"An error occurred while get the status of the pipeline: {e}")

# COMMAND ----------

def update_run_id_table(dbx_run_id, adf_run_id, job_run_table, adf_pipe_full_status):
    """
    Inserts the Databricks start run ID and Azure Data Factory run ID into a specified table.

    Args:
        dbx_start_run_id (str): The Databricks start run ID.
        adf_run_id (str): The Azure Data Factory run ID.
        job_run_table (str): The name of the table where the IDs should be inserted.

    """

    sql = f"""UPDATE {job_run_table}
              SET 
              dbx_follow_run_id = "{dbx_run_id}", 
              adf_run_status = "{adf_pipe_full_status}"
              WHERE adf_run_id = "{adf_run_id}"
            """

    # print(sql)        
    print(f"Update table {job_run_table}")
    spark.sql(sql).display()

# COMMAND ----------

adf_pipe_status, adf_pipe_full_status = check_adf_pipeline_run(subscription_id, resource_group, factory_name,  adf_run_id)
print(adf_pipe_status)
print(adf_pipe_full_status)

# COMMAND ----------

update_run_id_table(dbx_run_id, adf_run_id, job_run_table, adf_pipe_full_status)

# COMMAND ----------

spark.sql(f"SELECT * FROM {job_run_table} WHERE adf_run_id = '{adf_run_id}'").display()

# COMMAND ----------


