# FSND_Multi_User_Blog

## Project Overview

The FSND_Multi_User_Blog is a multi-user blog application developed as a part of the Udacity Full Stack Web Developer Nanodegree. This application allows multiple users to create, edit, and manage their blog posts. It is built using Python and utilizes Google App Engine for deployment, showcasing essential web development skills.

### Structure

The project is structured as follows:

- `app.yaml`: Configuration file for Google App Engine.
- `main.py`: The main Python script that handles routing and controllers.
- `models/`: Directory containing ORM models for the datastore entities.
- `templates/`: Folder for HTML templates for rendering views.
- `static/`: Contains static files like CSS and JavaScript.
- `utils/`: Utility functions and helpers.

## Setup and Installation

### Prerequisites

- Python 2.7
- Google Cloud SDK
- A Google Cloud Platform account

### Installation Steps

1. **Clone the Repository:**
   ```bash
   git clone https://github.com/yourusername/FSND_Multi_User_Blog.git
   cd FSND_Multi_User_Blog
   ```

2. **Install Google Cloud SDK:**
   Follow the instructions at https://cloud.google.com/sdk/docs/install to install and initialize the Google Cloud SDK.

3. **Run the Application Locally:**
   ```bash
   dev_appserver.py app.yaml
   ```
   This command will start the app on your local server, usually accessible at `http://localhost:8080`.

4. **Deploy to Google App Engine:**
   Once you are ready to deploy the application, you can use the following command:
   ```bash
   gcloud app deploy
   ```
   Follow the prompts to select your project and deploy the application.

## Usage

After deploying the application or running it locally, you can access it through your web browser.

- **Home Page:** Shows all the blog posts.
- **Signup:** New users can create an account.
- **Login:** Existing users can log in.
- **Create Post:** Logged-in users can create new blog posts.
- **Edit/Delete Post:** Post owners can edit or delete their posts.

## Contributing

Contributions to the FSND_Multi_User_Blog are welcome!

1. **Fork the Repository:** Start by forking the repository to your GitHub account.
2. **Clone the Forked Repository:** Clone the repository to your local machine.
3. **Create a New Branch:** Create a branch for your changes and switch to it.
4. **Make Changes:** Implement your changes or improvements.
5. **Commit Changes:** Commit your changes with a clear commit message.
6. **Push to GitHub:** Push your changes to your fork on GitHub.
7. **Submit a Pull Request:** Open a pull request from your fork to the original repository.

Please ensure your code adheres to the existing style so that your changes can be easily integrated.

## License

This project is open-sourced under the MIT License. See the LICENSE file for more details.