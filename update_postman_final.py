import json
import os

POSTMAN_FILE = "/home/ebony/PycharmProjects/PIC_ERP_Backend/assets/PIC ERP Backend.postman_collection (2).json"

def get_dms_folder():
    return {
        "name": "DMS",
        "item": [
            {
                "name": "Departments",
                "item": [
                    {
                        "name": "List Departments",
                        "request": {
                            "method": "GET",
                            "header": [],
                            "url": "{{base_url}}/dms/departments/"
                        },
                        "response": []
                    }
                ]
            },
            {
                "name": "Tasks",
                "item": [
                    {
                        "name": "List Tasks (My Tasks)",
                        "request": {
                            "method": "GET",
                            "header": [],
                            "url": {
                                "raw": "{{base_url}}/dms/tasks/?mode=my_tasks&project_id=1",
                                "query": [{"key": "mode", "value": "my_tasks"}, {"key": "project_id", "value": "1"}]
                            }
                        },
                        "response": []
                    },
                    {
                         "name": "Create Task (Manual)",
                         "request": {
                            "method": "POST",
                            "header": [{"key": "Content-Type", "value": "application/json"}],
                            "body": {
                                "mode": "raw",
                                "raw": json.dumps({
                                    "title": "Review Site Drawings",
                                    "description": "Urgent review required.",
                                    "project": 1,
                                    "workflow_step": 1,
                                    "priority": "HIGH",
                                    "due_date": "2026-02-01"
                                }, indent=2)
                            },
                            "url": "{{base_url}}/dms/tasks/"
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
            },
            {
                "name": "Documents",
                "item": [
                    {
                        "name": "Upload Document",
                        "request": {
                            "method": "POST",
                            "header": [],
                            "body": {
                                "mode": "formdata",
                                "formdata": [
                                    {"key": "file", "type": "file", "src": []},
                                    {"key": "task", "value": "1", "type": "text"},
                                    {"key": "document_type", "value": "DRAWING", "type": "text"},
                                    {"key": "version", "value": "1.0", "type": "text"},
                                    {"key": "project", "value": "1", "type": "text"}
                                ]
                            },
                            "url": "{{base_url}}/dms/documents/"
                        },
                        "response": []
                    },
                     {
                        "name": "List Documents",
                        "request": {
                            "method": "GET",
                            "header": [],
                            "url": "{{base_url}}/dms/documents/?task=1"
                        },
                        "response": []
                    }
                ]
            }
        ]
    }

def get_contracts_folder():
    return {
        "name": "AI Contracts",
        "item": [
            {
                "name": "List Contracts",
                "request": {
                    "method": "GET",
                    "header": [],
                    "url": "{{base_url}}/contracts/contracts/"
                },
                "response": []
            },
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
                            {"key": "file", "type": "file", "src": []},
                            {"key": "contract_value", "value": "5000000", "type": "text"},
                            {"key": "start_date", "value": "2026-01-01", "type": "text"}
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

    # Remove old 'DMS' and 'AI Contracts' folders first to avoid duplicates/stale data
    new_items = []
    for item in data['item']:
        if item['name'] not in ['DMS', 'AI Contracts']:
            new_items.append(item)
    
    # Append fresh folders
    new_items.append(get_dms_folder())
    new_items.append(get_contracts_folder())
    
    data['item'] = new_items

    with open(POSTMAN_FILE, "w") as f:
        json.dump(data, f, indent=4)
    
    print("Postman collection updated successfully with FINAL export structure.")

if __name__ == "__main__":
    update_postman_collection()
