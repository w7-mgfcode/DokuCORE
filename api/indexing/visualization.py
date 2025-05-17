"""
Index visualization tools for hierarchical document structure.

This module provides tools to visualize document hierarchies, relationships,
and search results for better understanding and debugging.
"""

import logging
import json
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
import matplotlib.pyplot as plt
import networkx as nx
from matplotlib.patches import Rectangle
import seaborn as sns
import numpy as np

logger = logging.getLogger(__name__)

@dataclass
class VisualizationConfig:
    """Configuration for visualization tools."""
    figure_size: Tuple[int, int] = (12, 8)
    node_size: int = 1000
    font_size: int = 10
    edge_width: float = 2.0
    color_scheme: str = "viridis"
    max_nodes: int = 50  # Limit for performance
    show_labels: bool = True
    save_path: Optional[str] = None
    dpi: int = 300

class IndexVisualizer:
    """Visualization tools for hierarchical document index."""
    
    def __init__(self, config: Optional[VisualizationConfig] = None):
        """Initialize the visualizer with configuration."""
        self.config = config or VisualizationConfig()
        
    def visualize_document_hierarchy(self, 
                                   hierarchy_data: List[Dict[str, Any]],
                                   document_title: str = "Document") -> None:
        """
        Visualize document hierarchy as a tree structure.
        
        Args:
            hierarchy_data: List of hierarchy nodes with parent-child relationships
            document_title: Title of the document
        """
        # Create directed graph
        G = nx.DiGraph()
        
        # Add nodes and edges
        for node in hierarchy_data[:self.config.max_nodes]:
            node_id = node['id']
            G.add_node(node_id, 
                      title=node['title'][:30] + '...' if len(node['title']) > 30 else node['title'],
                      level=node['level'])
            
            if node.get('parent_id'):
                G.add_edge(node['parent_id'], node_id)
        
        # Create visualization
        plt.figure(figsize=self.config.figure_size)
        
        # Use hierarchical layout
        pos = nx.spring_layout(G, k=2, iterations=50)
        
        # Color nodes by level
        node_colors = [G.nodes[node]['level'] for node in G.nodes()]
        
        # Draw the graph
        nx.draw_networkx_nodes(G, pos, 
                              node_color=node_colors,
                              node_size=self.config.node_size,
                              cmap=self.config.color_scheme,
                              alpha=0.8)
        
        nx.draw_networkx_edges(G, pos,
                              edge_color='gray',
                              arrows=True,
                              arrowsize=20,
                              width=self.config.edge_width,
                              alpha=0.6)
        
        # Add labels
        if self.config.show_labels:
            labels = nx.get_node_attributes(G, 'title')
            nx.draw_networkx_labels(G, pos, labels,
                                  font_size=self.config.font_size)
        
        plt.title(f"Document Hierarchy: {document_title}", fontsize=16)
        plt.axis('off')
        
        if self.config.save_path:
            plt.savefig(f"{self.config.save_path}/hierarchy_{document_title}.png", 
                       dpi=self.config.dpi, bbox_inches='tight')
        else:
            plt.show()
    
    def visualize_relationship_network(self,
                                     relationships: List[Dict[str, Any]],
                                     nodes: List[Dict[str, Any]]) -> None:
        """
        Visualize relationships between document nodes.
        
        Args:
            relationships: List of relationships with source, target, type, and strength
            nodes: List of nodes with id and title
        """
        # Create graph
        G = nx.Graph()
        
        # Add nodes
        node_dict = {node['id']: node for node in nodes[:self.config.max_nodes]}
        for node_id, node in node_dict.items():
            G.add_node(node_id, title=node['title'][:20] + '...')
        
        # Add edges with weights
        for rel in relationships:
            if rel['source_id'] in node_dict and rel['target_id'] in node_dict:
                G.add_edge(rel['source_id'], rel['target_id'],
                          weight=rel['strength'],
                          type=rel['relationship_type'])
        
        plt.figure(figsize=self.config.figure_size)
        
        # Layout
        pos = nx.spring_layout(G, k=3, iterations=50)
        
        # Edge colors by type
        edge_colors = []
        edge_widths = []
        relationship_types = set()
        
        for u, v, d in G.edges(data=True):
            relationship_types.add(d['type'])
            edge_widths.append(d['weight'] * 5)
            
            if d['type'] == 'semantic':
                edge_colors.append('blue')
            elif d['type'] == 'sibling':
                edge_colors.append('green')
            elif d['type'] == 'keyword_based':
                edge_colors.append('orange')
            else:
                edge_colors.append('gray')
        
        # Draw
        nx.draw_networkx_nodes(G, pos,
                              node_color='lightblue',
                              node_size=self.config.node_size,
                              alpha=0.8)
        
        nx.draw_networkx_edges(G, pos,
                              edge_color=edge_colors,
                              width=edge_widths,
                              alpha=0.6)
        
        # Labels
        if self.config.show_labels:
            labels = nx.get_node_attributes(G, 'title')
            nx.draw_networkx_labels(G, pos, labels,
                                  font_size=self.config.font_size)
        
        # Legend
        legend_elements = []
        for rel_type in relationship_types:
            if rel_type == 'semantic':
                color = 'blue'
            elif rel_type == 'sibling':
                color = 'green'
            elif rel_type == 'keyword_based':
                color = 'orange'
            else:
                color = 'gray'
            
            legend_elements.append(plt.Line2D([0], [0], color=color, lw=3, label=rel_type))
        
        plt.legend(handles=legend_elements, loc='best')
        plt.title("Document Relationship Network", fontsize=16)
        plt.axis('off')
        
        if self.config.save_path:
            plt.savefig(f"{self.config.save_path}/relationships.png", 
                       dpi=self.config.dpi, bbox_inches='tight')
        else:
            plt.show()
    
    def visualize_search_results(self,
                               search_results: List[Dict[str, Any]],
                               query: str) -> None:
        """
        Visualize search results with relevance scores.
        
        Args:
            search_results: List of search results with relevance scores
            query: The search query
        """
        if not search_results:
            logger.warning("No search results to visualize")
            return
        
        plt.figure(figsize=self.config.figure_size)
        
        # Prepare data
        titles = [r['title'][:30] + '...' if len(r['title']) > 30 else r['title'] 
                 for r in search_results]
        relevances = [r['relevance'] for r in search_results]
        match_types = [r['match_type'] for r in search_results]
        
        # Color by match type
        colors = []
        for match_type in match_types:
            if 'keyword' in match_type:
                colors.append('green')
            elif 'semantic' in match_type:
                colors.append('blue')
            elif 'related' in match_type:
                colors.append('orange')
            else:
                colors.append('gray')
        
        # Create horizontal bar chart
        y_pos = np.arange(len(titles))
        plt.barh(y_pos, relevances, color=colors, alpha=0.8)
        
        plt.yticks(y_pos, titles)
        plt.xlabel('Relevance Score')
        plt.title(f'Search Results for: "{query}"', fontsize=16)
        plt.xlim(0, 1)
        
        # Add value labels
        for i, (relevance, title) in enumerate(zip(relevances, titles)):
            plt.text(relevance + 0.01, i, f'{relevance:.3f}', 
                    va='center', fontsize=8)
        
        # Legend
        legend_elements = [
            plt.Rectangle((0,0),1,1, fc='green', alpha=0.8, label='Keyword Match'),
            plt.Rectangle((0,0),1,1, fc='blue', alpha=0.8, label='Semantic Match'),
            plt.Rectangle((0,0),1,1, fc='orange', alpha=0.8, label='Related Match'),
            plt.Rectangle((0,0),1,1, fc='gray', alpha=0.8, label='Other')
        ]
        plt.legend(handles=legend_elements, loc='lower right')
        
        plt.tight_layout()
        
        if self.config.save_path:
            plt.savefig(f"{self.config.save_path}/search_results_{query}.png", 
                       dpi=self.config.dpi, bbox_inches='tight')
        else:
            plt.show()
    
    def visualize_keyword_distribution(self,
                                     keywords: List[Dict[str, Any]],
                                     document_title: str = "Document") -> None:
        """
        Visualize keyword distribution and importance.
        
        Args:
            keywords: List of keywords with importance scores
            document_title: Title of the document
        """
        if not keywords:
            logger.warning("No keywords to visualize")
            return
        
        plt.figure(figsize=self.config.figure_size)
        
        # Sort keywords by importance
        sorted_keywords = sorted(keywords, key=lambda x: x['importance'], reverse=True)
        top_keywords = sorted_keywords[:20]  # Limit to top 20
        
        # Prepare data
        words = [k['keyword'] for k in top_keywords]
        importances = [k['importance'] for k in top_keywords]
        
        # Create word cloud style visualization
        plt.scatter(range(len(words)), importances, 
                   s=[imp * 1000 for imp in importances],
                   alpha=0.7, c=importances, cmap=self.config.color_scheme)
        
        # Add labels
        for i, (word, imp) in enumerate(zip(words, importances)):
            plt.annotate(word, (i, imp), 
                        xytext=(0, 5), textcoords='offset points',
                        ha='center', fontsize=int(8 + imp * 10))
        
        plt.xlabel('Keywords')
        plt.ylabel('Importance Score')
        plt.title(f'Keyword Distribution: {document_title}', fontsize=16)
        plt.xticks([])
        
        if self.config.save_path:
            plt.savefig(f"{self.config.save_path}/keywords_{document_title}.png", 
                       dpi=self.config.dpi, bbox_inches='tight')
        else:
            plt.show()
    
    def visualize_embedding_similarity_heatmap(self,
                                            embeddings: np.ndarray,
                                            labels: List[str]) -> None:
        """
        Visualize embedding similarity as a heatmap.
        
        Args:
            embeddings: Array of embeddings
            labels: Labels for each embedding
        """
        if len(embeddings) > self.config.max_nodes:
            # Sample for performance
            indices = np.random.choice(len(embeddings), self.config.max_nodes, replace=False)
            embeddings = embeddings[indices]
            labels = [labels[i] for i in indices]
        
        # Calculate similarity matrix
        similarity_matrix = np.inner(embeddings, embeddings)
        
        plt.figure(figsize=self.config.figure_size)
        
        # Create heatmap
        sns.heatmap(similarity_matrix, 
                   xticklabels=labels,
                   yticklabels=labels,
                   cmap='YlOrRd',
                   center=0.5,
                   square=True,
                   cbar_kws={"label": "Cosine Similarity"})
        
        plt.title("Document Embedding Similarity Heatmap", fontsize=16)
        plt.xticks(rotation=45, ha='right')
        plt.yticks(rotation=0)
        plt.tight_layout()
        
        if self.config.save_path:
            plt.savefig(f"{self.config.save_path}/embedding_similarity.png", 
                       dpi=self.config.dpi, bbox_inches='tight')
        else:
            plt.show()
    
    def generate_index_report(self,
                            corpus_stats: Dict[str, Any],
                            output_path: str) -> None:
        """
        Generate a comprehensive HTML report of the index.
        
        Args:
            corpus_stats: Statistics about the indexed corpus
            output_path: Path to save the HTML report
        """
        html_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Document Index Report</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                h1 { color: #333; }
                .stat { margin: 10px 0; }
                .stat-label { font-weight: bold; }
                .chart { margin: 20px 0; }
                table { border-collapse: collapse; width: 100%; }
                th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
                th { background-color: #f2f2f2; }
            </style>
        </head>
        <body>
            <h1>Document Index Report</h1>
            
            <div class="stats">
                <h2>Corpus Statistics</h2>
                <div class="stat">
                    <span class="stat-label">Total Documents:</span> {total_documents}
                </div>
                <div class="stat">
                    <span class="stat-label">Total Nodes:</span> {total_nodes}
                </div>
                <div class="stat">
                    <span class="stat-label">Total Relationships:</span> {total_relationships}
                </div>
                <div class="stat">
                    <span class="stat-label">Total Keywords:</span> {total_keywords}
                </div>
                <div class="stat">
                    <span class="stat-label">Average Nodes per Document:</span> {avg_nodes_per_doc:.2f}
                </div>
                <div class="stat">
                    <span class="stat-label">Average Relationships per Node:</span> {avg_relationships_per_node:.2f}
                </div>
            </div>
            
            <div class="charts">
                <h2>Visualizations</h2>
                <div class="chart">
                    <h3>Document Size Distribution</h3>
                    <img src="document_sizes.png" alt="Document Size Distribution">
                </div>
                <div class="chart">
                    <h3>Relationship Type Distribution</h3>
                    <img src="relationship_types.png" alt="Relationship Type Distribution">
                </div>
                <div class="chart">
                    <h3>Keyword Frequency</h3>
                    <img src="keyword_frequency.png" alt="Keyword Frequency">
                </div>
            </div>
            
            <div class="details">
                <h2>Index Details</h2>
                <table>
                    <tr>
                        <th>Metric</th>
                        <th>Value</th>
                    </tr>
                    <tr>
                        <td>Embedding Dimensions</td>
                        <td>{embedding_dim}</td>
                    </tr>
                    <tr>
                        <td>Index Type</td>
                        <td>{index_type}</td>
                    </tr>
                    <tr>
                        <td>Similarity Metric</td>
                        <td>{similarity_metric}</td>
                    </tr>
                    <tr>
                        <td>Storage Size</td>
                        <td>{storage_size_mb:.2f} MB</td>
                    </tr>
                </table>
            </div>
            
            <div class="timestamp">
                <p>Generated on: {timestamp}</p>
            </div>
        </body>
        </html>
        """
        
        # Format the HTML with stats
        html_content = html_template.format(
            total_documents=corpus_stats.get('total_documents', 0),
            total_nodes=corpus_stats.get('total_nodes', 0),
            total_relationships=corpus_stats.get('total_relationships', 0),
            total_keywords=corpus_stats.get('total_keywords', 0),
            avg_nodes_per_doc=corpus_stats.get('avg_nodes_per_doc', 0),
            avg_relationships_per_node=corpus_stats.get('avg_relationships_per_node', 0),
            embedding_dim=corpus_stats.get('embedding_dim', 384),
            index_type=corpus_stats.get('index_type', 'HNSW'),
            similarity_metric=corpus_stats.get('similarity_metric', 'cosine'),
            storage_size_mb=corpus_stats.get('storage_size_mb', 0),
            timestamp=corpus_stats.get('timestamp', 'N/A')
        )
        
        # Save HTML report
        with open(output_path, 'w') as f:
            f.write(html_content)
        
        logger.info(f"Index report generated at {output_path}")
    
    def create_interactive_graph(self,
                               hierarchy_data: List[Dict[str, Any]],
                               relationships: List[Dict[str, Any]],
                               output_path: str) -> None:
        """
        Create an interactive graph visualization using JavaScript.
        
        Args:
            hierarchy_data: Document hierarchy nodes
            relationships: Node relationships
            output_path: Path to save the HTML file
        """
        # Prepare data for D3.js
        nodes_json = json.dumps([{
            'id': node['id'],
            'title': node['title'],
            'level': node['level']
        } for node in hierarchy_data[:self.config.max_nodes]])
        
        edges_json = json.dumps([{
            'source': rel['source_id'],
            'target': rel['target_id'],
            'strength': rel['strength'],
            'type': rel['relationship_type']
        } for rel in relationships])
        
        html_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Interactive Document Graph</title>
            <script src="https://d3js.org/d3.v7.min.js"></script>
            <style>
                .links line {
                    stroke: #999;
                    stroke-opacity: 0.6;
                }
                .nodes circle {
                    stroke: #fff;
                    stroke-width: 1.5px;
                }
                .tooltip {
                    position: absolute;
                    text-align: center;
                    width: 200px;
                    height: auto;
                    padding: 5px;
                    font: 12px sans-serif;
                    background: lightsteelblue;
                    border: 0px;
                    border-radius: 8px;
                    pointer-events: none;
                    opacity: 0;
                }
            </style>
        </head>
        <body>
            <div id="graph"></div>
            <script>
                const nodes = {nodes_json};
                const links = {edges_json};
                
                const width = 960;
                const height = 600;
                
                const svg = d3.select("#graph")
                    .append("svg")
                    .attr("width", width)
                    .attr("height", height);
                
                const simulation = d3.forceSimulation(nodes)
                    .force("link", d3.forceLink(links).id(d => d.id).distance(100))
                    .force("charge", d3.forceManyBody().strength(-300))
                    .force("center", d3.forceCenter(width / 2, height / 2));
                
                const link = svg.append("g")
                    .attr("class", "links")
                    .selectAll("line")
                    .data(links)
                    .enter().append("line")
                    .attr("stroke-width", d => Math.sqrt(d.strength) * 5);
                
                const node = svg.append("g")
                    .attr("class", "nodes")
                    .selectAll("circle")
                    .data(nodes)
                    .enter().append("circle")
                    .attr("r", d => 5 + d.level * 2)
                    .attr("fill", d => d3.schemeCategory10[d.level])
                    .call(d3.drag()
                        .on("start", dragstarted)
                        .on("drag", dragged)
                        .on("end", dragended));
                
                node.append("title")
                    .text(d => d.title);
                
                simulation.on("tick", () => {{
                    link
                        .attr("x1", d => d.source.x)
                        .attr("y1", d => d.source.y)
                        .attr("x2", d => d.target.x)
                        .attr("y2", d => d.target.y);
                    
                    node
                        .attr("cx", d => d.x)
                        .attr("cy", d => d.y);
                }});
                
                function dragstarted(event, d) {{
                    if (!event.active) simulation.alphaTarget(0.3).restart();
                    d.fx = d.x;
                    d.fy = d.y;
                }}
                
                function dragged(event, d) {{
                    d.fx = event.x;
                    d.fy = event.y;
                }}
                
                function dragended(event, d) {{
                    if (!event.active) simulation.alphaTarget(0);
                    d.fx = null;
                    d.fy = null;
                }}
            </script>
        </body>
        </html>
        """
        
        html_content = html_template.format(
            nodes_json=nodes_json,
            edges_json=edges_json
        )
        
        with open(output_path, 'w') as f:
            f.write(html_content)
        
        logger.info(f"Interactive graph created at {output_path}")