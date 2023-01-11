#!/bin/sh

echo "Deleting old function zip"
rm -f function.zip

echo "Zipping updated function code"
zip -FSr function.zip ./*.py ./**/*.py

echo "Uploading new function code zip to AWS"
aws lambda update-function-code --function-name update-terraform-from-action --zip-file fileb://function.zip

echo "Done!"
