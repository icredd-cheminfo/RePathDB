from dash_html_components import Div, H1, Hr, Button, Label
from dash_marvinjs import DashMarvinJS
from dash_core_components import Dropdown, Input as InputField, Markdown


def get_layout(app):
    row_1 = Div([
                Div([
                    Div([
                        DashMarvinJS(id='editor', marvin_url=app.get_asset_url('mjs/editor.html'), marvin_width='100%'),
                        Markdown(
    '''
    # Hey there
    - My mighty helpfull advises should be here to navigate noobies in darkspace of visualisation
    - ***star***
    '''
                                )
                        ], className='col'),
                    ], className='col-md-6'),
                Div([Markdown("DIV for: selection of path")], className='col-md-6')
                ], className='row col-md-12')

    row_2 = Div([
                Div([Markdown("DIV for: Some awesome graph will be shown here")], className='col-md-8'),
                Div([Markdown("DIV for: Visualisation of some structure")], className='col-md-4'),
                ], className='row col-md-12')

    layout = Div([H1("AFIR database visualisation",  style={'textAlign': 'center'}), Hr(), row_1, Hr(), row_2])
    return layout
