# QA Lab

Quickly create and run test cases with dynamic data.

For example, if you need to test the same endpoint on a few different environments, with different query params in the URL, but don't want to set up 14 different tests.

Set up your evironments. Configure their variables. Create and run your test cases.

## Getting Started

### 1. Create and activate a virtual environment
```bash
python3 -m venv venv
source venv/bin/activate
```

### 2. Install requirements
```bash
pip install -r requirements.txt
```

### 3. Run the development server
```bash
python app.py
```

### 4. Database
- The SQLite database (`site.db`) is created automatically if it does not exist.
- To reset the database, delete `site.db` and restart the app.

## Features

- **Test Cases:** Add, view, and delete test cases and steps.
- **Environments:** Manage environments with a base URL and variables.
- **Variables:** Add variables to environments; use them in step slugs as `+varname+`.
- **Step URLs:** Step URLs are dynamically rendered using the environment URL and variables.
- **Test Runs:** Start a test run for all test cases in a selected environment, step through each step, and record results.
- **Run Summaries:** View summaries of completed test runs.

## Usage Tips

- Use `+varname+` in step slugs to insert environment variable values into URLs.
- When running tests, the correct environment and variable values are substituted automatically.
- To add a variable to a step slug, use the "Insert Variable" dropdown on the homepage.

## Project Structure

```
qa-lab/
├── app.py
├── requirements.txt
├── site.db
├── templates/
│   ├── base.html
│   ├── home.html
│   ├── environments.html
│   ├── run_step.html
│   └── run_summary.html
└── static/
```

## Running Tests

To run the test suite, make sure you are in your virtual environment.

First, install development requirements (including pytest):

```bash
pip install -r dev-requirements.txt
```

Then run:

```bash
pytest
```

All tests are located in the `tests` directory.

## TODO
- [ ] Add ability to edit test cases
- [ ] Add variable overrides on a per-run basis
- [ ] Add support for data migrations once schema stabilizes
- [ ] Explore rendering test step URLs on page in an iframe
- [ ] Make it pretty

## License

This project is licensed under the MIT License.  
See the [LICENSE](LICENSE) file for details.
