"""
LLM module for Google Gemini integration to generate flavor reports and insights
"""

import os
from typing import Dict, List, Optional
import google.generativeai as genai
from pathlib import Path


class GeminiFlavorReporter:
    """
    Google Gemini-powered flavor report generator for liquor analytics
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Gemini API client
        
        Args:
            api_key: Google Gemini API key (defaults to GEMINI_API_KEY env var)
        """
        self.api_key = api_key or os.getenv('GEMINI_API_KEY')
        
        if not self.api_key:
            raise ValueError(
                "Gemini API key not found. Set GEMINI_API_KEY environment variable "
                "or pass api_key parameter."
            )
        
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-pro')
    
    def generate_flavor_report(
        self,
        chemical_data: Dict,
        sensory_scores: Optional[Dict] = None,
        sensory_notes: Optional[Dict] = None
    ) -> str:
        """
        Generate comprehensive flavor report based on chemical and sensory data
        
        Args:
            chemical_data: Dictionary with chemical composition data
            sensory_scores: Optional dictionary with predicted/actual sensory scores
            sensory_notes: Optional dictionary with tasting notes
        
        Returns:
            AI-generated flavor report as string
        """
        prompt = self._build_flavor_report_prompt(chemical_data, sensory_scores, sensory_notes)
        
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"Error generating flavor report: {str(e)}"
    
    def _build_flavor_report_prompt(
        self,
        chemical_data: Dict,
        sensory_scores: Optional[Dict],
        sensory_notes: Optional[Dict]
    ) -> str:
        """Build prompt for flavor report generation"""
        
        prompt = """You are an expert sommelier and liquor analyst. Generate a detailed, 
professional flavor report based on the following data:

**Chemical Composition:**
"""
        
        # Add chemical data
        for key, value in chemical_data.items():
            if value is not None:
                prompt += f"- {key.replace('_', ' ').title()}: {value}\n"
        
        # Add sensory scores if available
        if sensory_scores:
            prompt += "\n**Sensory Scores (0-100):**\n"
            for key, value in sensory_scores.items():
                if value is not None:
                    prompt += f"- {key.replace('_', ' ').title()}: {value:.1f}\n"
        
        # Add sensory notes if available
        if sensory_notes:
            prompt += "\n**Tasting Notes:**\n"
            for key, value in sensory_notes.items():
                if value is not None:
                    prompt += f"- {key.replace('_', ' ').title()}: {value}\n"
        
        prompt += """

Please provide:
1. **Flavor Profile Summary**: A concise overview of the expected flavor characteristics
2. **Aroma Analysis**: Detailed description of aromatic compounds and expected nose
3. **Taste & Palate**: Description of flavor notes, balance, and complexity
4. **Finish**: Analysis of aftertaste and lingering flavors
5. **Quality Assessment**: Overall quality evaluation and drinking recommendations
6. **Pairing Suggestions**: Food or occasion pairing recommendations

Keep the tone professional yet accessible, suitable for both industry professionals and enthusiasts.
"""
        
        return prompt
    
    def generate_chemical_insights(self, chemical_data: Dict) -> str:
        """
        Generate insights about chemical composition and its impact on flavor
        
        Args:
            chemical_data: Dictionary with chemical composition data
        
        Returns:
            AI-generated insights
        """
        prompt = f"""As an expert in liquor chemistry and flavor science, analyze this chemical composition:

{self._format_chemical_data(chemical_data)}

Provide insights on:
1. How these chemical parameters influence flavor and aroma
2. Balance assessment (e.g., alcohol-to-sugar ratio, acidity balance)
3. Potential aging or maturation characteristics
4. Comparison to typical industry standards
5. Any notable chemical signatures or unique aspects

Be specific and technical but also explain in accessible terms.
"""
        
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"Error generating insights: {str(e)}"
    
    def generate_comparison_report(
        self,
        lot_data_list: List[Dict],
        focus_lot: str
    ) -> str:
        """
        Generate comparative analysis report for multiple LOTs
        
        Args:
            lot_data_list: List of LOT data dictionaries
            focus_lot: LOT number to focus the comparison on
        
        Returns:
            AI-generated comparison report
        """
        prompt = f"""Compare and analyze these liquor LOTs, with focus on LOT {focus_lot}:

"""
        
        for lot_data in lot_data_list:
            lot_num = lot_data.get('lot_number', 'Unknown')
            prompt += f"\n**LOT {lot_num}:**\n"
            prompt += self._format_chemical_data(lot_data)
            prompt += "\n"
        
        prompt += f"""

Provide a comparative analysis including:
1. Key differences in chemical composition
2. How LOT {focus_lot} stands out from the others
3. Quality ranking and rationale
4. Recommendations for each LOT (best use, target market, etc.)
5. Trends or patterns observed across the LOTs
"""
        
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"Error generating comparison report: {str(e)}"
    
    def generate_sensory_descriptors(
        self,
        chemical_data: Dict,
        predicted_scores: Dict
    ) -> Dict[str, List[str]]:
        """
        Generate sensory descriptors based on chemical data and predicted scores
        
        Args:
            chemical_data: Chemical composition data
            predicted_scores: Predicted sensory scores
        
        Returns:
            Dictionary with lists of descriptors for aroma, flavor, etc.
        """
        prompt = f"""Based on this liquor analysis:

Chemical Data:
{self._format_chemical_data(chemical_data)}

Predicted Scores:
{self._format_scores(predicted_scores)}

Generate specific sensory descriptors in the following categories:
- Aroma descriptors (list 5-7 specific aromas)
- Flavor descriptors (list 5-7 specific flavors)
- Mouthfeel descriptors (list 3-5 texture/body descriptors)
- Finish descriptors (list 3-5 aftertaste descriptors)

Format your response as:
AROMA: descriptor1, descriptor2, descriptor3...
FLAVOR: descriptor1, descriptor2, descriptor3...
MOUTHFEEL: descriptor1, descriptor2, descriptor3...
FINISH: descriptor1, descriptor2, descriptor3...
"""
        
        try:
            response = self.model.generate_content(prompt)
            text = response.text
            
            # Parse response into structured format
            descriptors = {
                'aroma': [],
                'flavor': [],
                'mouthfeel': [],
                'finish': []
            }
            
            for line in text.split('\n'):
                line = line.strip()
                if line.startswith('AROMA:'):
                    descriptors['aroma'] = [d.strip() for d in line.replace('AROMA:', '').split(',')]
                elif line.startswith('FLAVOR:'):
                    descriptors['flavor'] = [d.strip() for d in line.replace('FLAVOR:', '').split(',')]
                elif line.startswith('MOUTHFEEL:'):
                    descriptors['mouthfeel'] = [d.strip() for d in line.replace('MOUTHFEEL:', '').split(',')]
                elif line.startswith('FINISH:'):
                    descriptors['finish'] = [d.strip() for d in line.replace('FINISH:', '').split(',')]
            
            return descriptors
        except Exception as e:
            return {
                'aroma': ['Error generating descriptors'],
                'flavor': [str(e)],
                'mouthfeel': [],
                'finish': []
            }
    
    def _format_chemical_data(self, chemical_data: Dict) -> str:
        """Format chemical data for prompt inclusion"""
        lines = []
        for key, value in chemical_data.items():
            if value is not None and 'score' not in key.lower():
                lines.append(f"- {key.replace('_', ' ').title()}: {value}")
        return '\n'.join(lines)
    
    def _format_scores(self, scores: Dict) -> str:
        """Format sensory scores for prompt inclusion"""
        lines = []
        for key, value in scores.items():
            if value is not None:
                lines.append(f"- {key.replace('_', ' ').title()}: {value:.1f}/100")
        return '\n'.join(lines)


def test_gemini_connection(api_key: Optional[str] = None) -> bool:
    """
    Test Gemini API connection
    
    Args:
        api_key: Optional API key for testing
    
    Returns:
        True if connection successful, False otherwise
    """
    try:
        reporter = GeminiFlavorReporter(api_key=api_key)
        # Simple test prompt
        response = reporter.model.generate_content("Say 'Connection successful' if you can read this.")
        return "successful" in response.text.lower()
    except Exception as e:
        print(f"Connection test failed: {e}")
        return False
