import plotly.graph_objects as go
import networkx as nx
from typing import Union


def plot(
    G,
    title="Graph",
    layout=None,
    size_method="degree",
    color_method="degree",
    node_text=[],
    show_edgetext=False,
    titlefont_size=16,
    showlegend=False,
    annotation_text="",
    colorscale="YlGnBu",
    colorbar_title="",
):
    """
    Plots a Graph using Plotly.
    
    Parameters
    ----------
    G : Networkx Graph
        Network Graph

    title : str, optional
        Title of the graph, by default "Graph"

    layout : {"random", "circular", "kamada", "planar", "spring", "spectral", "spiral"}, optional
        Layout of the nodes on the plot.

            random (default): Position nodes uniformly at random in the unit square.
                For every node, a position is generated by choosing each of dim coordinates uniformly at random on the interval [0.0, 1.0).
            
            circular: Position nodes on a circle.
            
            kamada: Position nodes using Kamada-Kawai path-length cost-function.
            
            planar: Position nodes without edge intersections, if possible (if the Graph is planar).
            
            spring: Position nodes using Fruchterman-Reingold force-directed algorithm.
            
            spectral: Position nodes using the eigenvectors of the graph Laplacian.
            
            spiral: Position nodes in a spiral layout.
            
    size_method : {'degree', 'static'}, node property or a list, optional
        How to size the nodes., by default "degree"

            degree: The larger the degree, the larger the node.

            static: All nodes are the same size.

            node property: A property field of the node.

            list: A list pertaining to the size of the nodes.

    color_method : {'degree'}, hex color code, node property, or list optional
        How to color the node., by default "degree"

            degree: Color the nodes based on their degree.

            hex color code: Hex color code.

            node property: A property field of the node.

            list: A list pertaining to the colour of the nodes.

    node_text : list, optional
        A list of node properties to display when hovering over the node.

    show_edgetext : bool, optional
        True to display the edge properties on hover.

    titlefont_size : int, optional
        Font size of the title, by default 16

    showlegend : bool, optional
        True to show legend, by default False

    annotation_text : str, optional
        Graph annotation text, by default ""

    colorscale : {'Greys', 'YlGnBu', 'Greens', 'YlOrRd', 'Bluered', 'RdBu', 'Reds', 'Blues', 'Picnic', 'Rainbow', 'Portland', 'Jet', 'Hot', 'Blackbody', 'Earth', 'Electric', 'Viridis'}
        Scale of the color bar

    colorbar_title : str, optional
        Color bar axis title, by default ""
    
    Returns
    -------
    Plotly Figure
        Plotly figure of the graph
    """

    if layout:
        _apply_layout(G, layout)
    elif not nx.get_node_attributes(G, "pos"):
        _apply_layout(G, "random")

    node_trace, edge_trace, middle_node_trace = _generate_scatter_trace(
        G,
        size_method=size_method,
        color_method=color_method,
        colorscale=colorscale,
        colorbar_title=colorbar_title,
        node_text=node_text,
        show_edgetext=show_edgetext,
    )

    fig = _generate_figure(
        G,
        node_trace,
        edge_trace,
        middle_node_trace,
        title=title,
        titlefont_size=titlefont_size,
        showlegend=showlegend,
        annotation_text=annotation_text,
    )

    return fig


