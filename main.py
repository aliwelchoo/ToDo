from pathlib import Path
from datetime import date, datetime as dt, timedelta

import yaml
from dash import Dash, dcc, html, Output, Input, ALL, ctx, State
import dash_bootstrap_components as dbc
from dash.exceptions import PreventUpdate
from dash_iconify import DashIconify


def move_to_front(lst, idx):
    return [lst.pop(idx), *lst]


def write_tasks(save_tasks):
    with open(Path.cwd() / 'tasks.yaml', 'w') as file:
        _ = yaml.dump(save_tasks, file, sort_keys=True)


def read_tasks():
    with open(Path.cwd() / 'tasks.yaml', 'r') as file:
        return yaml.safe_load(file)


def task_item(text, index, task_type):
    return dbc.AccordionItem(
        dbc.Row([
                    dbc.Col(html.P(text, id={'type': task_type, 'index': index})),
                ] +
                ([dbc.Col(
                    [
                        dbc.Button(id={'type': 'bottom', 'index': index}, children=[
                            DashIconify(icon="material-symbols:keyboard-double-arrow-down-rounded")
                        ]),
                        dbc.Button(id={'type': 'down', 'index': index}, children=[
                            DashIconify(icon="material-symbols:keyboard-arrow-down-rounded")
                        ]),
                        dbc.Button(id={'type': 'up', 'index': index}, children=[
                            DashIconify(icon="material-symbols:keyboard-arrow-up-rounded")
                        ]),
                        dbc.Button(id={'type': 'top', 'index': index}, children=[
                            DashIconify(icon="material-symbols:keyboard-double-arrow-up-rounded")
                        ]),
                        dbc.Button(id={'type': 'del', 'index': index}, children=[
                            DashIconify(icon="fluent:delete-32-regular")
                        ]),
                        dbc.Button(id={'type': 'tick', 'index': index}, children=[
                            DashIconify(icon="charm:tick")
                        ]),
                    ], className='d-flex justify-content-end',
                )] if task_type == 'todo' else []),
                className='justify-content-between'))


def create_todo_accordion_items():
    return [
        dbc.AccordionItem(
            [task_item(task_text, i, 'completed') for i, task_text in enumerate(current_tasks['completed'])],
            title='Completed',
            item_id='complete'),
        dbc.AccordionItem([task_item(task_text, i, 'todo') for i, task_text in enumerate(current_tasks['todo'])],
                          title='To Do',
                          item_id='todo')
    ]


def run_app():
    app = Dash(__name__, title='To Do Stack', external_stylesheets=[dbc.themes.QUARTZ, 'assets/slate.css'])
    app.layout = dbc.Container([
        dbc.Row([
            dbc.Col(dbc.Button("Rollover", id={'type': 'carry', 'index': 0}), width=4),
            dbc.Col(
                dcc.DatePickerSingle(
                    id='my-date-picker-single',
                    display_format='Do MMMM Y',
                    initial_visible_month=date.today(),
                    date=date.today(),
                    className="dash-bootstrap",
                ),
                width=4,
            ),
        ]),
        dbc.Row([
            dbc.Col(dbc.Input(placeholder="Add a new task..", id='new-task', type='text'), width=10),
            dbc.Col(dbc.Button(DashIconify(icon="ant-design:plus-outlined"), id={'type': 'add', 'index': 0}), width=1),
        ]),
        dbc.Accordion(
            create_todo_accordion_items(),
            always_open=True,
            active_item='todo',
            id='all-tasks')
    ], className='p-0 p1-0 m-0 me-0 mw-100',
    )

    @app.callback(
        Output('all-tasks', 'children'),
        Output('new-task', 'value'),
        Input({'type': ALL, 'index': ALL}, 'n_clicks'),
        Input('my-date-picker-single', 'date'),
        State('new-task', 'value'),
        prevent_initial_call=True,
    )
    def tasks_change(n_clicks, current_date, new_task):
        if not n_clicks:
            raise PreventUpdate
        global active_date, current_tasks, tasks

        todos = current_tasks['todo']
        trigger_id = ctx.triggered_id

        if trigger_id == 'my-date-picker-single':
            active_date = current_date
            current_tasks = tasks.get(active_date, {'completed': [], 'todo': []})
            return create_todo_accordion_items(), new_task

        trigger_index, trigger_type = trigger_id.values()

        if trigger_type == 'bottom':
            todos.append(todos.pop(trigger_index))
        elif trigger_type == 'down':
            if trigger_index < len(todos)-1:
                todos[trigger_index], todos[trigger_index+1] = todos[trigger_index+1], todos[trigger_index]
        elif trigger_type == 'up':
            if trigger_index > 0:
                todos[trigger_index], todos[trigger_index - 1] = todos[trigger_index - 1], todos[trigger_index]
        elif trigger_type == 'top':
            todos = move_to_front(todos, trigger_index)
        elif trigger_type == 'add':
            todos.append(new_task)
            todos = move_to_front(todos, todos.index(new_task))
            new_task = []
        elif trigger_type == 'del':
            todos.pop(trigger_index)
        elif trigger_type == 'tick':
            current_tasks['completed'].append(todos[trigger_index])
            todos.pop(trigger_index)
        elif trigger_type == 'carry':
            date_before = dt.strftime(dt.strptime(active_date, '%Y-%M-%d') - timedelta(days=1), '%Y-%M-%d')
            todos.extend(tasks[date_before]['todo'])

        current_tasks['todo'] = todos
        tasks[active_date] = current_tasks
        write_tasks(tasks)
        return create_todo_accordion_items(), new_task

    app.run_server(debug=True)


tasks = read_tasks()
active_date = str(date.today())
current_tasks = tasks.get(active_date, {'completed': [], 'todo': []})


def main():
    run_app()


if __name__ == '__main__':
    main()
