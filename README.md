This Repository contains the Flask App with two routes

1. /reciever
This route makes a post request and sends the event action to the MongoDB database. It is connected to the webhook of action-repo repository.

2. /getActions
This route gets all the events collection from the MongoDB database. It is used by the React app UI (in action-repo repository) to display the events occurring in the action-repo every 15 seconds.