import plotly.graph_objects as go
from typing import Dict

class ChartBuilder:
    """Build interactive charts using Plotly"""
    
    @staticmethod
    def create_radar_chart(scores: Dict[str, float], title: str = "Site Suitability Scorecard") -> go.Figure:
        """
        Create a radar/spider chart for site scores
        
        Args:
            scores: Dict of category: score (0-5 scale)
            title: Chart title
        """
        categories = list(scores.keys())
        values = list(scores.values())
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatterpolar(
            r=values,
            theta=categories,
            fill='toself',
            name='Suitability Score'
        ))
        
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 5]
                )
            ),
            title=title,
            template="plotly_dark",
            height=500
        )
        
        return fig
    
    @staticmethod
    def create_score_bar_chart(scores: Dict[str, float], title: str = "Layer Scores") -> go.Figure:
        """Create a bar chart showing individual layer scores"""
        
        categories = list(scores.keys())
        values = list(scores.values())
        
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            x=categories,
            y=values,
            marker=dict(
                color=values,
                colorscale='RdYlGn',
                cmin=0,
                cmax=5,
                showscale=True,
                colorbar=dict(title="Score (0-5)")
            )
        ))
        
        fig.update_layout(
            title=title,
            yaxis_title="Suitability Score",
            template="plotly_dark",
            height=400,
            xaxis_tickangle=-45
        )
        
        return fig
    
    @staticmethod
    def create_weight_summary(weights: Dict[str, float]) -> go.Figure:
        """Create pie chart showing weight distribution"""
        
        categories = list(weights.keys())
        values = list(weights.values())
        
        fig = go.Figure(data=[go.Pie(
            labels=categories,
            values=values,
            hole=0.3
        )])
        
        fig.update_layout(
            title="Weightage Distribution",
            template="plotly_dark",
            height=400
        )
        
        return fig
