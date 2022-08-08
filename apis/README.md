# Canvara Backend API
## Convert to HTML
Use [redoc-cli](https://github.com/Redocly/redoc/blob/master/cli/README.md) to generate a standalone html file.
```
npx redoc-cli bundle api.yaml -o api.html
```
## Upload to S3
```
aws s3 cp api.html s3://docs.canvara.com/api.html
```
