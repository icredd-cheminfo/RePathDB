from plotly.graph_objects import Figure, Layout, Scatter
from CGRdb import db_session
from ..graph import Molecule, Reaction, Complex
from io import StringIO
from CGRtools import  MRVWrite

def get_figure(edges, nodes):
    edge_trace = Scatter(
        x=[x for x, _ in edges], y=[x for _, x in edges],
        line=dict(width=0.5, color='#888'),
        hoverinfo='none',
        mode='lines')

    node_trace = Scatter(
        x=[x[0] for x in nodes.values()], y=[x[1] for x in nodes.values()],
        customdata=[(x, y[3]) for x, y in nodes.items()],
        text=[x[3] for x in nodes.values()],
        mode='markers',
        hoverinfo='text',
        marker=dict(
            showscale=False,
            color=[x[2] for x in nodes.values()],
            size=15))

    figure = Figure(data=[edge_trace, node_trace],
                    layout=Layout(
                        showlegend=False,
                        hovermode='closest',
                        margin=dict(b=20, l=5, r=5, t=40),
                        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                        yaxis=dict(showgrid=False, zeroline=False, showticklabels=True),
                        paper_bgcolor='rgba(0,0,0,0)',
                        plot_bgcolor='rgba(0,0,0,0)'
                    ),
                    )
    return figure


def get_3d(s, order_map, xyz):
    bonds = []
    tmp = {'atoms': [{'elem': a.atomic_symbol, 'x': xyz[n][0], 'y': xyz[n][1], 'z': xyz[n][2]}
                     for n, a in s.atoms()],
           'bonds': bonds}

    for n, m, b in s.bonds():
        if b.order is None:
            bonds.append({'atom1': order_map[n], 'atom2': order_map[m],
                          'maxorder': b.p_order,
                          'from': 0})
        elif b.p_order is None:
            bonds.append({'atom1': order_map[n], 'atom2': order_map[m],
                          'maxorder': b.order,
                          'to': 0})
        elif b.p_order == b.order:
            bonds.append({'atom1': order_map[n], 'atom2': order_map[m],
                          'maxorder': b.order,
                          })
        else:
            if b.order > b.p_order:
                bonds.append({'atom1': order_map[n], 'atom2': order_map[m],
                              'maxorder': b.order,
                              'to': b.p_order})
            else:
                bonds.append({'atom1': order_map[n], 'atom2': order_map[m],
                              'maxorder': b.p_order,
                              'from': b.order})
    return tmp


def draw(click_data):
    if not click_data:
        return {'atoms': [], 'bonds': []}
    if "customdata" not in click_data['points'][0]:
        return {'atoms': [], 'bonds': []}
    _id, identifier = click_data['points'][0]['customdata']
    with db_session:
        if identifier == "MOL" or "Complex" in identifier:
            if identifier == "MOL":
                #node = Molecule.get(_id)
                pass
            if "Complex" in identifier:
                node = Complex.get(_id)
            eq = node.equilibrium_states.order_by('energy').first()
            mp = node.equilibrium_states.relationship(eq).mapping
            xyz = {mp[k]: v for k, v in eq.xyz.items()}
            s = node.structure
            order_map = {n: i for i, n in enumerate(s)}
            tmp = {'atoms': [{'elem': a.atomic_symbol, 'x': xyz[n][0], 'y': xyz[n][1], 'z': xyz[n][2]}
                             for n, a in s.atoms()],
                   'bonds': [{'atom1': order_map[n], 'atom2': order_map[m], 'maxorder': b.order}
                             for n, m, b in s.bonds()]}
        else:
            node = Reaction.get(_id)
            ts = node.transition_states.order_by('energy').first()
            mp = node.transition_states.relationship(ts).mapping
            xyz = {mp[k]: v for k, v in ts.xyz.items()}
            s = node.structure
            order_map = {n: i for i, n in enumerate(s)}
            tmp = get_3d(s, order_map, xyz)

    return tmp


def get_mrv(structure):
    with StringIO() as f:
        with MRVWrite(f) as o:
            o.write(structure)
            return f.getvalue()