def _generate_scatter_trace(
    G,
    size_method: Union[str, list],
    color_method: Union[str, list],
    colorscale: str,
    colorbar_title: str,
    node_text: list,
    show_edgetext: bool,
):
    """
    Helper function to generate Scatter plot traces for the graph.
    """

    edge_text_list = []
    edge_properties = {}

    edge_trace = go.Scatter(
        x=[], y=[], line=dict(width=2, color="#888"), hoverinfo="text", mode="lines",
    )

    # NOTE: This is a hack because Plotly does not allow you to have hover text on a line
    # Were adding an invisible node to the edges that will display the edge properties
    middle_node_trace = go.Scatter(
        x=[], y=[], text=[], mode="markers", hoverinfo="text", marker=dict(opacity=0)
    )

    node_trace = go.Scatter(
        x=[],
        y=[],
        mode="markers",
        text=[],
        hoverinfo="text",
        marker=dict(
            showscale=True,
            colorscale=colorscale,
            reversescale=True,
            size=[],
            color=[],
            colorbar=dict(
                thickness=15, title=colorbar_title, xanchor="left", titleside="right"
            ),
            line_width=2,
        ),
    )

    for edge in G.edges(data=True):
        x0, y0 = G.nodes[edge[0]]["pos"]
        x1, y1 = G.nodes[edge[1]]["pos"]
        edge_trace["x"] += tuple([x0, x1, None])
        edge_trace["y"] += tuple([y0, y1, None])

        if show_edgetext:
            # Now we can add the text
            # First we need to aggregate all the properties for each edge
            edge_pair = (edge[0], edge[1])
            # if an edge property for an edge hasn't been tracked, add an entry
            if edge_pair not in edge_properties:
                edge_properties[edge_pair] = {}

                # Since we haven't seen this node combination before also add it to the trace
                middle_node_trace["x"] += tuple([(x0 + x1) / 2])
                middle_node_trace["y"] += tuple([(y0 + y1) / 2])

            # For each edge property, create an entry for that edge, keeping track of the property name and its values
            # If it doesn't exist, add an entry
            for k, v in edge[2].items():
                if k not in edge_properties[edge_pair]:
                    edge_properties[edge_pair][k] = []

                edge_properties[edge_pair][k] += [v]

    for node in G.nodes():
        text = f"Node: {node}<br>Degree: {G.degree(node)}"

        x, y = G.nodes[node]["pos"]
        node_trace["x"] += tuple([x])
        node_trace["y"] += tuple([y])

        if node_text:

            for prop in node_text:
                text += f"<br></br>{prop}: {G.nodes[node][prop]}"

        node_trace["text"] += tuple([text.strip()])

        if isinstance(size_method, list):
            node_trace["marker"]["size"] = size_method
        else:
            if size_method == "degree":
                node_trace["marker"]["size"] += tuple([G.degree(node) + 12])
            elif size_method == "static":
                node_trace["marker"]["size"] += tuple([12])
            else:
                node_trace["marker"]["size"] += tuple([G.nodes[node][size_method]])

        if isinstance(color_method, list):
            node_trace["marker"]["color"] = color_method
        else:
            if color_method == "degree":
                node_trace["marker"]["color"] += tuple([G.degree(node)])
            else:
                # Look for the property, otherwise look for a color code
                # If none exist, throw an error
                if color_method in G.nodes[node]:
                    node_trace["marker"]["color"] += tuple(
                        [G.nodes[node][color_method]]
                    )
                else:
                    node_trace["marker"]["color"] += tuple([color_method])

    if show_edgetext:

        edge_text_list = [
            "\n".join(f"{k}: {v}" for k, v in vals.items())
            for _, vals in edge_properties.items()
        ]

        middle_node_trace["text"] = edge_text_list

    return node_trace, edge_trace, middle_node_trace


def _generate_figure(
    G,
    node_trace,
    edge_trace,
    middle_node_trace,
    title,
    titlefont_size,
    showlegend,
    annotation_text,
):
    """
    Helper function to generate the figure for the Graph.
    """

    annotations = [
        dict(
            text=annotation_text,
            showarrow=False,
            xref="paper",
            yref="paper",
            x=0.005,
            y=-0.002,
        )
    ]

    if isinstance(G, (nx.DiGraph, nx.MultiDiGraph)):

        for edge in G.edges():
            annotations.append(
                dict(
                    ax=G.nodes[edge[0]]["pos"][0],
                    ay=G.nodes[edge[0]]["pos"][1],
                    axref="x",
                    ayref="y",
                    x=G.nodes[edge[1]]["pos"][0],
                    y=G.nodes[edge[1]]["pos"][1],
                    xref="x",
                    yref="y",
                    showarrow=True,
                    arrowhead=1,
                )
            )

    fig = go.Figure(
        data=[edge_trace, node_trace, middle_node_trace],
        layout=go.Layout(
            title=title,
            titlefont_size=titlefont_size,
            showlegend=showlegend,
            hovermode="closest",
            margin=dict(b=20, l=5, r=5, t=40),
            annotations=annotations,
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        ),
    )

    return fig


def _apply_layout(G, layout):
    """
    Applies a layout to a Graph.
    """

    layout_functions = {
        "random": nx.random_layout,
        "circular": nx.circular_layout,
        "kamada": nx.kamada_kawai_layout,
        "planar": nx.planar_layout,
        "spring": nx.spring_layout,
        "spectral": nx.spectral_layout,
        "spiral": nx.spiral_layout,
    }

    pos_dict = layout_functions[layout](G)

    nx.set_node_attributes(G, pos_dict, "pos")
