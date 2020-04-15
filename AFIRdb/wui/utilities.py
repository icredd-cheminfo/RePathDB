from plotly.graph_objects import Figure, Layout, Scatter


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
                        yaxis=dict(showgrid=False, zeroline=False, showticklabels=True))
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