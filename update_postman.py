import json
import os

POSTMAN_FILE = "/home/ebony/PycharmProjects/PIC_ERP_Backend/assets/PIC ERP Backend.postman_collection (2).json"

def create_dms_folder():
    return {
        "name": "DMS",
        "item": [
            {
                "name": "List Tasks",
                "request": {
                    "method": "GET",
                    "header": [],
                    "url": {
                        "raw": "{{base_url}}/dms/tasks/?project_id=1&mode=my_tasks",
                        "host": ["{{base_url}}"],
                        "path": ["dms", "tasks", ""],
                        "query": [
                            {"key": "project_id", "value": "1"},
                            {"key": "mode", "value": "my_tasks", "description": "Options: my_tasks, department"}
                        ]
                    }
                },
                "response": []
            },
            {
                "name": "Assign Task",
                "request": {
                    "method": "POST",
                    "header": [{"key": "Content-Type", "value": "application/json"}],
                    "body": {
                        "mode": "raw",
                        "raw": json.dumps({
                            "action": "ASSIGN",
                            "assigned_to": 2,
                            "comments": "Please review this document."
                        }, indent=2)
                    },
                    "url": "{{base_url}}/dms/tasks/1/perform_action/"
                },
                "response": []
            },
            {
                "name": "Approve Task",
                "request": {
                    "method": "POST",
                    "header": [{"key": "Content-Type", "value": "application/json"}],
                    "body": {
                        "mode": "raw",
                        "raw": json.dumps({
                            "action": "APPROVE",
                            "comments": "Approved based on technical review."
                        }, indent=2)
                    },
                    "url": "{{base_url}}/dms/tasks/1/perform_action/"
                },
                "response": []
            },
            {
                "name": "Dashboard Stats",
                "request": {
                    "method": "GET",
                    "header": [],
                    "url": "{{base_url}}/dms/tasks/dashboard_stats/?project_id=1"
                },
                "response": []
            }
        ]
    }

def create_contracts_folder():
    return {
        "name": "AI Contracts",
        "item": [
            {
                "name": "Upload Contract",
                "request": {
                    "method": "POST",
                    "header": [],
                    "body": {
                        "mode": "formdata",
                        "formdata": [
                            {"key": "title", "value": "Main Construction Agreement", "type": "text"},
                            {"key": "project", "value": "1", "type": "text"},
                            {"key": "file", "type": "file", "src": []}
                        ]
                    },
                    "url": "{{base_url}}/contracts/contracts/"
                },
                "response": []
            },
            {
                "name": "Process Contract (AI Embedding)",
                "request": {
                    "method": "POST",
                    "header": [],
                    "url": "{{base_url}}/contracts/contracts/1/process/"
                },
                "description": "Triggers the local SBERT model to parse and embed clauses.",
                "response": []
            },
            {
                "name": "Semantic Search",
                "request": {
                    "method": "GET",
                    "header": [],
                    "url": {
                        "raw": "{{base_url}}/contracts/contracts/1/search/?q=When is the payment due?",
                        "host": ["{{base_url}}"],
                        "path": ["contracts", "contracts", "1", "search", ""],
                        "query": [
                            {"key": "q", "value": "When is the payment due?", "description": "Natural language query"}
                        ]
                    }
                },
                "response": []
            }
        ]
    }

def update_postman_collection():
    if not os.path.exists(POSTMAN_FILE):
        print(f"File not found: {POSTMAN_FILE}")
        return

    with open(POSTMAN_FILE, "r") as f:
        data = json.load(f)

    # Check if folders already exist to avoid duplicates
    existing_folders = [item['name'] for item in data['item']]
    
    if "DMS" not in existing_folders:
        data['item'].append(create_dms_folder())
        print("Added DMS folder.")
    else:
        print("DMS folder already exists. Skipping.")

    if "AI Contracts" not in existing_folders:
        data['item'].append(create_contracts_folder())
        print("Added AI Contracts folder.")
    else:
        print("AI Contracts folder already exists. Skipping.")

    with open(POSTMAN_FILE, "w") as f:
        json.dump(data, f, indent=4)
    
    print("Postman collection updated successfully.")

if __name__ == "__main__":
    update_postman_collection()
