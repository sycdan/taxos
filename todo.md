# To Do: Taxos Development

## Today's Task

we need to move the logic for downloading receipt files out of the connectrpc api, in as much as possible, and into a domain action (e.g. tenant/receipt/download_file) and just call the domain action from the endpoint.

also, we have stared saving attached files inside the tenant's data (tenants/<guid>/files) so we need to look there for the file instead of uploads.
