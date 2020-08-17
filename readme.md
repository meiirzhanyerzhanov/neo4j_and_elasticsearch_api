On the first run, go to http://localhost:7474/browser/ and change neo4j password to "test"
by default username: neo4j, password: neo4j

# API documentation 

Build

•	```/build``` – initialize db or add data

Person

•	```/persons``` - ‘GET’, ‘POST’

•	```/persons/:id``` – ‘GET’, ‘PATCH’, ‘DELETE’

•	```/persons``` GET – list of 10 persons

•	```/persons``` GET, form-data{‘size’: n} – list of n persons

•	```//persons```/ POST, form-data{all data for Person object, group_id and group name if want to make relationship} – create person

•	```//persons/:id```/ GET – retrieve Person by id

•	```//persons/:id```/ DELETE – delete Person by id

•	```//persons/:id```/ PATCH – update info in Person object, send form-data{} to specify which field want to update except id

•	```//persons/search/:name```/ GET – search Person by name

Organization

•	```//organizations```/ - ‘GET’, ‘POST’

•	```//organizations /:id```/ – ‘GET’, ‘PATCH’, ‘DELETE’

•	```//organizations```/ GET – list of 10 organizations

•	```//organizations```/ GET, form-data{‘size’: n} – list of n organizations

•	```//organizations```/ POST, form-data{all data for Organization object} – create organization

•	```//organizations /:id```/ GET – retrieve Organization by id

•	```//organizations /:id```/ DELETE – delete Organization by id

•	```//organizations /:id```/ PATCH – update info in Organization object, send form-data{} to specify which field want to update except group_id

