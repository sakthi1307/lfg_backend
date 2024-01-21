# LGF

This is a Flask app that uses MongoDB as a backend database.

## Installation

To install the required dependencies, run the following command:

```
pip install -r requirements.txt
```

You will also need to install MongoDB on your machine. Please follow the instructions on the [official MongoDB website](https://www.mongodb.com/) to install it.



## MongoDB Setup

To use MongoDB with this app, you will need to set the following environment variables:


- `MONGO_URI`: The URL of your MongoDB instance with username and password.

You can set these variables by running the following commands in your terminal:

```

export MONGO_URI=<your_mongodb_uri>
```

Alternatively, you can create a `.env` file in the root directory of the project and set the variables there. Be sure to add the `.env` file to your `.gitignore` file to prevent it from being committed to your repository.




## Usage

To run the app, use the following command:
```
gunicorn -w 4 'app:app'
```
The -w option specifies the number of processes to run
Once the app is running, you can access it by navigating to `http://localhost:5000` in your web browser.


