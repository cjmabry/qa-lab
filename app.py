from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import re

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Example model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)

    def __repr__(self):
        return f'<User {self.username}>'

class TestStep(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    step_text = db.Column(db.Text, nullable=False)
    expected_result = db.Column(db.Text, nullable=False)
    slug = db.Column(db.String(255), nullable=True)  # <-- Replace url with slug
    testcase_id = db.Column(db.Integer, db.ForeignKey('test_case.id'), nullable=False)

    def __repr__(self):
        return f'<TestStep {self.step_text[:20]}...>'

class TestCase(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=True)
    steps = db.relationship('TestStep', backref='testcase', lazy=True)

    def __repr__(self):
        return f'<TestCase {self.title}>'

class TestRun(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    started_at = db.Column(db.DateTime, server_default=db.func.now())
    notes = db.Column(db.Text, nullable=True)
    environment_id = db.Column(
        db.Integer,
        db.ForeignKey('environment.id', name='fk_testrun_environment_id'),
        nullable=False
    )
    steps = db.relationship('TestRunStep', backref='testrun', lazy=True)
    environment = db.relationship('Environment')  # Optional: for easy access

class TestRunStep(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    testrun_id = db.Column(
        db.Integer,
        db.ForeignKey('test_run.id', name='fk_testrunstep_testrun_id'),
        nullable=False
    )
    testcase_id = db.Column(
        db.Integer,
        db.ForeignKey('test_case.id', name='fk_testrunstep_testcase_id'),
        nullable=False
    )
    teststep_id = db.Column(
        db.Integer,
        db.ForeignKey('test_step.id', name='fk_testrunstep_teststep_id'),
        nullable=False
    )
    status = db.Column(db.String(10), nullable=True)  # pass, fail, skip
    notes = db.Column(db.Text, nullable=True)

class EnvironmentVariable(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    value = db.Column(db.String(255), nullable=False)
    environment_id = db.Column(db.Integer, db.ForeignKey('environment.id'), nullable=False)

class Environment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    url = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    variables = db.relationship('EnvironmentVariable', backref='environment', lazy=True)

    def __repr__(self):
        return f'<Environment {self.title}>'

def render_slug(slug, variables):
    rendered = slug or ""
    for name, value in variables.items():
        rendered = rendered.replace(f'+{name}+', value)
    return rendered

app.jinja_env.globals.update(render_slug=render_slug)

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        url = request.form.get('url')
        new_case = TestCase(title=title, description=description)
        db.session.add(new_case)
        db.session.commit()
        return redirect(url_for('home'))
    test_cases = TestCase.query.all()
    environments = Environment.query.all()  # <-- Add this line
    return render_template('home.html', test_cases=test_cases, environments=environments)

@app.route('/add_step/<int:testcase_id>', methods=['POST'])
def add_step(testcase_id):
    step_text = request.form['step_text']
    expected_result = request.form['expected_result']
    slug = request.form.get('slug')
    new_step = TestStep(step_text=step_text, expected_result=expected_result, slug=slug, testcase_id=testcase_id)
    db.session.add(new_step)
    db.session.commit()
    return redirect(url_for('home'))

@app.route('/delete_case/<int:case_id>', methods=['POST'])
def delete_case(case_id):
    case = TestCase.query.get_or_404(case_id)
    # Delete all steps associated with this case
    for step in case.steps:
        db.session.delete(step)
    db.session.delete(case)
    db.session.commit()
    return redirect(url_for('home'))

@app.route('/delete_step/<int:step_id>', methods=['POST'])
def delete_step(step_id):
    step = TestStep.query.get_or_404(step_id)
    db.session.delete(step)
    db.session.commit()
    return redirect(url_for('home'))

@app.route('/start_run', methods=['POST'])
def start_run():
    environment_id = request.form['environment_id']
    testrun = TestRun(environment_id=environment_id)
    db.session.add(testrun)
    db.session.commit()
    for case in TestCase.query.all():
        for step in case.steps:
            run_step = TestRunStep(
                testrun_id=testrun.id,
                testcase_id=case.id,
                teststep_id=step.id
            )
            db.session.add(run_step)
    db.session.commit()
    return redirect(url_for('run_step', run_id=testrun.id, idx=0))

@app.route('/run/<int:run_id>/step/<int:idx>', methods=['GET', 'POST'])
def run_step(run_id, idx):
    testrun = TestRun.query.get_or_404(run_id)
    steps = TestRunStep.query.filter_by(testrun_id=run_id).all()
    if idx >= len(steps):
        return redirect(url_for('run_summary', run_id=run_id))
    step = steps[idx]
    teststep = TestStep.query.get(step.teststep_id)
    testcase = TestCase.query.get(step.testcase_id)
    environment = testrun.environment
    variables = {var.name: var.value for var in environment.variables}
    rendered_slug = render_slug(teststep.slug, variables)
    if request.method == 'POST':
        step.status = request.form['status']
        step.notes = request.form.get('notes')
        db.session.commit()
        return redirect(url_for('run_step', run_id=run_id, idx=idx+1))
    return render_template(
        'run_step.html',
        step=step,
        teststep=teststep,
        testcase=testcase,
        idx=idx,
        total=len(steps),
        environment=environment,
        rendered_slug=rendered_slug
    )

@app.route('/run/<int:run_id>/summary')
def run_summary(run_id):
    testrun = TestRun.query.get_or_404(run_id)
    steps = TestRunStep.query.filter_by(testrun_id=run_id).all()
    # Optionally, join with TestCase and TestStep for display
    step_details = []
    for step in steps:
        testcase = TestCase.query.get(step.testcase_id)
        teststep = TestStep.query.get(step.teststep_id)
        step_details.append({
            'testcase': testcase,
            'teststep': teststep,
            'status': step.status,
            'notes': step.notes
        })
    return render_template('run_summary.html', testrun=testrun, step_details=step_details)

@app.route('/runs')
def runs():
    runs = TestRun.query.order_by(TestRun.started_at.desc()).all()
    return render_template('runs.html', runs=runs)

@app.route('/environments', methods=['GET', 'POST'])
def environments():
    if request.method == 'POST':
        title = request.form['title']
        url = request.form['url']
        description = request.form['description']
        env = Environment(title=title, url=url, description=description)
        db.session.add(env)
        db.session.commit()
        return redirect(url_for('environments'))
    envs = Environment.query.all()
    return render_template('environments.html', environments=envs)

@app.route('/environments/<int:env_id>/add_var', methods=['POST'])
def add_env_var(env_id):
    name = request.form['name']
    value = request.form['value']
    var = EnvironmentVariable(name=name, value=value, environment_id=env_id)
    db.session.add(var)
    db.session.commit()
    return redirect(url_for('environments'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)