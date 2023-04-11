# Port Terraform PR provisioner

Python project to be used as a self-service action to receive inputs and open a PR that adds new resources to a terraform module.

The example includes two handlers for the Lambda:

- create doc db - will provision a new AWS Document DB instance based on the inputs received from Port;
- update doc db - will update the Terraform definition of an existing AWS Document DB that is currently configured through Terraform
