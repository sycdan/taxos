# Today's Task

We need to figure out how to upload receipt files via the UI.

I am thinking we can have ./data/uploads where we will store zips named for the hash of the uploaded file (provided by the frontend, and vaerified by the backend).

The flow will be:

- User drags a file over the website and drops it
- We hash the file on the client side
- We upload it (endpoint does not exist yet) and save it in compressed format (we can preserve the filename inside the zip)
- After uploading, we show the user the add receipt modal
- When they submit, the post includes the file hash, so the receipt becomes implicitly linked to the upload via the hash (we can add download capability in future if necessary this way)


