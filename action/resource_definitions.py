RESOURCE_DEFINITIONS = {
    "add_document_db": {
        "db_name": None,
        "backup_retention_period": 1,
        "skip_final_snapshot": True,
        "count": 1,
        "instance_class": "db.t3.medium"
    },
    "update_document_db": {
        "backup_retention_period": None,
        "skip_final_snapshot": None,
        "count": None,
        "instance_class": None
    }
}

VARIABLE_RESOURCES = {
    "port-terraform-provisioner-docdb": ["backup_retention_period", "skip_final_snapshot"],
    "cluster_instances": ["count", "instance_class"]
}
