# SSG API Demo Application

![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)
![AWS](https://img.shields.io/badge/AWS-%23FF9900.svg?style=for-the-badge&logo=amazon-aws&logoColor=white)

Built with Streamlit, this sample application provides you with a quick and easy way to try out our APIs without 
needing to write your own code!

## AWS Deployment

Don't want to install any packages or run commands? Head over to [this site]() where this application is being hosted
on to get started quickly!

## Local Installation

This application was built using Python 3.12, and it uses the following Python libraries:

* `streamlit`: Main UI framework
* `pycodestyle`: Checkstyle for Python
* `requests`: Library for sending HTTP requests; the backbone of this application
* `cryptography`: For encryption and decryption of the requests and payloads
* `streamlit-nested-layout`: Patch for UI framework to allow deep nesting of elements
* `requests-oauthlib`: OAuth Authentication with `requests`
* `apscheduler`: Runs cron jobs required for maintenance and housekeeping
* `certifi`: Provides updated information on Root Certificate Authority
* `pyOpenSSL`: Provides SSL functionalities
* `coverage`: Provides code coverage reports for unit tests

There are 2 ways to install Python, along with the necessary libraries: Using `Python` directly, or through a package
and environment manager such as `conda`.

### Python

Firstly, you need to install `Python 3.12` on your device of choice. Refer to [this link](https://www.python.org/downloads/release/python-3123/)
get the different installers for your Operating System. If you are using Windows, use the **Windows Installer**; If you 
are using macOS, use the **macOS Installer**; If you are using Linux, refer to [this guide](https://www.geeksforgeeks.org/how-to-install-python-in-ubuntu/)
on how to install Python 3.12.

>  ❗ For Linux, make sure that you **explicitly specify Python version 3.12** in the commands that require specification 
> of Python version.

#### Installation of libraries

After installing Python, open a command prompt or terminal in the same location as this `README.md` file.

Install the required libraries by running the following command:

```shell
pip install -r requirements.txt
```

The command should install all the required Python libraries on your system.

> ❓ If your command fails to execute, try replacing `pip` with `pip3` instead!


### `conda`

`conda` is a Command Line tool that helps you manage your packages and environments on your system. It is compatible 
with Windows, MacOS and Linux.

> ❗ You are highly recommended to use Python package managers to help maintain your Python environments. Installations 
> on the base environment provided when you first install Python may result in dependency clashes with future 
> packages you install.

Refer to the following links to find out more on how to install `conda` on your OS of choice:
[Windows](https://conda.io/projects/conda/en/latest/user-guide/install/windows.html),
[MacOS](https://conda.io/projects/conda/en/latest/user-guide/install/macos.html),
[Linux](https://conda.io/projects/conda/en/latest/user-guide/install/linux.html)

After installing `conda`, open up a command prompt or a terminal in the same location as this `README.md` document.

Run the command:

```shell
conda create -n [YOUR ENV NAME HERE] python=3.12
```

> ❗ Make sure to change `[YOUR ENV NAME HERE]` to any name that you desire (e.g. `ssg`, `api`, `demo`, `application`)!

Running the command will create a new `conda` environment with `Python 3.12` installed!

#### Installation of libraries

After your environment is created, make sure to activate it first. To activate an environment, run the command:

```shell
conda activate [YOUR ENV NAME HERE]
```

where `[YOUR ENV NAME HERE]` is the same environment name that you used in the previous steps.


Then, run the following commands to install the required Python libraries into your `conda` environment.

```shell
pip install -r requirements.txt
```

> ❓ If your command fails to execute, try replacing `pip` with `pip3` instead!

## Usage

First, open up a command prompt or terminal at the same location as this `README.md` document.

If you are using `conda`, make sure to activate the environment which you have installed the required Python
libraries in.

Then, run the command:

```shell
streamlit run Home.py 
```

If successful, you should be able to see that your browser would open, and you will be navigated to the `localhost`
address where this application is hosted on!


## Features

There are 6 main pages of the application. Each page focuses on one particular aspect of the SSG 15 mandated APIs,
as well as the SkillsFuture Credit API.

The pages are all found within the [pages](app/pages) folder.

### Demo Code - Authentication

This page contains sample code which you can use in your application to get started with authentication.

This page also provides you with a quick and simple way to test if your credentials work, allowing you to do a 
quick sanity check on the veracity of your credentials.

### Courses

This page contains APIs that are related to Course Runs and Course sessions!

Using this API, you can:

* Add a Course Run
* Delete a Course Run
* Update a Course Run
* View a Course Run
* View Course Sessions

### Enrollment

This page contains APIs that are related to the enrollment of learners to your courses!

Using this API, you can:

* Create Enrollment
* View Enrollment
* Search Enrollment
* Update Enrollment
* Delete Enrollment

### Attendance

This page contains APIs that are related to the attendance of learners enrolled your courses!

Using this API, you can:

* View Course Session Attendance
* Upload Course Session Attendance

### Assessments

This page contains APIs that are related to the assessment of learners enrolled in your courses!

Using this API, you can:

* Create Assessment
* Update Assessment
* Void Assessment
* View Assessment
* Search Assessment

### SkillsFuture Credit Pay API

This page contains APIs that are related to the use of SkillsFuture Credit Pay API to help manage the 
use of SkillsFuture credits by learners enrolled into your course.

Using this API, you can:

* Encrypt Payment Request
* Decrypt Payment Request Response
* Upload Supporting Documents for Claims
* View Claims Details
* Cancel Claims

## Acknowledgements

Many of the backend functions are adapted from the [SSG-API-Testing-Application](../../Sample-Codes/SSG-API-Testing-Application).