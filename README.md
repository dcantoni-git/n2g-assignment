# n2g-assignment
Assignment for backend engineer position at net2grid.

# App Description
I built a REST API using Python Django and the Django REST Framework. I used Docker to containize the application. I also used GitHub Actions and Workflows for automatic testing and linting. The unit tests were made with a mysql local database, because i didn't have permissions to create a test database on the net2grid host. When the developmnet was finished, I used the remote net2grid database that I wes given and did manual tests.

To run the application you need to run "docker-compose build" and "docker-compose up"

The API endpoints were automatically documented using swaggerUI and the can be found in the url 127.0.0.1/api/docs

In order to demontrate some other features, such as token authentication, database tables connections and filtering, I created a "user" app. Because the API had no authentication, I thought it would be a good practice to add authentication and tracability for the messages. That means the application stores the id of the user who used the API and it offers the ability to retrieve the messages that were sent by each user. 

The two data tables, one for the users and the other for the messages were created using the Django ORM. But of course they could have been created with SQL commands.

The message table has the following 



:

/api/user/create/ --> C



