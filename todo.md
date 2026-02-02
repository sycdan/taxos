# Today's Task

we need to have one single docker compose file that will build and run the entire application for development.

it should restart the application when changes are made to the code.

we should be able to run the application with a single command: `docker compose up`

we should be able to make a deployable image of the entire application with a single command: `docker compose build`

remove any extraneous configuration or example files.

we will not use a databse for the backend; we will sue filesystem persistence (self-managed) via volume mounts.

we will use grpc for the backend and grpc-web for the frontend.

